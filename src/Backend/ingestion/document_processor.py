# ============================================================
# document_processor.py - Module 2 : Classe principale
# Orchestre l'extraction, le nettoyage et le découpage
# ============================================================

from pathlib import Path
from src.config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLUMN_TOLERANCE_PX,
    COLUMN_WINDOW,
    COLUMN_REPETITIONS
)
import re

SYMBOLES_MATHS = re.compile(
    r'[αβγδεζηθλμνξπρστφψωΩΣΔΓΛΨ∫∂∑∏√∞≤≥≠≈±×÷→←↔∈∉⊂⊃∪∩]'
)

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
        - "simple"  → pdfplumber 
        - "complex" → docling
        - "scanned" → unstructured + OCR 
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
                
                # Vérification 2 : formules mathématiques
                # Méthode 1 : polices mathématiques embarquées (LaTeX, MathJax)
                polices = {obj.get("fontname", "") for obj in page.chars}
                if any("CMMI" in p or "CMSY" in p or "Math" in p or "MSAM" in p
                    for p in polices):
                    self.pdf_complexity = "complex"
                    return "complex"

                # Méthode 2 : symboles mathématiques dans le texte extrait
                if SYMBOLES_MATHS.search(texte_page):
                    self.pdf_complexity = "complex"
                    return "complex"
                
                # Vérification 3 : présence d'images significatives
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

                # Vérification 4 : texte en colonnes
                words = page.extract_words()
                if self._est_en_colonnes(words):
                    self.pdf_complexity = "complex"
                    return "complex"

            # Sécurité finale : si le PDF entier contient moins de 50 caractères
            # de texte extractible, c'est un document scanné sans couche texte.
            if len(texte_total.strip()) < 50:
                self.pdf_complexity = "scanned"
                return "scanned"

        self.pdf_complexity = "simple"
        return "simple"


    def _est_en_colonnes(self, words: list) -> bool:
        """
        Détecte les vraies colonnes en vérifiant que les "colonnes" détectées
        contiennent réellement une majorité significative des mots.
        
        Dans de vraies colonnes :
        - Chaque colonne contient >20% des mots du document
        - Les mots sont groupés près des axes verticaux
        """
        if len(words) < 20:
            return False
    
        lignes = {}
        for w in words:
            y = round(w["top"] / 3) * 3
            x = round(w["x0"] / COLUMN_TOLERANCE_PX) * COLUMN_TOLERANCE_PX
            lignes.setdefault(y, []).append(x)
    
        lignes_triees = [(y, xs) for y, xs in sorted(lignes.items())]
    
        if len(lignes_triees) < 4:
            return False
    
        # Étape 1 : Identifier les axes verticaux répétitifs
        axes_verticaux = set()
        nb_lignes = len(lignes_triees)
        
        for i in range(nb_lignes - COLUMN_WINDOW):
            _, xs_i = lignes_triees[i]
            for x_candidat in xs_i:
                repetitions = sum(
                    1 for j in range(i + 1, min(i + 1 + COLUMN_WINDOW, nb_lignes))
                    if x_candidat in lignes_triees[j][1]
                )
                if repetitions >= COLUMN_REPETITIONS:
                    axes_verticaux.add(x_candidat)
        
        if len(axes_verticaux) < 2:
            return False
        
        # Étape 2 : Filtrer les axes bien espacés
        axes_tries = sorted(axes_verticaux)
        MIN_COLUMN_SPACING = 150
        
        colonnes_candidates = [axes_tries[0]]
        for i in range(1, len(axes_tries)):
            if axes_tries[i] - colonnes_candidates[-1] >= MIN_COLUMN_SPACING:
                colonnes_candidates.append(axes_tries[i])
        
        if len(colonnes_candidates) < 2:
            return False
        
        # ============================================================
        # ÉTAPE 3 : VÉRIFICATION PAR DENSITÉ DE CLUSTER
        # ============================================================
        # Compter combien de mots appartiennent à chaque colonne
        # Un mot "appartient" à une colonne s'il est à ±50px de l'axe
        
        tous_les_mots_x = [x for _, xs in lignes_triees for x in xs]
        nb_mots_total = len(tous_les_mots_x)
        
        CLUSTER_RADIUS = 50  # Rayon autour de l'axe de colonne
        
        mots_par_colonne = []
        for col_x in colonnes_candidates:
            # Compter les mots proches de cet axe
            nb_mots_colonne = sum(
                1 for x in tous_les_mots_x
                if abs(x - col_x) <= CLUSTER_RADIUS
            )
            pourcentage = (nb_mots_colonne / nb_mots_total) * 100
            mots_par_colonne.append((col_x, nb_mots_colonne, pourcentage))
        
        # Pour avoir de vraies colonnes, chaque colonne doit contenir
        # au moins 20% des mots du document
        MIN_POURCENTAGE_PAR_COLONNE = 20
        
        colonnes_significatives = [
            col for col, nb, pct in mots_par_colonne
            if pct >= MIN_POURCENTAGE_PAR_COLONNE
        ]
        
        # Si moins de 2 colonnes contiennent au moins 20% des mots chacune
        # → c'est probablement du texte justifié, pas des colonnes
        if len(colonnes_significatives) < 2:
            return False
        
        # Étape 4 : Vérifier la présence simultanée (au moins 3 lignes)
        lignes_avec_multi_colonnes = 0
        
        for y, xs_ligne in lignes_triees:
            colonnes_presentes = sum(
                1 for col_x in colonnes_significatives
                if col_x in xs_ligne
            )
            
            if colonnes_presentes >= 2:
                lignes_avec_multi_colonnes += 1
        
        MIN_LIGNES_MULTI_COLONNES = 3
        
        return lignes_avec_multi_colonnes >= MIN_LIGNES_MULTI_COLONNES

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
        Extrait les métadonnées embarquées dans le document 
        (auteur, titre, nb pages...).
        Les métadonnées spécifiques au contenu (pages, sections) sont
        enrichies plus tard lors du chunking.
        """
        self.metadata = {
            "source": self.file_path.name,
            "format": self.file_type,
            "chemin": str(self.file_path),
        }

        # Métadonnées embarquées — selon le format
        try:
            if self.file_type == "pdf":
                self._extract_metadata_pdf()
            elif self.file_type == "pptx":
                self._extract_metadata_pptx()
            elif self.file_type == "docx":
                self._extract_metadata_docx()
        except Exception:
            # Les métadonnées embarquées sont optionnelles
            # On ne bloque jamais l'ingestion si elles sont absentes ou corrompues
            pass

        return self.metadata


    def _extract_metadata_pdf(self) -> None:
        import pdfplumber
        with pdfplumber.open(self.file_path) as pdf:
            meta = pdf.metadata or {}
            self.metadata.update({
                "titre":    meta.get("Title", ""),
                "auteur":   meta.get("Author", ""),
                "sujet":    meta.get("Subject", ""),
                "nb_pages": len(pdf.pages),
            })


    def _extract_metadata_pptx(self) -> None:
        from pptx import Presentation
        prs = Presentation(self.file_path)
        props = prs.core_properties
        self.metadata.update({
            "titre":     props.title or "",
            "auteur":    props.author or "",
            "sujet":     props.subject or "",
            "nb_slides": len(prs.slides),
        })


    def _extract_metadata_docx(self) -> None:
        from docx import Document
        doc = Document(self.file_path)
        props = doc.core_properties
        self.metadata.update({
            "titre":          props.title or "",
            "auteur":         props.author or "",
            "sujet":          props.subject or "",
            "nb_paragraphes": len(doc.paragraphs),
        })
        
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