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


class FakeOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=MagicMock(return_value=[]))
        )


fake_sentence_transformers = types.ModuleType("sentence_transformers")
fake_sentence_transformers.SentenceTransformer = FakeEmbeddingModel
sys.modules["sentence_transformers"] = fake_sentence_transformers

fake_openai = types.ModuleType("openai")
fake_openai.OpenAI = FakeOpenAI
sys.modules["openai"] = fake_openai

fake_vector_store = types.ModuleType("src.Backend.database.vector_store")
fake_vector_store.rechercher_chunks = MagicMock()
fake_vector_store.get_system_prompt = MagicMock(return_value="Prompt systeme")
fake_vector_store.sauvegarder_historique = MagicMock()
sys.modules["src.Backend.database.vector_store"] = fake_vector_store

rag_engine_module = importlib.import_module("src.Backend.rag.rag_engine")

# helper method
def faire_faux_token(content):
    """Crée un faux chunk OpenAI stream avec un contenu donné."""
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(
            delta=types.SimpleNamespace(content=content)
        )]
    )

class TestRAGEngine(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.engine = rag_engine_module.RAGEngine(db=self.db, utilisateur_id=12, top_k=2)

    # tester la methode run

    def test_run_pipeline_complet(self):
        """run() doit appeler les 3 sous-méthodes dans l'ordre et stocker les métadonnées."""
        chunks = [
            {"id": 10, "text": "Chunk 1"},
            {"id": 11, "text": "Chunk 2"},
        ]
        messages = [{"role": "system", "content": "prompt"}]

        with patch.object(self.engine.retriever, "retrieve_chunks", return_value=chunks) as mock_retrieve:
            with patch.object(self.engine.prompt_builder, "build_prompt", return_value=messages) as mock_build:
                with patch.object(self.engine, "stream_response", return_value=iter(["Bon", "jour"])) as mock_stream:
                    tokens = list(self.engine.run(question="Salut ?", module_id=4))

        mock_retrieve.assert_called_once_with(question="Salut ?", module_id=4)
        mock_build.assert_called_once_with(question="Salut ?", chunks=chunks, module_id=4)
        mock_stream.assert_called_once_with(messages)
        self.assertEqual(tokens, ["Bon", "jour"])
        self.assertEqual(self.engine._derniere_reponse, "Bonjour")
        self.assertEqual(self.engine._derniers_chunks, chunks)
        self.assertEqual(self.engine._derniere_question, "Salut ?")
        self.assertEqual(self.engine._dernier_module_id, 4)
        self.assertEqual(self.engine._derniers_chunks_ids, [10, 11])

    # stream_response 

    def test_stream_filtre_tokens_vides(self):
        """Doit retourner uniquement les tokens dont le contenu est non-None et non-vide."""
        stream = [
            faire_faux_token("Bon"),
            faire_faux_token(None),
            faire_faux_token(""),
            faire_faux_token("jour"),
        ]

        self.engine.llm_client.chat.completions.create = MagicMock(return_value=stream)

        tokens = list(self.engine.stream_response([{"role": "user", "content": "test"}]))

        self.assertEqual(tokens, ["Bon", "jour"])
        self.engine.llm_client.chat.completions.create.assert_called_once()

    def test_stream_stream_true(self):
        """Doit appeler le LLM avec stream=True et les bons messages."""
        self.engine.llm_client.chat.completions.create = MagicMock(return_value=[])
        messages = [{"role": "user", "content": "Question ?"}]

        list(self.engine.stream_response(messages=messages))

        _, kwargs = self.engine.llm_client.chat.completions.create.call_args
        self.assertEqual(kwargs["messages"], messages)
        self.assertTrue(kwargs["stream"])

    def test_stream_vide(self):
        """Si le LLM ne retourne aucun token, le générateur doit être vide."""
        self.engine.llm_client.chat.completions.create = MagicMock(return_value=[])

        tokens = list(self.engine.stream_response([]))

        self.assertEqual(tokens, [])


    # sauvegarder

    def test_sauvegarder_appelle_historique(self):
        """sauvegarder() doit appeler sauvegarder_historique avec toutes les données stockées."""
        self.engine._dernier_module_id = 8
        self.engine._derniere_question = "Question"
        self.engine._derniere_reponse = "Reponse"
        self.engine._derniers_chunks_ids = [1, 2, 3]

        with patch.object(rag_engine_module, "sauvegarder_historique") as mock_sauvegarder:
            self.engine.sauvegarder()

        mock_sauvegarder.assert_called_once_with(
            db=self.db,
            utilisateur_id=12,
            module_id=8,
            question="Question",
            reponse="Reponse",
            chunks_ids=[1, 2, 3],
        )
