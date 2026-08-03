import streamlit as st
import pandas as pd
import os
import sys
import datetime
import subprocess
import platform

from pathlib import Path
from backend import productos, clientes, ventas
from backend.services.ventas_service import VentasService
from backend.session import init_session


# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="Ventas Profesionales",
    layout="wide"
)

# =========================================================
# VALIDAR SESIÓN
# =========================================================
init_session()

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]

# =========================================================
# CACHE
# =========================================================
@st.cache_data(ttl=20)
def cached_clients():
    return clientes.list_clients() or []


@st.cache_data(ttl=20)
def cached_products():
    return productos.list_products() or []


@st.cache_data(ttl=20)
def cached_sales():
    return ventas.list_sales() or []


# =========================================================
# HELPERS
# =========================================================
def format_money(value):
    return f"${float(value):,.2f}"


def format_dataframe_currency(df, columns):
    df_copy = df.copy()

    for col in columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].map(format_money)

    return df_copy


# =========================================================
# CARGA DE DATOS
# =========================================================
clientes_data = cached_clients()
productos_data = cached_products()
ventas_list = cached_sales()

clientes_dict = {c["nombre"]: c["id"] for c in clientes_data}
clientes_map = {c["id"]: c["nombre"] for c in clientes_data}

# =========================================================
# SESSION STATE
# =========================================================
if "items_venta" not in st.session_state:
    st.session_state["items_venta"] = []

if "venta_ok" not in st.session_state:
    st.session_state["venta_ok"] = False

# =========================================================
# MENSAJES
# =========================================================
if st.session_state.get("venta_ok"):
    st.success("✅ Venta registrada correctamente.")
    st.session_state["venta_ok"] = False

# =========================================================
# EXPORTS DIRECTORY
# =========================================================

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

EXPORTS_DIR = BASE_DIR / "exports"

PDF_DIR = EXPORTS_DIR / "pdf"
EXCEL_DIR = EXPORTS_DIR / "excel"

PDF_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# TÍTULO
# =========================================================
st.title("🛒 Registrar Venta Profesional")

# =========================================================
# CLIENTES
# =========================================================
st.subheader("👤 Cliente")

cliente_id = None

cliente_nombre = st.selectbox(
    "Selecciona un cliente",
    [""] + list(clientes_dict.keys()),
    key="cliente_select"
)

if cliente_nombre:
    cliente_id = clientes_dict[cliente_nombre]

# =========================================================
# CREAR CLIENTE
# =========================================================
with st.expander("➕ Crear nuevo cliente"):

    with st.form("nuevo_cliente_form", clear_on_submit=True):

        nombre_nuevo = st.text_input("Nombre *")
        direccion_nueva = st.text_input("Dirección")
        telefono_nuevo = st.text_input("Teléfono")
        ci_nuevo = st.text_input("CI")
        chapa_nueva = st.text_input("Chapa")

        submitted_cliente = st.form_submit_button("Crear Cliente")

        if submitted_cliente:

            if not nombre_nuevo.strip():
                st.error("El nombre es obligatorio.")

            else:

                try:
                    clientes.add_client(
                        nombre=nombre_nuevo.strip(),
                        direccion=direccion_nueva.strip(),
                        telefono=telefono_nuevo.strip(),
                        ci=ci_nuevo.strip(),
                        chapa=chapa_nueva.strip()
                    )

                    cached_clients.clear()

                    st.success(f"Cliente '{nombre_nuevo}' creado correctamente.")

                    st.rerun()

                except Exception as e:
                    st.error(f"Error creando cliente: {str(e)}")

# =========================================================
# PRODUCTOS
# =========================================================
st.subheader("📦 Productos")

if not productos_data:
    st.warning("No hay productos registrados.")

else:

    opciones_productos = {
        f"{p['nombre']} | Stock: {p['cantidad']} | {format_money(p['precio'])}": p
        for p in productos_data
    }

    producto_nombre = st.selectbox(
        "Selecciona un producto",
        [""] + list(opciones_productos.keys()),
        key="producto_select"
    )

    if producto_nombre:

        prod = opciones_productos[producto_nombre]

        stock_actual = int(prod.get("cantidad", 0))

        if stock_actual <= 0:

            st.warning("⚠️ Producto sin stock.")

        else:

            cantidad = st.number_input(
                "Cantidad",
                min_value=1,
                max_value=stock_actual,
                value=1,
                step=1,
                key=f"cantidad_{prod['id']}"
            )

            precio = st.number_input(
                "Precio unitario",
                min_value=0.01,
                value=float(prod.get("precio", 0)),
                step=0.01,
                key=f"precio_{prod['id']}"
            )

            if st.button(f"➕ Añadir {prod['nombre']}"):

                existente = next(
                    (
                        i for i in st.session_state["items_venta"]
                        if i["id_producto"] == prod["id"]
                    ),
                    None
                )

                if existente:

                    nueva_cantidad = existente["cantidad"] + cantidad

                    if nueva_cantidad > stock_actual:
                        st.error(
                            f"Stock insuficiente. Disponible: {stock_actual}"
                        )

                    else:
                        existente["cantidad"] = nueva_cantidad
                        existente["precio_unitario"] = precio

                        st.success(
                            f"Cantidad actualizada para {prod['nombre']}."
                        )

                else:

                    st.session_state["items_venta"].append({
                        "id_producto": prod["id"],
                        "nombre": prod["nombre"],
                        "cantidad": cantidad,
                        "precio_unitario": precio
                    })

                    st.success(f"{prod['nombre']} agregado.")

