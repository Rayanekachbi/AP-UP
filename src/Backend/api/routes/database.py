from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.Backend.api.dependencies import get_database_session
from src.Backend.api.schemas import (
    DatabaseMessageResponse,
    ModuleResponse,
    PasswordMigrationResponse,
)
from src.Backend.api.security import hash_password, password_needs_hash


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
        
@router.get("/modules", response_model=list[ModuleResponse])
def list_modules(db: Session = Depends(get_database_session)):
    """
    Exemple database simple :
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
            }
            for module in modules
        ]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc
