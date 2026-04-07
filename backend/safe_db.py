# backend/safe_db.py
import sqlite3
from .errors import DatabaseConnectionError, DatabaseQueryError


def safe_execute(func, *args, **kwargs):
    """
    Ejecuta una función de BD de forma segura
    y transforma errores técnicos en errores controlados
    """
    try:
        return func(*args, **kwargs)

    except sqlite3.OperationalError as e:
        # Error de conexión o SQL (tabla no existe, columna inexistente, etc.)
        raise DatabaseQueryError(
            "Error al ejecutar la consulta en la base de datos"
        ) from e

    except sqlite3.DatabaseError as e:
        # Error general de BD
        raise DatabaseConnectionError(
            "No se pudo conectar con la base de datos"
        ) from e