# =========================================================
# ORDEN ACTUAL
# =========================================================
if st.session_state["items_venta"]:

    st.subheader("🧾 Orden Actual")

    df = pd.DataFrame(st.session_state["items_venta"])

    df["Subtotal"] = (
        df["cantidad"] * df["precio_unitario"]
    )

    total = df["Subtotal"].sum()

    df_display = format_dataframe_currency(
        df,
        ["precio_unitario", "Subtotal"]
    )

    st.dataframe(
        df_display[
            [
                "id_producto",
                "nombre",
                "cantidad",
                "precio_unitario",
                "Subtotal"
            ]
        ],
        use_container_width=True
    )

    st.subheader(f"💰 Total: {format_money(total)}")

    col1, col2 = st.columns(2)

    # =====================================================
    # VACIAR ORDEN
    # =====================================================
    with col1:

        if st.button("🗑️ Vaciar Orden"):

            st.session_state["items_venta"] = []

            st.success("Orden vaciada correctamente.")

            st.rerun()

    # =====================================================
    # REGISTRAR VENTA
    # =====================================================
    with col2:

        if cliente_id:

            pago_estado = st.radio(
                "Estado del Pago",
                ["Pagado", "Pendiente"]
            )

            tipo_pago = "Pendiente"

            if pago_estado == "Pagado":

                tipo_pago = st.selectbox(
                    "Método de Pago",
                    ["Efectivo", "Zelle"]
                )

            if st.button("💾 Registrar Venta"):

                try:

                    monto_pagado = (
                        float(total)
                        if pago_estado == "Pagado"
                        else 0.0
                    )

                    nueva_venta = VentasService.registrar_venta(
                        cliente_id=cliente_id,
                        productos=st.session_state["items_venta"],
                        total=float(total),
                        pagado=monto_pagado,
                        usuario=usuario_actual,
                        tipo_pago=tipo_pago
                    )

                    if nueva_venta.get("saldo", 0) > 0:
                        st.info(
                            f"Deuda creada: {format_money(nueva_venta['saldo'])}"
                        )

                    # =====================================
                    # LIMPIAR CACHE
                    # =====================================
                    cached_products.clear()
                    cached_sales.clear()
                    st.cache_data.clear()

                    # =====================================
                    # LIMPIAR ORDEN
                    # =====================================
                    st.session_state["items_venta"] = []

                    st.session_state["venta_ok"] = True

                    st.rerun()

                except Exception as e:
                    st.error(f"Error registrando venta: {str(e)}")

# =========================================================
# GESTIÓN DE VENTAS
# =========================================================
st.divider()

st.title("🛠️ Gestionar Ventas y Facturas")

ventas_dict = {}

for v in ventas_list:

    cliente_nombre = clientes_map.get(
        v.get("cliente_id"),
        "N/A"
    )

    fecha = ""

    fecha_obj = v.get("fecha")

    if fecha_obj:

        if hasattr(fecha_obj, "strftime"):
            fecha = fecha_obj.strftime("%d/%m/%Y %H:%M")

        else:
            fecha = str(fecha_obj)

    key = (
        f"Factura #{v.get('id')} | "
        f"{cliente_nombre} | "
        f"{fecha} | "
        f"{format_money(v.get('total', 0))}"
    )

    ventas_dict[key] = v

venta_sel = st.selectbox(
    "Selecciona una venta",
    [""] + list(ventas_dict.keys())
)

