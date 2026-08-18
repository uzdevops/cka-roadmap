"""Auth + user schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    """Sign-in payload.

    The field is an identifier, not an email: `admin` is a valid value. It is
    still accepted under the key "email" so existing clients keep working - this
    used to be an EmailStr, which rejected a bare username with a 422 before the
    request ever reached the lookup.
    """

    identifier: str = Field(
        min_length=1,
        max_length=320,
        validation_alias=AliasChoices("identifier", "username", "email"),
    )
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
    username: str | None = None
    full_name: str | None = None
    role: str
    is_active: bool
    # The two grants, plus the name the UI shows for their combination. The
    # label is derived on the model, never stored.
    access_topics: bool = True
    access_certificates: bool = True
    role_label: str = ""
    # The exam date moved to TrackEnrollment - one column could only ever
    # describe one exam, and a person studying two tracks needs two dates.
    daily_study_minutes: int
    avatar_url: str | None = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    # A target date is set through PATCH /tracks/{slug}/enrollment.
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
