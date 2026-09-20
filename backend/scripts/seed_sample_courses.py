"""Seed sample courses, sections, and videos by scanning the storage directory.

Layouts supported on disk:

    storage/videos/<course-slug>/<NN-section-title>/<NN-video-title>.mp4   (nested)
    storage/videos/<course-slug>/<NN-video-title>.mp4                       (flat → "Lessons")

    storage/thumbnails/<course-slug>.(jpg|png|webp)                         (optional cover)

Run from the `backend/` directory:

    python -m scripts.seed_sample_courses

This is a development helper that calls the same `sync_content` service the
app runs on startup (when `AUTO_SEED_ON_STARTUP=true`). It is idempotent:
re-running upserts by slug and replaces each course's sections/videos.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script from the `backend/` directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal  # noqa: E402
from app.services.content_sync_service import sync_content  # noqa: E402
from app.utils.storage import ensure_storage_dirs  # noqa: E402


def main() -> None:
    ensure_storage_dirs()
    with SessionLocal() as db:
        stats = sync_content(db, prune_missing_courses=True)
    print(
        f"Done. courses +{stats.courses_added} ~{stats.courses_updated} -{stats.courses_removed}, "
        f"{stats.videos_indexed} videos indexed."
    )


if __name__ == "__main__":
    main()
