from typing import List, Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    title: str
    chunk_id: str
    similarity: float
    text_snippet: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=20)
    category_filter: Optional[str] = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    latency_seconds: float
    model: str

class SessionSummary(BaseModel):
    session_id: str
    user_id: str
    message_count: int
    last_updated: Optional[str] = None
