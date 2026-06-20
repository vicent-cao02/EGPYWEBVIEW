import streamlit as st
import pandas as pd
from io import BytesIO
import uuid
import os
import sys
import datetime
import subprocess
import platform

from pathlib import Path
from backend import clientes, productos, deudas
from backend.deudas import generar_factura_pago_deuda


# =========================================================
# 🔐 VALIDACIÓN DE SESIÓN
# =========================================================
if "usuario" not in st.session_state or not st.session_state.usuario:
    st.warning("Debes iniciar sesión para acceder.")
    st.stop()


# =========================================================
# 📦 SESSION STATE
# =========================================================
if "refresh" not in st.session_state:
    st.session_state.refresh = False


# =========================================================
# ⚡ CACHÉ
# =========================================================
@st.cache_data(ttl=60)
def load_clientes_con_deuda():
    return deudas.list_clientes_con_deuda() or []

@st.cache_data(ttl=60)
def load_productos_map():
    return productos.map_productos() or {}

@st.cache_data(ttl=60)
def load_deudas_cliente(cid: int):
    return deudas.debts_by_client(cid) or []

@st.cache_data(ttl=60)
def load_detalle_deudas():
    return deudas.list_detalle_deudas() or []

@st.cache_data(ttl=60)
def load_clientes_dict():
    lista = clientes.list_clients() or []
    return {c["id"]: c["nombre"] for c in lista}


# =========================================================
# ⚙️ CONFIGURACIÓN
# =========================================================
st.set_page_config(page_title="Gestión de Deudas", layout="wide")
st.title("💳 Gestión de Deudas")


# =========================================================
# 📁 EXPORTS
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
# 📊 CARGA DE DATOS
# =========================================================
clientes_con_deuda = load_clientes_con_deuda()
productos_map = load_productos_map()
clientes_dict = load_clientes_dict()

clientes_opciones = {c["nombre"]: c["id"] for c in clientes_con_deuda}
lista_nombres = list(clientes_opciones.keys())


# =========================================================
# 👤 SELECCIÓN CLIENTE
# =========================================================
st.subheader("Seleccionar cliente")

seleccion_cliente = st.selectbox("Clientes con deuda", [""] + lista_nombres)

