import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

# ---------------------------
# Configuración SQLite
# ---------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "negocio.db")

def get_connection():
    """
    Devuelve una conexión SQLite con row_factory configurado para dict.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Habilitar foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para conexiones SQLite.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def test_connection():
    """
    Prueba la conexión a la base de datos SQLite.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Conexión SQLite exitosa - {count} productos encontrados")
        return True
    except Exception as e:
        print(f"❌ Error de conexión SQLite: {e}")
        return False

if __name__ == "__main__":
    test_connection()
