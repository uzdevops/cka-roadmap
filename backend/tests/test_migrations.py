"""The migration chain has to actually run.

Every other test builds its schema with `Base.metadata.create_all`, so a broken
Alembic revision passes the whole suite and fails at container start - in
production, where `entrypoint.sh` runs `alembic upgrade head` before uvicorn
binds. These tests are the only thing that executes a migration.

They run against a throwaway database so nothing else is at risk.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"
SCRATCH_DB = f"{settings.postgres_db}_migrationtest"


def _expected_head() -> str:
    """The one revision no other revision names as its down_revision."""
    revisions: dict[str, str | None] = {}
    for path in VERSIONS_DIR.glob("*.py"):
        body = path.read_text(encoding="utf-8")
        rev = re.search(r"^revision(?::\s*str)?\s*=\s*[\"']([^\"']+)[\"']", body, re.M)
        down = re.search(
            r"^down_revision(?::\s*[^=]+)?\s*=\s*(?:[\"']([^\"']+)[\"']|None)", body, re.M
        )
        if rev:
            revisions[rev.group(1)] = down.group(1) if down and down.group(1) else None

    assert revisions, f"no migrations found in {VERSIONS_DIR}"
    parents = {d for d in revisions.values() if d}
    heads = [r for r in revisions if r not in parents]
    assert len(heads) == 1, f"expected exactly one head, found {heads}"

    # Every down_revision must name a revision that exists, or `upgrade head`
    # fails at runtime with a KeyError that no unit test would otherwise see.
    for rev, down in revisions.items():
        assert down is None or down in revisions, f"{rev} points at missing {down}"
    return heads[0]


async def _run_sql_on_postgres(statement: str) -> None:
    admin_url = settings.sqlalchemy_url.rpartition("/")[0] + "/postgres"
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.execute(text(statement))
    finally:
        await engine.dispose()


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    """Run alembic exactly the way the entrypoint does, against the scratch DB.

    `alembic/env.py` overrides sqlalchemy.url from app settings, so the database
    is redirected through the environment rather than through -x.
    """
    env = {**os.environ, "POSTGRES_DB": SCRATCH_DB}
    return subprocess.run(
        ["alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


async def _version_in_scratch() -> str | None:
    url = settings.sqlalchemy_url.rpartition("/")[0] + f"/{SCRATCH_DB}"
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            return await conn.scalar(text("SELECT version_num FROM alembic_version"))
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def scratch_db() -> None:
    assert SCRATCH_DB != settings.postgres_db, "scratch database must not be the real one"
    await _run_sql_on_postgres(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}"')
    await _run_sql_on_postgres(f'CREATE DATABASE "{SCRATCH_DB}"')
    yield
    await _run_sql_on_postgres(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}"')


def test_migration_chain_is_linear_with_one_head() -> None:
    """Cheap, no database: catches a duplicated or dangling down_revision."""
    assert _expected_head()


async def test_upgrade_head_runs_on_an_empty_database(scratch_db: None) -> None:
    result = _alembic("upgrade", "head")
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stderr}"
    assert await _version_in_scratch() == _expected_head()


async def test_latest_revision_can_be_rolled_back(scratch_db: None) -> None:
    """A downgrade nobody has run is a downgrade that does not work.

    This is what makes a bad deploy recoverable without restoring a dump.
    """
    assert _alembic("upgrade", "head").returncode == 0

    down = _alembic("downgrade", "-1")
    assert down.returncode == 0, f"downgrade -1 failed:\n{down.stderr}"
    assert await _version_in_scratch() != _expected_head()

    up = _alembic("upgrade", "head")
    assert up.returncode == 0, f"re-upgrade failed:\n{up.stderr}"
    assert await _version_in_scratch() == _expected_head()
