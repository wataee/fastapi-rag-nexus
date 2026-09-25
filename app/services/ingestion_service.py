import uuid
import time
from typing import List, Dict, Any
from app.schemas.document import DocumentUploadResponse, DocumentListItem

class IngestionService:
    def __init__(self):
        self._docs: Dict[str, Dict[str, Any]] = {}
        # Pre-seed sample document
        sample_id = "doc_sys_arch_001"
        self._docs[sample_id] = {
            "document_id": sample_id,
            "filename": "architecture_overview.pdf",
            "category": "technical",
            "chunks_count": 18,
            "created_at": "2026-09-01T12:00:00Z"
        }

    def ingest_document(self, filename: str, content: bytes, category: str = "general") -> DocumentUploadResponse:
        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        # Approximate chunk count based on content size
        estimated_chunks = max(1, len(content) // 600)
        self._docs[doc_id] = {
            "document_id": doc_id,
            "filename": filename,
            "category": category,
            "chunks_count": estimated_chunks,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return DocumentUploadResponse(
            document_id=doc_id,
            filename=filename,
            chunks_created=estimated_chunks,
            status="indexed"
        )

    def list_documents(self) -> List[DocumentListItem]:
        return [DocumentListItem(**d) for d in self._docs.values()]

    def delete_document(self, document_id: str) -> bool:
        if document_id in self._docs:
            del self._docs[document_id]
            return True
        return False

ingestion_service = IngestionService()
