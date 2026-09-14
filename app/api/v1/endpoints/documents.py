from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.schemas.user import UserOut
from app.schemas.document import DocumentUploadResponse, DocumentListItem
from app.services.ingestion_service import ingestion_service

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, summary="Upload and chunk document into knowledge base")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    current_user: UserOut = Depends(get_current_user),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    return ingestion_service.ingest_document(filename=file.filename, content=content, category=category)


@router.get("", response_model=List[DocumentListItem], summary="List ingested documents")
async def list_documents(current_user: UserOut = Depends(get_current_user)):
    return ingestion_service.list_documents()


@router.delete("/{document_id}", summary="Delete document from knowledge base")
async def delete_document(document_id: str, current_user: UserOut = Depends(get_current_user)):
    success = ingestion_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"status": "success", "message": f"Document {document_id} deleted."}
