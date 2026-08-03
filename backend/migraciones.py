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

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()