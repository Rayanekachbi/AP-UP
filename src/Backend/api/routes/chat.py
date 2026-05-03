from fastapi import APIRouter, Depends, HTTPException, Query, status
from openai import APIConnectionError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.Backend.api.dependencies import get_database_session
from src.Backend.api.schemas import (
    ChatHistoryEntryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
)


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history", response_model=list[ChatHistoryEntryResponse])
def get_history(
    utilisateur_id: int = Query(...),
    module_id: int = Query(...),
    db: Session = Depends(get_database_session),
):
    try:
        from src.Backend.database.models import Historique

        historique = (
            db.query(Historique)
            .filter_by(
                utilisateur_id=utilisateur_id,
                module_id=module_id,
            )
            .order_by(Historique.date_heure.asc(), Historique.id.asc())
            .all()
        )

        return [
            {
                "id": entry.id,
                "utilisateur_id": entry.utilisateur_id,
                "module_id": entry.module_id,
                "question": entry.question,
                "reponse": entry.reponse,
                "date_heure": entry.date_heure.isoformat(),
            }
            for entry in historique
        ]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc


@router.delete("/history")
def clear_history(
    utilisateur_id: int = Query(...),
    db: Session = Depends(get_database_session),
):
    try:
        from src.Backend.database.models import Historique

        db.query(Historique).filter_by(utilisateur_id=utilisateur_id).delete()
        db.commit()

        return {"message": "Historique supprime."}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc


@router.post("/message", response_model=ChatMessageResponse)
def send_message(payload: ChatMessageRequest, db: Session = Depends(get_database_session)):
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La question ne peut pas etre vide.",
        )

    try:
        from src.Backend.database.models import Historique, Module
        from src.Backend.database.vector_store import get_chunks_par_module
        from src.Backend.filtrage.filtering import FilteringPipeline
        from src.Backend.rag.rag_engine import RAGEngine

        module = db.query(Module).filter(Module.id == payload.module_id).first()
        if module is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module introuvable.",
            )

        chunk_vectors = get_chunks_par_module(db, payload.module_id)
        if not chunk_vectors:
            raise ValueError(
                f"Aucun chunk trouvé pour le module {payload.module_id}. "
                "Vérifiez que des documents ont bien été indexés."
            )

        filtering = FilteringPipeline()
        input_result = filtering.validate_input(question, chunk_vectors)
        if not input_result.is_valid:
            return {
                "id": 0,
                "utilisateur_id": payload.utilisateur_id,
                "module_id": payload.module_id,
                "question": question,
                "reponse": input_result.reason,
                "chunks_sources": None,
            }

        engine = RAGEngine(
            db=db,
            utilisateur_id=payload.utilisateur_id,
        )
        reponse = "".join(
            engine.run(
                question=question,
                module_id=payload.module_id,
            )
        )

        output_result = filtering.validate_output(reponse, engine._derniers_chunks)
        if not output_result.is_valid:
            reponse = output_result.reason
            engine._derniere_reponse = reponse

        engine.sauvegarder()
        historique = (
            db.query(Historique)
            .filter_by(
                utilisateur_id=payload.utilisateur_id,
                module_id=payload.module_id,
                question=question,
                reponse=reponse,
            )
            .order_by(Historique.id.desc())
            .first()
        )
        if historique is None:
            raise ValueError("Historique introuvable apres sauvegarde.")

        return {
            "id": historique.id,
            "utilisateur_id": historique.utilisateur_id,
            "module_id": historique.module_id,
            "question": question,
            "reponse": reponse,
            "chunks_sources": historique.chunks_sources,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc
    except APIConnectionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Le serveur LLM ne repond pas. Lance Ollama ou configure "
                "LLM_BASE_URL dans src/config/settings.py."
            ),
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CHAT ERROR: {exc}",
        ) from exc
