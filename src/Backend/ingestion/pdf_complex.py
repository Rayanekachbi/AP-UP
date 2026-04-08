# ============================================================
# pdf_complex.py - Module 2 : Extraction PDF complexe
# Utilise marker-pdf pour les PDF avec tableaux/colonnes/formules
# ============================================================

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from src.Backend.ingestion.document_processor import DocumentProcessor


class PDFComplexProcessor(DocumentProcessor):
    """
    Sous-classe pour les PDF complexes contenant des tableaux,
    du texte en colonnes ou des formules mathématiques.
    Utilise marker-pdf qui retourne du Markdown structuré.
    """

    def extract_text(self) -> str:
        """
        Extrait le texte d'un PDF complexe via PdfConverter.
        Retourne le contenu en Markdown structuré.
        """
        # Charger le dictionnaire de modèles
        model_dict = create_model_dict()

        # Initialiser le convertisseur
        converter = PdfConverter(artifact_dict=model_dict)

        # Convertir le fichier
        # rendered est un objet contenant le texte et les métadonnées
        rendered = converter(str(self.file_path))

        # Extraire le texte markdown
        # text_from_rendered retourne (texte_complet, images, metadonnées)
        texte_markdown, _, _ = text_from_rendered(rendered)

        if not texte_markdown or len(texte_markdown.strip()) < 10:
            raise ValueError(
                f"Extraction échouée pour le fichier : {self.file_path.name}"
            )

        return texte_markdown