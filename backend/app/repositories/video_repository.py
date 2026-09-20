"""Video repository — read access to videos and playlist neighbours."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.course import Section, Video
from app.repositories.base import BaseRepository


class VideoRepository(BaseRepository[Video]):
    model = Video

    def __init__(self, db: Session):
        super().__init__(db, Video)

    def get_with_section(self, video_id: int) -> Optional[Video]:
        stmt = (
            select(Video)
            .options(joinedload(Video.section))
            .where(Video.id == video_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()
