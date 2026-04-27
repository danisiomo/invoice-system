import uuid
from datetime import datetime

from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: str | None = None
    username: str
    password: str
    full_name: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    username: str
    full_name: str
    is_active: bool
    roles: list[RoleResponse] = []

    class Config:
        from_attributes = True