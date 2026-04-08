# ============================================================
# pdf_simple.py - Module 2 : Extraction PDF simple
# Utilise pdfplumber pour les PDF strictement textuels
# ============================================================

import pdfplumber
from src.Backend.ingestion.document_processor import DocumentProcessor


class PDFSimpleProcessor(DocumentProcessor):
    """
    Sous-classe pour les PDF strictement textuels.
    Utilise pdfplumber pour extraire le texte page par page.
    """

    def extract_text(self) -> str:
        """
        Extrait le texte brut d'un PDF simple page par page.
        Ajoute le numéro de page dans les métadonnées.

        Retourne le texte complet du document.
        """
        texte_complet = []

        with pdfplumber.open(self.file_path) as pdf:
            for numero_page, page in enumerate(pdf.pages, start=1):
                texte_page = page.extract_text()

                if texte_page:
                    # On préfixe chaque page pour garder la traçabilité
                    texte_complet.append(
                        f"[PAGE {numero_page}]\n{texte_page}"
                    )

        if not texte_complet:
            raise ValueError(
                f"Aucun texte détectable dans le fichier : {self.file_path.name}"
            )

        return "\n\n".join(texte_complet)