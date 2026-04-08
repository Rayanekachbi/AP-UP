# ============================================================
# models.py - Module 3 : Définition des 5 tables
# Chaque classe = une table dans PostgreSQL
# ============================================================

from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, TIMESTAMP, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from src.Backend.database.db_session import Base


# ============================================================
# TABLE 1 : utilisateurs
# Stocke les étudiants et les enseignants
# ============================================================

class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "etudiant" ou "enseignant"
    date_creation: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now)

    # Relations
    modules: Mapped[list["Module"]] = relationship(back_populates="enseignant")
    documents: Mapped[list["Document"]] = relationship(back_populates="enseignant")
    historiques: Mapped[list["Historique"]] = relationship(back_populates="utilisateur")

    def __repr__(self):
        return f"Utilisateur(id={self.id}, email={self.email}, role={self.role})"


# ============================================================
# TABLE 2 : modules
# Stocke les modules pédagogiques (ex: Réseaux, BDD, Algo)
# ============================================================

class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    enseignant_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True)  # Prompt défini par l'enseignant

    # Relations
    enseignant: Mapped["Utilisateur"] = relationship(back_populates="modules")
    documents: Mapped[list["Document"]] = relationship(back_populates="module")
    historiques: Mapped[list["Historique"]] = relationship(back_populates="module")

    def __repr__(self):
        return f"Module(id={self.id}, nom={self.nom})"


# ============================================================
# TABLE 3 : documents
# Stocke les fichiers déposés par les enseignants
# ============================================================

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False)
    enseignant_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    chemin_fichier: Mapped[str] = mapped_column(String(512), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # "pdf", "pptx", "mp4"...
    statut: Mapped[str] = mapped_column(String(20), nullable=False)  # "indexé" ou "erreur"
    date_depot: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now)

    # Relations
    module: Mapped["Module"] = relationship(back_populates="documents")
    enseignant: Mapped["Utilisateur"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document")

    def __repr__(self):
        return f"Document(id={self.id}, titre={self.titre}, statut={self.statut})"


# ============================================================
# TABLE 4 : chunks
# Stocke les fragments de texte + leurs vecteurs (pgvector)
# C'est la table la plus importante pour le RAG
# ============================================================

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    contenu_texte: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(768), nullable=False)  # Vecteur sémantique
    page_source: Mapped[int] = mapped_column(Integer, nullable=True)
    section: Mapped[str] = mapped_column(String(255), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relation
    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self):
        return f"Chunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})"


# ============================================================
# TABLE 5 : historique
# Stocke les échanges question/réponse des étudiants
# ============================================================

class Historique(Base):
    __tablename__ = "historique"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reponse: Mapped[str] = mapped_column(Text, nullable=False)
    chunks_sources: Mapped[str] = mapped_column(Text, nullable=True)  # IDs des chunks utilisés (JSON)
    #chunks_sources: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=True)
    #On avait décidé de stocker un INTEGER[] (tableau d'entiers PostgreSQL), pas du JSON en Text
    date_heure: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now)

    # Relations
    utilisateur: Mapped["Utilisateur"] = relationship(back_populates="historiques")
    module: Mapped["Module"] = relationship(back_populates="historiques")

    def __repr__(self):
        return f"Historique(id={self.id}, utilisateur_id={self.utilisateur_id}, date={self.date_heure})"