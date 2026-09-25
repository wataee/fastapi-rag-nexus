from typing import Optional
from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    status: str

class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    category: str
    chunks_count: int
    created_at: str
