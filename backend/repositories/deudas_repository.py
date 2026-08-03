from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.database import db


class DeudasRepository:
    """Repositorio para la tabla deudas y deudas_detalle."""

    def __init__(self, conn=None):
        self.conn = conn

    def _execute(self, query: str, params=()):
        if self.conn:
            return self.conn.execute(query, params)

        with db.transaction() as conn:
            cursor = conn.execute(query, params)
            if query.lstrip().upper().startswith("SELECT"):
                return cursor
            return cursor.lastrowid

    def _fetchall(self, query: str, params=()) -> List[Dict[str, Any]]:
        if self.conn:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        return db.fetchall(query, params)

    def _fetchone(self, query: str, params=()) -> Optional[Dict[str, Any]]:
        if self.conn:
            cursor = self.conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

        return db.fetchone(query, params)

    def crear(
        self,
        cliente_id: Optional[int] = None,
        venta_id: Optional[int] = None,
        monto_total: float = 0.0,
        productos: Optional[List[Dict[str, Any]]] = None,
        estado: str = "pendiente",
        fecha: Optional[str] = None,
        descripcion: Optional[str] = None,
    ) -> int:
        if isinstance(cliente_id, dict):
            data = cliente_id
            cliente_id = data.get("cliente_id")
            venta_id = data.get("venta_id")
            monto_total = data.get("monto_total", 0.0)
            productos = data.get("productos") or []
            estado = data.get("estado", "pendiente")
            fecha = data.get("fecha")
            descripcion = data.get("descripcion")

        fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        descripcion = descripcion or f"Deuda generada por venta #{venta_id}"

        cursor = self._execute(
            """
            INSERT INTO deudas (
                cliente_id,
                venta_id,
                monto_total,
                estado,
                fecha,
                descripcion
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                venta_id,
                float(monto_total),
                str(estado).lower(),
                fecha,
                descripcion,
            ),
        )

        deuda_id = cursor.lastrowid

        if productos:
            for item in productos:
                self._execute(
                    """
                    INSERT INTO deudas_detalle (
                        deuda_id,
                        producto_id,
                        cantidad,
                        precio_unitario,
                        estado
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        deuda_id,
                        item.get("id_producto") or item.get("id"),
                        float(item.get("cantidad", 0)),
                        float(item.get("precio_unitario", 0)),
                        "pendiente",
                    ),
                )

        return deuda_id
