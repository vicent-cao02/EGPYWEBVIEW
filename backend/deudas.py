# backend/deudas.py

from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO

import os
import json

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

from .db import get_connection
from .clientes import update_debt
from backend.ventas import get_sale
from backend import ventas


# ======================================================
# 📜 LISTAR TODAS LAS DEUDAS
# ======================================================
def list_debts() -> List[Dict[str, Any]]:

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM deudas
            ORDER BY fecha DESC
        """)

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# ======================================================
# 🔍 OBTENER DEUDA
# ======================================================
def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.cliente_id,
                d.venta_id,
                d.monto_total,
                d.estado,
                d.fecha,
                d.descripcion,

                dd.id AS detalle_id,
                dd.producto_id,
                dd.cantidad,
                dd.precio_unitario,
                dd.estado AS estado_detalle

            FROM deudas d

            LEFT JOIN deudas_detalle dd
                ON d.id = dd.deuda_id

            WHERE d.id = ?

            ORDER BY dd.id
        """, (deuda_id,))

        rows = cursor.fetchall()

    finally:
        conn.close()

    if not rows:
        return None

    deuda = dict(rows[0])

    detalles = []

    for r in rows:

        if r["detalle_id"] is not None:

            detalles.append({
                "id": r["detalle_id"],
                "producto_id": r["producto_id"],
                "cantidad": float(r["cantidad"]),
                "precio_unitario": float(r["precio_unitario"]),
                "estado": r["estado_detalle"]
            })

    deuda["detalles"] = detalles

    # limpiar columnas repetidas
    for k in [
        "detalle_id",
        "producto_id",
        "cantidad",
        "precio_unitario",
        "estado_detalle"
    ]:
        deuda.pop(k, None)

    return deuda


# ======================================================
# ➕ CREAR DEUDA
# ======================================================
def add_debt(
    cliente_id: int,
    venta_id: int = None,
    productos: list = None,
    monto_total: float = 0.0,
    estado: str = "pendiente",
    usuario: str = None
) -> int:

    estado = str(estado).lower()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        fecha = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO deudas (
                cliente_id,
                venta_id,
                monto_total,
                estado,
                fecha,
                descripcion
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            venta_id,
            float(monto_total),
            estado,
            fecha,
            f"Deuda generada por venta #{venta_id}"
        ))

        deuda_id = cursor.lastrowid

        if productos:

            for p in productos:

                cursor.execute("""
                    INSERT INTO deudas_detalle (
                        deuda_id,
                        producto_id,
                        cantidad,
                        precio_unitario,
                        estado
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    deuda_id,
                    p["id_producto"],
                    float(p["cantidad"]),
                    float(p["precio_unitario"]),
                    "pendiente"
                ))

        update_debt(cliente_id, float(monto_total), usuario=usuario or "sistema", conn=conn)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return deuda_id


# ======================================================
# 💰 PAGAR DEUDA
# ======================================================
def pay_debt_producto(
    deuda_id: int,
    producto_id: int,
    monto_pago: float,
    usuario=None
):

    deuda = get_debt(deuda_id)

    if not deuda:
        raise Exception("Deuda no encontrada")

    detalle = next(
        (
            d for d in deuda["detalles"]
            if int(d["producto_id"]) == int(producto_id)
        ),
        None
    )

    if not detalle:
        raise Exception("Producto no encontrado en la deuda")

    precio_unitario = float(detalle["precio_unitario"])

    cantidad_actual = float(detalle["cantidad"])

    cantidad_pagada = float(monto_pago) / precio_unitario

    nueva_cantidad = max(
        cantidad_actual - cantidad_pagada,
        0
    )

    nuevo_estado = (
        "pagado"
        if nueva_cantidad <= 0
        else "pendiente"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ==================================================
        # ACTUALIZAR DETALLE
        # ==================================================
        cursor.execute("""
            UPDATE deudas_detalle
            SET cantidad = ?,
                estado = ?
            WHERE id = ?
        """, (
            nueva_cantidad,
            nuevo_estado,
            detalle["id"]
        ))

        # ==================================================
        # CALCULAR RESTANTE
        # ==================================================
        cursor.execute("""
            SELECT
                SUM(cantidad * precio_unitario)
            FROM deudas_detalle
            WHERE deuda_id = ?
            AND estado = 'pendiente'
        """, (deuda_id,))

        restante = cursor.fetchone()[0] or 0

        estado_deuda = (
            "pagada"
            if restante <= 0
            else "pendiente"
        )

        # ==================================================
        # ACTUALIZAR DEUDA
        # ==================================================
        cursor.execute("""
            UPDATE deudas
            SET estado = ?,
                monto_total = ?
            WHERE id = ?
        """, (
            estado_deuda,
            restante,
            deuda_id
        ))

        update_debt(deuda["cliente_id"], -float(monto_pago), usuario=usuario or "sistema", conn=conn)

        # ======================================================
        # ACTUALIZAR VENTA SI SE PAGÓ COMPLETA
        # ======================================================
        venta_id = deuda.get("venta_id")

        if venta_id:

            venta = get_sale(venta_id)

            if venta:

                nuevo_pagado = (
                    float(venta["total"])
                    - float(restante)
                )

                cursor.execute("""
                    UPDATE ventas
                    SET pagado = ?,
                        saldo = ?
                    WHERE id = ?
                """, (
                    nuevo_pagado,
                    restante,
                    venta_id
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return True


# ======================================================
# 📋 DEUDAS POR CLIENTE
# ======================================================
def debts_by_client(cliente_id: int):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT

                d.id,
                d.cliente_id,
                d.venta_id,
                d.monto_total,
                d.estado,
                d.fecha,
                d.descripcion,

                dd.id AS detalle_id,
                dd.producto_id,
                dd.cantidad,
                dd.precio_unitario,
                dd.estado AS estado_detalle

            FROM deudas d

            LEFT JOIN deudas_detalle dd
                ON d.id = dd.deuda_id

            WHERE d.cliente_id = ?

            ORDER BY d.fecha DESC
        """, (cliente_id,))

        rows = cursor.fetchall()

    finally:
        conn.close()

    if not rows:
        return []

    deudas_map = {}

    for r in rows:

        deuda_id = r["id"]

        if deuda_id not in deudas_map:

            deudas_map[deuda_id] = {
                "id": r["id"],
                "cliente_id": r["cliente_id"],
                "venta_id": r["venta_id"],
                "monto_total": r["monto_total"],
                "estado": r["estado"],
                "fecha": r["fecha"],
                "descripcion": r["descripcion"],
                "detalles": []
            }

        if r["detalle_id"] is not None:

            deudas_map[deuda_id]["detalles"].append({
                "id": r["detalle_id"],
                "producto_id": r["producto_id"],
                "cantidad": float(r["cantidad"]),
                "precio_unitario": float(r["precio_unitario"]),
                "estado": r["estado_detalle"]
            })

    return list(deudas_map.values())


