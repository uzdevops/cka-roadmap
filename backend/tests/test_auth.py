"""Authentication flow: register -> login -> me -> refresh, plus role checks."""

from __future__ import annotations

from httpx import AsyncClient

from app.config import settings
from tests.conftest import auth_header, login

API = settings.api_v1_prefix


async def test_register_returns_token_pair(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": "new@example.com",
            "password": "SuperSecret1!",
            "full_name": "New Learner",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dupe@example.com", "password": "SuperSecret1!"}
    first = await client.post(f"{API}/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post(f"{API}/auth/register", json=payload)
    assert second.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/register", json={"email": "short@example.com", "password": "abc"}
    )
    assert resp.status_code == 422


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
        json={"full_name": "Renamed", "target_exam_date": "2026-06-01",
              "daily_study_minutes": 120},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Renamed"
    assert body["target_exam_date"] == "2026-06-01"
    assert body["daily_study_minutes"] == 120


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
