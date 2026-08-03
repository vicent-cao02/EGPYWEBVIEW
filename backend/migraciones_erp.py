"""Migraciones ERP seguras para negocio.db

Este script crea las tablas y columnas necesarias para convertir
la base existente a un modelo ERP manteniendo compatibilidad con
los datos actuales (usa ALTER TABLE ADD COLUMN cuando es posible).

Uso:
    from backend.migraciones_erp import ejecutar_migraciones
    ejecutar_migraciones()

O ejecutar directamente:
    python backend/migraciones_erp.py
"""
import shutil
import datetime
import pathlib
import sqlite3


DB_PATH = pathlib.Path("negocio.db")


def backup_db():
    if not DB_PATH.exists():
        raise FileNotFoundError("negocio.db no encontrado en el directorio de trabajo")
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    dest = DB_PATH.with_name(f"negocio.db.bak-{ts}")
    shutil.copy(DB_PATH, dest)
    return dest


def _has_column(cursor, table, column_name):
    cursor.execute(f"PRAGMA table_info({table})")
    rows = cursor.fetchall()
    return any(r[1] == column_name for r in rows)


def _add_column(cursor, table, column_def):
    # column_def debe incluir 'name TYPE ...' por ejemplo: "created_at TEXT DEFAULT (datetime('now'))"
    name = column_def.split()[0]
    if not _has_column(cursor, table, name):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def _create_tables(cursor):
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contacto TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        ruc TEXT,
        estado TEXT DEFAULT 'activo',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER,
        fecha TEXT DEFAULT (datetime('now')),
        subtotal REAL NOT NULL DEFAULT 0,
        impuesto REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        usuario TEXT,
        observaciones TEXT,
        referencia TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compra_detalle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compra_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad REAL NOT NULL,
        precio_unitario REAL NOT NULL,
        descuento REAL DEFAULT 0,
        subtotal REAL NOT NULL,
        unidad_medida TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        saldo_inicial REAL NOT NULL DEFAULT 0,
        saldo_actual REAL NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'abierta',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caja_id INTEGER NOT NULL,
        tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('INGRESO','EGRESO','AJUSTE')),
        monto REAL NOT NULL,
        fecha TEXT DEFAULT (datetime('now')),
        referencia TEXT,
        descripcion TEXT,
        usuario TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (caja_id) REFERENCES caja(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        venta_id INTEGER,
        deuda_id INTEGER,
        monto_original REAL NOT NULL DEFAULT 0,
        monto_pendiente REAL NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        vencimiento TEXT,
        descripcion TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE SET NULL,
        FOREIGN KEY (deuda_id) REFERENCES deudas(id) ON DELETE SET NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER,
        compra_id INTEGER,
        monto_original REAL NOT NULL DEFAULT 0,
        monto_pendiente REAL NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        vencimiento TEXT,
        descripcion TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL,
        FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE SET NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario_movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        referencia_tipo TEXT,
        referencia_id INTEGER,
        cantidad REAL NOT NULL,
        stock_anterior REAL NOT NULL DEFAULT 0,
        stock_nuevo REAL NOT NULL DEFAULT 0,
        usuario TEXT,
        motivo TEXT,
        fecha TEXT DEFAULT (datetime('now')),
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        rol TEXT NOT NULL,
        descripcion TEXT,
        creado_por TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT,
        deleted_at TEXT,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """)


def _create_indices(cursor):
    indices = [
        ("idx_clientes_email", "clientes(email)"),
        ("idx_clientes_documento", "clientes(tipo_documento, numero_documento)"),
        ("idx_productos_categoria", "productos(categoria_id)"),
        ("idx_productos_activos", "productos(activo)"),
        ("idx_ventas_cliente", "ventas(cliente_id)"),
        ("idx_ventas_fecha", "ventas(fecha)"),
        ("idx_venta_detalle_venta", "venta_detalle(venta_id)"),
        ("idx_venta_detalle_producto", "venta_detalle(producto_id)"),
        ("idx_compras_proveedor", "compras(proveedor_id)"),
        ("idx_compras_fecha", "compras(fecha)"),
        ("idx_compra_detalle_compra", "compra_detalle(compra_id)"),
        ("idx_movimientos_caja_caja", "movimientos_caja(caja_id)"),
        ("idx_movimientos_caja_fecha", "movimientos_caja(fecha)"),
        ("idx_cuentas_por_cobrar_cliente", "cuentas_por_cobrar(cliente_id)"),
        ("idx_cuentas_por_pagar_proveedor", "cuentas_por_pagar(proveedor_id)"),
        ("idx_inventario_movimientos_producto", "inventario_movimientos(producto_id)"),
        ("idx_usuarios_roles_usuario", "usuarios_roles(usuario_id)"),
    ]
    for name, expr in indices:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {expr}")


def _add_audit_columns(cursor):
    # Añade columnas de auditoría y soft-delete a tablas conocidas
    tables = [
        "clientes",
        "categorias",
        "productos",
        "ventas",
        "venta_detalle",
        "deudas",
        "deudas_detalle",
        "pagos_deuda",
        "logs",
        "auditoria",
        "usuarios",
    ]
    for t in tables:
        try:
            _add_column(cursor, t, "created_at TEXT DEFAULT (datetime('now'))")
            _add_column(cursor, t, "updated_at TEXT")
            _add_column(cursor, t, "deleted_at TEXT")
            _add_column(cursor, t, "is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1))")
        except Exception:
            # Si la tabla no existe, continuar
            continue

    # Campos adicionales útiles
    try:
        _add_column(cursor, "clientes", "email TEXT")
        _add_column(cursor, "clientes", "tipo_documento TEXT")
        _add_column(cursor, "clientes", "numero_documento TEXT")
        _add_column(cursor, "clientes", "limite_credito REAL DEFAULT 0")
    except Exception:
        pass


def ejecutar_migraciones():
    backup = backup_db()
    print(f"Backup creado: {backup}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Altera columnas y crea tablas/índices
        conn.execute("PRAGMA foreign_keys = OFF")
        _add_audit_columns(cursor)
        _create_tables(cursor)
        _create_indices(cursor)
        conn.commit()
        print("Migración aplicada (estructura). Revisa los índices y relaciones en la copia de la BD.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    ejecutar_migraciones()
