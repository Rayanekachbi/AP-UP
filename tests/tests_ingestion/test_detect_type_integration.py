# ============================================================
# tests_ingestion/test_detect_type_integration.py
# ============================================================
import pytest
from pathlib import Path
from src.Backend.ingestion.document_processor import DocumentProcessor

# On marque ces tests comme lents car ils ouvrent de vrais fichiers
pytestmark = pytest.mark.slow

def test_detect_type_pdf_simple():
    """Vérifie qu'un PDF textuel classique est bien routé vers 'simple'."""
    chemin_pdf = Path(__file__).parent / "files" / "sample_simple.pdf"
    processeur = DocumentProcessor(str(chemin_pdf))
    
    # Act
    resultat = processeur.detect_type()
    
    # Assert
    assert resultat == "simple"
    assert processeur.file_type == "pdf"


def test_detect_type_pdf_complex_colonnes():
    """Vérifie qu'un PDF avec des colonnes est détecté comme 'complex'."""
    chemin_pdf = Path(__file__).parent / "files" / "sample_columns.pdf"
    processeur = DocumentProcessor(str(chemin_pdf))
    
    # Act
    resultat = processeur.detect_type()
    
    # Assert
    assert resultat == "complex"


def test_detect_type_pdf_scanne():
    """Vérifie qu'un PDF sans texte (juste une image) est détecté comme 'scanned'."""
    chemin_pdf = Path(__file__).parent / "files" / "sample_scanned.pdf"
    processeur = DocumentProcessor(str(chemin_pdf))
    
    # Act
    resultat = processeur.detect_type()
    
    # Assert
    assert resultat == "scanned"


def test_detect_type_audio():
    """Vérifie que les extensions audio sont bien routées vers 'audio_video'."""
    chemin_audio = Path(__file__).parent / "files" / "sample_audio.mp3"
    processeur = DocumentProcessor(str(chemin_audio))
    
    # Act
    resultat = processeur.detect_type()
    
    # Assert
    assert resultat == "audio_video"
    assert processeur.file_type == "mp3"