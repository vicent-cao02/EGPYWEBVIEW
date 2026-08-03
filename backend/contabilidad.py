from typing import List, Dict, Optional

from backend.repositories.contabilidad_repository import ContabilidadRepository


def registrar_asiento(conn, descripcion: str, referencia: str, usuario: str, movimientos: List[Dict]):
    repo = ContabilidadRepository(conn)
    # delega a servicio si es necesario, pero aquí usamos repo directamente
    # movimientos deben incluir 'codigo', 'debe' y/o 'haber'
    from backend.services.contabilidad_service import registrar_asiento_con_conn, ensure_default_accounts

    ensure_default_accounts(conn)

    return registrar_asiento_con_conn(conn, descripcion, referencia, usuario, movimientos)


def libro_diario(fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None) -> List[Dict]:
    repo = ContabilidadRepository()
    return repo.libro_diario(fecha_inicio, fecha_fin)


def mayor_general(cuenta_id: int, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None) -> List[Dict]:
    repo = ContabilidadRepository()
    return repo.mayor_general(cuenta_id, fecha_inicio, fecha_fin)


def balance_general() -> List[Dict]:
    repo = ContabilidadRepository()
    cuentas = repo.cuentas_para_balance()
    # calcular saldos básicos a partir de detalle_asientos
    result = []
    for c in cuentas:
        detalles = repo._fetchall(
            "SELECT SUM(debe) as debe, SUM(haber) as haber FROM detalle_asientos WHERE cuenta_id = ?",
            (c["id"],),
        )
        debe = detalles[0]["debe"] or 0 if detalles else 0
        haber = detalles[0]["haber"] or 0 if detalles else 0
        saldo = (debe - haber)
        result.append({"cuenta": c, "saldo": saldo})

    return result


def estado_resultados() -> Dict[str, float]:
    repo = ContabilidadRepository()
    # sumar cuentas tipo Ingresos y Gastos
    ingresos = repo._fetchall("SELECT id FROM cuentas_contables WHERE tipo = 'Ingresos'")
    gastos = repo._fetchall("SELECT id FROM cuentas_contables WHERE tipo = 'Gastos'")

    def suma(ids):
        if not ids:
            return 0
        placeholders = ",".join(["?"] * len(ids))
        q = f"SELECT SUM(debe) as debe, SUM(haber) as haber FROM detalle_asientos WHERE cuenta_id IN ({placeholders})"
        vals = tuple(i["id"] for i in ids)
        r = repo._fetchall(q, vals)
        if not r:
            return 0
        return (r[0].get("haber") or 0) - (r[0].get("debe") or 0)

    total_ingresos = suma(ingresos)
    total_gastos = suma(gastos)

    return {"ingresos": total_ingresos, "gastos": total_gastos, "resultado": total_ingresos - total_gastos}
