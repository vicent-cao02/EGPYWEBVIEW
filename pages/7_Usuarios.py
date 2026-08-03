# pages/6_Usuarios.py
import streamlit as st
from backend.controllers.usuarios_controller import UsuariosController
import ui.error_handler as handle_app_error


st.set_page_config(page_title="Gestión de Usuarios", layout="wide")
st.title("👤 Gestión de Usuarios")
st.caption("Administra los usuarios del sistema. Solo los administradores pueden acceder a esta página.")

# ---------------------------
# Verificar sesión y rol
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()
if st.session_state.usuario["rol"] != "admin":
    st.error("Solo usuarios con rol admin pueden acceder.")
    st.stop()

# ---------------
# cache de usuarios con TTL (30s)
# ----------------------------
@st.cache_data(ttl=30)
def cached_usuarios():
    return UsuariosController.listar_usuarios()

try:
    usuarios = cached_usuarios()
        
    # ---------------------------
    # Lista de usuarios con filtros
    # ---------------------------
    usuarios = UsuariosController.listar_usuarios()
    st.subheader("🔎 Buscar y filtrar usuarios")
    col1, col2 = st.columns(2)
    with col1:
        filtro_username = st.text_input("Buscar por usuario")
    with col2:
        filtro_rol = st.selectbox("Filtrar por rol", ["Todos"] + sorted(set(u["rol"] for u in usuarios)))

    usuarios_filtrados = [
        u for u in usuarios
        if (filtro_username.lower() in u["username"].lower()) and (filtro_rol == "Todos" or u["rol"] == filtro_rol)
    ]

    st.subheader("Usuarios registrados")
    if usuarios_filtrados:
        for u in usuarios_filtrados:
            estado_texto = "Activo" if u["activo"] else "Inactivo"
            with st.expander(f"👤 {u['username']} ({estado_texto})"):
                col1, col2, col3, col4 = st.columns([2,2,2,2])
                with col1:
                    st.text_input("Usuario", value=u["username"], disabled=True)
                with col2:
                    nuevo_rol = st.selectbox(
                        "Rol", ["empleado", "admin"],
                        index=["empleado","admin"].index(u["rol"]),
                        key=f"rol_{u['username']}"
                    )
                with col3:
                    nuevo_estado = st.selectbox(
                        "Estado", ["Activo", "Inactivo"],
                        index=0 if u["activo"] else 1,
                        key=f"estado_{u['username']}"
                    )
                with col4:
                    if st.button("💾 Guardar cambios", key=f"save_{u['username']}"):
                        UsuariosController.cambiar_rol(u["username"], nuevo_rol, actor=st.session_state.usuario["username"])
                        if nuevo_estado == "Activo" and not u["activo"]:
                            UsuariosController.activar_usuario(u["username"], actor=st.session_state.usuario["username"])
                        elif nuevo_estado == "Inactivo" and u["activo"]:
                            UsuariosController.desactivar_usuario(u["username"], actor=st.session_state.usuario["username"])
                        st.success("Cambios guardados")
                        st.rerun()

                # Ver historial de acciones
                if st.button("📜 Ver historial de acciones", key=f"log_{u['username']}"):
                    logs = UsuariosController.obtener_logs_usuario(u["username"])
                    if logs:
                        for log in logs:
                            st.write(f"{log['fecha']} - {log['accion']}: {log['detalles']}")
                    else:
                        st.info("Sin historial para este usuario.")
    else:
        st.info("No hay usuarios que coincidan con los filtros.")

    st.divider()

    # ---------------------------
    # Crear nuevo usuario
    # ---------------------------
    st.subheader("➕ Crear nuevo usuario")
    with st.form("form_nuevo_usuario"):
        nuevo_user = st.text_input("Usuario *")
        nuevo_pass = st.text_input("Contraseña *", type="password")
        nuevo_rol = st.selectbox("Rol *", ["empleado", "admin"])
        submitted = st.form_submit_button("Crear usuario")
        if submitted:
            if not nuevo_user.strip():
                st.error("Ingresa un nombre de usuario.")
            else:
                try:
                    UsuariosController.crear_usuario(nuevo_user, nuevo_pass, nuevo_rol, actor=st.session_state.usuario["username"])
                    st.success(f"Usuario '{nuevo_user}' creado ✅")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.divider()

    # ---------------------------
    # Cambiar contraseña de usuario activo
    # ---------------------------
    st.subheader("🔧 Modificar usuario existente")
    usernames = [u["username"] for u in usuarios if u["activo"]]
    if usernames:
        seleccionado = st.selectbox("Selecciona usuario activo", usernames)
        new_pass = st.text_input("Nueva contraseña", key="new_pass", type="password")
        if st.button("Cambiar contraseña"):
            if not new_pass.strip():
                st.error("Ingresa una nueva contraseña.")
            else:
                UsuariosController.cambiar_password(seleccionado, new_pass, actor=st.session_state.usuario["username"])
                st.success("Contraseña actualizada ✅")
                st.rerun()
    else:
        st.info("No hay usuarios activos para modificar.")

    #selector para eliinar usuario
    st.divider()
    usuario_a_eliminar = st.selectbox("Selecciona usuario a eliminar", usernames)
    if st.button("Eliminar usuario"):
        UsuariosController.eliminar_usuario(usuario_a_eliminar, actor=st.session_state.usuario["username"])
        st.success("Usuario eliminado ✅")
        st.rerun()
except Exception as e:
    handle_app_error(e, "Error al cargar o procesar los datos de usuarios. Por favor, intenta nuevamente.")