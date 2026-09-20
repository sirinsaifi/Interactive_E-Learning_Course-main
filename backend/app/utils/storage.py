"""Storage path helpers for video and thumbnail files.

All paths in the database are *relative* to the configured storage root.
This module is the only place that joins those relative paths with the
absolute on-disk location.
"""
import re
from pathlib import Path

from app.core.config import settings


def storage_root() -> Path:
    return Path(settings.STORAGE_ROOT).resolve()


def videos_dir() -> Path:
    return storage_root() / settings.VIDEOS_SUBDIR


def thumbnails_dir() -> Path:
    return storage_root() / settings.THUMBNAILS_SUBDIR


def ensure_storage_dirs() -> None:
    videos_dir().mkdir(parents=True, exist_ok=True)
    thumbnails_dir().mkdir(parents=True, exist_ok=True)


def resolve_video_path(relative_path: str) -> Path:
    """Resolve a stored relative path to an absolute path, preventing traversal."""
    base = videos_dir()
    candidate = (base / relative_path).resolve()
    if base not in candidate.parents and candidate != base:
        raise ValueError("Resolved path escapes the videos directory")
    return candidate


def thumbnail_url(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    prefix = settings.THUMBNAILS_URL_PREFIX.rstrip("/")
    return f"{prefix}/{relative_path.lstrip('/')}"


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """Reduce an uploaded filename to a safe relative-path segment."""
    cleaned = _SAFE_NAME_RE.sub("-", name.strip()) or "file"
    return cleaned[:200]


def unique_video_path(course_slug: str, section_slug: str, filename: str) -> tuple[Path, str]:
    """Return (absolute_path, relative_path) for a new uploaded video.

    Creates the parent directory and disambiguates by suffixing -N if needed.
    """
    base = videos_dir() / course_slug / section_slug
    base.mkdir(parents=True, exist_ok=True)
    safe = sanitize_filename(filename)
    stem, _, ext = safe.rpartition(".")
    if not stem:
        stem, ext = safe, "mp4"
    candidate = base / f"{stem}.{ext}"
    counter = 1
    while candidate.exists():
        candidate = base / f"{stem}-{counter}.{ext}"
        counter += 1
    rel = candidate.relative_to(videos_dir()).as_posix()
    return candidate, rel
