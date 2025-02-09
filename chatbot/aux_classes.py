from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3  # Número de respuestas a recuperar# Modelo de consulta

class GitHubWebhookData(BaseModel):
    ref: str | None = None