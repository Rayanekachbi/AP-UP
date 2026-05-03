from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    role: str


class DatabaseMessageResponse(BaseModel):
    message: str


class PasswordMigrationResponse(BaseModel):
    message: str
    users_updated: int


class ModuleResponse(BaseModel):
    id: int
    nom: str
    description: str | None = None
    system_prompt: str | None = None


class ModulePromptRequest(BaseModel):
    system_prompt: str


class ModulePromptResponse(BaseModel):
    id: int
    nom: str
    system_prompt: str | None = None


class ChatMessageRequest(BaseModel):
    utilisateur_id: int
    module_id: int
    question: str


class ChatMessageResponse(BaseModel):
    id: int
    utilisateur_id: int
    module_id: int
    question: str
    reponse: str
    chunks_sources: str | None = None


class ChatHistoryEntryResponse(BaseModel):
    id: int
    utilisateur_id: int
    module_id: int
    question: str
    reponse: str
    date_heure: str


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    title: str
    module_id: int
    chunks_created: int
    status: str


class DocumentResponse(BaseModel):
    id: int
    title: str
    course: str
    status: str
