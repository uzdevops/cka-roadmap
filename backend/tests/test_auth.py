"""Authentication flow: register -> login -> me -> refresh, plus role checks."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from tests.conftest import auth_header, login

API = settings.api_v1_prefix


async def test_registration_is_closed(client: AsyncClient) -> None:
    """Self-registration was removed; accounts come from an administrator."""
    resp = await client.post(
        f"{API}/auth/register",
        json={"email": "new@example.com", "password": "SuperSecret1!"},
    )
    assert resp.status_code == 403
    assert "administrator" in resp.json()["detail"].lower()


async def test_auth_config_advertises_that_registration_is_off(
    client: AsyncClient,
) -> None:
    """The login page hides its sign-up link from this flag."""
    resp = await client.get(f"{API}/auth/config")
    assert resp.status_code == 200
    assert resp.json()["registration_enabled"] is False


async def test_login_and_fetch_profile(client: AsyncClient, student_user) -> None:
    token = await login(client, "student@test.local", "StudentPass123!")

    resp = await client.get(f"{API}/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "student@test.local"
    assert body["role"] == "student"


async def test_login_with_wrong_password_is_401(client: AsyncClient, student_user) -> None:
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": "student@test.local", "password": "definitely-wrong"},
    )
    assert resp.status_code == 401


async def test_me_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(f"{API}/auth/me")).status_code == 401
    resp = await client.get(f"{API}/auth/me", headers=auth_header("not-a-real-jwt"))
    assert resp.status_code == 401


async def test_refresh_issues_new_access_token(client: AsyncClient, student_user) -> None:
    login_resp = await client.post(
        f"{API}/auth/login",
        json={"email": "student@test.local", "password": "StudentPass123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post(f"{API}/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_access_token_is_rejected_by_refresh(client: AsyncClient, student_user) -> None:
    """A refresh endpoint that accepts access tokens defeats the split."""
    access = await login(client, "student@test.local", "StudentPass123!")
    resp = await client.post(f"{API}/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


async def test_profile_update_persists(client: AsyncClient, student_user) -> None:
    token = await login(client, "student@test.local", "StudentPass123!")
    resp = await client.patch(
        f"{API}/auth/me",
        headers=auth_header(token),
        json={"full_name": "Renamed", "daily_study_minutes": 120},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Renamed"
    assert body["daily_study_minutes"] == 120


async def test_the_profile_no_longer_carries_an_exam_date(
    client: AsyncClient, student_user
) -> None:
    """It moved to the enrollment.

    One column on the account could only ever describe one exam; somebody
    studying CKA and LFCS at the same time needs a date for each. It is set
    through PATCH /tracks/{slug}/enrollment now, and the daily study budget
    stays on the account because that is about the person, not the track.
    """
    token = await login(client, "student@test.local", "StudentPass123!")

    resp = await client.get(f"{API}/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert "target_exam_date" not in resp.json()
    assert "daily_study_minutes" in resp.json()

    # Sending it is silently ignored rather than accepted and dropped, because
    # the field is not on the update schema at all.
    patched = await client.patch(
        f"{API}/auth/me",
        headers=auth_header(token),
        json={"target_exam_date": "2026-06-01"},
    )
    assert patched.status_code == 200
    assert "target_exam_date" not in patched.json()


async def test_admin_endpoints_reject_students(client: AsyncClient, student_user) -> None:
    token = await login(client, "student@test.local", "StudentPass123!")
    resp = await client.get(f"{API}/admin/stats", headers=auth_header(token))
    assert resp.status_code == 403


async def test_admin_endpoints_accept_admins(client: AsyncClient, admin_user) -> None:
    token = await login(client, "admin@test.local", "AdminPass123!")
    resp = await client.get(f"{API}/admin/stats", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["admins"] >= 1


async def test_auth_config_reports_oauth_state(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/auth/config")
    assert resp.status_code == 200
    # No Google credentials are configured in the test environment.
    assert resp.json()["google_oauth_enabled"] is False


async def test_google_authorize_404s_when_unconfigured(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/auth/google/authorize")
    assert resp.status_code == 404


# --- The platform is closed ----------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/roadmap",
        "/roadmap/phases",
        "/lessons",
        "/quizzes",
        "/labs",
    ],
)
async def test_content_requires_authentication(client: AsyncClient, path: str) -> None:
    """Hiding the UI is not access control - the API has to refuse too."""
    resp = await client.get(f"{API}{path}")
    assert resp.status_code == 401, f"{path} served content to an anonymous caller"


async def test_content_is_served_once_signed_in(student_client: AsyncClient) -> None:
    resp = await student_client.get(f"{API}/roadmap/phases")
    assert resp.status_code == 200
