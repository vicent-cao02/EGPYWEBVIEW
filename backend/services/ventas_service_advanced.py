"""
Servicio mejorado de ventas con todas las características avanzadas.
Incluye:
- Validación completa de productos y stock
- Cálculo de descuentos e impuestos
- Métodos de pago configurables
- Control de ventas a crédito
- Devoluciones
- Cancelación con auditoría
- Generación de facturas profesionales
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

from backend.unit_of_work import UnitOfWork
from backend.repositories.ventas_repository_advanced import VentasRepositoryAvanced
from backend.logs import registrar_log_con_conn
from backend.tipos_ventas import (
    Factura, ProductoVenta, PagoVenta, Devolucion,
    EstadoVenta, TipoVenta, EstadoDevolucion
)


class VentasServiceAdvanced:
    """
    Servicio de negocio para ventas mejorado.
    Maneja la lógica completa de venta con todas las características avanzadas.
    """

    # =====================================================
    # VALIDACIONES
    # =====================================================

    @staticmethod
    def validar_cliente(cliente_id: int, uow: UnitOfWork) -> Dict:
        """Valida que el cliente exista"""
        cliente = uow.clientes.obtener_por_id(cliente_id)
        if not cliente:
            raise ValueError(f"Cliente {cliente_id} no existe.")
        return cliente

    @staticmethod
    def validar_producto(producto_id: int, uow: UnitOfWork) -> Dict:
        """Valida que el producto exista"""
        producto = uow.productos.obtener_por_id(producto_id)
        if not producto:
            raise ValueError(f"Producto {producto_id} no existe.")
        return producto

    @staticmethod
    def validar_stock_producto(
        producto: Dict,
        cantidad_requerida: float
    ) -> None:
        """Valida que haya stock suficiente"""
        stock_disponible = float(producto.get("cantidad", 0))
        if cantidad_requerida > stock_disponible:
            raise ValueError(
                f"Stock insuficiente para {producto['nombre']}. "
                f"Disponible: {stock_disponible}, Requerido: {cantidad_requerida}"
            )

    @staticmethod
    def validar_productos_venta(productos: List[Dict]) -> None:
        """Valida que la lista de productos sea válida"""
        if not productos or len(productos) == 0:
            raise ValueError("La venta debe contener al menos un producto.")

        for idx, producto in enumerate(productos, 1):
            if not producto.get("id_producto") and not producto.get("id"):
                raise ValueError(f"Producto {idx} sin ID.")

            cantidad = float(producto.get("cantidad", 0))
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida en producto {idx}.")

            precio = float(producto.get("precio_unitario", 0))
            if precio < 0:
                raise ValueError(f"Precio negativo en producto {idx}.")

    @staticmethod
    def validar_metodo_pago(
        metodo_pago: str,
        referencia_pago: Optional[str],
        repo: VentasRepositoryAvanced
    ) -> bool:
        """Valida que el método de pago sea válido y tenga referencia si procede"""
        metodo = repo.obtener_metodo_pago(metodo_pago)
        if not metodo or not metodo.get("activo"):
            raise ValueError(f"Método de pago '{metodo_pago}' no es válido.")

        if metodo.get("requiere_referencia") and not referencia_pago:
            raise ValueError(
                f"El método de pago '{metodo_pago}' requiere una referencia."
            )
        return True

    # =====================================================
    # CÁLCULOS DE FACTURA
    # =====================================================

    @staticmethod
    def calcular_descuento(
        subtotal: float,
        porcentaje_descuento: float
    ) -> float:
        """Calcula el monto de descuento"""
        if porcentaje_descuento < 0 or porcentaje_descuento > 100:
            raise ValueError("Porcentaje de descuento debe estar entre 0 y 100.")
        return round(subtotal * (porcentaje_descuento / 100), 2)

    @staticmethod
    def aplicar_impuesto(
        monto: float,
        porcentaje_impuesto: float
    ) -> float:
        """Calcula el monto de impuesto"""
        if porcentaje_impuesto < 0:
            raise ValueError("Porcentaje de impuesto no puede ser negativo.")
        return round(monto * (porcentaje_impuesto / 100), 2)

    @staticmethod
    def calcular_totales_factura(
        productos: List[ProductoVenta],
        descuento_porcentaje: float = 0,
        porcentaje_impuesto: float = 0
    ) -> Tuple[float, float, float, float]:
        """
        Calcula subtotal, descuento, impuesto y total de la factura.
        Retorna: (subtotal, descuento_total, impuesto_total, total)
        """
        subtotal = sum(p.subtotal for p in productos)

        # Aplicar descuento al subtotal
        descuento_total = round(subtotal * (descuento_porcentaje / 100), 2)
        monto_con_descuento = round(subtotal - descuento_total, 2)

        # Aplicar impuesto al monto con descuento
        impuesto_total = round(monto_con_descuento * (porcentaje_impuesto / 100), 2)

        total = round(monto_con_descuento + impuesto_total, 2)

        return subtotal, descuento_total, impuesto_total, total

    # =====================================================
    # CREAR VENTA COMPLETA
    # =====================================================

    @staticmethod
    def crear_venta(
        cliente_id: int,
        usuario: str,
        tipo_venta: str = "CONTADO",
        metodo_pago: str = "EFECTIVO",
        productos: List[Dict] = None,
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
        Crea una venta completa con validación y control transaccional.

        Args:
            cliente_id: ID del cliente
            usuario: Usuario que registra la venta
            tipo_venta: CONTADO o CREDITO
            metodo_pago: Método de pago empleado
            productos: Lista de productos con id, cantidad, precio_unitario
            pagado: Monto pagado (0 si es crédito)
            descuento_porcentaje: Descuento porcentual
            referencia_pago: Referencia del pago (p.ej. número de cheque)
            observaciones: Observaciones adicionales
            vendedor: Nombre del vendedor
            telefono_vendedor: Teléfono del vendedor
            chofer: Nombre del chofer
            chapa: Chapa del vehículo

        Returns:
            Diccionario con datos de la venta creada
        """
        if productos is None:
            productos = []

        # Validar datos básicos
        VentasServiceAdvanced.validar_productos_venta(productos)
        pagado = float(pagado) if pagado else 0.0
        descuento_porcentaje = float(descuento_porcentaje) if descuento_porcentaje else 0.0

        if descuento_porcentaje < 0 or descuento_porcentaje > 100:
            raise ValueError("Descuento debe estar entre 0 y 100%.")

        repo = VentasRepositoryAvanced()

        # Validar cliente y método de pago
        with UnitOfWork() as uow:
            VentasServiceAdvanced.validar_cliente(cliente_id, uow)
            VentasServiceAdvanced.validar_metodo_pago(metodo_pago, referencia_pago, repo)

            # Obtener impuesto configurado
            impuesto_config = repo.obtener_impuesto("IVA")
            porcentaje_impuesto = float(impuesto_config["porcentaje"]) if impuesto_config else 0.0

            # Procesar y validar productos
            productos_procesados = []
            for item in productos:
                producto_id = item.get("id_producto") or item.get("id")
                cantidad = float(item.get("cantidad", 0))
                precio_unitario = float(item.get("precio_unitario", 0))

                # Validar producto existe y tiene stock
                producto = VentasServiceAdvanced.validar_producto(producto_id, uow)
                VentasServiceAdvanced.validar_stock_producto(producto, cantidad)

                # Crear objeto ProductoVenta
                prod_venta = ProductoVenta(
                    id_producto=int(producto_id),
                    nombre=producto["nombre"],
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento=0,  # Descuento a nivel de factura, no por producto
                    impuesto=porcentaje_impuesto
                )

                productos_procesados.append(prod_venta)

            # Calcular totales
            subtotal, desc_total, imp_total, total = VentasServiceAdvanced.calcular_totales_factura(
                productos_procesados,
                descuento_porcentaje=descuento_porcentaje,
                porcentaje_impuesto=porcentaje_impuesto
            )

            # Validar monto pagado
            if pagado > total:
                raise ValueError(f"Pago ({pagado}) no puede superar el total ({total}).")

            # Determinar tipo de venta automáticamente
            if pagado >= total:
                tipo_venta_final = TipoVenta.CONTADO.value
            else:
                tipo_venta_final = TipoVenta.CREDITO.value

            # Crear venta en transacción
            venta_id = repo.crear_venta_completa(
                cliente_id=cliente_id,
                usuario=usuario,
                tipo_venta=tipo_venta_final,
                metodo_pago=metodo_pago,
                productos=[p.to_dict() for p in productos_procesados],
                pagado=pagado,
                observaciones=observaciones,
                vendedor=vendedor,
                telefono_vendedor=telefono_vendedor,
                chofer=chofer,
                chapa=chapa,
                referencia_pago=referencia_pago,
                descuento_total=desc_total,
                impuesto_total=imp_total,
            )

            # Descontar stock
            for prod in productos_procesados:
                uow.productos.descontar_stock(prod.id_producto, prod.cantidad)

            # Registrar deuda si es a crédito
            saldo = round(total - pagado, 2)
            if saldo > 0:
                uow.deudas.crear(
                    cliente_id=cliente_id,
                    venta_id=venta_id,
                    monto_total=saldo,
                    productos=[p.to_dict() for p in productos_procesados],
                )
                uow.clientes.actualizar_deuda_total(cliente_id, saldo)

            # Registrar en logs
            registrar_log_con_conn(
                usuario,
                "crear_venta",
                {
                    "venta_id": venta_id,
                    "cliente_id": cliente_id,
                    "tipo_venta": tipo_venta_final,
                    "subtotal": subtotal,
                    "descuento": desc_total,
                    "impuesto": imp_total,
                    "total": total,
                    "pagado": pagado,
                    "saldo": saldo,
                },
                conn=uow.conn,
            )

            return {
                "id": venta_id,
                "numero_factura": repo.obtener_venta_completa(venta_id)["numero_factura"],
                "cliente_id": cliente_id,
                "tipo_venta": tipo_venta_final,
                "subtotal": subtotal,
                "descuento_total": desc_total,
                "impuesto_total": imp_total,
                "total": total,
                "pagado": pagado,
                "saldo": saldo,
                "estado": EstadoVenta.PAGADA.value if saldo <= 0 else EstadoVenta.CREDITO.value,
                "productos": [p.to_dict() for p in productos_procesados],
            }

    # =====================================================
    # DEVOLUCIONES
    # =====================================================

    @staticmethod
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
            productos: Productos a devolver
            motivo: Motivo de la devolución
            observaciones: Observaciones adicionales

        Returns:
            Diccionario con datos de la devolución creada
        """
        repo = VentasRepositoryAvanced()
        VentasServiceAdvanced.validar_productos_venta(productos)

        with UnitOfWork() as uow:
            # Validar venta existe
            venta = repo.obtener_venta_completa(venta_id)
            if not venta:
                raise ValueError(f"Venta {venta_id} no existe.")

            cliente_id = venta["cliente_id"]

            # Procesar productos a devolver
            productos_devolucion = []
            for item in productos:
                producto_id = item.get("id_producto") or item.get("id")
                cantidad = float(item.get("cantidad", 0))
                precio_unitario = float(item.get("precio_unitario", 0))

                # Validar producto
                VentasServiceAdvanced.validar_producto(producto_id, uow)

                prod_dev = ProductoVenta(
                    id_producto=int(producto_id),
                    nombre=item.get("nombre", ""),
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                )

                productos_devolucion.append(prod_dev)

            # Crear devolución
            devolucion_id = repo.crear_devolucion(
                venta_id=venta_id,
                cliente_id=cliente_id,
                usuario=usuario,
                productos=[p.to_dict() for p in productos_devolucion],
                motivo=motivo,
                observaciones=observaciones,
            )

            # Restaurar stock
            for prod in productos_devolucion:
                # Incrementar stock
                producto = uow.productos.obtener_por_id(prod.id_producto)
                nuevo_stock = float(producto["cantidad"]) + prod.cantidad
                uow.productos.actualizar_stock(prod.id_producto, nuevo_stock)

            # Registrar en logs
            total_devolucion = sum(p.total for p in productos_devolucion)
            registrar_log_con_conn(
                usuario,
                "crear_devolucion",
                {
                    "devolucion_id": devolucion_id,
                    "venta_id": venta_id,
                    "cliente_id": cliente_id,
                    "total_devolucion": total_devolucion,
                    "motivo": motivo,
                },
                conn=uow.conn,
            )

            return {
                "id": devolucion_id,
                "numero_devolucion": repo.obtener_devolucion(devolucion_id)["numero_devolucion"],
                "venta_id": venta_id,
                "cliente_id": cliente_id,
                "motivo": motivo,
                "total_devolucion": total_devolucion,
                "productos": [p.to_dict() for p in productos_devolucion],
            }

    # =====================================================
    # CANCELACIÓN CON AUDITORÍA
    # =====================================================

    @staticmethod
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
            usuario: Usuario que cancela
            motivo: Motivo de cancelación

        Returns:
            True si la cancelación fue exitosa
        """
        if not motivo or len(motivo.strip()) == 0:
            raise ValueError("Debe especificar un motivo para cancelar la venta.")

        repo = VentasRepositoryAvanced()

        with UnitOfWork() as uow:
            # Obtener venta
            venta = repo.obtener_venta_completa(venta_id)
            if not venta:
                raise ValueError(f"Venta {venta_id} no existe.")

            # Validar que no esté ya cancelada
            if venta["estado"] == EstadoVenta.CANCELADA.value:
                raise ValueError(f"Venta {venta_id} ya está cancelada.")

            # Cancelar venta
            if not repo.cancelar_venta(venta_id, usuario, motivo):
                raise ValueError("Error al cancelar la venta.")

            # Restaurar stock de productos
            detalles = repo._fetchall(
                "SELECT * FROM venta_detalle WHERE venta_id = ?",
                (venta_id,)
            )

            for detalle in detalles:
                producto = uow.productos.obtener_por_id(detalle["producto_id"])
                nuevo_stock = float(producto["cantidad"]) + float(detalle["cantidad"])
                uow.productos.actualizar_stock(detalle["producto_id"], nuevo_stock)

            # Registrar en logs
            registrar_log_con_conn(
                usuario,
                "cancelar_venta",
                {
                    "venta_id": venta_id,
                    "cliente_id": venta["cliente_id"],
                    "motivo": motivo,
                    "total_revertido": venta["total"],
                },
                conn=uow.conn,
            )

            return True

    # =====================================================
    # REPORTES
    # =====================================================

    @staticmethod
    def obtener_resumen_ventas(
        fecha_inicio: str,
        fecha_fin: str
    ) -> Dict:
        """Obtiene resumen de ventas en un período"""
        repo = VentasRepositoryAvanced()
        totales = repo.obtener_total_ventas_por_periodo(fecha_inicio, fecha_fin)
        metodos = repo.obtener_ventas_por_metodo_pago(fecha_inicio, fecha_fin)

        return {
            "periodo": f"{fecha_inicio} a {fecha_fin}",
            "totales": totales,
            "por_metodo_pago": metodos,
        }
