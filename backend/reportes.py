
import datetime
from backend.ventas import list_sales
from collections import Counter
import json
from pathlib import Path
import pandas as pd
from .logs import registrar_log


def ventas_diarias(fecha=None, actor=None):
    if not fecha:
        fecha = str(datetime.date.today())
    resultado = [v for v in list_sales() if v["fecha"] == fecha]
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_diarias",
        detalles={"fecha": fecha, "total_registros": len(resultado)}
    )
    return resultado

def ventas_mensuales(mes, anio, actor=None):
    result = []
    for v in list_sales():
        v_fecha = datetime.datetime.strptime(v["fecha"], "%Y-%m-%d")
        if v_fecha.month == mes and v_fecha.year == anio:
            result.append(v)
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_mensuales",
        detalles={"mes": mes, "anio": anio, "total_registros": len(result)}
    )
    return result

def productos_mas_vendidos(actor=None):
    counter = Counter()
    for v in list_sales():
        for p in v["productos_vendidos"]:
            counter[p["nombre"]] += p["cantidad"]
    resultado = counter.most_common()
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_productos_mas_vendidos",
        detalles={"total_productos": len(resultado)}
    )
    return resultado

def deudas_clientes(actor=None):
    with open("data/deudas.json", "r") as f:
        deudas = json.load(f)
    if not deudas:
        df = pd.DataFrame(columns=["id", "cliente_id", "monto", "estado", "fecha"])
    else:
        df = pd.DataFrame(deudas)
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_deudas_clientes",
        detalles={"total_registros": len(df)}
    )
    return df