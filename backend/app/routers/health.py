"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness - deliberately does not touch the database."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(response: Response) -> dict[str, str]:
    """Readiness - fails while the database is unreachable."""
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any driver error means "not ready"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": type(exc).__name__}
    return {"status": "ready", "database": "ok"}
