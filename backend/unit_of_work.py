import sqlite3

from backend.database import get_connection
from backend.repositories.deudas_repository import DeudasRepository
from backend.repositories.productos_repository import ProductosRepository
from backend.repositories.ventas_repository import VentasRepository


class UnitOfWork:
    """
    Control centralizado de transacciones.

    Permite ejecutar varias operaciones
    como una sola operación contable.
    """

    def __init__(self):

        self.conn = None

    def __enter__(self):

        self.conn = get_connection()

        self.conn.row_factory = sqlite3.Row

        self.ventas = VentasRepository(self.conn)
        self.productos = ProductosRepository(self.conn)
        self.deudas = DeudasRepository(self.conn)

        return self

    def commit(self):

        if self.conn:
            self.conn.commit()

    def rollback(self):

        if self.conn:
            self.conn.rollback()

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        if exc_type:
            self.rollback()
        else:
            self.commit()

        if self.conn:
            self.conn.close()