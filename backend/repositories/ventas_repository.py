from typing import Dict, List, Optional

from backend.database import db



class VentasRepository:
    """
    Capa de acceso a datos de ventas.
    No contiene lógica de negocio.
    Soporta transacciones externas.
    """

    def __init__(self, conn=None):

        self.conn = conn



    # =====================================================
    # HELPERS
    # =====================================================

    def _execute(
        self,
        query,
        params=()
    ):

        if self.conn:

            cursor = self.conn.execute(
                query,
                params
            )

            return cursor


        with db.transaction() as conn:

            cursor = conn.execute(
                query,
                params
            )

            return cursor



    def _fetchall(
        self,
        query,
        params=()
    ):

        if self.conn:

            cursor = self.conn.execute(
                query,
                params
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]


        return db.fetchall(
            query,
            params
        )



    def _fetchone(
        self,
        query,
        params=()
    ):

        if self.conn:

            cursor = self.conn.execute(
                query,
                params
            )

            row = cursor.fetchone()

            return dict(row) if row else None


        return db.fetchone(
            query,
            params
        )



    # =====================================================
    # CONSULTAS
    # =====================================================

    def obtener_todas(self):

        return self._fetchall(
            """
            SELECT *
            FROM ventas
            ORDER BY fecha DESC
            """
        )



    def obtener_por_id(
        self,
        venta_id:int
    ):

        return self._fetchone(
            """
            SELECT *
            FROM ventas
            WHERE id=?
            """,
            (
                venta_id,
            )
        )



    def obtener_por_cliente(
        self,
        cliente_id:int
    ):

        return self._fetchall(
            """
            SELECT *
            FROM ventas
            WHERE cliente_id=?
            ORDER BY fecha DESC
            """,
            (
                cliente_id,
            )
        )



    def obtener_con_saldo(self):

        return self._fetchall(
            """
            SELECT *

            FROM ventas

            WHERE saldo > 0

            ORDER BY fecha DESC
            """
        )



    # =====================================================
    # CREAR
    # =====================================================

    def crear(
        self,
        datos:Dict
    ):

        cursor = self._execute(
            """
            INSERT INTO ventas
            (
                cliente_id,
                fecha,
                pagado,
                saldo,
                productos_vendidos,
                total,
                tipo_pago,
                usuario
            )

            VALUES
            (
                ?,?,?,?,?,?,?,?
            )
            """,
            (
                datos["cliente_id"],
                datos["fecha"],
                datos["pagado"],
                datos["saldo"],
                datos["productos_vendidos"],
                datos["total"],
                datos["tipo_pago"],
                datos["usuario"]
            )
        )


        return cursor.lastrowid



    # =====================================================
    # PAGOS
    # =====================================================

    def actualizar_pago(
        self,
        venta_id:int,
        pagado:float,
        saldo:float
    ):

        cursor=self._execute(
            """
            UPDATE ventas

            SET
                pagado=?,
                saldo=?

            WHERE id=?

            """,
            (
                pagado,
                saldo,
                venta_id
            )
        )


        return cursor.rowcount > 0



    # =====================================================
    # CAMPOS FACTURA
    # =====================================================

    def actualizar_extra(
        self,
        venta_id,
        observaciones=None,
        vendedor=None,
        telefono_vendedor=None,
        chofer=None,
        chapa=None
    ):

        cursor=self._execute(
            """
            UPDATE ventas

            SET
                observaciones=?,
                vendedor=?,
                telefono_vendedor=?,
                chofer=?,
                chapa=?

            WHERE id=?

            """,
            (
                observaciones,
                vendedor,
                telefono_vendedor,
                chofer,
                chapa,
                venta_id
            )
        )


        return cursor.rowcount > 0



    # =====================================================
    # ELIMINAR
    # =====================================================

    def eliminar(
        self,
        venta_id:int
    ):

        cursor=self._execute(
            """
            DELETE FROM ventas
            WHERE id=?
            """,
            (
                venta_id,
            )
        )


        return cursor.rowcount > 0