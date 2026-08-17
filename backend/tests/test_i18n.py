"""Content localisation: negotiation, per-field fallback, and the API surface."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from app.i18n import (
    DEFAULT_LOCALE,
    normalize_locale,
    pick_locale,
    tr,
    verdict,
    weekday,
)
from app.models import Lesson, Phase, Question, Quiz, Week

API = settings.api_v1_prefix


# --- Pure functions ------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("uz", "uz"),
        ("UZ", "uz"),
        ("uz-UZ", "uz"),
        ("uz_Latn", "uz"),
        ("en", "en"),
        ("fr", "en"),      # unsupported falls back
        ("", "en"),
        (None, "en"),
    ],
)
def test_normalize_locale(raw, expected) -> None:
    assert normalize_locale(raw) == expected


def test_accept_language_negotiation() -> None:
    assert pick_locale("uz-UZ,uz;q=0.9,en;q=0.8") == "uz"
    assert pick_locale("en-GB,en;q=0.9") == "en"
    assert pick_locale("de-DE,fr;q=0.7") == "en"
    assert pick_locale(None) == "en"


def test_tr_falls_back_per_field() -> None:
    lesson = Lesson(
        slug="x",
        title="English title",
        summary="English summary",
        content="English body",
        translations={"uz": {"title": "O'zbekcha sarlavha", "summary": "   "}},
    )
    assert tr(lesson, "title", "uz") == "O'zbekcha sarlavha"
    # Whitespace-only counts as untranslated, so English still shows.
    assert tr(lesson, "summary", "uz") == "English summary"
    assert tr(lesson, "content", "uz") == "English body"
    # The default locale never consults the translations bucket.
    assert tr(lesson, "title", "en") == "English title"


def test_tr_handles_missing_locale_and_empty_translations() -> None:
    lesson = Lesson(slug="x", title="T", summary="", content="", translations={})
    assert tr(lesson, "title", "uz") == "T"
    lesson.translations = None
    assert tr(lesson, "title", "uz") == "T"


def test_server_generated_strings_are_translated() -> None:
    assert verdict("ready", "en") != verdict("ready", "uz")
    assert weekday(1, "uz") == "Dushanba"
    assert weekday(1, "en") == "Monday"
    # Unknown locale degrades to English rather than raising.
    assert weekday(1, "de") == "Monday"


# --- Through the API -----------------------------------------------------


async def _seed(session) -> None:
    phase = Phase(
        slug="p1",
        title="Phase 1 - Foundations",
        description="English description",
        order_index=1,
        exam_weight=0,
        week_start=1,
        week_end=1,
        translations={"uz": {"title": "1-bosqich - Asoslar"}},
    )
    session.add(phase)
    await session.flush()

    week = Week(
        phase_id=phase.id,
        number=1,
        title="Week 1",
        order_index=1,
        translations={"uz": {"title": "1-hafta"}},
    )
    session.add(week)
    await session.flush()

    session.add_all(
        [
            Lesson(
                week_id=week.id,
                slug="translated",
                title="Translated lesson",
                summary="English summary",
                content="# English body",
                order_index=1,
                translations={
                    "uz": {
                        "title": "Tarjima qilingan dars",
                        "summary": "O'zbekcha xulosa",
                        "content": "# O'zbekcha matn",
                    }
                },
            ),
            Lesson(
                week_id=week.id,
                slug="untranslated",
                title="Untranslated lesson",
                summary="English only",
                content="# English body only",
                order_index=2,
            ),
        ]
    )

    quiz = Quiz(
        phase_id=phase.id,
        slug="q1",
        title="English quiz",
        description="",
        order_index=1,
        translations={"uz": {"title": "O'zbekcha test"}},
    )
    session.add(quiz)
    await session.flush()
    session.add(
        Question(
            quiz_id=quiz.id,
            key="k1",
            type="single_choice",
            prompt="English prompt",
            options=[{"id": "a", "text": "English option"}],
            correct_options=["a"],
            explanation="English explanation",
            points=1,
            order_index=1,
            translations={
                "uz": {
                    "prompt": "O'zbekcha savol",
                    "options": [{"id": "a", "text": "O'zbekcha variant"}],
                }
            },
        )
    )
    await session.commit()


async def test_lesson_is_served_in_the_requested_locale(
    client: AsyncClient, session
) -> None:
    await _seed(session)

    uz = (await client.get(f"{API}/lessons/translated?lang=uz")).json()
    assert uz["title"] == "Tarjima qilingan dars"
    assert uz["content"] == "# O'zbekcha matn"
    assert uz["content_translated"] is True
    assert uz["phase_title"] == "1-bosqich - Asoslar"

    en = (await client.get(f"{API}/lessons/translated")).json()
    assert en["title"] == "Translated lesson"
    assert en["content"] == "# English body"


async def test_untranslated_lesson_falls_back_and_is_flagged(
    client: AsyncClient, session
) -> None:
    await _seed(session)

    uz = (await client.get(f"{API}/lessons/untranslated?lang=uz")).json()
    assert uz["title"] == "Untranslated lesson"
    assert uz["content"] == "# English body only"
    # The flag lets the UI tell the reader the body is still English.
    assert uz["content_translated"] is False


async def test_accept_language_header_selects_the_locale(
    client: AsyncClient, session
) -> None:
    await _seed(session)
    resp = await client.get(
        f"{API}/lessons/translated", headers={"Accept-Language": "uz-UZ,uz;q=0.9"}
    )
    assert resp.json()["title"] == "Tarjima qilingan dars"


async def test_explicit_lang_beats_accept_language(
    client: AsyncClient, session
) -> None:
    await _seed(session)
    resp = await client.get(
        f"{API}/lessons/translated?lang=en", headers={"Accept-Language": "uz"}
    )
    assert resp.json()["title"] == "Translated lesson"


async def test_unsupported_locale_serves_english(client: AsyncClient, session) -> None:
    await _seed(session)
    resp = await client.get(f"{API}/lessons/translated?lang=klingon")
    assert resp.json()["title"] == "Translated lesson"


async def test_roadmap_and_phase_are_localised(client: AsyncClient, session) -> None:
    await _seed(session)

    phases = (await client.get(f"{API}/roadmap/phases?lang=uz")).json()
    assert phases[0]["title"] == "1-bosqich - Asoslar"
    # description has no Uzbek override, so English shows through.
    assert phases[0]["description"] == "English description"

    detail = (await client.get(f"{API}/roadmap/phases/p1?lang=uz")).json()
    assert detail["weeks"][0]["title"] == "1-hafta"
    assert detail["weeks"][0]["lessons"][0]["title"] == "Tarjima qilingan dars"


async def test_quiz_prompt_and_options_are_localised(
    client: AsyncClient, session
) -> None:
    await _seed(session)

    uz = (await client.get(f"{API}/quizzes/q1?lang=uz")).json()
    assert uz["title"] == "O'zbekcha test"
    question = uz["questions"][0]
    assert question["prompt"] == "O'zbekcha savol"
    assert question["options"][0]["text"] == "O'zbekcha variant"
    # Option ids are the answer key and must never be translated.
    assert question["options"][0]["id"] == "a"


async def test_grading_is_locale_independent(
    client: AsyncClient, session, student_user
) -> None:
    """Translating a quiz must not change which answers are correct."""
    from tests.conftest import auth_header, login

    await _seed(session)
    token = await login(client, "student@test.local", "StudentPass123!")
    quiz = (await client.get(f"{API}/quizzes/q1?lang=uz")).json()
    question_id = quiz["questions"][0]["id"]

    resp = await client.post(
        f"{API}/quizzes/q1/submit?lang=uz",
        headers=auth_header(token),
        json={"answers": [{"question_id": question_id, "selected_options": ["a"]}]},
    )
    body = resp.json()
    assert body["score"] == 100.0
    assert body["results"][0]["prompt"] == "O'zbekcha savol"
    # No Uzbek explanation was supplied, so English comes through.
    assert body["results"][0]["explanation"] == "English explanation"


async def test_auth_config_advertises_locales(client: AsyncClient) -> None:
    body = (await client.get(f"{API}/auth/config")).json()
    assert set(body["locales"]) == {"en", "uz"}
    assert body["default_locale"] == DEFAULT_LOCALE
