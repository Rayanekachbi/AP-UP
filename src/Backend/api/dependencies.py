from fastapi import HTTPException, status


def get_database_session():
    try:
        from src.Backend.database.db_session import get_db
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Dependances database manquantes. "
                "Installe requirements.txt avant d'utiliser les endpoints database."
            ),
        ) from exc

    yield from get_db()
