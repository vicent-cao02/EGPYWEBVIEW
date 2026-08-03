from typing import Dict, List, Optional
from backend.database import db


class ProductosRepository:
    """
    Repositorio de productos.
    Maneja CRUD y operaciones de inventario.
    """

    def __init__(self, conn=None):
        self.conn = conn

    def _fetchall(self, query: str, params=()) -> List[Dict]:
        if self.conn:
            cursor = self.conn.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        return db.fetchall(query, params)

    def _fetchone(self, query: str, params=()) -> Optional[Dict]:
        if self.conn:
            row = self.conn.execute(query, params).fetchone()
            return dict(row) if row else None
        return db.fetchone(query, params)

    def _execute(self, query: str, params=()) -> int:
        if self.conn:
            cur = self.conn.execute(query, params)
            return cur.lastrowid
        return db.execute(query, params)

    def obtener_por_id(self, producto_id: int) -> Optional[Dict]:
        return self._fetchone(
            "SELECT * FROM productos WHERE id = ?",
            (producto_id,)
        )

    def obtener_por_ids(self, ids: List[int]) -> List[Dict]:
        if not ids:
            return []
        placeholders = ",".join(["?"] * len(ids))
        return self._fetchall(
            f"SELECT * FROM productos WHERE id IN ({placeholders})",
            tuple(ids),
        )

    def obtener_todos(self) -> List[Dict]:
        return self._fetchall("SELECT * FROM productos ORDER BY nombre")

    def crear(self, nombre: str, precio: float, cantidad: float, categoria_id: int) -> int:
        return self._execute(
            "INSERT INTO productos (nombre, precio, cantidad, categoria_id) VALUES (?, ?, ?, ?)",
            (nombre.strip(), float(precio), float(cantidad), categoria_id),
        )

    def actualizar(self, producto_id: int, nombre: str, precio: float, cantidad: float, categoria_id: int) -> Optional[Dict]:
        self._execute(
            "UPDATE productos SET nombre = ?, precio = ?, cantidad = ?, categoria_id = ? WHERE id = ?",
            (nombre.strip(), float(precio), float(cantidad), categoria_id, producto_id),
        )
        return self.obtener_por_id(producto_id)

    def eliminar(self, producto_id: int) -> bool:
        self._execute(
            "DELETE FROM productos WHERE id = ?",
            (producto_id,),
        )
        return True

    def descontar_stock(self, producto_id: int, cantidad: float):
        self._execute(
            "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
            (cantidad, producto_id),
        )

    def aumentar_stock(self, producto_id: int, cantidad: float):
        self._execute(
            "UPDATE productos SET cantidad = cantidad + ? WHERE id = ?",
            (cantidad, producto_id),
        )

    def actualizar_stock(self, producto_id: int, cantidad: float):
        self._execute(
            "UPDATE productos SET cantidad = ? WHERE id = ?",
            (cantidad, producto_id),
        )
