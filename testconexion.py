import psycopg2
from psycopg2 import OperationalError, sql

# URL de conexión a Neon PostgreSQL
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_BY8QzbZ1Vsmu@ep-calm-mouse-adgcgbq7-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

def test_connection():
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cursor = conn.cursor()
        
        # Ejecutar un SELECT simple
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("✅ Conexión exitosa a Neon PostgreSQL")
        print("⏰ Hora actual en la base de datos:", result[0])
        
        # Cerrar cursor y conexión
        cursor.close()
        conn.close()
        
    except OperationalError as e:
        print("❌ Error al conectar a Neon:", e)
    except Exception as e:
        print("❌ Error inesperado:", e)

if __name__ == "__main__":
    test_connection()