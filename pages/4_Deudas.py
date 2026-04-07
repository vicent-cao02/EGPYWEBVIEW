import streamlit as st
import pandas as pd
from io import BytesIO
from backend import clientes, productos, deudas

# ===============================
# SESSION STATE INICIALIZACIÓN
# ===============================
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

if "pdf_comprobantes_lista" not in st.session_state:
    st.session_state["pdf_comprobantes_lista"] = []  # Lista de dicts: {"nombre": ..., "data": ...}

# ===============================
# CACHÉ PARA RENDIMIENTO
# ===============================
@st.cache_data(ttl=30)
def load_clientes_con_deuda():
    return deudas.list_clientes_con_deuda() or []

@st.cache_data(ttl=30)
def load_productos_map():
    return productos.map_productos() or {}

@st.cache_data(ttl=10)
def load_deudas_cliente(cid: int):
    return deudas.debts_by_client(cid) or []

@st.cache_data(ttl=20)
def load_detalle_deudas():
    return deudas.list_detalle_deudas() or []

@st.cache_data(ttl=30)
def load_clientes_dict():
    lista = clientes.list_clients() or []
    return {c["id"]: c["nombre"] for c in lista}

# ===============================
# CONFIGURACIÓN PÁGINA
# ===============================
st.set_page_config(page_title="💳 Gestión de Deudas", layout="wide")
st.title("💳 Gestión de Deudas")

# ===============================
# CARGA DE DATOS
# ===============================
clientes_con_deuda = load_clientes_con_deuda()
productos_map = load_productos_map()
clientes_dict = load_clientes_dict()
clientes_opciones = {c["nombre"]: c["id"] for c in clientes_con_deuda}
lista_nombres = [""] + list(clientes_opciones.keys())

# ===============================
# SELECTOR DE CLIENTE
# ===============================
st.subheader("👤 Selecciona un cliente con deuda")
seleccion_cliente = st.selectbox("Clientes con deuda:", lista_nombres)

if seleccion_cliente:
    cliente_id = clientes_opciones[seleccion_cliente]
    cliente_obj = clientes.get_client(cliente_id)
    deuda_total = float(cliente_obj.get("deuda_total", 0) or 0)

    st.markdown(
        f"<h4>💰 Deuda total de {seleccion_cliente}: "
        f"<span style='color:#c0392b;'>${deuda_total:,.2f}</span></h4>",
        unsafe_allow_html=True
    )

    # ===============================
    # CARGAR DEUDAS PENDIENTES DEL CLIENTE
    # ===============================
    deudas_cliente = load_deudas_cliente(cliente_id)
    filas_pendientes = []

    for deuda in deudas_cliente:
        for det in deuda.get("detalles", []):
            if (det.get("estado") or "").lower() != "pendiente":
                continue
            cantidad = float(det.get("cantidad") or 0)
            precio_unitario = float(det.get("precio_unitario") or 0)
            monto_pendiente = cantidad * precio_unitario

            filas_pendientes.append({
                "deuda_id": deuda.get("deuda_id"),
                "Detalle ID": det.get("id"),
                "Producto ID": det.get("producto_id"),
                "Producto": productos_map.get(det.get("producto_id"), "Producto"),
                "Cantidad": cantidad,
                "Precio Unitario": round(precio_unitario, 2),
                "Monto Pendiente": round(monto_pendiente, 2),
                "Fecha": str(deuda.get("fecha"))[:19],
            })

    df_pendientes = pd.DataFrame(filas_pendientes)

    st.subheader("📋 Deudas Pendientes del Cliente")
    if df_pendientes.empty:
        st.info("✔ Este cliente no tiene deudas pendientes.")
    else:
        st.dataframe(
            df_pendientes[["Producto","Cantidad", "Precio Unitario", "Monto Pendiente", "Fecha"]]
            .sort_values("Fecha", ascending=False)
            .style.format({
                "Cantidad": "{:,.0f}",
                "Precio Unitario": "${:,.2f}",
                "Monto Pendiente": "${:,.2f}"
            }),
            use_container_width=True,
            height=200
        )

        # ===============================
        # SELECTOR DE DEUDA A PAGAR
        # ===============================
        opciones_deuda = {
            f"{row['Producto']} - {row['Fecha']} (${row['Monto Pendiente']:,.2f})": row
            for _, row in df_pendientes.iterrows()
        }
        lista_opciones = list(opciones_deuda.keys())
        seleccion_detalle = st.selectbox("Selecciona una deuda pendiente:", [""] + lista_opciones)

        if seleccion_detalle:
            detalle = opciones_deuda[seleccion_detalle]
            monto_actual = detalle["Monto Pendiente"]
            detalle_id = detalle["Detalle ID"]

            st.markdown(f"### 💵 Monto pendiente de la deuda: **${monto_actual:,.2f}**")

            key_num_input = f"monto_pago_{cliente_id}_{detalle_id}"
            key_btn = f"btn_pagar_{cliente_id}_{detalle_id}"

            monto_pago = st.number_input(
                "Monto a pagar",
                min_value=0.01,
                max_value=monto_actual,
                value=monto_actual,
                step=0.01,
                key=key_num_input
            )

            if st.button(f"💳 Registrar pago (${monto_pago:,.2f})", key=key_btn):
                try:
                    # 🔹 Registrar pago
                    deudas.pay_debt_producto(
                        deuda_id=detalle["deuda_id"],
                        producto_id=detalle["Producto ID"],
                        monto_pago=monto_pago,
                        usuario=st.session_state.get("usuario", "desconocido")
                    )
                    st.success(f"💰 Pago de ${monto_pago:,.2f} registrado correctamente.")

                    # 🔹 Generar PDF inmediatamente para este detalle
                    detalle_factura = [{
                        "nombre": detalle["Producto"],
                        "cantidad": float(detalle.get("Cantidad", 0)),
                        "precio_unitario": float(detalle.get("Precio Unitario", 0))
                    }]

                    from backend.deudas import generar_factura_pago_deuda
                    pdf_bytes = generar_factura_pago_deuda(cliente_obj, detalle_factura)

                    if pdf_bytes and isinstance(pdf_bytes, (bytes, bytearray)):
                        nombre_pdf = f"ComprobantePago_{detalle['deuda_id']}_{detalle_id}.pdf"
                        st.session_state["pdf_comprobantes_lista"].append({
                            "nombre": nombre_pdf,
                            "data": pdf_bytes
                        })
                        st.success(f"📄 Comprobante generado: {nombre_pdf}")

                    # Limpiar caches
                    load_deudas_cliente.clear()
                    load_detalle_deudas.clear()
                    load_clientes_con_deuda.clear()

                    # 🔄 Forzar rerun para que se muestre botón inmediatamente
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al registrar el pago: {str(e)}")

