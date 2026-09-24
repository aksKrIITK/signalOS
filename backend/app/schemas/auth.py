import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.core.security import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    email: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    org_id: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str
    role: Optional[str] = UserRole.OWNER


class UserResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
