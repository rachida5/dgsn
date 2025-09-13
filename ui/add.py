"""Pages et formulaires pour l'ajout de criminels."""
import io
from datetime import date

import psycopg2
import streamlit as st
from PIL import Image

from database import cursor
from utils import image_to_bytes


def add_criminal_page() -> None:
    st.header("➕ Ajouter un criminel")

    if "add_criminal_step" not in st.session_state:
        st.session_state["add_criminal_step"] = 1
    if "form_data" not in st.session_state:
        st.session_state["form_data"] = {}

    st.markdown(
        f"""
    <div class="step-indicator">
        <div class="step {{'active' if st.session_state['add_criminal_step'] == 1 else ''}}"><span class="step-number">1</span> Informations personnelles</div>
        <div class="step {{'active' if st.session_state['add_criminal_step'] == 2 else ''}}"><span class="step-number">2</span> Informations judiciaires</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state["add_criminal_step"] == 1:
        step1_form()
    elif st.session_state["add_criminal_step"] == 2:
        step2_form()


def step1_form() -> None:
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
                st.session_state["form_data"].update(
                    {
                        "nom": nom,
                        "prenom": prenom,
                        "alias": alias,
                        "age": age,
                        "date_naissance": date_naissance,
                        "lieu_naissance": lieu_naissance,
                        "nationalite": nationalite,
                        "telephone": telephone,
                        "adresse": adresse,
                    }
                )
                st.session_state["add_criminal_step"] = 2
                st.rerun()


def step2_form() -> None:
    with st.form("add_criminal_form_step2", clear_on_submit=True):
        st.markdown("### Étape 2 : Informations judiciaires et images")
        st.info("Fournissez les détails judiciaires et chargez au moins une image. *Champs obligatoires.")

        date_arrestation = st.date_input("Date d'arrestation *", value=st.session_state["form_data"].get("date_arrestation", date.today()))
        implication = st.text_input("Implication", value=st.session_state["form_data"].get("implication", ""), placeholder="Niveau d'implication")

        cursor.execute("SELECT name FROM crime_types ORDER BY name")
        crime_types = [row[0] for row in cursor.fetchall()]
        crime = st.selectbox(
            "Infractioncrime *",
            crime_types,
            index=crime_types.index(st.session_state["form_data"].get("crime", crime_types[0]))
            if st.session_state["form_data"].get("crime") in crime_types
            else 0,
        )

        description = st.text_area(
            "Description détaillée",
            value=st.session_state["form_data"].get("description", ""),
            placeholder="Détails du crime",
        )
        images_files = st.file_uploader(
            "Charger des images (1 à 5) *",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )

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
                            st.session_state["form_data"]["nom"],
                            st.session_state["form_data"]["prenom"],
                            st.session_state["form_data"]["alias"],
                            st.session_state["form_data"]["age"],
                            st.session_state["form_data"]["date_naissance"],
                            st.session_state["form_data"]["lieu_naissance"],
                            st.session_state["form_data"]["nationalite"],
                            st.session_state["form_data"]["telephone"],
                            st.session_state["form_data"]["adresse"],
                            date_arrestation,
                            implication,
                            crime,
                            description,
                            psycopg2.Binary(first_img_bytes),
                        )
                        cursor.execute(
                            """
                            INSERT INTO criminals (nom, prenom, alias, age, date_naissance, lieu_naissance, nationalite, telephone, adresse, date_arrestation, implication, crime, description, image)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                            """,
                            data,
                        )
                        criminal_id = cursor.fetchone()[0]

                        added = 0
                        for f in images_files[:5]:
                            img_bytes = image_to_bytes(Image.open(f).convert("RGB"))
                            cursor.execute(
                                "INSERT INTO images_criminels (criminal_id, image) VALUES (%s, %s)",
                                (criminal_id, psycopg2.Binary(img_bytes)),
                            )
                            added += 1

                    st.success(f"✅ Criminel ajouté (ID {criminal_id}). Photos : {added}.")
                    st.session_state["add_criminal_step"] = 1
                    st.session_state["form_data"] = {}
                    st.rerun()

