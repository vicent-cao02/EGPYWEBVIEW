"""
Módulo para manejar deudas y pagos por producto en SQLite.

Funciones públicas:
- list_debts()
- get_debt(deuda_id)
- add_debt(cliente_id, venta_id=None, productos=None, usuario=None)
- pay_debt_producto(deuda_id, producto_id, monto_pago, usuario=None)
- debts_by_client(cliente_id)
- delete_debt(deuda_id, usuario=None)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .db import get_connection
from .clientes import update_debt
from backend.ventas import get_sale
from backend import ventas


# ======================================================
# 📜 Listar todas las deudas
# ======================================================
def list_debts() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deudas ORDER BY fecha DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ======================================================
# 🔍 Obtener deuda con detalles
# ======================================================
def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id AS deuda_id, d.cliente_id, d.venta_id, d.monto_total, d.estado, d.fecha, d.descripcion,
                   dd.id AS detalle_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado AS estado_detalle
            FROM deudas d
            LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
            WHERE d.id = ?
            ORDER BY dd.id
        """, (deuda_id,))
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    if not rows:
        return None

    deuda_info = dict(rows[0])
    detalles = []
    for r in rows:
        if r["detalle_id"] is not None:
            detalles.append({
                "id": r["detalle_id"],
                "producto_id": r["producto_id"],
                "cantidad": r["cantidad"],
                "precio_unitario": r["precio_unitario"],
                "estado": r["estado_detalle"]
            })

    deuda_info["detalles"] = detalles

    # Quitar columnas repetidas de detalle
    for k in ["detalle_id", "producto_id", "cantidad", "precio_unitario", "estado_detalle"]:
        deuda_info.pop(k, None)

    return deuda_info


# ======================================================
# ➕ Crear deuda con detalles por producto
# ======================================================
def add_debt(
    cliente_id: int,
    venta_id: int = None,
    productos: list = None,
    monto_total: float = 0.0,
    estado: str = "pendiente",
    usuario: str = None
) -> int:
    """
    Crea una deuda principal y registros por producto en deudas_detalle.
    """
    fecha = datetime.now().isoformat()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Insertar deuda principal
        cursor.execute("""
            INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cliente_id, venta_id, monto_total, estado, fecha, f"Deuda generada por venta {venta_id or 'N/A'}"))
        conn.commit()

        deuda_id = cursor.lastrowid

        # Insertar detalles por producto
        if productos:
            for p in productos:
                cursor.execute("""
                    INSERT INTO deudas_detalle (deuda_id, producto_id, cantidad, precio_unitario, estado)
                    VALUES (?, ?, ?, ?, 'pendiente')
                """, (deuda_id, p["id_producto"], p["cantidad"], p["precio_unitario"]))
            conn.commit()
    finally:
        conn.close()

    update_debt(cliente_id, monto_total)
    return deuda_id


# ======================================================
# 💵 Registrar pago de deuda por producto
# ======================================================

def pay_debt_producto(deuda_id: int, producto_id: int, monto_pago: float, usuario=None):
    deuda = get_debt(deuda_id)
    if not deuda:
        raise KeyError(f"Deuda {deuda_id} no encontrada")

    detalle = next((d for d in deuda.get("detalles", []) if d.get("producto_id") == producto_id), None)
    if not detalle:
        raise KeyError(f"Producto {producto_id} no encontrado en la deuda {deuda_id}")

    precio_unitario = float(detalle["precio_unitario"])
    cantidad_pagada = monto_pago / precio_unitario
    nueva_cantidad = max(float(detalle["cantidad"]) - cantidad_pagada, 0)
    nuevo_estado_det = "pagado" if nueva_cantidad == 0 else "pendiente"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Actualizar detalle
        cursor.execute("""
            UPDATE deudas_detalle
            SET cantidad = ?, estado = ?
            WHERE id = ?
        """, (nueva_cantidad, nuevo_estado_det, detalle["id"]))

        # Actualizar estado de deuda principal
        cursor.execute("""
            SELECT SUM(cantidad * precio_unitario)
            FROM deudas_detalle
            WHERE deuda_id = ? AND estado = 'pendiente'
        """, (deuda_id,))
        total_restante = cursor.fetchone()[0] or 0

        estado_deuda = "pagada" if total_restante <= 0 else "pendiente"
        cursor.execute("""
            UPDATE deudas
            SET estado = ?
            WHERE id = ?
        """, (estado_deuda, deuda_id))

        # Actualizar venta asociada
        if total_restante <= 0:
            deuda["estado"] = "pagada"
            venta_id = deuda.get("venta_id")
            if venta_id:
                venta = get_sale(venta_id)
                if venta:
                    venta["pagado"] = venta["total"]
                    ventas.editar_venta_extra(
                        sale_id=venta_id,
                        observaciones=venta.get("observaciones"),
                        usuario=usuario
                    )
        
        conn.commit()
    finally:
        conn.close()

    return {"detalle": detalle, "estado_deuda": estado_deuda}


# ======================================================
# 📋 Listar deudas por cliente
# ======================================================
def debts_by_client(cliente_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id AS deuda_id, d.cliente_id, d.venta_id, d.monto_total, d.estado, d.fecha, d.descripcion,
                   dd.id AS detalle_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado AS estado_detalle
            FROM deudas d
            LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
            WHERE d.cliente_id = ?
            ORDER BY d.fecha DESC, dd.id
        """, (cliente_id,))
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    if not rows:
        return []

    deudas_map = {}
    for r in rows:
        d_id = r["deuda_id"]
        if d_id not in deudas_map:
            deudas_map[d_id] = dict(r)
            deudas_map[d_id]["detalles"] = []

        if r["detalle_id"] is not None:
            deudas_map[d_id]["detalles"].append({
                "id": r["detalle_id"],
                "producto_id": r["producto_id"],
                "cantidad": r["cantidad"],
                "precio_unitario": r["precio_unitario"],
                "estado": r["estado_detalle"]
            })

    # Limpiar columnas repetidas de detalle
    for deuda in deudas_map.values():
        for k in ["detalle_id", "producto_id", "cantidad", "precio_unitario", "estado_detalle"]:
            deuda.pop(k, None)

    return list(deudas_map.values())


