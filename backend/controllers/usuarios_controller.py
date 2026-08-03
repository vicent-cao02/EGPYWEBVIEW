from typing import List, Dict, Any, Optional

from backend import usuarios as usuarios_module


class UsuariosController:
    @staticmethod
    def listar_usuarios() -> List[Dict[str, Any]]:
        return usuarios_module.listar_usuarios()

    @staticmethod
    def crear_usuario(username: str, password: str, rol: str = "empleado", actor: Optional[str] = None) -> Dict[str, Any]:
        return usuarios_module.crear_usuario(username, password, rol, actor)

    @staticmethod
    def autenticar_usuario(username: str, password: str):
        return usuarios_module.autenticar_usuario(username, password)

    @staticmethod
    def cambiar_password(username: str, new_password: str, actor: Optional[str] = None):
        return usuarios_module.cambiar_password(username, new_password, actor)

    @staticmethod
    def cambiar_rol(username: str, nuevo_rol: str, actor: Optional[str] = None):
        return usuarios_module.cambiar_rol(username, nuevo_rol, actor)

    @staticmethod
    def activar_usuario(username: str, actor: Optional[str] = None):
        return usuarios_module.activar_usuario(username, actor)

    @staticmethod
    def desactivar_usuario(username: str, actor: Optional[str] = None):
        return usuarios_module.desactivar_usuario(username, actor)

    @staticmethod
    def eliminar_usuario(username: str, actor: Optional[str] = None):
        return usuarios_module.eliminar_usuario(username, actor)
