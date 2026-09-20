"""Video endpoints — metadata and range-aware streaming."""
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.course import VideoRead
from app.services.video_service import VideoService
from app.utils.streaming import stream_file_with_range

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/{video_id}", response_model=VideoRead, summary="Get video metadata")
def get_video(video_id: int, db: Session = Depends(db_session)) -> VideoRead:
    return VideoService(db).get_metadata(video_id)


@router.get(
    "/{video_id}/stream",
    summary="Stream a video or serve an HTML module",
    response_class=None,
    responses={
        200: {"content": {"video/*": {}, "text/html": {}}, "description": "Full content"},
        206: {"content": {"video/*": {}}, "description": "Partial content"},
        302: {"description": "Redirect to remote object storage URL"},
        404: {"description": "Video not found"},
        416: {"description": "Requested range not satisfiable"},
    },
)
def stream_video(video_id: int, request: Request, db: Session = Depends(db_session)):
    video, target = VideoService(db).resolve_stream(video_id)

    if target.is_local and target.local_path is not None:
        local_path: Path = target.local_path
        # HTML interactive modules: serve directly as a page, no range logic needed.
        if local_path.suffix.lower() == ".html":
            return FileResponse(
                path=str(local_path),
                media_type="text/html",
                content_disposition_type="inline",
                headers={"Cache-Control": "no-store"},
            )
        # Regular media file: honour Range header for seeking.
        return stream_file_with_range(request, local_path, filename=local_path.name)

    # Remote object (R2 / public CDN): redirect the browser.
    return RedirectResponse(url=target.redirect_url, status_code=302)
