#!/usr/bin/env python3
"""
Migra datos desde una base Postgres (Neon) a `negocio.db` SQLite local.
Se espera que la URL de conexión esté en la variable de entorno `DATABASE_URL` o en `.env`.

Uso:
  export DATABASE_URL="postgresql://..."
  python scripts/migrate_from_neon.py

El script intenta copiar tablas comunes; si una tabla no existe en Neon la omite.
"""

import os
import sys
import sqlite3
from pathlib import Path

try:
    import pandas as pd
except Exception:
    print("Pandas no está instalado. Instálalo con: pip install pandas")
    sys.exit(1)

try:
    import psycopg2
except Exception:
    print("psycopg2 no está instalado. Instálalo con: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: No se encontró DATABASE_URL en las variables de entorno o en .env")
    sys.exit(1)

BASE = Path(__file__).resolve().parent.parent
SQLITE_PATH = BASE / "negocio.db"

# Tablas a migrar (ordenadas para evitar FK temporales)
tablas = [
    "categorias",
    "clientes",
    "usuarios",
    "productos",
    "ventas",
    "venta_detalle",
    "deudas",
    "deudas_detalle",
    "pagos_deuda",
    "logs",
    "auditoria"
]

print("Conectando a Neon (Postgres)...")
pg_conn = psycopg2.connect(DATABASE_URL)
pg_conn.autocommit = True

print(f"Conectando a SQLite en {SQLITE_PATH}...")
if SQLITE_PATH.exists():
    print("La base local existe y será sobrescrita: se recomienda tener backup antes de ejecutar.")

sqlite_conn = sqlite3.connect(str(SQLITE_PATH))

# Desactivar temporalmente foreign keys en SQLite mientras migramos
sqlite_conn.execute("PRAGMA foreign_keys=OFF;")

for tabla in tablas:
    print(f"\nMigrando tabla: {tabla}")
    try:
        df = pd.read_sql(f"SELECT * FROM {tabla};", pg_conn)
    except Exception as e:
        print(f"  ⚠️ Omitiendo {tabla}: no existe o error: {e}")
        continue

    if df.empty:
        print(f"  ⚠️ {tabla} vacía")
        try:
            df.to_sql(tabla, sqlite_conn, if_exists='replace', index=False)
        except Exception:
            pass
        continue

    # Normalizar tipos simples y nulos
    df = df.where(pd.notnull(df), None)

    # Serializar listas/dicts a JSON para evitar errores al insertar en sqlite
    for col in df.columns:
        if df[col].dtype == object:
            try:
                # comprobar si hay listas/dicts en la columna
                if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                    df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
            except Exception:
                pass

    try:
        df.to_sql(tabla, sqlite_conn, if_exists='replace', index=False)

        # Si la tabla tiene una columna 'id', recrearla para que 'id' sea PRIMARY KEY
        if 'id' in df.columns:
            try:
                cols = ', '.join([f'"{c}"' for c in df.columns if c != 'id'])
                sqlite_conn.execute('BEGIN')
                sqlite_conn.execute(f'CREATE TABLE IF NOT EXISTS {tabla}_new (id INTEGER PRIMARY KEY, {cols});')
                sqlite_conn.execute(f'INSERT INTO {tabla}_new (id, {cols}) SELECT id, {cols} FROM {tabla};')
                sqlite_conn.execute(f'DROP TABLE {tabla};')
                sqlite_conn.execute(f'ALTER TABLE {tabla}_new RENAME TO {tabla};')
                sqlite_conn.execute('COMMIT')
            except Exception as e:
                sqlite_conn.execute('ROLLBACK')
                print(f"  ⚠️ No se pudo establecer PK en {tabla}: {e}")

        print(f"  ✅ {tabla}: {len(df)} registros migrados")
    except Exception as e:
        print(f"  ❌ Error al volcar {tabla} a sqlite: {e}")

# Reactivar foreign keys
a = sqlite_conn.execute("PRAGMA foreign_keys=ON;")

pg_conn.close()
sqlite_conn.close()

print("\nMigración finalizada.")
print("Ejecuta `python scripts/migrate_from_neon.py` con `DATABASE_URL` configurada.")
