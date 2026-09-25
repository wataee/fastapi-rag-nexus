import time
from typing import List, Dict, Any
from app.schemas.chat import ChatMessage, SessionSummary

class SessionService:
    def __init__(self):
        # memory buffer: user_id -> session_id -> list of ChatMessage
        self._storage: Dict[str, Dict[str, List[ChatMessage]]] = {}

    def get_messages(self, user_id: str, session_id: str) -> List[ChatMessage]:
        return self._storage.get(user_id, {}).get(session_id, [])

    def append_message(self, user_id: str, session_id: str, message: ChatMessage):
        if user_id not in self._storage:
            self._storage[user_id] = {}
        if session_id not in self._storage[user_id]:
            self._storage[user_id][session_id] = []
        if not message.timestamp:
            message.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._storage[user_id][session_id].append(message)

    def list_sessions(self, user_id: str) -> List[SessionSummary]:
        user_sessions = self._storage.get(user_id, {})
        summaries = []
        for sid, msgs in user_sessions.items():
            last_ts = msgs[-1].timestamp if msgs else None
            summaries.append(SessionSummary(
                session_id=sid,
                user_id=user_id,
                message_count=len(msgs),
                last_updated=last_ts
            ))
        return summaries

    def delete_session(self, user_id: str, session_id: str) -> bool:
        if user_id in self._storage and session_id in self._storage[user_id]:
            del self._storage[user_id][session_id]
            return True
        return False

session_service = SessionService()
