"""Aggregator for v1 routers."""
from fastapi import APIRouter

from app.api.v1 import (
    activities,
    admin,
    auth,
    certificates,
    courses,
    health,
    instructor,
    progress,
    quizzes,
    videos,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(videos.router)
api_router.include_router(progress.router)
api_router.include_router(quizzes.router)
api_router.include_router(certificates.router)
api_router.include_router(activities.router)
api_router.include_router(instructor.router)
api_router.include_router(admin.router)
