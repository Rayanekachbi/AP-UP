# ============================================================
# db_session.py - Module 3 : Connexion à la base de données
# Gère la connexion à PostgreSQL via SQLAlchemy
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# ============================================================
# URL DE CONNEXION À POSTGRESQL
# Format : postgresql://utilisateur:motdepasse@host:port/base
# ============================================================

DATABASE_URL = "postgresql://postgres:password@127.0.0.1:5432/ap_up"
#from src.config.settings import DATABASE_URL

# ============================================================
# CLASSE DE BASE POUR LES MODÈLES ORM
# Toutes les tables (Utilisateur, Module, etc.) héritent de Base
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# MOTEUR DE CONNEXION (ENGINE)
# C'est lui qui gère la communication avec PostgreSQL
# ============================================================

engine = create_engine(
    DATABASE_URL,
    echo=False  # Mettre True pour afficher les requêtes SQL dans le terminal (utile pour déboguer)
)


# ============================================================
# FABRIQUE DE SESSIONS
# Chaque session = une transaction avec la base de données
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # On gère les commits manuellement
    autoflush=False
)


# ============================================================
# FONCTION UTILITAIRE : get_db()
# Retourne une session et la ferme automatiquement après usage
# ============================================================

def get_db():
    """
    Retourne une session SQLAlchemy.
    À utiliser avec un bloc 'with' pour fermer automatiquement la session.

    Exemple d'utilisation :
        db = next(get_db())
        db.query(Chunk).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# FONCTION : init_db()
# Crée toutes les tables dans PostgreSQL si elles n'existent pas
# ============================================================

def init_db():
    """
    Crée toutes les tables définies dans models.py.
    À appeler une seule fois au démarrage de l'application.
    """
    # On importe les modèles ici pour que SQLAlchemy les connaisse
    from src.Backend.database import models  # noqa: F401

    # Active l'extension pgvector si pas encore fait
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Crée toutes les tables
    Base.metadata.create_all(bind=engine)
    print("Base de données initialisée avec succès !")


# ============================================================
# TEST DE CONNEXION
# Lance ce fichier directement pour tester la connexion
# ============================================================

if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connexion à PostgreSQL réussie !")
    except Exception as e:
        print(f"Erreur de connexion : {e}")