# settings.py
# Paramètres globaux et configurables de l'application AP-UP
import os
# ── Serveur d'inférence ──────────────────────────────────────────────
#LLM_BASE_URL = "http://172.27.72.55:11434/v1"  # Pléiade (université)
LLM_BASE_URL = "http://host.docker.internal:11434/v1"   # Ollama (développement local)
LLM_MODEL = "phi4-mini:latest"                          # modèle à utiliser
LLM_TEMPERATURE = 0.1                           # fidélité au cours (0=strict, 1=créatif)
LLM_API_KEY = "ollama"                          # ignoré par Pléiade/Ollama mais requis

# ── Base de données ──────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/apup")
# ── Chunking ─────────────────────────────────────────────────────────
CHUNK_SIZE = 512        # taille cible d'un chunk en tokens
CHUNK_OVERLAP = 50      # chevauchement entre deux chunks en tokens

# ── RAG ──────────────────────────────────────────────────────────────
TOP_K = 5               # nombre de chunks pertinents à récupérer

# ── Embedding ────────────────────────────────────────────────────────
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"  # modèle sentence-transformers
EMBEDDING_DIMENSION = 768                            # dimension des vecteurs

# ── Filtrage ─────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD_IN = 0.35   # seuil de pertinence pour la question
SIMILARITY_THRESHOLD_OUT = 0.50  # seuil d'ancrage pour la réponse
SIMILARITY_THRESHOLD_BLOCK = 0.30  # seuil de blocage immédiat
SLM_CONFIDENCE_THRESHOLD = 0.6   # seuil de confiance du SLM évaluateur

# ── Stockage des fichiers ─────────────────────────────────────────────
DATA_DIR = "data"  # répertoire des documents uploadés

# se trouve dans les settings de mounir
SIMILARITY_THRESHOLD_OUT_HIGH = 0.50
SIMILARITY_THRESHOLD_OUT_LOW = 0.30
SLM_MODEL = "mistral"
OLLAMA_BASE_URL = "http://host.docker.internal:11434/v1"
MESSAGE_QUESTION_BLOQUEE = "Votre question ne semble pas liée au contenu du module sélectionné. Veuillez reformuler ou choisir un autre module."
MESSAGE_REPONSE_BLOQUEE = "La réponse générée ne peut pas être fournie car elle ne semble pas ancrée dans le contenu du cours."

COLUMN_TOLERANCE_PX = 5   # tolérance d'arrondi pour les coordonnées X
COLUMN_WINDOW = 5          # nombre de lignes suivantes à inspecter
COLUMN_REPETITIONS = 4     # répétitions min pour valider un axe vertical

# ── Frontend ─────────────────────────────────────────────────────────
FRONTEND_URL = "http://localhost:5173"  # Port par défaut de Vite (React)

NB_ECHANGES_HISTORIQUE = 1
