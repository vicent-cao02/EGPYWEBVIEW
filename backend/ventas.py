"""
Módulo de ventas mejorado con todas las características avanzadas.
Incluye:
- Facturación profesional con números secuenciales
- Control de stock
- Validación completa de productos
- Descuentos e impuestos configurables
- Múltiples métodos de pago
- Ventas a crédito
- Devoluciones
- Cancelación con auditoría
- Reportes completos
"""

from typing import Dict, List, Optional
import json

# Importaciones del módulo antiguo (mantener compatibilidad)
from backend.services.ventas_service import VentasService
from backend.repositories.ventas_repository import VentasRepository

# Importaciones del módulo nuevo
from backend.services.ventas_service_advanced import VentasServiceAdvanced
from backend.repositories.ventas_repository_advanced import VentasRepositoryAvanced
from backend.tipos_ventas import (
    Factura, ProductoVenta, PagoVenta, Devolucion,
    EstadoVenta, TipoVenta, MetodoPago
)
from backend.logs import registrar_log


# ==========================================================
# COMPATIBILIDAD CON API ANTIGUA
# ==========================================================

def register_sale(
    cliente_id: int,
    total: float,
    pagado: float,
    usuario: str,
    tipo_pago: str,
    productos: List[Dict]
):
    """API antigua - mantener para compatibilidad"""
    return VentasService.registrar_venta(
        cliente_id=cliente_id,
        total=total,
        pagado=pagado,
        usuario=usuario,
        tipo_pago=tipo_pago,
        productos=productos
    )


def list_sales():
    """API antigua - listar todas las ventas"""
    repo = VentasRepository()
    ventas = repo.obtener_todas()

    for venta in ventas:
        try:
            venta["productos_vendidos"] = json.loads(
                venta.get("productos_vendidos", "[]")
            )
        except Exception:
            venta["productos_vendidos"] = []

    return ventas


def get_sale(sale_id: int):
    """API antigua - obtener venta por ID"""
    repo = VentasRepository()
    venta = repo.obtener_por_id(sale_id)

    if not venta:
        return None

    try:
        venta["productos_vendidos"] = json.loads(
            venta.get("productos_vendidos", "[]")
        )
    except Exception:
        venta["productos_vendidos"] = []

    detalle = repo.obtener_detalles_por_venta(venta["id"])
    if detalle:
        venta["venta_detalle"] = detalle
    else:
        venta["venta_detalle"] = []

    return venta


# ==========================================================
# NUEVA API - VENTAS PROFESIONALES
# ==========================================================

# =========================================================
# CREAR VENTA
# =========================================================

def crear_venta(
    cliente_id: int,
    usuario: str,
    productos: List[Dict],
    tipo_venta: str = "CONTADO",
    metodo_pago: str = "EFECTIVO",
    pagado: float = 0.0,
    descuento_porcentaje: float = 0.0,
    referencia_pago: Optional[str] = None,
    observaciones: Optional[str] = None,
    vendedor: Optional[str] = None,
    telefono_vendedor: Optional[str] = None,
    chofer: Optional[str] = None,
    chapa: Optional[str] = None,
) -> Dict:
    """
    Crea una venta completa y profesional.

    Args:
        cliente_id: ID del cliente
        usuario: Usuario que registra la venta
        productos: Lista de productos con estructura [{"id_producto", "cantidad", "precio_unitario"}]
        tipo_venta: "CONTADO" o "CREDITO" (se determina automáticamente)
        metodo_pago: Método de pago: EFECTIVO, TARJETA_DEBITO, TARJETA_CREDITO, TRANSFERENCIA, CHEQUE
        pagado: Monto pagado (0 si es crédito)
        descuento_porcentaje: Descuento porcentual a aplicar
        referencia_pago: Referencia de pago (requerido para algunos métodos)
        observaciones: Observaciones adicionales
        vendedor: Nombre del vendedor
        telefono_vendedor: Teléfono del vendedor
        chofer: Nombre del chofer (si aplica)
        chapa: Chapa del vehículo (si aplica)

    Returns:
        Diccionario con datos de la venta creada, incluyendo número de factura

    Raises:
        ValueError: Si hay errores de validación

    Ejemplo:
        >>> venta = crear_venta(
        ...     cliente_id=1,
        ...     usuario='admin',
        ...     productos=[
        ...         {'id_producto': 1, 'cantidad': 2, 'precio_unitario': 100.00},
        ...         {'id_producto': 2, 'cantidad': 1, 'precio_unitario': 50.00}
        ...     ],
        ...     metodo_pago='EFECTIVO'
        ... )
    """
    return VentasServiceAdvanced.crear_venta(
        cliente_id=cliente_id,
        usuario=usuario,
        tipo_venta=tipo_venta,
        metodo_pago=metodo_pago,
        productos=productos,
        pagado=pagado,
        descuento_porcentaje=descuento_porcentaje,
        referencia_pago=referencia_pago,
        observaciones=observaciones,
        vendedor=vendedor,
        telefono_vendedor=telefono_vendedor,
        chofer=chofer,
        chapa=chapa,
    )


