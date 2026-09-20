"""Video service — metadata and file resolution for streaming."""
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.course import Video
from app.repositories.video_repository import VideoRepository
from app.schemas.course import VideoRead
from app.utils.object_storage import StreamTarget, get_storage_backend


class VideoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VideoRepository(db)

    def get_metadata(self, video_id: int) -> VideoRead:
        video = self.repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")
        ext = Path(video.file_path).suffix.lower() if video.file_path else ""
        content_type = "html" if ext == ".html" else "video"
        return VideoRead.model_validate(
            {
                "id": video.id,
                "section_id": video.section_id,
                "title": video.title,
                "description": video.description,
                "duration_seconds": video.duration_seconds,
                "order_index": video.order_index,
                "content_type": content_type,
                "stream_url": f"/api/v1/videos/{video.id}/stream",
                "created_at": video.created_at,
                "updated_at": video.updated_at,
            }
        )

    def resolve_stream(self, video_id: int) -> tuple[Video, StreamTarget]:
        video = self.repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")
        try:
            target = get_storage_backend().get_stream_target(video.file_path)
        except FileNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        return video, target

    # Back-compat alias used by older callers/tests.
    def resolve_file(self, video_id: int) -> tuple[Video, Path]:
        video, target = self.resolve_stream(video_id)
        if not target.is_local or target.local_path is None:
            raise NotFoundError(
                f"Video {video_id} is stored remotely and cannot be opened as a local file"
            )
        return video, target.local_path
