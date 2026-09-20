"""Repositories package.

Each repository encapsulates persistence logic for a single aggregate.
Services depend on repositories — routers must NOT use SQLAlchemy directly.
"""
from app.repositories.base import BaseRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.video_repository import VideoRepository

__all__ = ["BaseRepository", "CourseRepository", "UserRepository", "VideoRepository"]
