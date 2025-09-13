import streamlit as st
from time import time, sleep
from PIL import Image


def apply_brand_css() -> None:
    """Injecte le bloc CSS de marque."""
    st.markdown(
        """
        <style>
        :root {
            --brand-bg: #0d1b2a; /* à adapter à la charte DGSN */
            --brand-surface: #1b263b; /* à adapter à la charte DGSN */
            --brand-accent: #d32f2f; /* à adapter à la charte DGSN */
            --brand-border: rgba(255,255,255,0.1); /* à adapter à la charte DGSN */
            --brand-text: #ffffff; /* à adapter à la charte DGSN */
            --brand-muted: #8b949e; /* à adapter à la charte DGSN */
            --header-height: 3.5rem; /* hauteur approximative de l'entête */
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--brand-bg);
            color: var(--brand-text);
        }
        [data-testid="block-container"] {
            max-width: 960px;
            padding-top: 0;
            padding-bottom: 0;
        }
        .app-center {
            min-height: calc(100dvh - var(--header-height));
            min-height: calc(100vh - var(--header-height));
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        .login-card {
            background: var(--brand-surface);
            border: 1px solid var(--brand-border);
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            padding: 24px;
            width: clamp(360px, 92vw, 480px);
        }
        .page-title {
            text-align: center;
            font-size: 30px;
            margin-bottom: 1rem;
        }
        .muted { color: var(--brand-muted); }
        .accent { color: var(--brand-accent); }
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
            height: 44px;
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
                padding: 16px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def validate_credentials(username: str, password: str) -> bool:
    """Stub d'authentification. À remplacer par la logique réelle."""
    return username == "admin" and password == "admin"


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
    locked = time() < st.session_state["lockout_until"]
    username_default = st.session_state["remembered_username"]

    st.markdown("<div class='app-center'><div class='login-card'>", unsafe_allow_html=True)

    logo = Image.open("logo.png")
    st.image(logo, width=72)
    st.markdown("<h1 class='page-title'>Connexion</h1>", unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Nom d'utilisateur",
            placeholder="Votre identifiant",
            value=username_default,
        )
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Votre mot de passe",
        )
        remember = st.checkbox("Se souvenir de moi", value=bool(username_default))
        submit = st.form_submit_button(
            "Se connecter",
            use_container_width=True,
            disabled=locked or not username or not password,
        )

    st.markdown("<div class='link-button' style='text-align:right'>", unsafe_allow_html=True)
    forgot = st.button("Mot de passe oublié ?")
    st.markdown("</div>", unsafe_allow_html=True)

    if forgot:
        st.info("Veuillez contacter l'administrateur pour réinitialiser votre mot de passe.")

    if locked:
        st.warning(f"Trop de tentatives. Réessayez dans {_lockout_remaining()}s.")

    if submit:
        if len(username) < 3 or len(password) < 4:
            st.error("Identifiants trop courts.")
            st.stop()

        if remember:
            st.session_state["remembered_username"] = username
        else:
            st.session_state["remembered_username"] = ""

        with st.spinner("Vérification des identifiants..."):
            sleep(1)
            valid = validate_credentials(username, password)

        if valid:
            st.session_state["failed_attempts"] = 0
            st.success("Connexion réussie.")
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")
            st.session_state["failed_attempts"] += 1
            if st.session_state["failed_attempts"] >= 5:
                st.session_state["lockout_until"] = time() + 60
                st.warning("Trop de tentatives. Bouton désactivé 60s.")

    st.markdown("</div></div>", unsafe_allow_html=True)


st.set_page_config(
    page_title="DGSN — Système de Reconnaissance Faciale",
    page_icon="logo.png",
    layout="wide",
)

apply_brand_css()
build_login_page()
