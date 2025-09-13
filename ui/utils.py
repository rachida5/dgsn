"""UI helper functions."""
import os
import base64
import streamlit as st


def load_css(file_name: str = "style.css") -> None:
    """Injecte le CSS de base et applique le thème de l'application."""
    base_css = ""
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            base_css = f.read()

    theme_css = """
:root {
  --brand-bg: #0d1b2a;
  --brand-surface: #1b263b;
  --brand-accent: #d32f2f;
  --brand-border: #415a77;
  --brand-text: #e0e0e0;
  --brand-muted: #778da9;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--brand-bg);
  color: var(--brand-text);
}

#fixed-header {
  background: var(--brand-surface);
  color: var(--brand-text);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.block-container {
  padding-top: 100px;
  max-width: 1200px;
}

.app-center {
  min-height: calc(100vh - 80px);
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-card {
  background: var(--brand-surface);
  padding: 2.5rem 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  width: 100%;
  max-width: 480px;
}

.login-title {
  color: var(--brand-accent);
  text-align: center;
  margin-bottom: 1.5rem;
}

[data-testid="stSidebar"] {
  background: var(--brand-bg);
}

[data-testid="stSidebar"] > div:first-child {
  display: flex;
  flex-direction: column;
  height: 100%;
}

[data-testid="stSidebar"] .sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 1rem 1rem;
}

[data-testid="stSidebar"] .sidebar-logo {
  height: 40px;
}

[data-testid="stSidebar"] .sidebar-title {
  font-weight: 700;
  color: var(--brand-text);
}

[data-testid="stSidebar"] [role="radiogroup"] {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

[data-testid="stSidebar"] [role="radiogroup"] > label {
  padding: 0.75rem 1rem;
  border-left: 4px solid transparent;
  border-radius: 8px;
  cursor: pointer;
}

[data-testid="stSidebar"] [role="radiogroup"] > label:hover {
  background: rgba(255,255,255,0.05);
}

[data-testid="stSidebar"] [role="radiogroup"] > label[aria-checked="true"] {
  background: rgba(255,255,255,0.08);
  border-left-color: var(--brand-accent);
  color: var(--brand-accent);
}

.card {
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 16px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  padding: 1.5rem;
}

.card > h1:first-child,
.card > h2:first-child,
.card > h3:first-child {
  margin-top: 0;
  margin-bottom: 1rem;
  border-bottom: 3px solid var(--brand-accent);
  padding-bottom: 0.25rem;
}

[data-testid="stSidebar"] .sidebar-footer {
  margin-top: auto;
  font-size: 0.8rem;
  color: var(--brand-muted);
  padding: 1rem;
  border-top: 1px solid var(--brand-border);
}
"""

    st.markdown(f"<style>{base_css}\n{theme_css}</style>", unsafe_allow_html=True)


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
      {"<img src='data:image/png;base64," + _logo + "' style='height:60px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));'>" if _logo else ""}
      <span>DGSN — Système de Reconnaissance Faciale</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
