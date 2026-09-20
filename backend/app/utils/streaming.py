"""HTTP Range streaming utilities for serving large media files.

Implements RFC 7233 single-range requests: parses the `Range` header,
returns 206 Partial Content with the correct `Content-Range`,
`Content-Length`, and `Accept-Ranges` headers, and yields the requested
byte slice in fixed-size chunks.
"""
from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Iterator, Tuple

from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.config import settings

_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _parse_range(range_header: str, file_size: int) -> Tuple[int, int]:
    """Parse a single-range `Range` header. Returns inclusive (start, end)."""
    match = _RANGE_RE.match(range_header.strip())
    if not match:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail="Invalid Range header",
        )

    start_s, end_s = match.group(1), match.group(2)

    if start_s == "" and end_s == "":
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail="Invalid Range header",
        )

    if start_s == "":
        # Suffix range: last N bytes.
        suffix = int(end_s)
        if suffix == 0:
            raise HTTPException(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail="Invalid suffix range",
            )
        start = max(file_size - suffix, 0)
        end = file_size - 1
    else:
        start = int(start_s)
        end = int(end_s) if end_s else file_size - 1

    if start > end or start >= file_size:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail="Requested range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    end = min(end, file_size - 1)
    return start, end


def _file_iterator(path: Path, start: int, end: int, chunk_size: int) -> Iterator[bytes]:
    """Yield bytes from `path` between inclusive offsets `start` and `end`."""
    remaining = end - start + 1
    with path.open("rb") as f:
        f.seek(start)
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


def stream_file_with_range(
    request: Request,
    path: Path,
    *,
    media_type: str | None = None,
    chunk_size: int | None = None,
    filename: str | None = None,
) -> StreamingResponse:
    """Return a StreamingResponse honouring the request's `Range` header."""
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file_size = path.stat().st_size
    chunk = chunk_size or settings.VIDEO_STREAM_CHUNK_SIZE
    mtype = media_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    range_header = request.headers.get("range") or request.headers.get("Range")

    base_headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=3600",
    }
    if filename:
        base_headers["Content-Disposition"] = f'inline; filename="{filename}"'

    if range_header is None:
        base_headers["Content-Length"] = str(file_size)
        return StreamingResponse(
            _file_iterator(path, 0, file_size - 1, chunk),
            status_code=status.HTTP_200_OK,
            media_type=mtype,
            headers=base_headers,
        )

    start, end = _parse_range(range_header, file_size)
    content_length = end - start + 1
    headers = {
        **base_headers,
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
    }
    return StreamingResponse(
        _file_iterator(path, start, end, chunk),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        media_type=mtype,
        headers=headers,
    )
