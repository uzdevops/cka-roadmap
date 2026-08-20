"""Idempotent database seeding.

Run on every container start. Two kinds of thing come out of the seed files,
and they are owned differently:

* **Structure** - which tracks exist, which phases and weeks they have, which
  lesson sits in which week on which day, which phase a quiz or lab belongs to.
  This is the repo's, and it is kept in sync on every run: a lesson that moved
  in `phases.json` moves in the database, a phase that disappeared from the
  file is removed once nothing points at it any more. Without that rule a
  rewritten roadmap would leave the old one standing next to the new one.

* **Authored content** - a lesson's title, summary, body and timing, a quiz's
  questions, a lab's tasks. Written once, then left alone, so an edit made
  through the admin panel survives a restart. The one exception is a
  placeholder lesson: as long as no real markdown exists for its slug it is
  still the seed's to describe, and it is upgraded in place when the markdown
  appears.

Content lives per track under `seed_data/tracks/<slug>/` (phases.json,
lessons/, quizzes/, labs/, i18n/). A track with no directory is created empty.

    python -m app.seed
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal
from app.i18n import SUPPORTED_LOCALES, DEFAULT_LOCALE
from app.models import Lab, Lesson, Phase, Question, Quiz, Track, User, UserRole, Week
from app.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s seed: %(message)s")
log = logging.getLogger("seed")

DATA_DIR = Path(__file__).parent / "seed_data"
TRACKS_DIR = DATA_DIR / "tracks"
REFERENCES_FILE = DATA_DIR / "references.json"
# {lesson_slug: [{"title", "url"}]} - lesson slugs are unique across tracks, so
# one map serves every track.
_REFERENCES: dict[str, list[dict[str, str]]] = (
    json.loads(REFERENCES_FILE.read_text(encoding="utf-8"))
    if REFERENCES_FILE.is_file()
    else {}
)


class Counter:
    def __init__(self) -> None:
        self.created: dict[str, int] = {}
        self.updated: dict[str, int] = {}
        self.removed: dict[str, int] = {}

    def create(self, kind: str) -> None:
        self.created[kind] = self.created.get(kind, 0) + 1

    def update(self, kind: str) -> None:
        self.updated[kind] = self.updated.get(kind, 0) + 1

    def remove(self, kind: str) -> None:
        self.removed[kind] = self.removed.get(kind, 0) + 1

    def report(self) -> str:
        if not self.created and not self.updated and not self.removed:
            return "nothing to do - database already seeded"
        parts = []
        for verb, bucket in (
            ("created", self.created),
            ("updated", self.updated),
            ("removed", self.removed),
        ):
            if bucket:
                parts.append(
                    f"{verb} " + ", ".join(f"{v} {k}" for k, v in sorted(bucket.items()))
                )
        return "; ".join(parts)


class TrackContent:
    """The seed files of one track, by convention under one directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.phases_file = root / "phases.json"
        self.lesson_dir = root / "lessons"
        self.quiz_dir = root / "quizzes"
        self.lab_dir = root / "labs"
        self.i18n_dir = root / "i18n"

    @classmethod
    def for_track(cls, slug: str) -> "TrackContent | None":
        root = TRACKS_DIR / slug
        return cls(root) if (root / "phases.json").is_file() else None


def _placeholder_content(title: str, summary: str, phase_title: str) -> str:
    """Stand-in body for a lesson whose markdown has not been written yet.

    It says so plainly - the roadmap is complete and navigable, the prose for
    this one is still to come - and points at what to do meanwhile, so a
    learner who lands here is not left staring at an empty page.
    """
    return (
        f"## {title}\n\n"
        f"{summary}\n\n"
        ":::warning\n"
        "This lesson is not fully written yet. The roadmap structure is complete - "
        "you can plan and navigate around it - and the written material is being "
        "filled in phase by phase.\n"
        ":::\n\n"
        "## What this lesson covers\n\n"
        f"This lesson belongs to **{phase_title}**. When it is ready it will follow "
        "the same shape as the written lessons:\n\n"
        "- the concept explained from first principles\n"
        "- the YAML and `kubectl` you actually need\n"
        "- failure modes and how to recognise them\n"
        "- exam-relevant tips and a short self-check\n\n"
        "## In the meantime\n\n"
        "Work through the official documentation on this topic and practise the "
        "commands on your own cluster:\n\n"
        "```bash\n"
        "kubectl api-resources\n"
        "kubectl explain <resource> --recursive | less\n"
        "```\n"
    )


