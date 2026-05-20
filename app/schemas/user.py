from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.schemas.types import DatetimeFormatted


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("username must be at most 50 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_active: bool
    created_at: DatetimeFormatted


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