# ======================================================
# 🗑️ ELIMINAR DEUDA
# ======================================================
def delete_debt(
    deuda_id: int,
    usuario: Optional[str] = None
) -> bool:

    deuda = get_debt(deuda_id)

    if not deuda:
        return False

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM deudas_detalle
            WHERE deuda_id = ?
        """, (deuda_id,))

        cursor.execute("""
            DELETE FROM deudas
            WHERE id = ?
        """, (deuda_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    update_debt(
        deuda["cliente_id"],
        -float(deuda["monto_total"])
    )

    return True


# ======================================================
# 📊 DETALLE DEUDAS
# ======================================================
def list_detalle_deudas():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT

                dd.id AS detalle_id,
                dd.deuda_id,
                dd.producto_id,
                dd.cantidad,
                dd.precio_unitario,
                dd.estado,

                d.cliente_id,
                d.fecha,
                d.monto_total,
                d.estado AS estado_deuda

            FROM deudas_detalle dd

            JOIN deudas d
                ON d.id = dd.deuda_id

            ORDER BY d.fecha DESC
        """)

        rows = cursor.fetchall()

        return [dict(r) for r in rows]

    finally:
        conn.close()


# ======================================================
# 👤 CLIENTES CON DEUDA
# ======================================================
def list_clientes_con_deuda():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT

                c.id,
                c.nombre,
                c.deuda_total

            FROM clientes c

            JOIN deudas d
                ON c.id = d.cliente_id

            WHERE LOWER(d.estado) = 'pendiente'
            AND c.deuda_total > 0

            ORDER BY c.nombre
        """)

        rows = cursor.fetchall()

        return [dict(r) for r in rows]

    finally:
        conn.close()


# ======================================================
# 📄 FACTURA PDF
# ======================================================
def generar_factura_pago_deuda(
    cliente,
    productos_pagados,
    deuda_id=None,
    usuario="desconocido",
    metodo_pago="Efectivo",
    observaciones="",
    logo_path="assets/logo.png"
):

    buffer = BytesIO()

    c = canvas.Canvas(
        buffer,
        pagesize=letter
    )

    width, height = letter

    logo = None

    if os.path.exists(logo_path):

        try:
            logo = ImageReader(logo_path)
        except:
            pass

    fecha_pago = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    def draw(y_offset=0):

        current_y = height - 50 - y_offset

        if logo:

            c.drawImage(
                logo,
                40,
                current_y - 30,
                width=80,
                height=60,
                preserveAspectRatio=True
            )

        c.setFont("Helvetica-Bold", 16)

        c.drawString(
            140,
            current_y,
            "RECIBO DE PAGO"
        )

        current_y -= 30

        c.setFont("Helvetica", 10)

        c.drawString(40, current_y, f"Cliente: {cliente.get('nombre', '')}")
        c.drawString(40, current_y - 15, f"Fecha: {fecha_pago}")
        c.drawString(40, current_y - 30, f"Usuario: {usuario}")

        if observaciones:
            c.drawString(40, current_y - 45, f"Observaciones: {observaciones}")

        items = []
        for p in productos_pagados:
            items.append([
                p.get("nombre", "Producto"),
                p.get("cantidad", 0),
                p.get("precio_unitario", 0),
                p.get("cantidad", 0) * p.get("precio_unitario", 0)
            ])

        table_data = [["Producto", "Cantidad", "Precio", "Subtotal"]]
        table_data.extend(items)

        table = Table(table_data, colWidths=[220, 70, 70, 70])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
        ]))

        table.wrapOn(c, 0, 0)
        table.drawOn(c, 40, current_y - 120)

        c.showPage()

    draw()
    c.save()
    return buffer.getvalue()