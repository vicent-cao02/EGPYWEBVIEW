
from .logs import registrar_log

class NotFoundError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        registrar_log(
            usuario=kwargs.get("actor", "sistema"),
            accion="exception_NotFoundError",
            detalles={"mensaje": str(args[0]) if args else ""}
        )

class ValidationError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        registrar_log(
            usuario=kwargs.get("actor", "sistema"),
            accion="exception_ValidationError",
            detalles={"mensaje": str(args[0]) if args else ""}
        )

class InsufficientStockError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        registrar_log(
            usuario=kwargs.get("actor", "sistema"),
            accion="exception_InsufficientStockError",
            detalles={"mensaje": str(args[0]) if args else ""}
        )
