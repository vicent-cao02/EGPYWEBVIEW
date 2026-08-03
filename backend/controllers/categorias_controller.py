from typing import List, Dict, Any, Optional

from backend import categorias as categorias_module


class CategoriasController:
    @staticmethod
    def list_categories() -> List[Dict[str, Any]]:
        return categorias_module.list_categories()

    @staticmethod
    def get_category(cat_id: int) -> Optional[Dict[str, Any]]:
        return categorias_module.get_category(cat_id)

    @staticmethod
    def agregar_categoria(nombre: str, usuario: str = None) -> str:
        return categorias_module.agregar_categoria(nombre, usuario)

    @staticmethod
    def editar_categoria(cat_id: int, nombre_nuevo: str, usuario: str = None) -> str:
        return categorias_module.editar_categoria(cat_id, nombre_nuevo, usuario)

    @staticmethod
    def eliminar_categoria(cat_id: int, usuario: str = None):
        return categorias_module.eliminar_categoria(cat_id, usuario)

    @staticmethod
    def list_products_by_category(categoria_id: int) -> list[dict]:
        return categorias_module.list_products_by_category(categoria_id)
