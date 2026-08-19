"""Authentication endpoints (email/password + optional Google OAuth).

Note: this module deliberately does NOT use `from __future__ import annotations`.
slowapi's @limiter.limit wrapper makes FastAPI resolve type hints against
slowapi's module globals, so postponed (string) annotations would fail to
resolve and every body parameter would be misread as a query parameter.
"""

import logging
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES
from app.deps import CurrentUser, SessionDep
from app.rate_limit import limiter
from app.schemas.auth import (
    AuthConfig,
    PasswordChange,
    RefreshRequest,
    TokenPair,
    UserLogin,
    UserRead,
    UserRegister,
    UserUpdate,
)
from app.services import auth_service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/config", response_model=AuthConfig)
async def auth_config() -> AuthConfig:
    """Lets the UI hide the Google button when no credentials are configured."""
    return AuthConfig(
        google_oauth_enabled=settings.google_oauth_enabled,
        registration_enabled=False,
        phase_unlock_enforced=settings.enforce_phase_unlock,
        telegram_enabled=settings.telegram_enabled,
        locales=list(SUPPORTED_LOCALES),
        default_locale=DEFAULT_LOCALE,
    )


@router.post("/register", response_model=None, include_in_schema=False)
@limiter.limit(settings.auth_rate_limit)
async def register(request: Request, response: Response) -> None:
    """Self-registration is closed; accounts are created by an administrator.

    Kept as a route that refuses rather than deleted, so an old client or a
    bookmarked form gets a clear answer instead of a 404 that reads like a bug.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Self-registration is disabled. Ask an administrator for an account.",
    )


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.auth_rate_limit)
async def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    session: SessionDep,
) -> TokenPair:
    user = await auth_service.authenticate(session, payload.identifier, payload.password)
    return auth_service.issue_tokens(user)


@router.post("/token", response_model=TokenPair, include_in_schema=False)
@limiter.limit(settings.auth_rate_limit)
async def login_form(
    request: Request,
    response: Response,
    session: SessionDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenPair:
    """OAuth2 password flow - powers the Authorize button in /docs."""
    user = await auth_service.authenticate(session, form.username, form.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(settings.auth_rate_limit)
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest,
    session: SessionDep,
) -> TokenPair:
    return await auth_service.refresh_tokens(session, payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate, user: CurrentUser, session: SessionDep
) -> UserRead:
    updated = await auth_service.update_profile(session, user, payload)
    return UserRead.model_validate(updated)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def change_password(
    payload: PasswordChange, user: CurrentUser, session: SessionDep
) -> None:
    await auth_service.change_password(
        session, user, payload.current_password, payload.new_password
    )


# --- Google OAuth (only mounted logically; 404s when unconfigured) --------


def _oauth_client():
    from authlib.integrations.starlette_client import OAuth

    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth.create_client("google")


def _require_oauth_enabled() -> None:
    if not settings.google_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google OAuth is not configured on this deployment",
        )


@router.get("/google/authorize")
async def google_authorize(request: Request):
    _require_oauth_enabled()
    client = _oauth_client()
    return await client.authorize_redirect(request, settings.oauth_redirect_url)


@router.get("/google/callback")
async def google_callback(request: Request, session: SessionDep):
    _require_oauth_enabled()
    client = _oauth_client()
    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:  # noqa: BLE001 - upstream raises many types
        log.warning("Google OAuth callback failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth exchange failed"
        ) from exc

    info = token.get("userinfo") or {}
    email = info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not return an email address",
        )

    user = await auth_service.upsert_oauth_user(
        session,
        provider="google",
        subject=str(info.get("sub")),
        email=email,
        full_name=info.get("name"),
        avatar_url=info.get("picture"),
    )
    tokens = auth_service.issue_tokens(user)
    query = urlencode(
        {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}
    )
    return RedirectResponse(url=f"{settings.oauth_success_redirect}?{query}")
