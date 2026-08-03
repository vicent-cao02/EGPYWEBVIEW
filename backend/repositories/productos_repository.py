from typing import Dict, List, Optional

from backend.database import db


class ProductosRepository:
    """
    Repositorio encargado únicamente del acceso
    a la tabla productos.

    No contiene lógica de negocio.
    Solo CRUD e inventario básico.
    """


    def __init__(self, conn=None):

        # Conexión externa para transacciones
        # Si es None usa la capa db normal.
        self.conn = conn



    # =====================================================
    # MÉTODOS INTERNOS
    # =====================================================

    def _fetchall(
        self,
        query: str,
        params=()
    ) -> List[Dict]:


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
        query: str,
        params=()
    ) -> Optional[Dict]:


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



    def _execute(
        self,
        query: str,
        params=()
    ) -> int:


        if self.conn:

            cursor = self.conn.execute(
                query,
                params
            )

            return cursor.lastrowid


        return db.execute(
            query,
            params
        )



    # =====================================================
    # CONSULTAS
    # =====================================================


    def obtener_por_id(
        self,
        producto_id: int
    ) -> Optional[Dict]:

        return self._fetchone(
            """
            SELECT *

            FROM productos

            WHERE id=?
            """,
            (
                producto_id,
            )
        )



    def obtener_por_ids(
        self,
        ids: List[int]
    ) -> List[Dict]:


        if not ids:

            return []


        placeholders = ",".join(
            ["?"] * len(ids)
        )


        return self._fetchall(

            f"""
            SELECT *

            FROM productos

            WHERE id IN ({placeholders})
            """,

            tuple(ids)

        )



    def obtener_todos(self):

        return self._fetchall(

            """
            SELECT *

            FROM productos

            ORDER BY nombre
            """

        )



    # =====================================================
    # CONTROL DE INVENTARIO
    # =====================================================


    def descontar_stock(
        self,
        producto_id: int,
        cantidad: float
    ):


        self._execute(

            """
            UPDATE productos

            SET cantidad = cantidad - ?

            WHERE id=?

            """,

            (
                cantidad,
                producto_id
            )

        )



    def aumentar_stock(
        self,
        producto_id: int,
        cantidad: float
    ):


        self._execute(

            """
            UPDATE productos

            SET cantidad = cantidad + ?

            WHERE id=?

            """,

            (
                cantidad,
                producto_id
            )

        )



    def actualizar_stock(
        self,
        producto_id: int,
        cantidad: float
    ):


        self._execute(

            """
            UPDATE productos

            SET cantidad=?

            WHERE id=?

            """,

            (
                cantidad,
                producto_id
            )

        )



    # =====================================================
    # CRUD PRODUCTOS
    # =====================================================


    def crear(
        self,
        nombre,
        precio,
        cantidad,
        categoria_id
    ):


        return self._execute(

            """
            INSERT INTO productos
            (
                nombre,
                precio,
                cantidad,
                categoria_id
            )

            VALUES
            (
                ?,?,?,?
            )

            """,

            (
                nombre,
                precio,
                cantidad,
                categoria_id
            )

        )



    def actualizar(
        self,
        producto_id,
        nombre,
        precio,
        cantidad
    ):


        self._execute(

            """
            UPDATE productos

            SET

                nombre=?,

                precio=?,

                cantidad=?

            WHERE id=?

            """,

            (
                nombre,
                precio,
                cantidad,
                producto_id
            )

        )



    def eliminar(
        self,
        producto_id
    ):


        self._execute(

            """
            DELETE

            FROM productos

            WHERE id=?

            """,

            (
                producto_id,
            )

        )