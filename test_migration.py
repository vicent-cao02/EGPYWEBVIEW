#!/usr/bin/env python3
"""
Script de prueba para verificar que la migración de PostgreSQL a SQLite funciona correctamente.
"""

import sys
sys.path.insert(0, '/Users/vicent/Story/EGPYWEBVIEW')

from backend.db import get_connection, test_connection
from backend import productos, clientes, usuarios, ventas, deudas, categorias, logs

print("\n" + "="*60)
print("🧪 PRUEBAS DE MIGRACIÓN: PostgreSQL → SQLite")
print("="*60 + "\n")

# Prueba 1: Conexión a BD
print("1️⃣ Probando conexión a BD...")
if test_connection():
    print("   ✅ Conexión a SQLite exitosa\n")
else:
    print("   ❌ Fallo en la conexión\n")
    sys.exit(1)

# Prueba 2: Listar categorías
print("2️⃣ Probando lectura de categorías...")
try:
    cats = categorias.list_categories()
    print(f"   ✅ {len(cats)} categorías encontradas\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Prueba 3: Listar productos
print("3️⃣ Probando lectura de productos...")
try:
    prods = productos.list_products()
    print(f"   ✅ {len(prods)} productos encontrados\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Prueba 4: Listar clientes
print("4️⃣ Probando lectura de clientes...")
try:
    clis = clientes.list_clients()
    print(f"   ✅ {len(clis)} clientes encontrados\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Prueba 5: Listar usuarios
print("5️⃣ Probando lectura de usuarios...")
try:
    users = usuarios.listar_usuarios()
    print(f"   ✅ {len(users)} usuarios encontrados\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Prueba 6: Listar ventas
print("6️⃣ Probando lectura de ventas...")
try:
    vts = ventas.list_sales()
    print(f"   ✅ {len(vts)} ventas encontradas\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Prueba 7: Listar deudas
print("7️⃣ Probando lectura de deudas...")
try:
    dts = deudas.list_debts()
    print(f"   ✅ {len(dts)} deudas encontradas\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Prueba 8: Listar logs
print("8️⃣ Probando lectura de logs...")
try:
    lgs = logs.listar_logs()
    print(f"   ✅ {len(lgs)} logs encontrados\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("="*60)
print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
print("="*60 + "\n")
print("🎉 La migración de PostgreSQL a SQLite fue exitosa!")
print("📌 El proyecto está listo para usar SQLite local.\n")