## =========================================
# 📥 Selector de Comprobantes Generados
# =========================================
st.subheader("📥 Comprobantes Generados")

# Inicializar lista si no existe
if "pdf_comprobantes_lista" not in st.session_state:
    st.session_state["pdf_comprobantes_lista"] = []

# 🔹 Generar comprobante doble y agregarlo a la lista
if "detalle_factura" in st.session_state and "cliente_obj" in st.session_state:
    detalle = st.session_state.get("detalle_actual")  # Deuda actual seleccionada
    cliente_obj = st.session_state.get("cliente_obj")
    detalle_factura = st.session_state.get("detalle_factura")

    if detalle and cliente_obj and detalle_factura:
        pdf_bytes = generar_factura_pago_deuda(
            cliente=cliente_obj,
            productos_pagados=detalle_factura,
            deuda_id=detalle["deuda_id"],
            fecha_pago="15/02/2026",
            usuario=st.session_state.get("usuario","desconocido"),
            metodo_pago="Efectivo",
            observaciones="Pago completo de la deuda"
        )

        # Guardar en session_state
        st.session_state["pdf_comprobantes_lista"].append({
            "nombre": f"Comprobante_{detalle['deuda_id']}.pdf",
            "data": pdf_bytes
        })

# Mostrar lista de comprobantes
if st.session_state["pdf_comprobantes_lista"]:
    # Invertir la lista para que la última factura aparezca primero
    pdfs_invertidos = list(reversed(st.session_state["pdf_comprobantes_lista"]))

    # Crear diccionario para selectbox
    opciones = {pdf["nombre"]: idx for idx, pdf in enumerate(pdfs_invertidos)}
    seleccion = st.selectbox("Selecciona un comprobante para descargar:", [""] + list(opciones.keys()))
    
    if seleccion:
        idx_pdf = opciones[seleccion]
        pdf = pdfs_invertidos[idx_pdf]
        
        st.download_button(
            label=f"📄 Descargar {pdf['nombre']}",
            data=pdf["data"],
            file_name=pdf["nombre"],
            mime="application/pdf",
            key=f"download_pdf_{idx_pdf}"
        )
else:
    st.info("✔ Aún no se han generado comprobantes de pago.")

# ===============================
# TABLA GENERAL DE TODAS LAS DEUDAS PENDIENTES
# ===============================
st.subheader("📊 Todas las Deudas Pendientes")
detalles_totales = load_detalle_deudas()
filas = []

for d in detalles_totales:
    if str(d.get("estado", "pendiente")).lower() != "pendiente":
        continue
    cantidad = float(d.get("cantidad") or 0)
    precio_unitario = float(d.get("precio_unitario") or 0)
    monto_total = cantidad * precio_unitario

    filas.append({
        "Cliente": clientes_dict.get(d.get("cliente_id"), "Desconocido"),
        "Deuda ID": d.get("deuda_id"),
        "Producto": productos_map.get(d.get("producto_id"), "Producto"),
        "Cantidad": round(cantidad, 2),
        "Precio Unitario": round(precio_unitario, 2),
        "Monto Total": round(monto_total, 2),
        "Fecha": str(d.get("fecha"))[:19]
    })

df_general = pd.DataFrame(filas)

if df_general.empty:
    st.info("✔ No hay deudas pendientes.")
else:
    st.dataframe(
        df_general.sort_values(["Fecha", "Cliente"], ascending=[False, True])
        .style.format({
            "Cantidad": "{:,.0f}",
            "Precio Unitario": "${:,.2f}",
            "Monto Total": "${:,.2f}"
        }),
        use_container_width=True,
        height=400
    )

    # Exportar Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_general.to_excel(writer, index=False, sheet_name="DeudasPendientes")
    st.download_button(
        "⬇️ Descargar Excel General",
        buffer.getvalue(),
        "deudas_pendientes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
