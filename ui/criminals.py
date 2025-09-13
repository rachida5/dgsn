"""Pages pour la gestion des criminels."""
import io

import streamlit as st
from PIL import Image

from database import cursor, delete_photo, get_criminal_by_id, update_criminal


def list_criminals_page() -> None:
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
    criminal_data = get_criminal_by_id(criminal_id)
    if not criminal_data:
        st.error("Criminel non trouvé.")
        return

    keys = [
        "id",
        "nom",
        "prenom",
        "alias",
        "age",
        "date_naissance",
        "lieu_naissance",
        "nationalite",
        "telephone",
        "adresse",
        "date_arrestation",
        "implication",
        "crime",
        "description",
        "image",
    ]
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

        submit_col, cancel_col = st.columns([1, 5])
        with submit_col:
            if st.form_submit_button("Enregistrer"):
                if not nom:
                    st.error("⚠️ Le nom est obligatoire.")
                else:
                    updated_data = {
                        "nom": nom,
                        "prenom": prenom,
                        "alias": alias,
                        "age": age,
                        "date_naissance": date_naissance,
                        "lieu_naissance": lieu_naissance,
                        "nationalite": nationalite,
                        "telephone": telephone,
                        "adresse": adresse,
                        "date_arrestation": date_arrestation,
                        "implication": implication,
                        "crime": crime,
                        "description": description,
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

