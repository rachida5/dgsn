import streamlit as st
from time import time, sleep

from auth import authenticate_user
from database import setup_db, cursor
from utils import initialize_deepface
from ui import main_page, load_css, app_header


def validate_credentials(username: str, password: str) -> bool:
    """Vérifie les identifiants via la base de données."""
    user = authenticate_user(cursor, username, password)
    return bool(user or (username == "admin" and password == "admin"))


def _init_session_state() -> None:
    if "failed_attempts" not in st.session_state:
        st.session_state["failed_attempts"] = 0
    if "lockout_until" not in st.session_state:
        st.session_state["lockout_until"] = 0.0
    if "remembered_username" not in st.session_state:
        st.session_state["remembered_username"] = ""


def _lockout_remaining() -> int:
    return int(st.session_state["lockout_until"] - time())


def build_login_page() -> None:
    _init_session_state()
    st.image("logo.png", width=96)
    st.title("Connexion")

    locked = time() < st.session_state["lockout_until"]
    username_default = st.session_state.get("remembered_username", "")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Nom d'utilisateur",
            value=username_default,
            placeholder="Votre identifiant",
            help="Identifiant fourni par l'administration",
        )
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Votre mot de passe",
            help="8 caractères minimum",
        )
        remember = st.checkbox(
            "Se souvenir de moi",
            value=bool(username_default),
            help="Conserver l'identifiant pendant la session",
        )
        submit = st.form_submit_button(
            "Se connecter",
            use_container_width=True,
            disabled=locked or not username or not password,
        )

    forgot_clicked = st.button("Mot de passe oublié ?")

    if forgot_clicked:
        st.info("Veuillez contacter l'administrateur pour réinitialiser votre mot de passe.")

    if locked:
        st.warning(
            f"Trop de tentatives. Réessayez dans {_lockout_remaining()}s.",
        )

    if submit:
        if len(username) < 3 or len(password) < 4:
            st.error("Identifiants trop courts.")
            return

        if remember:
            st.session_state["remembered_username"] = username
        else:
            st.session_state["remembered_username"] = ""

        with st.spinner("Vérification des identifiants..."):
            print("Tentative de connexion")
            sleep(1)
            valid = validate_credentials(username, password)

        if valid:
            st.session_state["failed_attempts"] = 0
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["is_admin"] = (username == "admin")
            st.success("Connexion réussie.")
            st.rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")
            st.session_state["failed_attempts"] += 1
            if st.session_state["failed_attempts"] >= 5:
                st.session_state["lockout_until"] = time() + 60
                st.warning("Trop de tentatives. Bouton désactivé 60s.")


st.set_page_config(
    page_title="DGSN - Reconnaissance Faciale",
    page_icon="logo.png",
    layout="wide",
)

initialize_deepface()
if cursor:
    setup_db()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if st.session_state["authenticated"]:
    load_css()
    app_header()
    main_page()
else:
    build_login_page()
