from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.Backend.api.routes import auth, chat, database, ingestion
from src.config.settings import FRONTEND_URL

app = FastAPI(
    title="AP UP API",
    description="Premiere version simple de l'API pour connecter le frontend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(database.router)
app.include_router(ingestion.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"message": "API AP UP active"}
