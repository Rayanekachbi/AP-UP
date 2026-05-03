# ============================================================
# tests/integration/test_extraction_integration.py
# ============================================================
import pytest
from pathlib import Path
from src.Backend.ingestion.pdf_simple import PDFSimpleProcessor
from src.Backend.ingestion.pdf_complex import PDFComplexProcessor
from src.Backend.ingestion.other_formats import AudioVideoProcessor
from src.Backend.ingestion.other_formats import UnstructuredProcessor

# Marque tous les tests de ce fichier comme lents
pytestmark = pytest.mark.slow

def test_pdf_simple_vraie_extraction():
    """Test d'intégration réel sur le PDF simple de l'histoire de Léo."""
    # Chemin vers le fichier sample_simple.pdf
    chemin_pdf = Path(__file__).parent / "files" / "sample_simple.pdf"
    processeur = PDFSimpleProcessor(str(chemin_pdf))
    
    # Act
    texte_extrait = processeur.extract_text()
    
    # Assert
    assert "[PAGE 1]" in texte_extrait
    # On vérifie des phrases clés du texte !
    assert "Le Secret de la Forêt Écarlate" in texte_extrait
    assert "Dans un petit village niché au creux des montagnes" in texte_extrait


def test_pdf_complex_vraie_extraction_colonnes():
    """Test d'intégration réel avec Docling sur un PDF formaté en colonnes."""
    # Chemin vers le fichier sample_columns.pdf
    chemin_pdf = Path(__file__).parent / "files" / "sample_columns.pdf"
    processeur = PDFComplexProcessor(str(chemin_pdf))
    
    # Act
    texte_extrait = processeur.extract_text()
    
    # Assert
    assert isinstance(texte_extrait, str)
    assert len(texte_extrait) > 0
    # On vérifie que Docling a bien extrait le texte
    assert "Le Secret de la Forêt Écarlate" in texte_extrait
    # Surtout, on vérifie une phrase assez longue pour s'assurer que la lecture 
    # n'a pas sauté de la colonne de gauche vers la droite au milieu d'une ligne !
    assert "Un après-midi, alors que le ciel se couvrait de nuages" in texte_extrait


def test_audio_vraie_transcription():
    """Test d'intégration réel avec Whisper sur le cours de traitement d'images."""
    # Chemin vers ton fichier sample_audio.mp3
    chemin_audio = Path(__file__).parent / "files" / "sample_audio.mp3"
    processeur = AudioVideoProcessor(str(chemin_audio))
    
    # Act
    texte_extrait = processeur.extract_text()
    
    # Assert
    assert isinstance(texte_extrait, str)
    assert len(texte_extrait) > 0
    # On vérifie un bout de la transcription audio !
    assert "évaluation d'un système de traitement des images" in texte_extrait
    


def test_pdf_scanne_vraie_extraction_ocr():
    """Test d'intégration réel avec Unstructured (OCR) sur un PDF contenant une image."""
    # Chemin vers le fichier sample_scanned.pdf
    chemin_pdf = Path(__file__).parent / "files" / "sample_scanned.pdf"
    processeur = UnstructuredProcessor(str(chemin_pdf))
    
    # Act
    texte_extrait = processeur.extract_text()
    
    # Assert
    assert isinstance(texte_extrait, str)
    assert len(texte_extrait) > 0
    
    # On met le texte en minuscules pour l'assertion, car l'OCR peut parfois 
    # se tromper sur les majuscules selon la qualité de l'image.
    texte_minuscule = texte_extrait.lower()
    
    # On vérifie que l'OCR a bien "lu" l'image !
    assert "rapport confidentiel scanné" in texte_minuscule
    assert "fonctionne parfaitement" in texte_minuscule