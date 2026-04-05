import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from backend import ventas, clientes, productos
from ui.error_handler import handle_app_error

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# Cachear datos para eficiencia
# ---------------------------
@st.cache_data(ttl=60)
def cached_clients():
    return {c["id"]: c for c in clientes.list_clients() or []}
@st.cache_data(ttl=60)
def cargar_datos():
    ventas_data = ventas.list_sales() or []
    clientes_data = {c["id"]: c for c in clientes.list_clients() or []}
    productos_data = {p["id"]: p for p in productos.list_products() or []}
    return ventas_data, clientes_data, productos_data

ventas_data, clientes_data, productos_data = cargar_datos()


try:
    clientes_data = cached_clients()
    st.set_page_config(page_title="Ventas del Día", layout="wide")
    st.title("🛒 Reporte de Ventas del Día")

    # ---------------------------
    # Filtrar por fecha
    # ---------------------------
    st.subheader("📅 Filtrar por fecha")
    fecha_inicio = st.date_input("Fecha inicio", pd.Timestamp.today())
    fecha_fin = st.date_input("Fecha fin", pd.Timestamp.today())
    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser mayor que la fecha final")
        st.stop()


    # ---------------------------
    # Generar filas de ventas
    # ---------------------------
    def generar_filas(v):
        fecha_venta = pd.to_datetime(v.get("fecha", pd.Timestamp.now()))
        cliente = clientes_data.get(v.get("cliente_id"), {"nombre": "Desconocido", "telefono": ""})
        estado = "Pagada" if v.get("pagado", 0.0) >= v.get("total", 0.0) else "Pendiente"
        filas = []

        productos_vendidos = v.get("productos_vendidos") or [{"nombre": "", "cantidad": 0, "precio_unitario": 0.0, "subtotal": 0.0}]
        for p in productos_vendidos:
            filas.append({
                "ID Venta": v.get("id", ""),
                "Fecha": fecha_venta,
                "Cliente": cliente.get("nombre"),
                "Teléfono": cliente.get("telefono", ""),
                "Producto": p.get("nombre", ""),
                "Cantidad": int(p.get("cantidad", 0)),
                "Precio Unitario": float(p.get("precio_unitario", 0.0)),
                "Subtotal": float(p.get("subtotal", 0.0)),
                "Total Venta": float(v.get("total", 0.0)),
                "Pagado": float(v.get("pagado", 0.0)),
                "Saldo Pendiente": max(float(v.get("total", 0.0)) - float(v.get("pagado", 0.0)), 0.0),
                "Estado": estado
            })
        return filas

    # ---------------------------
    # Filtrar ventas por rango de fecha
    # ---------------------------
    rows = [
        fila
        for v in ventas_data
        if fecha_inicio <= pd.to_datetime(v.get("fecha", pd.Timestamp.now())).date() <= fecha_fin
        for fila in generar_filas(v)
    ]

    if not rows:
        st.info("No hay ventas registradas en este rango de fechas.")
        st.stop()

    df_ventas = pd.DataFrame(rows).sort_values("Fecha", ascending=False)

    # ---------------------------
    # Formateo y estilo
    # ---------------------------
    def formatear_monedas(x): return f"${x:,.0f}" if pd.notnull(x) else "$0"
    def alinear_derecha(s): return [ "text-align: right" for _ in s ]

    moneda_cols = ["Precio Unitario", "Subtotal", "Total Venta", "Pagado", "Saldo Pendiente"]

    df_display = df_ventas.copy()
    for col in moneda_cols:
        df_display[col] = df_display[col].round(0)

    styled_df = df_display.style.format({col: "${:,.0f}" for col in moneda_cols})\
                            .set_properties(subset=moneda_cols + ["Cantidad"], **{"text-align": "right"})\
                            .set_properties(subset=["ID Venta", "Fecha", "Cliente", "Teléfono", "Producto", "Estado"], **{"text-align": "left"})

    # ---------------------------
    # Mostrar ventas completas
    # ---------------------------
    st.subheader("📋 Todas las Ventas")
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ---------------------------
    # Ventas pagadas y pendientes
    # ---------------------------
    # Filtrar DataFrame primero
    pagadas_df = df_display[df_display["Estado"] == "Pagada"]
    pendientes_df = df_display[df_display["Estado"] == "Pendiente"]

    # Aplicar estilo a cada uno
    def aplicar_estilo(df):
        return df.style.format({col: "${:,.0f}" for col in moneda_cols})\
                .set_properties(subset=moneda_cols + ["Cantidad"], **{"text-align": "right"})\
                .set_properties(subset=["ID Venta", "Fecha", "Cliente", "Teléfono", "Producto", "Estado"], **{"text-align": "left"})

    # Mostrar ventas pagadas
    if not pagadas_df.empty:
        st.subheader("✅ Ventas Pagadas")
        st.metric("💵 Total Ventas Pagadas", f"${pagadas_df['Pagado'].sum():,.0f}")
        st.dataframe(aplicar_estilo(pagadas_df), use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas pagadas en este rango.")

    # Mostrar ventas pendientes
    if not pendientes_df.empty:
        st.subheader("⚠️ Ventas con Deuda")
        st.metric("💰 Total Pendiente", f"${pendientes_df['Saldo Pendiente'].sum():,.0f}")
        st.dataframe(aplicar_estilo(pendientes_df), use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas pendientes en este rango.")

    # ---------------------------
    # Métricas generales
    # ---------------------------
    st.subheader("📊 Métricas Generales")
    st.metric("Total ventas", f"{df_ventas['ID Venta'].nunique()}")
    st.metric("Productos vendidos", f"{df_ventas['Cantidad'].sum():,.0f}")
    st.metric("Total pagado", f"${df_ventas['Pagado'].sum():,.0f}")
    st.metric("Deuda total", f"${df_ventas['Saldo Pendiente'].sum():,.0f}")

    # ---------------------------
    # Productos más vendidos
    # ---------------------------
    st.subheader("🏆 Productos Más Vendidos")
    productos_vendidos = df_ventas.groupby("Producto")["Cantidad"].sum().reset_index()
    df_productos = pd.DataFrame([{"Producto": p["nombre"], "Precio": float(p["precio"])} for p in productos_data.values()])

    productos_vendidos = productos_vendidos.merge(df_productos, on="Producto", how="left")
    productos_vendidos["Total Vendido"] = productos_vendidos["Cantidad"] * productos_vendidos["Precio"]
    productos_vendidos = productos_vendidos.sort_values("Cantidad", ascending=False)

    # Formateo
    productos_vendidos_display = productos_vendidos.copy()
    productos_vendidos_display["Precio"] = productos_vendidos_display["Precio"].apply(lambda x: f"${x:,.0f}")
    productos_vendidos_display["Total Vendido"] = productos_vendidos_display["Total Vendido"].apply(lambda x: f"${x:,.0f}")

    st.dataframe(productos_vendidos_display, use_container_width=True, hide_index=True)

    # ---------------------------
    # Función para exportar Excel
    # ---------------------------
    def descargar_excel(df: pd.DataFrame, nombre_archivo: str):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Reporte")
        st.download_button(
            label=f"💾 Descargar {nombre_archivo}",
            data=buffer.getvalue(),
            file_name=f"{nombre_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Botones de descarga
    descargar_excel(df_ventas, f"ventas_completas_{fecha_inicio}_{fecha_fin}")
    if not pagadas_df.empty:
        descargar_excel(pagadas_df, f"ventas_pagadas_{fecha_inicio}_{fecha_fin}")
    if not pendientes_df.empty:
        descargar_excel(pendientes_df, f"ventas_pendientes_{fecha_inicio}_{fecha_fin}")

except Exception as e:
    handle_app_error(e, "Error al cargar o procesar los datos de ventas. Por favor, intenta nuevamente.")