# ============================================================
# prompt_builder.py - Module 4 : Assemblage du prompt
# Construit le prompt enrichi envoyé au LLM
# ============================================================

from sqlalchemy.orm import Session
from src.Backend.database.vector_store import get_system_prompt


# ============================================================
# CLASSE : PromptBuilder
# ============================================================

class PromptBuilder:
    """
    Responsable de la construction du prompt enrichi
    envoyé au serveur d'inférence.
    Le prompt combine le prompt système de l'enseignant,
    les chunks numérotés et sourcés, et la question de l'étudiant.
    """

    def __init__(self, db: Session):
        self.db = db

    def build_prompt(
        self,
        question: str,
        chunks: list[dict],
        module_id: int
    ) -> list[dict]:
        """
        Assemble le prompt final selon la structure :
        - Message système : prompt défini par l'enseignant
        - Message utilisateur : contexte (chunks) + question

        Paramètres :
        - question  : question de l'étudiant
        - chunks    : liste des chunks récupérés par le Retriever
        - module_id : ID du module pour récupérer le prompt système

        Retourne une liste de messages au format OpenAI.
        """

        # Étape 1 : récupérer le prompt système
        system_prompt = get_system_prompt(
            db=self.db,
            module_id=module_id
        )

        # Étape 2 : formater les chunks avec numérotation et sources
        contexte = self._formater_chunks(chunks)

        # Étape 3 : assembler le message utilisateur
        message_utilisateur = (
            f"Contexte extrait du cours :\n"
            f"{contexte}\n\n"
            f"Question : {question}"
        )

        # Étape 4 : construire la liste de messages
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message_utilisateur
            }
        ]

        return messages

    def _formater_chunks(self, chunks: list[dict]) -> str:
        """
        Formate les chunks avec numérotation et métadonnées sources.

        Exemple de sortie :
        [1] (source: cours_reseaux.pdf, section: 2.1 Le modèle OSI) :
            Le modèle OSI est composé de 7 couches...
        [2] (source: cours_reseaux.pdf, page: 5) :
            TCP/IP est un ensemble de protocoles...
        """
        lignes = []

        for i, chunk in enumerate(chunks, start=1):
            # Construire les infos de source
            source = chunk.get("source", "inconnu")
            section = chunk.get("section")
            page = chunk.get("page")

            if section:
                info_source = f"source: {source}, section: {section}"
            elif page:
                info_source = f"source: {source}, page: {page}"
            else:
                info_source = f"source: {source}"

            # Formater le chunk
            lignes.append(
                f"[{i}] ({info_source}) :\n"
                f"    {chunk.get('text', chunk.get('texte', ''))}"
            )

        return "\n\n".join(lignes)