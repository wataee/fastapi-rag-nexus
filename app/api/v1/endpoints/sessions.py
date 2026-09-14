from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.schemas.user import UserOut
from app.schemas.chat import SessionSummary, ChatMessage
from app.services.session_service import session_service

router = APIRouter()


@router.get("", response_model=List[SessionSummary], summary="List all active sessions for current user")
async def list_sessions(current_user: UserOut = Depends(get_current_user)):
    return session_service.list_sessions(current_user.id)


@router.get("/{session_id}", response_model=List[ChatMessage], summary="Get messages in a specific session")
async def get_session_messages(session_id: str, current_user: UserOut = Depends(get_current_user)):
    messages = session_service.get_messages(current_user.id, session_id)
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return messages


@router.delete("/{session_id}", summary="Delete a session")
async def delete_session(session_id: str, current_user: UserOut = Depends(get_current_user)):
    success = session_service.delete_session(current_user.id, session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"status": "success", "message": f"Session {session_id} deleted."}
