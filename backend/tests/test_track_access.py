"""Per-track access: the allowlist overrides the category grants.

0007 gave a student two category checkboxes - "which KIND of student is this".
0012 adds the finer grain - "this person bought CKA and nothing else". NULL
keeps the categories in charge, which is what every pre-existing row has; a
list means exactly those tracks; an empty list means none at all.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from tests.conftest import auth_header, ensure_track, login

API = settings.api_v1_prefix
PASSWORD = "LearnerPass1!"


@pytest.fixture
async def two_tracks(session: AsyncSession) -> None:
    await ensure_track(session, "t1")
    await ensure_track(session, "t2")
    await session.commit()


async def _create_student(
    admin_client: AsyncClient, username: str, access_tracks: list[str] | None
) -> dict:
    resp = await admin_client.post(
        f"{API}/admin/users",
        json={
            "email": f"{username}@example.com",
            "username": username,
            "password": PASSWORD,
            "access_tracks": access_tracks,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _visible_slugs(client: AsyncClient, username: str) -> list[str]:
    token = await login(client, username, PASSWORD)
    resp = await client.get(f"{API}/tracks", headers=auth_header(token))
    assert resp.status_code == 200, resp.text
    return [t["slug"] for t in resp.json()]


async def test_allowlist_names_exactly_what_it_names(
    admin_client: AsyncClient, client: AsyncClient, two_tracks
) -> None:
    created = await _create_student(admin_client, "onetrack", ["t1"])
    assert created["access_tracks"] == ["t1"]
    assert created["role_label"] == "Custom Access"

    assert await _visible_slugs(client, "onetrack") == ["t1"]

    token = await login(client, "onetrack", PASSWORD)
    ok = await client.get(
        f"{API}/roadmap/phases", params={"track": "t1"}, headers=auth_header(token)
    )
    assert ok.status_code == 200, ok.text
    denied = await client.get(
        f"{API}/roadmap/phases", params={"track": "t2"}, headers=auth_header(token)
    )
    assert denied.status_code == 403, denied.text


async def test_slugs_are_normalised_on_the_way_in(
    admin_client: AsyncClient, two_tracks
) -> None:
    created = await _create_student(admin_client, "shouty", [" T1 ", "t1", "t2"])
    # Lowercased, trimmed, deduplicated - stored the way the lookup compares.
    assert created["access_tracks"] == ["t1", "t2"]


async def test_an_empty_allowlist_means_no_tracks(
    admin_client: AsyncClient, client: AsyncClient, two_tracks
) -> None:
    created = await _create_student(admin_client, "boxedout", [])
    assert created["role_label"] == "No access"
    assert await _visible_slugs(client, "boxedout") == []

    token = await login(client, "boxedout", PASSWORD)
    denied = await client.get(
        f"{API}/roadmap/phases", params={"track": "t1"}, headers=auth_header(token)
    )
    assert denied.status_code == 403


async def test_an_unknown_slug_is_refused_not_stored(
    admin_client: AsyncClient, two_tracks
) -> None:
    """Silently storing it would grant nothing while looking like a grant."""
    resp = await admin_client.post(
        f"{API}/admin/users",
        json={
            "email": "typo@example.com",
            "username": "typo",
            "password": PASSWORD,
            "access_tracks": ["t1", "nope"],
        },
    )
    assert resp.status_code == 400
    assert "nope" in resp.json()["detail"]


async def test_clearing_the_allowlist_hands_back_to_the_categories(
    admin_client: AsyncClient, client: AsyncClient, two_tracks
) -> None:
    created = await _create_student(admin_client, "restored", ["t1"])
    assert await _visible_slugs(client, "restored") == ["t1"]

    # An explicit null clears the list; the category grants (both default true,
    # and ensure_track makes topics) take over again.
    patched = await admin_client.patch(
        f"{API}/admin/users/{created['id']}", json={"access_tracks": None}
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["access_tracks"] is None
    assert patched.json()["role_label"] == "Full Student"

    assert await _visible_slugs(client, "restored") == ["t1", "t2"]


async def test_an_omitted_key_leaves_the_allowlist_alone(
    admin_client: AsyncClient, client: AsyncClient, two_tracks
) -> None:
    """PATCHing an unrelated field must not clear a restriction."""
    created = await _create_student(admin_client, "renamed", ["t1"])

    patched = await admin_client.patch(
        f"{API}/admin/users/{created['id']}", json={"full_name": "Still Limited"}
    )
    assert patched.status_code == 200
    assert patched.json()["access_tracks"] == ["t1"]

    assert await _visible_slugs(client, "renamed") == ["t1"]
