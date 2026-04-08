# ============================================================
# document_processor.py - Module 2 : Classe principale
# Orchestre l'extraction, le nettoyage et le découpage
# ============================================================

from pathlib import Path
from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP


# ============================================================
# CLASSE PRINCIPALE : DocumentProcessor
# Contient la logique commune à tous les types de fichiers
# ============================================================

class DocumentProcessor:
    """
    Classe de base pour le traitement des documents pédagogiques.
    Chaque sous-classe surcharge uniquement extract_text()
    selon le format du fichier.
    """

    FORMATS_SUPPORTES = ["pdf", "pptx", "docx", "html", "mp4", "mp3"]

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_type: str = ""           # extension détectée
        self.pdf_complexity: str = ""      # "simple", "complex" ou "scanned"
        self.raw_text: str = ""            # texte brut extrait
        self.chunks: list[dict] = []       # fragments après découpage
        self.chunk_size: int = CHUNK_SIZE
        self.chunk_overlap: int = CHUNK_OVERLAP
        self.metadata: dict = {}           # nom, page, section

    # ============================================================
    # MÉTHODE 1 : detect_type()
    # Détecte le type de fichier et sa complexité si c'est un PDF
    # ============================================================

    def detect_type(self) -> str:
        """
        Détecte le type de fichier à partir de son extension.
        Pour les PDF, délègue à analyze_pdf_complexity().

        Retourne le type détecté : "pdf_simple", "pdf_complex",
        "scanned", "pptx", "docx", "html", "audio_video"
        """
        extension = self.file_path.suffix.lower().strip(".")

        if extension not in self.FORMATS_SUPPORTES:
            raise ValueError(f"Format non supporté : {extension}")

        self.file_type = extension

        if extension == "pdf":
            return self.analyze_pdf_complexity()

        elif extension in ["pptx", "docx", "html"]:
            return "unstructured"

        elif extension in ["mp4", "mp3"]:
            return "audio_video"

        return extension

    # ============================================================
    # MÉTHODE 2 : analyze_pdf_complexity()
    # Parcourt le PDF pour détecter sa complexité
    # ============================================================

    def analyze_pdf_complexity(self) -> str:
        """
        Analyse le contenu du PDF pour choisir le bon parser.
        Parcourt toutes les pages et s'arrête dès qu'un indicateur
        de complexité est détecté.

        Retourne :
        - "simple"  → pdfplumber suffit
        - "complex" → marker-pdf nécessaire (tableaux, colonnes, formules)
        - "scanned" → unstructured + OCR nécessaire
        """
        import pdfplumber

        with pdfplumber.open(self.file_path) as pdf:
            texte_total = "" # Variable pour vérifier le volume de texte global

            for page in pdf.pages:
                # Vérification 1 : présence de tableaux
                if page.extract_tables():
                    self.pdf_complexity = "complex"
                    return "complex"

                # Extraction du texte pour les vérifications
                texte_page = page.extract_text() or ""
                texte_total += texte_page

                # Vérification 2 : présence d'images significatives
                if page.images:
                    images_significatives = [
                        img for img in page.images
                        if img.get("width", 0) > 100 and img.get("height", 0) > 100
                    ]
                    
                    if len(texte_page.strip()) < 20 and images_significatives:
                        self.pdf_complexity = "scanned"
                        return "scanned"
                    elif len(images_significatives) > 2:
                        self.pdf_complexity = "complex"
                        return "complex"

                # Vérification 3 : texte en colonnes
                words = page.extract_words()
                if self._est_en_colonnes(words):
                    self.pdf_complexity = "complex"
                    return "complex"

            # Sécurité finale : si après 500 pages (ou moins), 
            # on a presque aucun texte, c'est forcément un scan.
            if len(texte_total.strip()) < 50:
                self.pdf_complexity = "scanned"
                return "scanned"

        self.pdf_complexity = "simple"
        return "simple"


    def _est_en_colonnes(self, words: list) -> bool:
        """
        Détecte si le texte est disposé en colonnes en cherchant
        un vide significatif au milieu de la page.
        """
        if len(words) < 20:
            return False

        positions_x = sorted([w["x0"] for w in words])
        x_min = min(positions_x)
        x_max = max(positions_x)
        largeur = x_max - x_min

        if largeur < 100:
            return False

        # Diviser la page en 10 tranches verticales
        nb_tranches = 10
        taille_tranche = largeur / nb_tranches
        tranches = [0] * nb_tranches

        for x in positions_x:
            tranche = int((x - x_min) / taille_tranche)
            tranche = min(tranche, nb_tranches - 1)
            tranches[tranche] += 1

        # Chercher un vide significatif au milieu (tranches 3 à 6)
        total_mots = len(positions_x)
        for i in range(3, 7):
            if tranches[i] < total_mots * 0.02:  # moins de 2% des mots dans cette tranche
                return True

        return False

    # ============================================================
    # MÉTHODE 3 : extract_text() — abstraite
    # Surchargée par chaque sous-classe
    # ============================================================

    def extract_text(self) -> str:
        """
        Méthode abstraite — surchargée par chaque sous-classe.
        Lève une exception si appelée directement.
        """
        raise NotImplementedError(
            "extract_text() doit être implémentée par la sous-classe."
        )

    # ============================================================
    # MÉTHODE 4 : clean_text()
    # Nettoie le texte extrait
    # ============================================================

    def clean_text(self, raw_text: str) -> str:
        """
        Nettoie le texte brut extrait :
        - Supprime les espaces multiples
        - Normalise les sauts de ligne
        - Supprime les lignes vides consécutives
        """
        import re

        # Normaliser les retours à la ligne Windows
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

        # Supprimer les espaces multiples sur une même ligne
        text = re.sub(r"[ \t]+", " ", text)

        # Supprimer les lignes vides consécutives (max 2 sauts)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # ============================================================
    # MÉTHODE 5 : extract_metadata()
    # Extrait les métadonnées du fichier
    # ============================================================

    def extract_metadata(self) -> dict:
        """
        Extrait les métadonnées de base du fichier.
        Les métadonnées spécifiques (pages, sections) sont
        enrichies lors du chunking.
        """
        self.metadata = {
            "source": self.file_path.name,
            "format": self.file_type,
            "chemin": str(self.file_path)
        }
        return self.metadata

    # ============================================================
    # MÉTHODE 6 : process()
    # Méthode orchestratrice — appelle tout dans l'ordre
    # ============================================================

    def process(self) -> tuple[list[dict], dict]:
        """
        Orchestre le pipeline complet d'ingestion :
        detect_type → extract_text → clean_text →
        extract_metadata → chunk_text

        Retourne un tuple (chunks, metadata).
        """
        from src.Backend.ingestion.chunking import chunk_text

        # Étape 1 : détecter le type
        self.detect_type()

        # Étape 2 : extraire le texte (via la sous-classe)
        self.raw_text = self.extract_text()

        # Étape 3 : nettoyer le texte
        cleaned = self.clean_text(self.raw_text)

        # Étape 4 : extraire les métadonnées
        self.extract_metadata()

        # Étape 5 : découper en chunks
        self.chunks = chunk_text(
            text=cleaned,
            metadata=self.metadata,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        return self.chunks, self.metadata