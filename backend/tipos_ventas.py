"""
Tipos de datos, enums y estructuras para el módulo de ventas mejorado.
Define la estructura normalizada para ventas, devoluciones e impuestos.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ==========================================================
# ENUMS
# ==========================================================

class EstadoVenta(Enum):
    """Estados posibles de una venta"""
    ACTIVA = "ACTIVA"
    PAGADA = "PAGADA"
    PARCIALMENTE_PAGADA = "PARCIALMENTE_PAGADA"
    CREDITO = "CREDITO"
    CANCELADA = "CANCELADA"
    ANULADA = "ANULADA"


class TipoVenta(Enum):
    """Tipos de transacción de venta"""
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"
    DEVOLUCION = "DEVOLUCION"


class EstadoDevolucion(Enum):
    """Estados posibles de una devolución"""
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    PROCESADA = "PROCESADA"
    RECHAZADA = "RECHAZADA"


class MotivoDevolución(Enum):
    """Motivos válidos para una devolución"""
    DEFECTO = "DEFECTO"
    NO_CONFORME = "NO_CONFORME"
    ERROR_ORDEN = "ERROR_ORDEN"
    CAMBIO = "CAMBIO"
    OTROS = "OTROS"


class MetodoPago(Enum):
    """Métodos de pago disponibles"""
    EFECTIVO = "EFECTIVO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TRANSFERENCIA = "TRANSFERENCIA"
    CHEQUE = "CHEQUE"


# ==========================================================
# DATACLASSES
# ==========================================================

@dataclass
class ProductoVenta:
    """Producto dentro de una venta"""
    id_producto: int
    nombre: str
    cantidad: float
    precio_unitario: float
    descuento: float = 0.0
    impuesto: float = 0.0
    
    @property
    def subtotal(self) -> float:
        """Subtotal sin descuento ni impuesto"""
        return round(self.cantidad * self.precio_unitario, 2)
    
    @property
    def total_descuento(self) -> float:
        """Total de descuento en este producto"""
        return round(self.subtotal * (self.descuento / 100), 2)
    
    @property
    def subtotal_con_descuento(self) -> float:
        """Subtotal después de aplicar descuento"""
        return round(self.subtotal - self.total_descuento, 2)
    
    @property
    def total_impuesto(self) -> float:
        """Total de impuesto en este producto"""
        return round(self.subtotal_con_descuento * (self.impuesto / 100), 2)
    
    @property
    def total(self) -> float:
        """Total con descuento e impuesto"""
        return round(self.subtotal_con_descuento + self.total_impuesto, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id_producto": self.id_producto,
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "descuento": self.descuento,
            "impuesto": self.impuesto,
            "subtotal": self.subtotal,
            "total_descuento": self.total_descuento,
            "subtotal_con_descuento": self.subtotal_con_descuento,
            "total_impuesto": self.total_impuesto,
            "total": self.total,
        }


@dataclass
class PagoVenta:
    """Información de pago en una venta"""
    metodo: str  # MetodoPago
    monto: float
    referencia: Optional[str] = None
    fecha: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "metodo": self.metodo,
            "monto": self.monto,
            "referencia": self.referencia,
            "fecha": self.fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


@dataclass
class Factura:
    """Estructura de factura completa"""
    id: Optional[int] = None
    numero_factura: Optional[str] = None
    cliente_id: int = 0
    usuario: str = ""
    fecha: Optional[str] = None
    estado: str = EstadoVenta.ACTIVA.value
    tipo_venta: str = TipoVenta.CONTADO.value
    
    # Detalles de productos
    productos: List[ProductoVenta] = None
    
    # Cálculos
    subtotal: float = 0.0
    descuento_total: float = 0.0
    impuesto_total: float = 0.0
    total: float = 0.0
    
    # Pago
    pagos: List[PagoVenta] = None
    saldo_pendiente: float = 0.0
    
    # Campos opcionales
    observaciones: Optional[str] = None
    vendedor: Optional[str] = None
    telefono_vendedor: Optional[str] = None
    chofer: Optional[str] = None
    chapa: Optional[str] = None
    referencia_pago: Optional[str] = None
    
    def __post_init__(self):
        """Inicializar listas vacías"""
        if self.productos is None:
            self.productos = []
        if self.pagos is None:
            self.pagos = []
        if not self.fecha:
            self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def recalcular_totales(self):
        """Recalcular todos los totales"""
        if not self.productos:
            self.subtotal = 0.0
            self.descuento_total = 0.0
            self.impuesto_total = 0.0
            self.total = 0.0
            self.saldo_pendiente = 0.0
            return
        
        # Calcular subtotales
        self.subtotal = sum(p.subtotal for p in self.productos)
        self.descuento_total = sum(p.total_descuento for p in self.productos)
        self.impuesto_total = sum(p.total_impuesto for p in self.productos)
        
        # Total final
        self.total = sum(p.total for p in self.productos)
        
        # Saldo pendiente
        pagos_realizados = sum(p.monto for p in self.pagos)
        self.saldo_pendiente = round(self.total - pagos_realizados, 2)
    
    def agregar_producto(self, producto: ProductoVenta):
        """Agregar producto a la factura"""
        self.productos.append(producto)
        self.recalcular_totales()
    
    def agregar_pago(self, pago: PagoVenta):
        """Agregar pago a la factura"""
        self.pagos.append(pago)
        self.recalcular_totales()
        
        # Actualizar estado basado en saldo
        if self.saldo_pendiente <= 0:
            self.estado = EstadoVenta.PAGADA.value
        elif sum(p.monto for p in self.pagos) > 0:
            self.estado = EstadoVenta.PARCIALMENTE_PAGADA.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir factura a diccionario"""
        return {
            "id": self.id,
            "numero_factura": self.numero_factura,
            "cliente_id": self.cliente_id,
            "usuario": self.usuario,
            "fecha": self.fecha,
            "estado": self.estado,
            "tipo_venta": self.tipo_venta,
            "productos": [p.to_dict() for p in self.productos],
            "subtotal": self.subtotal,
            "descuento_total": self.descuento_total,
            "impuesto_total": self.impuesto_total,
            "total": self.total,
            "pagos": [p.to_dict() for p in self.pagos],
            "saldo_pendiente": self.saldo_pendiente,
            "observaciones": self.observaciones,
            "vendedor": self.vendedor,
            "telefono_vendedor": self.telefono_vendedor,
            "chofer": self.chofer,
            "chapa": self.chapa,
            "referencia_pago": self.referencia_pago,
        }


