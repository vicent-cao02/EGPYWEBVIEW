# pages/1_Inventario.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from backend import productos, categorias, clientes
from ui.export_utils import exportar_excel, abrir_archivo
from ui.error_handler import handle_app_error

# ---------------------------
# CONFIGURACIÓN DE PÁGINA (ARRIBA SIEMPRE)
# ---------------------------
st.set_page_config(page_title="Inventario", layout="wide")

# ---------------------------
# VALIDAR SESIÓN
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

if st.session_state.usuario["rol"] != "admin":
    st.error("Solo usuarios con rol admin pueden acceder.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]

# ---------------------------
# CACHE
# ---------------------------
@st.cache_data(ttl=60)
def cached_clientes():
    return {c["id"]: c for c in clientes.list_clients() or []}

@st.cache_data(ttl=60)
def load_categories():
    cats = categorias.list_categories() or []
    return cats, {c["id"]: c["nombre"] for c in cats}

# ---------------------------
# LOAD DATA
# ---------------------------
def load_products():
    return productos.list_products() or []

categorias_lista, cat_id_to_name = load_categories()

try:
    clientes_data = cached_clientes()
    productos_lista = load_products()

    # ---------------------------
    # TITLE
    # ---------------------------
    st.title("📦 Gestión de Inventario")

    # ---------------------------
    # MÉTRICAS (DASHBOARD)
    # ---------------------------
    col1, col2, col3 = st.columns(3)

    total_productos = len(productos_lista)
    stock_bajo = sum(1 for p in productos_lista if p.get("cantidad", 0) <= 5)
    

    col1.metric("📦 Productos", total_productos)
    col2.metric("⚠️ Stock Bajo", stock_bajo)

    # ---------------------------
    # DATAFRAME
    # ---------------------------
    def build_df(prods):
        df = pd.DataFrame([
            {
                "ID": p["id"],
                "Nombre": p["nombre"],
                "Categoría": cat_id_to_name.get(p.get("categoria_id"), ""),
                "Cantidad": int(p.get("cantidad", 0)),
                "Precio": float(p.get("precio", 0.0)),
            } for p in prods
        ])
        return df

    def style_df(df):
        def highlight_stock(val):
            if val <= 5:
                return "background-color: #ff4d4d; color: white;"
            elif val <= 10:
                return "background-color: #ffa64d;"
            return ""

        return df.style.map(highlight_stock, subset=["Cantidad"]) \
                      .set_properties(**{"text-align": "center"})

    df_display = build_df(productos_lista)

    # ---------------------------
    # FILTROS
    # ---------------------------
    col_f1, col_f2 = st.columns([2,1])

    with col_f1:
        busqueda = st.text_input("🔍 Buscar producto")

    with col_f2:
        filtro_categoria = st.selectbox(
            "Filtrar categoría",
            ["Todas"] + [c["nombre"] for c in categorias_lista]
        )

    if busqueda:
        b = busqueda.lower()
        df_display = df_display[
            df_display["Nombre"].str.lower().str.contains(b) |
            df_display["Categoría"].str.lower().str.contains(b, na=False) |
            df_display["ID"].astype(str).str.contains(b)
        ]

    if filtro_categoria != "Todas":
        df_display = df_display[df_display["Categoría"] == filtro_categoria]

    # Formateo visual
    df_display["Precio"] = df_display["Precio"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(style_df(df_display), use_container_width=True)

    # ---------------------------
    # FORMULARIO (EXPANDER)
    # ---------------------------
    with st.expander("➕ Crear / Editar Producto", expanded=False):

        opciones = [("", None)] + [
            (f"{p['nombre']} | {cat_id_to_name.get(p['categoria_id'],'')} | {p['id']}", p["id"])
            for p in productos_lista
        ]

        seleccion = st.selectbox(
            "Selecciona un producto para editar (opcional):",
            options=opciones,
            format_func=lambda x: x[0] if isinstance(x, tuple) else "",
        )

        producto_id = seleccion[1] if isinstance(seleccion, tuple) else None
        producto_actual = productos.get_product(producto_id) if producto_id else None

        colA, colB = st.columns([2,1])

        with colA:
            nombre = st.text_input(
                "Nombre",
                value=producto_actual["nombre"] if producto_actual else ""
            )

            categoria_nombre = st.selectbox(
                "Categoría",
                options=[c["nombre"] for c in categorias_lista],
                index=[c["id"] for c in categorias_lista].index(producto_actual["categoria_id"]) if producto_actual else 0
            )

        with colB:
            precio = st.number_input(
                "Precio",
                value=float(producto_actual["precio"]) if producto_actual else 0.0,
                step=0.01,
                format="%.2f"
            )

            cantidad = st.number_input(
                "Cantidad",
                value=int(producto_actual["cantidad"]) if producto_actual else 0,
                min_value=0,
                step=1
            )

        categoria_id = next(
            (c["id"] for c in categorias_lista if c["nombre"] == categoria_nombre),
            None
        )

        col1, col2 = st.columns(2)

        # ---------------------------
        # GUARDAR
        # ---------------------------
        with col1:
            if st.button("💾 Guardar"):
                try:
                    if producto_actual:
                        productos.editar_producto(
                            producto_id=producto_actual["id"],
                            nombre=nombre,
                            precio=precio,
                            cantidad=cantidad,
                            categoria_id=categoria_id,
                            usuario=usuario_actual
                        )
                        st.success(f"Producto '{nombre}' actualizado ✅")
                    else:
                        productos.guardar_producto(
                            nombre=nombre,
                            precio=precio,
                            cantidad=cantidad,
                            categoria_id=categoria_id,
                            usuario=usuario_actual
                        )
                        st.success(f"Producto '{nombre}' creado ✅")

                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {str(e)}")

        # ---------------------------
        # ELIMINAR PRO
        # ---------------------------
        with col2:
            if producto_actual:
                if st.button("🗑️ Eliminar"):
                    st.session_state.confirm_delete = True

        if st.session_state.get("confirm_delete") and producto_actual:
            st.warning(f"¿Seguro que quieres eliminar '{producto_actual['nombre']}'?")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sí eliminar"):
                    productos.eliminar_producto(
                        producto_actual["id"],
                        usuario=usuario_actual
                    )
                    st.success("Producto eliminado ✅")
                    st.session_state.confirm_delete = False
                    st.rerun()

            with c2:
                if st.button("❌ Cancelar"):
                    st.session_state.confirm_delete = False

    # ---------------------------
    # EXPORTAR (VERSIÓN PRO)
    # ---------------------------
    from datetime import datetime

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Generar y descargar Excel"):
            excel_df = pd.DataFrame([
                {
                    "Nombre": p["nombre"],
                    "Cantidad": int(p.get("cantidad", 0)),
                }
                for p in productos_lista
            ])

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"inventario_{timestamp}.xlsx"

            ruta_archivo = exportar_excel(excel_df, nombre_archivo)

            st.session_state["last_export"] = ruta_archivo

            with open(ruta_archivo, "rb") as f:
                st.download_button(
                    label="📥 Descargar ahora",
                    data=f,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with col2:
        if "last_export" in st.session_state:
            if st.button("📂 Abrir último archivo"):
                abrir_archivo(st.session_state["last_export"])
                st.success("📂 Abriendo archivo...")

except Exception as e:
    handle_app_error(
        e,
        "Error al cargar o procesar los datos de inventario. Por favor, intenta nuevamente."
    )