# pages/7_Logs.py
import streamlit as st
import pandas as pd
import io
from backend.db import get_connection
from backend import productos

st.set_page_config(page_title="🧾 Auditoría del Sistema", layout="wide")
st.title("🧾 Auditoría del Sistema")

# ---------------------------
# Verificar sesión y rol
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()
if st.session_state.usuario["rol"] != "admin":
    st.error("Solo usuarios con rol admin pueden acceder.")
    st.stop()

# ---------------------------
# Cargar auditoría (con cache)
# ---------------------------
@st.cache_data(ttl=30)
def cargar_auditoria():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                accion,
                producto_id,
                usuario,
                fecha
            FROM auditoria
            ORDER BY fecha DESC
        """)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
    finally:
        conn.close()
    
    df = pd.DataFrame(result)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["fecha_str"] = df["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df

df = cargar_auditoria()
if df.empty:
    st.info("No hay registros de auditoría todavía.")
    st.stop()

# ---------------------------
# Mapear nombre del producto
# ---------------------------
productos_data = productos.list_products() or []
productos_map = {p["id"]: p["nombre"] for p in productos_data}
df["producto_nombre"] = df["producto_id"].map(productos_map).fillna("N/A")

# ---------------------------
# KPIs resumen
# ---------------------------
col1, col2, col3 = st.columns(3)
col1.metric("🧮 Total registros", len(df))
col2.metric("👥 Usuarios distintos", df["usuario"].nunique())
col3.metric("⚙️ Acciones distintas", df["accion"].nunique())

# ---------------------------
# Filtros en sidebar
# ---------------------------
st.sidebar.header("Filtros de auditoría")
usuarios = sorted(df["usuario"].dropna().unique())
acciones = sorted(df["accion"].dropna().unique())
productos_list = sorted(df["producto_nombre"].dropna().unique())

usuario_sel = st.sidebar.multiselect("Usuario", usuarios, default=usuarios)
accion_sel = st.sidebar.multiselect("Acción", acciones, default=acciones)
producto_sel = st.sidebar.multiselect("Producto", productos_list, default=productos_list)

# Rango de fechas
fecha_min, fecha_max = df["fecha"].min().date(), df["fecha"].max().date()
rango_fechas = st.sidebar.date_input("Rango de fechas", [fecha_min, fecha_max])
fecha_ini, fecha_fin = (rango_fechas[0], rango_fechas[-1]) if len(rango_fechas) == 2 else (fecha_min, fecha_max)

# ---------------------------
# Aplicar filtros
# ---------------------------
filtro = (
    df["usuario"].isin(usuario_sel)
    & df["accion"].isin(accion_sel)
    & df["producto_nombre"].isin(producto_sel)
    & df["fecha"].dt.date.between(fecha_ini, fecha_fin)
)
df_filtrado = df[filtro].sort_values("fecha", ascending=False)

# ---------------------------
# Búsqueda avanzada
# ---------------------------
busqueda = st.text_input("🔍 Buscar por usuario, acción o producto:")
if busqueda:
    mask = (
        df_filtrado["usuario"].str.contains(busqueda, case=False, na=False)
        | df_filtrado["accion"].str.contains(busqueda, case=False, na=False)
        | df_filtrado["producto_nombre"].str.contains(busqueda, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]

# ---------------------------
# Mostrar auditoría
# ---------------------------
st.subheader(f"📋 Registros encontrados: {len(df_filtrado)}")

def color_por_accion(val):
    colores = {"crear": "background-color:#d4edda;", "editar": "background-color:#fff3cd;", "eliminar": "background-color:#f8d7da;"}
    return colores.get(val.lower(), "")

if not df_filtrado.empty:
    df_display = df_filtrado[["fecha_str", "usuario", "accion", "producto_nombre"]].copy()
    df_display.rename(
        columns={"fecha_str": "Fecha", "usuario": "Usuario", "accion": "Acción", "producto_nombre": "Producto"},
        inplace=True,
    )

    st.dataframe(df_display.style.applymap(color_por_accion, subset=["Acción"]), use_container_width=True)

    # Exportar a Excel
    def exportar_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Auditoría")
            workbook = writer.book
            worksheet = writer.sheets["Auditoría"]

            formato_crear = workbook.add_format({"bg_color": "#d4edda"})
            formato_editar = workbook.add_format({"bg_color": "#fff3cd"})
            formato_eliminar = workbook.add_format({"bg_color": "#f8d7da"})

            for row, val in enumerate(df["Acción"], start=1):
                if val.lower() == "crear":
                    worksheet.set_row(row, None, formato_crear)
                elif val.lower() == "editar":
                    worksheet.set_row(row, None, formato_editar)
                elif val.lower() == "eliminar":
                    worksheet.set_row(row, None, formato_eliminar)

        return output.getvalue()

    excel_data = exportar_excel(df_display)
    st.download_button(
        label="📥 Descargar en Excel",
        data=excel_data,
        file_name="auditoria_sistema.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.warning("No hay registros que coincidan con los filtros o búsqueda.")
