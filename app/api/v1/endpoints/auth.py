from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from app.config import settings
from app.core.security import create_access_token
from app.crud.user_crud import user_crud
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register(user_in: UserCreate):
    if user_crud.get_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    if user_crud.get_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )
    return user_crud.create(user_in)


@router.post("/login", response_model=Token, summary="Authenticate and acquire JWT token")
async def login(credentials: UserLogin):
    user = user_crud.authenticate(credentials.username_or_email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
        )
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer", user=UserOut(**user))


@router.get("/me", response_model=UserOut, summary="Get profile of the currently logged-in user")
async def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user
