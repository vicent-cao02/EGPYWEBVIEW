"""
Módulo para manejar deudas y pagos por producto en PostgreSQL.

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
from sqlalchemy import text
from .db import engine
from .clientes import update_debt
from backend.ventas import get_sale
from backend import ventas


# ======================================================
# 📜 Listar todas las deudas
# ======================================================
def list_debts() -> List[Dict[str, Any]]:
    query = text("SELECT * FROM deudas ORDER BY fecha DESC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


# ======================================================
# 🔍 Obtener deuda con detalles
# ======================================================
def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:
    query = text("""
        SELECT d.id AS deuda_id, d.cliente_id, d.venta_id, d.monto_total, d.estado, d.fecha, d.descripcion,
               dd.id AS detalle_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado AS estado_detalle
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.id = :deuda_id
        ORDER BY dd.id
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"deuda_id": deuda_id}).mappings().all()
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
    productos: list = None,  # lista de dicts: {id_producto, cantidad, precio_unitario}
    monto_total: float = 0.0,
    estado: str = "pendiente",
    usuario: str = None
) -> int:
    """
    Crea una deuda principal y registros por producto en deudas_detalle.
    """
    fecha = datetime.now()

    with engine.begin() as conn:
        # Insertar deuda principal
        query = text("""
            INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion)
            VALUES (:cliente_id, :venta_id, :monto_total, :estado, :fecha, :descripcion)
            RETURNING id
        """)
        deuda_id = conn.execute(query, {
            "cliente_id": cliente_id,
            "venta_id": venta_id,
            "monto_total": monto_total,
            "estado": estado,
            "fecha": fecha,
            "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}"
        }).scalar()

        # Insertar detalles por producto
        if productos:
            for p in productos:
                conn.execute(text("""
                    INSERT INTO deudas_detalle (deuda_id, producto_id, cantidad, precio_unitario, estado)
                    VALUES (:deuda_id, :producto_id, :cantidad, :precio_unitario, 'pendiente')
                """), {
                    "deuda_id": deuda_id,
                    "producto_id": p["id_producto"],
                    "cantidad": p["cantidad"],
                    "precio_unitario": p["precio_unitario"]
                })

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

    with engine.begin() as conn:
        # Actualizar detalle
        conn.execute(text("""
            UPDATE deudas_detalle
            SET cantidad=:cantidad, estado=:estado
            WHERE id=:id
        """), {"cantidad": nueva_cantidad, "estado": nuevo_estado_det, "id": detalle["id"]})

        # Actualizar estado de deuda principal
        total_restante = conn.execute(text("""
            SELECT SUM(cantidad * precio_unitario)
            FROM deudas_detalle
            WHERE deuda_id=:deuda_id AND estado='pendiente'
        """), {"deuda_id": deuda_id}).scalar() or 0

        estado_deuda = "pagada" if total_restante <= 0 else "pendiente"
        conn.execute(text("""
            UPDATE deudas
            SET estado=:estado
            WHERE id=:deuda_id
        """), {"estado": estado_deuda, "deuda_id": deuda_id})

        # Actualizar venta asociada
        if total_restante <= 0:
            deuda["estado"] = "pagada"
            venta_id = deuda.get("venta_id")
            if venta_id:
                venta = get_sale(venta_id)
                if venta:
                    venta["pagado"] = venta["total"]
                    from backend import ventas
                    ventas.editar_venta_extra(
                        sale_id=venta_id,
                        observaciones=venta.get("observaciones"),
                        usuario=usuario
                    )

    return {"detalle": detalle, "estado_deuda": estado_deuda}


