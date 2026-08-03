from backend.db import get_connection


def _normalizar_fechas():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, CAST(fecha AS TEXT) FROM deudas WHERE fecha IS NOT NULL")
        rows = cursor.fetchall()
        for deuda_id, fecha in rows:
            if not fecha:
                continue
            valor = str(fecha)
            if "T" in valor and " " not in valor:
                nueva = valor.replace("T", " ")
                cursor.execute("UPDATE deudas SET fecha = ? WHERE id = ?", (nueva, deuda_id))

        cursor.execute("SELECT id, CAST(fecha AS TEXT) FROM ventas WHERE fecha IS NOT NULL")
        rows = cursor.fetchall()
        for venta_id, fecha in rows:
            if not fecha:
                continue
            valor = str(fecha)
            if "T" in valor and " " not in valor:
                nueva = valor.replace("T", " ")
                cursor.execute("UPDATE ventas SET fecha = ? WHERE id = ?", (nueva, venta_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ejecutar_migraciones():
    conn = get_connection()
    cursor = conn.cursor()

    try:

        _normalizar_fechas()

        # ==========================================================
        # ÍNDICES
        # ==========================================================

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_cliente
        ON ventas(cliente_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_fecha
        ON ventas(fecha)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_deudas_cliente
        ON deudas(cliente_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_productos_nombre
        ON productos(nombre)
        """)

        # ==========================================================
        # TABLA DETALLE DE VENTAS
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS venta_detalle (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            venta_id INTEGER NOT NULL,

            producto_id INTEGER NOT NULL,

            cantidad REAL NOT NULL,

            precio_unitario REAL NOT NULL,

            descuento REAL DEFAULT 0,

            subtotal REAL NOT NULL,

            FOREIGN KEY (venta_id)
                REFERENCES ventas(id)
                ON DELETE CASCADE,

            FOREIGN KEY (producto_id)
                REFERENCES productos(id)
        )
        """)

        # ==========================================================
        # TABLA PAGOS DE DEUDAS
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_deuda (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            deuda_id INTEGER NOT NULL,

            fecha TEXT NOT NULL,

            monto REAL NOT NULL,

            usuario TEXT,

            observacion TEXT,

            FOREIGN KEY (deuda_id)
                REFERENCES deudas(id)
                ON DELETE CASCADE
        )
        """)

        # ==========================================================
        # ÍNDICES NUEVOS
        # ==========================================================

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_detalle_venta
        ON venta_detalle(venta_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_detalle_producto
        ON venta_detalle(producto_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pagos_deuda
        ON pagos_deuda(deuda_id)
        """)

        # ==========================================================
        # MÓDULO CONTABLE: PLAN DE CUENTAS Y ASIENTOS
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas_contables (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo TEXT NOT NULL UNIQUE,

            nombre TEXT NOT NULL,

            tipo TEXT NOT NULL,

            padre_id INTEGER,

            saldo_inicial REAL DEFAULT 0,

            FOREIGN KEY (padre_id)
                REFERENCES cuentas_contables(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS asientos_contables (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fecha TEXT NOT NULL,

            descripcion TEXT,

            referencia TEXT,

            usuario TEXT,

            total REAL NOT NULL

        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_asientos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            asiento_id INTEGER NOT NULL,

            cuenta_id INTEGER NOT NULL,

            debe REAL DEFAULT 0,

            haber REAL DEFAULT 0,

            descripcion TEXT,

            FOREIGN KEY (asiento_id)
                REFERENCES asientos_contables(id)
                ON DELETE CASCADE,

            FOREIGN KEY (cuenta_id)
                REFERENCES cuentas_contables(id)
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_asientos_fecha
        ON asientos_contables(fecha)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_detalle_asiento_asiento
        ON detalle_asientos(asiento_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cuentas_codigo
        ON cuentas_contables(codigo)
        """)

        # ==========================================================
        # TABLA CONFIGURACIÓN DE IMPUESTOS
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_impuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            porcentaje REAL NOT NULL DEFAULT 0,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion TEXT
        )
        """)

        # Insertar IVA estándar si no existe
        cursor.execute("SELECT * FROM configuracion_impuestos WHERE nombre='IVA'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO configuracion_impuestos (nombre, porcentaje, activo)
                VALUES ('IVA', 0, 1)
            """)

        # ==========================================================
        # TABLA SECUENCIAL DE FACTURAS
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS secuencial_facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_venta TEXT NOT NULL UNIQUE,
            numero_actual INTEGER NOT NULL DEFAULT 0,
            prefijo TEXT DEFAULT '',
            fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Insertar tipos de venta por defecto
        cursor.execute("SELECT * FROM secuencial_facturas WHERE tipo_venta='CONTADO'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO secuencial_facturas (tipo_venta, numero_actual, prefijo)
                VALUES ('CONTADO', 0, 'FAC')
            """)
            cursor.execute("""
                INSERT INTO secuencial_facturas (tipo_venta, numero_actual, prefijo)
                VALUES ('CREDITO', 0, 'CRE')
            """)
            cursor.execute("""
                INSERT INTO secuencial_facturas (tipo_venta, numero_actual, prefijo)
                VALUES ('DEVOLUCION', 0, 'DEV')
            """)

        # ==========================================================
        # TABLA MÉTODOS DE PAGO
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metodos_pago (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            requiere_referencia BOOLEAN DEFAULT 0,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Insertar métodos de pago por defecto
        cursor.execute("SELECT * FROM metodos_pago WHERE nombre='EFECTIVO'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO metodos_pago (nombre, descripcion, requiere_referencia, activo)
                VALUES ('EFECTIVO', 'Pago en efectivo', 0, 1)
            """)
            cursor.execute("""
                INSERT INTO metodos_pago (nombre, descripcion, requiere_referencia, activo)
                VALUES ('TARJETA_DEBITO', 'Tarjeta de débito', 1, 1)
            """)
            cursor.execute("""
                INSERT INTO metodos_pago (nombre, descripcion, requiere_referencia, activo)
                VALUES ('TARJETA_CREDITO', 'Tarjeta de crédito', 1, 1)
            """)
            cursor.execute("""
                INSERT INTO metodos_pago (nombre, descripcion, requiere_referencia, activo)
                VALUES ('TRANSFERENCIA', 'Transferencia bancaria', 1, 1)
            """)
            cursor.execute("""
                INSERT INTO metodos_pago (nombre, descripcion, requiere_referencia, activo)
                VALUES ('CHEQUE', 'Cheque', 1, 1)
            """)

        # ==========================================================
        # TABLA DEVOLUCIONES
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devoluciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            numero_devolucion TEXT NOT NULL UNIQUE,
            fecha TEXT NOT NULL,
            cliente_id INTEGER NOT NULL,
            usuario TEXT NOT NULL,
            motivo TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            observaciones TEXT,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
        """)

        # ==========================================================
        # TABLA DETALLE DE DEVOLUCIONES
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devolucion_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            devolucion_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            razon TEXT,
            FOREIGN KEY (devolucion_id) REFERENCES devoluciones(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
        """)

        # ==========================================================
        # TABLA VENTAS CANCELADAS (AUDITORÍA)
        # ==========================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas_canceladas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            fecha_cancelacion TEXT NOT NULL,
            usuario_cancelacion TEXT NOT NULL,
            motivo TEXT,
            datos_originales TEXT,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ==========================================================
        # MEJORAR TABLA VENTAS - AGREGAR CAMPOS SI NO EXISTEN
        # ==========================================================

        # Verificar y agregar columnas a la tabla ventas si no existen
        cursor.execute("PRAGMA table_info(ventas)")
        columnas = {row[1] for row in cursor.fetchall()}

        if 'numero_factura' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN numero_factura TEXT UNIQUE")

        if 'estado' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN estado TEXT DEFAULT 'ACTIVA'")

        if 'fecha_cancelacion' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN fecha_cancelacion TEXT")

        if 'tipo_cliente' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN tipo_cliente TEXT DEFAULT 'CONTADO'")

        if 'descuento_total' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN descuento_total REAL DEFAULT 0")

        if 'impuesto_total' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN impuesto_total REAL DEFAULT 0")

        if 'referencia_pago' not in columnas:
            cursor.execute("ALTER TABLE ventas ADD COLUMN referencia_pago TEXT")

        # ==========================================================
        # ÍNDICES PARA NUEVAS TABLAS
        # ==========================================================

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_devoluciones_venta
        ON devoluciones(venta_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_devoluciones_cliente
        ON devoluciones(cliente_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_devolucion_detalle
        ON devolucion_detalle(devolucion_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_numero_factura
        ON ventas(numero_factura)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_estado
        ON ventas(estado)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_canceladas
        ON ventas_canceladas(venta_id)
        """)

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()