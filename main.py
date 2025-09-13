# main.py
import streamlit as st
from contextlib import contextmanager

from database import setup_db, cursor
from ui import login_page, main_page, load_css, app_header
from utils import initialize_deepface

# Configuration de la page
st.set_page_config(page_title="DGSN - Reconnaissance Faciale", page_icon="logo.png", layout="wide")

# Initialisations
initialize_deepface()
if cursor:
    setup_db()
load_css()
app_header()

# Gestion de l'état "busy"
if "busy" not in st.session_state:
    st.session_state["busy"] = False

st.markdown("""
<div id="status-chip"><div class="chip"><div class="spinner"></div>Traitement...</div></div>
""", unsafe_allow_html=True)
_status_placeholder = st.empty()

def _set_busy(state: bool):
    st.session_state["busy"] = state
    if state:
        _status_placeholder.markdown("<script>document.getElementById('status-chip').style.display='block';</script>", unsafe_allow_html=True)
    else:
        _status_placeholder.markdown("<script>document.getElementById('status-chip').style.display='none';</script>", unsafe_allow_html=True)

@contextmanager
def show_running(message="Traitement en cours..."):
    _set_busy(True)
    with st.spinner(message):
        try:
            yield
        finally:
            _set_busy(False)

# Logique d'authentification et de routage
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
else:
    main_page()