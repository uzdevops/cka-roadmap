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


def _find_stack() -> Path | None:
    candidates = [
        Path(__file__).resolve().parents[2] / "docker-stack.yml",
        Path("/repo/docker-stack.yml"),
        Path.cwd() / "docker-stack.yml",
    ]
    if env := os.environ.get("STACK_FILE_PATH"):
        candidates.insert(0, Path(env))
    return next((c for c in candidates if c.is_file()), None)


STACK = _find_stack()

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


# --- the Swarm file has to agree with the compose file ----------------------


def _stack_defaults() -> dict[str, str]:
    """Same `VAR: ${VAR:-default}` shape, one indent level deeper."""
    if STACK is None:
        return {}
    pattern = re.compile(r"^\s{6}([A-Z0-9_]+):\s*\$\{\1:-(.*)\}\s*$", re.M)
    return {
        name: default
        for name, default in pattern.findall(STACK.read_text(encoding="utf-8"))
        if name not in NOT_MIRRORED
    }


def test_stack_file_is_readable() -> None:
    if STACK is None:
        pytest.skip(
            "docker-stack.yml not reachable from here. Run with -v $PWD:/repo or "
            "set STACK_FILE_PATH."
        )
    assert _stack_defaults(), "no `VAR: ${VAR:-default}` lines found - regex stale?"


def test_the_swarm_file_defaults_match_the_compose_file() -> None:
    """Two deployment paths, one set of defaults.

    Whichever file a deployment uses wins over `Settings`, so a value that
    differs between them means the same command produces two different
    applications depending on how it was started - and nothing reports it.
    """
    if STACK is None or COMPOSE is None:
        pytest.skip("both deployment files are needed for this comparison")

    compose = _compose_defaults()
    stack = _stack_defaults()

    disagreements = {
        name: (compose[name], stack[name])
        for name in compose.keys() & stack.keys()
        if compose[name] != stack[name]
    }
    assert not disagreements, (
        "docker-compose.yml and docker-stack.yml disagree: "
        + ", ".join(
            f"{n}: compose={c!r} stack={s!r}" for n, (c, s) in sorted(disagreements.items())
        )
    )


def test_the_swarm_file_covers_the_same_variables() -> None:
    """A variable the Swarm path forgets falls back to a different default.

    Two are expected to be missing: SECRET_KEY and POSTGRES_PASSWORD arrive as
    Docker secrets there (`*_FILE`), which is the point of the Swarm path.
    """
    if STACK is None or COMPOSE is None:
        pytest.skip("both deployment files are needed for this comparison")

    via_secret = {"SECRET_KEY", "POSTGRES_PASSWORD"}
    missing = set(_compose_defaults()) - set(_stack_defaults()) - via_secret
    assert not missing, (
        f"docker-stack.yml does not set {sorted(missing)}. Those services would "
        f"fall back to the image default instead of the deployment's."
    )


# --- Docker secrets ---------------------------------------------------------


def test_a_secret_can_arrive_as_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Swarm mounts secrets at /run/secrets/<name>, not into the environment.

    Keeping them out of the environment is the point: an environment variable
    is visible in `docker inspect` and inherited by every child process.
    """
    from app.config import _load_file_backed_secrets

    secret = tmp_path / "cka_secret_key"
    secret.write_text("value-from-the-file\n", encoding="utf-8")

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("SECRET_KEY_FILE", str(secret))
    _load_file_backed_secrets()

    assert Settings().secret_key == "value-from-the-file", "trailing newline not stripped?"


def test_an_explicit_value_beats_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """So a compose run with a plain .env is never overridden by a stale mount."""
    from app.config import _load_file_backed_secrets

    secret = tmp_path / "cka_secret_key"
    secret.write_text("from-the-file", encoding="utf-8")

    monkeypatch.setenv("SECRET_KEY", "from-the-environment")
    monkeypatch.setenv("SECRET_KEY_FILE", str(secret))
    _load_file_backed_secrets()

    assert Settings().secret_key == "from-the-environment"


def test_a_missing_secret_file_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The field's own default or validation should report the problem, in terms
    an operator recognises - not a traceback out of the config module."""
    from app.config import _load_file_backed_secrets

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("SECRET_KEY_FILE", str(tmp_path / "does-not-exist"))

    _load_file_backed_secrets()  # must not raise
    assert Settings().secret_key


# --- and the Kubernetes manifest, which is a third copy of the same list -----


def _find_k8s_config() -> Path | None:
    candidates = [
        Path(__file__).resolve().parents[2] / "k8s" / "01-config.yaml",
        Path("/repo/k8s/01-config.yaml"),
        Path.cwd() / "k8s" / "01-config.yaml",
    ]
    if env := os.environ.get("K8S_CONFIG_PATH"):
        candidates.insert(0, Path(env))
    return next((c for c in candidates if c.is_file()), None)


K8S_CONFIG = _find_k8s_config()


def _k8s_values() -> dict[str, str]:
    """ConfigMap entries, which are `NAME: "value"` with no ${} indirection."""
    if K8S_CONFIG is None:
        return {}
    pattern = re.compile(r'^\s{2}([A-Z0-9_]+):\s*"(.*)"\s*$', re.M)
    return {
        name: value
        for name, value in pattern.findall(K8S_CONFIG.read_text(encoding="utf-8"))
        if name not in NOT_MIRRORED
    }


# Behaviour switches: these decide what the application DOES, so they have to
# mean the same thing wherever it runs. Everything else in the manifest -
# domains, secrets, ENVIRONMENT, the demo credentials - is deployment-specific
# and SHOULD differ; comparing those would be asserting something untrue.
BEHAVIOUR_FLAGS = {
    "ENFORCE_PHASE_UNLOCK",
    "ENFORCE_TRACK_START",
    "TRACK_DEFAULT_WEEKS",
    "PHASE_UNLOCK_MIN_SCORE",
    "SEED_ON_START",
}


def test_the_kubernetes_manifest_agrees_on_the_behaviour_flags() -> None:
    """A third place the same switches are written down.

    Easy to forget precisely because nothing in the local workflow reads it, so
    a wrong value can sit there for months and surface only on a cluster. It
    already did: ENFORCE_TRACK_START stayed "true" here after every other file
    was set to false, which would have gated every user out of their content on
    Kubernetes and nowhere else.
    """
    if K8S_CONFIG is None or COMPOSE is None:
        pytest.skip("both files are needed for this comparison")

    compose = _compose_defaults()
    k8s = _k8s_values()

    shared = compose.keys() & k8s.keys() & BEHAVIOUR_FLAGS
    assert shared, "no behaviour flags found in both files - are the regexes stale?"

    disagreements = {
        name: (compose[name], k8s[name])
        for name in shared
        if compose[name] != k8s[name]
    }
    assert not disagreements, (
        "k8s/01-config.yaml and docker-compose.yml disagree on a behaviour flag: "
        + ", ".join(
            f"{n}: compose={c!r} k8s={k!r}" for n, (c, k) in sorted(disagreements.items())
        )
    )
