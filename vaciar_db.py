import sqlite3
import os

DB_PATH = "negocio.db"

def vaciar_base_datos():
    if not os.path.exists(DB_PATH):
        print("❌ La base de datos no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Desactivar restricciones de claves foráneas
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Vaciar cada tabla
        for (table,) in tables:
            if table == "sqlite_sequence":
                continue
            print(f"🧹 Vaciando tabla: {table}")
            cursor.execute(f"DELETE FROM {table};")

        # Reiniciar autoincrementos
        cursor.execute("DELETE FROM sqlite_sequence;")

        # Reactivar foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        conn.commit()
        print("✅ Base de datos vaciada correctamente.")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    vaciar_base_datos()