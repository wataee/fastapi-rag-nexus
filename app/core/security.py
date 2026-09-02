import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Secure SHA-256 salted password hashing."""
    salt = settings.SECRET_KEY[:16].encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000).hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire.timestamp()})

    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    signature = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header}.{payload}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected_sig = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig + "==")
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        data = json.loads(base64.urlsafe_b64decode(payload + "==").decode())
        if "exp" in data and datetime.utcnow().timestamp() > data["exp"]:
            return None
        return data
    except Exception:
        return None
