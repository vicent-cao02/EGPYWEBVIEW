"""
Migraciones para el módulo de inventario profesional.
Crea tablas para Kardex, movimientos, entradas, salidas y ajustes.
"""

from backend.database import db


def crear_tablas_inventario():
    """
    Crea las tablas necesarias para el módulo de inventario profesional.
    - inventario_movimientos: Kardex completo
    - inventario_config: Configuración de stock mínimo y alertas
    - inventario_entradas: Registro de entradas
    - inventario_salidas: Registro de salidas
    - inventario_ajustes: Registro de ajustes
    """

    # Tabla de movimientos (Kardex)
    sql_movimientos = """
    CREATE TABLE IF NOT EXISTS inventario_movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        cantidad REAL NOT NULL,
        stock_anterior REAL NOT NULL,
        stock_posterior REAL NOT NULL,
        referencia TEXT,
        usuario TEXT,
        fecha TEXT NOT NULL,
        observaciones TEXT,
        fecha_registro TEXT NOT NULL,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        CHECK (tipo IN ('ENTRADA', 'SALIDA', 'AJUSTE', 'INICIAL'))
    )
    """

    # Tabla de configuración de inventario
    sql_config = """
    CREATE TABLE IF NOT EXISTS inventario_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL UNIQUE,
        stock_minimo REAL DEFAULT 0,
        stock_maximo REAL DEFAULT 999999,
        alertar_minimo INTEGER DEFAULT 1,
        fecha_actualizacion TEXT NOT NULL,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
    )
    """

    # Tabla de entradas
    sql_entradas = """
    CREATE TABLE IF NOT EXISTS inventario_entradas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        cantidad REAL NOT NULL,
        precio_unitario REAL,
        proveedor TEXT,
        numero_compra TEXT,
        usuario TEXT,
        fecha TEXT NOT NULL,
        observaciones TEXT,
        movimiento_id INTEGER,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (movimiento_id) REFERENCES inventario_movimientos(id) ON DELETE SET NULL
    )
    """

    # Tabla de salidas
    sql_salidas = """
    CREATE TABLE IF NOT EXISTS inventario_salidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        cantidad REAL NOT NULL,
        motivo TEXT,
        numero_documento TEXT,
        usuario TEXT,
        fecha TEXT NOT NULL,
        observaciones TEXT,
        movimiento_id INTEGER,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (movimiento_id) REFERENCES inventario_movimientos(id) ON DELETE SET NULL
    )
    """

    # Tabla de ajustes
    sql_ajustes = """
    CREATE TABLE IF NOT EXISTS inventario_ajustes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        cantidad_anterior REAL NOT NULL,
        cantidad_nueva REAL NOT NULL,
        cantidad_ajuste REAL NOT NULL,
        razon TEXT,
        usuario TEXT,
        fecha TEXT NOT NULL,
        observaciones TEXT,
        movimiento_id INTEGER,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (movimiento_id) REFERENCES inventario_movimientos(id) ON DELETE SET NULL
    )
    """

    # Tabla de alertas
    sql_alertas = """
    CREATE TABLE IF NOT EXISTS inventario_alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        mensaje TEXT,
        stock_actual REAL,
        stock_minimo REAL,
        resuelta INTEGER DEFAULT 0,
        fecha_creacion TEXT NOT NULL,
        fecha_resolucion TEXT,
        usuario_resolucion TEXT,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        CHECK (tipo IN ('STOCK_BAJO', 'SIN_STOCK', 'EXCESO'))
    )
    """

    # Crear índices para optimizar búsquedas
    sql_indices = [
        "CREATE INDEX IF NOT EXISTS idx_mov_producto ON inventario_movimientos(producto_id)",
        "CREATE INDEX IF NOT EXISTS idx_mov_fecha ON inventario_movimientos(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_mov_tipo ON inventario_movimientos(tipo)",
        "CREATE INDEX IF NOT EXISTS idx_entrada_producto ON inventario_entradas(producto_id)",
        "CREATE INDEX IF NOT EXISTS idx_salida_producto ON inventario_salidas(producto_id)",
        "CREATE INDEX IF NOT EXISTS idx_ajuste_producto ON inventario_ajustes(producto_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerta_producto ON inventario_alertas(producto_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerta_resuelta ON inventario_alertas(resuelta)",
    ]

    try:
        with db.transaction() as conn:
            conn.execute(sql_movimientos)
            conn.execute(sql_config)
            conn.execute(sql_entradas)
            conn.execute(sql_salidas)
            conn.execute(sql_ajustes)
            conn.execute(sql_alertas)

            for sql_indice in sql_indices:
                conn.execute(sql_indice)

        print("✓ Tablas de inventario creadas exitosamente")
        return True

    except Exception as e:
        print(f"✗ Error al crear tablas de inventario: {e}")
        return False


def agregar_stock_minimo_a_productos_existentes():
    """
    Crea configuración de inventario para todos los productos existentes.
    """
    try:
        with db.transaction() as conn:
            cursor = conn.execute("SELECT id FROM productos")
            productos = cursor.fetchall()

            from datetime import datetime
            ahora = datetime.now().isoformat()

            for row in productos:
                producto_id = row[0]
                conn.execute(
                    """
                    INSERT OR IGNORE INTO inventario_config 
                    (producto_id, stock_minimo, stock_maximo, fecha_actualizacion)
                    VALUES (?, ?, ?, ?)
                    """,
                    (producto_id, 5, 999999, ahora)
                )

        print("✓ Configuración de stock mínimo agregada a productos existentes")
        return True

    except Exception as e:
        print(f"✗ Error al agregar configuración de stock: {e}")
        return False


if __name__ == "__main__":
    crear_tablas_inventario()
    agregar_stock_minimo_a_productos_existentes()
