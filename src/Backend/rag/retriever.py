# ============================================================
# retriever.py - Module 4 : Recherche de chunks pertinents
# Vectorise la question et récupère les top_k chunks
# ============================================================

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from src.config.settings import EMBEDDING_MODEL, TOP_K
from src.Backend.database.vector_store import rechercher_chunks


# ============================================================
# MODÈLE D'EMBEDDING
# Chargé une seule fois au démarrage du module
# Important : doit être le même modèle que celui utilisé
# lors de l'indexation des chunks (Module 3)
# ============================================================

modele_embedding = SentenceTransformer(EMBEDDING_MODEL)


# ============================================================
# CLASSE : Retriever
# ============================================================

class Retriever:
    """
    Responsable de la vectorisation de la question
    et de la récupération des chunks pertinents depuis la BDD.
    """

    def __init__(self, db: Session, top_k: int = TOP_K):
        self.db = db
        self.top_k = top_k

    def vectoriser_question(self, question: str) -> list[float]:
        """
        Transforme la question en vecteur sémantique.
        Utilise le même modèle d'embedding que lors de l'indexation
        pour garantir la comparabilité des vecteurs.

        Paramètres :
        - question : texte de la question de l'étudiant

        Retourne un vecteur de 768 floats.
        """
        vecteur = modele_embedding.encode(question)
        return vecteur.tolist()

    def retrieve_chunks(
        self,
        question: str,
        module_id: int
    ) -> list[dict]:
        """
        Vectorise la question et récupère les top_k chunks
        les plus pertinents depuis la base vectorielle.

        Paramètres :
        - question  : texte de la question de l'étudiant
        - module_id : ID du module pédagogique sélectionné

        Retourne une liste de dictionnaires contenant
        le texte et les métadonnées de chaque chunk.
        """

        # Étape 1 : vectoriser la question
        query_vector = self.vectoriser_question(question)

        # Étape 2 : rechercher les chunks pertinents
        chunks = rechercher_chunks(
            db=self.db,
            query_vector=query_vector,
            module_id=module_id,
            top_k=self.top_k
        )

        if not chunks:
            raise ValueError(
                f"Aucun chunk trouvé pour le module {module_id}. "
                "Vérifiez que des documents ont bien été indexés."
            )

        return chunks