# src/Backend/ingestion/pdf_complex.py

from docling.document_converter import DocumentConverter
from src.Backend.ingestion.document_processor import DocumentProcessor

class PDFComplexProcessor(DocumentProcessor):
    """
    Traducteur de PDF vers Markdown.
    Idéal pour les documents avec colonnes, tableaux et formules.
    Consomme beaucoup moins de RAM que Marker.
    """

    def extract_text(self) -> str:
        """
        Convertit le PDF complexe en Markdown vectorisable.
        """
        print(f"[DOCLING] Début de la conversion : {self.file_path.name}")
        
        try:
            # Initialiser le convertisseur Docling
            converter = DocumentConverter()
            
            # Lancer la conversion (Docling gère les tableaux/colonnes nativement)
            result = converter.convert(self.file_path)
            
            # Exporter le résultat en Markdown
            texte_markdown = result.document.export_to_markdown()
            
            if not texte_markdown:
                raise ValueError("Le document extrait est vide.")
                
            return texte_markdown

        except Exception as e:
            print(f"[ERREUR DOCLING] : {str(e)}")
            raise e