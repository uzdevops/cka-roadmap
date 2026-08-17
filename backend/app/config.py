"""Application configuration.

Every value has a working default so the stack boots with zero .env files.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App -------------------------------------------------------------
    app_name: str = "CKA Prep API"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- Database --------------------------------------------------------
    postgres_user: str = "cka"
    postgres_password: str = "cka_password"
    postgres_db: str = "cka_prep"
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str | None = None

    # --- Security --------------------------------------------------------
    secret_key: str = "dev-secret-change-me-in-production-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # --- CORS ------------------------------------------------------------
    frontend_origin: str = "http://localhost:3000"
    cors_origins: str = ""

    # --- Google OAuth (entirely optional) --------------------------------
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:8000/api/v1/auth/google/callback"
    oauth_success_redirect: str = "http://localhost:3000/auth/callback"

    # --- Feature flags ---------------------------------------------------
    enforce_phase_unlock: bool = False
    phase_unlock_min_score: float = 70.0

    # --- Rate limiting ---------------------------------------------------
    auth_rate_limit: str = "20/minute"
    rate_limit_enabled: bool = True

    # --- Seed ------------------------------------------------------------
    seed_on_start: bool = True
    demo_student_email: str = "student@demo.local"
    demo_student_password: str = "DemoPass123!"
    demo_admin_email: str = "admin@demo.local"
    demo_admin_password: str = "AdminPass123!"

    @field_validator("database_url", mode="before")
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        return v or None

    @property
    def sqlalchemy_url(self) -> str:
        """Async SQLAlchemy DSN."""
        if self.database_url:
            return self._normalize(self.database_url)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_sqlalchemy_url(self) -> str:
        """Sync DSN (used by tooling that cannot speak asyncpg)."""
        return self.sqlalchemy_url.replace("+asyncpg", "")

    @staticmethod
    def _normalize(url: str) -> str:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def allowed_origins(self) -> list[str]:
        raw = self.cors_origins or self.frontend_origin
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        return origins or ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
