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


class TikTokPublisher(SocialPublisher):
    """Publishes video content to TikTok using the TikTok Content Posting API.

    TODO: Before this can go live you must:
      1. Register on https://developers.tiktok.com/ and create an app.
      2. Request the "Content Posting API" permission and "video.publish" scope.
      3. Complete TikTok's app review process (may take several weeks).
      4. Replace the stub calls below with the real Content Posting API flow.

    Reference: https://developers.tiktok.com/doc/content-posting-api-get-started
    """

    PLATFORM = "tiktok"

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
        """Verify TikTok account token.

        TODO: Call https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name
        """
        logger.info("[TikTok STUB] validate_account for account_id=%s", self.account.id)
        # TODO: Implement real validation with TikTok /user/info/ endpoint

    async def validate_media(self, video_key: str) -> dict[str, Any]:
        """Validate video against TikTok requirements.

        TODO: TikTok limits:
          - Max file size: 4 GB (direct post) / 64 MB (chunk upload per chunk)
          - Duration: 3s – 10 min
          - Aspect ratio: 9:16 recommended
          - Formats: .mp4, .mov, .webm
        """
        logger.info("[TikTok STUB] validate_media key=%s", video_key)
        meta = self._storage.get_object_metadata(video_key)
        return {"valid": True, "metadata": meta}

    async def upload_media(self, video_key: str) -> str:
        """Upload video to TikTok's upload inbox.

        TODO: Implement the TikTok file upload flow:
          1. POST /v2/post/publish/inbox/video/init/ to initialise the upload.
          2. Upload chunks to the returned upload_url.
          3. Return the publish_id from the init response.

        Reference: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
        """
        logger.info("[TikTok STUB] upload_media key=%s", video_key)
        # TODO: Replace with real TikTok upload
        return f"stub_tiktok_publish_id_{video_key.split('/')[-1]}"

    async def create_post(
        self,
        *,
        video_key: str,
        caption: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a TikTok post.

        TODO: After uploading, call POST /v2/post/publish/video/init/ with:
          {
            "post_info": {"title": caption, "privacy_level": "PUBLIC_TO_EVERYONE"},
            "source_info": {"source": "FILE_UPLOAD", "video_size": ..., "chunk_size": ..., "total_chunk_count": ...}
          }
        """
        logger.info("[TikTok STUB] create_post key=%s caption=%r", video_key, caption)
        tags_str = " ".join(f"#{t.lstrip('#')}" for t in (hashtags or []))
        full_caption = f"{caption} {tags_str}".strip()
        stub_publish_id = await self.upload_media(video_key)

        logger.info(
            "[TikTok STUB] Would publish TikTok video: publish_id=%s caption=%r",
            stub_publish_id, full_caption,
        )
        return {
            "post_id": stub_publish_id,
            "post_url": f"https://www.tiktok.com/@{self.account.account_name}/video/{stub_publish_id}",
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
        """Schedule a TikTok post.

        TODO: TikTok does not natively support scheduled posts via API (as of 2024).
              Implement this using Celery Beat to trigger create_post at the scheduled time.
        """
        logger.info(
            "[TikTok STUB] schedule_post key=%s publish_at=%s", video_key, publish_at
        )
        stub_publish_id = await self.upload_media(video_key)
        return {
            "post_id": stub_publish_id,
            "post_url": f"https://www.tiktok.com/@{self.account.account_name}/video/{stub_publish_id}",
            "scheduled_at": publish_at,
        }

    async def get_post_status(self, post_id: str) -> dict[str, Any]:
        """Check TikTok post publish status.

        TODO: Call POST /v2/post/publish/status/fetch/ with {"publish_id": post_id}
        """
        logger.info("[TikTok STUB] get_post_status post_id=%s", post_id)
        return {"status": "processing", "post_id": post_id}
