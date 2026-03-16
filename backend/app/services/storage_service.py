from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import unquote

from app.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class StorageService:
    """Local filesystem-based object storage service.

    Files are stored under ``settings.UPLOAD_DIR`` using the same
    ``key`` path convention previously used for S3 objects, e.g.
    ``videos/{user_id}/{job_id}/original.mp4``.

    For social-platform publishing that requires a publicly reachable
    video URL, set ``PUBLIC_BASE_URL`` in the environment to the public
    root of the backend (e.g. ``https://api.yourdomain.com``).  The
    ``generate_presigned_download_url`` method will return
    ``{PUBLIC_BASE_URL}/api/v1/media/{key}``.
    """

    def __init__(self) -> None:
        self._upload_dir = Path(settings.UPLOAD_DIR)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_key(self, key: str) -> Path:
        """Resolve *key* to an absolute path, guarding against path traversal.

        Both plain ``../..`` and URL-encoded ``%2F``-style traversals are blocked.
        """
        # Decode percent-encoding before resolving so that encoded traversals
        # (e.g. ``..%2F..%2Fetc%2Fpasswd``) are caught the same way as plain ones.
        decoded = unquote(key)
        normalised = Path(decoded.lstrip("/"))
        resolved = (self._upload_dir / normalised).resolve()
        upload_dir_resolved = self._upload_dir.resolve()
        # The resolved path must be the upload dir itself or a file inside it.
        within_dir = str(resolved).startswith(str(upload_dir_resolved) + os.sep)
        if not (within_dir or resolved == upload_dir_resolved):
            raise AppException(f"Invalid storage key: {key!r}")
        return resolved

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_fileobj(self, fileobj: BinaryIO, key: str) -> None:
        """Write *fileobj* to local storage under *key*."""
        dest = self._resolve_key(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(dest, "wb") as f:
                shutil.copyfileobj(fileobj, f)
        except OSError as exc:
            logger.exception("Failed to write storage object key=%s", key)
            raise AppException(f"Storage write error: {exc}") from exc

    def generate_presigned_download_url(self, key: str) -> str:
        """Return a URL that serves the stored object through the backend API.

        For the URL to be reachable by external services (e.g. Instagram),
        set ``PUBLIC_BASE_URL`` in your environment to the public HTTPS root
        of the backend (e.g. ``https://api.yourdomain.com``).
        """
        base = settings.PUBLIC_BASE_URL.rstrip("/")
        return f"{base}/api/v1/media/{key}"

    def delete_object(self, key: str) -> None:
        """Delete a stored file. Silently succeeds if the key does not exist."""
        path = self._resolve_key(key)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.exception("Failed to delete storage object key=%s", key)
            raise AppException(f"Storage error: {exc}") from exc

    def get_object_metadata(self, key: str) -> dict[str, Any]:
        """Return basic metadata for a stored file."""
        path = self._resolve_key(key)
        if not path.exists():
            raise AppException(f"Object not found in storage: {key}")
        stat = path.stat()
        return {
            "content_length": stat.st_size,
            "content_type": None,
            "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            "etag": None,
        }

    def copy_object(self, source_key: str, dest_key: str) -> None:
        """Copy a stored file to a new key."""
        src = self._resolve_key(source_key)
        dst = self._resolve_key(dest_key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except OSError as exc:
            logger.exception("Failed to copy storage object %s → %s", source_key, dest_key)
            raise AppException(f"Storage error: {exc}") from exc

    def download_file(self, key: str, local_path: str) -> None:
        """Copy a stored file to *local_path* (used by Celery workers)."""
        src = self._resolve_key(key)
        try:
            shutil.copy2(src, local_path)
        except OSError as exc:
            logger.exception("Failed to download storage object key=%s", key)
            raise AppException(f"Storage download error: {exc}") from exc

    def upload_file(self, local_path: str, key: str) -> None:
        """Copy a local file into storage under *key* (used by Celery workers)."""
        dest = self._resolve_key(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(local_path, dest)
        except OSError as exc:
            logger.exception("Failed to upload file to storage key=%s", key)
            raise AppException(f"Storage upload error: {exc}") from exc

    def get_file_path(self, key: str) -> Path:
        """Return the absolute filesystem path for *key* (for serving via FileResponse)."""
        return self._resolve_key(key)
