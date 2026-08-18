"""docker-compose.yml must not silently override the defaults in config.py.

Every `VAR: ${VAR:-default}` line in the compose file wins over the matching
field default in `Settings`, because by the time pydantic reads the environment
the variable is already set. So a default written in both places is really only
written in one - the compose one - and changing config.py alone does nothing.

That has bitten twice: SEED_ON_START (which made "unset means skip" unreachable)
and DEMO_ADMIN_PASSWORD (which kept the old password after the default changed).
This test compares the two lists so the next drift fails here instead of in a
confusing debugging session.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from app.config import Settings

def _find_compose() -> Path | None:
    """The compose file lives beside the backend, which is not in the image.

    Tests usually run inside the container (where only /app exists), so look in
    the repo checkout, in an explicitly mounted /repo, and at COMPOSE_FILE_PATH.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "docker-compose.yml",
        Path("/repo/docker-compose.yml"),
        Path.cwd() / "docker-compose.yml",
    ]
    if env := os.environ.get("COMPOSE_FILE_PATH"):
        candidates.insert(0, Path(env))
    return next((c for c in candidates if c.is_file()), None)


COMPOSE = _find_compose()

# Values compose computes for the container rather than mirroring from Settings:
# service hostnames, ports inside the network, and bind addresses.
NOT_MIRRORED = {
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "INTERNAL_API_URL",
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_SITE_URL",
    "NEXT_PUBLIC_DEFAULT_LOCALE",
    "BACKEND_IMAGE",
    "FRONTEND_IMAGE",
    "DOCKER_NETWORK",
}

# `VAR: ${VAR:-default}` - only the colon form carries a default worth checking.
PATTERN = re.compile(r"^\s{6}([A-Z0-9_]+):\s*\$\{\1:-(.*)\}\s*$", re.M)


def _compose_defaults() -> dict[str, str]:
    if COMPOSE is None:
        return {}
    return {
        name: default
        for name, default in PATTERN.findall(COMPOSE.read_text(encoding="utf-8"))
        if name not in NOT_MIRRORED
    }


def _settings_defaults() -> dict[str, object]:
    return {
        name.upper(): field.default
        for name, field in Settings.model_fields.items()
        if field.default is not None
    }


def test_compose_file_is_readable() -> None:
    if COMPOSE is None:
        pytest.skip(
            "docker-compose.yml not reachable from here - it is outside the "
            "backend image. Run with -v $PWD:/repo or set COMPOSE_FILE_PATH."
        )
    assert _compose_defaults(), "no `VAR: ${VAR:-default}` lines found - regex stale?"


@pytest.mark.parametrize("name,compose_default", sorted(_compose_defaults().items()))
def test_compose_default_matches_settings(name: str, compose_default: str) -> None:
    settings_defaults = _settings_defaults()
    if name not in settings_defaults:
        pytest.skip(f"{name} has no matching Settings field")

    expected = settings_defaults[name]
    # Compose values are always strings; Settings holds real types.
    if isinstance(expected, bool):
        actual: object = compose_default.strip().lower() in {"true", "1", "yes"}
    elif isinstance(expected, int):
        actual = int(compose_default)
    else:
        actual = compose_default

    assert actual == expected, (
        f"{name}: docker-compose.yml defaults to {compose_default!r} but "
        f"config.py defaults to {expected!r}. The compose value wins, so the "
        f"config.py default is dead. Change both or neither."
    )


def test_production_refuses_the_development_admin_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A trivial password is fine on a laptop and not fine on the internet."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "123")
    monkeypatch.setenv("SEED_ON_START", "true")

    with pytest.raises(ValueError, match="still the development default"):
        Settings()


def test_production_is_fine_once_the_password_is_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "a-real-password")
    assert Settings().demo_admin_password == "a-real-password"


def test_the_guard_does_not_fire_when_demo_accounts_are_not_seeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No demo admin is created, so the value is never used."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "123")
    monkeypatch.setenv("SEED_ON_START", "false")

    assert Settings().seed_on_start is False


def test_development_keeps_the_convenient_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)
    settings = Settings()
    assert settings.demo_admin_username == "admin"
    assert settings.demo_admin_password == "123"
