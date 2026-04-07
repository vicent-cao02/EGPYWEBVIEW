# backend/historial.py
"""
Funciones para obtener historial de cambios por registro (entidad+id).
"""
from .logs import listar_logs


def historial_por_registro(entidad, id_registro):
    """
    Devuelve todos los logs relacionados con una entidad e id (ej: producto, cliente, venta, deuda).
    """
    logs = listar_logs()
    resultado = []
    for log in logs:
        detalles = log.get("detalles", {})
        
        # Si detalles es un string JSON, intentar parsearlo
        if isinstance(detalles, str):
            import json
            try:
                detalles = json.loads(detalles)
            except:
                detalles = {}
        
        if detalles.get(f"{entidad}_id") == id_registro or (detalles.get(entidad) and detalles[entidad].get("id") == id_registro):
            resultado.append(log)
    return resultado
