import streamlit as st
from backend.usuarios import autenticar_usuario
from datetime import datetime

st.set_page_config(page_title="Login | ElectroGalíndez", layout="centered")

# ─────────────────────────────────────────────
# Inicializar sesión
# ─────────────────────────────────────────────
usuario = st.session_state.get("usuario", None)

# ─────────────────────────────────────────────
# Si ya está logueado → no volver a pedir login
# ─────────────────────────────────────────────
if usuario:
    st.sidebar.write(f"👤 Usuario: **{usuario['username']}**")
    st.sidebar.write(f"Rol: **{usuario['rol']}**")

    st.success(f"Bienvenido, {usuario['username']} ({usuario['rol']})")

    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    st.stop()  # ← evita renderizar la parte del login


# ─────────────────────────────────────────────
# UI de Login
# ─────────────────────────────────────────────
st.title("🔒 Iniciar sesión")

username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")

login_btn = st.button("Ingresar", use_container_width=True)

# ─────────────────────────────────────────────
# Procesar intento de login
# ─────────────────────────────────────────────
if login_btn:

    with st.spinner("Verificando credenciales..."):
        user = autenticar_usuario(username, password)

    if isinstance(user, dict) and user.get("bloqueado"):
        try:
            blk = datetime.fromisoformat(user["bloqueado_hasta"])
            st.error(f"⚠️ Usuario bloqueado hasta: **{blk.strftime('%Y-%m-%d %H:%M')}**")
        except:
            st.error("⚠️ Usuario bloqueado temporalmente.")
        st.stop()

    if user:
        st.session_state.usuario = user
        st.success(f"¡Bienvenido, {user['username']}!")
        st.rerun()

    else:
        st.error("❌ Usuario o contraseña incorrectos")
