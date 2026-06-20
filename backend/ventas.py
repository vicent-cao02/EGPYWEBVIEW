import json
from datetime import datetime
from typing import Dict, Optional, List

from backend.db import get_connection
from backend.logs import registrar_log


# =========================================================
# 🛒 REGISTRAR VENTA (ROBUSTO + STOCK SEGURO)
# =========================================================
def register_sale(
    cliente_id: int,
    total: float,
    pagado: float,
    usuario: str,
    tipo_pago: str,
    productos: List[Dict]
):

    if not productos:
        raise ValueError("No hay productos en la venta")

    conn = get_connection()
    cursor = conn.cursor()

    total = float(total)
    pagado = float(pagado)
    saldo = total - pagado
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # =====================================================
        # VALIDAR IDs DE PRODUCTOS
        # =====================================================
        ids = tuple(
            p.get("id_producto") or p.get("id")
            for p in productos
        )

        if not ids:
            raise ValueError("Productos inválidos")

        query = f"""
            SELECT id, nombre, cantidad, precio
            FROM productos
            WHERE id IN ({','.join(['?'] * len(ids))})
        """

        productos_db = cursor.execute(query, ids).fetchall()
        productos_map = {p[0]: p for p in productos_db}

        productos_final = []

        for item in productos:

            prod_id = item.get("id_producto") or item.get("id")
            cantidad = float(item.get("cantidad"))
            precio = float(item.get("precio_unitario"))

            if prod_id not in productos_map:
                raise ValueError(f"Producto ID {prod_id} no existe")

            producto = productos_map[prod_id]
            stock = float(producto[2])

            if cantidad <= 0:
                raise ValueError("Cantidad inválida")

            if cantidad > stock:
                raise ValueError(
                    f"Stock insuficiente para {producto[1]} (Disponible: {stock})"
                )

            productos_final.append({
                "id_producto": prod_id,
                "nombre": producto[1],
                "cantidad": cantidad,
                "precio_unitario": precio,
                "subtotal": round(cantidad * precio, 2)
            })

        # =====================================================
        # DESCONTAR STOCK (SEGURO)
        # =====================================================
        for p in productos_final:

            cursor.execute("""
                UPDATE productos
                SET cantidad = cantidad - ?
                WHERE id = ? AND cantidad >= ?
            """, (
                p["cantidad"],
                p["id_producto"],
                p["cantidad"]
            ))

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Stock insuficiente (concurrencia) producto {p['id_producto']}"
                )

        # =====================================================
        # INSERTAR VENTA (AJUSTADO A NUEVA TABLA)
        # =====================================================
        cursor.execute("""
            INSERT INTO ventas (
                cliente_id,
                fecha,
                pagado,
                saldo,
                productos_vendidos,
                total,
                tipo_pago,
                usuario
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            fecha,
            pagado,
            saldo,
            json.dumps(productos_final),
            total,
            tipo_pago,
            usuario
        ))

        venta_id = cursor.lastrowid
        

        conn.commit()

        registrar_log(usuario, "registrar_venta", {
            "venta_id": venta_id,
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "saldo": saldo
        })

        return {
            "id": venta_id,
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "saldo": saldo,
            "productos": productos_final
        }

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()
# =========================================================
# ✏️ EDITAR CAMPOS EXTRA
# =========================================================
def editar_venta_extra(
    sale_id: int,
    observaciones: Optional[str] = None,
    vendedor: Optional[str] = None,
    telefono_vendedor: Optional[str] = None,
    chofer: Optional[str] = None,
    chapa: Optional[str] = None,
    usuario: Optional[str] = None
):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE ventas
            SET observaciones = COALESCE(?, observaciones),
                vendedor = COALESCE(?, vendedor),
                telefono_vendedor = COALESCE(?, telefono_vendedor),
                chofer = COALESCE(?, chofer),
                chapa = COALESCE(?, chapa)
            WHERE id = ?
        """, (
            observaciones,
            vendedor,
            telefono_vendedor,
            chofer,
            chapa,
            sale_id
        ))

        conn.commit()

        registrar_log(usuario or "system", "editar_venta_extra", {
            "venta_id": sale_id
        })

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# 📋 LISTAR VENTAS
# =========================================================
def list_sales():

    conn = get_connection()
    cursor = conn.cursor()

    try:
        rows = cursor.execute("""
            SELECT * FROM ventas ORDER BY fecha DESC
        """).fetchall()

        ventas = []

        for r in rows:

            try:
                productos = json.loads(r[6]) if r[6] else []
            except:
                productos = []

            ventas.append({
                "id": r[0],
                "cliente_id": r[1],
                "fecha": r[2],
                "subtotal": r[3],
                "pagado": r[4],
                "saldo": r[5],
                "productos_vendidos": productos,
                "total": r[7],
                "tipo_pago": r[8],
                "usuario": r[9],
                "observaciones": r[10],
                "vendedor": r[11],
                "telefono_vendedor": r[12],
                "chofer": r[13],
                "chapa": r[14]
            })

        return ventas

    finally:
        conn.close()


