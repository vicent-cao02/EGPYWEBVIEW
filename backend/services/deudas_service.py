from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.logs import registrar_log_con_conn
from backend.repositories.deudas_repository import DeudasRepository
from backend.unit_of_work import UnitOfWork


class DeudasService:
    @staticmethod
    def list_debts() -> List[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.deudas.obtener_todas()

    @staticmethod
    def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.deudas.obtener_por_id(deuda_id)

    @staticmethod
    def add_debt(cliente_id: int, venta_id: Optional[int] = None, productos: Optional[List[Dict[str, Any]]] = None, monto_total: float = 0.0, estado: str = "pendiente", usuario: Optional[str] = None) -> int:
        with UnitOfWork() as uow:
            deuda_id = uow.deudas.crear(
                cliente_id=cliente_id,
                venta_id=venta_id,
                monto_total=monto_total,
                productos=productos,
                estado=estado,
                fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                descripcion=f"Deuda generada por venta #{venta_id}",
            )
            uow.clientes.actualizar_deuda_total(cliente_id, float(monto_total))
            registrar_log_con_conn(usuario or "sistema", "crear_deuda", {"id": deuda_id, "cliente_id": cliente_id, "monto_total": monto_total}, conn=uow.conn)
            return deuda_id

    @staticmethod
    def pay_debt_producto(deuda_id: int, producto_id: int, monto_pago: float, usuario=None) -> bool:
        with UnitOfWork() as uow:
            deuda = uow.deudas.obtener_por_id(deuda_id)
            if not deuda:
                raise Exception("Deuda no encontrada")

            detalle = next((d for d in deuda.get("detalles", []) if int(d["producto_id"]) == int(producto_id)), None)
            if not detalle:
                raise Exception("Producto no encontrado en la deuda")

            precio_unitario = float(detalle["precio_unitario"])
            cantidad_actual = float(detalle["cantidad"])
            cantidad_pagada = float(monto_pago) / precio_unitario if precio_unitario else 0
            nueva_cantidad = max(cantidad_actual - cantidad_pagada, 0)
            nuevo_estado = "pagado" if nueva_cantidad <= 0 else "pendiente"

            uow.deudas.actualizar_detalle(detalle["id"], nueva_cantidad, nuevo_estado)
            restante = uow.deudas.calcular_restante(deuda_id)
            estado_deuda = "pagada" if restante <= 0 else "pendiente"
            uow.deudas.actualizar_estado(deuda_id, estado_deuda, restante)
            uow.clientes.actualizar_deuda_total(deuda["cliente_id"], -float(monto_pago))

            venta_id = deuda.get("venta_id")
            if venta_id:
                venta = uow.ventas.obtener_por_id(venta_id)
                if venta:
                    nuevo_pagado = float(venta.get("total", 0)) - float(restante)
                    uow.ventas.actualizar_pago(venta_id, nuevo_pagado, restante)

            registrar_log_con_conn(usuario or "sistema", "pagar_deuda", {"deuda_id": deuda_id, "producto_id": producto_id, "monto_pago": monto_pago}, conn=uow.conn)
            return True

    @staticmethod
    def debts_by_client(cliente_id: int) -> List[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.deudas.obtener_por_cliente(cliente_id)

    @staticmethod
    def delete_debt(deuda_id: int, usuario: Optional[str] = None) -> bool:
        with UnitOfWork() as uow:
            deuda = uow.deudas.obtener_por_id(deuda_id)
            if not deuda:
                return False
            uow.deudas.eliminar(deuda_id)
            uow.clientes.actualizar_deuda_total(deuda["cliente_id"], -float(deuda.get("monto_total", 0)))
            registrar_log_con_conn(usuario or "sistema", "eliminar_deuda", {"id": deuda_id}, conn=uow.conn)
            return True

    @staticmethod
    def list_detalle_deudas() -> List[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.deudas.obtener_detalles()

    @staticmethod
    def list_clientes_con_deuda() -> List[Dict[str, Any]]:
        with UnitOfWork() as uow:
            return uow.deudas.obtener_clientes_con_deuda()
