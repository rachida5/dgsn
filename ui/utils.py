"""UI helper functions."""
import base64
import streamlit as st


def load_css(file_name: str = "style.css") -> None:
    """Charge un fichier CSS et l'applique à l'application."""
    try:
        with open(file_name, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Fichier {file_name} manquant !")


def show_running_ui(state: bool) -> None:
    """Affiche ou masque un indicateur de chargement personnalisé."""
    _status_placeholder = st.empty()
    if state:
        _status_placeholder.markdown(
            "<script>document.getElementById('status-chip').style.display='block';</script>",
            unsafe_allow_html=True,
        )
    else:
        _status_placeholder.markdown(
            "<script>document.getElementById('status-chip').style.display='none';</script>",
            unsafe_allow_html=True,
        )


def _logo_b64(path: str = "logo.png"):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def app_header() -> None:
    """Affiche l'en-tête fixe de l'application."""
    _logo = _logo_b64()
    st.markdown(
        f"""
    <div id="fixed-header">
      {{"<img src='data:image/png;base64,"+_logo+"' style='height:60px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));'>" if _logo else ""}}
      <span>DGSN — Système de Reconnaissance Faciale</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
