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


class FacebookPublisher(SocialPublisher):
    """Publishes video content to a Facebook Page using the Graph API.

    TODO: Before this can go live you must:
      1. Create a Facebook App at https://developers.facebook.com/
      2. Request publish_video and pages_manage_posts permissions.
      3. Complete the App Review process with a demo of the publishing flow.
      4. Replace stub calls with real Graph API requests.

    Reference:
      - https://developers.facebook.com/docs/video-api/guides/publishing
      - https://developers.facebook.com/docs/pages/publishing
    """

    PLATFORM = "facebook"
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
        """Verify the Facebook Page access token.

        TODO: Call GET /me?fields=id,name,access_token&access_token={page_token}
              to confirm the token is valid and has the required permissions.
        """
        logger.info(
            "[Facebook STUB] validate_account for account_id=%s", self.account.id
        )
        # TODO: Validate by calling /me/permissions and checking publish_video + pages_manage_posts

    async def validate_media(self, video_key: str) -> dict[str, Any]:
        """Validate video against Facebook's requirements.

        TODO: Facebook video requirements:
          - Max size: 10 GB (Reels max 1 GB)
          - Duration: up to 240 min for videos, 90s for Reels
          - Aspect ratio: 9:16 for Reels, 16:9 for landscape videos
          - Format: MP4, MOV preferred
          - Minimum resolution: 1080p for Reels
        """
        logger.info("[Facebook STUB] validate_media key=%s", video_key)
        meta = self._storage.get_object_metadata(video_key)
        return {"valid": True, "metadata": meta}

    async def upload_media(self, video_key: str) -> str:
        """Upload a video to a Facebook Page.

        TODO: Use the resumable upload API:
          1. POST /{page-id}/videos?fields=id&upload_phase=start
          2. Upload chunks to the returned upload_session_id.
          3. POST /{page-id}/videos with upload_phase=finish and the upload_session_id.
          4. Return the video ID from the response.

        Reference: https://developers.facebook.com/docs/video-api/guides/publishing#resumable-upload
        """
        logger.info("[Facebook STUB] upload_media key=%s", video_key)
        # TODO: Replace with real Facebook video upload
        return f"stub_fb_video_id_{video_key.split('/')[-1]}"

    async def create_post(
        self,
        *,
        video_key: str,
        caption: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Publish a video to the Facebook Page.

        TODO: After upload_media, call:
          POST /{page-id}/videos with:
          {"video_id": ..., "description": caption, "published": true}
        """
        logger.info(
            "[Facebook STUB] create_post key=%s caption=%r", video_key, caption
        )
        tags_str = " ".join(f"#{t.lstrip('#')}" for t in (hashtags or []))
        full_description = f"{caption}\n\n{tags_str}".strip()
        stub_video_id = await self.upload_media(video_key)

        logger.info(
            "[Facebook STUB] Would publish Facebook video: video_id=%s description=%r",
            stub_video_id, full_description,
        )
        return {
            "post_id": stub_video_id,
            "post_url": f"https://www.facebook.com/video/{stub_video_id}",
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
        """Schedule a Facebook video post.

        TODO: Include "published": false and "scheduled_publish_time": unix_timestamp
              in the videos POST request body.
        """
        logger.info(
            "[Facebook STUB] schedule_post key=%s publish_at=%s", video_key, publish_at
        )
        stub_video_id = await self.upload_media(video_key)
        return {
            "post_id": stub_video_id,
            "post_url": f"https://www.facebook.com/video/{stub_video_id}",
            "scheduled_at": publish_at,
        }

    async def get_post_status(self, post_id: str) -> dict[str, Any]:
        """Check the processing/publish status of a Facebook video.

        TODO: Call GET /{video-id}?fields=status,permalink_url
        """
        logger.info("[Facebook STUB] get_post_status post_id=%s", post_id)
        return {"status": "ready", "post_id": post_id}
