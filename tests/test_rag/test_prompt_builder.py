import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


fake_vector_store = types.ModuleType("src.Backend.database.vector_store")
fake_vector_store.get_system_prompt = MagicMock()
sys.modules["src.Backend.database.vector_store"] = fake_vector_store

import importlib
prompt_builder_module = importlib.import_module("src.Backend.rag.prompt_builder")


class TestPromptBuilder(unittest.TestCase):
    """Tests pour PromptBuilder."""

    def setUp(self):
        """Crée un builder avant chaque test."""
        self.db = MagicMock()
        self.builder = prompt_builder_module.PromptBuilder(db=self.db)

 
    def _build(self, question="Q?", chunks=None, module_id=1, system_prompt="Prompt."):
        """Appelle build_prompt avec un patch sur get_system_prompt."""
        if chunks is None:
            chunks = []
        with patch.object(prompt_builder_module, "get_system_prompt", return_value=system_prompt):
            return self.builder.build_prompt(question=question, chunks=chunks, module_id=module_id)

    #Test de build_prompt
    def test_retourne_exactement_deux_messages(self):
        messages = self._build()
        self.assertEqual(len(messages), 2)

    def test_premier_message_est_system(self):
        messages = self._build(system_prompt="Tu es un assistant.")
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "Tu es un assistant.")

    def test_deuxieme_message_est_user(self):
        messages = self._build()
        self.assertEqual(messages[1]["role"], "user")

    def test_question_presente_dans_message_user(self):
        messages = self._build(question="Question de test")
        self.assertIn("Question de test", messages[1]["content"])

    def test_header_contexte_present(self):
        messages = self._build()
        self.assertIn("Contexte extrait du cours :", messages[1]["content"])

    def test_chunks_numerotes_dans_message_user(self):
        chunks = [
            {"text": "Reponse 1", "source": "document_test.pdf", "section": "Partie 1"},
            {"text": "Reponse 2", "source": "document_test.pdf", "page": 12},
        ]
        messages = self._build(chunks=chunks)
        self.assertIn("[1] (source: document_test.pdf, section: Partie 1)", messages[1]["content"])
        self.assertIn("[2] (source: document_test.pdf, page: 12)", messages[1]["content"])

    def test_get_system_prompt_appele_avec_bons_args(self):
        with patch.object(prompt_builder_module, "get_system_prompt", return_value="P.") as mock:
            self.builder.build_prompt(question="Q?", chunks=[], module_id=42)
        mock.assert_called_once_with(db=self.db, module_id=42)


    #Tests : _formater_chunks
    def test_liste_vide_retourne_chaine_vide(self):
        self.assertEqual(self.builder._formater_chunks([]), "")

    def test_chunk_avec_section(self):
        chunks = [{"text": "Contenu.", "source": "cours.pdf", "section": "1.1 Intro"}]
        resultat = self.builder._formater_chunks(chunks)
        self.assertIn("[1] (source: cours.pdf, section: 1.1 Intro)", resultat)

    def test_chunk_avec_page(self):
        chunks = [{"text": "Contenu.", "source": "cours.pdf", "page": 5}]
        resultat = self.builder._formater_chunks(chunks)
        self.assertIn("[1] (source: cours.pdf, page: 5)", resultat)

    def test_chunk_sans_section_ni_page(self):
        chunks = [{"text": "Contenu.", "source": "cours.pdf"}]
        resultat = self.builder._formater_chunks(chunks)
        self.assertIn("[1] (source: cours.pdf)", resultat)
        self.assertNotIn("section", resultat)
        self.assertNotIn("page",    resultat)

    def test_chunk_sans_source_utilise_inconnu(self):
        chunks = [{"text": "Contenu sans source."}]
        resultat = self.builder._formater_chunks(chunks)
        self.assertIn("source: inconnu", resultat)

    def test_section_prioritaire_sur_page(self):

        chunks = [{"text": "Salut", "source": "f.pdf", "section": "2.1", "page": 3}]
        resultat = self.builder._formater_chunks(chunks)
        self.assertIn("section: 2.1", resultat)
        self.assertNotIn("page:",     resultat)