if venta_sel:

    venta_obj = ventas_dict[venta_sel]

    cliente_obj = clientes.get_client(
        venta_obj.get("cliente_id")
    )

    if not cliente_obj:
        st.error("Cliente no encontrado.")
        st.stop()

    productos_vendidos = venta_obj.get(
        "productos_vendidos",
        []
    )

    # =====================================================
    # DETALLES
    # =====================================================
    st.subheader(
        f"📄 Venta ID {venta_obj.get('id')}"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            f"**Cliente:** {cliente_obj.get('nombre', '')}"
        )

        st.markdown(
            f"**CI:** {cliente_obj.get('ci', '')}"
        )

        st.markdown(
            f"**Dirección:** {cliente_obj.get('direccion', '')}"
        )

        st.markdown(
            f"**Teléfono:** {cliente_obj.get('telefono', '')}"
        )

    with col2:

        st.markdown(
            f"**Fecha:** {venta_obj.get('fecha')}"
        )

        st.markdown(
            f"**Total:** {format_money(venta_obj.get('total', 0))}"
        )

        st.markdown(
            f"**Pagado:** {format_money(venta_obj.get('pagado', 0))}"
        )

        saldo = (
            float(venta_obj.get("total", 0))
            - float(venta_obj.get("pagado", 0))
        )

        st.markdown(
            f"**Saldo Pendiente:** {format_money(saldo)}"
        )

        st.markdown(
            f"**Tipo Pago:** {venta_obj.get('tipo_pago', '')}"
        )

        st.markdown(
            f"**Usuario:** {venta_obj.get('usuario', '')}"
        )

    # =====================================================
    # PRODUCTOS
    # =====================================================
    st.subheader("📦 Productos Vendidos")

    df_prod = pd.DataFrame(productos_vendidos)

    if not df_prod.empty:

        df_prod["Subtotal"] = (
            df_prod["cantidad"]
            * df_prod["precio_unitario"]
        )

        df_display = format_dataframe_currency(
            df_prod,
            ["precio_unitario", "Subtotal"]
        )

        st.dataframe(
            df_display[
                [
                    "nombre",
                    "cantidad",
                    "precio_unitario",
                    "Subtotal"
                ]
            ],
            use_container_width=True
        )

    else:
        st.info("No hay productos.")

    # =====================================================
    # FACTURA PDF
    # =====================================================
    with st.form("factura_form"):

        st.subheader("🖨️ Factura PDF")

        observaciones = st.text_area(
            "Observaciones",
            value=venta_obj.get("observaciones", "")
        )

        c1, c2 = st.columns(2)

        with c1:

            vendedor = st.text_input(
                "Vendedor",
                value=venta_obj.get("vendedor", "")
            )

            chofer = st.text_input(
                "Chofer",
                value=venta_obj.get("chofer", "")
            )

        with c2:

            telefono_vendedor = st.text_input(
                "Teléfono",
                value=venta_obj.get(
                    "telefono_vendedor",
                    ""
                )
            )

            chapa = st.text_input(
                "Chapa",
                value=venta_obj.get("chapa", "")
            )

        generar_pdf = st.form_submit_button(
            "Generar Factura PDF"
        )

    # =====================================================
    # GENERAR PDF
    # =====================================================
    if generar_pdf:

        try:

            venta_obj.update({
                "observaciones": observaciones,
                "vendedor": vendedor,
                "telefono_vendedor": telefono_vendedor,
                "chofer": chofer,
                "chapa": chapa
            })

            gestor_info = {
                "vendedor": (
                    f"{vendedor} (+53 {telefono_vendedor})"
                    if vendedor else ""
                ),
                "chofer": chofer,
                "chapa": chapa
            }

            # =================================================
            # GENERAR PDF EN MEMORIA
            # =================================================
            pdf_bytes = ventas.generar_factura_pdf(
                venta_obj,
                cliente_obj,
                productos_vendidos,
                gestor_info=gestor_info,
                logo_path="assets/logo.png"
            )

            # =================================================
            # TIMESTAMP
            # =================================================
            timestamp = datetime.datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            # =================================================
            # NOMBRE DEL PDF
            # =================================================
            pdf_filename = (
                f"Factura_{venta_obj.get('id')}_{timestamp}.pdf"
            )

            pdf_path = PDF_DIR / pdf_filename

            # =================================================
            # GUARDAR PDF
            # =================================================
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)

            st.success(
                f"✅ Factura guardada correctamente"
            )

            st.info(
                f"📁 {pdf_path}"
            )

            # =================================================
            # ABRIR PDF AUTOMÁTICAMENTE
            # =================================================
            sistema = platform.system()

            if sistema == "Windows":

                os.startfile(pdf_path)

            elif sistema == "Darwin":

                subprocess.call([
                    "open",
                    str(pdf_path)
                ])

            else:

                subprocess.call([
                    "xdg-open",
                    str(pdf_path)
                ])

        except Exception as e:

            st.error(
                f"Error generando PDF: {str(e)}"
            )
    # =====================================================
    # ELIMINAR VENTA
    # =====================================================
    st.divider()

    st.subheader("⚠️ Eliminar Venta")

    confirmar = st.checkbox(
        f"Confirmar eliminación de venta #{venta_obj.get('id')}"
    )

    if confirmar:

        if st.button("🗑️ Eliminar Venta"):

            try:

                ventas.delete_sale(
                    venta_obj["id"],
                    usuario=usuario_actual
                )

                cached_products.clear()
                cached_sales.clear()

                st.success(
                    f"Venta #{venta_obj['id']} eliminada correctamente."
                )

                st.rerun()

            except Exception as e:
                st.error(f"Error eliminando venta: {str(e)}")