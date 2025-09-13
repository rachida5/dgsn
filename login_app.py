import streamlit as st
from time import time, sleep

from auth import authenticate_user
from database import setup_db, cursor
from utils import initialize_deepface
from ui import main_page, load_css, app_header


def apply_brand_css() -> None:
    """Injecte le bloc CSS de marque."""
    st.markdown(
        """
        <style>
        :root {
            --brand-bg: #0d1b2a; /* à ajuster selon charte DGSN */
            --brand-surface: #1b263b; /* à ajuster selon charte DGSN */
            --brand-accent: #d32f2f; /* à ajuster selon charte DGSN */
            --brand-border: rgba(255,255,255,0.1); /* à ajuster selon charte DGSN */
            --brand-text: #ffffff; /* à ajuster selon charte DGSN */
            --brand-muted: #8b949e; /* à ajuster selon charte DGSN */
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--brand-bg);
            color: var(--brand-text);
        }
        [data-testid="block-container"] {
            max-width: 1000px;
            padding-top: 0;
            padding-bottom: 0;
        }
        .app-center {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        .login-card {
            background: var(--brand-surface);
            border: 1px solid var(--brand-border);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 480px;
            padding: 2.5rem 2rem;
        }
        .login-card img {
            display: block;
            margin: 0 auto 1.5rem auto;
            height: auto;
        }
        .page-title {
            position: relative;
            text-align: center;
            margin-bottom: 2rem;
            color: var(--brand-text);
        }
        .page-title::after {
            content: "";
            position: absolute;
            bottom: -0.5rem;
            left: 50%;
            transform: translateX(-50%);
            width: 40px;
            height: 4px;
            background: var(--brand-accent);
            border-radius: 2px;
        }
        .muted { color: var(--brand-muted); }
        .accent { color: var(--brand-accent); }
        .danger { color: var(--brand-accent); }
        .link-button button {
            background: none;
            border: none;
            color: var(--brand-accent);
            text-decoration: underline;
            padding: 0;
        }
        .link-button button:hover {
            color: var(--brand-text);
            background: none;
        }
        .stTextInput>div>div>input {
            color: var(--brand-text);
        }
        .stTextInput>div>div>input:focus {
            border-color: var(--brand-accent);
            box-shadow: 0 0 0 1px var(--brand-accent);
        }
        .stCheckbox>label {
            color: var(--brand-text);
        }
        .stButton>button {
            background: var(--brand-accent);
            color: var(--brand-bg);
            border-radius: 8px;
            border: 1px solid var(--brand-border);
        }
        .stButton>button:hover:enabled {
            filter: brightness(1.1);
        }
        .stButton>button:focus {
            outline: 2px solid var(--brand-accent);
            outline-offset: 2px;
        }
        .stButton>button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        @media (max-width: 600px) {
            .login-card {
                padding: 2rem 1rem;
                max-width: 90%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    st.markdown("<div class='app-center'><div class='login-card'>", unsafe_allow_html=True)
    st.image("logo.png", width=96)
    st.markdown("<h1 class='page-title'>Connexion</h1>", unsafe_allow_html=True)

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

    st.markdown("<div class='link-button' style='text-align:right'>", unsafe_allow_html=True)
    forgot_clicked = st.button("Mot de passe oublié ?")
    st.markdown("</div>", unsafe_allow_html=True)

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

    st.markdown("</div></div>", unsafe_allow_html=True)

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
    apply_brand_css()
    build_login_page()