@dataclass
class Devolucion:
    """Estructura para devoluciones"""
    id: Optional[int] = None
    numero_devolucion: Optional[str] = None
    venta_id: int = 0
    cliente_id: int = 0
    usuario: str = ""
    fecha: Optional[str] = None
    motivo: str = ""
    estado: str = EstadoDevolucion.PENDIENTE.value
    observaciones: Optional[str] = None
    
    # Productos a devolver
    productos: List[ProductoVenta] = None
    
    # Totales
    total_devolucion: float = 0.0
    
    def __post_init__(self):
        """Inicializar listas vacías"""
        if self.productos is None:
            self.productos = []
        if not self.fecha:
            self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def recalcular_totales(self):
        """Recalcular total de devolución"""
        self.total_devolucion = sum(p.total for p in self.productos)
    
    def agregar_producto(self, producto: ProductoVenta):
        """Agregar producto a la devolución"""
        self.productos.append(producto)
        self.recalcular_totales()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "numero_devolucion": self.numero_devolucion,
            "venta_id": self.venta_id,
            "cliente_id": self.cliente_id,
            "usuario": self.usuario,
            "fecha": self.fecha,
            "motivo": self.motivo,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "productos": [p.to_dict() for p in self.productos],
            "total_devolucion": self.total_devolucion,
        }


@dataclass
class ConfiguracionImpuesto:
    """Configuración de impuestos del sistema"""
    id: Optional[int] = None
    nombre: str = ""
    porcentaje: float = 0.0
    activo: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "porcentaje": self.porcentaje,
            "activo": self.activo,
        }


@dataclass
class MetodoPagoConfig:
    """Configuración de métodos de pago"""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: Optional[str] = None
    requiere_referencia: bool = False
    activo: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "requiere_referencia": self.requiere_referencia,
            "activo": self.activo,
        }
