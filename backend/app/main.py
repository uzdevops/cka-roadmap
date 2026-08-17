"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import engine
from app.rate_limit import limiter
from app.routers import admin, auth, health, labs, lessons, progress, quizzes, roadmap

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "Starting %s (env=%s, google_oauth=%s)",
        settings.app_name,
        settings.environment,
        settings.google_oauth_enabled,
    )
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Backend API for the CKA exam-prep learning platform: roadmap, lessons, "
        "quizzes, labs and progress tracking."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# --- Middleware ----------------------------------------------------------

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests - slow down and try again shortly."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authlib's OAuth flow needs a signed session cookie for the state parameter.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False,
)

# --- Routes --------------------------------------------------------------

app.include_router(health.router)

api = settings.api_v1_prefix
app.include_router(auth.router, prefix=api)
app.include_router(roadmap.router, prefix=api)
app.include_router(lessons.router, prefix=api)
app.include_router(quizzes.router, prefix=api)
app.include_router(labs.router, prefix=api)
app.include_router(progress.router, prefix=api)
app.include_router(admin.router, prefix=api)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.api_v1_prefix,
    }
