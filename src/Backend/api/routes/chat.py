from fastapi import APIRouter, Depends, HTTPException, status
from openai import APIConnectionError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.Backend.api.dependencies import get_database_session
from src.Backend.api.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
)


router = APIRouter(prefix="/chat", tags=["chat"])


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
        from src.Backend.rag.rag_engine import RAGEngine

        module = db.query(Module).filter(Module.id == payload.module_id).first()
        if module is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module introuvable.",
            )

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
            detail=(
                "Le moteur RAG n'est pas disponible. "
                "Verifiez les chunks indexes, le modele d'embedding et le serveur LLM."
            ),
        ) from exc
