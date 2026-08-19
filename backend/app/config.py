"""Application configuration.

Every value has a working default so the stack boots with zero .env files.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Secrets that may arrive as a file path instead of a value. Docker Swarm mounts
# secrets at /run/secrets/<name> rather than putting them in the environment,
# which keeps them out of `docker inspect` and out of the process environment of
# every child process.
_FILE_BACKED = ("SECRET_KEY", "POSTGRES_PASSWORD", "TELEGRAM_BOT_TOKEN")


def _load_file_backed_secrets() -> None:
    """Turns `FOO_FILE=/run/secrets/x` into `FOO=<contents of x>`.

    Runs before Settings is constructed. An explicit FOO in the environment wins,
    so a compose run with a plain .env is unaffected; this only fills a gap.
    A missing or unreadable file is left alone rather than raising - the field's
    own default or validation then reports the problem in terms the operator
    recognises, instead of a traceback out of the config module.
    """
    for name in _FILE_BACKED:
        if os.environ.get(name):
            continue
        path = os.environ.get(f"{name}_FILE")
        if not path:
            continue
        try:
            value = Path(path).read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            os.environ[name] = value


# The password a fresh checkout starts with. Referenced by the guard below.
_DEV_ADMIN_PASSWORD = "123"


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
    # A track is opened by pressing Start, which is what gives the countdown a
    # day one. Off, every track behaves as it did before enrollments existed.
    # Off until the frontend has a Start screen. The 0009 backfill gives an
    # enrolment to anyone with progress, but a newly created account has
    # none, and with the gate on it could reach no content and have no way
    # to fix that. Turn it on once there is a button to press.
    enforce_track_start: bool = True
    # Fallback length for a track whose phases declare no week range and which
    # has no weeks yet - an empty track still needs a target date to show.
    track_default_weeks: int = 20
    phase_unlock_min_score: float = 70.0

    # --- Rate limiting ---------------------------------------------------
    auth_rate_limit: str = "20/minute"
    rate_limit_enabled: bool = True

    # --- Telegram (entirely optional) ------------------------------------
    #
    # Empty token means no bot: the service exits cleanly instead of
    # crash-looping, /auth/config reports it as disabled, and the UI hides
    # everything about it. Nothing else in the platform depends on it.
    telegram_bot_token: str = ""
    # The @name, without the @ - only used to build the t.me deep link.
    telegram_bot_username: str = ""
    # A link token is single-use and short-lived; fifteen minutes is long enough
    # to switch to a phone and short enough that a forwarded link is dead.
    link_token_ttl_minutes: int = 15

    # --- Daily reminder --------------------------------------------------
    #
    # One time for everybody rather than a per-user setting: a personal
    # schedule sounds better than it works, and it multiplies the number of
    # states the sender has to reason about by the number of users.
    #
    # The zone must be explicit. A server is usually UTC, and 20:30 there is
    # the middle of the night here - a naive datetime would be silently wrong.
    reminder_tz: str = "Asia/Tashkent"
    reminder_hour: int = 20
    reminder_minute: int = 30

    # --- Seed ------------------------------------------------------------
    seed_on_start: bool = True
    demo_student_email: str = "student@demo.local"
    demo_student_username: str = "student"
    demo_student_password: str = "DemoPass123!"
    demo_admin_email: str = "admin@demo.local"
    demo_admin_username: str = "admin"
    # Deliberately trivial so a fresh checkout is usable immediately: sign in as
    # admin / 123 and change it from the profile page. `_reject_default_admin_password`
    # below refuses to boot with this value in production.
    demo_admin_password: str = _DEV_ADMIN_PASSWORD

    @model_validator(mode="after")
    def _reject_default_admin_password(self) -> "Settings":
        """A trivial admin password is for a laptop, not for the internet.

        The default exists so a fresh checkout is usable straight away. Shipping
        it to a public deployment would leave an admin account open to anyone
        who read this file, so production has to set its own - unless it does
        not seed the demo accounts at all, in which case the value is unused.
        """
        if (
            self.environment.strip().lower() == "production"
            and self.seed_on_start
            and self.demo_admin_password == _DEV_ADMIN_PASSWORD
        ):
            raise ValueError(
                "DEMO_ADMIN_PASSWORD is still the development default "
                f"({_DEV_ADMIN_PASSWORD!r}). Set a real one in .env, or set "
                "SEED_ON_START=false if this deployment does not want demo accounts."
            )
        return self

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
    def telegram_enabled(self) -> bool:
        """Both halves are needed: a token to talk, a username to be found."""
        return bool(self.telegram_bot_token and self.telegram_bot_username)

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
    _load_file_backed_secrets()
    return Settings()


settings = get_settings()
