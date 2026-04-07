# backend/categorias.py
from sqlalchemy import text
from .db import engine
from .logs import registrar_log
from typing import Optional, Dict, List

# ---------------------------
# Funciones de categorías
# ---------------------------

def list_categories() -> List[Dict]:
    """Devuelve todas las categorías con su id desde la DB"""
    query = text("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.mappings().all()]

def get_category(cat_id: int) -> Optional[Dict]:
    """Devuelve una categoría específica por su id"""
    query = text("SELECT id, nombre FROM categorias WHERE id = :id")
    with engine.connect() as conn:
        result = conn.execute(query, {"id": cat_id}).mappings().first()
        return dict(result) if result else None

def agregar_categoria(nombre: str, usuario: str = None) -> str:
    """Agrega una nueva categoría"""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    # Verificar duplicado
    categorias = [c["nombre"].lower() for c in list_categories()]
    if nombre.lower() in categorias:
        raise ValueError(f"La categoría '{nombre}' ya existe.")

    query = text("INSERT INTO categorias (nombre) VALUES (:nombre)")
    with engine.begin() as conn:
        conn.execute(query, {"nombre": nombre})

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

    query = text("UPDATE categorias SET nombre = :nombre_nuevo WHERE id = :cat_id")
    with engine.begin() as conn:
        conn.execute(query, {"nombre_nuevo": nombre_nuevo, "cat_id": cat_id})

    registrar_log(usuario or "sistema", "editar_categoria", {
        "id": cat_id,
        "nombre_nuevo": nombre_nuevo
    })
    return nombre_nuevo

def eliminar_categoria(cat_id: int, usuario: str = None):
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM categorias WHERE id = :id RETURNING id, nombre"), {"id": cat_id})
        row = res.mappings().first()
    if row:
        registrar_log(usuario or "sistema", "eliminar_categoria", dict(row))
        return dict(row)
    else:
        raise ValueError("Categoría no encontrada")

def list_products_by_category(categoria_id: int) -> list[dict]:
    """Devuelve todos los productos de una categoría específica"""
    query = text("SELECT * FROM productos WHERE categoria_id = :categoria_id ORDER BY nombre")
    with engine.connect() as conn:
        result = conn.execute(query, {"categoria_id": categoria_id})
        return [dict(row) for row in result.mappings().all()]