if seleccion_cliente:

    cliente_id = clientes_opciones[seleccion_cliente]
    cliente_obj = clientes.get_client(cliente_id)

    deuda_total = float(cliente_obj.get("deuda_total", 0) or 0)

    st.markdown(
        f"### Deuda total: **${deuda_total:,.2f}**"
    )


    # =====================================================
    # 📌 DEUDAS DEL CLIENTE
    # =====================================================
    deudas_cliente = load_deudas_cliente(cliente_id)

    filas = []

    for deuda in deudas_cliente:
        for det in deuda.get("detalles", []):

            if (det.get("estado") or "").lower() != "pendiente":
                continue

            cantidad = float(det.get("cantidad") or 0)
            precio = float(det.get("precio_unitario") or 0)

            filas.append({
                "deuda_id": deuda.get("deuda_id"),
                "detalle_id": det.get("id"),
                "producto_id": det.get("producto_id"),
                "producto": productos_map.get(det.get("producto_id"), "Producto"),
                "cantidad": cantidad,
                "precio": precio,
                "monto": cantidad * precio,
                "fecha": str(deuda.get("fecha"))[:19]
            })

    df = pd.DataFrame(filas)


    # =====================================================
    # 📋 TABLA
    # =====================================================
    st.subheader("Deudas pendientes")

    if df.empty:
        st.info("No hay deudas pendientes.")
    else:
        st.dataframe(
            df.sort_values("fecha", ascending=False)[
                ["producto", "cantidad", "precio", "monto", "fecha"]
            ],
            use_container_width=True,
            height=250
        )


        # =================================================
        # 💳 SELECCIÓN DE PAGO
        # =================================================
        opciones = {
            f"{r['producto']} | {r['fecha']} | ${r['monto']:.2f}": r
            for _, r in df.iterrows()
        }

        seleccion = st.selectbox(
            "Selecciona deuda a pagar",
            [""] + list(opciones.keys())
        )


        if seleccion:

            detalle = opciones[seleccion]

            st.markdown(f"### Monto: ${detalle['monto']:.2f}")

            monto_pago = st.number_input(
                "Monto a pagar",
                min_value=0.01,
                max_value=float(detalle["monto"]),
                value=float(detalle["monto"])
            )


            # =================================================
            # 💰 PROCESO DE PAGO
            # =================================================
            if st.button("Registrar pago"):

                try:
                    deudas.pay_debt_producto(
                        deuda_id=detalle["deuda_id"],
                        producto_id=detalle["producto_id"],
                        monto_pago=monto_pago,
                        usuario=st.session_state.usuario
                    )

                    # 📄 Generar factura
                    factura = [{
                        "nombre": detalle["producto"],
                        "cantidad": detalle["cantidad"],
                        "precio_unitario": detalle["precio"]
                    }]

                    pdf = generar_factura_pago_deuda(
                        cliente_obj,
                        factura
                    )

                    # =====================================================
                    # 📁 GUARDAR PDF
                    # =====================================================

                    timestamp = datetime.datetime.now().strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    pdf_filename = (
                        f"Pago_Deuda_{detalle['deuda_id']}_{timestamp}.pdf"
                    )

                    pdf_path = PDF_DIR / pdf_filename

                    with open(pdf_path, "wb") as f:
                        f.write(pdf)

                    st.success("✅ Comprobante PDF guardado correctamente")

                    st.info(f"📁 {pdf_path}")

                    # =====================================================
                    # 🚀 ABRIR PDF AUTOMÁTICAMENTE
                    # =====================================================

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
                    # 🔄 limpiar cache
                    st.cache_data.clear()

                    st.success("Pago registrado correctamente")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {str(e)}")



st.divider()
st.subheader("Comprobantes generados")


if st.session_state.comprobantes:

    for pdf in reversed(st.session_state.comprobantes):

        if st.button("📥 Generar Excel"):

            try:

                timestamp = datetime.datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                excel_filename = (
                    f"Deudas_{timestamp}.xlsx"
                )

                excel_path = EXCEL_DIR / excel_filename

                with open(excel_path, "wb") as f:
                    f.write(buffer.getvalue())

                st.success("✅ Excel generado correctamente")

                st.info(f"📁 {excel_path}")

                # =============================================
                # 🚀 ABRIR AUTOMÁTICAMENTE
                # =============================================

                sistema = platform.system()

                if sistema == "Windows":

                    os.startfile(excel_path)

                elif sistema == "Darwin":

                    subprocess.call([
                        "open",
                        str(excel_path)
                    ])

                else:

                    subprocess.call([
                        "xdg-open",
                        str(excel_path)
                    ])

            except Exception as e:

                st.error(f"Error generando Excel: {str(e)}")

else:
    st.info("No hay comprobantes generados.")


# =========================================================
# 📊 TODAS LAS DEUDAS
# =========================================================
st.divider()
st.subheader("Todas las deudas pendientes")


detalles = load_detalle_deudas()

filas = []

for d in detalles:

    if str(d.get("estado", "")).lower() != "pendiente":
        continue

    cantidad = float(d.get("cantidad") or 0)
    precio = float(d.get("precio_unitario") or 0)

    filas.append({
        "cliente": clientes_dict.get(d.get("cliente_id"), "Desconocido"),
        "producto": productos_map.get(d.get("producto_id"), "Producto"),
        "cantidad": cantidad,
        "precio": precio,
        "monto": cantidad * precio,
        "fecha": str(d.get("fecha"))[:19]
    })


df_all = pd.DataFrame(filas)


if df_all.empty:
    st.info("No hay deudas pendientes.")
else:
    st.dataframe(df_all, use_container_width=True, height=400)

    # 📥 Excel
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_all.to_excel(writer, index=False, sheet_name="Deudas")

    st.download_button(
        "Descargar Excel",
        buffer.getvalue(),
        file_name="deudas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )