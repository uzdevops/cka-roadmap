"""Handing out the link button, and taking the link back.

Note: this module deliberately does NOT use postponed annotations, for the same
reason auth.py does not. slowapi's @limiter.limit wraps the endpoint, so FastAPI
resolves its type hints against slowapi's module globals - where `SessionDep`
and `CurrentUser` do not exist. String annotations therefore fail to resolve and
FastAPI quietly treats both as query parameters, answering every call with a 422
about missing `session` and `user`.
"""

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.config import settings
from app.deps import CurrentUser, SessionDep
from app.rate_limit import limiter
from app.schemas.telegram import TelegramLinkOffer, TelegramStatus
from app.services import telegram_service

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _status(user) -> TelegramStatus:
    return TelegramStatus(
        enabled=settings.telegram_enabled,
        linked=user.telegram_linked,
        username=user.telegram_username,
        linked_at=user.telegram_linked_at,
    )


@router.get("/status", response_model=TelegramStatus)
async def telegram_status(user: CurrentUser) -> TelegramStatus:
    return _status(user)


@router.post("/link-token", response_model=TelegramLinkOffer, status_code=201)
# Rate limited because a token is a credential: without a cap, anybody could mint
# them continuously and keep a stream of live links in flight.
@limiter.limit("10/minute")
async def create_link_token(
    request: Request,
    # slowapi writes its X-RateLimit-* headers onto this, and raises if the
    # endpoint does not declare one. Same reason auth.py's login takes it.
    response: Response,
    session: SessionDep,
    user: CurrentUser,
) -> TelegramLinkOffer:
    if not settings.telegram_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Telegram bot is not configured on this deployment",
        )

    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()
    return TelegramLinkOffer(
        url=offer.url,
        expires_at=offer.expires_at,
        ttl_minutes=settings.link_token_ttl_minutes,
    )


@router.delete("/link", response_model=TelegramStatus)
async def disconnect(session: SessionDep, user: CurrentUser) -> TelegramStatus:
    """Idempotent: disconnecting an unlinked account is not an error, it is the
    state the caller asked for."""
    await telegram_service.unlink(session, user)
    return _status(user)
