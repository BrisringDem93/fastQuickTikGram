from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from app.config import settings
from app.core.exceptions import PublishingError
from app.core.security import decrypt_token
from app.publishers.base import SocialPublisher
from app.services.storage_service import StorageService

if TYPE_CHECKING:
    from app.models.social_account import SocialAccount

logger = logging.getLogger(__name__)


class InstagramPublisher(SocialPublisher):
    """Publishes Reels / video content to Instagram via the Instagram Graph API.

    TODO: Before this can go live you must:
      1. Your app must be connected to a Facebook App.
      2. The Instagram account must be a Professional account (Creator or Business).
      3. Request instagram_content_publish permission and pass Facebook app review.
      4. Replace stub calls with real Graph API calls.

    Reference: https://developers.facebook.com/docs/instagram-api/guides/content-publishing
    """

    PLATFORM = "instagram"
    GRAPH_BASE = "https://graph.facebook.com/v18.0"

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
        """Verify Instagram account token and permissions.

        TODO: Call GET /{ig-user-id}?fields=id,username,account_type
        """
        logger.info(
            "[Instagram STUB] validate_account for account_id=%s", self.account.id
        )
        # TODO: Call /me/accounts to confirm the page token and ig_user_id

    async def validate_media(self, video_key: str) -> dict[str, Any]:
        """Validate video against Instagram Reels requirements.

        TODO: Instagram Reels limits:
          - Duration: 3s – 90s (for Reels), up to 60 min for regular videos
          - Aspect ratio: 9:16 (0.01:1 – 10:1 for feed videos)
          - Max size: 1 GB
          - Formats: MP4 or MOV
          - Minimum resolution: 720p
        """
        logger.info("[Instagram STUB] validate_media key=%s", video_key)
        meta = self._storage.get_object_metadata(video_key)
        return {"valid": True, "metadata": meta}

    async def upload_media(self, video_key: str) -> str:
        """Create an Instagram media container.

        TODO: For Reels:
          1. Generate a public/presigned download URL for the video.
          2. POST /{ig-user-id}/media with:
             {"media_type": "REELS", "video_url": presigned_url, "caption": caption}
          3. Poll /{media-container-id}?fields=status_code until status is FINISHED.
          4. Return the container ID.
        """
        logger.info("[Instagram STUB] upload_media key=%s", video_key)
        # TODO: Replace with real Instagram container creation
        return f"stub_ig_container_{video_key.split('/')[-1]}"

    async def create_post(
        self,
        *,
        video_key: str,
        caption: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Publish an Instagram Reel.

        TODO: After upload_media returns a container ID, call:
          POST /{ig-user-id}/media_publish with {"creation_id": container_id}
        """
        logger.info(
            "[Instagram STUB] create_post key=%s caption=%r", video_key, caption
        )
        tags_str = " ".join(f"#{t.lstrip('#')}" for t in (hashtags or []))
        full_caption = f"{caption}\n\n{tags_str}".strip()
        container_id = await self.upload_media(video_key)

        logger.info(
            "[Instagram STUB] Would publish Instagram Reel: container=%s caption=%r",
            container_id, full_caption,
        )
        stub_media_id = f"ig_media_{container_id}"
        return {
            "post_id": stub_media_id,
            "post_url": f"https://www.instagram.com/p/{stub_media_id}/",
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
        """Schedule an Instagram post.

        TODO: Pass "published": false and "scheduled_publish_time": unix_timestamp
              to the media container creation endpoint.
        """
        logger.info(
            "[Instagram STUB] schedule_post key=%s publish_at=%s", video_key, publish_at
        )
        container_id = await self.upload_media(video_key)
        stub_media_id = f"ig_media_{container_id}"
        return {
            "post_id": stub_media_id,
            "post_url": f"https://www.instagram.com/p/{stub_media_id}/",
            "scheduled_at": publish_at,
        }

    async def get_post_status(self, post_id: str) -> dict[str, Any]:
        """Retrieve the status of an Instagram media object.

        TODO: Call GET /{media-id}?fields=id,media_type,permalink,timestamp
        """
        logger.info("[Instagram STUB] get_post_status post_id=%s", post_id)
        return {"status": "published", "post_id": post_id}
