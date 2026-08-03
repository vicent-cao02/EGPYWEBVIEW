from typing import List, Dict, Any

from backend.repositories.logs_repository import LogsRepository


class LogsController:
    @staticmethod
    def listar_auditoria(limit: int = 100) -> List[Dict[str, Any]]:
        repo = LogsRepository()
        return repo.obtener_auditoria(limit=limit)

    @staticmethod
    def listar_logs() -> List[Dict[str, Any]]:
        repo = LogsRepository()
        return repo.listar_logs()

    @staticmethod
    def obtener_logs_usuario(username: str) -> List[Dict[str, Any]]:
        repo = LogsRepository()
        return repo.obtener_logs_usuario(username)
