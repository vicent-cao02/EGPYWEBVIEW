# backend/logs.py
from datetime import datetime
from typing import List, Dict, Any
import json
from .db import get_connection

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

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs (usuario, accion, detalles, fecha)
            VALUES (?, ?, ?, ?)
        """, (usuario, accion, detalles, fecha))
        conn.commit()
    finally:
        conn.close()

# ---------------------------
# Listar todos los logs
# ---------------------------
def listar_logs() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY fecha DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def obtener_logs_usuario(username: str):
    """Devuelve los registros del historial de acciones de un usuario."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT usuario, accion, fecha, detalles
            FROM logs
            WHERE usuario = ?
            ORDER BY fecha DESC
            LIMIT 100
        """, (username,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()