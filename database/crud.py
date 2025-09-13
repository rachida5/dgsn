"""Database CRUD operations."""
from PIL import Image
import psycopg2
from utils import image_to_bytes
from . import cursor


def delete_photo(photo_id: int):
    if not cursor:
        return
    cursor.execute("DELETE FROM images_criminels WHERE id = %s", (photo_id,))


def update_photo(photo_id: int, file):
    if not cursor:
        return
    pil = Image.open(file).convert("RGB")
    img_bytes = image_to_bytes(pil)
    cursor.execute(
        "UPDATE images_criminels SET image = %s WHERE id = %s",
        (psycopg2.Binary(img_bytes), photo_id),
    )


def search_criminals_by_text(search_query: str = ""):
    """Recherche des criminels par un terme unique dans tous les champs"""
    if not search_query.strip() or not cursor:
        return []
    search_term = f"%{search_query.lower()}%"
    query = """
        SELECT id, nom, prenom, alias, crime, description, implication,
               age, date_naissance, lieu_naissance, nationalite, telephone,
               adresse, date_arrestation, image
        FROM criminals
        WHERE LOWER(nom) LIKE %s
           OR LOWER(prenom) LIKE %s
           OR LOWER(alias) LIKE %s
           OR LOWER(crime) LIKE %s
           OR LOWER(description) LIKE %s
           OR LOWER(implication) LIKE %s
           OR LOWER(lieu_naissance) LIKE %s
           OR LOWER(nationalite) LIKE %s
           OR LOWER(adresse) LIKE %s
        ORDER BY nom, prenom
    """
    params = [search_term] * 9
    cursor.execute(query, params)
    return cursor.fetchall()


def get_criminal_by_id(criminal_id: int):
    """Récupère toutes les informations d'un criminel par son ID."""
    if not cursor:
        return None
    cursor.execute("SELECT * FROM criminals WHERE id = %s", (criminal_id,))
    return cursor.fetchone()


def update_criminal(criminal_id: int, data: dict):
    """Met à jour les informations d'un criminel."""
    if not cursor:
        return
    query = """
        UPDATE criminals SET
            nom = %s, prenom = %s, alias = %s, age = %s, date_naissance = %s,
            lieu_naissance = %s, nationalite = %s, telephone = %s, adresse = %s,
            date_arrestation = %s, implication = %s, crime = %s, description = %s
        WHERE id = %s
    """
    params = (
        data['nom'], data['prenom'], data['alias'], data['age'], data['date_naissance'],
        data['lieu_naissance'], data['nationalite'], data['telephone'], data['adresse'],
        data['date_arrestation'], data['implication'], data['crime'], data['description'],
        criminal_id
    )
    cursor.execute(query, params)
