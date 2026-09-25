import uuid
from typing import Dict, Any, Optional
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate

class UserCRUD:
    def __init__(self):
        self._users: Dict[str, Dict[str, Any]] = {}
        # Pre-seed default admin user
        admin_id = "user_admin_001"
        self._users[admin_id] = {
            "id": admin_id,
            "username": "admin",
            "email": "admin@streamrag.dev",
            "hashed_password": hash_password("admin123"),
            "full_name": "StreamRAG Admin",
            "is_active": True,
            "is_superuser": True
        }

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for u in self._users.values():
            if u["email"].lower() == email.lower():
                return u
        return None

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        for u in self._users.values():
            if u["username"].lower() == username.lower():
                return u
        return None

    def create(self, user_in: UserCreate) -> Dict[str, Any]:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "id": user_id,
            "username": user_in.username,
            "email": user_in.email,
            "hashed_password": hash_password(user_in.password),
            "full_name": user_in.full_name or user_in.username,
            "is_active": True,
            "is_superuser": False
        }
        self._users[user_id] = user
        return user

    def authenticate(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_by_email(username_or_email) or self.get_by_username(username_or_email)
        if not user:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return user

user_crud = UserCRUD()
