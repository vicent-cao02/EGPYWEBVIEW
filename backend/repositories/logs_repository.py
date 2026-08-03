from typing import List, Dict, Any, Optional

from backend.database import db


class LogsRepository:
    """Repositorio para la tabla `logs` y `auditoria`."""

    def __init__(self, conn=None):
        self.conn = conn

    def _fetchall(self, query: str, params=()) -> List[Dict[str, Any]]:
        if self.conn:
            cur = self.conn.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        return db.fetchall(query, params)

    def listar_logs(self) -> List[Dict[str, Any]]:
        return self._fetchall("SELECT * FROM logs ORDER BY fecha DESC")

    def obtener_logs_usuario(self, username: str) -> List[Dict[str, Any]]:
        return self._fetchall(
            """
            SELECT usuario, accion, fecha, detalles
            FROM logs
            WHERE usuario = ?
            ORDER BY fecha DESC
            LIMIT 100
            """,
            (username,)
        )

    def listar_auditoria(self) -> List[Dict[str, Any]]:
        return self._fetchall(
            """
            SELECT id, accion, producto_id, usuario, fecha
            FROM auditoria
            ORDER BY fecha DESC
            """
        )

    def obtener_auditoria(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._fetchall(
            "SELECT id, accion, producto_id, usuario, fecha FROM auditoria ORDER BY fecha DESC LIMIT ?",
            (limit,),
        )
