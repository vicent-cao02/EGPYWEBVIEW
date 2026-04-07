import streamlit as st
import streamlit.components.v1 as components
import time

# ---------------------------
# Configuración de tiempo de inactividad (por defecto 15 min)
# ---------------------------
DEFAULT_INACTIVIDAD_MINUTOS = 15

def proteger_pagina(inactividad_minutos: int = DEFAULT_INACTIVIDAD_MINUTOS):
    """
    Protege la página: requiere login y cierra sesión automáticamente
    si hay inactividad.
    """
    INACTIVIDAD_SEGUNDOS = inactividad_minutos * 60

    # Inicializar sesión
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "_last_interaction" not in st.session_state:
        st.session_state._last_interaction = time.time()

    # ---------------------------
    # Actualizar interacción automáticamente
    # ---------------------------
    st.session_state._last_interaction = time.time()

    # ---------------------------
    # Cierre de sesión por inactividad
    # ---------------------------
    if st.session_state.usuario and (time.time() - st.session_state._last_interaction > INACTIVIDAD_SEGUNDOS):
        st.session_state.usuario = None
        st.warning(f"⚠️ Sesión cerrada por inactividad ({inactividad_minutos} min).")
        st.rerun()

    # ---------------------------
    # Redirigir al login si no hay usuario
    # ---------------------------
    if st.session_state.usuario is None:
        st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
        st.stop()


def cerrar_sesion_al_cerrar():
    """
    Limpia la sesión cuando el usuario cierra o recarga el navegador.
    """
    components.html('''
        <script>
        window.addEventListener('beforeunload', function () {
            window.sessionStorage.clear();
        });
        </script>
    ''', height=0)
