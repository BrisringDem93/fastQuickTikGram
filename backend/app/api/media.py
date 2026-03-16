from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser
from app.core.exceptions import AppException
from app.services.storage_service import StorageService

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{path:path}", summary="Stream a stored media file")
async def serve_media(
    path: str,
    current_user: CurrentUser,
) -> FileResponse:
    """Return a stored video or image file by its storage key.

    The storage key is the path-like string used when the file was saved,
    e.g. ``videos/{user_id}/{job_id}/original.mp4``.

    Ownership is verified by comparing the ``{user_id}`` segment of the path
    against the authenticated user's ID so that users cannot access each
    other's media.
    """
    # Verify ownership: storage keys follow the pattern
    # "videos/{user_id}/{job_id}/..." – extract and validate the user segment.
    # Paths that are too short or contain a non-UUID user segment are rejected.
    parts = Path(path).parts
    if len(parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )
    try:
        path_user_id = uuid.UUID(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )
    if path_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    storage = StorageService()
    try:
        abs_path: Path = storage.get_file_path(path)
    except AppException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid media path.",
        )

    if not abs_path.exists() or not abs_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found.",
        )

    return FileResponse(path=abs_path)