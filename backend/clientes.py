from typing import Dict, Any, List, Optional

from backend.services.clientes_service import ClientesService


def get_client(cliente_id: int) -> Optional[Dict[str, Any]]:
    return ClientesService.get_client(cliente_id)


def add_client(nombre, telefono, ci, direccion, chapa, usuario=None):
    return ClientesService.add_client(nombre, telefono, ci, direccion, chapa, usuario)


def update_client(cliente_id: int, nombre=None, telefono=None, ci=None, chapa=None, direccion=None, usuario=None):
    return ClientesService.update_client(cliente_id, nombre, telefono, ci, chapa, direccion, usuario)


def delete_client(cliente_id: int, usuario: str = "sistema") -> bool:
    return ClientesService.delete_client(cliente_id, usuario)


def update_debt(cliente_id: int, monto: float, usuario: str = "sistema", conn=None) -> Dict[str, Any]:
    return ClientesService.update_debt(cliente_id, monto, usuario, conn=conn)


def list_clients() -> List[Dict[str, Any]]:
    return ClientesService.list_clients()


def edit_client(cliente_id: int, nombre: Optional[str] = None, telefono: Optional[str] = None,
                ci: Optional[str] = None, chapa: Optional[str] = None, direccion: Optional[str] = None,
                usuario: str = "sistema") -> Dict[str, Any]:
    return ClientesService.edit_client(cliente_id, nombre, telefono, ci, chapa, direccion, usuario)
