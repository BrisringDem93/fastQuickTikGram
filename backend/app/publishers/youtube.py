from __future__ import annotations

import logging
import tempfile
from typing import Any, TYPE_CHECKING

from app.config import settings
from app.core.exceptions import PublishingError
from app.core.security import decrypt_token
from app.publishers.base import SocialPublisher
from app.services.storage_service import StorageService

if TYPE_CHECKING:
    from app.models.social_account import SocialAccount

logger = logging.getLogger(__name__)


class YouTubePublisher(SocialPublisher):
    """Publishes video content to YouTube using the YouTube Data API v3.

    TODO: Before this can go live you must:
      1. Create a Google Cloud project and enable the YouTube Data API v3.
      2. Create OAuth2 credentials (Web application) and add authorised redirect URIs.
      3. Go through Google's app review for the youtube.upload scope (required for production).
      4. Replace the stub HTTP calls below with the actual googleapis library calls.
    """

    PLATFORM = "youtube"

    def __init__(self, account: "SocialAccount") -> None:
        super().__init__(account)
        self._storage = StorageService()

    def _get_access_token(self) -> str:
        if not self.account.encrypted_access_token:
            raise PublishingError("No access token available", platform=self.PLATFORM)
        return decrypt_token(
            self.account.encrypted_access_token,
            encryption_key=settings.ENCRYPTION_KEY,
        )

    async def validate_account(self) -> None:
        """Verify that the YouTube account token is valid.

        TODO: Call https://www.googleapis.com/youtube/v3/channels?part=id&mine=true
              with the Bearer token to confirm credentials are valid.
        """
        logger.info(
            "[YouTube STUB] validate_account for account_id=%s", self.account.id
        )
        # TODO: Implement real validation
        # async with httpx.AsyncClient() as client:
        #     resp = await client.get(
        #         "https://www.googleapis.com/youtube/v3/channels",
        #         params={"part": "id", "mine": "true"},
        #         headers={"Authorization": f"Bearer {self._get_access_token()}"},
        #     )
        #     if resp.status_code != 200:
        #         raise PublishingError(f"Account validation failed: {resp.text}", platform=self.PLATFORM)

    async def validate_media(self, video_key: str) -> dict[str, Any]:
        """Validate video against YouTube's requirements.

        TODO: YouTube limits:
          - Max file size: 256 GB
          - Max duration: 12 hours (verified accounts)
          - Supported formats: .MOV, .MPEG4, .MP4, .AVI, .WMV, .MPEGPS, .FLV, 3GPP, WebM
        """
        logger.info("[YouTube STUB] validate_media key=%s", video_key)
        meta = self._storage.get_object_metadata(video_key)
        return {"valid": True, "metadata": meta}

    async def upload_media(self, video_key: str) -> str:
        """Upload video using YouTube's resumable upload API.

        TODO: Implement the resumable upload flow:
          1. POST to https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable
          2. Receive the upload URI from the Location header.
          3. Stream the video file to the upload URI in chunks.
          4. Return the YouTube video ID from the response body.

        Reference: https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
        """
        logger.info("[YouTube STUB] upload_media key=%s", video_key)
        # TODO: Replace with real resumable upload implementation
        return f"stub_youtube_video_id_{video_key.split('/')[-1]}"

    async def create_post(
        self,
        *,
        video_key: str,
        caption: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Upload the video and insert a YouTube video resource.

        TODO: After uploading the video (upload_media), call:
          POST https://www.googleapis.com/youtube/v3/videos?part=snippet,status
          with body:
          {
            "snippet": {"title": caption, "tags": hashtags, "categoryId": "22"},
            "status": {"privacyStatus": "public"}
          }
        """
        logger.info("[YouTube STUB] create_post key=%s caption=%r", video_key, caption)
        tags = hashtags or []
        stub_video_id = await self.upload_media(video_key)

        # TODO: Call YouTube insert API
        logger.info(
            "[YouTube STUB] Would create YouTube post: video_id=%s title=%r tags=%s",
            stub_video_id, caption, tags,
        )
        return {
            "post_id": stub_video_id,
            "post_url": f"https://www.youtube.com/watch?v={stub_video_id}",
        }

    async def schedule_post(
        self,
        *,
        video_key: str,
        caption: str,
        publish_at: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Schedule a YouTube video for future publishing.

        TODO: Set "status.privacyStatus": "private" and "status.publishAt": publish_at
              in the videos.insert request body.
        """
        logger.info(
            "[YouTube STUB] schedule_post key=%s publish_at=%s", video_key, publish_at
        )
        stub_video_id = await self.upload_media(video_key)
        return {
            "post_id": stub_video_id,
            "post_url": f"https://www.youtube.com/watch?v={stub_video_id}",
            "scheduled_at": publish_at,
        }

    async def get_post_status(self, post_id: str) -> dict[str, Any]:
        """Get the current status of a YouTube video.

        TODO: Call https://www.googleapis.com/youtube/v3/videos?part=status&id={post_id}
        """
        logger.info("[YouTube STUB] get_post_status post_id=%s", post_id)
        return {"status": "uploaded", "url": f"https://www.youtube.com/watch?v={post_id}"}
