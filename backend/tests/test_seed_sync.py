"""The seed keeps STRUCTURE in sync and leaves AUTHORED content alone.

A rewritten phases.json has to move lessons, weeks and quizzes to where the
file now says they live - otherwise the old roadmap stays standing next to
the new one - while never touching the body of a lesson somebody has
written or edited, and never deleting anything that still holds data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lab, Lesson, Phase, Quiz, Track, Week
from app.seed import Counter, TrackContent, seed_track


def _write(root: Path, phases: list[dict]) -> TrackContent:
    root.mkdir(parents=True, exist_ok=True)
    (root / "phases.json").write_text(json.dumps({"phases": phases}), encoding="utf-8")
    return TrackContent(root)


def _lesson(slug: str, day: int = 1) -> dict:
    return {"slug": slug, "title": f"Lesson {slug}", "summary": "s", "day_of_week": day}


def _phase(slug: str, order: int, start: int, end: int, weeks: list[dict]) -> dict:
    return {
        "slug": slug, "title": f"Phase {slug}", "description": "d", "order_index": order,
        "exam_domain": "x", "exam_weight": 10, "week_start": start, "week_end": end,
        "color": "sky", "weeks": weeks,
    }


def _week(number: int, lessons: list[dict]) -> dict:
    return {"number": number, "title": f"Week {number}", "description": "", "lessons": lessons}


@pytest.fixture
async def track(session: AsyncSession) -> Track:
    t = Track(slug="t-seed", title="Seed track", is_topic=True)
    session.add(t)
    await session.commit()
    return t


async def _seed(session: AsyncSession, track: Track, content: TrackContent) -> Counter:
    counter = Counter()
    await seed_track(session, counter, track, content)
    return counter


async def test_moved_lessons_move_and_empty_phases_are_pruned(
    session: AsyncSession, track: Track, tmp_path: Path
) -> None:
    # Two phases, two weeks, one lesson each; a quiz and a lab hang off week 2.
    content = _write(tmp_path / "v1", [
        _phase("one", 1, 1, 1, [_week(1, [_lesson("a")])]),
        _phase("two", 2, 2, 2, [_week(2, [_lesson("b", day=3)])]),
    ])
    (content.quiz_dir / "weeks").mkdir(parents=True)
    (content.quiz_dir / "weeks" / "w2.json").write_text(json.dumps({
        "slug": "w2-review", "phase_slug": "two", "week_number": 2, "title": "W2",
        "questions": [{"key": "q1", "type": "single_choice", "prompt": "?",
                       "options": [{"id": "a", "text": "a"}], "correct_options": ["a"]}],
    }))
    content.lab_dir.mkdir()
    (content.lab_dir / "lab.json").write_text(json.dumps({
        "slug": "lab-b", "phase_slug": "two", "week_number": 2, "title": "Lab", "tasks": [],
    }))
    await _seed(session, track, content)

    # The file is rewritten: phase "two" is gone, lesson b now lives in week 1
    # of phase "one" on Friday, and the quiz and lab follow it.
    content = _write(tmp_path / "v2", [
        _phase("one", 1, 1, 1, [_week(1, [_lesson("a"), _lesson("b", day=5)])]),
    ])
    (content.quiz_dir / "weeks").mkdir(parents=True)
    (content.quiz_dir / "weeks" / "w2.json").write_text(json.dumps({
        "slug": "w2-review", "phase_slug": "one", "week_number": 1, "title": "W2",
        "questions": [],
    }))
    content.lab_dir.mkdir()
    (content.lab_dir / "lab.json").write_text(json.dumps({
        "slug": "lab-b", "phase_slug": "one", "week_number": 1, "title": "Lab", "tasks": [],
    }))
    counter = await _seed(session, track, content)

    b = (await session.execute(select(Lesson).where(Lesson.slug == "b"))).scalar_one()
    week1 = (await session.execute(
        select(Week).where(Week.track_id == track.id, Week.number == 1)
    )).scalar_one()
    assert b.week_id == week1.id
    assert b.day_of_week == 5
    assert b.order_index == 2

    phases = (await session.execute(
        select(Phase.slug).where(Phase.track_id == track.id)
    )).scalars().all()
    assert phases == ["one"], "the phase the file dropped should be gone"
    weeks = (await session.execute(
        select(Week.number).where(Week.track_id == track.id)
    )).scalars().all()
    assert weeks == [1]

    quiz = (await session.execute(select(Quiz).where(Quiz.slug == "w2-review"))).scalar_one()
    lab = (await session.execute(select(Lab).where(Lab.slug == "lab-b"))).scalar_one()
    assert quiz.week_id == week1.id and lab.week_id == week1.id
    assert counter.removed == {"phases": 1, "weeks": 1}


async def test_authored_content_is_never_overwritten_but_placeholders_follow(
    session: AsyncSession, track: Track, tmp_path: Path
) -> None:
    content = _write(tmp_path / "v1", [
        _phase("one", 1, 1, 1, [_week(1, [_lesson("written"), _lesson("blank")])]),
    ])
    content.lesson_dir.mkdir()
    (content.lesson_dir / "written.md").write_text("# real prose")
    await _seed(session, track, content)

    written = (await session.execute(select(Lesson).where(Lesson.slug == "written"))).scalar_one()
    blank = (await session.execute(select(Lesson).where(Lesson.slug == "blank"))).scalar_one()
    assert not written.is_placeholder and blank.is_placeholder

    # An admin edits both titles and the written body; the file then renames both.
    written.title = "Edited by hand"
    written.content = "# edited prose"
    blank.title = "Edited placeholder"
    await session.commit()

    phases = [_phase("one", 1, 1, 1, [_week(1, [
        {**_lesson("written"), "title": "Renamed in file"},
        {**_lesson("blank"), "title": "Renamed placeholder", "summary": "new"},
    ])])]
    content = _write(tmp_path / "v2", phases)
    content.lesson_dir.mkdir()
    (content.lesson_dir / "written.md").write_text("# real prose")
    await _seed(session, track, content)
    await session.refresh(written)
    await session.refresh(blank)

    assert written.title == "Edited by hand"
    assert written.content == "# edited prose"
    # Still a placeholder, so still the seed's to describe.
    assert blank.title == "Renamed placeholder"
    assert blank.summary == "new"


async def test_a_week_that_still_holds_a_forgotten_lesson_is_kept(
    session: AsyncSession, track: Track, tmp_path: Path
) -> None:
    """Pruning never destroys data: a lesson the file forgot keeps its week."""
    content = _write(tmp_path / "v1", [
        _phase("one", 1, 1, 2, [_week(1, [_lesson("a")]), _week(2, [_lesson("b")])]),
    ])
    await _seed(session, track, content)

    content = _write(tmp_path / "v2", [
        _phase("one", 1, 1, 1, [_week(1, [_lesson("a")])]),
    ])
    counter = await _seed(session, track, content)

    weeks = (await session.execute(
        select(Week.number).where(Week.track_id == track.id).order_by(Week.number)
    )).scalars().all()
    assert weeks == [1, 2]
    assert counter.removed == {}
    b = (await session.execute(select(Lesson).where(Lesson.slug == "b"))).scalar_one()
    assert b is not None


async def test_a_stale_uz_placeholder_is_dropped_once_the_body_is_written(
    session: AsyncSession, track: Track, tmp_path: Path
) -> None:
    """Once English prose exists, the Uzbek side must stop saying "not yet"."""
    content = _write(tmp_path / "v1", [_phase("one", 1, 1, 1, [_week(1, [_lesson("late")])])])
    (content.i18n_dir / "uz").mkdir(parents=True)
    (content.i18n_dir / "uz" / "structure.json").write_text(json.dumps({
        "locale": "uz", "phases": {}, "weeks": {}, "lessons": {"late": {"title": "Kech", "summary": "x"}},
    }))
    await _seed(session, track, content)
    late = (await session.execute(select(Lesson).where(Lesson.slug == "late"))).scalar_one()
    assert late.is_placeholder
    assert "Bu dars hali to'liq yozilmagan" in late.translations["uz"]["content"]

    # The English body arrives; no Uzbek body does.
    content = _write(tmp_path / "v2", [_phase("one", 1, 1, 1, [_week(1, [_lesson("late")])])])
    content.lesson_dir.mkdir()
    (content.lesson_dir / "late.md").write_text("# written at last")
    (content.i18n_dir / "uz").mkdir(parents=True)
    (content.i18n_dir / "uz" / "structure.json").write_text(json.dumps({
        "locale": "uz", "phases": {}, "weeks": {}, "lessons": {"late": {"title": "Kech", "summary": "x"}},
    }))
    await _seed(session, track, content)
    await session.refresh(late)

    assert not late.is_placeholder
    assert "content" not in late.translations["uz"], "stale placeholder kept"
    assert late.translations["uz"]["title"] == "Kech"
