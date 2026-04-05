# backend/safe_db.py

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from .errors import DatabaseConnectionError, DatabaseQueryError


def safe_execute(func, *args, **kwargs):
    """
    Ejecuta una función de BD de forma segura
    y transforma errores técnicos en errores controlados
    """
    try:
        return func(*args, **kwargs)

    except OperationalError as e:
        # Error de conexión (Neon, Postgres, red, DNS, etc.)
        raise DatabaseConnectionError(
            "No se pudo conectar con la base de datos"
        ) from e

    except SQLAlchemyError as e:
        # Error SQL (query mal formada, columna inexistente, etc.)
        raise DatabaseQueryError(
            "Error al ejecutar la consulta en la base de datos"
        ) from e