# ======================================================
# 🗑️ Eliminar deuda
# ======================================================
def delete_debt(deuda_id: int, usuario: Optional[str] = None) -> bool:
    deuda = get_debt(deuda_id)
    if not deuda:
        return False

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deudas_detalle WHERE deuda_id = ?", (deuda_id,))
        cursor.execute("DELETE FROM deudas WHERE id = ?", (deuda_id,))
        conn.commit()
    finally:
        conn.close()

    update_debt(deuda["cliente_id"], -float(deuda["monto_total"]))

    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_deuda", {
            "deuda_id": deuda_id,
            "cliente_id": deuda["cliente_id"],
            "monto_total": deuda["monto_total"]
        })
    except Exception:
        pass

    return True


# ======================================================
# 📊 Listar todos los detalles de deudas
# ======================================================
def list_detalle_deudas():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dd.id AS detalle_id, dd.deuda_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado,
                   d.cliente_id, d.fecha, d.monto_total, d.estado AS estado_deuda
            FROM deudas_detalle dd
            JOIN deudas d ON d.id = dd.deuda_id
            ORDER BY d.fecha DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ======================================================
# 📋 Listar clientes con deudas pendientes
# ======================================================
def list_clientes_con_deuda():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.id, c.nombre, c.deuda_total
            FROM clientes c
            JOIN deudas d ON c.id = d.cliente_id
            WHERE d.estado = 'pendiente' AND c.deuda_total > 0
            ORDER BY c.nombre
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ======================================================
# 📄 Generar Factura de Pago de Deuda (PDF)
# ======================================================
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
import os
from datetime import datetime

# Contador simple global para número de deuda
DEUDA_COUNTER = 1

