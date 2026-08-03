from datetime import datetime
from typing import List, Dict

from backend.repositories.contabilidad_repository import ContabilidadRepository
from backend.logs import registrar_log_con_conn


DEFAULT_ACCOUNTS = [
    # codigo, nombre, tipo
    ("1.1.1", "Caja", "Activo"),
    ("1.1.2", "Clientes", "Activo"),
    ("1.1.3", "Inventario", "Activo"),
    ("2.1.1", "Proveedores", "Pasivo"),
    ("3.1.1", "Patrimonio", "Patrimonio"),
    ("4.1.1", "Ventas", "Ingresos"),
    ("5.1.1", "Gastos", "Gastos"),
]


def ensure_default_accounts(conn):
    repo = ContabilidadRepository(conn)

    for codigo, nombre, tipo in DEFAULT_ACCOUNTS:
        repo.crear_cuenta(codigo, nombre, tipo)


def registrar_asiento_con_conn(conn, descripcion: str, referencia: str, usuario: str, movimientos: List[Dict]):
    """
    movimientos: list de dicts {codigo: str, debe: float, haber: float, descripcion: str}
    """
    repo = ContabilidadRepository(conn)

    # asegurar cuentas por defecto
    ensure_default_accounts(conn)

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = sum((m.get("debe", 0) or 0) for m in movimientos)

    asiento_id = repo.crear_asiento(fecha, descripcion, referencia, usuario, total)

    for m in movimientos:
        codigo = m["codigo"]
        cuenta = repo.obtener_por_codigo(codigo)
        if not cuenta:
            # crear cuenta mínima si no existe
            repo.crear_cuenta(codigo, codigo, "Activo")
            cuenta = repo.obtener_por_codigo(codigo)

        repo.agregar_detalle(
            asiento_id,
            cuenta["id"],
            m.get("debe", 0) or 0,
            m.get("haber", 0) or 0,
            m.get("descripcion"),
        )

    registrar_log_con_conn(usuario or "sistema", "registrar_asiento", {"asiento_id": asiento_id, "descripcion": descripcion}, conn=conn)

    return asiento_id
