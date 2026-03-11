from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class StorageService:
    """Wraps boto3 for S3-compatible object storage operations."""

    def __init__(self) -> None:
        kwargs: dict[str, Any] = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": settings.S3_REGION,
            "config": Config(signature_version="s3v4"),
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self._s3 = boto3.client("s3", **kwargs)
        self._bucket = settings.S3_BUCKET

    def generate_presigned_upload_url(
        self,
        key: str,
        *,
        content_type: str = "application/octet-stream",
        expires_in: int = 3600,
        max_size_bytes: int | None = None,
    ) -> str:
        """Return a presigned PUT URL for direct client-side uploads."""
        params: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": key,
            "ContentType": content_type,
        }
        if max_size_bytes:
            params["ContentLength"] = max_size_bytes

        try:
            url: str = self._s3.generate_presigned_url(
                ClientMethod="put_object",
                Params=params,
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
            return url
        except ClientError as exc:
            logger.exception("Failed to generate presigned upload URL for key=%s", key)
            raise AppException(f"Storage error: {exc}") from exc

    def generate_presigned_download_url(
        self,
        key: str,
        *,
        expires_in: int = 3600,
    ) -> str:
        """Return a presigned GET URL for secure object downloads."""
        try:
            url: str = self._s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as exc:
            logger.exception("Failed to generate presigned download URL for key=%s", key)
            raise AppException(f"Storage error: {exc}") from exc

    def delete_object(self, key: str) -> None:
        """Delete an object from S3. Silently succeeds if key doesn't exist."""
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            logger.exception("Failed to delete S3 object key=%s", key)
            raise AppException(f"Storage error: {exc}") from exc

    def get_object_metadata(self, key: str) -> dict[str, Any]:
        """Return the object's metadata dict (HeadObject response)."""
        try:
            response = self._s3.head_object(Bucket=self._bucket, Key=key)
            return {
                "content_length": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
            }
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise AppException(f"Object not found in storage: {key}") from exc
            logger.exception("Failed to get metadata for S3 object key=%s", key)
            raise AppException(f"Storage error: {exc}") from exc

    def copy_object(self, source_key: str, dest_key: str) -> None:
        """Copy an object within the same bucket."""
        try:
            self._s3.copy_object(
                Bucket=self._bucket,
                CopySource={"Bucket": self._bucket, "Key": source_key},
                Key=dest_key,
            )
        except ClientError as exc:
            logger.exception("Failed to copy S3 object from %s to %s", source_key, dest_key)
            raise AppException(f"Storage error: {exc}") from exc

    def download_file(self, key: str, local_path: str) -> None:
        """Download an S3 object to a local path."""
        try:
            self._s3.download_file(self._bucket, key, local_path)
        except ClientError as exc:
            logger.exception("Failed to download S3 object key=%s", key)
            raise AppException(f"Storage download error: {exc}") from exc

    def upload_file(self, local_path: str, key: str, content_type: str | None = None) -> None:
        """Upload a local file to S3."""
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        try:
            self._s3.upload_file(local_path, self._bucket, key, ExtraArgs=extra_args or None)
        except ClientError as exc:
            logger.exception("Failed to upload file to S3 key=%s", key)
            raise AppException(f"Storage upload error: {exc}") from exc
