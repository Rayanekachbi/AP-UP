# ============================================================
# tests/unit/test_document_processor.py
# ============================================================
import pytest
from pathlib import Path
from src.Backend.ingestion.document_processor import DocumentProcessor
from unittest.mock import patch, MagicMock

class TestDocumentProcessorLogic:
    """Tests concentrés sur la VRAIE logique métier."""
    
    @pytest.fixture
    def processor(self):
        return DocumentProcessor("/path/to/fake.pdf")

    # ---------------------------------------------------------
    # Tests du nettoyage de texte
    # ---------------------------------------------------------
    def test_clean_text_espaces_multiples(self, processor):
        texte = "Texte   avec    beaucoup     d'espaces"
        result = processor.clean_text(texte)
        assert result == "Texte avec beaucoup d'espaces"
    
    def test_clean_text_retours_ligne_windows(self, processor):
        texte = "Ligne 1\r\nLigne 2\r\nLigne 3"
        result = processor.clean_text(texte)
        assert result == "Ligne 1\nLigne 2\nLigne 3"
    
    def test_clean_text_lignes_vides_consecutives(self, processor):
        texte = "Ligne 1\n\n\n\n\nLigne 2"
        result = processor.clean_text(texte)
        assert result == "Ligne 1\n\nLigne 2"

    # ---------------------------------------------------------
    # Tests de l'algorithme de détection de colonnes (PyMuPDF)
    # ---------------------------------------------------------

    @patch('pymupdf.open')
    def test_pas_de_colonnes_texte_normal(self, mock_pymupdf_open, processor):
        """Du texte empilé verticalement, sans chevauchement horizontal."""
        # On crée une fausse page
        mock_page = MagicMock()
        # On simule le retour de get_text("blocks")
        # Format attendu : (x0, y0, x1, y1, "texte", block_no, block_type)
        mock_page.get_text.return_value = [
            (100, 100, 500, 200, "Paragraphe 1", 0, 0),
            (100, 210, 500, 300, "Paragraphe 2", 1, 0)
        ]
        
        # On fait en sorte que doc[:3] retourne une liste contenant notre fausse page
        mock_doc = MagicMock()
        mock_doc.__getitem__.return_value = [mock_page]
        mock_pymupdf_open.return_value = mock_doc
        
        # On appelle la fonction sans argument (elle utilise le mock en interne)
        assert processor._est_en_colonnes() is False

    @patch('pymupdf.open')
    def test_vraies_colonnes_detectees(self, mock_pymupdf_open, processor):
        """Deux blocs de texte côte à côte (chevauchement Y, espacés en X)."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = [
            # Colonne gauche (y: 100->500, x: 50->250)
            (50, 100, 250, 500, "Colonne de gauche", 0, 0),
            # Colonne droite (y: 100->500, x: 300->500)
            (300, 100, 500, 500, "Colonne de droite", 1, 0)
        ]
        
        mock_doc = MagicMock()
        mock_doc.__getitem__.return_value = [mock_page]
        mock_pymupdf_open.return_value = mock_doc
        
        assert processor._est_en_colonnes() is True

    @patch('pymupdf.open')
    def test_colonnes_erreur_silencieuse(self, mock_pymupdf_open, processor):
        """Si PyMuPDF crashe (fichier corrompu), la fonction doit retourner False proprement."""
        mock_pymupdf_open.side_effect = Exception("PDF illisible")
        
        # Vérifie que le try/except fait bien son travail
        assert processor._est_en_colonnes() is False

    # ---------------------------------------------------------
    # Tests du routage (très simplifiés)
    # ---------------------------------------------------------
    def test_detect_type_pptx(self, processor):
        processor.file_path = Path("/path/to/presentation.pptx")
        assert processor.detect_type() == "unstructured"

    def test_detect_type_format_non_supporte(self, processor):
        processor.file_path = Path("/path/to/file.xyz")
        with pytest.raises(ValueError, match="Format non supporté"):
            processor.detect_type()