"""Admin panel API. Every route is behind a server-side role check."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select

from app.deps import AdminUser, SessionDep, require_admin
from app.models import (
    Lab,
    Lesson,
    Phase,
    Question,
    Quiz,
    QuizAttempt,
    User,
    Week,
)
from app.repositories import progress_repo
from app.schemas.admin import (
    AdminLabRead,
    AdminLessonRead,
    AdminQuizRead,
    AdminStats,
    LabCreate,
    LabUpdate,
    LessonCreate,
    LessonUpdate,
    QuizCreate,
    QuizUpdate,
)
from app.schemas.quiz import QuestionWrite

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


# --- Stats ---------------------------------------------------------------


@router.get("/stats", response_model=AdminStats)
async def stats(session: SessionDep) -> AdminStats:
    async def count(model) -> int:
        return int((await session.execute(select(func.count(model.id)))).scalar_one())

    role_rows = (
        await session.execute(select(User.role, func.count(User.id)).group_by(User.role))
    ).all()
    roles = {role: n for role, n in role_rows}

    return AdminStats(
        users=sum(roles.values()),
        students=roles.get("student", 0),
        admins=roles.get("admin", 0),
        phases=await count(Phase),
        weeks=await count(Week),
        lessons=await count(Lesson),
        quizzes=await count(Quiz),
        questions=await count(Question),
        labs=await count(Lab),
        quiz_attempts=await count(QuizAttempt),
        completed_lessons=await progress_repo.count_all_completed_lessons(session),
    )


# --- Lessons -------------------------------------------------------------


@router.get("/lessons", response_model=list[AdminLessonRead])
async def list_lessons(session: SessionDep) -> list[Lesson]:
    stmt = select(Lesson).order_by(Lesson.week_id, Lesson.order_index, Lesson.id)
    return list((await session.execute(stmt)).scalars().all())


@router.post("/lessons", response_model=AdminLessonRead, status_code=201)
async def create_lesson(payload: LessonCreate, session: SessionDep) -> Lesson:
    if await session.get(Week, payload.week_id) is None:
        raise HTTPException(status_code=400, detail="week_id does not exist")
    existing = (
        await session.execute(select(Lesson).where(Lesson.slug == payload.slug))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="A lesson with this slug exists")

    lesson = Lesson(**payload.model_dump(), is_placeholder=False)
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)
    return lesson


@router.get("/lessons/{lesson_id}", response_model=AdminLessonRead)
async def get_lesson(lesson_id: int, session: SessionDep) -> Lesson:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=AdminLessonRead)
async def update_lesson(
    lesson_id: int, payload: LessonUpdate, session: SessionDep
) -> Lesson:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("content"):
        lesson.is_placeholder = False
    for field, value in data.items():
        setattr(lesson, field, value)
    await session.commit()
    await session.refresh(lesson)
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_lesson(lesson_id: int, session: SessionDep) -> None:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    await session.delete(lesson)
    await session.commit()


# --- Quizzes -------------------------------------------------------------


def _quiz_read(quiz: Quiz) -> AdminQuizRead:
    return AdminQuizRead(
        id=quiz.id,
        phase_id=quiz.phase_id,
        week_id=quiz.week_id,
        slug=quiz.slug,
        title=quiz.title,
        description=quiz.description,
        pass_score=quiz.pass_score,
        time_limit_minutes=quiz.time_limit_minutes,
        order_index=quiz.order_index,
        is_published=quiz.is_published,
        translations=quiz.translations or {},
        questions=[
            QuestionWrite(
                key=q.key,
                type=q.type,
                prompt=q.prompt,
                options=q.options or [],
                correct_options=q.correct_options or [],
                accepted_answers=q.accepted_answers or [],
                explanation=q.explanation,
                points=q.points,
                order_index=q.order_index,
                translations=q.translations or {},
            )
            for q in sorted(quiz.questions, key=lambda x: (x.order_index, x.id))
        ],
    )


async def _load_quiz(session, quiz_id: int) -> Quiz:
    from app.repositories import quiz_repo

    quiz = await quiz_repo.get_quiz_by_id(session, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.get("/quizzes", response_model=list[AdminQuizRead])
async def list_quizzes(session: SessionDep) -> list[AdminQuizRead]:
    from app.repositories import quiz_repo

    quizzes = await quiz_repo.list_quizzes(session)
    return [_quiz_read(q) for q in quizzes]


@router.post("/quizzes", response_model=AdminQuizRead, status_code=201)
async def create_quiz(payload: QuizCreate, session: SessionDep) -> AdminQuizRead:
    if await session.get(Phase, payload.phase_id) is None:
        raise HTTPException(status_code=400, detail="phase_id does not exist")
    existing = (
        await session.execute(select(Quiz).where(Quiz.slug == payload.slug))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="A quiz with this slug exists")

    data = payload.model_dump(exclude={"questions"})
    quiz = Quiz(**data)
    session.add(quiz)
    await session.flush()
    for idx, q in enumerate(payload.questions):
        session.add(Question(quiz_id=quiz.id, **{**q.model_dump(), "order_index": q.order_index or idx}))
    await session.commit()
    return _quiz_read(await _load_quiz(session, quiz.id))


@router.get("/quizzes/{quiz_id}", response_model=AdminQuizRead)
async def get_quiz(quiz_id: int, session: SessionDep) -> AdminQuizRead:
    return _quiz_read(await _load_quiz(session, quiz_id))


@router.patch("/quizzes/{quiz_id}", response_model=AdminQuizRead)
async def update_quiz(
    quiz_id: int, payload: QuizUpdate, session: SessionDep
) -> AdminQuizRead:
    quiz = await _load_quiz(session, quiz_id)
    data = payload.model_dump(exclude_unset=True, exclude={"questions"})
    for field, value in data.items():
        setattr(quiz, field, value)

    if payload.questions is not None:
        await session.execute(delete(Question).where(Question.quiz_id == quiz.id))
        await session.flush()
        for idx, q in enumerate(payload.questions):
            session.add(
                Question(quiz_id=quiz.id, **{**q.model_dump(), "order_index": q.order_index or idx})
            )
    await session.commit()
    return _quiz_read(await _load_quiz(session, quiz_id))


@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_quiz(quiz_id: int, session: SessionDep) -> None:
    quiz = await session.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    await session.delete(quiz)
    await session.commit()


# --- Labs ----------------------------------------------------------------


@router.get("/labs", response_model=list[AdminLabRead])
async def list_labs(session: SessionDep) -> list[Lab]:
    stmt = select(Lab).order_by(Lab.phase_id, Lab.order_index, Lab.id)
    return list((await session.execute(stmt)).scalars().all())


@router.post("/labs", response_model=AdminLabRead, status_code=201)
async def create_lab(payload: LabCreate, session: SessionDep) -> Lab:
    if await session.get(Phase, payload.phase_id) is None:
        raise HTTPException(status_code=400, detail="phase_id does not exist")
    existing = (
        await session.execute(select(Lab).where(Lab.slug == payload.slug))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="A lab with this slug exists")
    lab = Lab(**payload.model_dump())
    session.add(lab)
    await session.commit()
    await session.refresh(lab)
    return lab


@router.get("/labs/{lab_id}", response_model=AdminLabRead)
async def get_lab(lab_id: int, session: SessionDep) -> Lab:
    lab = await session.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return lab


@router.patch("/labs/{lab_id}", response_model=AdminLabRead)
async def update_lab(lab_id: int, payload: LabUpdate, session: SessionDep) -> Lab:
    lab = await session.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lab, field, value)
    await session.commit()
    await session.refresh(lab)
    return lab


@router.delete("/labs/{lab_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_lab(lab_id: int, session: SessionDep) -> None:
    lab = await session.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    await session.delete(lab)
    await session.commit()


# --- Structure helpers for the editor dropdowns --------------------------


@router.get("/structure")
async def structure(session: SessionDep, admin: AdminUser) -> list[dict]:
    phases = (
        (await session.execute(select(Phase).order_by(Phase.order_index)))
        .scalars()
        .all()
    )
    weeks = (await session.execute(select(Week).order_by(Week.number))).scalars().all()
    by_phase: dict[int, list[dict]] = {}
    for week in weeks:
        by_phase.setdefault(week.phase_id, []).append(
            {"id": week.id, "number": week.number, "title": week.title}
        )
    return [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "order_index": p.order_index,
            "weeks": by_phase.get(p.id, []),
        }
        for p in phases
    ]
