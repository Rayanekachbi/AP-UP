from src.Backend.ingestion.pdf_simple import PDFSimpleProcessor
from src.Backend.ingestion.pdf_complex import PDFComplexProcessor
from src.Backend.ingestion.other_formats import UnstructuredProcessor
from src.Backend.rag.retriever import modele_embedding # Pour générer les vecteurs
from src.Backend.database.db_session import SessionLocal
from src.Backend.database.vector_store import inserer_chunk
from src.Backend.database.models import Document
from src.Backend.database.models import Utilisateur, Module, Document

def get_processor(file_path):
    # On crée un processeur temporaire juste pour détecter le type
    # (Ou on peut simplement regarder l'extension ici)
    if file_path.endswith(".pdf"):
        # Logique simplifiée pour le test :
        return PDFSimpleProcessor(file_path)
    else:
        return UnstructuredProcessor(file_path)

# Ton code de test devient :
path = "tests/Histoire.pdf"
processor = get_processor(path) # L'aiguilleur choisit la bonne sous-classe
chunks, metadata = processor.process()

print(f"Nombre de chunks : {len(chunks)}")
print(f"Premier chunk : {chunks[0]}")
print(f"Métadonnées : {metadata}")

# Connexion à la base
db = SessionLocal()

try:
    # ÉTAPE A : Créer l'enseignant s'il n'existe pas
    enseignant = db.query(Utilisateur).filter_by(id=1).first()
    if not enseignant:
        enseignant = Utilisateur(
            id=1,
            nom="Martin",
            prenom="Alice",
            email="alice.martin@univ.fr",
            mot_de_passe="password123",
            role="enseignant"
        )
        db.add(enseignant)
        db.flush() # Prépare l'insertion sans valider tout de suite

    # ÉTAPE B : Créer le module s'il n'existe pas
    module = db.query(Module).filter_by(id=1).first()
    if not module:
        module = Module(
            id=1,
            nom="Module de Test Histoire",
            description="Test d'ingestion",
            enseignant_id=1
        )
        db.add(module)
        db.flush()

    # ÉTAPE C : Créer le document s'il n'existe pas
    nouveau_doc = db.query(Document).filter_by(id=1).first()
    if not nouveau_doc:
        nouveau_doc = Document(
            id=1, 
            titre="Histoire.pdf", 
            module_id=1,
            enseignant_id=1, 
            chemin_fichier="tests/Histoire.pdf",
            format="pdf",
            statut="indexé"
        )
        db.add(nouveau_doc)
    
    # On valide la création des parents
    db.commit()

    # ÉTAPE D : Insertion des chunks
    print(f"Insertion de {len(chunks)} chunks dans la base...")
    for i, chunk_data in enumerate(chunks):
        vecteur = modele_embedding.encode(chunk_data['texte']).tolist()
        
        inserer_chunk(
            db=db,
            contenu=chunk_data['texte'],
            embedding=vecteur,
            document_id=1,
            chunk_index=i,
            page=chunk_data.get('page')
        )
    print("✅ Tout est en base ! Tu peux vérifier pgAdmin.")

except Exception as e:
    db.rollback() # Annule tout en cas d'erreur
    print(f"❌ Erreur : {e}")
finally:
    db.close()