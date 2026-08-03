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
            return cursor

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

    def obtener_por_id(self, deuda_id: int) -> Optional[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT
                d.id,
                d.cliente_id,
                d.venta_id,
                d.monto_total,
                d.estado,
                d.fecha,
                d.descripcion,
                dd.id AS detalle_id,
                dd.producto_id,
                dd.cantidad,
                dd.precio_unitario,
                dd.estado AS estado_detalle
            FROM deudas d
            LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
            WHERE d.id = ?
            ORDER BY dd.id
            """,
            (deuda_id,),
        )

        if not rows:
            return None

        deuda = dict(rows[0])
        detalles = []

        for row in rows:
            if row["detalle_id"] is not None:
                detalles.append({
                    "id": row["detalle_id"],
                    "producto_id": row["producto_id"],
                    "cantidad": float(row["cantidad"]),
                    "precio_unitario": float(row["precio_unitario"]),
                    "estado": row["estado_detalle"],
                })

        deuda["detalles"] = detalles
        for key in ["detalle_id", "producto_id", "cantidad", "precio_unitario", "estado_detalle"]:
            deuda.pop(key, None)

        return deuda

    def obtener_todas(self) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT
                d.id,
                d.cliente_id,
                d.venta_id,
                d.monto_total,
                d.estado,
                d.fecha,
                d.descripcion
            FROM deudas d
            ORDER BY d.fecha DESC
            """
        )
        return rows

    def obtener_por_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT
                d.id,
                d.cliente_id,
                d.venta_id,
                d.monto_total,
                d.estado,
                d.fecha,
                d.descripcion,
                dd.id AS detalle_id,
                dd.producto_id,
                dd.cantidad,
                dd.precio_unitario,
                dd.estado AS estado_detalle
            FROM deudas d
            LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
            WHERE d.cliente_id = ?
            ORDER BY d.fecha DESC, dd.id
            """,
            (cliente_id,),
        )
        return self._map_deuda_rows(rows)

    def actualizar_detalle(self, detalle_id: int, cantidad: float, estado: str) -> None:
        self._execute(
            """
            UPDATE deudas_detalle
            SET cantidad = ?, estado = ?
            WHERE id = ?
            """,
            (cantidad, estado, detalle_id),
        )

    def calcular_restante(self, deuda_id: int) -> float:
        row = self._fetchone(
            """
            SELECT SUM(cantidad * precio_unitario) AS restante
            FROM deudas_detalle
            WHERE deuda_id = ?
              AND estado = 'pendiente'
            """,
            (deuda_id,),
        )
        return float(row["restante"] or 0)

    def actualizar_estado(self, deuda_id: int, estado: str, monto_total: float) -> None:
        self._execute(
            """
            UPDATE deudas
            SET estado = ?, monto_total = ?
            WHERE id = ?
            """,
            (str(estado).lower(), monto_total, deuda_id),
        )

    def eliminar(self, deuda_id: int) -> None:
        self._execute(
            """
            DELETE FROM deudas_detalle WHERE deuda_id = ?
            """,
            (deuda_id,),
        )
        self._execute(
            """
            DELETE FROM deudas WHERE id = ?
            """,
            (deuda_id,),
        )

    def obtener_detalles(self) -> List[Dict[str, Any]]:
        return self._fetchall(
            """
            SELECT
                dd.id AS detalle_id,
                dd.deuda_id,
                dd.producto_id,
                dd.cantidad,
                dd.precio_unitario,
                dd.estado,
                d.cliente_id,
                d.fecha,
                d.monto_total,
                d.estado AS estado_deuda
            FROM deudas_detalle dd
            JOIN deudas d ON d.id = dd.deuda_id
            ORDER BY d.fecha DESC
            """
        )

    def obtener_clientes_con_deuda(self) -> List[Dict[str, Any]]:
        return self._fetchall(
            """
            SELECT DISTINCT
                c.id,
                c.nombre,
                c.deuda_total
            FROM clientes c
            JOIN deudas d ON c.id = d.cliente_id
            WHERE LOWER(d.estado) = 'pendiente'
              AND c.deuda_total > 0
            ORDER BY c.nombre
            """
        )

    def _map_deuda_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deudas_map: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            deuda_id = row["id"]
            if deuda_id not in deudas_map:
                deudas_map[deuda_id] = {
                    "id": row["id"],
                    "cliente_id": row["cliente_id"],
                    "venta_id": row["venta_id"],
                    "monto_total": row["monto_total"],
                    "estado": row["estado"],
                    "fecha": row["fecha"],
                    "descripcion": row["descripcion"],
                    "detalles": [],
                }
            if row["detalle_id"] is not None:
                deudas_map[deuda_id]["detalles"].append({
                    "id": row["detalle_id"],
                    "producto_id": row["producto_id"],
                    "cantidad": float(row["cantidad"]),
                    "precio_unitario": float(row["precio_unitario"]),
                    "estado": row["estado_detalle"],
                })
        return list(deudas_map.values())

