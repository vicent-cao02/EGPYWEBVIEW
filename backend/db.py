import sqlite3
import os
from contextlib import contextmanager

# ---------------------------
# Ruta a la base de datos SQLite
# ---------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "negocio.db")


# ---------------------------
# Función centralizada de conexión
# ---------------------------
def get_connection():
    """
    Devuelve una conexión SQLite a negocio.db con row_factory configurado.
    Las filas se devuelven como diccionarios.
    
    Uso:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        rows = cursor.fetchall()
        conn.close()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    conn.execute("PRAGMA foreign_keys = ON")  # Habilita foreign keys
    return conn


# ---------------------------
# Context manager para conexión (opcional, para comodidad)
# ---------------------------
@contextmanager
def get_db_connection():
    """
    Context manager para manejar la conexión automáticamente.
    
    Uso:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
            conn.commit()
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


# ---------------------------
# Función de prueba
# ---------------------------
def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM productos LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        print("✅ Conexión a SQLite exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


if __name__ == "__main__":
    test_connection()
