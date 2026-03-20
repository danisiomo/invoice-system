import uuid

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True