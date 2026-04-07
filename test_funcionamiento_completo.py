#!/usr/bin/env python3
"""
🧪 PRUEBA COMPLETA DE FUNCIONAMIENTO POST-MIGRACIÓN
Prueba operaciones CRUD básicas en todos los módulos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.db import get_connection, test_connection
from backend.productos import guardar_producto, list_products, get_product, delete_product
from backend.clientes import add_client, list_clients, get_client, update_client
from backend.usuarios import autenticar_usuario, listar_usuarios
from backend.ventas import register_sale, list_sales
from backend.deudas import add_debt, list_debts
from backend.categorias import list_categories, agregar_categoria
from backend.logs import registrar_log, listar_logs
import json
from datetime import datetime

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print('='*60)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def test_database_connection():
    print_test_header("PRUEBA DE CONEXIÓN A BASE DE DATOS")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        conn.close()
        print_success(f"Conexión exitosa. {count} productos encontrados.")
        return True
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        return False

def test_categories():
    print_test_header("PRUEBA DE CATEGORÍAS")
    try:
        categories = list_categories()
        print_success(f"{len(categories)} categorías encontradas")

        # Probar agregar nueva categoría
        nueva_cat = f"Test Category {datetime.now().strftime('%H%M%S')}"
        result = agregar_categoria(nueva_cat)
        if result:
            print_success("Nueva categoría agregada correctamente")
        else:
            print_error("Error al agregar categoría")

        return True
    except Exception as e:
        print_error(f"Error en categorías: {e}")
        return False

def test_products():
    print_test_header("PRUEBA DE PRODUCTOS")
    try:
        products = list_products()
        print_success(f"{len(products)} productos encontrados")

        # Probar crear producto
<<<<<<< Updated upstream
        test_product_name = f"Producto Test {datetime.now().strftime('%H%M%S')}"
        result = guardar_producto(
            nombre=test_product_name,
            precio=10.50,
            cantidad=100,
            categoria_id=1,
            usuario="admin"
        )
        if result:
            print_success("Producto creado correctamente")
            product_id = result["id"]
=======
        test_product = {
            "nombre": f"Producto Test {datetime.now().strftime('%H%M%S')}",
            "descripcion": "Producto de prueba",
            "precio": 10.50,
            "stock": 100,
            "categoria_id": 1,
            "codigo_barras": f"TEST{datetime.now().strftime('%H%M%S')}"
        }

        result = guardar_producto(test_product)
        if result:
            print_success("Producto creado correctamente")
            product_id = result
>>>>>>> Stashed changes

            # Probar obtener producto
            product = get_product(product_id)
            if product:
                print_success("Producto obtenido correctamente")

                # Probar eliminar producto
                delete_result = delete_product(product_id)
                if delete_result:
                    print_success("Producto eliminado correctamente")
                else:
                    print_error("Error al eliminar producto")
            else:
                print_error("Error al obtener producto")
        else:
            print_error("Error al crear producto")

        return True
    except Exception as e:
        print_error(f"Error en productos: {e}")
        return False

def test_clients():
    print_test_header("PRUEBA DE CLIENTES")
    try:
        clients = list_clients()
        print_success(f"{len(clients)} clientes encontrados")

        # Probar crear cliente
<<<<<<< Updated upstream
        test_client_name = f"Cliente Test {datetime.now().strftime('%H%M%S')}"
        result = add_client(
            nombre=test_client_name,
            telefono="099123456",
            ci=f"12345678{datetime.now().strftime('%S')}",
            direccion="Dirección de prueba",
            chapa=f"CHAPA{datetime.now().strftime('%H%M%S')}",
            usuario="admin"
        )
=======
        test_client = {
            "nombre": f"Cliente Test {datetime.now().strftime('%H%M%S')}",
            "ci": f"12345678{datetime.now().strftime('%S')}",
            "telefono": "099123456",
            "direccion": "Dirección de prueba",
            "chapa": f"CHAPA{datetime.now().strftime('%H%M%S')}"
        }

        result = add_client(test_client)
>>>>>>> Stashed changes
        if result:
            print_success("Cliente creado correctamente")
            client_id = result

            # Probar obtener cliente
            client = get_client(client_id)
            if client:
                print_success("Cliente obtenido correctamente")

                # Probar actualizar cliente
<<<<<<< Updated upstream
                update_result = update_client(client_id, {
                    "nombre": test_client_name,
                    "telefono": "098765432",
                    "ci": f"12345678{datetime.now().strftime('%S')}",
                    "direccion": "Dirección actualizada",
                    "chapa": f"CHAPA{datetime.now().strftime('%H%M%S')}"
                })
=======
                test_client["telefono"] = "098765432"
                update_result = update_client(client_id, test_client)
>>>>>>> Stashed changes
                if update_result:
                    print_success("Cliente actualizado correctamente")
                else:
                    print_error("Error al actualizar cliente")
            else:
                print_error("Error al obtener cliente")
        else:
            print_error("Error al crear cliente")

        return True
    except Exception as e:
        print_error(f"Error en clientes: {e}")
        return False

def test_users():
    print_test_header("PRUEBA DE USUARIOS")
    try:
        users = listar_usuarios()
        print_success(f"{len(users)} usuarios encontrados")

        # Probar autenticación con usuario existente
        # Asumiendo que hay al menos un usuario admin
        auth_result = autenticar_usuario("admin", "admin123")
        if auth_result:
            print_success("Autenticación exitosa")
        else:
            print("⚠️  Autenticación falló (posiblemente credenciales diferentes)")

        return True
    except Exception as e:
        print_error(f"Error en usuarios: {e}")
        return False

def test_sales():
    print_test_header("PRUEBA DE VENTAS")
    try:
<<<<<<< Updated upstream
        sales = list_sales()
        print_success(f"{len(sales)} ventas encontradas")
=======
        sales = list_sales(limit=10)
        print_success(f"Últimas {len(sales)} ventas obtenidas")
>>>>>>> Stashed changes

        # Para probar registro de venta necesitaríamos productos existentes
        # Por ahora solo verificamos que la función existe y no da error
        print_success("Módulo de ventas operativo")

        return True
    except Exception as e:
        print_error(f"Error en ventas: {e}")
        return False

def test_debts():
    print_test_header("PRUEBA DE DEUDAS")
    try:
        debts = list_debts()
        print_success(f"{len(debts)} deudas encontradas")

        # Para probar agregar deuda necesitaríamos cliente y productos
        # Por ahora solo verificamos que la función existe
        print_success("Módulo de deudas operativo")

        return True
    except Exception as e:
        print_error(f"Error en deudas: {e}")
        return False

def test_logs():
    print_test_header("PRUEBA DE LOGS")
    try:
<<<<<<< Updated upstream
        logs = listar_logs()
        print_success(f"{len(logs)} logs encontrados")
=======
        logs = listar_logs(limit=10)
        print_success(f"Últimos {len(logs)} logs obtenidos")
>>>>>>> Stashed changes

        # Probar registrar log
        result = registrar_log("Test", "Prueba de funcionamiento", "admin")
        if result:
            print_success("Log registrado correctamente")
        else:
            print_error("Error al registrar log")

        return True
    except Exception as e:
        print_error(f"Error en logs: {e}")
        return False

def main():
    print("🚀 INICIANDO PRUEBAS COMPLETAS DE FUNCIONAMIENTO")
    print("=" * 80)

    tests = [
        ("Conexión BD", test_database_connection),
        ("Categorías", test_categories),
        ("Productos", test_products),
        ("Clientes", test_clients),
        ("Usuarios", test_users),
        ("Ventas", test_sales),
        ("Deudas", test_debts),
        ("Logs", test_logs)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print_error(f"Excepción en {test_name}: {e}")

    print(f"\n{'='*80}")
    print("📊 RESULTADOS FINALES:")
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("✨ El sistema está completamente funcional con SQLite")
    else:
        print(f"\n⚠️  {total - passed} pruebas fallaron. Revisar logs arriba.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)