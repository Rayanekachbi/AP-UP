# ============================================================
# tests/unit/test_chunking.py
# ============================================================
import pytest
from src.Backend.ingestion import chunking

# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------
@pytest.fixture
def mock_encodeur(mocker):
    """Mock propre de l'encodeur tiktoken."""
    return mocker.patch('src.Backend.ingestion.chunking.encodeur')

# ---------------------------------------------------------
# Tests de la logique métier pure
# ---------------------------------------------------------
def test_compter_tokens_vide(mock_encodeur):
    mock_encodeur.encode.return_value = []
    assert chunking.compter_tokens("") == 0

def test_compter_tokens_simple(mock_encodeur):
    mock_encodeur.encode.return_value = [1, 2, 3, 4, 5]
    assert chunking.compter_tokens("Hello world") == 5

def test_decouper_par_structure_avec_titres_markdown():
    texte = "## Titre 1\nContenu 1\n## Titre 2\nContenu 2"
    result = chunking._decouper_par_structure(texte)
    assert len(result) == 2
    assert "## Titre 1" in result[0]
    assert "## Titre 2" in result[1]

def test_decouper_par_structure_avec_paragraphes():
    texte = "Paragraphe 1\n\nParagraphe 2\n\nParagraphe 3"
    result = chunking._decouper_par_structure(texte)
    assert len(result) == 3
    assert result == ["Paragraphe 1", "Paragraphe 2", "Paragraphe 3"]

def test_redecoupage_par_saut_de_ligne(mocker):
    # On mock directement `compter_tokens` pour contrôler le flux de l'algorithme
    texte = "Partie 1\nPartie 2\nPartie 3"
    mocker.patch('src.Backend.ingestion.chunking.compter_tokens', side_effect=lambda txt: 150 if txt == texte else 10)
    
    result = chunking._redecouper(texte, chunk_size=50)
    assert len(result) >= 2

def test_appliquer_chevauchement_normal(mock_encodeur):
    chunks = ["Premier chunk", "Deuxième chunk", "Troisième chunk"]
    mock_encodeur.encode.side_effect = lambda txt: [ord(c) for c in txt[:5]]
    mock_encodeur.decode.return_value = "overlap_"
    
    result = chunking._appliquer_chevauchement(chunks, chunk_overlap=3)
    
    assert result[0] == "Premier chunk"
    assert "overlap_" in result[1]
    assert "overlap_" in result[2]

def test_extraire_page_avec_prefixe():
    result = chunking._extraire_page("[PAGE 5] Contenu", "...")
    assert result == 5

def test_chunk_text_workflow_complet(mocker):
    """Test global du découpage pour s'assurer que toutes les briques s'emboîtent."""
    mocker.patch('src.Backend.ingestion.chunking.compter_tokens', return_value=50)
    texte = "## Section 1\nContenu 1\n\n## Section 2\nContenu 2"
    metadata = {"source": "test.pdf"}
    
    result = chunking.chunk_text(texte, metadata, chunk_size=200, chunk_overlap=20)
    
    assert len(result) > 0
    assert "texte" in result[0]
    assert result[0]["source"] == "test.pdf"