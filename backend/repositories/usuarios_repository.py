from typing import Any, Dict, List, Optional

from backend.database import db


class UsuariosRepository:
    def __init__(self, conn=None):
        self.conn = conn

    def _fetchall(self, query: str, params=()) -> List[Dict[str, Any]]:
        if self.conn:
            cur = self.conn.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        return db.fetchall(query, params)

    def listar_usuarios(self) -> List[Dict[str, Any]]:
        return self._fetchall(
            """
            SELECT username, rol, activo, created_at, requiere_cambio_password
            FROM usuarios ORDER BY created_at DESC
            """
        )

    def obtener_rol(self, username: str) -> Optional[str]:
        rows = self._fetchall("SELECT rol FROM usuarios WHERE username=?", (username,))
        return rows[0]["rol"] if rows else None

    def autenticar(self, username: str):
        rows = self._fetchall(
            "SELECT password, activo, intentos_fallidos, bloqueado_hasta, rol FROM usuarios WHERE username=?",
            (username,),
        )
        return rows[0] if rows else None
