"""Auth + user schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool
    target_exam_date: date | None = None
    daily_study_minutes: int
    avatar_url: str | None = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    target_exam_date: date | None = None
    daily_study_minutes: int | None = Field(default=None, ge=5, le=1440)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class AuthConfig(BaseModel):
    """Told to the frontend so it can hide the Google button when unset."""

    google_oauth_enabled: bool
    registration_enabled: bool = True
    phase_unlock_enforced: bool = False
    locales: list[str] = Field(default_factory=list)
    default_locale: str = "en"
