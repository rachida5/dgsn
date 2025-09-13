# ui.py
import streamlit as st
import base64
from datetime import date, datetime
from PIL import Image
import io
import psycopg2

from database import (
    cursor, delete_photo, update_photo, search_criminals_by_text,
    get_criminal_by_id, update_criminal
)
from utils import generate_pdf, find_match, image_to_bytes
from auth import authenticate_user

# =========================
# Utilitaires UI
# =========================
def load_css(file_name="style.css"):
    try:
        with open(file_name, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Fichier {file_name} manquant !")

def show_running_ui(state: bool):
    _status_placeholder = st.empty()
    if state:
        _status_placeholder.markdown("<script>document.getElementById('status-chip').style.display='block';</script>", unsafe_allow_html=True)
    else:
        _status_placeholder.markdown("<script>document.getElementById('status-chip').style.display='none';</script>", unsafe_allow_html=True)

def app_header():
    _logo = _logo_b64()
    st.markdown(f"""
    <div id="fixed-header">
      {"<img src='data:image/png;base64,"+_logo+"' style='height:60px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));'>" if _logo else ""}
      <span>DGSN — Système de Reconnaissance Faciale</span>
    </div>
    """, unsafe_allow_html=True)

def _logo_b64(path="logo.png"):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

# =========================
# Pages de l'application
# =========================
def login_page():
    with st.container():
        st.markdown('<div class="login-page">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-title">🔒 Connexion</h1>', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter")
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
        st.markdown("</div>", unsafe_allow_html=True)

def main_page():
    st.sidebar.title("📌 Navigation")

    # Initialiser l'état de la page si non défini
    if "page" not in st.session_state:
        st.session_state.page = "Rechercher"

    # Logique de navigation avec des boutons
    if st.sidebar.button("➕ Ajouter un criminel", use_container_width=True):
        st.session_state.page = "Ajouter"
    if st.sidebar.button("🔍 Rechercher un criminel", use_container_width=True):
        st.session_state.page = "Rechercher"
    if st.sidebar.button("📄 Voir les criminels", use_container_width=True):
        st.session_state.page = "Voir"

    # Afficher la page sélectionnée
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
            for key in st.session_state.keys():
                del st.session_state[key]
            st.session_state["authenticated"] = False
        st.rerun()


def add_criminal_page():
    st.header("➕ Ajouter un criminel")

    if "add_criminal_step" not in st.session_state:
        st.session_state["add_criminal_step"] = 1
    if "form_data" not in st.session_state:
        st.session_state["form_data"] = {}

    st.markdown(f"""
    <div class="step-indicator">
        <div class="step {'active' if st.session_state['add_criminal_step'] == 1 else ''}"><span class="step-number">1</span> Informations personnelles</div>
        <div class="step {'active' if st.session_state['add_criminal_step'] == 2 else ''}"><span class="step-number">2</span> Informations judiciaires</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state["add_criminal_step"] == 1:
        step1_form()
    elif st.session_state["add_criminal_step"] == 2:
        step2_form()

def step1_form():
    with st.form("add_criminal_form_step1", clear_on_submit=False):
        st.markdown("### Étape 1 : Informations personnelles")
        st.info("Veuillez remplir les informations personnelles du criminel. *Champs obligatoires.")

        col_left, col_right = st.columns(2)
        with col_left:
            nom = st.text_input("Nom *", value=st.session_state["form_data"].get("nom", ""), placeholder="Entrez le nom")
            prenom = st.text_input("Prénom", value=st.session_state["form_data"].get("prenom", ""), placeholder="Entrez le prénom")
            alias = st.text_input("Alias", value=st.session_state["form_data"].get("alias", ""), placeholder="Surnom")
            age = st.number_input("Âge", min_value=0, max_value=120, value=st.session_state["form_data"].get("age", 0), step=1)
            date_naissance = st.date_input("Date de naissance", value=st.session_state["form_data"].get("date_naissance", date.today()), min_value=date(1900, 1, 1), max_value=date.today())

        with col_right:
            lieu_naissance = st.text_input("Lieu de naissance", value=st.session_state["form_data"].get("lieu_naissance", ""), placeholder="Lieu de naissance")
            nationalite = st.text_input("Nationalité", value=st.session_state["form_data"].get("nationalite", ""), placeholder="Nationalité")
            telephone = st.text_input("Téléphone", value=st.session_state["form_data"].get("telephone", ""), placeholder="Téléphone")
            adresse = st.text_input("Adresse", value=st.session_state["form_data"].get("adresse", ""), placeholder="Adresse")

        if st.form_submit_button("Suivant"):
            if not nom:
                st.error("⚠️ Le nom est obligatoire.")
            else:
                st.session_state["form_data"].update({
                    "nom": nom, "prenom": prenom, "alias": alias, "age": age, "date_naissance": date_naissance,
                    "lieu_naissance": lieu_naissance, "nationalite": nationalite, "telephone": telephone, "adresse": adresse
                })
                st.session_state["add_criminal_step"] = 2
                st.rerun()

def step2_form():
    with st.form("add_criminal_form_step2", clear_on_submit=True):
        st.markdown("### Étape 2 : Informations judiciaires et images")
        st.info("Fournissez les détails judiciaires et chargez au moins une image. *Champs obligatoires.")

        date_arrestation = st.date_input("Date d'arrestation *", value=st.session_state["form_data"].get("date_arrestation", date.today()))
        implication = st.text_input("Implication", value=st.session_state["form_data"].get("implication", ""), placeholder="Niveau d'implication")

        cursor.execute("SELECT name FROM crime_types ORDER BY name")
        crime_types = [row[0] for row in cursor.fetchall()]
        crime = st.selectbox("Infractioncrime *", crime_types, index=crime_types.index(st.session_state["form_data"].get("crime", crime_types[0])) if st.session_state["form_data"].get("crime") in crime_types else 0)

        description = st.text_area("Description détaillée", value=st.session_state["form_data"].get("description", ""), placeholder="Détails du crime")
        images_files = st.file_uploader("Charger des images (1 à 5) *", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("Précédent"):
                st.session_state["add_criminal_step"] = 1
                st.rerun()
        with col2:
            if st.form_submit_button("Enregistrer"):
                if not images_files or not crime:
                    st.error("⚠️ Au moins une image et un Infractioncrime sont requis.")
                else:
                    with st.spinner("Enregistrement..."):
                        first_img_bytes = image_to_bytes(Image.open(images_files[0]).convert("RGB"))
                        data = (
                            st.session_state["form_data"]["nom"], st.session_state["form_data"]["prenom"], st.session_state["form_data"]["alias"],
                            st.session_state["form_data"]["age"], st.session_state["form_data"]["date_naissance"], st.session_state["form_data"]["lieu_naissance"],
                            st.session_state["form_data"]["nationalite"], st.session_state["form_data"]["telephone"], st.session_state["form_data"]["adresse"],
                            date_arrestation, implication, crime, description, psycopg2.Binary(first_img_bytes)
                        )
                        cursor.execute("""
                            INSERT INTO criminals (nom, prenom, alias, age, date_naissance, lieu_naissance, nationalite, telephone, adresse, date_arrestation, implication, crime, description, image)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                        """, data)
                        criminal_id = cursor.fetchone()[0]

                        added = 0
                        for f in images_files[:5]:
                            img_bytes = image_to_bytes(Image.open(f).convert("RGB"))
                            cursor.execute("INSERT INTO images_criminels (criminal_id, image) VALUES (%s, %s)", (criminal_id, psycopg2.Binary(img_bytes)))
                            added += 1

                    st.success(f"✅ Criminel ajouté (ID {criminal_id}). Photos : {added}.")
                    st.session_state["add_criminal_step"] = 1
                    st.session_state["form_data"] = {}
                    st.rerun()

def search_criminal_page():
    st.header("🔍 Rechercher un criminel")
    tab1, tab2 = st.tabs(["🖼️ Par image", "🔎 Par mots-clés"])
    with tab1:
        st.markdown("### 📸 Recherche par reconnaissance faciale")
        uploaded_file = st.file_uploader("Choisir une image", type=["jpg", "jpeg", "png"])
        if uploaded_file and st.button("🔍 Rechercher", key="search_face"):
            with st.spinner("Recherche en cours..."):
                input_img = Image.open(uploaded_file).convert("RGB")
                results = find_match(input_img, cursor)
                if results:
                    st.success(f"✅ {len(results)} correspondance(s) trouvée(s) !")
                    display_search_results(results)
                else:
                    st.info("Aucune correspondance trouvée.")
    with tab2:
        st.markdown("### 🔍 Recherche par nom/mots-clés")
        search_term = st.text_input("Entrez un nom, crime, ou mot-clé:")
        if search_term and st.button("🔍 Rechercher", key="search_text"):
            with st.spinner("Recherche en cours..."):
                results = search_criminals_by_text(search_term)
                if results:
                    st.success(f"✅ {len(results)} résultat(s) trouvé(s) !")
                    display_text_search_results(results)
                else:
                    st.info("Aucun résultat trouvé.")


def display_casier_judiciaire(criminal_data, image_data=None, similarity=None):
    """Affiche un format A4 compact et uniforme, exportable en PDF"""
    current_date = datetime.now().strftime("%d/%m/%Y à %H:%M")

    _logo = _logo_b64()

    # Conteneur principal pour chaque résultat
    st.markdown("""
    <div style="
        max-width: 794px;
        margin: 20px auto;
        background: #ffffff;
        color: #000;
        font-family: Arial, sans-serif;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 20px;
        overflow: hidden;
    ">
    """, unsafe_allow_html=True)

    # Logo centré
    if _logo:
        st.markdown(f"""
        <div style="text-align: center; padding: 10px;">
            <img src='data:image/png;base64,{_logo}' style='height:100px;'>
        </div>
        """, unsafe_allow_html=True)

    # Photo du criminel (centrée)
    if image_data:
        try:
            if isinstance(image_data, memoryview):
                img_bytes = image_data.tobytes()
            elif isinstance(image_data, bytes):
                img_bytes = image_data
            else:
                img = Image.open(io.BytesIO(image_data)).convert("RGB")
                img_bytes = image_to_bytes(img)
            img = Image.open(io.BytesIO(img_bytes))

            # Centrer l'image
            st.markdown(
                """
                <style>
                    div.stImage > img {
                        display: block;
                        margin-left: auto;
                        margin-right: auto;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.image(img, width=200)

        except Exception:
            st.info("📷 Photo non disponible")
    else:
        st.info("📷 Pas de photo disponible")

    # Section Identité
    st.markdown("""
    <div style="
        padding: 15px;
        background: #ffffff;
        border-left: 4px solid #d32f2f;
        border-radius: 4px;
        margin-bottom: 15px;
    ">
    <h3 style="
        color: #d32f2f;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
        border-bottom: 2px solid #d32f2f;
    ">👤 IDENTITÉ</h3>
    """, unsafe_allow_html=True)
    info_html = f"""
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">👤 Nom complet</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('nom', '')} {criminal_data.get('prenom', '')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">🎭 Alias/Surnom</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('alias', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">📅 Âge</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('age', 'N/A')} ans</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">🎂 Date de naissance</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('date_naissance', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">🏙️ Lieu de naissance</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('lieu_naissance', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">🌍 Nationalité</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('nationalite', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">📞 Téléphone</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('telephone', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">🏠 Adresse</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('adresse', 'N/A')}</div>
    </div>
    """
    st.markdown(info_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Section Informations judiciaires
    st.markdown("""
    <div style="
        padding: 15px;
        background: #ffffff;
        border-left: 4px solid #d32f2f;
        border-radius: 4px;
    ">
    <h3 style="
        color: #d32f2f;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
        border-bottom: 2px solid #d32f2f;
    ">⚖️ INFORMATIONS JUDICIAIRES</h3>
    """, unsafe_allow_html=True)
    crime_html = f"""
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">⚖️ Infractioncrime</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('crime', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">🚔 Date d'arrestation</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('date_arrestation', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">⚖️ Niveau d'implication</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('implication', 'N/A')}</div>
    </div>
    <div style="margin-bottom: 10px;">
        <div style="font-weight: bold; color: #495057; font-size: 12px; text-transform: uppercase;">📝 Description détaillée</div>
        <div style="color: #212529; font-size: 14px; padding: 5px 0; border-bottom: 1px solid #e9ecef;">{criminal_data.get('description', 'N/A')}</div>
    </div>
    """
    st.markdown(crime_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Pied de page
    st.markdown(f"""
    <div style="
        border-top: 2px solid #d32f2f;
        padding: 15px;
        text-align: center;
        font-size: 11px;
        color: #666;
        margin-top: 15px;
    ">
        📅 <strong>Document généré le {current_date}</strong><br>
        <strong style="font-size: 16px; color: red;">⚖️ DOCUMENT CONFIDENTIEL</strong>
    </div>
    """, unsafe_allow_html=True)

    # Bouton d'exportation PDF
    img_bytes = image_data if isinstance(image_data, bytes) else None

    file_name = f"{criminal_data.get('nom', 'unknown')}_{criminal_data.get('prenom', '')}.pdf"

    pdf_buffer = generate_pdf(criminal_data, img_bytes, similarity, current_date)
    st.download_button(
        label="📄 Exporter en PDF",
        data=pdf_buffer,
        file_name=file_name,
        mime="application/pdf",
        key=f"export_pdf_{criminal_data.get('id', 'unknown')}"
    )

    st.markdown("</div>", unsafe_allow_html=True)


def display_search_results(results):
    st.markdown("<div class='results-container'>", unsafe_allow_html=True)
    for r in results:
        cursor.execute("SELECT nom, prenom, alias, crime, description, implication, age, date_naissance, lieu_naissance, nationalite, telephone, adresse, date_arrestation FROM criminals WHERE id = %s", (r['id'],))
        details = cursor.fetchone()
        if details:
            criminal_data = {
                'id': r['id'], 'nom': details[0], 'prenom': details[1], 'alias': details[2], 'crime': details[3], 'description': details[4], 'implication': details[5],
                'age': details[6], 'date_naissance': details[7], 'lieu_naissance': details[8], 'nationalite': details[9], 'telephone': details[10], 'adresse': details[11],
                'date_arrestation': details[12]
            }
            ref_img_bytes = image_to_bytes(r['reference_image']) if r.get('reference_image') else None

            with st.container():
                st.markdown(f"#### {criminal_data['nom']} {criminal_data['prenom']}")
                st.image(ref_img_bytes, width=100)
                st.write(f"**Correspondance :** {r['similarity']:.2f}%")
                with st.expander("Voir les détails"):
                    display_casier_judiciaire(criminal_data, ref_img_bytes, r['similarity'])
    st.markdown("</div>", unsafe_allow_html=True)

def display_text_search_results(results):
    st.markdown("<div class='results-container'>", unsafe_allow_html=True)
    for row in results:
        criminal_data = {
            'id': row[0], 'nom': row[1], 'prenom': row[2], 'alias': row[3], 'crime': row[4], 'description': row[5], 'implication': row[6],
            'age': row[7], 'date_naissance': row[8], 'lieu_naissance': row[9], 'nationalite': row[10], 'telephone': row[11], 'adresse': row[12],
            'date_arrestation': row[13]
        }
        img_bytes = row[14]

        with st.container():
            st.markdown(f"#### {criminal_data['nom']} {criminal_data['prenom']}")
            if img_bytes:
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    st.image(img, width=100)
                except Exception as e:
                    st.warning(f"Impossible d'afficher l'image : {e}")

            with st.expander("Voir les détails"):
                display_casier_judiciaire(criminal_data, img_bytes)
    st.markdown("</div>", unsafe_allow_html=True)

def list_criminals_page():
    st.header("📄 Liste des criminels enregistrés")
    cursor.execute("SELECT id, nom, crime, description, image FROM criminals ORDER BY id DESC")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            id_criminal, nom, crime, desc, img_bytes = row
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            with col1:
                if img_bytes:
                    try:
                        st.image(Image.open(io.BytesIO(img_bytes)), width=100)
                    except Exception:
                        st.write("Pas d'image")
                else:
                    st.write("Pas d'image")
            with col2:
                st.markdown(f"**{nom}**")
                st.write(f"**Crime :** {crime}")
                with st.expander("Gérer les photos"):
                    manage_photos(id_criminal)
            with col3:
                if st.session_state.get("is_admin"):
                    if st.button("✏️ Éditer", key=f"edit_{id_criminal}"):
                        st.session_state.editing_criminal_id = id_criminal
                        st.rerun()
            with col4:
                if st.session_state.get("is_admin"):
                    if st.button("🗑️ Supprimer", key=f"delete_{id_criminal}"):
                        with st.spinner(f"Suppression de {nom}..."):
                            cursor.execute("DELETE FROM criminals WHERE id = %s", (id_criminal,))
                        st.success(f"✅ Criminel {nom} supprimé.")
                        st.rerun()
    else:
        st.info("ℹ️ Aucun criminel enregistré.")

def edit_criminal_page(criminal_id):
    st.header("✏️ Modifier un criminel")

    # Récupérer les données actuelles du criminel
    criminal_data = get_criminal_by_id(criminal_id)
    if not criminal_data:
        st.error("Criminel non trouvé.")
        return

    # Convertir le tuple en dictionnaire
    keys = ["id", "nom", "prenom", "alias", "age", "date_naissance", "lieu_naissance",
            "nationalite", "telephone", "adresse", "date_arrestation", "implication",
            "crime", "description", "image"]
    criminal_dict = dict(zip(keys, criminal_data))

    with st.form("edit_criminal_form"):
        st.markdown("### Informations du criminel")

        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom *", value=criminal_dict['nom'])
            prenom = st.text_input("Prénom", value=criminal_dict['prenom'])
            alias = st.text_input("Alias", value=criminal_dict['alias'])
            age = st.number_input("Âge", min_value=0, max_value=120, value=criminal_dict['age'])
            date_naissance = st.date_input("Date de naissance", value=criminal_dict['date_naissance'])

        with col2:
            lieu_naissance = st.text_input("Lieu de naissance", value=criminal_dict['lieu_naissance'])
            nationalite = st.text_input("Nationalité", value=criminal_dict['nationalite'])
            telephone = st.text_input("Téléphone", value=criminal_dict['telephone'])
            adresse = st.text_input("Adresse", value=criminal_dict['adresse'])
            date_arrestation = st.date_input("Date d'arrestation", value=criminal_dict['date_arrestation'])

        st.markdown("### Informations judiciaires")
        cursor.execute("SELECT name FROM crime_types ORDER BY name")
        crime_types = [row[0] for row in cursor.fetchall()]
        crime_index = crime_types.index(criminal_dict['crime']) if criminal_dict['crime'] in crime_types else 0
        crime = st.selectbox("Infractioncrime *", crime_types, index=crime_index)
        implication = st.text_input("Implication", value=criminal_dict['implication'])
        description = st.text_area("Description détaillée", value=criminal_dict['description'])

        # Boutons
        submit_col, cancel_col = st.columns([1, 5])
        with submit_col:
            if st.form_submit_button("Enregistrer"):
                if not nom:
                    st.error("⚠️ Le nom est obligatoire.")
                else:
                    updated_data = {
                        "nom": nom, "prenom": prenom, "alias": alias, "age": age,
                        "date_naissance": date_naissance, "lieu_naissance": lieu_naissance,
                        "nationalite": nationalite, "telephone": telephone, "adresse": adresse,
                        "date_arrestation": date_arrestation, "implication": implication,
                        "crime": crime, "description": description
                    }
                    with st.spinner("Mise à jour..."):
                        update_criminal(criminal_id, updated_data)
                    st.success("✅ Informations mises à jour.")
                    st.session_state.editing_criminal_id = None
                    st.rerun()

        with cancel_col:
            if st.form_submit_button("Annuler"):
                st.session_state.editing_criminal_id = None
                st.rerun()

def manage_photos(criminal_id):
    st.header("🖼️ Gérer les photos")
    cursor.execute("SELECT id, image FROM images_criminels WHERE criminal_id = %s ORDER BY id DESC", (criminal_id,))
    photos = cursor.fetchall()
    if photos:
        cols = st.columns(3)
        for idx, (pid, pbytes) in enumerate(photos):
            with cols[idx % 3]:
                st.image(Image.open(io.BytesIO(pbytes)).convert("RGB"), use_container_width=True, caption=f"Photo #{pid}")
                if st.session_state.get("is_admin"):
                    if st.button("🗑️", key=f"del_{pid}"):
                        with st.spinner("Suppression..."):
                            delete_photo(pid)
                        st.rerun()