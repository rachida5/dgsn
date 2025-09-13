# database.py
import psycopg2
from PIL import Image
from utils import image_to_bytes

# Connexion PostgreSQL
try:
    conn = psycopg2.connect(
        dbname="DGSN", user="postgres", password="Abdou", host="localhost", port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()
except Exception as e:
    # Gérer l'erreur de manière appropriée, par exemple en l'affichant dans Streamlit
    print(f"Erreur de connexion à la base de données : {e}")
    cursor = None # S'assurer que le curseur est None si la connexion échoue

# Setup BDD
def setup_db():
    if not cursor: return
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS criminals (
          id SERIAL PRIMARY KEY,
          nom VARCHAR(255) NOT NULL,
          prenom VARCHAR(255),
          alias VARCHAR(255),
          age INTEGER,
          date_naissance DATE,
          lieu_naissance VARCHAR(255),
          nationalite VARCHAR(255),
          telephone VARCHAR(50),
          adresse TEXT,
          date_arrestation DATE,
          implication TEXT,
          crime VARCHAR(255),
          description TEXT,
          image BYTEA
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crime_types (
          id SERIAL PRIMARY KEY,
          name VARCHAR(255) UNIQUE NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          username VARCHAR(255) UNIQUE NOT NULL,
          password VARCHAR(255) NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images_criminels (
          id SERIAL PRIMARY KEY,
          criminal_id INTEGER NOT NULL REFERENCES criminals(id) ON DELETE CASCADE,
          image BYTEA NOT NULL,
          created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_criminels_criminal ON images_criminels(criminal_id);")
        cursor.execute("SELECT COUNT(*) FROM images_criminels;")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("""
                INSERT INTO images_criminels (criminal_id, image)
                SELECT id AS criminal_id, image
                FROM criminals
                WHERE image IS NOT NULL
            """)
    except Exception as e:
        print(f"Attention: initialisation de la table images_criminels incomplète ({e}).")

# Fonctions de manipulation de données
def delete_photo(photo_id: int):
    if not cursor: return
    cursor.execute("DELETE FROM images_criminels WHERE id = %s", (photo_id,))

def update_photo(photo_id: int, file):
    if not cursor: return
    pil = Image.open(file).convert("RGB")
    img_bytes = image_to_bytes(pil)
    cursor.execute("UPDATE images_criminels SET image = %s WHERE id = %s", (psycopg2.Binary(img_bytes), photo_id))

def search_criminals_by_text(search_query=""):
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
    if not cursor: return None
    cursor.execute("SELECT * FROM criminals WHERE id = %s", (criminal_id,))
    return cursor.fetchone()

def update_criminal(criminal_id: int, data: dict):
    """Met à jour les informations d'un criminel."""
    if not cursor: return
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