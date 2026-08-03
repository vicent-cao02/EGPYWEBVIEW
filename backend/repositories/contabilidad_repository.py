from typing import Dict, List, Optional

from backend.database import db


class ContabilidadRepository:
    """
    Repositorio para operaciones contables básicas.
    Puede recibir una conexión externa para operaciones transaccionales.
    """

    def __init__(self, conn=None):
        self.conn = conn

    def _execute(self, query: str, params=()):
        if self.conn:
            cursor = self.conn.execute(query, params)
            return cursor

        return db.execute(query, params)

    def _fetchall(self, query: str, params=()):
        if self.conn:
            cursor = self.conn.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

        return db.fetchall(query, params)

    def _fetchone(self, query: str, params=()):
        if self.conn:
            cursor = self.conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

        return db.fetchone(query, params)

    # Cuentas
    def crear_cuenta(self, codigo: str, nombre: str, tipo: str, padre_id: Optional[int] = None):
        return self._execute(
            """
            INSERT OR IGNORE INTO cuentas_contables (codigo, nombre, tipo, padre_id)
            VALUES (?, ?, ?, ?)
            """,
            (codigo, nombre, tipo, padre_id),
        )

    def obtener_por_codigo(self, codigo: str) -> Optional[Dict]:
        return self._fetchone(
            """
            SELECT * FROM cuentas_contables WHERE codigo = ?
            """,
            (codigo,)
        )

    def crear_asiento(self, fecha: str, descripcion: str, referencia: str, usuario: str, total: float):
        cursor = self._execute(
            """
            INSERT INTO asientos_contables (fecha, descripcion, referencia, usuario, total)
            VALUES (?, ?, ?, ?, ?)
            """,
            (fecha, descripcion, referencia, usuario, total),
        )

        # Si self.conn está presente, cursor es un cursor sqlite
        try:
            return cursor.lastrowid
        except Exception:
            # db.execute devuelve lastrowid ya
            return cursor

    def agregar_detalle(self, asiento_id: int, cuenta_id: int, debe: float = 0, haber: float = 0, descripcion: str = None):
        return self._execute(
            """
            INSERT INTO detalle_asientos (asiento_id, cuenta_id, debe, haber, descripcion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asiento_id, cuenta_id, debe, haber, descripcion),
        )

    # Reportes básicos
    def libro_diario(self, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
        q = "SELECT * FROM asientos_contables"
        params = ()
        if fecha_inicio and fecha_fin:
            q = "SELECT * FROM asientos_contables WHERE fecha BETWEEN ? AND ? ORDER BY fecha"
            params = (fecha_inicio, fecha_fin)

        return self._fetchall(q, params)

    def detalles_asiento(self, asiento_id: int) -> List[Dict]:
        return self._fetchall(
            "SELECT da.*, c.codigo, c.nombre FROM detalle_asientos da JOIN cuentas_contables c ON c.id=da.cuenta_id WHERE da.asiento_id = ?",
            (asiento_id,)
        )

    def mayor_general(self, cuenta_id: int, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
        q = "SELECT * FROM detalle_asientos WHERE cuenta_id = ?"
        params = (cuenta_id,)
        if fecha_inicio and fecha_fin:
            q = (
                "SELECT da.* FROM detalle_asientos da JOIN asientos_contables a ON a.id=da.asiento_id"
                " WHERE da.cuenta_id = ? AND a.fecha BETWEEN ? AND ? ORDER BY a.fecha"
            )
            params = (cuenta_id, fecha_inicio, fecha_fin)

        return self._fetchall(q, params)

    def cuentas_para_balance(self) -> List[Dict]:
        return self._fetchall("SELECT * FROM cuentas_contables ORDER BY codigo")
