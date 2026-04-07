
import datetime
from backend.ventas import list_sales
from backend.deudas import list_debts
from collections import Counter
import json
from pathlib import Path
import pandas as pd
from .logs import registrar_log


def ventas_diarias(fecha=None, actor=None):
    if not fecha:
        fecha = str(datetime.date.today())
    
    ventas = list_sales()
    resultado = []
    for v in ventas:
        # Manejar tanto strings como objetos datetime
        v_fecha = v.get("fecha", "")
        if isinstance(v_fecha, str):
            v_fecha_str = v_fecha.split("T")[0] if "T" in v_fecha else v_fecha
        else:
            v_fecha_str = str(v_fecha)
        
        if v_fecha_str == fecha:
            resultado.append(v)
    
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_diarias",
        detalles={"fecha": fecha, "total_registros": len(resultado)}
    )
    return resultado


def ventas_mensuales(mes, anio, actor=None):
    result = []
    for v in list_sales():
        try:
            v_fecha_str = v.get("fecha", "").split("T")[0] if "T" in str(v.get("fecha", "")) else str(v.get("fecha", ""))
            v_fecha = datetime.datetime.strptime(v_fecha_str, "%Y-%m-%d")
            if v_fecha.month == mes and v_fecha.year == anio:
                result.append(v)
        except (ValueError, AttributeError):
            pass
    
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_mensuales",
        detalles={"mes": mes, "anio": anio, "total_registros": len(result)}
    )
    return result


def productos_mas_vendidos(actor=None):
    counter = Counter()
    for v in list_sales():
        for p in v.get("productos_vendidos", []):
            counter[p.get("nombre", "Desconocido")] += float(p.get("cantidad", 0))
    resultado = counter.most_common()
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_productos_mas_vendidos",
        detalles={"total_productos": len(resultado)}
    )
    return resultado


def deudas_clientes(actor=None):
    deudas = list_debts()
    if not deudas:
        df = pd.DataFrame(columns=["id", "cliente_id", "monto_total", "estado", "fecha"])
    else:
        df = pd.DataFrame(deudas)
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_deudas_clientes",
        detalles={"total_registros": len(df)}
    )
    return df