# --- Tracks --------------------------------------------------------------


async def seed_tracks(session: AsyncSession, counter: Counter) -> list[Track]:
    """Creates every track in tracks.json and returns them all, in file order."""
    payload = json.loads((DATA_DIR / "tracks.json").read_text(encoding="utf-8"))
    tracks: list[Track] = []

    for data in payload["tracks"]:
        track = (
            await session.execute(select(Track).where(Track.slug == data["slug"]))
        ).scalar_one_or_none()

        if track is None:
            track = Track(
                slug=data["slug"],
                title=data["title"],
                short_title=data.get("short_title"),
                summary=data.get("summary", ""),
                provider=data.get("provider"),
                is_topic=data.get("is_topic", False),
                is_certificate=data.get("is_certificate", False),
                exam_code=data.get("exam_code"),
                exam_minutes=data.get("exam_minutes"),
                order_index=data.get("order_index", 0),
                mark=data.get("mark"),
                accent=data.get("accent", "sky"),
                references=data.get("references") or [],
                is_published=True,
            )
            session.add(track)
            await session.flush()
            counter.create("tracks")
        else:
            # Two fields are kept in sync on an existing row; everything else is
            # create-only so an edit made in the admin panel survives a redeploy.
            #
            # order_index encodes a RELATIVE ordering, so applying it only to new
            # rows leaves two tracks sharing an index and the list order goes
            # undefined - which is exactly what happened when CompTIA was split
            # into three.
            #
            # references are the track's official links, and they are reference
            # data the repo owns rather than authored content. Never blanks a
            # non-empty list with an empty one, on the same reasoning as lesson
            # references.
            if track.order_index != data.get("order_index", 0):
                track.order_index = data.get("order_index", 0)
                counter.update("track order")

            refs = data.get("references") or []
            if refs and track.references != refs:
                track.references = refs
                counter.update("track references")

        tracks.append(track)

    if not tracks:
        raise RuntimeError("tracks.json defines no tracks")
    return tracks


# --- Structure -----------------------------------------------------------


async def seed_structure(
    session: AsyncSession, counter: Counter, track: Track, content: TrackContent
) -> None:
    """Phases, weeks and lessons - created when new, MOVED when the file moved them."""
    payload = json.loads(content.phases_file.read_text(encoding="utf-8"))

    for phase_data in payload["phases"]:
        phase = (
            await session.execute(
                select(Phase).where(
                    Phase.track_id == track.id, Phase.slug == phase_data["slug"]
                )
            )
        ).scalar_one_or_none()

        fields = dict(
            title=phase_data["title"],
            description=phase_data["description"],
            order_index=phase_data["order_index"],
            exam_domain=phase_data.get("exam_domain"),
            exam_weight=phase_data.get("exam_weight", 0),
            week_start=phase_data["week_start"],
            week_end=phase_data["week_end"],
            color=phase_data.get("color", "sky"),
        )
        if phase is None:
            phase = Phase(track_id=track.id, slug=phase_data["slug"], **fields)
            session.add(phase)
            await session.flush()
            counter.create("phases")
        elif _apply(phase, fields):
            # A phase is structure through and through - its name, its range,
            # its weight in the readiness score - so the file always wins.
            counter.update("phases")

        for week_index, week_data in enumerate(phase_data["weeks"], start=1):
            week = (
                await session.execute(
                    select(Week).where(
                        Week.track_id == track.id,
                        Week.number == week_data["number"],
                    )
                )
            ).scalar_one_or_none()

            fields = dict(
                phase_id=phase.id,
                title=week_data["title"],
                description=week_data.get("description", ""),
                order_index=week_index,
            )
            if week is None:
                week = Week(track_id=track.id, number=week_data["number"], **fields)
                session.add(week)
                await session.flush()
                counter.create("weeks")
            elif _apply(week, fields):
                counter.update("weeks")

            for lesson_index, lesson_data in enumerate(week_data["lessons"], start=1):
                await _seed_lesson(
                    session, counter, content, week, phase, lesson_data, lesson_index
                )


