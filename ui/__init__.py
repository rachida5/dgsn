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
    st.markdown(
        """
        <style>
            .login-wrapper {
                min-height: calc(100vh - 80px);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            .login-card {
                background: #1b263b;
                padding: 2rem;
                border-radius: 8px;
                width: 100%;
                max-width: 400px;
            }
            .block-container {
                max-width: 900px;
                margin: 0 auto;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">🔒 Connexion</h1>', unsafe_allow_html=True)
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
    st.markdown("</div></div>", unsafe_allow_html=True)


def main_page() -> None:
    st.sidebar.title("📌 Navigation")

    pages = {
        "➕ Ajouter": "Ajouter",
        "🔍 Rechercher": "Rechercher",
        "📄 Voir": "Voir",
    }

    if "page" not in st.session_state:
        st.session_state.page = "Rechercher"

    choice = st.sidebar.radio(
        "Changer de page",
        list(pages.keys()),
        index=list(pages.values()).index(st.session_state.page),
        label_visibility="collapsed",
    )
    st.session_state.page = pages[choice]

    if st.session_state.page == "Ajouter":
        if st.session_state.get("is_admin"):
            add_criminal_page()
        else:
            st.warning("Accès réservé aux administrateurs.")
    elif st.session_state.page == "Rechercher":
        search_criminal_page()
    elif st.session_state.page == "Voir":
        if "editing_criminal_id" in st.session_state and st.session_state.editing_criminal_id is not None:
            edit_criminal_page(st.session_state.editing_criminal_id)
        else:
            list_criminals_page()

    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter", use_container_width=True):
        with st.spinner("Déconnexion..."):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["authenticated"] = False
        st.rerun()

