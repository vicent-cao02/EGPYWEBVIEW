from typing import Any, Dict, Optional

from backend.logs import registrar_log, registrar_log_con_conn
from backend.repositories.clientes_repository import ClientesRepository
from backend.unit_of_work import UnitOfWork


class ClientesService:
    @staticmethod
    def get_client(cliente_id: int) -> Optional[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.clientes.obtener_por_id(cliente_id)

    @staticmethod
    def list_clients() -> list[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.clientes.obtener_todos()

    @staticmethod
    def add_client(nombre, telefono, ci, direccion, chapa, usuario=None):
        with UnitOfWork() as uow:
            cliente = uow.clientes.crear(nombre, telefono, ci, direccion, chapa)
            if usuario:
                registrar_log_con_conn(usuario, "crear_cliente", {"nombre": nombre, "telefono": telefono, "ci": ci, "direccion": direccion, "chapa": chapa}, conn=uow.conn)
            return cliente

    @staticmethod
    def update_client(cliente_id: int, nombre=None, telefono=None, ci=None, chapa=None, direccion=None, usuario=None):
        with UnitOfWork() as uow:
            cliente = uow.clientes.actualizar(cliente_id, nombre=nombre, telefono=telefono, ci=ci, chapa=chapa, direccion=direccion)
            if usuario:
                registrar_log_con_conn(usuario, "update_client", {"id": cliente_id}, conn=uow.conn)
            return cliente

    @staticmethod
    def delete_client(cliente_id: int, usuario: str = "sistema"):
        with UnitOfWork() as uow:
            ok = uow.clientes.eliminar(cliente_id)
            if usuario:
                registrar_log_con_conn(usuario, "delete_client", {"id": cliente_id}, conn=uow.conn)
            return ok

    @staticmethod
    def update_debt(cliente_id: int, monto: float, usuario: str = "sistema", conn=None):
        if conn is None:
            with UnitOfWork() as uow:
                cliente = uow.clientes.actualizar_deuda_total(cliente_id, monto)
                registrar_log_con_conn(usuario, "update_debt", {"id": cliente_id, "monto": monto}, conn=uow.conn)
                return cliente
        repo = ClientesRepository(conn)
        cliente = repo.actualizar_deuda_total(cliente_id, monto)
        registrar_log_con_conn(usuario, "update_debt", {"id": cliente_id, "monto": monto}, conn=conn)
        return cliente

    @staticmethod
    def edit_client(cliente_id: int, nombre: Optional[str] = None, telefono: Optional[str] = None, ci: Optional[str] = None, chapa: Optional[str] = None, direccion: Optional[str] = None, usuario: str = "sistema"):
        return ClientesService.update_client(cliente_id, nombre, telefono, ci, chapa, direccion, usuario)
