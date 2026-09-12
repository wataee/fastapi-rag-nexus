import uuid
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.config import settings
from app.api.deps import get_current_user
from app.core.rate_limiter import limiter
from app.schemas.user import UserOut
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage, Citation
from app.services.session_service import session_service
from app.services.rag_chain import rag_chain

router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Send a message to conversational RAG")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
    current_user: UserOut = Depends(get_current_user),
):
    session_id = body.session_id or str(uuid.uuid4())
    history = session_service.get_messages(current_user.id, session_id)

    # Record user message
    user_msg = ChatMessage(role="user", content=body.message)
    session_service.append_message(current_user.id, session_id, user_msg)

    # Run RAG
    answer, citations, latency = await rag_chain.execute(
        user_message=body.message,
        history=history,
        top_k=body.top_k,
        category=body.category_filter,
        temperature=body.temperature,
    )

    # Record assistant message
    asst_msg = ChatMessage(role="assistant", content=answer, citations=citations)
    session_service.append_message(current_user.id, session_id, asst_msg)

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        citations=citations,
        latency_seconds=latency,
        model=settings.LLM_MODEL,
    )


@router.post("/stream", summary="Stream conversational RAG response via SSE")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def chat_stream_endpoint(
    request: Request,
    body: ChatRequest,
    current_user: UserOut = Depends(get_current_user),
):
    session_id = body.session_id or str(uuid.uuid4())
    history = session_service.get_messages(current_user.id, session_id)

    user_msg = ChatMessage(role="user", content=body.message)
    session_service.append_message(current_user.id, session_id, user_msg)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'init', 'session_id': session_id})}\n\n"
        full_tokens = []
        citations_data = []

        async for chunk in rag_chain.stream(
            user_message=body.message,
            history=history,
            top_k=body.top_k,
            category=body.category_filter,
            temperature=body.temperature,
        ):
            if chunk.get("type") == "token":
                full_tokens.append(chunk["delta"])
            elif chunk.get("type") == "citations":
                citations_data = chunk.get("citations", [])
            yield f"data: {json.dumps(chunk)}\n\n"

        asst_msg = ChatMessage(
            role="assistant",
            content="".join(full_tokens),
            citations=[Citation(**c) for c in citations_data],
        )
        session_service.append_message(current_user.id, session_id, asst_msg)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