def generar_factura_pago_deuda(
    cliente,
    productos_pagados,
    deuda_id=None,
    usuario="desconocido",
    metodo_pago="Efectivo",
    observaciones="",
    logo_path="assets/logo.png"
):
    """
    Genera un PDF de factura de pago de deuda para un cliente,
    duplicada en la misma hoja (una copia para el cliente y otra para archivo interno).
    """
    global DEUDA_COUNTER
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    line_height = 15

    # Cargar logo local
    logo = None
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")

    # Generar número de deuda consecutivo si no se pasa
    if deuda_id is None:
        deuda_id = DEUDA_COUNTER
        DEUDA_COUNTER += 1

    # Fecha de pago actual
    fecha_pago = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def draw_factura(y_offset=0):
        nonlocal c
        current_y = height - 50 - y_offset

        # Logo
        if logo:
            c.drawImage(logo, 40, current_y - 30, width=80, height=60, preserveAspectRatio=True)

        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawString(140, current_y, "RECIBO DE PAGO DE DEUDA")
        current_y -= 30

        # Información de la empresa
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, current_y, "Omar Galíndez Ramirez. CI: 85082506984")
        current_y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(40, current_y, f"Recibo N°: {deuda_id}")
        c.drawString(300, current_y, f"Fecha: {fecha_pago}")
        current_y -= 20

        # Información del cliente
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, current_y, "Cliente:")
        c.setFont("Helvetica", 10)
        c.drawString(100, current_y, cliente.get("nombre", ""))
        current_y -= 15
        c.drawString(40, current_y, "CI:")
        c.drawString(100, current_y, cliente.get("ci", ""))
        current_y -= 15
        c.drawString(40, current_y, "Chapa:")
        c.drawString(100, current_y, cliente.get("chapa", ""))
        current_y -= 20

        # Información del pago
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, current_y, "Método de Pago:")
        c.setFont("Helvetica", 10)
        c.drawString(140, current_y, metodo_pago)
        current_y -= 15
        c.drawString(40, current_y, "Usuario:")
        c.drawString(140, current_y, usuario)
        current_y -= 20

        # Tabla de productos pagados
        table_data = [["Producto", "Cantidad", "Precio Unitario", "Total Pagado"]]
        total_pagado = 0

        for p in productos_pagados:
            nombre = p.get("nombre", "")
            cantidad = float(p.get("cantidad", 0))
            precio_unitario = float(p.get("precio_unitario", 0))
            subtotal = cantidad * precio_unitario
            total_pagado += subtotal

            table_data.append([
                nombre,
                f"{cantidad:.0f}",
                f"${precio_unitario:.2f}",
                f"${subtotal:.2f}"
            ])

        # Agregar fila de total
        table_data.append(["", "", "TOTAL:", f"${total_pagado:.2f}"])

        table = Table(table_data, colWidths=[150, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(1,1),(-1,-1),'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (-1,-1), (-1,-1), colors.lightgrey),
            ('FONTNAME', (-1,-1), (-1,-1), 'Helvetica-Bold')
        ]))

        table.wrapOn(c, width, height)
        table.drawOn(c, 40, current_y - len(table_data)*20 - 20)

        # Observaciones
        if observaciones:
            current_y -= len(table_data)*20 + 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, current_y, "Observaciones:")
            current_y -= 15
            c.setFont("Helvetica", 9)
            words = observaciones.split()
            line = ""
            for word in words:
                if c.stringWidth(line + word, "Helvetica", 9) < 500:
                    line += word + " "
                else:
                    c.drawString(40, current_y, line.strip())
                    current_y -= 12
                    line = word + " "
            if line.strip():
                c.drawString(40, current_y, line.strip())

        # Firmas
        firma_y = current_y - 60
        c.setFont("Helvetica", 10)
        c.drawString(40, firma_y, "__________________________")
        c.drawString(40, firma_y - 10, "Firma Cliente")
        c.drawString(300, firma_y, "__________________________")
        c.drawString(300, firma_y - 10, "Firma Vendedor")

    # Dibujar dos copias en la misma hoja
    draw_factura(y_offset=0)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(1)
    c.line(40, height/2, width-40, height/2)
    draw_factura(y_offset=height/2)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
