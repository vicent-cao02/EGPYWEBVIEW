from typing import Dict, Any, List, Optional

from backend.logs import registrar_log
from backend.repositories.productos_repository import ProductosRepository
from backend.services.inventario_service import registrar_entrada, registrar_ajuste

repo = ProductosRepository()


def list_products() -> List[Dict[str, Any]]:
    return repo.obtener_todos()


def get_product(producto_id: int) -> Optional[Dict[str, Any]]:
    return repo.obtener_por_id(producto_id)


def crear_producto(
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: int,
    usuario: Optional[str] = None
) -> Dict[str, Any]:
    producto_id = repo.crear(nombre, precio, 0, categoria_id)
    producto = repo.obtener_por_id(producto_id)
    if usuario and producto:
        registrar_log(usuario, "crear_producto", producto)

    if cantidad and cantidad > 0:
        registrar_entrada(
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio,
            proveedor="Entrada inicial",
            numero_compra="INICIAL",
            usuario=usuario,
            observaciones="Entrada inicial al crear producto"
        )

    return producto


def guardar_producto(
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: int,
    usuario: Optional[str] = None
) -> Dict[str, Any]:
    return crear_producto(nombre, precio, cantidad, categoria_id, usuario)


def editar_producto(
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: int,
    usuario: Optional[str] = None
) -> Dict[str, Any]:
    producto_actual = repo.obtener_por_id(producto_id)
    if not producto_actual:
        raise ValueError("Producto no encontrado")

    stock_actual = producto_actual["cantidad"]
    producto = repo.actualizar(producto_id, nombre, precio, stock_actual, categoria_id)

    if cantidad != stock_actual:
        registrar_ajuste(
            producto_id=producto_id,
            cantidad_nueva=cantidad,
            razon="Ajuste por edición de producto",
            usuario=usuario,
            observaciones="Ajuste generado desde edición de producto"
        )

    producto = repo.obtener_por_id(producto_id)
    if usuario and producto:
        registrar_log(usuario, "editar_producto", producto)
    return producto


def eliminar_producto(producto_id: int, usuario: Optional[str] = None) -> bool:
    producto = repo.obtener_por_id(producto_id)
    if not producto:
        return False
    ok = repo.eliminar(producto_id)
    if usuario:
        registrar_log(usuario, "eliminar_producto", producto)
    return ok


def adjust_stock(product_id: int, cantidad_delta: int, usuario=None) -> Dict[str, Any]:
    producto = repo.obtener_por_id(product_id)
    if not producto:
        raise ValueError("Producto no encontrado")

    nuevo_stock = producto["cantidad"] + cantidad_delta
    if nuevo_stock < 0:
        raise ValueError("Stock insuficiente")

    repo.actualizar_stock(product_id, nuevo_stock)
    producto["cantidad"] = nuevo_stock

    if usuario:
        registrar_log(usuario, "ajustar_stock", {
            "producto_id": product_id,
            "antes": producto["cantidad"] - cantidad_delta,
            "despues": nuevo_stock,
            "delta": cantidad_delta
        })

    return producto


def increment_stock(producto_id: int, cantidad: int, usuario=None):
    return adjust_stock(producto_id, cantidad, usuario)


def map_productos():
    return {p["id"]: p["nombre"] for p in list_products()}
