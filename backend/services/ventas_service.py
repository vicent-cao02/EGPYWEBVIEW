from datetime import datetime
import json
from typing import Dict, List

from backend.logs import registrar_log, registrar_log_con_conn
from backend.unit_of_work import UnitOfWork


class VentasService:
    """
    Capa de negocio para ventas.

    Responsabilidades:
    - Validar venta
    - Validar productos
    - Controlar stock
    - Registrar venta
    - Mantener consistencia transaccional

    No ejecuta SQL directamente.
    """

    @staticmethod
    def registrar_venta(
        cliente_id: int,
        total: float,
        pagado: float,
        usuario: str,
        tipo_pago: str,
        productos: List[Dict]
    ) -> Dict:

        # ==========================================
        # VALIDACIONES GENERALES
        # ==========================================

        if not cliente_id:
            raise ValueError("Debe seleccionar un cliente.")

        if not productos:
            raise ValueError("La venta no contiene productos.")

        total = round(float(total), 2)
        pagado = round(float(pagado), 2)

        if total <= 0:
            raise ValueError("El total debe ser mayor que cero.")

        if pagado < 0:
            raise ValueError("El pago no puede ser negativo.")

        if pagado > total:
            raise ValueError("El pago no puede superar el total.")

        saldo = round(total - pagado, 2)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        productos_final = []

        # ==========================================
        # TRANSACCIÓN COMPLETA
        # ==========================================

        with UnitOfWork() as uow:

            ids_productos = []

            for item in productos:
                producto_id = item.get("id_producto") or item.get("id")
                if not producto_id:
                    raise ValueError("Producto sin ID.")
                ids_productos.append(int(producto_id))

            productos_db = uow.productos.obtener_por_ids(ids_productos)
            mapa_productos = {p["id"]: p for p in productos_db}

            for item in productos:
                producto_id = int(item.get("id_producto") or item.get("id"))
                cantidad = float(item.get("cantidad", 0))
                precio = float(item.get("precio_unitario", 0))

                if cantidad <= 0:
                    raise ValueError("Cantidad inválida.")

                if producto_id not in mapa_productos:
                    raise ValueError(f"Producto {producto_id} no existe.")

                producto = mapa_productos[producto_id]
                stock = float(producto["cantidad"])

                if cantidad > stock:
                    raise ValueError(
                        f"Stock insuficiente: {producto['nombre']} (Disponible {stock})"
                    )

                uow.productos.descontar_stock(producto_id, cantidad)

                productos_final.append({
                    "id_producto": producto_id,
                    "nombre": producto["nombre"],
                    "cantidad": cantidad,
                    "precio_unitario": precio,
                    "subtotal": round(cantidad * precio, 2),
                })

            venta_id = uow.ventas.crear({
                "cliente_id": cliente_id,
                "fecha": fecha,
                "pagado": pagado,
                "saldo": saldo,
                "productos_vendidos": json.dumps(productos_final, ensure_ascii=False),
                "total": total,
                "tipo_pago": tipo_pago,
                "usuario": usuario,
                "detalle_productos": productos_final,
            })

            if saldo > 0:
                uow.deudas.crear(
                    cliente_id=cliente_id,
                    venta_id=venta_id,
                    monto_total=saldo,
                    productos=productos_final,
                )

                uow.clientes.actualizar_deuda_total(cliente_id, saldo)

            registrar_log_con_conn(
                usuario,
                "registrar_venta",
                {
                    "venta_id": venta_id,
                    "cliente_id": cliente_id,
                    "total": total,
                    "pagado": pagado,
                    "saldo": saldo,
                },
                conn=uow.conn,
            )

            # ==========================
            # Registro contable
            # Debe: Caja (por lo pagado) y/o Clientes (por saldo)
            # Haber: Ventas (por el total)
            # ==========================

            try:
                from backend.services.contabilidad_service import registrar_asiento_con_conn, ensure_default_accounts

                # asegurar cuentas básicas
                ensure_default_accounts(uow.conn)

                movimientos = []

                if pagado and pagado > 0:
                    movimientos.append({"codigo": "1.1.1", "debe": pagado, "descripcion": f"Cobro venta {venta_id}"})

                if saldo and saldo > 0:
                    movimientos.append({"codigo": "1.1.2", "debe": saldo, "descripcion": f"Cuenta por cobrar venta {venta_id}"})

                # Haber ventas por el total
                movimientos.append({"codigo": "4.1.1", "haber": total, "descripcion": f"Venta {venta_id}"})

                registrar_asiento_con_conn(
                    uow.conn,
                    descripcion=f"Venta #{venta_id}",
                    referencia=str(venta_id),
                    usuario=usuario,
                    movimientos=movimientos,
                )
            except Exception:
                # No queremos que un fallo contable rompa la venta; loguear y seguir
                pass

            return {
                "id": venta_id,
                "cliente_id": cliente_id,
                "total": total,
                "pagado": pagado,
                "saldo": saldo,
                "productos": productos_final,
                "estado": "pagada" if saldo == 0 else "pendiente",
            }