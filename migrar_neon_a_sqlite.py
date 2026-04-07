"""
DEPRECATED - Script histórico de migración de PostgreSQL (Neon) a SQLite
Este archivo ya no es necesario ya que toda la aplicación ha sido refactorizada a SQLite.

Para usar este script (si es necesario), instala psycopg2:
    pip install psycopg2

Sin embargo, la aplicación ya está completamente funcionando con SQLite local.
"""

# import pandas as pd
# import sqlite3
# import psycopg2

# # =========================================
# # 🔌 CONEXIÓN NEON (MISMA QUE TU TEST)
# # =========================================
# NEON_DATABASE_URL = "postgresql://neondb_owner:npg_BY8QzbZ1Vsmu@ep-calm-mouse-adgcgbq7-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

# neon_conn = psycopg2.connect(NEON_DATABASE_URL)

# # =========================================
# # 🔌 SQLITE LOCAL
# # =========================================
# sqlite_conn = sqlite3.connect("negocio.db")

# # =========================================
# # 📋 TABLAS
# # =========================================
# tablas = [
#     "productos",
#     "clientes",
#     "ventas",
#     "deudas",
#     "usuarios",
#     "categorias",
#     "logs",
#     "auditoria",
#     "ventas_detalle",
#     "deudas_detalle"
# ]

# # =========================================
# # 🚀 MIGRACIÓN
# # =========================================
# for tabla in tablas:
#     print(f"\n🔄 Migrando: {tabla}")

#     try:
#         query = f"SELECT * FROM {tabla};"
#         df = pd.read_sql(query, neon_conn)

#         if df.empty:
#             print(f"⚠️ {tabla} vacía")
#             continue

#         # LIMPIEZA
#         df = df.fillna("")
#         df = df.astype(str)

#         df.to_sql(tabla, sqlite_conn, if_exists="append", index=False)

#         print(f"✅ {tabla}: {len(df)} registros")

#     except Exception as e:
#         print(f"❌ Error en {tabla}: {e}")

# # =========================================
# # 🔚 CIERRE
# # =========================================
# neon_conn.close()
# sqlite_conn.close()
# print("\n🎉 MIGRACIÓN COMPLETA REAL")