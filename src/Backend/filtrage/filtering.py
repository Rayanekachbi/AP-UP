# ============================================================
# filtering.py - Module 5 : Filtrage et Sécurité (STABLE)
# ============================================================

import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from src.Backend.filtrage.validators import FilterResult, InputValidator, OutputValidator
from src.config.settings import (
    MESSAGE_QUESTION_BLOQUEE,
    MESSAGE_REPONSE_BLOQUEE,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
    SLM_MODEL,
)

logger = logging.getLogger(__name__)

OLLAMA_URL = OLLAMA_BASE_URL
LLM_MODEL = SLM_MODEL


class FilteringPipeline:

    def __init__(self):
        # Modèle chargé une seule fois et partagé entre les deux validators
        self._shared_model = SentenceTransformer(EMBEDDING_MODEL)

        self.input_validator = InputValidator(model=self._shared_model)
        self.output_validator = OutputValidator(model=self._shared_model)

        self.llm_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

    # ============================================================
    # INPUT
    # ============================================================

    def validate_input(self, question: str, chunk_vectors: list, chunks_preview=None):

        result = self.input_validator.validate(question, chunk_vectors, chunks_preview)

        if not result.is_valid and chunks_preview:
            suggestions = self.suggest_questions(question, chunks_preview)
            if suggestions:
                result.reason += "\n💡 Suggestions :\n" + "\n".join(
                    f"{i+1}. {s}" for i, s in enumerate(suggestions)
                )

        return result

    # ============================================================
    # OUTPUT
    # ============================================================

    def validate_output(self, response: str, chunks: list):

        result = self.output_validator.validate(response, chunks)

        if result.is_valid:
            refs = self.format_references(chunks)
            result.response = response + refs

        return result

    # ============================================================
    # ORCHESTRATEUR
    # ============================================================

    def run(self, question: str, chunk_vectors: list, response: str, chunks: list, chunks_preview: list = None) -> FilterResult:
        chunks_preview = chunks_preview or chunks
        input_result = self.validate_input(question, chunk_vectors, chunks_preview)

        if not input_result.is_valid:
            logger.info("[FILTRAGE ENTRÉE] Bloquée. Score=%.2f méthode=%s", input_result.score, input_result.method)
            return input_result

        logger.info("[FILTRAGE ENTRÉE] Acceptée. Score=%.2f méthode=%s", input_result.score, input_result.method)

        output_result = self.validate_output(response, chunks)

        if not output_result.is_valid:
            logger.info("[FILTRAGE SORTIE] Bloquée. Score=%.2f méthode=%s", output_result.score, output_result.method)
        else:
            logger.info("[FILTRAGE SORTIE] Validée. Score=%.2f méthode=%s", output_result.score, output_result.method)

        return output_result

    # ============================================================
    # SUGGESTIONS — reformulées en vraies questions via SLM
    # ============================================================

    def suggest_questions(self, question: str, chunks_preview: list, top_k: int = 3) -> list:
        """
        Sélectionne les top_k chunks les plus proches de la question,
        puis demande au SLM de reformuler chaque extrait en une vraie question.
        """
        q_vec = self._shared_model.encode(question)

        scores = []
        for c in chunks_preview:
            chunk_vec = np.array(c.get("vector"))
            sim = np.dot(q_vec, chunk_vec) / (
                np.linalg.norm(q_vec) * np.linalg.norm(chunk_vec) + 1e-9
            )
            scores.append((sim, c.get("text", "")))

        scores.sort(reverse=True)
        top_texts = [t for _, t in scores[:top_k]]

        # Reformulation SLM
        suggestions = []
        for text in top_texts:
            try:
                prompt = (
                    f"Voici un extrait de cours :\n\"{text[:400]}\"\n\n"
                    "Formule une question pédagogique courte et claire (max 15 mots) "
                    "qu'un étudiant pourrait poser sur cet extrait. "
                    "Réponds uniquement avec la question, sans ponctuation finale."
                )
                resp = self.llm_client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=40,
                    temperature=0.3,
                )
                q = resp.choices[0].message.content.strip().strip("?").strip() + " ?"
                suggestions.append(q)
            except Exception as e:
                logger.warning("Reformulation SLM échouée : %s", e)
                # Fallback : on retourne le début du chunk si le SLM plante
                suggestions.append(text[:80] + "...")

        return suggestions

    # ============================================================
    # REFERENCES — dédupliquées
    # ============================================================

    def format_references(self, chunks: list) -> str:
        seen = {}
        for c in chunks:
            source = c.get("source", "unknown")
            section = c.get("section", "unknown")
            key = f"{source}||{section}"
            seen[key] = f"📄 {source} — {section}"

        if not seen:
            return ""

        return "\n\n---\nSources :\n" + "\n".join(seen.values())