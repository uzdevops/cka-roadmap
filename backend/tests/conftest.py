"""Test fixtures.

Tests run against a dedicated `<database>_test` database on the same Postgres
server, created on demand, so they never touch the development data.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models import Base, Track, User, UserRole
from app.rate_limit import limiter
from app.security import hash_password

# Throttling would otherwise reject the repeated logins these tests perform.
limiter.enabled = False

# The track-start gate is a feature flag, and almost every test here predates it
# and is about something else. It is switched off by default and switched ON
# explicitly in tests/test_track_start.py, which is the same arrangement
# ENFORCE_PHASE_UNLOCK has - see tests/test_phase_unlock.py. The point of the
# dedicated file is that a flag nothing exercises is a flag that breaks silently
# the day it is turned on.
settings.enforce_track_start = False

TEST_DB_NAME = f"{settings.postgres_db}_test"


def _test_url() -> str:
    base = settings.sqlalchemy_url
    head, _, _ = base.rpartition("/")
    return f"{head}/{TEST_DB_NAME}"


async def _ensure_test_database() -> None:
    """CREATE DATABASE is not transactional, so it needs its own connection."""
    admin_url = settings.sqlalchemy_url.rpartition("/")[0] + "/postgres"
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text

            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DB_NAME},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        await engine.dispose()


async def ensure_track(session: AsyncSession, slug: str = "t1") -> Track:
    """Content hangs off a track, so every test that builds phases needs one.

    Phase slugs and week numbers are unique per track rather than globally, so
    tests that want two isolated roadmaps ask for two different slugs.
    """
    from sqlalchemy import select

    track = (
        await session.execute(select(Track).where(Track.slug == slug))
    ).scalar_one_or_none()
    if track is None:
        track = Track(slug=slug, title=f"Track {slug}", is_topic=True)
        session.add(track)
        await session.flush()
    return track


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    await _ensure_test_database()
    # NullPool: every connection is closed the moment it is released, so no
    # connection outlives the test that opened it. With a pooled engine a
    # connection from the previous test could still be holding a row lock while
    # this test's `drop_all` asks for an AccessExclusiveLock on the same table -
    # Postgres reports that as a deadlock, and it surfaces as a fixture error in
    # an unrelated test. It only started happening once track_enrollments made
    # the schema wide enough to widen that window.
    engine = create_async_engine(_test_url(), poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        yield db

    await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(session: AsyncSession) -> User:
    user = User(
        email="admin@test.local",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Test Admin",
        role=UserRole.ADMIN.value,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_user(session: AsyncSession) -> User:
    user = User(
        email="student@test.local",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Test Student",
        role=UserRole.STUDENT.value,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_client(
    client: AsyncClient, student_user: User
) -> AsyncGenerator[AsyncClient, None]:
    """A signed-in student.

    Reading content needs an account now that the platform is closed, so the
    tests that only care about *what* an endpoint returns use this and leave the
    bare `client` to the tests that are specifically about being anonymous.
    """
    token = await login(client, "student@test.local", "StudentPass123!")
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_header(token)
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_client(
    client: AsyncClient, admin_user: User
) -> AsyncGenerator[AsyncClient, None]:
    token = await login(client, "admin@test.local", "AdminPass123!")
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_header(token)
    ) as ac:
        yield ac


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
