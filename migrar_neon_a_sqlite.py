import pandas as pd
import sqlite3
from sqlalchemy import create_engine

# =========================================
# 🔌 CONEXIÓN A NEON (YA CONFIGURADA)
# =========================================
POSTGRES_URL = "postgresql://neondb_owner:npg_BY8QzbZ1Vsmu@ep-calm-mouse-adgcgbq7-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(POSTGRES_URL)

# =========================================
# 🔌 SQLITE LOCAL
# =========================================
sqlite_conn = sqlite3.connect("negocio.db")

# =========================================
# 📋 TABLAS A MIGRAR
# =========================================
tablas = [
    "productos",
    "clientes",
    "ventas",
    "deudas",
    "usuarios",
    "categorias",
    "logs",
    "auditoria",
    "ventas_detalle",
    "deudas_detalle"
]

# =========================================
# 🚀 MIGRACIÓN ROBUSTA
# =========================================
for tabla in tablas:
    print(f"\n🔄 Migrando: {tabla}")

    try:
        # Leer datos desde Neon
        df = pd.read_sql(f"SELECT * FROM {tabla}", engine)

        if df.empty:
            print(f"⚠️ {tabla} está vacía")
            continue

        # 🔧 LIMPIEZA (CLAVE)
        df = df.fillna("")

        # Convertir tipos problemáticos
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str)

        # Insertar en SQLite
        df.to_sql(tabla, sqlite_conn, if_exists="append", index=False)

        print(f"✅ {tabla}: {len(df)} registros migrados")

    except Exception as e:
        print(f"❌ Error en {tabla}: {e}")

# =========================================
# 🔚 CIERRE
# =========================================
sqlite_conn.close()
print("\n🎉 MIGRACIÓN COMPLETADA")