# settings.py
# Paramètres globaux et configurables de l'application AP-UP

# ── Serveur d'inférence ──────────────────────────────────────────────
#LLM_BASE_URL = "http://172.27.72.55:11434/v1"  # Pléiade (université)
LLM_BASE_URL = "http://localhost:11434/v1"   # Ollama (développement local)
LLM_MODEL = "tinyllama:latest"                          # modèle à utiliser
LLM_TEMPERATURE = 0.1                           # fidélité au cours (0=strict, 1=créatif)
LLM_API_KEY = "ollama"                          # ignoré par Pléiade/Ollama mais requis

# ── Base de données ──────────────────────────────────────────────────
DATABASE_URL = "postgresql://user:password@localhost:5432/apup"

# ── Chunking ─────────────────────────────────────────────────────────
CHUNK_SIZE = 512        # taille cible d'un chunk en tokens
CHUNK_OVERLAP = 50      # chevauchement entre deux chunks en tokens

# ── RAG ──────────────────────────────────────────────────────────────
TOP_K = 5               # nombre de chunks pertinents à récupérer

# ── Embedding ────────────────────────────────────────────────────────
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"  # modèle sentence-transformers
EMBEDDING_DIMENSION = 768                            # dimension des vecteurs

# ── Filtrage ─────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD_IN = 0.35   # seuil de pertinence pour la question
SIMILARITY_THRESHOLD_OUT = 0.50  # seuil d'ancrage pour la réponse
SIMILARITY_THRESHOLD_BLOCK = 0.30  # seuil de blocage immédiat
SLM_CONFIDENCE_THRESHOLD = 0.6   # seuil de confiance du SLM évaluateur

# ── Stockage des fichiers ─────────────────────────────────────────────
DATA_DIR = "data/"  # répertoire des documents uploadés