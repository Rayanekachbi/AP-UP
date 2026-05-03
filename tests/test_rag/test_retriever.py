import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class FakeEmbeddingModel:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, question):
        return FakeVector([0.1, 0.2, 0.3])


class FakeVector:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


fake_sentence_transformers = types.ModuleType("sentence_transformers")
fake_sentence_transformers.SentenceTransformer = FakeEmbeddingModel
sys.modules["sentence_transformers"] = fake_sentence_transformers

fake_vector_store = types.ModuleType("src.Backend.database.vector_store")
fake_vector_store.rechercher_chunks = MagicMock()
sys.modules["src.Backend.database.vector_store"] = fake_vector_store

retriever_module = importlib.import_module("src.Backend.rag.retriever")



class TestRetriever(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.retriever = retriever_module.Retriever(db=self.db, top_k=3)

    # vectoriser_question

    def test_vectoriser_question_retourne_liste(self):
        """Doit retourner exactement le vecteur produit par le modèle."""
        resultat = self.retriever.vectoriser_question("Question de test")
        self.assertEqual(resultat, [0.1, 0.2, 0.3])

    def test_vectoriser_question_retourne_une_liste_de_floats(self):
        """Le vecteur doit contenir uniquement des floats."""
        resultat = self.retriever.vectoriser_question("Question de test")
        self.assertTrue(all(isinstance(v, float) for v in resultat))

    def test_vectoriser_question_non_vide(self):
        """Le vecteur ne doit pas être vide."""
        resultat = self.retriever.vectoriser_question("Question de test")
        self.assertGreater(len(resultat), 0)

    def test_vectoriser_question_chaine_vide(self):
        """Même une question vide doit retourner un vecteur (comportement du modèle)."""
        resultat = self.retriever.vectoriser_question("")
        self.assertIsInstance(resultat, list)

    # retrieve_chunks

    def test_retrieve_chunks_retourne_les_resultats_du_vector_store(self):
        """Doit retourner exactement ce que rechercher_chunks renvoie."""
        faux_chunks = [{"id": 1, "text": "Contenu de test"}]
        with patch.object(
            retriever_module, "rechercher_chunks", return_value=faux_chunks
        ) as mock_rechercher:
            resultat = self.retriever.retrieve_chunks(question="Question de test", module_id=7)

        mock_rechercher.assert_called_once_with(
            db=self.db,
            query_vector=[0.1, 0.2, 0.3],
            module_id=7,
            top_k=3,
        )
        self.assertEqual(resultat, faux_chunks)

    def test_retrieve_chunks_appelle_vectoriser_question(self):
        """retrieve_chunks doit bien passer par vectoriser_question."""
        faux_chunks = [{"id": 1, "text": "Contenu"}]
        with patch.object(retriever_module, "rechercher_chunks", return_value=faux_chunks):
            with patch.object(
                self.retriever, "vectoriser_question", wraps=self.retriever.vectoriser_question
            ) as mock_vect:
                self.retriever.retrieve_chunks("Question", module_id=1)
                mock_vect.assert_called_once_with("Question")

    def test_retrieve_chunks_respecte_top_k(self):
        """Le top_k passé au constructeur doit être transmis à rechercher_chunks."""
        retriever_top5 = retriever_module.Retriever(db=self.db, top_k=5)
        faux_chunks = [{"id": i} for i in range(5)]
        with patch.object(
            retriever_module, "rechercher_chunks", return_value=faux_chunks
        ) as mock_rechercher:
            retriever_top5.retrieve_chunks("Question", module_id=1)
            _, kwargs = mock_rechercher.call_args
            self.assertEqual(kwargs["top_k"], 5)

    def test_retrieve_chunks_transmet_le_bon_module_id(self):
        """Le module_id doit être transmis tel quel à rechercher_chunks."""
        faux_chunks = [{"id": 1}]
        with patch.object(
            retriever_module, "rechercher_chunks", return_value=faux_chunks
        ) as mock_rechercher:
            self.retriever.retrieve_chunks("Question", module_id=42)
            _, kwargs = mock_rechercher.call_args
            self.assertEqual(kwargs["module_id"], 42)

    def test_retrieve_chunks_retourne_plusieurs_chunks(self):
        """Doit gérer une liste de plusieurs chunks sans problème."""
        faux_chunks = [{"id": i, "text": f"chunk {i}"} for i in range(3)]
        with patch.object(retriever_module, "rechercher_chunks", return_value=faux_chunks):
            resultat = self.retriever.retrieve_chunks("Question", module_id=1)
        self.assertEqual(len(resultat), 3)

    def test_retrieve_chunks_leve_une_erreur_si_aucun_chunk(self):
        """Doit lever ValueError si rechercher_chunks retourne une liste vide."""
        with patch.object(retriever_module, "rechercher_chunks", return_value=[]):
            with self.assertRaises(ValueError) as context:
                self.retriever.retrieve_chunks(question="Question sans contexte", module_id=99)

        self.assertIn("Aucun chunk trouve", str(context.exception).replace("é", "e"))
        self.assertIn("99", str(context.exception))
