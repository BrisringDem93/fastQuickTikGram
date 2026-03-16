from __future__ import annotations

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
    current_user: CurrentUser,  # noqa: ARG001 – presence proves the caller is authenticated
) -> FileResponse:
    """Return a stored video or image file by its storage key.

    The storage key is the path-like string used when the file was saved,
    e.g. ``videos/{user_id}/{job_id}/original.mp4``.

    Authentication is required so that only logged-in users can retrieve
    media.  For social-platform publishing that needs a publicly reachable
    URL, set ``PUBLIC_BASE_URL`` and ensure the ``/api/v1/media`` prefix
    is accessible from the internet on your Hetzner / Coolify deployment.
    """
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
