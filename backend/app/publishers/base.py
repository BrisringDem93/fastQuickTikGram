from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.social_account import SocialAccount

logger = logging.getLogger(__name__)


class SocialPublisher(ABC):
    """Abstract base for all platform publishers."""

    def __init__(self, account: "SocialAccount") -> None:
        self.account = account

    @abstractmethod
    async def validate_account(self) -> None:
        """Verify that the connected account credentials are valid and have required permissions."""

    @abstractmethod
    async def validate_media(self, video_key: str) -> dict[str, Any]:
        """Validate the media file meets platform requirements.

        Returns a dict with validation results (duration, size, codec, etc.).
        """

    @abstractmethod
    async def upload_media(self, video_key: str) -> str:
        """Upload the media to the platform's upload endpoint.

        Returns a platform-specific media/upload ID.
        """

    @abstractmethod
    async def create_post(
        self,
        *,
        video_key: str,
        caption: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Publish the video as a post.

        Returns a dict containing at minimum: {"post_id": ..., "post_url": ...}
        """

    @abstractmethod
    async def schedule_post(
        self,
        *,
        video_key: str,
        caption: str,
        publish_at: str,
        hashtags: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Schedule a post for future publishing.

        *publish_at* is an ISO-8601 datetime string.
        Returns same structure as create_post.
        """

    @abstractmethod
    async def get_post_status(self, post_id: str) -> dict[str, Any]:
        """Retrieve the current status of a post from the platform.

        Returns a dict with at minimum: {"status": ..., "url": ...}
        """


class PublisherFactory:
    """Factory that returns the correct SocialPublisher for a given platform."""

    @staticmethod
    def get_publisher(platform: str, *, account: "SocialAccount") -> SocialPublisher:
        """Return a SocialPublisher instance for *platform*.

        Raises ValueError for unsupported platforms.
        """
        from app.publishers.youtube import YouTubePublisher
        from app.publishers.tiktok import TikTokPublisher
        from app.publishers.instagram import InstagramPublisher
        from app.publishers.facebook import FacebookPublisher

        publishers: dict[str, type[SocialPublisher]] = {
            "youtube": YouTubePublisher,
            "tiktok": TikTokPublisher,
            "instagram": InstagramPublisher,
            "facebook": FacebookPublisher,
        }
        cls = publishers.get(platform.lower())
        if cls is None:
            raise ValueError(f"No publisher registered for platform: {platform!r}")
        return cls(account)