# =========================================================
# DEVOLUCIONES
# =========================================================

def crear_devolucion(
    venta_id: int,
    usuario: str,
    productos: List[Dict],
    motivo: str = "",
    observaciones: Optional[str] = None,
) -> Dict:
    """
    Crea una devolución de venta.

    Args:
        venta_id: ID de la venta original
        usuario: Usuario que registra la devolución
        productos: Productos a devolver [{"id_producto", "cantidad", "precio_unitario", "nombre"}]
        motivo: Motivo de la devolución
        observaciones: Observaciones adicionales

    Returns:
        Diccionario con datos de la devolución

    Raises:
        ValueError: Si la venta no existe o hay errores de validación

    Ejemplo:
        >>> dev = crear_devolucion(
        ...     venta_id=1,
        ...     usuario='admin',
        ...     productos=[{'id_producto': 1, 'cantidad': 1, 'precio_unitario': 100.0, 'nombre': 'Producto'}],
        ...     motivo='Producto defectuoso'
        ... )
    """
    return VentasServiceAdvanced.crear_devolucion(
        venta_id=venta_id,
        usuario=usuario,
        productos=productos,
        motivo=motivo,
        observaciones=observaciones,
    )


def obtener_devoluciones_venta(venta_id: int) -> List[Dict]:
    """Obtiene todas las devoluciones de una venta específica"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_devoluciones_venta(venta_id)


def obtener_devolucion(devolucion_id: int) -> Optional[Dict]:
    """Obtiene una devolución específica con sus detalles"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_devolucion(devolucion_id)


# =========================================================
# CANCELACIÓN CON AUDITORÍA
# =========================================================

def cancelar_venta(
    venta_id: int,
    usuario: str,
    motivo: str
) -> bool:
    """
    Cancela una venta con auditoría completa.
    Solo administradores pueden cancelar ventas.

    Args:
        venta_id: ID de la venta a cancelar
        usuario: Usuario que cancela (debe ser admin)
        motivo: Motivo de cancelación

    Returns:
        True si la cancelación fue exitosa

    Raises:
        ValueError: Si hay errores o la venta no puede cancelarse

    Ejemplo:
        >>> cancelar_venta(1, 'admin', 'Cancelada por error')
    """
    return VentasServiceAdvanced.cancelar_venta(venta_id, usuario, motivo)


def obtener_venta_cancelada(venta_id: int) -> Optional[Dict]:
    """Obtiene el registro de auditoría de una venta cancelada"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_venta_cancelada(venta_id)


def obtener_historial_cancelaciones() -> List[Dict]:
    """Obtiene el historial completo de cancelaciones de ventas"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_historial_cancelaciones()


# =========================================================
# FACTURACIÓN
# =========================================================

def obtener_venta_completa(venta_id: int) -> Optional[Dict]:
    """Obtiene una venta con todos sus detalles"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_venta_completa(venta_id)


def obtener_siguiente_numero_factura(tipo_venta: str = "CONTADO") -> str:
    """
    Obtiene el siguiente número de factura disponible.

    Args:
        tipo_venta: CONTADO, CREDITO o DEVOLUCION

    Returns:
        Número de factura en formato: FAC-000001

    Ejemplo:
        >>> numero = obtener_siguiente_numero_factura("CONTADO")
        >>> print(numero)
        'FAC-000001'
    """
    repo = VentasRepositoryAvanced()
    return repo.obtener_siguiente_numero_factura(tipo_venta)


# =========================================================
# IMPUESTOS
# =========================================================

def obtener_impuestos() -> List[Dict]:
    """Obtiene todos los impuestos configurados"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_impuestos()


