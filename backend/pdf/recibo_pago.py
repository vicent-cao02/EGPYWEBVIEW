from io import BytesIO
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle


def generar_recibo_pago(cliente, productos_pagados, deuda_id=None, usuario="desconocido", metodo_pago="Efectivo", observaciones="", logo_path="assets/logo.png"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    logo = None
    if logo_path and os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
        except Exception:
            logo = None

    fecha_pago = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    current_y = height - 50

    if logo:
        c.drawImage(logo, 40, current_y - 30, width=80, height=60, preserveAspectRatio=True)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, current_y, "RECIBO DE PAGO")
    current_y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, current_y, f"Fecha: {fecha_pago}")
    current_y -= 15
    c.drawString(40, current_y, f"Cliente: {cliente.get('nombre', '')}")
    current_y -= 15
    c.drawString(40, current_y, f"CI: {cliente.get('ci', '')}")
    current_y -= 20

    table_data = [["Producto", "Cantidad", "Precio", "Total"]]
    total = 0.0

    for p in productos_pagados:
        cantidad = float(p.get("cantidad", 0))
        precio = float(p.get("precio_unitario", 0))
        subtotal = cantidad * precio
        total += subtotal
        table_data.append([
            p.get("nombre", "Producto"),
            str(cantidad),
            f"${precio:,.2f}",
            f"${subtotal:,.2f}"
        ])

    table_data.append(["", "", "TOTAL", f"${total:,.2f}"])

    table = Table(table_data, colWidths=[220, 70, 70, 70])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 40, current_y - 120)

    current_y -= 140 + len(table_data) * 18
    c.drawString(40, current_y, f"Método de pago: {metodo_pago}")
    c.drawString(40, current_y - 15, f"Usuario: {usuario}")
    if observaciones:
        c.drawString(40, current_y - 30, f"Observaciones: {observaciones}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
