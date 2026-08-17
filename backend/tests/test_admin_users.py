"""Admin user management.

Self-registration is closed, so these endpoints are the only way an account is
created - which also makes them the only place the "do not lock yourself out"
rules can live.
"""

from __future__ import annotations

from httpx import AsyncClient

from app.config import settings
from app.models import Lesson, Phase, Week

API = settings.api_v1_prefix


async def _seed_one_lesson(session) -> None:
    phase = Phase(slug="p1", title="Phase 1", description="", order_index=0,
                  exam_weight=10, week_start=1, week_end=1)
    session.add(phase)
    await session.flush()
    week = Week(phase_id=phase.id, number=1, title="Week 1", description="", order_index=0)
    session.add(week)
    await session.flush()
    session.add(Lesson(week_id=week.id, slug="l1", title="Lesson", summary="",
                       content="body", order_index=0, estimated_minutes=10,
                       is_published=True, is_placeholder=False))
    await session.commit()


async def test_student_cannot_reach_user_admin(student_client: AsyncClient) -> None:
    assert (await student_client.get(f"{API}/admin/users")).status_code == 403


async def test_anonymous_cannot_reach_user_admin(client: AsyncClient) -> None:
    assert (await client.get(f"{API}/admin/users")).status_code == 401


async def test_create_list_and_delete_a_user(
    admin_client: AsyncClient, session
) -> None:
    await _seed_one_lesson(session)

    created = await admin_client.post(
        f"{API}/admin/users",
        json={"email": "New@Example.com", "password": "LearnerPass1!",
              "full_name": "New Learner", "role": "student"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["email"] == "new@example.com"  # normalised
    assert body["role"] == "student"
    assert body["total_lessons"] == 1
    user_id = body["id"]

    listed = await admin_client.get(f"{API}/admin/users")
    assert listed.status_code == 200
    emails = [u["email"] for u in listed.json()]
    assert "new@example.com" in emails

    row = next(u for u in listed.json() if u["id"] == user_id)
    assert row["completed_lessons"] == 0
    assert row["quiz_average"] is None
    assert row["progress_percent"] == 0.0

    assert (await admin_client.delete(f"{API}/admin/users/{user_id}")).status_code == 204
    after = await admin_client.get(f"{API}/admin/users")
    assert user_id not in [u["id"] for u in after.json()]


async def test_duplicate_email_is_rejected(admin_client: AsyncClient) -> None:
    payload = {"email": "dupe@example.com", "password": "LearnerPass1!"}
    assert (await admin_client.post(f"{API}/admin/users", json=payload)).status_code == 201
    assert (await admin_client.post(f"{API}/admin/users", json=payload)).status_code == 409


async def test_short_password_is_rejected(admin_client: AsyncClient) -> None:
    resp = await admin_client.post(
        f"{API}/admin/users", json={"email": "short@example.com", "password": "abc"}
    )
    assert resp.status_code == 422


async def test_created_user_can_sign_in(
    admin_client: AsyncClient, client: AsyncClient
) -> None:
    await admin_client.post(
        f"{API}/admin/users",
        json={"email": "signin@example.com", "password": "LearnerPass1!"},
    )
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": "signin@example.com", "password": "LearnerPass1!"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_admin_cannot_delete_or_demote_themselves(
    admin_client: AsyncClient, admin_user
) -> None:
    assert (
        await admin_client.delete(f"{API}/admin/users/{admin_user.id}")
    ).status_code == 400
    assert (
        await admin_client.patch(
            f"{API}/admin/users/{admin_user.id}", json={"role": "student"}
        )
    ).status_code == 400
    assert (
        await admin_client.patch(
            f"{API}/admin/users/{admin_user.id}", json={"is_active": False}
        )
    ).status_code == 400


async def test_password_reset_takes_effect(
    admin_client: AsyncClient, client: AsyncClient
) -> None:
    created = await admin_client.post(
        f"{API}/admin/users",
        json={"email": "reset@example.com", "password": "OldPassword1!"},
    )
    user_id = created.json()["id"]

    assert (
        await admin_client.patch(
            f"{API}/admin/users/{user_id}", json={"password": "BrandNewPass1!"}
        )
    ).status_code == 200

    old = await client.post(
        f"{API}/auth/login",
        json={"email": "reset@example.com", "password": "OldPassword1!"},
    )
    assert old.status_code == 401
    new = await client.post(
        f"{API}/auth/login",
        json={"email": "reset@example.com", "password": "BrandNewPass1!"},
    )
    assert new.status_code == 200


async def test_deactivated_user_cannot_sign_in(
    admin_client: AsyncClient, client: AsyncClient
) -> None:
    created = await admin_client.post(
        f"{API}/admin/users",
        json={"email": "off@example.com", "password": "LearnerPass1!"},
    )
    user_id = created.json()["id"]
    await admin_client.patch(f"{API}/admin/users/{user_id}", json={"is_active": False})

    resp = await client.post(
        f"{API}/auth/login",
        json={"email": "off@example.com", "password": "LearnerPass1!"},
    )
    # 403, not 401: the credentials were correct, the account is switched off.
    assert resp.status_code == 403
    assert "disabled" in resp.json()["detail"].lower()
