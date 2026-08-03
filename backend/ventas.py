from typing import Dict, List, Optional

from backend.services.ventas_service import VentasService
from backend.repositories.ventas_repository import VentasRepository

from backend.logs import registrar_log


# =========================================================
# REGISTRAR VENTA
# =========================================================

def register_sale(
    cliente_id: int,
    total: float,
    pagado: float,
    usuario: str,
    tipo_pago: str,
    productos: List[Dict]
):

    return VentasService.registrar_venta(
        cliente_id=cliente_id,
        total=total,
        pagado=pagado,
        usuario=usuario,
        tipo_pago=tipo_pago,
        productos=productos
    )


# =========================================================
# LISTAR VENTAS
# =========================================================

def list_sales():

    repo = VentasRepository()

    ventas = repo.obtener_todas()


    for venta in ventas:

        try:
            import json

            venta["productos_vendidos"] = json.loads(
                venta.get(
                    "productos_vendidos",
                    "[]"
                )
            )

        except Exception:

            venta["productos_vendidos"] = []


    return ventas



# =========================================================
# OBTENER VENTA
# =========================================================

def get_sale(
    sale_id:int
):

    repo = VentasRepository()

    venta = repo.obtener_por_id(
        sale_id
    )


    if not venta:

        return None


    try:

        import json

        venta["productos_vendidos"] = json.loads(
            venta.get(
                "productos_vendidos",
                "[]"
            )
        )

    except:

        venta["productos_vendidos"] = []


    return venta



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

try:
    from backend.reports.factura import generar_factura_pdf
except ImportError:  # pragma: no cover - compatibilidad si el módulo no existe
    def generar_factura_pdf(*args, **kwargs):
        raise ImportError("Módulo de factura no disponible")