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
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def map_productos() -> Dict[str, str]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM productos")
        rows = cursor.fetchall()
        return {row["id"]: row["nombre"] for row in rows}
    finally:
        conn.close()
# ---------------------------
# AGREGAR PRODUCTO
# ---------------------------
def guardar_producto(
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: str,
    usuario: Optional[str] = None
) -> dict:
    """
    Crea un nuevo producto o edita uno existente si ya existe.
    Devuelve el producto creado/actualizado como diccionario.
    """
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del producto no puede estar vacío.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Verificar si ya existe un producto con ese nombre
        cursor.execute("SELECT * FROM productos WHERE nombre = ?", (nombre,))
        existing = cursor.fetchone()

        if existing:
            # Editar producto existente
            cursor.execute("""
                UPDATE productos
                SET precio = ?, cantidad = ?, categoria_id = ?
                WHERE id = ?
            """, (precio, cantidad, categoria_id, existing["id"]))
            conn.commit()

            # Obtener el producto actualizado
            cursor.execute("SELECT * FROM productos WHERE id = ?", (existing["id"],))
            updated = dict(cursor.fetchone())

            registrar_log(usuario or "sistema", "editar_producto", {
                "id": updated["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id
            })

            return updated

        else:
            # Crear nuevo producto
            cursor.execute("""
                INSERT INTO productos (nombre, precio, cantidad, categoria_id)
                VALUES (?, ?, ?, ?)
            """, (nombre, precio, cantidad, categoria_id))
            conn.commit()

            # Obtener el producto creado
            cursor.execute("SELECT * FROM productos WHERE id = last_insert_rowid()")
            new_prod = dict(cursor.fetchone())

            registrar_log(usuario or "sistema", "crear_producto", {
                "id": new_prod["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id
            })

            return new_prod
            
    finally:
        conn.close()

        
# editar producto
def editar_producto(
    producto_id: str,
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: str,
    usuario: Optional[str] = None
) -> dict:  
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, precio = ?, cantidad = ?, categoria_id = ?
            WHERE id = ?
        """, (nombre, precio, cantidad, categoria_id, producto_id))
        conn.commit()

        # Obtener producto actualizado
        cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
        updated = dict(cursor.fetchone())

        registrar_log(usuario or "sistema", "editar_producto", {
            "id": updated["id"],
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "categoria_id": categoria_id
        })

        return updated
    finally:
        conn.close()


# ---------------------------
# OBTENER PRODUCTO
# ---------------------------
def get_product(producto_id: str) -> Dict[str, Any]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

# ---------------------------
# ELIMINAR PRODUCTO
# ---------------------------
def delete_product(producto_id: str, usuario: Optional[str] = None) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener el nombre del producto antes de eliminarlo para el log
        cursor.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,))
        row = cursor.fetchone()
        if not row:
            return False  # Producto no encontrado

        producto_nombre = row["nombre"]

        # Eliminar el producto
        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()

        # Registrar log de eliminación
        if usuario:
            registrar_log(usuario, "eliminar_producto", {
                "id": producto_id,
                "nombre": producto_nombre
            })

        return True
    finally:
        conn.close()

# ---------------------------
#   adjust_stock
# ---------------------------

def adjust_stock(product_id: str, cantidad_delta: int, usuario=None) -> dict:
    """
    Ajusta el stock de un producto sumando o restando cantidad_delta.
    Devuelve el producto actualizado.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener stock actual
        cursor.execute("SELECT * FROM productos WHERE id = ?", (product_id,))
        prod = cursor.fetchone()
        if not prod:
            raise ValueError(f"Producto {product_id} no encontrado")
        
        prod_dict = dict(prod)
        nuevo_stock = prod_dict["cantidad"] + cantidad_delta
        if nuevo_stock < 0:
            raise ValueError(f"Stock insuficiente para el producto")
        
        cursor.execute(
            "UPDATE productos SET cantidad = ? WHERE id = ?",
            (nuevo_stock, product_id)
        )
        conn.commit()
        
        # Opcional: registrar log
        if usuario:
            registrar_log(usuario, "ajustar_stock", {"producto_id": product_id, "delta": cantidad_delta})
        
        prod_dict["cantidad"] = nuevo_stock
        return prod_dict
    finally:
        conn.close()

    
def update_product(id_producto, nombre, cantidad, precio):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, cantidad = ?, precio = ?
            WHERE id = ?
        """, (nombre, cantidad, precio, id_producto))
        conn.commit()
    finally:
        conn.close()


def eliminar_producto(id_producto: int, usuario: str = None):
    """
    Elimina un producto de la base de datos por su ID y registra la acción en logs.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener datos del producto antes de eliminarlo
        cursor.execute("SELECT id, nombre FROM productos WHERE id = ?", (id_producto,))
        eliminado = cursor.fetchone()

        if eliminado:
            cursor.execute("DELETE FROM productos WHERE id = ?", (id_producto,))
            conn.commit()
            
            # Registrar log si se proporciona usuario
            if usuario:
                registrar_log(usuario, f"Eliminó producto {eliminado['nombre']} (ID {eliminado['id']})")
            return dict(eliminado)
        return None
    finally:
        conn.close()
        
        
def increment_stock(producto_id, cantidad):
    """
    Aumenta la cantidad de stock de un producto.
    """
    producto = get_product(producto_id)
    if producto:
        nuevo_stock = float(producto.get("cantidad", 0)) + float(cantidad)
        update_product(producto_id, nombre=producto["nombre"], cantidad=nuevo_stock, precio=producto["precio"])
    else:
        raise ValueError(f"Producto con ID {producto_id} no encontrado")