"""Signing in with `admin`, not only with `admin@somewhere`.

The sign-in field used to be an `EmailStr`, so a bare username was rejected with
a 422 before the request ever reached the password check. It now takes either,
under any of three keys, so older clients that post `{"email": ...}` keep
working.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, UserRole
from app.security import hash_password

API = settings.api_v1_prefix
PASSWORD = "s3cret-password"


@pytest.fixture
async def person(session: AsyncSession) -> User:
    user = User(
        email="Someone@Example.COM",
        username="someone",
        hashed_password=hash_password(PASSWORD),
        full_name="Someone",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    return user


@pytest.mark.parametrize(
    "key", ["identifier", "email", "username"],
    ids=["identifier key", "legacy email key", "username key"],
)
async def test_username_is_accepted_under_every_key(
    client: AsyncClient, person: User, key: str
) -> None:
    response = await client.post(
        f"{API}/auth/login", json={key: "someone", "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


async def test_email_still_works(client: AsyncClient, person: User) -> None:
    response = await client.post(
        f"{API}/auth/login",
        json={"identifier": "someone@example.com", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text


async def test_identifier_is_case_insensitive(client: AsyncClient, person: User) -> None:
    """The row was stored with mixed case; typing it in caps must still match."""
    for value in ("SOMEONE", "Someone@Example.com"):
        response = await client.post(
            f"{API}/auth/login", json={"identifier": value, "password": PASSWORD}
        )
        assert response.status_code == 200, f"{value}: {response.text}"


async def test_a_username_that_does_not_exist_is_401_not_422(
    client: AsyncClient, person: User
) -> None:
    """A bare word used to fail schema validation before reaching the lookup.

    422 leaks that the input was not even considered; 401 is the honest answer
    and matches what a wrong password returns.
    """
    response = await client.post(
        f"{API}/auth/login", json={"identifier": "nobody", "password": PASSWORD}
    )
    assert response.status_code == 401, response.text


async def test_wrong_password_is_rejected(client: AsyncClient, person: User) -> None:
    response = await client.post(
        f"{API}/auth/login", json={"identifier": "someone", "password": "wrong"}
    )
    assert response.status_code == 401


async def test_empty_identifier_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/auth/login", json={"identifier": "", "password": PASSWORD}
    )
    assert response.status_code == 422


async def test_seeded_admin_signs_in_with_the_configured_username(
    session: AsyncSession, client: AsyncClient
) -> None:
    """What a fresh checkout is expected to do: sign in as admin / 123."""
    session.add(
        User(
            email=settings.demo_admin_email,
            username=settings.demo_admin_username,
            hashed_password=hash_password(settings.demo_admin_password),
            full_name="Demo Admin",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
    )
    await session.commit()

    response = await client.post(
        f"{API}/auth/login",
        json={
            "identifier": settings.demo_admin_username,
            "password": settings.demo_admin_password,
        },
    )
    assert response.status_code == 200, response.text

    me = await client.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert me.json()["role"] == UserRole.ADMIN.value
    assert me.json()["username"] == settings.demo_admin_username
