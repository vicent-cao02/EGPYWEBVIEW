from backend.services.deudas_service import DeudasService


def list_debts() -> list[dict]:
    """Retorna la lista de todas las deudas."""
    return DeudasService.list_debts()


def get_debt(deuda_id: int) -> dict | None:
    """Retorna los datos de una deuda por su ID."""
    return DeudasService.get_debt(deuda_id=deuda_id)


def add_debt(cliente_id: int, venta_id: int | None = None, productos: list[dict] | None = None, monto_total: float = 0.0, estado: str = "pendiente", usuario: str | None = None) -> int:
    """Registra una nueva deuda."""
    return DeudasService.add_debt(
        cliente_id=cliente_id,
        venta_id=venta_id,
        productos=productos,
        monto_total=monto_total,
        estado=estado,
        usuario=usuario,
    )


def debts_by_client(cliente_id: int) -> list[dict]:
    """Retorna las deudas de un cliente específico."""
    return DeudasService.debts_by_client(cliente_id=cliente_id)


def delete_debt(deuda_id: int, usuario: str | None = None) -> bool:
    """Elimina una deuda por su ID."""
    return DeudasService.delete_debt(deuda_id=deuda_id, usuario=usuario)


def pay_debt_producto(deuda_id: int, producto_id: int, monto_pago: float, usuario: str | None = None) -> bool:
    """Registra un pago de deuda sobre un producto específico."""
    return DeudasService.pay_debt_producto(deuda_id=deuda_id, producto_id=producto_id, monto_pago=monto_pago, usuario=usuario)


def list_detalle_deudas() -> list[dict]:
    """Retorna el detalle de las deudas."""
    return DeudasService.list_detalle_deudas()


def list_clientes_con_deuda() -> list[dict]:
    """Retorna los clientes que tienen deudas pendientes."""
    return DeudasService.list_clientes_con_deuda()
