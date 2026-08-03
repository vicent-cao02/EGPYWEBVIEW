from typing import Any, Dict, List, Optional

from backend.database import db


class ClientesRepository:
    def __init__(self, conn=None):
        self.conn = conn

    def _fetchone(self, query: str, params=()) -> Optional[Dict[str, Any]]:
        if self.conn:
            row = self.conn.execute(query, params).fetchone()
            return dict(row) if row else None
        return db.fetchone(query, params)

    def _fetchall(self, query: str, params=()) -> List[Dict[str, Any]]:
        if self.conn:
            rows = self.conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        return db.fetchall(query, params)

    def _execute(self, query: str, params=()) -> int:
        if self.conn:
            cursor = self.conn.execute(query, params)
            return cursor.lastrowid
        return db.execute(query, params)

    def obtener_por_id(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        return self._fetchone(
            """
            SELECT id, nombre, telefono, ci, chapa, direccion, deuda_total
            FROM clientes
            WHERE id = ?
            """,
            (cliente_id,),
        )

    def obtener_todos(self) -> List[Dict[str, Any]]:
        return self._fetchall(
            """
            SELECT id, nombre, telefono, ci, chapa, direccion, deuda_total
            FROM clientes
            ORDER BY nombre
            """
        )

    def crear(self, nombre: str, telefono: Optional[str], ci: Optional[str], direccion: Optional[str], chapa: Optional[str]) -> Dict[str, Any]:
        cliente_id = self._execute(
            """
            INSERT INTO clientes (nombre, telefono, ci, direccion, chapa)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre.strip(), telefono.strip() if telefono else None, ci.strip() if ci else None, direccion.strip() if direccion else None, chapa.strip() if chapa else None),
        )
        return self.obtener_por_id(cliente_id)

    def actualizar(self, cliente_id: int, nombre: Optional[str] = None, telefono: Optional[str] = None, ci: Optional[str] = None, chapa: Optional[str] = None, direccion: Optional[str] = None) -> Optional[Dict[str, Any]]:
        cliente_actual = self.obtener_por_id(cliente_id)
        if not cliente_actual:
            return None
        nombre = nombre or cliente_actual.get("nombre")
        telefono = telefono or cliente_actual.get("telefono", "")
        ci = ci or cliente_actual.get("ci", "")
        chapa = chapa or cliente_actual.get("chapa", "")
        direccion = direccion or cliente_actual.get("direccion", "")
        self._execute(
            """
            UPDATE clientes
            SET nombre = ?, telefono = ?, ci = ?, chapa = ?, direccion = ?
            WHERE id = ?
            """,
            (nombre, telefono, ci, chapa, direccion, cliente_id),
        )
        return self.obtener_por_id(cliente_id)

    def eliminar(self, cliente_id: int) -> bool:
        self._execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        return True

    def actualizar_deuda_total(self, cliente_id: int, monto: float) -> Optional[Dict[str, Any]]:
        self._execute(
            """
            UPDATE clientes
            SET deuda_total = MAX(deuda_total + ?, 0)
            WHERE id = ?
            """,
            (monto, cliente_id),
        )
        return self.obtener_por_id(cliente_id)
