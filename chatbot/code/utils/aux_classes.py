from typing import Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class GitHubWebhookData(BaseModel):
    ref: str | None = None