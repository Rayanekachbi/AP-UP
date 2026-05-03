# ============================================================
# test_filtering.py - Tests unitaires pour FilteringPipeline
# ============================================================

import sys
from unittest.mock import MagicMock

# On simule les bibliothèques lourdes
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['openai'] = MagicMock()

import unittest
import numpy as np
from unittest.mock import patch
from src.Backend.filtrage.filtering import FilteringPipeline
from src.Backend.filtrage.validators import FilterResult


# ============================================================
# TESTS DE FilteringPipeline
# ============================================================

class TestFilteringPipeline(unittest.TestCase):

    def setUp(self):
        """
        Préparation avant chaque test.
        On crée un FilteringPipeline et de faux données.
        """
        self.pipeline = FilteringPipeline()

        # Faux vecteurs de chunks du corpus
        np.random.seed(42)
        self.chunk_vectors = [np.random.rand(384).tolist() for _ in range(5)]

        # Faux chunks sources avec texte et vecteur
        self.chunks = [
            {"text": "Le modèle OSI comporte 7 couches.", "vector": np.random.rand(384).tolist()},
            {"text": "TCP/IP est un protocole de transport.", "vector": np.random.rand(384).tolist()},
            {"text": "Le routage IP permet de diriger les paquets.", "vector": np.random.rand(384).tolist()},
        ]

        self.question = "Comment fonctionne le protocole TCP ?"
        self.response = "TCP est un protocole de transport fiable qui assure la livraison des paquets."

    # --------------------------------------------------
    # TESTS DE validate_input
    # --------------------------------------------------

    def test_validate_input_acceptee(self):
        """
        CAS 1 : validate_input doit retourner is_valid=True
        si la question est liée au corpus.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.72):
            result = self.pipeline.validate_input(self.question, self.chunk_vectors)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.method, "cosine")

    def test_validate_input_bloquee(self):
        """
        CAS 2 : validate_input doit retourner is_valid=False
        si la question est hors-sujet.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.10):
            result = self.pipeline.validate_input("Recette de cuisine ?", self.chunk_vectors)
            self.assertFalse(result.is_valid)
            self.assertNotEqual(result.reason, "")

    # --------------------------------------------------
    # TESTS DE validate_output
    # --------------------------------------------------

    def test_validate_output_validee(self):
        """
        CAS 1 : validate_output doit retourner is_valid=True
        si la réponse est bien ancrée dans les chunks.
        """
        with patch.object(self.pipeline.output_validator, '_cosine_similarity', return_value=0.75):
            result = self.pipeline.validate_output(self.response, self.chunks)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.method, "cosine")

    def test_validate_output_bloquee(self):
        """
        CAS 2 : validate_output doit retourner is_valid=False
        si la réponse est hallucinée.
        """
        with patch.object(self.pipeline.output_validator, '_cosine_similarity', return_value=0.10):
            result = self.pipeline.validate_output("Réponse inventée.", self.chunks)
            self.assertFalse(result.is_valid)

    # --------------------------------------------------
    # TESTS DE run (pipeline complet)
    # --------------------------------------------------

    def test_run_tout_valide(self):
        """
        CAS 1 : Question valide + réponse valide → tout passe.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.72):
            with patch.object(self.pipeline.output_validator, '_cosine_similarity', return_value=0.75):
                result = self.pipeline.run(
                    question=self.question,
                    chunk_vectors=self.chunk_vectors,
                    response=self.response,
                    chunks=self.chunks
                )
                self.assertTrue(result.is_valid)

    def test_run_question_bloquee_en_entree(self):
        """
        CAS 2 : Question hors-sujet → bloquée dès l'entrée.
        Le validate_output ne doit PAS être appelé.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.10):
            with patch.object(self.pipeline, 'validate_output') as mock_output:
                result = self.pipeline.run(
                    question="Recette de cuisine ?",
                    chunk_vectors=self.chunk_vectors,
                    response=self.response,
                    chunks=self.chunks
                )
                self.assertFalse(result.is_valid)
                mock_output.assert_not_called()

    def test_run_reponse_bloquee_en_sortie(self):
        """
        CAS 3 : Question valide mais réponse hallucinée → bloquée en sortie.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.72):
            with patch.object(self.pipeline.output_validator, '_cosine_similarity', return_value=0.10):
                result = self.pipeline.run(
                    question=self.question,
                    chunk_vectors=self.chunk_vectors,
                    response="Réponse complètement inventée.",
                    chunks=self.chunks
                )
                self.assertFalse(result.is_valid)
                self.assertNotEqual(result.reason, "")

    def test_run_zone_grise_slm_valide(self):
        """
        CAS 4 : Question valide + réponse en zone grise + SLM dit OUI → validée.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.72):
            with patch.object(self.pipeline.output_validator, '_cosine_similarity', return_value=0.40):
                with patch.object(self.pipeline.output_validator, '_call_slm', return_value=(True, 0.85)):
                    result = self.pipeline.run(
                        question=self.question,
                        chunk_vectors=self.chunk_vectors,
                        response=self.response,
                        chunks=self.chunks
                    )
                    self.assertTrue(result.is_valid)
                    self.assertEqual(result.method, "slm")

    def test_run_zone_grise_slm_bloque(self):
        """
        CAS 5 : Question valide + réponse en zone grise + SLM dit NON → bloquée.
        """
        with patch.object(self.pipeline.input_validator, '_cosine_similarity', return_value=0.72):
            with patch.object(self.pipeline.output_validator, '_cosine_similarity', return_value=0.40):
                with patch.object(self.pipeline.output_validator, '_call_slm', return_value=(False, 0.32)):
                    result = self.pipeline.run(
                        question=self.question,
                        chunk_vectors=self.chunk_vectors,
                        response="Réponse douteuse.",
                        chunks=self.chunks
                    )
                    self.assertFalse(result.is_valid)
                    self.assertEqual(result.method, "slm")


# ============================================================
# LANCEMENT DES TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)