def _apply(row: Any, fields: dict[str, Any]) -> bool:
    """Sets each attribute that differs; reports whether anything changed."""
    changed = False
    for key, value in fields.items():
        if getattr(row, key) != value:
            setattr(row, key, value)
            changed = True
    return changed


async def _seed_lesson(
    session: AsyncSession,
    counter: Counter,
    content: TrackContent,
    week: Week,
    phase: Phase,
    data: dict[str, Any],
    order_index: int,
) -> None:
    slug = data["slug"]
    markdown_file = content.lesson_dir / f"{slug}.md"
    has_real_content = markdown_file.is_file()

    body = (
        markdown_file.read_text(encoding="utf-8")
        if has_real_content
        else _placeholder_content(data["title"], data.get("summary", ""), phase.title)
    )

    references = _REFERENCES.get(slug, [])

    lesson = (
        await session.execute(select(Lesson).where(Lesson.slug == slug))
    ).scalar_one_or_none()

    if lesson is None:
        session.add(
            Lesson(
                week_id=week.id,
                slug=slug,
                title=data["title"],
                summary=data.get("summary", ""),
                content=body,
                order_index=order_index,
                estimated_minutes=data.get("estimated_minutes", 30),
                day_of_week=data.get("day_of_week"),
                is_published=True,
                is_placeholder=not has_real_content,
                references=references,
                video_url=data.get("video_url"),
            )
        )
        counter.create("lessons")
        return

    # Placement is structure: where the lesson sits is the file's to decide,
    # and a lesson the roadmap moved has to move with it.
    if _apply(
        lesson,
        dict(
            week_id=week.id,
            order_index=order_index,
            day_of_week=data.get("day_of_week"),
        ),
    ):
        counter.update("lesson placement")

    # Links are reference data, not authored content: keep them current even on
    # a lesson somebody has edited, but never clobber a non-empty list with an
    # empty one.
    if references and lesson.references != references:
        lesson.references = references
        counter.update("lesson references")

    # Same reasoning as the links: a video URL is reference data the repo owns,
    # so keep it current - but never blank one an admin set by hand just because
    # the seed file has nothing to say about that lesson.
    video_url = data.get("video_url")
    if video_url and lesson.video_url != video_url:
        lesson.video_url = video_url
        counter.update("lesson videos")

    # A placeholder is still the seed's to describe: its title, summary and
    # timing follow the file until real markdown arrives, at which point the
    # body is upgraded in place. A lesson with a real body is authored content
    # and is left exactly as it is.
    if lesson.is_placeholder:
        if _apply(
            lesson,
            dict(
                title=data["title"],
                summary=data.get("summary", ""),
                estimated_minutes=data.get("estimated_minutes", 30),
            ),
        ):
            counter.update("lesson descriptions")
        if has_real_content:
            lesson.content = body
            lesson.is_placeholder = False
            counter.update("lessons")


# --- Quizzes -------------------------------------------------------------


