# ============================================================
# validators.py - Module 5 : Filtrage et Sécurité
# Contient : FilterResult, InputValidator, OutputValidator
# ============================================================

import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from src.config.settings import (
    SIMILARITY_THRESHOLD_IN,
    SIMILARITY_THRESHOLD_OUT_HIGH,
    SIMILARITY_THRESHOLD_OUT_LOW,
    SLM_CONFIDENCE_THRESHOLD,
    SLM_MODEL,
    OLLAMA_BASE_URL,
    MESSAGE_QUESTION_BLOQUEE,
    MESSAGE_REPONSE_BLOQUEE
)


# ============================================================
# CLASSE 1 : FilterResult
# C'est la "boîte résultat" retournée par chaque validation
# ============================================================

class FilterResult:
    def __init__(self, is_valid: bool, reason: str, score: float, method: str):
        # True si la validation est passée, False si bloquée
        self.is_valid = is_valid

        # Explication du blocage (vide si valide)
        self.reason = reason

        # Score obtenu (similarité cosinus ou confiance SLM)
        self.score = score

        # Qui a pris la décision : "cosine" ou "slm"
        self.method = method

    def __repr__(self):
        return (
            f"FilterResult("
            f"is_valid={self.is_valid}, "
            f"score={self.score:.2f}, "
            f"method={self.method}, "
            f"reason='{self.reason}')"
        )


# ============================================================
# CLASSE 2 : InputValidator
# Vérifie que la question est liée au corpus du module
# ============================================================

class InputValidator:
    def __init__(self):
        # On charge le modèle qui transforme le texte en vecteur
        from src.config.settings import EMBEDDING_MODEL
        self.model = SentenceTransformer(EMBEDDING_MODEL)
    
    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs.
        Retourne un score entre 0 et 1.
        0 = rien à voir / 1 = identiques
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    def _compute_centroid(self, chunk_vectors: list) -> list:
        """
        Calcule le vecteur centroïde = moyenne de tous les vecteurs des chunks.
        C'est le vecteur qui représente l'ensemble du corpus du module.
        """
        return np.mean(chunk_vectors, axis=0).tolist()

    def validate(self, question: str, chunk_vectors: list) -> FilterResult:
        """
        Valide la question en la comparant au centroïde du corpus.

        Paramètres :
        - question      : le texte de la question posée par l'étudiant
        - chunk_vectors : liste des vecteurs de tous les chunks du module

        Retourne un FilterResult.
        """

        # Étape 1 : transformer la question en vecteur
        question_vector = self.model.encode(question).tolist()

        # Étape 2 : calculer le centroïde du corpus
        centroid = self._compute_centroid(chunk_vectors)

        # Étape 3 : calculer la similarité cosinus
        score = self._cosine_similarity(question_vector, centroid)

        # Étape 4 : décision selon le seuil
        if score >= SIMILARITY_THRESHOLD_IN:
            # Question acceptée
            return FilterResult(
                is_valid=True,
                reason="",
                score=score,
                method="cosine"
            )
        else:
            # Question bloquée
            return FilterResult(
                is_valid=False,
                reason=MESSAGE_QUESTION_BLOQUEE,
                score=score,
                method="cosine"
            )


# ============================================================
# CLASSE 3 : OutputValidator
# Vérifie que la réponse générée est ancrée dans le cours
# ============================================================

class OutputValidator:
    def __init__(self):
        # Modèle pour transformer le texte en vecteur
        from src.config.settings import EMBEDDING_MODEL
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Client pour appeler le SLM via Ollama (utilisé uniquement en zone grise)
        self.slm_client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama"  # Ollama n'a pas besoin de vraie clé API
        )

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs.
        Retourne un score entre 0 et 1.
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    def _compute_centroid(self, chunk_vectors: list) -> list:
        """
        Calcule le vecteur centroïde des chunks sources.
        """
        return np.mean(chunk_vectors, axis=0).tolist()

    def _build_slm_prompt(self, response: str, chunks: list) -> str:
        """
        Construit le prompt envoyé au SLM pour évaluer la réponse.
        """
        chunks_text = ""
        #ici chunks est une liste de dictionnaires, et la boucle transforme cette liste en une seule 
        #chaine de texte que le SLM veut peut lire
        for i, chunk in enumerate(chunks, start=1):
            chunks_text += f"[{i}] {chunk['text']}\n\n"

        prompt = (
            "Tu es un évaluateur de fidélité. Voici des passages extraits d'un cours :\n\n"
            f"{chunks_text}"
            f"Voici une réponse générée : {response}\n\n"
            "Cette réponse est-elle fidèle et ancrée dans les passages fournis ?\n"
            "Réponds uniquement par OUI ou NON, suivi d'un score de confiance entre 0 et 1.\n"
            "Exemple : OUI 0.85 ou NON 0.32"
        )
        return prompt

    def _call_slm(self, response: str, chunks: list) -> tuple:
        """
        Appelle le SLM pour évaluer la réponse dans la zone grise.
        Retourne un tuple (décision: bool, confiance: float).
        """
        prompt = self._build_slm_prompt(response, chunks)

        slm_response = self.slm_client.chat.completions.create(
            model=SLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,      # On n'a besoin que de "OUI 0.85" ou "NON 0.32"
            temperature=0.0     # Pas de créativité, on veut une réponse précise
        )

        # Récupérer la réponse du SLM (ex: "OUI 0.85")
        slm_text = slm_response.choices[0].message.content.strip().upper()

        # Extraire la décision et le score de confiance
        parts = slm_text.split()
        decision = parts[0]                                          # "OUI" ou "NON"
        confidence = float(parts[1]) if len(parts) > 1 else 0.0     # 0.85

        is_valid = (decision == "OUI" and confidence >= SLM_CONFIDENCE_THRESHOLD)
        return is_valid, confidence

    def validate(self, response: str, chunks: list) -> FilterResult:
        """
        Valide la réponse générée en la comparant aux chunks sources.

        Paramètres :
        - response : le texte de la réponse générée par le LLM
        - chunks   : liste des chunks sources avec leurs textes et vecteurs

        Retourne un FilterResult.
        """

        # Étape 1 : transformer la réponse en vecteur
        response_vector = self.model.encode(response).tolist()

        # Étape 2 : récupérer les vecteurs des chunks sources
        chunk_vectors = [chunk["vector"] for chunk in chunks]

        # Étape 3 : calculer le centroïde des chunks
        centroid = self._compute_centroid(chunk_vectors)

        # Étape 4 : calculer la similarité cosinus
        score = self._cosine_similarity(response_vector, centroid)

        # --------------------------------------------------------
        # Étape 5 : décision selon les seuils
        # --------------------------------------------------------

        # CAS 1 : score élevé → réponse bien ancrée → validée directement
        if score >= SIMILARITY_THRESHOLD_OUT_HIGH:
            return FilterResult(
                is_valid=True,
                reason="",
                score=score,
                method="cosine"
            )

        # CAS 2 : score très bas → réponse hallucinée → bloquée directement
        elif score < SIMILARITY_THRESHOLD_OUT_LOW:
            return FilterResult(
                is_valid=False,
                reason=MESSAGE_REPONSE_BLOQUEE,
                score=score,
                method="cosine"
            )

        # CAS 3 : zone grise → on demande au SLM de trancher
        else:
            is_valid, confidence = self._call_slm(response, chunks)

            return FilterResult(
                is_valid=is_valid,
                reason="" if is_valid else MESSAGE_REPONSE_BLOQUEE,
                score=confidence,
                method="slm"
            )