# ======================================================
# 📋 Listar deudas por cliente
# ======================================================
def debts_by_client(cliente_id: int):
    query = text("""
        SELECT d.id AS deuda_id, d.cliente_id, d.venta_id, d.monto_total, d.estado, d.fecha, d.descripcion,
               dd.id AS detalle_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado AS estado_detalle
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.cliente_id = :cliente_id
        ORDER BY d.fecha DESC, dd.id
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"cliente_id": cliente_id}).mappings().all()
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

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM deudas_detalle WHERE deuda_id=:id"), {"id": deuda_id})
        conn.execute(text("DELETE FROM deudas WHERE id=:id"), {"id": deuda_id})

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
    query = text("""
        SELECT dd.id AS detalle_id, dd.deuda_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado,
               d.cliente_id, d.fecha, d.monto_total, d.estado AS estado_deuda
        FROM deudas_detalle dd
        JOIN deudas d ON d.id = dd.deuda_id
        ORDER BY d.fecha DESC
    """)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query)]


# ======================================================
# 📋 Listar clientes con deudas pendientes
# ======================================================
def list_clientes_con_deuda():
    query = text("""
        SELECT DISTINCT c.id, c.nombre, c.deuda_total
        FROM clientes c
        JOIN deudas d ON c.id = d.cliente_id
        WHERE d.estado='pendiente' AND c.deuda_total>0
        ORDER BY c.nombre
    """)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query)]
    

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

    # ---------------- Logo ----------------
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
        c.setFont("Helvetica-Bold", 14)
        c.drawString(150, current_y, "COMPROBANTE DE PAGO DE DEUDA")

        # Info deuda
        c.setFont("Helvetica", 10)
        current_y -= 40
        c.drawString(50, current_y, f"No. de Deuda: {str(deuda_id)}")
        current_y -= line_height
        c.drawString(50, current_y, f"Fecha de Pago: {fecha_pago}")
        current_y -= line_height

        # Info cliente
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, current_y, "Datos del Cliente:")
        current_y -= line_height
        c.setFont("Helvetica", 10)
        c.drawString(50, current_y, f"Nombre: {cliente.get('nombre','N/A')}"); current_y -= line_height
        c.drawString(50, current_y, f"CI / Documento: {cliente.get('ci','N/A')}"); current_y -= line_height
        c.drawString(50, current_y, f"Dirección: {cliente.get('direccion','N/A')}"); current_y -= line_height
        c.drawString(50, current_y, f"Teléfono: {cliente.get('telefono','N/A')}"); current_y -= line_height
        c.drawString(50, current_y, f"Chapa: {cliente.get('chapa','N/A')}"); current_y -= line_height + 10

        # Tabla productos
        table_y = current_y
        table_data = [["Producto", "Cantidad", "Precio Unitario", "Monto Pagado"]]
        total_pagado = 0
        for p in productos_pagados:
            cantidad = float(p.get("cantidad") or 0)
            precio = float(p.get("precio_unitario") or 0)
            subtotal = cantidad * precio
            total_pagado += subtotal
            table_data.append([p.get("nombre",""), str(int(cantidad)), f"${precio:.2f}", f"${subtotal:.2f}"])

        table = Table(table_data, colWidths=[200, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(1,1),(-1,-1),'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        table.wrapOn(c, 50, table_y - 20)
        table.drawOn(c, 50, table_y - len(table_data)*18)

        # Totales
        c.drawString(50, table_y - len(table_data)*18 - 20, f"Total Pagado: ${total_pagado:.2f}")
        c.drawString(50, table_y - len(table_data)*18 - 40, f"Método de pago: {metodo_pago or 'N/A'}")
        if observaciones:
            c.drawString(50, table_y - len(table_data)*18 - 60, f"Observaciones: {observaciones}")

        # Firmas
        firma_y = table_y - len(table_data)*18 - 100
        c.drawString(50, firma_y, "__________________________")
        c.drawString(50, firma_y - 12, "Firma Cliente")
        c.drawString(320, firma_y, "__________________________")
        c.drawString(320, firma_y - 12, "Firma Vendedor / Responsable")

    # ---------------- Dibujar dos facturas en la misma hoja ----------------
    draw_factura(y_offset=0)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(1)
    c.line(40, height/2, width-40, height/2)  # línea divisoria
    draw_factura(y_offset=height/2)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
