from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(User).where(
            (User.email == data.email) | (User.username == data.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Пользователь уже существует")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Неверный логин или пароль")

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user