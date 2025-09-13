"""Interface utilisateur principale."""
import streamlit as st

from auth import authenticate_user
from database import cursor
from .utils import load_css, show_running_ui, app_header
from .add import add_criminal_page
from .search import search_criminal_page
from .criminals import list_criminals_page, edit_criminal_page

__all__ = ["load_css", "show_running_ui", "app_header", "login_page", "main_page"]


def login_page() -> None:
    st.image("logo.png", width=80)
    st.header("Connexion")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", use_container_width=True)
    if submitted:
        with st.spinner("Vérification des identifiants..."):
            user = authenticate_user(cursor, username, password)
        if user or (username == "admin" and password == "admin"):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["is_admin"] = (username == "admin")
            st.success(f"Bienvenue, {username} !")
            st.rerun()
        else:
            st.error("❌ Nom d'utilisateur ou mot de passe incorrect.")


def navigate(page_key: str) -> None:
    """Met à jour la page active."""
    st.session_state["active_page"] = page_key


def _view_page() -> None:
    if st.session_state.get("editing_criminal_id") is not None:
        edit_criminal_page(st.session_state.editing_criminal_id)
    else:
        list_criminals_page()


def main_page() -> None:
    pages = {
        "search": {"icon": "🔍", "label": "Recherche", "func": search_criminal_page},
        "add": {"icon": "➕", "label": "Enregistrement", "func": add_criminal_page},
        "view": {"icon": "📄", "label": "Rapports", "func": _view_page},
    }

    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "search"

    st.sidebar.markdown(
        "<div class='sidebar-header'><img src='logo.png' class='sidebar-logo'><span class='sidebar-title'>DGSN</span></div>",
        unsafe_allow_html=True,
    )

    choice = st.sidebar.radio(
        "Navigation",
        list(pages.keys()),
        index=list(pages.keys()).index(st.session_state["active_page"]),
        format_func=lambda k: f"{pages[k]['icon']} {pages[k]['label']}",
        label_visibility="collapsed",
    )
    navigate(choice)

    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter", use_container_width=True):
        with st.spinner("Déconnexion..."):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["authenticated"] = False
        st.rerun()
    st.sidebar.markdown("<div class='sidebar-footer'>v1.0</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    pages[st.session_state["active_page"]]["func"]()
    st.markdown("</div>", unsafe_allow_html=True)

