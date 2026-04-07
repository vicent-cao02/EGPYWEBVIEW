# backend/categorias.py
from .db import get_connection
from .logs import registrar_log
from typing import Optional, Dict, List


# ---------------------------
# Funciones de categorías
# ---------------------------

def list_categories() -> List[Dict]:
    """Devuelve todas las categorías con su id desde la DB"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_category(cat_id: int) -> Optional[Dict]:
    """Devuelve una categoría específica por su id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias WHERE id = ?", (cat_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    finally:
        conn.close()


def agregar_categoria(nombre: str, usuario: str = None) -> str:
    """Agrega una nueva categoría"""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    # Verificar duplicado
    categorias = [c["nombre"].lower() for c in list_categories()]
    if nombre.lower() in categorias:
        raise ValueError(f"La categoría '{nombre}' ya existe.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        conn.commit()
    finally:
        conn.close()

    registrar_log(usuario or "sistema", "crear_categoria", {"nombre": nombre})
    return nombre


def editar_categoria(cat_id: int, nombre_nuevo: str, usuario: str = None) -> str:
    """Edita el nombre de una categoría existente por ID"""
    nombre_nuevo = nombre_nuevo.strip()
    if not nombre_nuevo:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    categoria = get_category(cat_id)
    if not categoria:
        raise ValueError(f"La categoría con ID {cat_id} no existe.")

    categorias = [c["nombre"].lower() for c in list_categories() if c["id"] != cat_id]
    if nombre_nuevo.lower() in categorias:
        raise ValueError(f"La categoría '{nombre_nuevo}' ya existe.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nombre_nuevo, cat_id))
        conn.commit()
    finally:
        conn.close()

    registrar_log(usuario or "sistema", "editar_categoria", {
        "id": cat_id,
        "nombre_nuevo": nombre_nuevo
    })
    return nombre_nuevo


def eliminar_categoria(cat_id: int, usuario: str = None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias WHERE id = ?", (cat_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
            conn.commit()
            registrar_log(usuario or "sistema", "eliminar_categoria", dict(row))
            return dict(row)
        else:
            raise ValueError("Categoría no encontrada")
    finally:
        conn.close()


def list_products_by_category(categoria_id: int) -> list[dict]:
    """Devuelve todos los productos de una categoría específica"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE categoria_id = ? ORDER BY nombre", (categoria_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
