# ============================================================
# rag_engine.py - Module 4 : Moteur d'inférence RAG
# Orchestre retriever, prompt_builder et stream_response
# ============================================================

from openai import OpenAI
from sqlalchemy.orm import Session
from src.config.settings import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_API_KEY, TOP_K
from src.Backend.rag.retriever import Retriever
from src.Backend.rag.prompt_builder import PromptBuilder
from src.Backend.database.vector_store import sauvegarder_historique
from typing import Generator


# ============================================================
# CLASSE : RAGEngine
# ============================================================

class RAGEngine:
    """
    Cœur interactif du système RAG.
    Orchestre la récupération des chunks, l'assemblage du prompt
    et la génération de la réponse en flux continu.
    Intervient exclusivement dans le parcours étudiant.
    """

    def __init__(self, db: Session, utilisateur_id: int, top_k: int = TOP_K):
        self.db = db
        self.utilisateur_id = utilisateur_id
        self.top_k = top_k

        # Client OpenAI pointant vers Pléiade ou Ollama
        self.llm_client = OpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY
        )

        # Sous-composants
        self.retriever = Retriever(db=db, top_k=top_k)
        self.prompt_builder = PromptBuilder(db=db)

    def stream_response(
        self,
        messages: list[dict]
    ) -> Generator[str, None, None]:
        """
        Soumet le prompt au serveur d'inférence et retourne
        un générateur produisant la réponse token par token.

        Paramètres :
        - messages : liste de messages au format OpenAI

        Retourne un générateur de tokens (str).
        """
        stream = self.llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def run(
        self,
        question: str,
        module_id: int
    ) -> Generator[str, None, None]:
        """
        Méthode orchestratrice du pipeline RAG complet :
        1. Récupération des chunks pertinents
        2. Assemblage du prompt enrichi
        3. Génération en flux continu
        4. Recomposition de la réponse complète pour le filtrage

        Paramètres :
        - question  : question de l'étudiant
        - module_id : ID du module pédagogique sélectionné

        Retourne un générateur de tokens.
        """

        # Étape 1 : récupérer les chunks pertinents
        chunks = self.retriever.retrieve_chunks(
            question=question,
            module_id=module_id
        )

        # Étape 2 : assembler le prompt
        messages = self.prompt_builder.build_prompt(
            question=question,
            chunks=chunks,
            module_id=module_id
        )

        # Étape 3 : générer en flux continu
        # On recompose aussi la réponse complète pour le filtrage
        reponse_complete = ""
        chunks_ids = [chunk["id"] for chunk in chunks]

        for token in self.stream_response(messages):
            reponse_complete += token
            yield token

        # Étape 4 : stocker les données pour le filtrage
        # On les attache à l'objet pour que le Module 5 puisse y accéder
        self._derniere_reponse = reponse_complete
        self._derniers_chunks = chunks
        self._derniere_question = question
        self._dernier_module_id = module_id
        self._derniers_chunks_ids = chunks_ids

    def sauvegarder(self) -> None:
        """
        Sauvegarde le dernier échange dans l'historique.
        Appelée par le Module 5 après validation de la réponse.
        """
        sauvegarder_historique(
            db=self.db,
            utilisateur_id=self.utilisateur_id,
            module_id=self._dernier_module_id,
            question=self._derniere_question,
            reponse=self._derniere_reponse,
            chunks_ids=self._derniers_chunks_ids
        )
