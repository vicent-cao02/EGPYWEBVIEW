# migrate_to_neon.py
import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Esquema de la base de datos (ajústalo a tus tablas actuales)
schema_sql = """
-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    ci VARCHAR(50),
    chapa VARCHAR(50)
);

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    precio NUMERIC(10,2) NOT NULL,
    cantidad INT NOT NULL
);

-- Tabla de ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id),
    total NUMERIC(10,2) NOT NULL,
    pagado NUMERIC(10,2) NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_pago VARCHAR(50)
);

-- Tabla de productos vendidos en cada venta
CREATE TABLE IF NOT EXISTS productos_vendidos (
    id SERIAL PRIMARY KEY,
    venta_id INT REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(id),
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    saldo NUMERIC(10,2) DEFAULT 0
);

-- Tabla de deudas
CREATE TABLE IF NOT EXISTS deudas (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id),
    venta_id INT REFERENCES ventas(id),
    monto_total NUMERIC(10,2) NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente'
);
"""

# Conectar a Neon y ejecutar esquema
try:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
    print("✅ Esquema migrado correctamente a Neon")
except Exception as e:
    print("❌ Error al migrar:", e)
