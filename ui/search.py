"""Recherche et affichage des criminels."""
import io
from datetime import datetime

import streamlit as st
from PIL import Image

from database import cursor, search_criminals_by_text
from utils import generate_pdf, find_match, image_to_bytes
from .utils import _logo_b64


def search_criminal_page() -> None:
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

    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )

    if _logo:
        st.markdown(
            f"""
        <div style="text-align: center; padding: 10px;">
            <img src='data:image/png;base64,{_logo}' style='height:100px;'>
        </div>
        """,
            unsafe_allow_html=True,
        )

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
                unsafe_allow_html=True,
            )
            st.image(img, width=200)
        except Exception:
            st.info("📷 Photo non disponible")
    else:
        st.info("📷 Pas de photo disponible")

    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )
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

    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )
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

    st.markdown(
        f"""
    <div style="
        border-top: 2px solid #d32f2f;
        padding: 15px;
        text-align: center;
        font-size: 11px;
        color: #666;
        margin-top: 15px;
    ">
        📅 <strong>Document généré le {current_date}</strong><br>
        <strong style=\"font-size: 16px; color: red;\">⚖️ DOCUMENT CONFIDENTIEL</strong>
    </div>
    """,
        unsafe_allow_html=True,
    )

    img_bytes = image_data if isinstance(image_data, bytes) else None
    file_name = f"{criminal_data.get('nom', 'unknown')}_{criminal_data.get('prenom', '')}.pdf"
    pdf_buffer = generate_pdf(criminal_data, img_bytes, similarity, current_date)
    st.download_button(
        label="📄 Exporter en PDF",
        data=pdf_buffer,
        file_name=file_name,
        mime="application/pdf",
        key=f"export_pdf_{criminal_data.get('id', 'unknown')}",
    )

    st.markdown("</div>", unsafe_allow_html=True)


def display_search_results(results):
    st.markdown("<div class='results-container'>", unsafe_allow_html=True)
    for r in results:
        cursor.execute(
            "SELECT nom, prenom, alias, crime, description, implication, age, date_naissance, lieu_naissance, nationalite, telephone, adresse, date_arrestation FROM criminals WHERE id = %s",
            (r['id'],),
        )
        details = cursor.fetchone()
        if details:
            criminal_data = {
                'id': r['id'],
                'nom': details[0],
                'prenom': details[1],
                'alias': details[2],
                'crime': details[3],
                'description': details[4],
                'implication': details[5],
                'age': details[6],
                'date_naissance': details[7],
                'lieu_naissance': details[8],
                'nationalite': details[9],
                'telephone': details[10],
                'adresse': details[11],
                'date_arrestation': details[12],
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
            'id': row[0],
            'nom': row[1],
            'prenom': row[2],
            'alias': row[3],
            'crime': row[4],
            'description': row[5],
            'implication': row[6],
            'age': row[7],
            'date_naissance': row[8],
            'lieu_naissance': row[9],
            'nationalite': row[10],
            'telephone': row[11],
            'adresse': row[12],
            'date_arrestation': row[13],
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

