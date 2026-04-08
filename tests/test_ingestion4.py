from src.Backend.ingestion.document_processor import DocumentProcessor
from src.Backend.ingestion.pdf_simple import PDFSimpleProcessor
from src.Backend.ingestion.pdf_complex import PDFComplexProcessor
from src.Backend.ingestion.other_formats import UnstructuredProcessor
from src.Backend.rag.retriever import modele_embedding
from src.Backend.database.db_session import SessionLocal
from src.Backend.database.vector_store import inserer_chunk
from src.Backend.database.models import Utilisateur, Module, Document


def get_processor(file_path):
    """
    Analyse le fichier et retourne l'instance du processeur approprié.
    """
    from src.Backend.ingestion.document_processor import DocumentProcessor
    detector = DocumentProcessor(file_path)
    type_detecte = detector.detect_type()
    print(f"🔍 Type détecté pour '{file_path}' : {type_detecte}")

    if type_detecte == "simple":
        return PDFSimpleProcessor(file_path)
    elif type_detecte == "complex":
        return PDFComplexProcessor(file_path)
    elif type_detecte == "scanned":
        return UnstructuredProcessor(file_path)
    else:
        return UnstructuredProcessor(file_path)


def get_or_create_enseignant(db, email: str, nom: str, prenom: str) -> Utilisateur:
    """
    Récupère l'enseignant par email ou le crée s'il n'existe pas.
    L'ID est géré automatiquement par PostgreSQL.
    """
    enseignant = db.query(Utilisateur).filter_by(email=email).first()
    if not enseignant:
        enseignant = Utilisateur(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe="password123",
            role="enseignant"
        )
        db.add(enseignant)
        db.flush()
        print(f"✅ Enseignant créé avec l'ID : {enseignant.id}")
    else:
        print(f"ℹ️ Enseignant déjà existant : ID={enseignant.id}")
    return enseignant


def get_or_create_module(db, nom: str, enseignant_id: int) -> Module:
    """
    Récupère le module par nom et enseignant ou le crée s'il n'existe pas.
    L'ID est géré automatiquement par PostgreSQL.
    """
    module = db.query(Module).filter_by(
        nom=nom,
        enseignant_id=enseignant_id
    ).first()
    if not module:
        module = Module(
            nom=nom,
            description="Module de test",
            enseignant_id=enseignant_id
        )
        db.add(module)
        db.flush()
        print(f"✅ Module créé avec l'ID : {module.id}")
    else:
        print(f"ℹ️ Module déjà existant : ID={module.id}")
    return module


def get_or_create_document(db, titre: str, chemin: str, module_id: int, enseignant_id: int) -> tuple[Document, bool]:
    """
    Récupère le document par chemin ou le crée s'il n'existe pas.
    Retourne un tuple (document, déjà_existant).
    L'ID est géré automatiquement par PostgreSQL.
    """
    document = db.query(Document).filter_by(chemin_fichier=chemin).first()
    if not document:
        document = Document(
            titre=titre,
            module_id=module_id,
            enseignant_id=enseignant_id,
            chemin_fichier=chemin,
            format="pdf",
            statut="indexé"
        )
        db.add(document)
        db.flush()
        print(f"✅ Document créé avec l'ID : {document.id}")
        return document, False
    else:
        print(f"ℹ️ Document déjà existant : ID={document.id} — les chunks ne seront pas réinsérés.")
        return document, True


def tester_ingestion(file_path: str):
    """
    Pipeline complet de test : ingestion → vectorisation → stockage en BDD.
    Gère automatiquement les doublons sans erreur.
    """
    print(f"\n{'='*50}")
    print(f"🚀 Traitement de : {file_path}")
    print(f"{'='*50}")

    # ÉTAPE 1 : ingestion et chunking
    processor = get_processor(file_path)
    print(f"⚙️ Processeur choisi : {type(processor).__name__}")

    chunks, metadata = processor.process()
    print(f"📄 {len(chunks)} chunks générés.")

    # ÉTAPE 2 : connexion à la base
    db = SessionLocal()

    try:
        # ÉTAPE 3 : récupérer ou créer l'enseignant
        enseignant = get_or_create_enseignant(
            db=db,
            email="alice.martin@univ.fr",
            nom="Martin",
            prenom="Alice"
        )

        # ÉTAPE 4 : récupérer ou créer le module
        module = get_or_create_module(
            db=db,
            nom="Module de Test",
            enseignant_id=enseignant.id
        )

        # ÉTAPE 5 : récupérer ou créer le document
        document, deja_existant = get_or_create_document(
            db=db,
            titre=metadata["source"],
            chemin=file_path,
            module_id=module.id,
            enseignant_id=enseignant.id
        )

        # Valider les créations
        db.commit()

        # ÉTAPE 6 : insérer les chunks uniquement si le document est nouveau
        if deja_existant:
            print(f"⏭️ Chunks déjà en base pour ce document — insertion ignorée.")
        else:
            print(f"📥 Insertion de {len(chunks)} chunks...")
            for chunk_data in chunks:
                vecteur = modele_embedding.encode(chunk_data["texte"]).tolist()
                inserer_chunk(
                    db=db,
                    contenu=chunk_data["texte"],
                    embedding=vecteur,
                    document_id=document.id,
                    chunk_index=chunk_data["chunk_index"],
                    page=chunk_data.get("page"),
                    section=chunk_data.get("section")
                )
            print(f"✅ {len(chunks)} chunks insérés en base.")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur : {e}")
        raise
    finally:
        db.close()


# ============================================================
# ZONE DE TEST
# ============================================================

fichiers_a_tester = [
    "tests/Histoire.pdf",
    "tests/Cahier_de_recette_L3S.pdf"
]

for path in fichiers_a_tester:
    tester_ingestion(path)