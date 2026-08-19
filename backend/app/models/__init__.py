"""ORM models. Importing this package registers every table on `Base.metadata`."""

from app.models.base import Base, TimestampMixin
from app.models.telegram import TelegramLinkToken
from app.models.enrollment import EnrollmentStatus, TargetSource, TrackEnrollment
from app.models.content import Lab, Lesson, Phase, Track, Week
from app.models.progress import LabProgress, LessonProgress, StudyActivity
from app.models.quiz import Question, QuestionType, Quiz, QuizAttempt
from app.models.user import User, UserRole

__all__ = [
    "Base",
    "TimestampMixin",
    "Phase",
    "Track",
    "TrackEnrollment",
    "TelegramLinkToken",
    "EnrollmentStatus",
    "TargetSource",
    "Week",
    "Lesson",
    "Lab",
    "Quiz",
    "Question",
    "QuestionType",
    "QuizAttempt",
    "LessonProgress",
    "LabProgress",
    "StudyActivity",
    "User",
    "UserRole",
]
