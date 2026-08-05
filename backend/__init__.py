# Permite importar módulos desde backend
from .database import Database, db, get_connection

from .usuarios import (
    crear_usuario, autenticar_usuario, cambiar_password,
    requiere_cambio_password, activar_usuario, desactivar_usuario,
    obtener_logs_usuario, eliminar_usuario
)

from .productos import (
    list_products, get_product,
    adjust_stock, eliminar_producto, editar_producto, guardar_producto
)

from .clientes import (
    list_clients, add_client, update_client,
    delete_client, get_client, edit_client
)

from .ventas import (
    list_sales, get_sale, delete_sale,
    register_sale, listar_ventas_dict, editar_venta_extra
)

from .contabilidad import (
    registrar_asiento, libro_diario, mayor_general, balance_general, estado_resultados
)

from .deudas import (
    list_debts, get_debt, add_debt,
    debts_by_client, delete_debt, pay_debt_producto,
    list_detalle_deudas, list_clientes_con_deuda
)

from .categorias import (
    list_categories, get_category, agregar_categoria,
    editar_categoria, eliminar_categoria,
    list_products_by_category
)

from .logs import registrar_log
from .safe_db import safe_execute

from .services.inventario_service import (
    registrar_entrada,
    registrar_salida,
    registrar_ajuste,
    obtener_kardex_producto,
    obtener_kardex_completo,
    obtener_entradas,
    obtener_salidas,
    obtener_ajustes,
    obtener_config,
    configurar_stock_minimo,
    obtener_alertas,
    resolver_alerta,
)

from .errors import (
    AppError,
    DatabaseConnectionError,
    DatabaseQueryError,
    NotFoundError
)
