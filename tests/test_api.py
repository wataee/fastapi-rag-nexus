import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.crud.user_crud import user_crud
from app.services.session_service import session_service
from app.services.ingestion_service import ingestion_service
from app.schemas.chat import ChatMessage

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert "StreamRAG" in data["service"]

def test_health_liveness():
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_health_readiness():
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

def test_password_hashing():
    pwd = "SecretPassword123!"
    h = hash_password(pwd)
    assert verify_password(pwd, h)
    assert not verify_password("WrongPassword", h)

def test_jwt_token_encode_decode():
    data = {"sub": "user_123", "username": "alex"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_123"

def test_auth_login_success():
    res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@streamrag.dev"

def test_auth_login_invalid_password():
    res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "wrong"})
    assert res.status_code == 401

def test_auth_login_unknown_user():
    res = client.post("/api/v1/auth/login", json={"username_or_email": "unknown@domain.com", "password": "pass"})
    assert res.status_code == 401

def test_auth_register_user():
    email = "researcher@streamrag.dev"
    res = client.post("/api/v1/auth/register", json={
        "username": "researcher",
        "email": email,
        "password": "ResearchPass123!",
        "full_name": "AI Researcher"
    })
    assert res.status_code == 201
    assert res.json()["email"] == email

def test_auth_register_duplicate_email():
    res = client.post("/api/v1/auth/register", json={
        "username": "duplicate_user",
        "email": "admin@streamrag.dev",
        "password": "pwd"
    })
    assert res.status_code == 400

def test_get_me_authenticated():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "admin@streamrag.dev"

def test_chat_sync_completion():
    res = client.post("/api/v1/chat", json={
        "message": "Summarize the vector index configuration.",
        "top_k": 2,
        "temperature": 0.1
    })
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["citations"]) <= 2
    assert "session_id" in data

def test_chat_sse_stream_endpoint():
    res = client.post("/api/v1/chat/stream", json={
        "message": "What is the token emission rate?",
        "top_k": 2
    })
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    text = res.text
    assert "event: token" in text
    assert "event: done" in text
    assert "data: [DONE]" in text

def test_session_lifecycle():
    user_id = "user_admin_001"
    session_id = "test_sess_flow_99"
    msg = ChatMessage(role="user", content="Hello streamrag")
    session_service.append_message(user_id, session_id, msg)
    
    msgs = session_service.get_messages(user_id, session_id)
    assert len(msgs) == 1
    assert msgs[0].content == "Hello streamrag"

    sessions = session_service.list_sessions(user_id)
    assert any(s.session_id == session_id for s in sessions)

    deleted = session_service.delete_session(user_id, session_id)
    assert deleted is True

def test_get_session_messages_endpoint():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    
    # Create message via chat
    chat_res = client.post("/api/v1/chat", json={"message": "Test message"}, headers={"Authorization": f"Bearer {token}"})
    sid = chat_res.json()["session_id"]
    
    res = client.get(f"/api/v1/sessions/{sid}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_list_sessions_endpoint():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    res = client.get("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_delete_unknown_session():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    res = client.delete("/api/v1/sessions/non_existent_id", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_document_ingestion_service():
    content = b"StreamRAG provides hybrid lexical and dense vector search capabilities."
    res = ingestion_service.ingest_document("test_manual.pdf", content, "specs")
    assert res.status == "indexed"
    assert res.chunks_created >= 1

    docs = ingestion_service.list_documents()
    assert any(d.document_id == res.document_id for d in docs)

    del_ok = ingestion_service.delete_document(res.document_id)
    assert del_ok is True

def test_document_upload_api():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    
    files = {"file": ("integration_guide.txt", b"Document content for knowledge base indexation.", "text/plain")}
    res = client.post("/api/v1/documents/upload", files=files, data={"category": "guides"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["status"] == "indexed"

def test_document_list_api():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_delete_document_api():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    
    files = {"file": ("to_delete.txt", b"temporary", "text/plain")}
    up = client.post("/api/v1/documents/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    doc_id = up.json()["document_id"]
    
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

def test_delete_missing_document_api():
    login_res = client.post("/api/v1/auth/login", json={"username_or_email": "admin@streamrag.dev", "password": "admin123"})
    token = login_res.json()["access_token"]
    del_res = client.delete("/api/v1/documents/doc_non_existent", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 404

def test_chat_empty_message_validation():
    res = client.post("/api/v1/chat", json={"message": ""})
    assert res.status_code == 422

def test_chat_invalid_top_k():
    res = client.post("/api/v1/chat", json={"message": "hi", "top_k": 999})
    assert res.status_code == 422
