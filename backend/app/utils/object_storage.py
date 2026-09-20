"""Pluggable object storage for uploaded videos.

Two backends are supported, selected by `STORAGE_BACKEND`:

* ``local`` — files live under ``STORAGE_ROOT/VIDEOS_SUBDIR`` on disk. This is
  the default for local dev and ``docker-compose``.
* ``cloudinary`` — files are uploaded to Cloudinary. Uploads stream to Cloudinary;
  the streaming endpoint redirects the browser to the Cloudinary CDN URL. This
  is the recommended backend for deployed environments — sign-up, API keys,
  and video delivery are all simpler to manage than a blob-storage account.

Seeded-on-disk content keeps working under the cloud backend: when a key is
also present on the local filesystem we serve it locally. This lets the
``storage/videos/`` folder bundled in the Docker image keep working without
having to upload every seed file to the remote store.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("-", name.strip()) or "file"
    return cleaned[:200]


@dataclass(frozen=True)
class StreamTarget:
    """How the streaming endpoint should serve a stored object."""
    local_path: Optional[Path] = None
    redirect_url: Optional[str] = None

    @property
    def is_local(self) -> bool:
        return self.local_path is not None


def _videos_dir() -> Path:
    return (Path(settings.STORAGE_ROOT) / settings.VIDEOS_SUBDIR).resolve()


def _safe_local_path(key: str) -> Path:
    base = _videos_dir()
    candidate = (base / key).resolve()
    if base not in candidate.parents and candidate != base:
        raise ValueError("Resolved path escapes the videos directory")
    return candidate


class _LocalBackend:
    """Disk-backed implementation. Identical to the legacy behaviour."""

    def save_upload(
        self,
        course_slug: str,
        section_slug: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> str:
        base = _videos_dir() / course_slug / section_slug
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
        with candidate.open("wb") as out:
            shutil.copyfileobj(file_obj, out)
        return candidate.relative_to(_videos_dir()).as_posix()

    def delete(self, key: str) -> None:
        try:
            path = _safe_local_path(key)
        except ValueError:
            return
        if path.exists():
            try:
                path.unlink()
            except OSError:
                logger.warning("Failed to remove %s", path, exc_info=True)

    def get_stream_target(self, key: str) -> StreamTarget:
        path = _safe_local_path(key)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Video file not found: {key}")
        return StreamTarget(local_path=path)


_MIME_BY_EXT = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".m4v": "video/x-m4v",
}


def _guess_content_type(filename: str) -> str:
    return _MIME_BY_EXT.get(Path(filename).suffix.lower(), "application/octet-stream")


class _CloudinaryBackend:
    """Cloudinary implementation.

    Falls back to the local backend when the object key happens to exist on
    disk (useful for seeded content shipped inside the Docker image).
    """

    def __init__(self) -> None:
        import cloudinary

        missing = [
            name
            for name, val in (
                ("CLOUDINARY_CLOUD_NAME", settings.CLOUDINARY_CLOUD_NAME),
                ("CLOUDINARY_API_KEY", settings.CLOUDINARY_API_KEY),
                ("CLOUDINARY_API_SECRET", settings.CLOUDINARY_API_SECRET),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(
                "STORAGE_BACKEND=cloudinary but the following env vars are unset: "
                + ", ".join(missing)
            )

        self._cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self._api_key = settings.CLOUDINARY_API_KEY
        self._api_secret = settings.CLOUDINARY_API_SECRET
        self._folder = settings.CLOUDINARY_FOLDER.strip("/")

        cloudinary.config(
            cloud_name=self._cloud_name,
            api_key=self._api_key,
            api_secret=self._api_secret,
        )

        self._local_fallback = _LocalBackend()
        logger.info(
            "Cloudinary backend initialised (cloud=%s, folder=%s)",
            self._cloud_name,
            self._folder,
        )

    def _remote_key(self, key: str) -> str:
        # Same layout as the local backend so DB rows stay portable:
        # `videos/<course>/<section>/<file>`.
        return f"{self._folder.strip('/')}/{key.lstrip('/')}"

    def save_upload(
        self,
        course_slug: str,
        section_slug: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> str:
        import cloudinary.uploader

        safe = sanitize_filename(filename)
        stem, _, ext = safe.rpartition(".")
        if not stem:
            stem, ext = safe, "mp4"
        public_id = f"{self._folder}/{course_slug}/{section_slug}/{stem}"

        try:
            response = cloudinary.uploader.upload(
                file_obj,
                public_id=public_id,
                resource_type="video",
                overwrite=False,
                folder=self._folder,
            )
        except Exception as exc:
            raise RuntimeError(f"Upload to Cloudinary failed: {exc}") from exc

        # Return the key in the same format as local backend for DB consistency
        return f"{course_slug}/{section_slug}/{response['public_id'].split('/')[-1]}"

    def delete(self, key: str) -> None:
        import cloudinary.uploader

        try:
            cloudinary.uploader.destroy(
                self._remote_key(key),
                resource_type="video"
            )
        except Exception:
            logger.warning("Failed to delete Cloudinary asset %s", key, exc_info=True)
        # Also clean any local copy (e.g. legacy seeded file).
        self._local_fallback.delete(key)

    def get_stream_target(self, key: str) -> StreamTarget:
        # Prefer a local copy if the bundled disk has it — avoids a round-trip
        # to Cloudinary for seeded content.
        try:
            return self._local_fallback.get_stream_target(key)
        except FileNotFoundError:
            pass

        import cloudinary

        # Generate a Cloudinary delivery URL with quality optimization
        remote_key = self._remote_key(key)
        url = cloudinary.CloudinaryResource(remote_key).build_url(
            resource_type="video",
            quality="auto",
            secure=True,
        )
        return StreamTarget(redirect_url=url)


_backend: _LocalBackend | _CloudinaryBackend | None = None


def get_storage_backend() -> _LocalBackend | _CloudinaryBackend:
    """Lazily build (and cache) the configured backend."""
    global _backend
    if _backend is not None:
        return _backend
    kind = (settings.STORAGE_BACKEND or "local").strip().lower()
    if kind == "cloudinary":
        _backend = _CloudinaryBackend()
    elif kind == "local":
        _backend = _LocalBackend()
    else:
        raise RuntimeError(
            f"Unknown STORAGE_BACKEND={settings.STORAGE_BACKEND!r}. "
            "Expected one of: local, cloudinary."
        )
    return _backend
