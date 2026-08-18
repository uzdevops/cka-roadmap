"""Who may open which track.

Access is two independent grants, not one role, because the content categories
overlap: a track can be a topic, a certificate, or both. The interesting case is
that overlap - CKA is both, so it has to be reachable by a student granted only
topics AND by a student granted only certificates. A model that stored one role
name could not express that without duplicating the content.

The four names the product uses are derived from the pair and asserted here, so
renaming a role stays a code change rather than a data migration.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Track, User, UserRole
from app.security import hash_password
from tests.conftest import auth_header, login

API = settings.api_v1_prefix
PASSWORD = "grant-test-password"

# slug, is_topic, is_certificate
TRACKS = [
    ("docker", True, False),    # topic only
    ("cks", False, True),       # certificate only
    ("cka", True, True),        # both - the case the two-flag model exists for
]


@pytest.fixture
async def tracks(session: AsyncSession) -> None:
    for order, (slug, is_topic, is_cert) in enumerate(TRACKS):
        session.add(
            Track(
                slug=slug,
                title=slug.upper(),
                is_topic=is_topic,
                is_certificate=is_cert,
                order_index=order,
            )
        )
    await session.commit()


async def _make(
    session: AsyncSession, username: str, *, topics: bool, certs: bool,
    admin: bool = False,
) -> User:
    user = User(
        email=f"{username}@example.com",
        username=username,
        hashed_password=hash_password(PASSWORD),
        full_name=username,
        role=UserRole.ADMIN.value if admin else UserRole.STUDENT.value,
        is_active=True,
        access_topics=topics,
        access_certificates=certs,
    )
    session.add(user)
    await session.commit()
    return user


async def _client_for(client: AsyncClient, username: str) -> dict[str, str]:
    token = await login(client, username, PASSWORD)
    return auth_header(token)


# --- the derived names ------------------------------------------------------


@pytest.mark.parametrize(
    "topics,certs,admin,expected",
    [
        (True, False, False, "DevOps Student"),
        (False, True, False, "Certificate Student"),
        (True, True, False, "Full Student"),
        (True, True, True, "Administrator"),
        (False, False, False, "No access"),
    ],
)
async def test_role_label_is_derived_from_the_grants(
    session: AsyncSession, topics: bool, certs: bool, admin: bool, expected: str
) -> None:
    user = await _make(
        session, f"u{topics}{certs}{admin}", topics=topics, certs=certs, admin=admin
    )
    assert user.role_label == expected


# --- what /tracks offers ----------------------------------------------------


@pytest.mark.parametrize(
    "topics,certs,visible",
    [
        (True, False, {"docker", "cka"}),
        (False, True, {"cks", "cka"}),
        (True, True, {"docker", "cks", "cka"}),
    ],
    ids=["devops student", "certificate student", "full student"],
)
async def test_track_list_shows_only_what_the_account_may_open(
    session: AsyncSession, client: AsyncClient, tracks: None,
    topics: bool, certs: bool, visible: set[str],
) -> None:
    """The switcher must not offer a choice the API would then refuse."""
    name = f"s{int(topics)}{int(certs)}"
    await _make(session, name, topics=topics, certs=certs)

    response = await client.get(f"{API}/tracks", headers=await _client_for(client, name))
    assert response.status_code == 200, response.text
    assert {t["slug"] for t in response.json()} == visible


async def test_a_dual_nature_track_is_visible_to_both_kinds_of_student(
    session: AsyncSession, client: AsyncClient, tracks: None
) -> None:
    """CKA is a topic AND a certificate. This is the whole reason the model uses
    two flags instead of one type field."""
    await _make(session, "topicsonly", topics=True, certs=False)
    await _make(session, "certsonly", topics=False, certs=True)

    for name in ("topicsonly", "certsonly"):
        response = await client.get(
            f"{API}/tracks", headers=await _client_for(client, name)
        )
        assert "cka" in {t["slug"] for t in response.json()}, name


async def test_admin_sees_every_track(
    session: AsyncSession, client: AsyncClient, tracks: None
) -> None:
    await _make(session, "boss", topics=False, certs=False, admin=True)
    response = await client.get(f"{API}/tracks", headers=await _client_for(client, "boss"))
    assert {t["slug"] for t in response.json()} == {"docker", "cks", "cka"}


# --- enforcement, not just presentation -------------------------------------


async def test_asking_for_a_forbidden_track_is_refused(
    session: AsyncSession, client: AsyncClient, tracks: None
) -> None:
    """Hiding it from the list is not access control - the API has to refuse."""
    await _make(session, "devops", topics=True, certs=False)
    headers = await _client_for(client, "devops")

    allowed = await client.get(f"{API}/lessons", params={"track": "docker"}, headers=headers)
    assert allowed.status_code == 200

    refused = await client.get(f"{API}/lessons", params={"track": "cks"}, headers=headers)
    assert refused.status_code == 403, refused.text


async def test_the_default_track_respects_the_grants(
    session: AsyncSession, client: AsyncClient, tracks: None
) -> None:
    """With no ?track=, the fallback must not hand back a forbidden track.

    `cks` sorts before `cka`, so a certificate-only student's default is cks
    while a topics-only student's is docker - neither may be the other's.
    """
    await _make(session, "certs", topics=False, certs=True)
    response = await client.get(
        f"{API}/tracks", headers=await _client_for(client, "certs")
    )
    assert response.json()[0]["slug"] == "cks"

    await _make(session, "topics", topics=True, certs=False)
    response = await client.get(
        f"{API}/tracks", headers=await _client_for(client, "topics")
    )
    assert response.json()[0]["slug"] == "docker"


async def test_an_account_with_no_grants_reaches_no_content(
    session: AsyncSession, client: AsyncClient, tracks: None
) -> None:
    await _make(session, "nobody", topics=False, certs=False)
    headers = await _client_for(client, "nobody")

    listing = await client.get(f"{API}/tracks", headers=headers)
    assert listing.json() == []

    refused = await client.get(f"{API}/lessons", params={"track": "cka"}, headers=headers)
    assert refused.status_code == 403


# --- the admin surface ------------------------------------------------------


async def test_admin_can_set_the_grants_and_the_label_follows(
    session: AsyncSession, admin_client: AsyncClient, tracks: None
) -> None:
    created = await admin_client.post(
        f"{API}/admin/users",
        json={
            "email": "new@example.com",
            "username": "newbie",
            "password": "a-real-password",
            "full_name": "New Student",
            "access_topics": True,
            "access_certificates": False,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["access_topics"] is True
    assert body["access_certificates"] is False
    assert body["role_label"] == "DevOps Student"

    patched = await admin_client.patch(
        f"{API}/admin/users/{body['id']}", json={"access_certificates": True}
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["role_label"] == "Full Student"


async def test_admin_can_deactivate_an_account(
    session: AsyncSession, admin_client: AsyncClient, client: AsyncClient
) -> None:
    user = await _make(session, "temp", topics=True, certs=True)

    patched = await admin_client.patch(
        f"{API}/admin/users/{user.id}", json={"is_active": False}
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["is_active"] is False

    denied = await client.post(
        f"{API}/auth/login", json={"identifier": "temp", "password": PASSWORD}
    )
    assert denied.status_code == 403, denied.text
