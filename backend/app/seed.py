"""Idempotent database seeding.

Run on every container start. The rule is simple and makes re-runs safe:

* objects are matched by their natural key (slug, week number, email);
* missing objects are created;
* existing objects are left alone, so edits made through the admin panel
  survive a restart.

The one exception is a placeholder lesson: if real markdown later appears for
its slug, the placeholder is upgraded in place.

    python -m app.seed
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal
from app.i18n import SUPPORTED_LOCALES, DEFAULT_LOCALE
from app.models import Lab, Lesson, Phase, Question, Quiz, Track, User, UserRole, Week
from app.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s seed: %(message)s")
log = logging.getLogger("seed")


# The track that owns every phase, week and lesson seeded from these files.
# Other tracks are created empty until their own content exists.
DEFAULT_TRACK_SLUG = "cka"

DATA_DIR = Path(__file__).parent / "seed_data"
LESSON_DIR = DATA_DIR / "lessons"
QUIZ_DIR = DATA_DIR / "quizzes"
LAB_DIR = DATA_DIR / "labs"
I18N_DIR = DATA_DIR / "i18n"
REFERENCES_FILE = DATA_DIR / "references.json"
# {lesson_slug: [{"title", "url"}]}
_REFERENCES: dict[str, list[dict[str, str]]] = (
    json.loads(REFERENCES_FILE.read_text(encoding="utf-8"))
    if REFERENCES_FILE.is_file()
    else {}
)


class Counter:
    def __init__(self) -> None:
        self.created: dict[str, int] = {}
        self.updated: dict[str, int] = {}

    def create(self, kind: str) -> None:
        self.created[kind] = self.created.get(kind, 0) + 1

    def update(self, kind: str) -> None:
        self.updated[kind] = self.updated.get(kind, 0) + 1

    def report(self) -> str:
        if not self.created and not self.updated:
            return "nothing to do - database already seeded"
        parts = []
        if self.created:
            parts.append(
                "created " + ", ".join(f"{v} {k}" for k, v in sorted(self.created.items()))
            )
        if self.updated:
            parts.append(
                "updated " + ", ".join(f"{v} {k}" for k, v in sorted(self.updated.items()))
            )
        return "; ".join(parts)


def _placeholder_content(title: str, summary: str, phase_title: str) -> str:
    return (
        f"## {title}\n\n"
        f"{summary}\n\n"
        ":::warning\n"
        "This lesson is a placeholder. The full write-up for this topic is still "
        "being authored - the roadmap structure is complete so you can navigate and "
        "plan, and Phase 1 is fully written.\n"
        ":::\n\n"
        "## What this lesson will cover\n\n"
        f"This topic belongs to **{phase_title}**. When it lands it will follow the "
        "same shape as the Phase 1 lessons:\n\n"
        "- the concept explained from first principles\n"
        "- the YAML and `kubectl` commands you actually need\n"
        "- the failure modes and how to diagnose each one\n"
        "- exam-specific tips and a short self-check\n\n"
        "## In the meantime\n\n"
        "Work through the official documentation for this topic and practise the "
        "commands in your own cluster:\n\n"
        "```bash\n"
        "kubectl api-resources\n"
        "kubectl explain <resource> --recursive | less\n"
        "```\n\n"
        ":::tip\n"
        "An administrator can replace this text at any time from the admin panel - "
        "the seeder never overwrites a lesson that has real content.\n"
        ":::\n"
    )


# --- Phases / weeks / lessons -------------------------------------------


async def seed_tracks(session: AsyncSession, counter: Counter) -> Track:
    """Creates every programme of study and returns the one that owns the
    existing content.

    Only `cka` has phases today. The rest are created empty on purpose: an empty
    track cannot collide with another one, because the two things this schema
    keeps unique per track - a phase slug and a week number - do not exist yet.
    """
    payload = json.loads((DATA_DIR / "tracks.json").read_text(encoding="utf-8"))

    default: Track | None = None
    for data in payload["tracks"]:
        track = (
            await session.execute(select(Track).where(Track.slug == data["slug"]))
        ).scalar_one_or_none()

        if track is None:
            track = Track(
                slug=data["slug"],
                title=data["title"],
                short_title=data.get("short_title", ""),
                summary=data.get("summary", ""),
                provider=data.get("provider"),
                is_topic=data.get("is_topic", False),
                is_certificate=data.get("is_certificate", False),
                exam_code=data.get("exam_code"),
                exam_minutes=data.get("exam_minutes"),
                order_index=data.get("order_index", 0),
                mark=data.get("mark", ""),
                accent=data.get("accent", "sky"),
                references=data.get("references", []),
            )
            session.add(track)
            await session.flush()
            counter.create("tracks")
        elif track.order_index != data.get("order_index", 0):
            # The one field that is kept in sync on an existing row. It encodes a
            # RELATIVE ordering, so applying it only to new tracks leaves two
            # rows sharing an index and the list order goes undefined - which is
            # exactly what happened when CompTIA was split into three.
            # Revisit when the admin panel can reorder tracks: this would undo
            # that.
            track.order_index = data.get("order_index", 0)
            counter.update("track order")

        if track.slug == DEFAULT_TRACK_SLUG:
            default = track

    if default is None:
        raise RuntimeError(
            f"tracks.json must define the {DEFAULT_TRACK_SLUG!r} track - it owns "
            "all existing phases, weeks and lessons."
        )
    return default


async def seed_structure(
    session: AsyncSession, counter: Counter, track: Track
) -> None:
    payload = json.loads((DATA_DIR / "phases.json").read_text(encoding="utf-8"))

    for phase_data in payload["phases"]:
        phase = (
            await session.execute(
                select(Phase).where(
                    Phase.track_id == track.id, Phase.slug == phase_data["slug"]
                )
            )
        ).scalar_one_or_none()

        if phase is None:
            phase = Phase(
                track_id=track.id,
                slug=phase_data["slug"],
                title=phase_data["title"],
                description=phase_data["description"],
                order_index=phase_data["order_index"],
                exam_domain=phase_data.get("exam_domain"),
                exam_weight=phase_data.get("exam_weight", 0),
                week_start=phase_data["week_start"],
                week_end=phase_data["week_end"],
                color=phase_data.get("color", "sky"),
            )
            session.add(phase)
            await session.flush()
            counter.create("phases")

        for week_index, week_data in enumerate(phase_data["weeks"], start=1):
            week = (
                await session.execute(
                    select(Week).where(
                        Week.track_id == track.id,
                        Week.number == week_data["number"],
                    )
                )
            ).scalar_one_or_none()

            if week is None:
                week = Week(
                    track_id=track.id,
                    phase_id=phase.id,
                    number=week_data["number"],
                    title=week_data["title"],
                    description=week_data.get("description", ""),
                    order_index=week_index,
                )
                session.add(week)
                await session.flush()
                counter.create("weeks")

            for lesson_index, lesson_data in enumerate(week_data["lessons"], start=1):
                await _seed_lesson(
                    session, counter, week, phase, lesson_data, lesson_index
                )


async def _seed_lesson(
    session: AsyncSession,
    counter: Counter,
    week: Week,
    phase: Phase,
    data: dict[str, Any],
    order_index: int,
) -> None:
    slug = data["slug"]
    markdown_file = LESSON_DIR / f"{slug}.md"
    has_real_content = markdown_file.is_file()

    content = (
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
                content=content,
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

    # Upgrade a placeholder in place once real markdown appears for its slug.
    if lesson.is_placeholder and has_real_content:
        lesson.content = content
        lesson.is_placeholder = False
        counter.update("lessons")


# --- Quizzes -------------------------------------------------------------


async def seed_quizzes(
    session: AsyncSession, counter: Counter, track: Track
) -> None:
    for path in sorted(QUIZ_DIR.rglob("*.json")):
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
        elif quiz.lesson_id != lesson_id and lesson_id is not None:
            quiz.lesson_id = lesson_id
            counter.update("quizzes")

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
    session: AsyncSession, counter: Counter, track: Track
) -> None:
    for path in sorted(LAB_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        existing = (
            await session.execute(select(Lab).where(Lab.slug == data["slug"]))
        ).scalar_one_or_none()
        if existing is not None:
            continue

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


# --- Translations --------------------------------------------------------


def _fill(current: dict, locale: str, values: dict) -> tuple[dict, bool]:
    """Adds only the keys this locale does not have yet.

    Existing values win, so a translation edited through the admin panel is
    never overwritten by a later container start.
    """
    merged = {k: dict(v) for k, v in (current or {}).items()}
    bucket = merged.setdefault(locale, {})
    changed = False
    for key, value in values.items():
        if value in (None, "", [], {}):
            continue
        if not bucket.get(key):
            bucket[key] = value
            changed = True
    return merged, changed


async def seed_translations(
    session: AsyncSession, counter: Counter, track: Track
) -> None:
    for locale in SUPPORTED_LOCALES:
        if locale == DEFAULT_LOCALE:
            continue  # English is the base row itself
        root = I18N_DIR / locale
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
        phase.translations, changed = _fill(phase.translations, locale, values)
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
        week.translations, changed = _fill(week.translations, locale, values)
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

        lesson.translations, changed = _fill(lesson.translations, locale, payload)
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
        "rejalashtira olasiz va harakatlana olasiz, 1-bosqich esa to'liq "
        "yozilgan.\n"
        ":::\n\n"
        "## Bu dars nimani qamrab oladi\n\n"
        "Tayyor bo'lganda u 1-bosqich darslari bilan bir xil tuzilishga ega "
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


async def run_seed() -> None:
    counter = Counter()
    async with SessionLocal() as session:
        track = await seed_tracks(session, counter)
        await session.commit()

        await seed_structure(session, counter, track)
        await session.commit()

        await seed_quizzes(session, counter, track)
        await session.commit()

        await seed_labs(session, counter, track)
        await session.commit()

        await seed_translations(session, counter, track)
        await session.commit()

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
