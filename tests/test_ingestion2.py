from src.Backend.ingestion.document_processor import DocumentProcessor
from src.Backend.ingestion.pdf_simple import PDFSimpleProcessor
from src.Backend.ingestion.pdf_complex import PDFComplexProcessor
from src.Backend.ingestion.other_formats import UnstructuredProcessor

def get_processor(file_path):
    """
    Analyse le fichier et retourne l'instance du processeur approprié.
    Utilise la logique interne de détection de complexité.
    """
    # 1. On utilise la classe de base pour détecter le type réel
    detector = DocumentProcessor(file_path)
    type_detecte = detector.detect_type() # Analyse le PDF (tableaux, images, colonnes)
    
    print(f"🔍 Type détecté pour '{file_path}' : {type_detecte}")

    # 2. Aiguillage vers la bonne sous-classe
    if type_detecte == "simple":
        return PDFSimpleProcessor(file_path)
    elif type_detecte == "complex":
        return PDFComplexProcessor(file_path)
    elif type_detecte == "scanned":
        # Pour les scans (comme Threads.pdf), on utilise l'OCR d'Unstructured
        return UnstructuredProcessor(file_path)
    else:
        # Pour docx, pptx, html, etc.
        return UnstructuredProcessor(file_path)

# --- ZONE DE TEST ---
# Testez avec les deux fichiers pour voir la différence de détection
fichiers_a_tester = ["tests/Histoire.pdf", "tests/Cahier_de_recette_L3S.pdf"]

for path in fichiers_a_tester:
    print(f"\n--- Test de traitement : {path} ---")
    try:
        processor = get_processor(path)
        print(f"⚙️ Processeur choisi : {type(processor).__name__}")
        
        chunks, metadata = processor.process()
        print(f"✅ Succès : {len(chunks)} chunks générés.")
        
    except Exception as e:
        print(f"❌ Échec pour {path} : {e}")