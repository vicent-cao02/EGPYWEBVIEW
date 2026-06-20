# backend/productos.py

from typing import List, Dict, Any, Optional
from .db import get_connection
from .logs import registrar_log


# ---------------------------
# LISTAR PRODUCTOS
# ---------------------------
def list_products() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos ORDER BY nombre")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_product(producto_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------
# CREAR PRODUCTO
# ---------------------------
def crear_producto(
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: int,
    usuario: Optional[str] = None
) -> dict:

    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre no puede estar vacío")

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Validar duplicado
        cursor.execute("SELECT id FROM productos WHERE LOWER(nombre) = LOWER(?)", (nombre,))
        if cursor.fetchone():
            raise ValueError("Ya existe un producto con ese nombre")

        cursor.execute("""
            INSERT INTO productos (nombre, precio, cantidad, categoria_id)
            VALUES (?, ?, ?, ?)
        """, (nombre, precio, cantidad, categoria_id))

        conn.commit()

        cursor.execute("SELECT * FROM productos WHERE id = last_insert_rowid()")
        nuevo = dict(cursor.fetchone())

        if usuario:
            registrar_log(usuario, "crear_producto", nuevo)

        return nuevo

    finally:
        conn.close()


# ---------------------------
# EDITAR PRODUCTO
# ---------------------------
def editar_producto(
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: int,
    usuario: Optional[str] = None
) -> dict:

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Validar duplicado (excluyendo el actual)
        cursor.execute("""
            SELECT id FROM productos 
            WHERE LOWER(nombre) = LOWER(?) AND id != ?
        """, (nombre, producto_id))

        if cursor.fetchone():
            raise ValueError("Ya existe otro producto con ese nombre")

        cursor.execute("""
            UPDATE productos
            SET nombre = ?, precio = ?, cantidad = ?, categoria_id = ?
            WHERE id = ?
        """, (nombre, precio, cantidad, categoria_id, producto_id))

        conn.commit()

        producto = get_product(producto_id)

        if usuario:
            registrar_log(usuario, "editar_producto", producto)

        return producto

    finally:
        conn.close()


# ---------------------------
# ELIMINAR PRODUCTO (ÚNICO)
# ---------------------------
def eliminar_producto(producto_id: int, usuario: Optional[str] = None) -> bool:

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
        producto = cursor.fetchone()

        if not producto:
            return False

        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()

        if usuario:
            registrar_log(usuario, "eliminar_producto", dict(producto))

        return True

    finally:
        conn.close()


# ---------------------------
# AJUSTAR STOCK
# ---------------------------
def adjust_stock(product_id: int, cantidad_delta: int, usuario=None) -> dict:

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM productos WHERE id = ?", (product_id,))
        prod = cursor.fetchone()

        if not prod:
            raise ValueError("Producto no encontrado")

        prod = dict(prod)
        nuevo_stock = prod["cantidad"] + cantidad_delta

        if nuevo_stock < 0:
            raise ValueError("Stock insuficiente")

        cursor.execute(
            "UPDATE productos SET cantidad = ? WHERE id = ?",
            (nuevo_stock, product_id)
        )

        conn.commit()

        prod["cantidad"] = nuevo_stock

        if usuario:
            registrar_log(usuario, "ajustar_stock", {
                "producto_id": product_id,
                "antes": prod["cantidad"] - cantidad_delta,
                "despues": nuevo_stock,
                "delta": cantidad_delta
            })

        return prod

    finally:
        conn.close()


# ---------------------------
# INCREMENTAR STOCK (usa adjust_stock)
# ---------------------------
def increment_stock(producto_id: int, cantidad: int, usuario=None):
    return adjust_stock(producto_id, cantidad, usuario)


def map_productos():
    productos = list_products()  # o tu función real

    return {
        p["id"]: p["nombre"]
        for p in productos
    }