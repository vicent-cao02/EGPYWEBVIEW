import streamlit as st


DEFAULT_SESSION = {
    "usuario": None,
    "refresh": False,
    "carrito": [],
    "cliente_actual": None,
    "venta_actual": None,
    "comprobantes": [],
    "deuda_actual": None,
}


def init_session():
    for key, value in DEFAULT_SESSION.items():
        if key not in st.session_state:
            st.session_state[key] = value