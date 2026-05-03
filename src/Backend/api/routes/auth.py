import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.Backend.api.dependencies import get_database_session
from src.Backend.api.schemas import LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def verify_password(password: str, stored_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        stored_password.encode("utf-8"),
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, db: Session = Depends(get_database_session)):
    email = payload.email.strip().lower()

    try:
        from src.Backend.database.models import Utilisateur

        user = db.query(Utilisateur).filter(Utilisateur.email == email).first()

        if user and verify_password(payload.password, user.mot_de_passe):
            return {
                "id": user.id,
                "nom": user.nom,
                "prenom": user.prenom,
                "email": user.email,
                "role": user.role,
            }
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees indisponible. Verifiez DATABASE_URL.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou mot de passe incorrect.",
    )
