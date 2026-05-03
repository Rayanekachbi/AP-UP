from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.Backend.api.dependencies import get_database_session
from src.Backend.api.schemas import (
    DatabaseMessageResponse,
    DocumentResponse,
    DocumentUploadResponse,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
UPLOAD_DIR = Path("data/")

@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_database_session)):
    try:
        from src.Backend.database.models import Document

        documents = db.query(Document).order_by(Document.id.desc()).all()
        return [
            {
                "id": document.id,
                "title": document.titre,
                "course": document.module.nom,
                "status": document.statut,
            }
            for document in documents
        ]
    except SQLAlchemyError as exc:
        raise _database_error() from exc


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    module_id: int = Form(...),
    enseignant_id: int = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_database_session),
):
    original_filename = Path(file.filename or "document").name
    file_path = UPLOAD_DIR / original_filename

    try:
        from src.Backend.database.models import Document
        from src.Backend.database.vector_store import inserer_chunk
        from src.Backend.rag.retriever import modele_embedding

        content = await file.read()
        if not content:
            raise ValueError("Le fichier envoye est vide.")

        module, enseignant = _check_owner(db, module_id, enseignant_id)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        chunks, metadata = _process_file(file_path)
        if not chunks:
            raise ValueError("Aucun chunk n'a ete genere depuis ce document.")

        document_title = title.strip() if title and title.strip() else original_filename

        document = Document(
            titre=document_title,
            module_id=module.id,
            enseignant_id=enseignant.id,
            chemin_fichier=str(file_path),
            format=metadata.get("format", file_path.suffix.lower().strip(".")),
            statut="indexe",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        chunks_created = 0
        for index, chunk in enumerate(chunks):
            text = chunk.get("texte") or chunk.get("text") or ""
            inserer_chunk(
                db=db,
                contenu=text,
                embedding=modele_embedding.encode(text).tolist(),
                document_id=document.id,
                chunk_index=chunk.get("chunk_index", index),
                page=chunk.get("page"),
                section=chunk.get("section"),
            )
            chunks_created += 1

        return {
            "message": "Document importe et indexe.",
            "document_id": document.id,
            "title": document.titre,
            "module_id": document.module_id,
            "chunks_created": chunks_created,
            "status": document.statut,
        }
    except ValueError as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise _database_error() from exc


@router.delete("/documents/{document_id}", response_model=DatabaseMessageResponse)
def delete_document(document_id: int, db: Session = Depends(get_database_session)):
    try:
        from src.Backend.database.models import Chunk, Document

        document = db.query(Document).filter(Document.id == document_id).first()
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document introuvable.",
            )

        file_path = Path(document.chemin_fichier)
        db.query(Chunk).filter(Chunk.document_id == document.id).delete()
        db.delete(document)
        db.commit()
        file_path.unlink(missing_ok=True)

        return {"message": "Document supprime."}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise _database_error() from exc


def _process_file(file_path: Path) -> tuple[list[dict], dict]:
    if file_path.suffix.lower() == ".txt":
        from src.Backend.ingestion.chunking import chunk_text

        text = file_path.read_text(encoding="utf-8")
        metadata = {"source": file_path.name, "format": "txt", "chemin": str(file_path)}
        return chunk_text(text=text, metadata=metadata), metadata

    processor = get_processor(file_path)
    return processor.process()


def get_processor(file_path: str | Path):
    """
    Analyse le fichier et retourne le processeur adapte(complexe,simple,...).

    Permet d'utiliser la meme logique que dans les tests :
    processor = get_processor(path)
    chunks, metadata = processor.process()
    """
    file_path = Path(file_path)

    from src.Backend.ingestion.document_processor import DocumentProcessor

    detected_type = DocumentProcessor(str(file_path)).detect_type()

    if detected_type == "simple":
        from src.Backend.ingestion.pdf_simple import PDFSimpleProcessor

        return PDFSimpleProcessor(str(file_path))

    if detected_type == "complex":
        from src.Backend.ingestion.pdf_complex import PDFComplexProcessor

        return PDFComplexProcessor(str(file_path))

    if detected_type in {"scanned", "unstructured"}:
        from src.Backend.ingestion.other_formats import UnstructuredProcessor

        return UnstructuredProcessor(str(file_path))

    if detected_type == "audio_video":
        from src.Backend.ingestion.other_formats import AudioVideoProcessor

        return AudioVideoProcessor(str(file_path))

    raise ValueError(f"Format non supporte : {file_path.suffix.lower().lstrip('.')}")


def _check_owner(db: Session, module_id: int, enseignant_id: int):
    from src.Backend.database.models import Module, Utilisateur

    module = db.query(Module).filter_by(id=module_id).first()
    enseignant = db.query(Utilisateur).filter_by(id=enseignant_id).first()

    if module is None:
        raise ValueError("Module introuvable.")
    if enseignant is None:
        raise ValueError("Enseignant introuvable.")
    if enseignant.role != "enseignant":
        raise ValueError("Seul un enseignant peut importer un document.")
    if module.enseignant_id != enseignant.id:
        raise ValueError("Cet enseignant n'est pas associe au module choisi.")

    return module, enseignant


def _database_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
    )
