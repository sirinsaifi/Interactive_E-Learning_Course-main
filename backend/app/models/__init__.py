"""ORM models package.

Import every model module here so Alembic's autogenerate discovers
all tables via `Base.metadata`.
"""
from app.models.activity import ActivityCompletion, InteractiveActivity
from app.models.course import Course, Section, Video
from app.models.progress import VideoProgress
from app.models.quiz import Quiz, QuizAttempt, QuizQuestion
from app.models.user import User

__all__ = [
    "Course",
    "Section",
    "Video",
    "User",
    "VideoProgress",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "InteractiveActivity",
    "ActivityCompletion",
]
