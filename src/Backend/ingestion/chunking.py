# ============================================================
# chunking.py - Module 2 : Algorithme de découpage
# Stratégie hybride : structure en priorité, taille fixe en fallback
# ============================================================

import re
import tiktoken
from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP


# ============================================================
# ENCODEUR TIKTOKEN
# Chargé une seule fois au démarrage du module
# ============================================================

encodeur = tiktoken.get_encoding("cl100k_base")


def compter_tokens(texte: str) -> int:
    """Retourne le nombre de tokens d'un texte."""
    return len(encodeur.encode(texte))


# ============================================================
# FONCTION PRINCIPALE : chunk_text()
# ============================================================

def chunk_text(
    text: str,
    metadata: dict,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> list[dict]:
    """
    Découpe un texte en fragments homogènes selon une stratégie hybride :
    1. Découpage structurel (titres Markdown, paragraphes)
    2. Contrôle de taille (redécoupage si > chunk_size tokens)
    3. Application du chevauchement
    4. Enrichissement des métadonnées

    Paramètres :
    - text         : texte nettoyé à découper
    - metadata     : métadonnées du document source
    - chunk_size   : taille maximale d'un chunk en tokens
    - chunk_overlap: chevauchement entre deux chunks en tokens

    Retourne une liste de dictionnaires contenant le texte
    et les métadonnées de chaque chunk.
    """

    # Étape 1 : découpage structurel
    segments = _decouper_par_structure(text)

    # Étape 2 : contrôle de taille
    chunks_texte = []
    for segment in segments:
        if compter_tokens(segment) <= chunk_size:
            chunks_texte.append(segment)
        else:
            sous_fragments = _redecouper(segment, chunk_size)
            chunks_texte.extend(sous_fragments)

    # Étape 3 : application du chevauchement
    chunks_avec_overlap = _appliquer_chevauchement(chunks_texte, chunk_overlap)

    # Étape 4 : enrichissement des métadonnées
    chunks_finaux = _enrichir_metadonnees(chunks_avec_overlap, metadata, text)

    return chunks_finaux


# ============================================================
# FONCTION 1 : _decouper_par_structure()
# Découpe selon les séparateurs structurels par ordre de priorité
# ============================================================

def _decouper_par_structure(text: str) -> list[str]:
    """
    Découpe le texte selon les séparateurs structurels :
    Priorité 1 : titres Markdown (## ou #)
    Priorité 2 : doubles sauts de ligne (paragraphes)
    Priorité 3 : sauts de ligne simples
    """

    # Priorité 1 : découper par titres Markdown
    if re.search(r"\n#{1,2} ", text):
        segments = re.split(r"(?=\n#{1,2} )", text)
        segments = [s.strip() for s in segments if s.strip()]
        return segments

    # Priorité 2 : découper par paragraphes
    segments = text.split("\n\n")
    segments = [s.strip() for s in segments if s.strip()]

    if segments:
        return segments

    # Priorité 3 : découper par sauts de ligne simples
    segments = text.split("\n")
    return [s.strip() for s in segments if s.strip()]


# ============================================================
# FONCTION 2 : _redecouper()
# Redécoupe récursivement un segment trop long
# ============================================================

def _redecouper(texte: str, chunk_size: int) -> list[str]:
    """
    Redécoupe un segment trop long en tentant les séparateurs
    dans l'ordre suivant : \n → . → ' '
    """

    separateurs = ["\n", ". ", " "]

    for separateur in separateurs:
        parties = texte.split(separateur)
        parties = [p.strip() for p in parties if p.strip()]

        if len(parties) <= 1:
            continue

        # Regrouper les parties en chunks de taille acceptable
        chunks = []
        chunk_courant = ""

        for partie in parties:
            candidat = chunk_courant + separateur + partie if chunk_courant else partie

            if compter_tokens(candidat) <= chunk_size:
                chunk_courant = candidat
            else:
                if chunk_courant:
                    chunks.append(chunk_courant)
                chunk_courant = partie

        if chunk_courant:
            chunks.append(chunk_courant)

        if chunks:
            return chunks

    # Dernier recours : tronquer brutalement par nombre de tokens
    return _tronquer_par_tokens(texte, chunk_size)


def _tronquer_par_tokens(texte: str, chunk_size: int) -> list[str]:
    """
    Dernier recours — tronque le texte directement par tokens.
    """
    tokens = encodeur.encode(texte)
    chunks = []

    for i in range(0, len(tokens), chunk_size):
        fragment_tokens = tokens[i:i + chunk_size]
        fragment_texte = encodeur.decode(fragment_tokens)
        chunks.append(fragment_texte)

    return chunks


# ============================================================
# FONCTION 3 : _appliquer_chevauchement()
# Ajoute les derniers tokens du chunk précédent au début du suivant
# ============================================================

def _appliquer_chevauchement(chunks: list[str], chunk_overlap: int) -> list[str]:
    """
    Applique le chevauchement entre chunks consécutifs.
    Les chunk_overlap derniers tokens du chunk précédent
    sont ajoutés au début du chunk suivant.
    """
    if len(chunks) <= 1 or chunk_overlap == 0:
        return chunks

    chunks_avec_overlap = [chunks[0]]

    for i in range(1, len(chunks)):
        # Récupérer les derniers tokens du chunk précédent
        tokens_precedent = encodeur.encode(chunks[i - 1])
        overlap_tokens = tokens_precedent[-chunk_overlap:]
        overlap_texte = encodeur.decode(overlap_tokens)

        # Ajouter au début du chunk courant
        chunks_avec_overlap.append(overlap_texte + " " + chunks[i])

    return chunks_avec_overlap


# ============================================================
# FONCTION 4 : _enrichir_metadonnees()
# Associe les métadonnées à chaque chunk
# ============================================================

def _enrichir_metadonnees(
    chunks: list[str],
    metadata: dict,
    texte_original: str
) -> list[dict]:
    """
    Associe les métadonnées à chaque chunk :
    - source      : nom du fichier
    - page        : numéro de page détecté
    - section     : titre de section Markdown détecté
    - chunk_index : numéro d'ordre dans le document
    """
    chunks_finaux = []

    for index, chunk in enumerate(chunks):

        # Détecter le numéro de page depuis le préfixe [PAGE X]
        page = _extraire_page(chunk, texte_original)

        # Détecter le titre de section Markdown
        section = _extraire_section(chunk)

        chunks_finaux.append({
            "texte": chunk,
            "source": metadata.get("source", ""),
            "page": page,
            "section": section,
            "chunk_index": index
        })

    return chunks_finaux


def _extraire_page(chunk: str, texte_original: str) -> int | None:
    """
    Extrait le numéro de page depuis le préfixe [PAGE X]
    ajouté par PDFSimpleProcessor.
    """
    match = re.search(r"\[PAGE (\d+)\]", chunk)
    if match:
        return int(match.group(1))
    return None


def _extraire_section(chunk: str) -> str | None:
    """
    Extrait le titre de section Markdown (# ou ##)
    présent dans le chunk — disponible uniquement
    pour les PDF complexes traités par marker-pdf.
    """
    match = re.search(r"^#{1,2} (.+)$", chunk, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None