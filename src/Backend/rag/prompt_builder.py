# ============================================================
# prompt_builder.py - Module 4 : Assemblage du prompt
# Construit le prompt enrichi envoyé au LLM
# ============================================================

from sqlalchemy.orm import Session
from src.Backend.database.vector_store import get_system_prompt, get_historique_recent
from src.config.settings import NB_ECHANGES_HISTORIQUE


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
        module_id: int,
        utilisateur_id: int
    ) -> list[dict]:
        """
        Assemble le prompt final selon la structure :
        - Message système : prompt défini par l'enseignant
        - Historique de conversation : échanges récents entre l'étudiant et l'assistant
        - Message utilisateur : contexte (chunks) + question

        Paramètres :
        - question  : question de l'étudiant
        - chunks    : liste des chunks récupérés par le Retriever
        - module_id : ID du module pour récupérer le prompt système et filtrer l'historique
        - utilisateur_id : ID de l'utilisateur pour récupérer l'historique de ses échanges récents

        Retourne une liste de messages au format OpenAI.
        """

        # Étape 1 : récupérer le prompt système
        system_prompt = get_system_prompt(
            db=self.db,
            module_id=module_id
        )
        system_prompt += (
            "\n\nSi l'utilisateur fait référence à quelque chose mentionné "
            "dans les échanges précédents (par exemple 'son', 'il', 'ce concept'), "
            "utilise l'historique de la conversation pour comprendre le contexte."
        )
        # Étape 2 : formater les chunks avec numérotation et sources
        contexte = self._formater_chunks(chunks)

        # Étape 3 : récupérer l'historique récent
        historique = get_historique_recent(
            db=self.db,
            utilisateur_id=utilisateur_id,
            module_id=module_id,
            nb_echanges=NB_ECHANGES_HISTORIQUE
        )

        # Étape 4 : construire la liste de messages
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Étape 5 : ajouter l'historique conversationnel
        for echange in historique:
            messages.append({
                "role": "user",
                "content": echange["question"]
            })
            messages.append({
                "role": "assistant",
                "content": echange["reponse"]
            })

        # Étape 6 : ajouter la question actuelle avec le contexte
        messages.append({
            "role": "user",
            "content": (
                f"Contexte extrait du cours :\n"
                f"{contexte}\n\n"
                f"Question : {question}"
            )
        })

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