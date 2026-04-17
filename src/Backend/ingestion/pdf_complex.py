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
            # 1. Initialiser le convertisseur Docling
            converter = DocumentConverter()
            
            # 2. Lancer la conversion (Docling gère les tableaux/colonnes nativement)
            result = converter.convert(self.file_path)
            
            # 3. Exporter le résultat en Markdown
            # Ce format est parfait pour ton module chunking.py qui cherche les titres '#'
            texte_markdown = result.document.export_to_markdown()
            
            if not texte_markdown:
                raise ValueError("Le document extrait est vide.")
                
            return texte_markdown

        except Exception as e:
            print(f"[ERREUR DOCLING] : {str(e)}")
            raise e