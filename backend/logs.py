# backend/logs.py
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
import json
from .db import engine  # Función que devuelve conexión SQLAlchemy

# ---------------------------
# Registrar un log
# ---------------------------
def registrar_log(usuario: str, accion: str, detalles):
    """
    Registra una acción en la tabla de logs.
    Convierte dict o list a JSON string antes de guardar.
    """

    # Convertir detalles a JSON si es dict o list
    if isinstance(detalles, (dict, list)):
        detalles = json.dumps(detalles, default=str)

    # Asegurar que usuario sea string
    if isinstance(usuario, dict):
        usuario = usuario.get("username", "sistema")

    fecha = datetime.now()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO logs (usuario, accion, detalles, fecha)
                VALUES (:usuario, :accion, :detalles, :fecha)
            """),
            {
                "usuario": usuario,
                "accion": accion,
                "detalles": detalles,
                "fecha": fecha
            }
        )

# ---------------------------
# Listar todos los logs
# ---------------------------
def listar_logs() -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM logs ORDER BY fecha DESC"))
        return [dict(row) for row in result.fetchall()]


def obtener_logs_usuario(username: str):
    """Devuelve los registros del historial de acciones de un usuario."""
    query = text("""
        SELECT usuario, accion, fecha, detalles
        FROM logs
        WHERE usuario = :usuario
        ORDER BY fecha DESC
        LIMIT 100
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"usuario": username})
        return [row._asdict() for row in result]