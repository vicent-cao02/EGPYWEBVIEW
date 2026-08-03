from io import BytesIO
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle


def generar_factura_pdf(venta_obj, cliente_obj, productos_vendidos, gestor_info=None, logo_path="assets/logo.png"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    logo = None
    if logo_path and os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
        except Exception:
            logo = None

    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    start_y = height - 50

    if logo:
        c.drawImage(logo, 40, start_y - 20, width=80, height=60, preserveAspectRatio=True)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(140, start_y, "FACTURA")
    c.setFont("Helvetica", 10)
    c.drawString(40, start_y - 20, f"Fecha: {fecha_actual}")
    c.drawString(40, start_y - 35, f"Cliente: {cliente_obj.get('nombre', '')}")
    c.drawString(40, start_y - 50, f"CI: {cliente_obj.get('ci', '')}")
    c.drawString(40, start_y - 65, f"Teléfono: {cliente_obj.get('telefono', '')}")
    c.drawString(40, start_y - 80, f"Dirección: {cliente_obj.get('direccion', '')}")

    table_data = [["Producto", "Cantidad", "Precio", "Subtotal"]]
    total = 0.0

    for item in productos_vendidos:
        cantidad = float(item.get("cantidad", 0))
        precio = float(item.get("precio_unitario", 0))
        subtotal = cantidad * precio
        total += subtotal
        table_data.append([
            item.get("nombre", "Producto"),
            str(cantidad),
            f"${precio:,.2f}",
            f"${subtotal:,.2f}"
        ])

    table_data.append(["", "", "TOTAL", f"${total:,.2f}"])

    table = Table(table_data, colWidths=[220, 70, 90, 90])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 40, start_y - 230)

    c.setFont("Helvetica", 10)
    info_y = start_y - 260 - len(table_data) * 18
    c.drawString(40, info_y, f"Forma de pago: {venta_obj.get('tipo_pago', '')}")
    c.drawString(40, info_y - 15, f"Usuario: {venta_obj.get('usuario', '')}")

    if gestor_info:
        if gestor_info.get("vendedor"):
            c.drawString(40, info_y - 30, f"Vendedor: {gestor_info['vendedor']}")
        if gestor_info.get("chofer"):
            c.drawString(40, info_y - 45, f"Chofer: {gestor_info['chofer']}")
        if gestor_info.get("chapa"):
            c.drawString(40, info_y - 60, f"Chapa: {gestor_info['chapa']}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
