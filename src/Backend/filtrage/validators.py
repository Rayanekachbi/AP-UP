# ============================================================
# validators.py - SLM (ministral-3:3b) + COSINE STABLE
# ============================================================

import re
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from src.config.settings import (
    SIMILARITY_THRESHOLD_OUT_HIGH,
    SIMILARITY_THRESHOLD_OUT_LOW,
    SLM_CONFIDENCE_THRESHOLD,
    SLM_MODEL,
    OLLAMA_BASE_URL,
    MESSAGE_QUESTION_BLOQUEE,
    MESSAGE_REPONSE_BLOQUEE,
    EMBEDDING_MODEL,
    SIMILARITY_THRESHOLD_IN,
    COSINE_OVERRIDE_THRESHOLD,
)

logger = logging.getLogger(__name__)

SYSTEM_CLASSIFIEUR = "Tu es un classifieur binaire. Reponds uniquement OUI ou NON sans rien ajouter."


# ============================================================
# RESULT
# ============================================================

class FilterResult:
    def __init__(self, is_valid, reason, score, method, response=""):
        self.is_valid = is_valid
        self.reason = reason
        self.score = score
        self.method = method
        self.response = response


# ============================================================
# INPUT VALIDATOR (SLM + fallback cosine)
# ============================================================

class InputValidator:

    def __init__(self, model: SentenceTransformer = None):
        self.model = model or SentenceTransformer(EMBEDDING_MODEL)
        self.client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    def cosine(self, a, b):
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    def centroid(self, vecs):
        return np.mean(vecs, axis=0)

    def build_prompt(self, q, chunks):
        text = "\n".join(f"[{i+1}] {c.get('text', '')[:300]}" for i, c in enumerate(chunks[:5]))
        return (
            f"Voici des extraits d un cours :\n{text}\n\n"
            f"La question suivante porte-t-elle sur un sujet aborde dans ces extraits ?\n"
            f"Question : {q}\n"
            f"Reponds OUI si la question concerne un concept present dans les extraits, NON sinon."
        )

    def parse(self, text):
        upper = text.upper()
        decision = "OUI" if "OUI" in upper else "NON"
        match = re.search(r"\b(0\.\d+|1\.0)\b", text)
        score = float(match.group()) if match else 0.5
        return decision == "OUI", score

    def validate(self, question, chunk_vectors, chunks_preview):
        try:
            resp = self.client.chat.completions.create(
                model=SLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_CLASSIFIEUR},
                    {"role": "user", "content": self.build_prompt(question, chunks_preview)},
                ],
                temperature=0,
                max_tokens=3,
            )

            slm_text = resp.choices[0].message.content
            logger.debug("SLM raw input response: %r", slm_text)
            is_valid, conf = self.parse(slm_text)
            logger.debug("SLM input → %s (conf=%.3f)", "OUI" if is_valid else "NON", conf)

            q_vec = self.model.encode(question)
            c_vec = self.centroid(chunk_vectors)
            cosine = self.cosine(q_vec, c_vec)
            logger.debug("Cosine input = %.3f", cosine)

            if is_valid and conf >= SLM_CONFIDENCE_THRESHOLD:
                return FilterResult(True, "", conf, "slm")

            if cosine > COSINE_OVERRIDE_THRESHOLD:
                logger.debug("Cosine override (%.3f > %.3f)", cosine, COSINE_OVERRIDE_THRESHOLD)
                return FilterResult(True, "", cosine, "cosine_override")

            return FilterResult(False, MESSAGE_QUESTION_BLOQUEE, conf, "slm")

        except Exception as e:
            logger.warning("SLM indisponible, fallback cosine : %s", e)
            return self._fallback(question, chunk_vectors)

    def _fallback(self, question, chunk_vectors):
        if not chunk_vectors:
            return FilterResult(False, MESSAGE_QUESTION_BLOQUEE, 0.0, "cosine")
        q = self.model.encode(question)
        c = np.mean(chunk_vectors, axis=0)
        score = float(np.dot(q, c) / (np.linalg.norm(q) * np.linalg.norm(c) + 1e-9))
        return FilterResult(
            score > SIMILARITY_THRESHOLD_IN,
            MESSAGE_QUESTION_BLOQUEE,
            score,
            "cosine"
        )


# ============================================================
# OUTPUT VALIDATOR (cosine + SLM zone grise)
# ============================================================

class OutputValidator:

    def __init__(self, model: SentenceTransformer = None):
        self.model = model or SentenceTransformer(EMBEDDING_MODEL)
        self.client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    def cosine(self, a, b):
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    def _build_slm_prompt(self, response, chunks):
        chunks_text = ""
        for i, chunk in enumerate(chunks, start=1):
            texte = chunk.get("text", chunk.get("texte", ""))
            chunks_text += f"[{i}] {texte[:300]}\n\n"
        return (
            f"Voici des extraits d un cours :\n{chunks_text}"
            f"Voici une reponse generee : {response[:500]}\n\n"
            f"La reponse est-elle fidele et ancree dans les extraits du cours ?\n"
            f"Reponds OUI si la reponse s appuie sur les extraits, NON sinon."
        )

    def _call_slm(self, response, chunks):
        try:
            resp = self.client.chat.completions.create(
                model=SLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_CLASSIFIEUR},
                    {"role": "user", "content": self._build_slm_prompt(response, chunks)},
                ],
                max_tokens=3,
                temperature=0.0,
            )
            slm_text = resp.choices[0].message.content
            logger.debug("SLM output raw: %r", slm_text)
            upper = slm_text.upper()
            decision = "OUI" if "OUI" in upper else "NON"
            match = re.search(r"\b(0\.\d+|1\.0)\b", slm_text)
            confidence = float(match.group()) if match else 0.5
            return decision == "OUI", confidence
        except Exception as e:
            logger.warning("SLM output indisponible : %s", e)
            return True, 0.5

    def validate(self, response, chunks):

        vectors = []
        for c in chunks:
            v = c.get("vector")
            if v is None:
                v = c.get("embedding")
            if v is not None:
                vectors.append(np.array(v))

        if not vectors:
            return FilterResult(False, MESSAGE_REPONSE_BLOQUEE, 0.0, "no_vectors")

        r = self.model.encode(response)
        c = np.mean(vectors, axis=0)
        score = self.cosine(r, c)
        logger.debug("Cosine output = %.3f", score)

        if score >= SIMILARITY_THRESHOLD_OUT_HIGH:
            return FilterResult(True, "", score, "cosine")

        if score < SIMILARITY_THRESHOLD_OUT_LOW:
            return FilterResult(False, MESSAGE_REPONSE_BLOQUEE, score, "cosine")

        # Zone grise → SLM
        logger.debug("Zone grise output (%.3f), appel SLM...", score)
        is_valid, confidence = self._call_slm(response, chunks)
        return FilterResult(
            is_valid,
            "" if is_valid else MESSAGE_REPONSE_BLOQUEE,
            confidence,
            "slm"
        )