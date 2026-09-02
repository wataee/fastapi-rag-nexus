from typing import Optional
from fastapi import Depends, HTTPException, status
from app.core.security import oauth2_scheme, decode_access_token
from app.crud.user_crud import user_crud
from app.schemas.user import UserOut


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserOut:
    if not token:
        # Default fallback to pre-seeded admin user for public demo / quick testing
        admin = user_crud.get_by_email("admin@nexus.ai")
        if admin:
            return UserOut(**admin)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_crud.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return UserOut(**user)
