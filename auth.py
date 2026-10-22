from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    """What GET /api/auth/me returns, and what the get_current_user
    dependency hands to protected routes. Deliberately excludes
    password_hash — that field never leaves the database layer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