# =========================================================
# 🔍 OBTENER VENTA
# =========================================================
def get_sale(sale_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        r = cursor.execute("""
            SELECT * FROM ventas WHERE id = ?
        """, (sale_id,)).fetchone()

        if not r:
            return None

        try:
            productos = json.loads(r[6]) if r[6] else []
        except:
            productos = []

        return {
            "id": r[0],
            "cliente_id": r[1],
            "fecha": r[2],
            "subtotal": r[3],
            "pagado": r[4],
            "saldo": r[5],
            "productos_vendidos": productos,
            "total": r[7],
            "tipo_pago": r[8],
            "usuario": r[9],
            "observaciones": r[10],
            "vendedor": r[11],
            "telefono_vendedor": r[12],
            "chofer": r[13],
            "chapa": r[14]
        }

    finally:
        conn.close()


# =========================================================
# 💵 ACTUALIZAR PAGO (CRÍTICO PARA DEUDAS)
# =========================================================
def update_sale_payment(sale_id: int, pagado: float, saldo: float):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE ventas
            SET pagado = ?,
                saldo = ?
            WHERE id = ?
        """, (pagado, saldo, sale_id))

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# 🗑️ ELIMINAR VENTA (STOCK + DEUDA + CONSISTENCIA TOTAL)
# =========================================================
def delete_sale(sale_id: int, usuario: str = None):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        sale = get_sale(sale_id)

        if not sale:
            return False

        cliente_id = sale["cliente_id"]

        # =================================================
        # 🔥 RESTAURAR STOCK
        # =================================================
        for item in sale["productos_vendidos"]:

            cursor.execute("""
                UPDATE productos
                SET cantidad = cantidad + ?
                WHERE id = ?
            """, (
                item["cantidad"],
                item["id_producto"]
            ))

        # =================================================
        # 🔍 ELIMINAR DEUDA SI EXISTE
        # =================================================
        cursor.execute("""
            SELECT id, monto_total
            FROM deudas
            WHERE venta_id = ?
        """, (sale_id,))

        deuda = cursor.fetchone()

        if deuda:

            deuda_id = deuda[0]
            monto = float(deuda[1] or 0)

            cursor.execute("""
                DELETE FROM deudas_detalle
                WHERE deuda_id = ?
            """, (deuda_id,))

            cursor.execute("""
                DELETE FROM deudas
                WHERE id = ?
            """, (deuda_id,))

            cursor.execute("""
                UPDATE clientes
                SET deuda_total = deuda_total - ?
                WHERE id = ?
            """, (monto, cliente_id))

        # =================================================
        # 🗑️ ELIMINAR VENTA
        # =================================================
        cursor.execute("""
            DELETE FROM ventas
            WHERE id = ?
        """, (sale_id,))

        conn.commit()

        registrar_log(usuario or "system", "eliminar_venta", {
            "venta_id": sale_id,
            "cliente_id": cliente_id
        })

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# 📊 UTILIDAD UI
# =========================================================
def listar_ventas_dict():

    ventas = list_sales()

    return {
        f"ID {v['id']} - Cliente {v['cliente_id']} - ${v['total']}": v
        for v in ventas
    }

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os

def generar_factura_pdf(venta, cliente, productos_vendidos, gestor_info=None, logo_path="assets/logo.png"):
    """
    Genera una factura profesional en PDF mostrando todos los productos de la venta,
    duplicada en la misma hoja (para cliente y archivo interno).

    venta: dict con info de la venta
    cliente: dict con info del cliente
    productos_vendidos: lista de dicts {nombre, cantidad, precio_unitario}
    gestor_info: dict opcional con datos del vendedor/chofer
    logo_path: ruta local a logo de la empresa
    """
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

    def draw_multiline_text(c, text, x, y, max_width, line_height=12, font_name="Helvetica", font_size=10):
        """
        Dibuja texto ajustándolo automáticamente al ancho máximo permitido.
        Devuelve la nueva coordenada Y después de escribir el texto.
        """
        c.setFont(font_name, font_size)

        words = str(text).split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        for line in lines:
            c.drawString(x, y, line)
            y -= line_height

        return y

    def dibujar_factura(y_offset=0):
        nonlocal c

        # ---------------- Logo ----------------
        if logo:
            c.drawImage(logo, 40, height - 85 - y_offset, width=80, height=70, preserveAspectRatio=True)

        # ------------- Empresa ----------------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(130, height - 50 - y_offset, "Omar Galíndez Ramirez. CI: 85082506984")
        c.setFont("Helvetica", 10)
        c.drawString(130, height - 65 - y_offset, f"Factura N°: {venta.get('numero', venta.get('id',''))}")
        c.drawString(130, height - 80 - y_offset, f"Fecha: {venta.get('fecha','')}")

        # ------------- Columnas ----------------
        col1_x = 40
        col2_x = 320
        row_y = height - 110 - y_offset

        # Campos cliente, vacíos si no hay info
        cliente_nombre = cliente.get("nombre") or ""
        cliente_ci = cliente.get("ci") or ""
        cliente_chapa = cliente.get("chapa") or ""
        cliente_direccion = cliente.get("direccion") or ""
        cliente_telefono = cliente.get("telefono") or ""

        c.drawString(col1_x, row_y, f"Cliente: {cliente_nombre}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Carnet/ID: {cliente_ci}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Chapa: {cliente_chapa}"); row_y -= line_height
        row_y = draw_multiline_text(
            c,
            f"Dirección: {cliente_direccion}",
            col1_x,
            row_y,
            max_width=250,  
            line_height=line_height
        )
        c.drawString(col1_x, row_y, f"Teléfono: {cliente_telefono}"); row_y -= line_height

        # Totales y pagos
        total = float(venta.get("total") or 0)
        pagado_usd = float(venta.get("pagado") or 0)
        saldo = float(venta.get("saldo") or 0)
        metodo_pago = venta.get("tipo_pago") or ""
        vendedor = gestor_info.get("vendedor","") if gestor_info else ""
        chofer = gestor_info.get("chofer","") if gestor_info else ""
        chapa_vehiculo = gestor_info.get("chapa","") if gestor_info else ""
        observaciones = venta.get("observaciones","")

        tasa_cup = 120
        pagado_cup = pagado_usd * tasa_cup
        pagado_str = f"(USD) {pagado_usd:,.2f} - (CUP) {pagado_cup:,.2f}"

        row_y2 = height - 110 - y_offset
        c.drawString(col2_x, row_y2, f"Total: ${total:.2f}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Pagado: {pagado_str}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Saldo pendiente: ${saldo:.2f}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Método de pago: {metodo_pago}"); row_y2 -= line_height
        if observaciones:
            row_y2 = draw_multiline_text(
                c,
                f"Observaciones: {observaciones}",
                col2_x,
                row_y2,
                max_width=220,
                line_height=line_height
            )
        c.drawString(col2_x, row_y2, f"Vendedor: {vendedor}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Chofer: {chofer}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Chapa: {chapa_vehiculo}"); row_y2 -= line_height

        # ------------- Tabla de productos ----------------
        table_y_start = row_y - 40
        table_data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
        for p in productos_vendidos:
            nombre = p.get("nombre","")
            cantidad = float(p.get("cantidad") or 0)
            precio_unitario = float(p.get("precio_unitario") or 0)
            subtotal = cantidad * precio_unitario
            table_data.append([nombre, str(int(cantidad)), f"${precio_unitario:.2f}", f"${subtotal:.2f}"])

        table = Table(table_data, colWidths=[200, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(1,1),(-1,-1),'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        table.wrapOn(c, 50, table_y_start - 20)
        table.drawOn(c, 50, table_y_start - len(table_data)*18 - 20)

        # ------------- Firma doble ----------------
        firma_y = table_y_start - len(table_data)*18 - 60
        c.drawString(40, firma_y -30, "__________________________")
        c.drawString(40, firma_y - 40, "Firma Cliente")
        c.drawString(320, firma_y -30 ,"__________________________")
        c.drawString(320, firma_y - 40, "Firma Vendedor")

    # Dibujar dos facturas en la misma hoja
    dibujar_factura(y_offset=0)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(1)
    c.line(40, height/2, width-40, height/2)
    dibujar_factura(y_offset=height/2)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
