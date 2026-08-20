"""The shipped seed files actually seed.

test_seed_sync.py proves the seeder's rules on tiny fixtures; this proves the
real content under seed_data/tracks/ is internally consistent - every quiz and
lab names a phase and week that exist, every lesson slug is unique across
tracks, the Uzbek structure covers every lesson - by running it for real
against the test database and counting what came out.
"""

from __future__ import annotations

import json
import logging

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lab, Lesson, Phase, Quiz, Track, Week
from app.seed import TRACKS_DIR, Counter, TrackContent, seed_track, seed_tracks


def _content_tracks() -> list[str]:
    return sorted(p.name for p in TRACKS_DIR.iterdir() if (p / "phases.json").is_file())


def test_at_least_cka_and_lfcs_ship_content() -> None:
    assert {"cka", "lfcs"} <= set(_content_tracks())


@pytest.mark.parametrize("slug", _content_tracks())
async def test_track_content_seeds_without_dangling_references(
    session: AsyncSession, slug: str, caplog: pytest.LogCaptureFixture
) -> None:
    counter = Counter()
    tracks = {t.slug: t for t in await seed_tracks(session, counter)}
    await session.commit()
    track = tracks[slug]
    content = TrackContent.for_track(slug)
    assert content is not None

    with caplog.at_level(logging.WARNING, logger="seed"):
        await seed_track(session, counter, track, content)

    # A "skipping quiz ... missing" warning is a file naming a phase, week or
    # lesson that does not exist - exactly the drift this test is for.
    skipped = [r.getMessage() for r in caplog.records if "skipping" in r.getMessage()]
    assert not skipped, skipped

    phases = json.loads(content.phases_file.read_text())["phases"]
    expected_lessons = sum(len(w["lessons"]) for p in phases for w in p["weeks"])
    expected_weeks = sum(len(p["weeks"]) for p in phases)

    async def count(model, *where):
        return (await session.execute(select(func.count(model.id)).where(*where))).scalar_one()

    assert await count(Phase, Phase.track_id == track.id) == len(phases)
    assert await count(Week, Week.track_id == track.id) == expected_weeks
    assert (
        await count(Lesson, Lesson.week_id.in_(select(Week.id).where(Week.track_id == track.id)))
        == expected_lessons
    )
    assert await count(Lab, Lab.phase_id.in_(select(Phase.id).where(Phase.track_id == track.id))) == len(
        list(content.lab_dir.glob("*.json"))
    )
    assert await count(Quiz, Quiz.phase_id.in_(select(Phase.id).where(Phase.track_id == track.id))) == len(
        list(content.quiz_dir.rglob("*.json"))
    )

    # Weeks cover the track's range without a hole - the duration is the
    # furthest week_end, and a gap would be a week nobody can be in.
    numbers = sorted(w["number"] for p in phases for w in p["weeks"])
    assert numbers == list(range(1, len(numbers) + 1)), numbers

    # Every lesson has an Uzbek title and summary - the roadmap is bilingual.
    structure = json.loads((content.i18n_dir / "uz" / "structure.json").read_text())
    slugs = {l["slug"] for p in phases for w in p["weeks"] for l in w["lessons"]}
    missing = sorted(slugs - set(structure["lessons"]))
    assert not missing, f"lessons without uz entries: {missing[:10]}"


def test_lesson_slugs_are_unique_across_tracks() -> None:
    seen: dict[str, str] = {}
    for slug in _content_tracks():
        content = TrackContent.for_track(slug)
        assert content is not None
        phases = json.loads(content.phases_file.read_text())["phases"]
        for p in phases:
            for w in p["weeks"]:
                for l in w["lessons"]:
                    assert l["slug"] not in seen, f"{l['slug']} in both {seen[l['slug']]} and {slug}"
                    seen[l["slug"]] = slug