def obtener_impuesto(nombre: str) -> Optional[Dict]:
    """Obtiene la configuración de un impuesto específico"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_impuesto(nombre)


def actualizar_impuesto(nombre: str, porcentaje: float, activo: bool = True) -> bool:
    """Actualiza la configuración de un impuesto"""
    repo = VentasRepositoryAvanced()
    return repo.actualizar_impuesto(nombre, porcentaje, activo)


def crear_impuesto(nombre: str, porcentaje: float) -> int:
    """Crea un nuevo impuesto configurado"""
    repo = VentasRepositoryAvanced()
    return repo.crear_impuesto(nombre, porcentaje)


# =========================================================
# MÉTODOS DE PAGO
# =========================================================

def obtener_metodos_pago(solo_activos: bool = True) -> List[Dict]:
    """
    Obtiene todos los métodos de pago configurados.

    Args:
        solo_activos: Si True, solo retorna métodos activos

    Returns:
        Lista de métodos de pago disponibles
    """
    repo = VentasRepositoryAvanced()
    return repo.obtener_metodos_pago(solo_activos)


def obtener_metodo_pago(nombre: str) -> Optional[Dict]:
    """Obtiene la configuración de un método de pago específico"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_metodo_pago(nombre)


def crear_metodo_pago(
    nombre: str,
    descripcion: str = "",
    requiere_referencia: bool = False
) -> int:
    """Crea un nuevo método de pago"""
    repo = VentasRepositoryAvanced()
    return repo.crear_metodo_pago(nombre, descripcion, requiere_referencia)


# =========================================================
# BÚSQUEDAS Y REPORTES
# =========================================================

def obtener_ventas_por_estado(estado: str) -> List[Dict]:
    """
    Obtiene ventas por estado.

    Args:
        estado: ACTIVA, PAGADA, PARCIALMENTE_PAGADA, CREDITO, CANCELADA, ANULADA

    Returns:
        Lista de ventas con ese estado
    """
    repo = VentasRepositoryAvanced()
    return repo.obtener_ventas_por_estado(estado)


def obtener_ventas_por_rango_fechas(fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """
    Obtiene ventas dentro de un rango de fechas.

    Args:
        fecha_inicio: Fecha inicio en formato YYYY-MM-DD
        fecha_fin: Fecha fin en formato YYYY-MM-DD

    Returns:
        Lista de ventas en ese período
    """
    repo = VentasRepositoryAvanced()
    return repo.obtener_ventas_por_rango_fechas(fecha_inicio, fecha_fin)


def obtener_ventas_sin_cobrar() -> List[Dict]:
    """
    Obtiene todas las ventas pendientes de cobro.

    Returns:
        Lista de ventas con saldo pendiente
    """
    repo = VentasRepositoryAvanced()
    return repo.obtener_ventas_sin_cobrar()


def obtener_resumen_ventas(fecha_inicio: str, fecha_fin: str) -> Dict:
    """
    Obtiene resumen completo de ventas en un período.

    Args:
        fecha_inicio: Fecha inicio en formato YYYY-MM-DD
        fecha_fin: Fecha fin en formato YYYY-MM-DD

    Returns:
        Diccionario con totales y desglose por método de pago
    """
    return VentasServiceAdvanced.obtener_resumen_ventas(fecha_inicio, fecha_fin)


def obtener_ventas_por_metodo_pago(fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
    """Agrupa ventas por método de pago"""
    repo = VentasRepositoryAvanced()
    return repo.obtener_ventas_por_metodo_pago(fecha_inicio, fecha_fin)



# =========================================================
# ACTUALIZAR PAGO
# =========================================================

def update_sale_payment(
    sale_id:int,
    pagado:float,
    saldo:float
):

    repo = VentasRepository()

    repo.actualizar_pago(
        sale_id,
        pagado,
        saldo
    )

    return True



# =========================================================
# EDITAR INFORMACIÓN EXTRA
# =========================================================

def editar_venta_extra(
    sale_id:int,
    observaciones=None,
    vendedor=None,
    telefono_vendedor=None,
    chofer=None,
    chapa=None,
    usuario=None
):

    repo = VentasRepository()


    repo.actualizar_extra(
        sale_id,
        observaciones,
        vendedor,
        telefono_vendedor,
        chofer,
        chapa
    )


    registrar_log(
        usuario or "system",
        "editar_venta_extra",
        {
            "venta": sale_id
        }
    )


    return True



# =========================================================
# ELIMINAR VENTA
# =========================================================

def delete_sale(
    sale_id:int,
    usuario:str=None
):

    repo = VentasRepository()


    repo.eliminar(
        sale_id
    )


    registrar_log(
        usuario or "system",
        "eliminar_venta",
        {
            "venta": sale_id
        }
    )


    return True



# =========================================================
# UTILIDAD UI
# =========================================================

def listar_ventas_dict():

    ventas = list_sales()


    return {

        f"Factura #{v['id']}":v

        for v in ventas

    }



# =========================================================
# PDF
# =========================================================

from backend.pdf.factura import generar_factura_pdf