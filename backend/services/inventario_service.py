"""
Servicio de inventario profesional.
Maneja la lógica de negocio para movimientos de inventario.
Nunca modifica el stock directamente - siempre a través de movimientos.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime

from backend.database import db
from backend.repositories.inventario_repository import InventarioRepository
from backend.logs import registrar_log


inv_repo = InventarioRepository()


# =====================================================
# MOVIMIENTOS DE ENTRADA
# =====================================================

def registrar_entrada(
    producto_id: int,
    cantidad: float,
    precio_unitario: Optional[float] = None,
    proveedor: Optional[str] = None,
    numero_compra: Optional[str] = None,
    usuario: Optional[str] = None,
    observaciones: Optional[str] = None
) -> Tuple[bool, Dict]:
    """
    Registra una entrada de inventario.
    Crea movimiento en Kardex y actualiza stock.
    """
    try:
        if cantidad <= 0:
            return False, {"error": "La cantidad debe ser mayor a 0"}

        # Conectar con transacción para atomicidad
        with db.transaction() as conn:
            # Obtener stock actual
            cursor = conn.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
            resultado = cursor.fetchone()

            if not resultado:
                return False, {"error": "Producto no encontrado"}

            stock_anterior = resultado[0]

            # Calcular nuevo stock
            stock_posterior = stock_anterior + cantidad

            # Crear movimiento en Kardex
            cursor = conn.execute(
                """
                INSERT INTO inventario_movimientos
                (producto_id, tipo, cantidad, stock_anterior, stock_posterior,
                 referencia, usuario, fecha, observaciones, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (producto_id, "ENTRADA", cantidad, stock_anterior, stock_posterior,
                 numero_compra, usuario, datetime.now().isoformat(), observaciones,
                 datetime.now().isoformat())
            )
            movimiento_id = cursor.lastrowid

            # Crear registro de entrada
            conn.execute(
                """
                INSERT INTO inventario_entradas
                (producto_id, cantidad, precio_unitario, proveedor, numero_compra,
                 usuario, fecha, observaciones, movimiento_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (producto_id, cantidad, precio_unitario, proveedor, numero_compra,
                 usuario, datetime.now().isoformat(), observaciones, movimiento_id)
            )

            # Actualizar stock en productos
            conn.execute(
                "UPDATE productos SET cantidad = ? WHERE id = ?",
                (stock_posterior, producto_id)
            )

        if usuario:
            registrar_log(usuario, "inventario_entrada", {
                "producto_id": producto_id,
                "cantidad": cantidad,
                "stock_anterior": stock_anterior,
                "stock_posterior": stock_posterior,
                "proveedor": proveedor
            })

        return True, {
            "movimiento_id": movimiento_id,
            "stock_anterior": stock_anterior,
            "stock_posterior": stock_posterior,
            "mensaje": f"Entrada registrada: +{cantidad} unidades"
        }

    except Exception as e:
        return False, {"error": str(e)}


# =====================================================
# MOVIMIENTOS DE SALIDA
# =====================================================

def registrar_salida(
    producto_id: int,
    cantidad: float,
    motivo: Optional[str] = None,
    numero_documento: Optional[str] = None,
    usuario: Optional[str] = None,
    observaciones: Optional[str] = None
) -> Tuple[bool, Dict]:
    """
    Registra una salida de inventario.
    Valida stock disponible y crea movimiento en Kardex.
    """
    try:
        if cantidad <= 0:
            return False, {"error": "La cantidad debe ser mayor a 0"}

        with db.transaction() as conn:
            # Obtener stock actual
            cursor = conn.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
            resultado = cursor.fetchone()

            if not resultado:
                return False, {"error": "Producto no encontrado"}

            stock_anterior = resultado[0]

            # Validar stock disponible
            if stock_anterior < cantidad:
                return False, {
                    "error": f"Stock insuficiente. Disponible: {stock_anterior}, Solicitado: {cantidad}"
                }

            # Calcular nuevo stock
            stock_posterior = stock_anterior - cantidad

            # Crear movimiento en Kardex
            cursor = conn.execute(
                """
                INSERT INTO inventario_movimientos
                (producto_id, tipo, cantidad, stock_anterior, stock_posterior,
                 referencia, usuario, fecha, observaciones, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (producto_id, "SALIDA", cantidad, stock_anterior, stock_posterior,
                 numero_documento, usuario, datetime.now().isoformat(), observaciones,
                 datetime.now().isoformat())
            )
            movimiento_id = cursor.lastrowid

            # Crear registro de salida
            conn.execute(
                """
                INSERT INTO inventario_salidas
                (producto_id, cantidad, motivo, numero_documento, usuario, fecha, observaciones, movimiento_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (producto_id, cantidad, motivo, numero_documento, usuario,
                 datetime.now().isoformat(), observaciones, movimiento_id)
            )

            # Actualizar stock en productos
            conn.execute(
                "UPDATE productos SET cantidad = ? WHERE id = ?",
                (stock_posterior, producto_id)
            )

        if usuario:
            registrar_log(usuario, "inventario_salida", {
                "producto_id": producto_id,
                "cantidad": cantidad,
                "stock_anterior": stock_anterior,
                "stock_posterior": stock_posterior,
                "motivo": motivo
            })

        # Verificar alertas de stock bajo
        _verificar_alertas_stock(producto_id, stock_posterior)

        return True, {
            "movimiento_id": movimiento_id,
            "stock_anterior": stock_anterior,
            "stock_posterior": stock_posterior,
            "mensaje": f"Salida registrada: -{cantidad} unidades"
        }

    except Exception as e:
        return False, {"error": str(e)}


# =====================================================
# AJUSTES DE INVENTARIO
# =====================================================

def registrar_ajuste(
    producto_id: int,
    cantidad_nueva: float,
    razon: Optional[str] = None,
    usuario: Optional[str] = None,
    observaciones: Optional[str] = None
) -> Tuple[bool, Dict]:
    """
    Registra un ajuste de inventario.
    Requiere cantidad actual = cantidad nueva.
    Crea movimiento de ajuste en Kardex.
    """
    try:
        if cantidad_nueva < 0:
            return False, {"error": "La cantidad no puede ser negativa"}

        with db.transaction() as conn:
            # Obtener stock actual
            cursor = conn.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
            resultado = cursor.fetchone()

            if not resultado:
                return False, {"error": "Producto no encontrado"}

            stock_anterior = resultado[0]

            # Si la cantidad es igual, no hay ajuste
            if stock_anterior == cantidad_nueva:
                return False, {"error": "No hay diferencia entre stock actual y nuevo"}

            # Calcular diferencia
            cantidad_ajuste = cantidad_nueva - stock_anterior

            # Crear movimiento en Kardex
            cursor = conn.execute(
                """
                INSERT INTO inventario_movimientos
                (producto_id, tipo, cantidad, stock_anterior, stock_posterior,
                 referencia, usuario, fecha, observaciones, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (producto_id, "AJUSTE", abs(cantidad_ajuste), stock_anterior, cantidad_nueva,
                 None, usuario, datetime.now().isoformat(), observaciones,
                 datetime.now().isoformat())
            )
            movimiento_id = cursor.lastrowid

            # Crear registro de ajuste
            conn.execute(
                """
                INSERT INTO inventario_ajustes
                (producto_id, cantidad_anterior, cantidad_nueva, cantidad_ajuste,
                 razon, usuario, fecha, observaciones, movimiento_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (producto_id, stock_anterior, cantidad_nueva, cantidad_ajuste,
                 razon, usuario, datetime.now().isoformat(), observaciones, movimiento_id)
            )

            # Actualizar stock en productos
            conn.execute(
                "UPDATE productos SET cantidad = ? WHERE id = ?",
                (cantidad_nueva, producto_id)
            )

        if usuario:
            registrar_log(usuario, "inventario_ajuste", {
                "producto_id": producto_id,
                "stock_anterior": stock_anterior,
                "stock_nuevo": cantidad_nueva,
                "diferencia": cantidad_ajuste,
                "razon": razon
            })

        # Verificar alertas de stock
        _verificar_alertas_stock(producto_id, cantidad_nueva)

        return True, {
            "movimiento_id": movimiento_id,
            "stock_anterior": stock_anterior,
            "stock_nuevo": cantidad_nueva,
            "diferencia": cantidad_ajuste,
            "mensaje": f"Ajuste registrado: {cantidad_ajuste:+.0f} unidades"
        }

    except Exception as e:
        return False, {"error": str(e)}


# =====================================================
# GESTIÓN DE ALERTAS
# =====================================================

def _verificar_alertas_stock(producto_id: int, stock_actual: float) -> None:
    """
    Verifica si un producto necesita alertas de stock bajo/crítico.
    Crea alertas automáticamente.
    """
    try:
        config = inv_repo.obtener_config_inventario(producto_id)
        if not config:
            return

        stock_minimo = config.get("stock_minimo", 5)

        # Eliminar alertas duplicadas del mismo tipo
        inv_repo.eliminar_alertas_duplicadas(producto_id, "STOCK_BAJO")
        inv_repo.eliminar_alertas_duplicadas(producto_id, "SIN_STOCK")

        # Crear alerta si no hay stock
        if stock_actual <= 0:
            inv_repo.crear_alerta(
                producto_id, "SIN_STOCK",
                f"Sin stock disponible",
                stock_actual, stock_minimo
            )
        # Crear alerta si está bajo mínimo
        elif stock_actual <= stock_minimo:
            inv_repo.crear_alerta(
                producto_id, "STOCK_BAJO",
                f"Stock bajo: {stock_actual} unidades. Mínimo: {stock_minimo}",
                stock_actual, stock_minimo
            )

    except Exception:
        pass  # No interrumpir el proceso si hay error en alertas


def obtener_alertas() -> Dict:
    """Obtiene todas las alertas activas de inventario."""
    try:
        alertas_activas = inv_repo.obtener_alertas_activas()
        return {
            "count": len(alertas_activas),
            "alertas": alertas_activas
        }
    except Exception as e:
        return {"error": str(e), "count": 0, "alertas": []}


def resolver_alerta(alerta_id: int, usuario: Optional[str] = None) -> Tuple[bool, Dict]:
    """Marca una alerta como resuelta."""
    try:
        if inv_repo.resolver_alerta(alerta_id, usuario):
            return True, {"mensaje": "Alerta resuelta"}
        else:
            return False, {"error": "No se pudo resolver la alerta"}
    except Exception as e:
        return False, {"error": str(e)}


# =====================================================
# CONFIGURACIÓN DE STOCK MÍNIMO
# =====================================================

def configurar_stock_minimo(
    producto_id: int,
    stock_minimo: float,
    stock_maximo: float,
    usuario: Optional[str] = None
) -> Tuple[bool, Dict]:
    """Configura el stock mínimo y máximo de un producto."""
    try:
        if stock_minimo < 0 or stock_maximo < 0:
            return False, {"error": "Las cantidades no pueden ser negativas"}

        if stock_minimo > stock_maximo:
            return False, {"error": "Stock mínimo no puede ser mayor que máximo"}

        config = inv_repo.obtener_config_inventario(producto_id)

        if config:
            inv_repo.actualizar_stock_minimo(producto_id, stock_minimo, stock_maximo)
        else:
            inv_repo.crear_config_inventario(producto_id, stock_minimo, stock_maximo)

        if usuario:
            registrar_log(usuario, "configurar_stock_minimo", {
                "producto_id": producto_id,
                "stock_minimo": stock_minimo,
                "stock_maximo": stock_maximo
            })

        return True, {"mensaje": "Configuración actualizada"}

    except Exception as e:
        return False, {"error": str(e)}


# =====================================================
# REPORTES Y KARDEX
# =====================================================

def obtener_kardex_producto(producto_id: int, limite: int = 100) -> Dict:
    """Obtiene el Kardex (historial de movimientos) de un producto."""
    try:
        movimientos = inv_repo.obtener_movimientos(producto_id, limite)
        return {
            "producto_id": producto_id,
            "total_movimientos": len(movimientos),
            "movimientos": movimientos
        }
    except Exception as e:
        return {"error": str(e), "movimientos": []}


def obtener_kardex_completo() -> Dict:
    """Obtiene el Kardex completo del sistema."""
    try:
        movimientos = inv_repo.obtener_kardex_completo()
        return {
            "total_movimientos": len(movimientos),
            "movimientos": movimientos
        }
    except Exception as e:
        return {"error": str(e), "movimientos": []}


def obtener_resumen_inventario() -> Dict:
    """Obtiene un resumen del estado general del inventario."""
    try:
        alertas = obtener_alertas()
        movimientos = inv_repo.obtener_kardex_completo()

        total_productos = len(set(m["producto_id"] for m in movimientos))
        total_movimientos = len(movimientos)

        return {
            "total_productos": total_productos,
            "total_movimientos": total_movimientos,
            "alertas_activas": alertas.get("count", 0),
            "movimientos_recientes": movimientos[:10]
        }
    except Exception as e:
        return {"error": str(e)}
