import streamlit as st
import pandas as pd
from backend.clientes import list_clients, add_client, update_client, delete_client
import ui.error_handler as handle_app_error

# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]


# ---------------------------
# Cache de clientes con TTL (10s)
# ---------------------------
@st.cache_data(ttl=10)
def cached_clients():
    return list_clients()

clientes_data = cached_clients()

try:
    clientes_data = cached_clients()

        
    st.set_page_config(page_title="Gestión de Clientes", layout="wide")
    st.title("👥 Gestión de Clientes")


    # ---------------------------
    # Filtros por nombre o id
    # ---------------------------
    col1, col2 = st.columns(2)
    with col1:
        filtro_nombre = st.text_input("Filtrar por nombre", key="filtro_nombre")
    with col2:
        filtro_id = st.text_input("Filtrar por ID", key="filtro_id")

    # Filtrado seguro: si no hay filtro, se muestran todos
    def filter_clients(c):
        match_nombre = filtro_nombre.lower() in str(c["nombre"]).lower() if filtro_nombre else True
        match_id = filtro_id in str(c["id"]) if filtro_id else True
        return match_nombre and match_id

    clientes_filtrados = [c for c in clientes_data if filter_clients(c)]

    # ---------------------------
    # Tabla editable de clientes
    # ---------------------------
    # Tabla editable de clientes
    if clientes_filtrados:
        df = pd.DataFrame(clientes_filtrados)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "nombre": st.column_config.TextColumn("Nombre"),
                "direccion": st.column_config.TextColumn("Dirección"),
                "telefono": st.column_config.TextColumn("Teléfono"),
                "ci": st.column_config.TextColumn("CI"),
                "chapa": st.column_config.TextColumn("Chapa"),
                "deuda_total": st.column_config.NumberColumn("Deuda Total", disabled=True)
            }
        )

        if st.button("💾 Guardar cambios"):
            for _, row in edited_df.iterrows():
                update_client(
                    row["id"],
                    nombre=row["nombre"],
                    direccion=row.get("direccion",""),
                    telefono=row.get("telefono",""),
                    ci=row.get("ci",""),
                    chapa=row.get("chapa",""),
                    usuario=usuario_actual
                )

            st.success("✅ Clientes actualizados")
            # Limpiar cache para mostrar los cambios inmediatamente
            if "cached_clients" in st.session_state:
                del st.session_state["cached_clients"]
            st.rerun()
    else:
        st.info("No hay clientes que coincidan con los filtros.")

    # ---------------------------
    # Crear nuevo cliente
    # ---------------------------
    st.subheader("➕ Crear nuevo cliente")
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        nombre_nuevo = st.text_input("Nombre *", key="nombre_nuevo")
        direccion_nueva = st.text_input("Dirección", key="direccion_nueva")
        telefono_nuevo = st.text_input("Teléfono", key="telefono_nuevo")
        ci_nuevo = st.text_input("CI", key="ci_nuevo")
        chapa_nueva = st.text_input("Chapa", key="chapa_nueva")
        submitted = st.form_submit_button("Crear cliente")

        if submitted:
            if not nombre_nuevo.strip():
                st.error("❌ El nombre no puede estar vacío.")
            else:
                try:
                    cliente = add_client(
                        nombre=nombre_nuevo,
                        telefono=telefono_nuevo,
                        ci=ci_nuevo,
                        chapa=chapa_nueva,
                        direccion=direccion_nueva
                    )
                    if cliente:
                        st.success(f"✅ Cliente '{cliente['nombre']}' creado con ID {cliente['id']}")
                        # Limpiar cache para mostrarlo inmediatamente
                        if "cached_clients" in st.session_state:
                            del st.session_state["cached_clients"]
                        st.rerun()
                    else:
                        st.error("❌ No se pudo crear el cliente.")
                except Exception as e:
                    st.error(f"❌ Error al crear cliente: {str(e)}")

    # ---------------------------
    # Eliminar cliente con selector
    # ---------------------------
    st.subheader("🗑 Eliminar cliente")

    # Crear opciones con "ID - Nombre"
    opciones_clientes = [f"{c['id']} - {c['nombre']}" for c in clientes_data]

    if opciones_clientes:
        cliente_seleccionado = st.selectbox("Seleccionar cliente a eliminar", opciones_clientes, key="cliente_a_eliminar")
        # Extraer el ID del string seleccionado
        id_eliminar = cliente_seleccionado.split(" - ")[0]

        if st.button("Eliminar cliente"):
            try:
                delete_client(id_eliminar, usuario=usuario_actual)
                st.success(f"❌ Cliente con ID {id_eliminar} eliminado")
                # Limpiar cache para refrescar inmediatamente
                if "cached_clients" in st.session_state:
                    del st.session_state["cached_clients"]
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al eliminar cliente: {str(e)}")
    else:
        st.info("No hay clientes para eliminar.")

except Exception as e:
    handle_app_error(e, "Error al cargar o procesar los datos de clientes. Por favor, intenta nuevamente.")