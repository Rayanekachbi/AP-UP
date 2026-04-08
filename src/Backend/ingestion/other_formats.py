# ============================================================
# other_formats.py - Module 2 : Formats non-PDF
# Utilise unstructured pour PPTX, DOCX, HTML, images/scans
# Utilise whisper pour les fichiers audio/vidéo
# ============================================================

from unstructured.partition.auto import partition
from src.Backend.ingestion.document_processor import DocumentProcessor


class UnstructuredProcessor(DocumentProcessor):
    """
    Sous-classe pour les formats non-PDF et les PDF scannés.
    Utilise unstructured avec OCR pour les images et scans.
    Formats supportés : PPTX, DOCX, HTML, images, PDF scannés.
    """

    def extract_text(self) -> str:
        """
        Extrait le texte via unstructured.
        Pour les images et scans, active automatiquement l'OCR.

        Retourne le texte extrait sous forme de string.
        """
        elements = partition(filename=str(self.file_path))

        if not elements:
            raise ValueError(
                f"Aucun contenu extrait depuis : {self.file_path.name}"
            )

        # Joindre tous les éléments extraits
        texte = "\n\n".join([str(el) for el in elements])

        return texte


class AudioVideoProcessor(DocumentProcessor):
    """
    Sous-classe pour les fichiers audio et vidéo.
    Utilise whisper pour la transcription automatique.
    Formats supportés : MP4, MP3.
    """

    def extract_text(self) -> str:
        """
        Transcrit le fichier audio/vidéo via whisper.
        Retourne la transcription complète sous forme de string.
        """
        import whisper

        # Charger le modèle whisper (base = bon compromis vitesse/qualité)
        model = whisper.load_model("base")

        # Transcrire le fichier
        result = model.transcribe(str(self.file_path))

        if not result or not result.get("text"):
            raise ValueError(
                f"Transcription échouée pour : {self.file_path.name}"
            )

        return result["text"]