from src.Backend.database.db_session import get_db
from src.Backend.rag.rag_engine import RAGEngine

# 1. Récupérer la session de base de données
# get_db est un générateur, on utilise next() pour avoir la session
db = next(get_db())

try:
    # 2. Initialiser le moteur RAG
    # On utilise l'utilisateur 1 (enseignant ou étudiant)
    rag = RAGEngine(db=db, utilisateur_id=1)

    # 3. Poser une question

    question = "qui est léo?"
    module_id = 1

    print(f"Question : {question}\nRéponse : ", end="")

    # 4. Lancer la génération en flux (streaming)
    for token in rag.run(question=question, module_id=module_id):
        print(token, end="", flush=True)

except Exception as e:
    print(f"\n❌ Erreur pendant le RAG : {e}")
finally:
    db.close()