"""Database connection and initialization."""
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="DGSN", user="postgres", password="Abdou", host="localhost", port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()
except Exception as e:
    # Gérer l'erreur de manière appropriée, par exemple en l'affichant dans Streamlit
    print(f"Erreur de connexion à la base de données : {e}")
    cursor = None  # S'assurer que le curseur est None si la connexion échoue


def setup_db():
    if not cursor:
        return
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
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_images_criminels_criminal ON images_criminels(criminal_id);"
        )
        cursor.execute("SELECT COUNT(*) FROM images_criminels;")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute(
                """
                INSERT INTO images_criminels (criminal_id, image)
                SELECT id AS criminal_id, image
                FROM criminals
                WHERE image IS NOT NULL
                """
            )
    except Exception as e:
        print(f"Attention: initialisation de la table images_criminels incomplète ({e}).")


from .crud import (
    delete_photo,
    update_photo,
    search_criminals_by_text,
    get_criminal_by_id,
    update_criminal,
)

__all__ = [
    "cursor",
    "setup_db",
    "delete_photo",
    "update_photo",
    "search_criminals_by_text",
    "get_criminal_by_id",
    "update_criminal",
]
