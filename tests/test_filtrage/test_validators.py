# ============================================================
# test_validators.py
# ============================================================

import sys
from unittest.mock import MagicMock

# On simule les bibliothèques lourdes pour ne pas avoir besoin
# de les installer pour faire tourner les tests
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['openai'] = MagicMock()


import unittest
import numpy as np
from unittest.mock import MagicMock, patch
from src.Backend.filtrage.validators import FilterResult, InputValidator, OutputValidator


# ============================================================
# TESTS DE FilterResult
# ============================================================

class TestFilterResult(unittest.TestCase):

    def test_filter_result_valide(self):
        """
        Vérifie qu'un FilterResult valide contient les bonnes valeurs.
        """
        result = FilterResult(is_valid=True, reason="", score=0.75, method="cosine")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason, "")
        self.assertEqual(result.score, 0.75)
        self.assertEqual(result.method, "cosine")

    def test_filter_result_invalide(self):
        """
        Vérifie qu'un FilterResult invalide contient les bonnes valeurs.
        """
        result = FilterResult(is_valid=False, reason="Question hors sujet", score=0.10, method="cosine")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "Question hors sujet")
        self.assertEqual(result.score, 0.10)
        self.assertEqual(result.method, "cosine")


# ============================================================
# TESTS DE InputValidator
# ============================================================

class TestInputValidator(unittest.TestCase):

    def setUp(self):
        """
        Préparation avant chaque test.
        On crée un InputValidator et de faux vecteurs de chunks.
        """
        self.validator = InputValidator()

        # Faux vecteurs de chunks qui représentent un cours de Réseaux
        # (384 dimensions car le modèle all-MiniLM-L6-v2 produit des vecteurs de 384)
        np.random.seed(42)
        self.chunk_vectors = [np.random.rand(384).tolist() for _ in range(5)]

    def test_question_acceptee(self):
        """
        CAS 1 : Une question liée au cours doit être acceptée.
        On simule un score élevé (0.72) en mockant la similarité cosinus.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.72):
            result = self.validator.validate("Comment fonctionne le protocole TCP ?", self.chunk_vectors)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.method, "cosine")
            self.assertEqual(result.reason, "")
            self.assertGreaterEqual(result.score, 0.35)

    def test_question_bloquee(self):
        """
        CAS 2 : Une question hors-sujet doit être bloquée.
        On simule un score très bas (0.08).
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.08):
            result = self.validator.validate("Quelle est la recette de la tarte aux pommes ?", self.chunk_vectors)
            self.assertFalse(result.is_valid)
            self.assertEqual(result.method, "cosine")
            self.assertNotEqual(result.reason, "")
            self.assertLess(result.score, 0.35)

    def test_question_exactement_au_seuil(self):
        """
        CAS LIMITE : Un score exactement égal à 0.35 doit être accepté.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.35):
            result = self.validator.validate("Question quelconque", self.chunk_vectors)
            self.assertTrue(result.is_valid)

    def test_chunks_vides_leve_exception(self):
        """
        CAS ERREUR : Si la liste de chunks est vide, une exception doit être levée.
        """
        with self.assertRaises(Exception):
            self.validator.validate("Une question", [])


# ============================================================
# TESTS DE OutputValidator
# ============================================================

class TestOutputValidator(unittest.TestCase):

    def setUp(self):
        """
        Préparation avant chaque test.
        On crée un OutputValidator et de faux chunks sources.
        """
        self.validator = OutputValidator()

        # Faux chunks sources (texte + vecteur)
        np.random.seed(42)
        self.chunks = [
            {"text": "Le modèle OSI comporte 7 couches.", "vector": np.random.rand(384).tolist()},
            {"text": "TCP/IP est un protocole de transport.", "vector": np.random.rand(384).tolist()},
            {"text": "Le routage IP permet de diriger les paquets.", "vector": np.random.rand(384).tolist()},
        ]

    def test_reponse_validee_directement(self):
        """
        CAS 1 : Score >= 0.50 → réponse validée directement sans appel au SLM.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.72):
            result = self.validator.validate("Le modèle OSI comporte 7 couches.", self.chunks)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.method, "cosine")

    def test_reponse_bloquee_directement(self):
        """
        CAS 2 : Score < 0.30 → réponse hallucinée, bloquée directement sans appel au SLM.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.10):
            result = self.validator.validate("La tour Eiffel est à Paris.", self.chunks)
            self.assertFalse(result.is_valid)
            self.assertEqual(result.method, "cosine")

    def test_zone_grise_slm_valide(self):
        """
        CAS 3a : Score dans la zone grise (0.30-0.50) et SLM dit OUI avec confiance >= 0.6.
        → Réponse validée par le SLM.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.40):
            with patch.object(self.validator, '_call_slm', return_value=(True, 0.85)):
                result = self.validator.validate("Une réponse dans la zone grise.", self.chunks)
                self.assertTrue(result.is_valid)
                self.assertEqual(result.method, "slm")
                self.assertEqual(result.score, 0.85)

    def test_zone_grise_slm_bloque(self):
        """
        CAS 3b : Score dans la zone grise (0.30-0.50) et SLM dit NON.
        → Réponse bloquée par le SLM.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.40):
            with patch.object(self.validator, '_call_slm', return_value=(False, 0.32)):
                result = self.validator.validate("Une réponse douteuse.", self.chunks)
                self.assertFalse(result.is_valid)
                self.assertEqual(result.method, "slm")
                self.assertNotEqual(result.reason, "")

    def test_zone_grise_slm_confiance_insuffisante(self):
        """
        CAS 3c : SLM dit OUI mais confiance < 0.6 → réponse bloquée quand même.
        """
        with patch.object(self.validator, '_cosine_similarity', return_value=0.40):
            with patch.object(self.validator, '_call_slm', return_value=(False, 0.50)):
                result = self.validator.validate("Une réponse peu confiante.", self.chunks)
                self.assertFalse(result.is_valid)
                self.assertEqual(result.method, "slm")


# ============================================================
# LANCEMENT DES TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)