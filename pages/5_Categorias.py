# pages/5_Categorias.py
import streamlit as st
import pandas as pd
from backend.controllers.categorias_controller import CategoriasController
from backend import productos
import ui.error_handler as handle_app_error



# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

if st.session_state.usuario["rol"] != "admin":
    st.error("Solo usuarios con rol admin pueden acceder.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]


# ---------------------------
# Cache de categorías y productos
# ---------------------------
@st.cache_data(ttl=30)
def cargar_categorias():
    return CategoriasController.list_categories()

@st.cache_data(ttl=30)
def cargar_productos():
    return productos.list_products()

lista_categorias = cargar_categorias()
lista_productos = cargar_productos()

df_categorias = pd.DataFrame(lista_categorias)



try:
    categorias_data = cargar_categorias()
        
    st.set_page_config(page_title="Categorías", layout="wide")
    st.title("📂 Gestión de Categorías")



    # ---------------------------
    # Buscador dinámico
    # ---------------------------
    busqueda = st.text_input("🔍 Buscar por nombre o ID:")
    df_filtrado = df_categorias.copy()
    if busqueda:
        mask = (
            df_filtrado["nombre"].str.contains(busqueda, case=False, na=False) |
            df_filtrado["id"].astype(str).str.contains(busqueda)
        )
        df_filtrado = df_filtrado[mask]

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # ---------------------------
    # Selección de categoría
    # ---------------------------
    categoria_actual = None
    if not df_filtrado.empty:
        nombre_sel = st.selectbox("Selecciona una categoría", df_filtrado["nombre"].tolist())
        categoria_actual = next((c for c in lista_categorias if c["nombre"] == nombre_sel), None)

    # ---------------------------
    # Formulario Crear / Editar
    # ---------------------------
    st.subheader("➕ Crear o ✏️ Editar Categoría")
    with st.form("form_categoria"):
        nuevo_nombre = st.text_input(
            "Nombre de la categoría",
            value=categoria_actual["nombre"] if categoria_actual else ""
        )
        col1, col2 = st.columns(2)
        with col1:
            crear = st.form_submit_button("Guardar")
        with col2:
            actualizar = st.form_submit_button("Actualizar") if categoria_actual else False

        if crear:
            if nuevo_nombre.strip():
                CategoriasController.agregar_categoria(nuevo_nombre.strip(), usuario=usuario_actual)
                st.success(f"Categoría '{nuevo_nombre}' creada correctamente ✅")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("El nombre no puede estar vacío.")

        if actualizar:
            if nuevo_nombre.strip() and categoria_actual:
                CategoriasController.editar_categoria(categoria_actual["id"], nuevo_nombre.strip(), usuario=usuario_actual)
                st.success(f"Categoría actualizada a '{nuevo_nombre}' ✅")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("El nombre no puede estar vacío.")

    # ---------------------------
    # Eliminar categoría
    # ---------------------------
    st.subheader("🗑️ Eliminar Categoría")
    if categoria_actual:
        asociados = [p for p in lista_productos if p.get("categoria_id") == categoria_actual["id"]]
        if asociados:
            st.warning(
                f"No puedes eliminar la categoría '{categoria_actual['nombre']}' porque tiene {len(asociados)} productos asociados."
            )
            with st.expander("Ver productos asociados"):
                for p in asociados:
                    st.text(f"- {p['nombre']} (ID: {p['id']})")
        else:
            confirmar = st.checkbox(f"Sí, quiero eliminar '{categoria_actual['nombre']}'")
            if confirmar and st.button("Eliminar definitivamente"):
                try:
                    CategoriasController.eliminar_categoria(categoria_actual["id"], usuario=usuario_actual)
                    st.success(f"Categoría '{categoria_actual['nombre']}' eliminada correctamente ✅")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {str(e)}")
    else:
        st.info("Selecciona una categoría para editar o eliminar.")
except Exception as e:
    handle_app_error(e, "Error al cargar o procesar los datos de categorías. Por favor, intenta nuevamente.")   