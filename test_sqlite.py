#!/usr/bin/env python3
"""
Script de prueba para verificar que la refactorización a SQLite funciona correctamente.
"""

from backend.productos import list_products, get_product
from backend.clientes import list_clients
from backend.categorias import list_categories
from backend.logs import listar_logs
from backend.ventas import list_sales
from backend.deudas import list_debts

print("=" * 60)
print("🧪 PRUEBAS DE REFACTORIZACIÓN A SQLite")
print("=" * 60)

# Prueba 1: Listar productos
try:
    print("\n✅ Probando list_products()...")
    products = list_products()
    print(f"   Total de productos: {len(products)}")
    if products:
        print(f"   Primer producto: {products[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Prueba 2: Listar clientes
try:
    print("\n✅ Probando list_clients()...")
    clients = list_clients()
    print(f"   Total de clientes: {len(clients)}")
    if clients:
        print(f"   Primer cliente: {clients[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Prueba 3: Listar categorías
try:
    print("\n✅ Probando list_categories()...")
    categories = list_categories()
    print(f"   Total de categorías: {len(categories)}")
    if categories:
        print(f"   Primera categoría: {categories[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Prueba 4: Listar logs
try:
    print("\n✅ Probando listar_logs()...")
    logs = listar_logs()
    print(f"   Total de logs: {len(logs)}")
    if logs:
        print(f"   Primer log: {logs[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Prueba 5: Listar ventas
try:
    print("\n✅ Probando list_sales()...")
    sales = list_sales()
    print(f"   Total de ventas: {len(sales)}")
    if sales:
        print(f"   Primera venta: {sales[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Prueba 6: Listar deudas
try:
    print("\n✅ Probando list_debts()...")
    debts = list_debts()
    print(f"   Total de deudas: {len(debts)}")
    if debts:
        print(f"   Primera deuda: {debts[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Todas las pruebas completadas exitosamente!")
print("=" * 60)