async def seed_quizzes(
    session: AsyncSession, counter: Counter, track: Track, content: TrackContent
) -> None:
    if not content.quiz_dir.is_dir():
        return
    for path in sorted(content.quiz_dir.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        phase = (
            await session.execute(
                select(Phase).where(
                    Phase.track_id == track.id, Phase.slug == data["phase_slug"]
                )
            )
        ).scalar_one_or_none()
        if phase is None:
            log.warning("skipping quiz %s - phase %s missing", data["slug"], data["phase_slug"])
            continue

        # A quiz naming a lesson becomes that lesson's gate; one without a
        # lesson stays the week/phase quiz it always was.
        lesson_id = None
        if data.get("lesson_slug"):
            lesson = (
                await session.execute(
                    select(Lesson).where(Lesson.slug == data["lesson_slug"])
                )
            ).scalar_one_or_none()
            if lesson is None:
                log.warning(
                    "skipping quiz %s - lesson %s missing",
                    data["slug"],
                    data["lesson_slug"],
                )
                continue
            lesson_id = lesson.id

        week_id = None
        if data.get("week_number"):
            week = (
                await session.execute(
                    select(Week).where(
                        Week.track_id == track.id,
                        Week.number == data["week_number"],
                    )
                )
            ).scalar_one_or_none()
            week_id = week.id if week else None

        quiz = (
            await session.execute(select(Quiz).where(Quiz.slug == data["slug"]))
        ).scalar_one_or_none()

        if quiz is None:
            quiz = Quiz(
                phase_id=phase.id,
                week_id=week_id,
                lesson_id=lesson_id,
                slug=data["slug"],
                title=data["title"],
                description=data.get("description", ""),
                pass_score=data.get("pass_score", 70.0),
                time_limit_minutes=data.get("time_limit_minutes"),
                order_index=data.get("order_index", 0),
                is_published=True,
            )
            session.add(quiz)
            await session.flush()
            counter.create("quizzes")
        # Where the quiz hangs is structure and follows the file; its questions
        # and pass mark are authored and do not.
        elif _apply(quiz, dict(phase_id=phase.id, week_id=week_id, lesson_id=lesson_id)):
            counter.update("quiz placement")

        existing_keys = set(
            (
                await session.execute(
                    select(Question.key).where(Question.quiz_id == quiz.id)
                )
            )
            .scalars()
            .all()
        )

        for index, question in enumerate(data["questions"], start=1):
            if question["key"] in existing_keys:
                continue
            session.add(
                Question(
                    quiz_id=quiz.id,
                    key=question["key"],
                    type=question["type"],
                    prompt=question["prompt"],
                    options=question.get("options", []),
                    correct_options=question.get("correct_options", []),
                    accepted_answers=question.get("accepted_answers", []),
                    explanation=question.get("explanation", ""),
                    points=question.get("points", 1),
                    order_index=question.get("order_index", index),
                )
            )
            counter.create("questions")


# --- Labs ----------------------------------------------------------------


async def seed_labs(
    session: AsyncSession, counter: Counter, track: Track, content: TrackContent
) -> None:
    if not content.lab_dir.is_dir():
        return
    for path in sorted(content.lab_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        phase = (
            await session.execute(
                select(Phase).where(
                    Phase.track_id == track.id, Phase.slug == data["phase_slug"]
                )
            )
        ).scalar_one_or_none()
        if phase is None:
            log.warning("skipping lab %s - phase %s missing", data["slug"], data["phase_slug"])
            continue

        week_id = None
        if data.get("week_number"):
            week = (
                await session.execute(
                    select(Week).where(
                        Week.track_id == track.id,
                        Week.number == data["week_number"],
                    )
                )
            ).scalar_one_or_none()
            week_id = week.id if week else None

        existing = (
            await session.execute(select(Lab).where(Lab.slug == data["slug"]))
        ).scalar_one_or_none()
        if existing is not None:
            # Placement follows the file; the lab's own text does not.
            if _apply(existing, dict(phase_id=phase.id, week_id=week_id)):
                counter.update("lab placement")
            continue

        session.add(
            Lab(
                phase_id=phase.id,
                week_id=week_id,
                slug=data["slug"],
                title=data["title"],
                description=data.get("description", ""),
                scenario=data.get("scenario", ""),
                difficulty=data.get("difficulty", "beginner"),
                estimated_minutes=data.get("estimated_minutes", 45),
                environment_setup=data.get("environment_setup", ""),
                cleanup=data.get("cleanup", ""),
                tasks=data.get("tasks", []),
                order_index=data.get("order_index", 0),
                is_published=True,
            )
        )
        counter.create("labs")


# --- Pruning -------------------------------------------------------------


async def prune_structure(
    session: AsyncSession, counter: Counter, track: Track, content: TrackContent
) -> None:
    """Removes the phases and weeks the file no longer names - but only empty
    ones. A week that still holds a lesson the file forgot, or a phase a quiz
    still hangs from, is left standing with a warning: losing somebody's
    progress is never the seed's call to make."""
    payload = json.loads(content.phases_file.read_text(encoding="utf-8"))
    phase_slugs = {p["slug"] for p in payload["phases"]}
    week_numbers = {w["number"] for p in payload["phases"] for w in p["weeks"]}

    weeks = (
        await session.execute(select(Week).where(Week.track_id == track.id))
    ).scalars().all()
    for week in weeks:
        if week.number in week_numbers:
            continue
        lessons = (
            await session.execute(
                select(func.count(Lesson.id)).where(Lesson.week_id == week.id)
            )
        ).scalar_one()
        if lessons:
            log.warning(
                "week %s of %s is not in phases.json but still holds %d lesson(s) - kept",
                week.number, track.slug, lessons,
            )
            continue
        await session.delete(week)
        counter.remove("weeks")
    await session.flush()

    phases = (
        await session.execute(select(Phase).where(Phase.track_id == track.id))
    ).scalars().all()
    for phase in phases:
        if phase.slug in phase_slugs:
            continue
        held = {
            "week": (await session.execute(
                select(func.count(Week.id)).where(Week.phase_id == phase.id)
            )).scalar_one(),
            "quiz": (await session.execute(
                select(func.count(Quiz.id)).where(Quiz.phase_id == phase.id)
            )).scalar_one(),
            "lab": (await session.execute(
                select(func.count(Lab.id)).where(Lab.phase_id == phase.id)
            )).scalar_one(),
        }
        if any(held.values()):
            log.warning(
                "phase %s of %s is not in phases.json but still holds %s - kept",
                phase.slug, track.slug,
                ", ".join(f"{n} {k}(s)" for k, n in held.items() if n),
            )
            continue
        await session.delete(phase)
        counter.remove("phases")
    await session.flush()


# --- Translations --------------------------------------------------------


def _fill(
    current: dict, locale: str, values: dict, *, overwrite: bool = False
) -> tuple[dict, bool]:
    """Merges one locale's values into a translations blob.

    Fill-only by default: existing values win, so a translation edited through
    the admin panel is never overwritten by a later container start. With
    `overwrite` the file wins - used for the things the seed owns outright,
    which is structure (phase and week names) and the description of a lesson
    that is still a placeholder.
    """
    merged = {k: dict(v) for k, v in (current or {}).items()}
    bucket = merged.setdefault(locale, {})
    changed = False
    for key, value in values.items():
        if value in (None, "", [], {}):
            continue
        if overwrite:
            if bucket.get(key) != value:
                bucket[key] = value
                changed = True
        elif not bucket.get(key):
            bucket[key] = value
            changed = True
    return merged, changed


async def seed_translations(
    session: AsyncSession, counter: Counter, track: Track, content: TrackContent
) -> None:
    for locale in SUPPORTED_LOCALES:
        if locale == DEFAULT_LOCALE:
            continue  # English is the base row itself
        root = content.i18n_dir / locale
        if not root.is_dir():
            continue
        await _seed_structure_translations(session, counter, locale, root, track)
        await _seed_quiz_translations(session, counter, locale, root)
        await _seed_lab_translations(session, counter, locale, root)


async def _seed_structure_translations(
    session: AsyncSession, counter: Counter, locale: str, root: Path, track: Track
) -> None:
    structure_file = root / "structure.json"
    if not structure_file.is_file():
        return
    data = json.loads(structure_file.read_text(encoding="utf-8"))

    for slug, values in (data.get("phases") or {}).items():
        phase = (
            await session.execute(
                select(Phase).where(Phase.track_id == track.id, Phase.slug == slug)
            )
        ).scalar_one_or_none()
        if phase is None:
            continue
        # Structure: the file's names win, as they do for the English row.
        phase.translations, changed = _fill(
            phase.translations, locale, values, overwrite=True
        )
        if changed:
            counter.update(f"phase translations ({locale})")

    for number, values in (data.get("weeks") or {}).items():
        week = (
            await session.execute(
                select(Week).where(
                    Week.track_id == track.id, Week.number == int(number)
                )
            )
        ).scalar_one_or_none()
        if week is None:
            continue
        week.translations, changed = _fill(
            week.translations, locale, values, overwrite=True
        )
        if changed:
            counter.update(f"week translations ({locale})")

    # Localised documentation titles, if this locale supplies them. The URLs
    # stay the same - kubernetes.io has no Uzbek edition - so only the labels
    # in the list are translated.
    ref_file = root / "references.json"
    if ref_file.is_file():
        for slug, refs in json.loads(ref_file.read_text(encoding="utf-8")).items():
            lesson = (
                await session.execute(select(Lesson).where(Lesson.slug == slug))
            ).scalar_one_or_none()
            if lesson is None or not refs:
                continue
            lesson.translations, changed = _fill(
                lesson.translations, locale, {"references": refs}
            )
            if changed:
                counter.update(f"lesson references ({locale})")

    lesson_dir = root / "lessons"
    for slug, values in (data.get("lessons") or {}).items():
        lesson = (
            await session.execute(select(Lesson).where(Lesson.slug == slug))
        ).scalar_one_or_none()
        if lesson is None:
            continue

        payload = dict(values)
        body_file = lesson_dir / f"{slug}.md"
        if body_file.is_file():
            payload["content"] = body_file.read_text(encoding="utf-8")
        elif lesson.is_placeholder:
            payload["content"] = _placeholder_content_uz(
                payload.get("title", lesson.title), payload.get("summary", "")
            ) if locale == "uz" else None

        # A placeholder's description is the seed's in every language; once a
        # real body exists the lesson is authored and the translation is only
        # filled in where it is missing.
        lesson.translations, changed = _fill(
            lesson.translations, locale, payload, overwrite=lesson.is_placeholder
        )
        if changed:
            counter.update(f"lesson translations ({locale})")


async def _seed_quiz_translations(
    session: AsyncSession, counter: Counter, locale: str, root: Path
) -> None:
    for path in sorted((root / "quizzes").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        quiz = (
            await session.execute(select(Quiz).where(Quiz.slug == path.stem))
        ).scalar_one_or_none()
        if quiz is None:
            continue

        quiz.translations, changed = _fill(
            quiz.translations,
            locale,
            {"title": data.get("title"), "description": data.get("description")},
        )
        if changed:
            counter.update(f"quiz translations ({locale})")

        questions = (
            (await session.execute(select(Question).where(Question.quiz_id == quiz.id)))
            .scalars()
            .all()
        )
        by_key = {q.key: q for q in questions}
        for key, values in (data.get("questions") or {}).items():
            question = by_key.get(key)
            if question is None:
                continue
            question.translations, changed = _fill(question.translations, locale, values)
            if changed:
                counter.update(f"question translations ({locale})")


async def _seed_lab_translations(
    session: AsyncSession, counter: Counter, locale: str, root: Path
) -> None:
    for path in sorted((root / "labs").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        lab = (
            await session.execute(select(Lab).where(Lab.slug == path.stem))
        ).scalar_one_or_none()
        if lab is None:
            continue
        lab.translations, changed = _fill(lab.translations, locale, data)
        if changed:
            counter.update(f"lab translations ({locale})")


def _placeholder_content_uz(title: str, summary: str) -> str:
    return (
        f"## {title}\n\n"
        f"{summary}\n\n"
        ":::warning\n"
        "Bu dars hali to'liq yozilmagan. Yo'l xaritasi tuzilishi to'liq - siz "
        "rejalashtira olasiz va harakatlana olasiz, matnlar esa bosqichma-bosqich "
        "to'ldirilmoqda.\n"
        ":::\n\n"
        "## Bu dars nimani qamrab oladi\n\n"
        "Tayyor bo'lganda u yozilgan darslar bilan bir xil tuzilishga ega "
        "bo'ladi:\n\n"
        "- tushuncha boshidan tushuntiriladi\n"
        "- sizga haqiqatan kerak bo'ladigan YAML va `kubectl` buyruqlari\n"
        "- nosozlik holatlari va ularni qanday aniqlash\n"
        "- imtihonga oid maslahatlar va qisqa o'z-o'zini tekshirish\n\n"
        "## Shu orada\n\n"
        "Bu mavzu bo'yicha rasmiy hujjatlar bilan ishlang va buyruqlarni o'z "
        "klasteringizda mashq qiling:\n\n"
        "```bash\n"
        "kubectl api-resources\n"
        "kubectl explain <resurs> --recursive | less\n"
        "```\n"
    )


# --- Demo users ----------------------------------------------------------


async def seed_users(session: AsyncSession, counter: Counter) -> None:
    demo_users = [
        (
            settings.demo_student_email,
            settings.demo_student_username,
            settings.demo_student_password,
            "Demo Student",
            UserRole.STUDENT.value,
        ),
        (
            settings.demo_admin_email,
            settings.demo_admin_username,
            settings.demo_admin_password,
            "Demo Admin",
            UserRole.ADMIN.value,
        ),
    ]

    for email, username, password, name, role in demo_users:
        existing = (
            await session.execute(
                select(User).where(
                    or_(User.email == email, User.username == username)
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            # Backfill the username onto an account seeded before usernames
            # existed, so `admin` starts working without a wipe. The password is
            # never touched - resetting it on every container start would undo
            # any change the owner made from the profile page.
            if existing.username is None:
                existing.username = username
                counter.update("user usernames")
            continue
        session.add(
            User(
                email=email,
                username=username,
                hashed_password=hash_password(password),
                full_name=name,
                role=role,
                is_active=True,
                daily_study_minutes=90,
            )
        )
        counter.create("users")


# --- Entrypoint ----------------------------------------------------------


async def seed_track(
    session: AsyncSession, counter: Counter, track: Track, content: TrackContent
) -> None:
    """Everything one track's directory has to say, in dependency order.

    Structure first, then the quizzes and labs that hang from it, then the
    prune - which must come after quizzes and labs have been re-pointed, or a
    phase they moved away from would still look occupied.
    """
    await seed_structure(session, counter, track, content)
    await session.commit()
    await seed_quizzes(session, counter, track, content)
    await session.commit()
    await seed_labs(session, counter, track, content)
    await session.commit()
    await prune_structure(session, counter, track, content)
    await session.commit()
    await seed_translations(session, counter, track, content)
    await session.commit()


async def run_seed() -> None:
    counter = Counter()
    async with SessionLocal() as session:
        tracks = await seed_tracks(session, counter)
        await session.commit()

        for track in tracks:
            content = TrackContent.for_track(track.slug)
            if content is None:
                continue
            await seed_track(session, counter, track, content)

        await seed_users(session, counter)
        await session.commit()

    log.info(counter.report())


def main() -> None:
    if not settings.seed_on_start:
        log.info("SEED_ON_START is false - skipping")
        return
    asyncio.run(run_seed())


if __name__ == "__main__":
    main()
