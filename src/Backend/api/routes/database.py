from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.Backend.api.dependencies import get_database_session
from src.Backend.api.schemas import (
    DatabaseMessageResponse,
    ModulePromptRequest,
    ModulePromptResponse,
    ModuleResponse,
    PasswordMigrationResponse,
)


router = APIRouter(prefix="/database", tags=["database"])


@router.post("/init", response_model=DatabaseMessageResponse)
def init_database():
    """
    Cree les tables PostgreSQL declarees dans src/backend/database/models.py.
    """
    try:
        from src.Backend.database.db_session import init_db

        init_db()
        return {"message": "Base de donnees initialisee."}
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependances database manquantes. Lance pip install -r requirements.txt.",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc


@router.put("/modules/{module_id}/prompt", response_model=ModulePromptResponse)
def update_module_prompt(
    module_id: int,
    payload: ModulePromptRequest,
    db: Session = Depends(get_database_session),
):
    try:
        from src.Backend.database.models import Module

        module = db.query(Module).filter(Module.id == module_id).first()
        if module is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module introuvable.",
            )

        module.system_prompt = payload.system_prompt.strip() or None
        db.commit()
        db.refresh(module)

        return {
            "id": module.id,
            "nom": module.nom,
            "system_prompt": module.system_prompt,
        }
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc
        
@router.get("/modules", response_model=list[ModuleResponse])
def list_modules(db: Session = Depends(get_database_session)):
    """
    l'API lit les modules depuis la table SQLAlchemy `modules`.
    """
    try:
        from src.Backend.database.models import Module

        modules = db.query(Module).order_by(Module.id).all()
        return [
            {
                "id": module.id,
                "nom": module.nom,
                "description": module.description,
                "system_prompt": module.system_prompt,
            }
            for module in modules
        ]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc
