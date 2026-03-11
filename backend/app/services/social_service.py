from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppException, NotFoundError, PermissionError
from app.core.security import decrypt_token, encrypt_token
from app.models.social_account import Platform, SocialAccount

logger = logging.getLogger(__name__)

# State tokens are stored in-memory here for simplicity.
# In production, store these in Redis with a TTL.
_oauth_states: dict[str, dict[str, Any]] = {}

# ------------------------------------------------------------------
# Platform OAuth configuration helpers
# ------------------------------------------------------------------

_PLATFORM_CONFIG: dict[str, dict[str, str]] = {
    Platform.youtube.value: {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
        "client_id_key": "YOUTUBE_CLIENT_ID",
        "client_secret_key": "YOUTUBE_CLIENT_SECRET",
        "redirect_uri_key": "YOUTUBE_REDIRECT_URI",
    },
    Platform.tiktok.value: {
        "auth_url": "https://www.tiktok.com/v2/auth/authorize/",
        "token_url": "https://open.tiktokapis.com/v2/oauth/token/",
        "scope": "user.info.basic,video.upload,video.publish",
        "client_id_key": "TIKTOK_CLIENT_KEY",
        "client_secret_key": "TIKTOK_CLIENT_SECRET",
        "redirect_uri_key": "TIKTOK_REDIRECT_URI",
    },
    Platform.instagram.value: {
        "auth_url": "https://api.instagram.com/oauth/authorize",
        "token_url": "https://api.instagram.com/oauth/access_token",
        "scope": "instagram_basic,instagram_content_publish,pages_read_engagement",
        "client_id_key": "INSTAGRAM_CLIENT_ID",
        "client_secret_key": "INSTAGRAM_CLIENT_SECRET",
        "redirect_uri_key": "INSTAGRAM_REDIRECT_URI",
    },
    Platform.facebook.value: {
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scope": "pages_manage_posts,pages_read_engagement,publish_video",
        "client_id_key": "FACEBOOK_APP_ID",
        "client_secret_key": "FACEBOOK_APP_SECRET",
        "redirect_uri_key": "FACEBOOK_REDIRECT_URI",
    },
}


def _get_platform_setting(cfg: dict[str, str], key: str) -> str:
    attr = cfg[key]
    return getattr(settings, attr, "")


class SocialService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_oauth_url(self, *, platform: str, user_id: uuid.UUID) -> str:
        """Generate the OAuth authorization URL for the given platform."""
        cfg = _PLATFORM_CONFIG.get(platform)
        if not cfg:
            raise AppException(f"Unsupported platform: {platform!r}")

        client_id = _get_platform_setting(cfg, "client_id_key")
        if not client_id:
            raise AppException(f"Platform {platform!r} is not configured on this server")

        state = secrets.token_urlsafe(32)
        _oauth_states[state] = {"platform": platform, "user_id": str(user_id)}

        params: dict[str, str] = {
            "client_id": client_id,
            "redirect_uri": _get_platform_setting(cfg, "redirect_uri_key"),
            "scope": cfg["scope"],
            "response_type": "code",
            "state": state,
            "access_type": "offline",  # For Google / YouTube
        }
        return f"{cfg['auth_url']}?{urlencode(params)}"

    async def handle_callback(
        self,
        *,
        platform: str,
        code: str,
        state: str | None,
        user_id: uuid.UUID,
    ) -> SocialAccount:
        """Exchange *code* for tokens and upsert the SocialAccount."""
        cfg = _PLATFORM_CONFIG.get(platform)
        if not cfg:
            raise AppException(f"Unsupported platform: {platform!r}")

        # Validate state token
        if state:
            state_data = _oauth_states.pop(state, None)
            if state_data is None:
                raise AppException("Invalid or expired OAuth state token")
            if state_data.get("user_id") != str(user_id):
                raise AppException("OAuth state user mismatch")

        token_data = await self._exchange_code_for_tokens(cfg, code)

        access_token: str = token_data.get("access_token", "")
        refresh_token: str = token_data.get("refresh_token", "")
        expires_in: int = int(token_data.get("expires_in", 3600))
        scope: str = token_data.get("scope", cfg["scope"])

        token_expires_at = datetime.now(tz=timezone.utc).replace(
            microsecond=0
        )
        token_expires_at = token_expires_at + timedelta(seconds=expires_in)

        external_id, account_name = await self._fetch_profile(platform, access_token)

        # Upsert social account
        existing_result = await self._db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == Platform(platform),
                SocialAccount.external_account_id == external_id,
            )
        )
        account = existing_result.scalar_one_or_none()

        enc_access = encrypt_token(access_token, encryption_key=settings.ENCRYPTION_KEY)
        enc_refresh = encrypt_token(refresh_token, encryption_key=settings.ENCRYPTION_KEY) if refresh_token else None

        if account is None:
            account = SocialAccount(
                user_id=user_id,
                platform=Platform(platform),
                external_account_id=external_id,
                account_name=account_name,
                encrypted_access_token=enc_access,
                encrypted_refresh_token=enc_refresh,
                token_expires_at=token_expires_at,
                scopes=scope,
                is_active=True,
            )
            self._db.add(account)
        else:
            account.encrypted_access_token = enc_access
            account.encrypted_refresh_token = enc_refresh
            account.token_expires_at = token_expires_at
            account.scopes = scope
            account.is_active = True
            account.account_name = account_name

        await self._db.flush()
        await self._db.refresh(account)
        return account

    async def _exchange_code_for_tokens(
        self, cfg: dict[str, str], code: str
    ) -> dict[str, Any]:
        """Exchange the authorization code for access/refresh tokens."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                cfg["token_url"],
                data={
                    "client_id": _get_platform_setting(cfg, "client_id_key"),
                    "client_secret": _get_platform_setting(cfg, "client_secret_key"),
                    "redirect_uri": _get_platform_setting(cfg, "redirect_uri_key"),
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
        if resp.status_code >= 400:
            raise AppException(
                f"Token exchange failed ({resp.status_code}): {resp.text}"
            )
        return resp.json()

    async def _fetch_profile(
        self, platform: str, access_token: str
    ) -> tuple[str, str]:
        """Return (external_id, display_name) for the authenticated platform user."""
        try:
            if platform == Platform.youtube.value:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://www.googleapis.com/youtube/v3/channels",
                        params={"part": "snippet", "mine": "true"},
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                data = resp.json()
                item = data.get("items", [{}])[0]
                return (
                    item.get("id", "unknown"),
                    item.get("snippet", {}).get("title", "YouTube Channel"),
                )

            if platform == Platform.tiktok.value:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://open.tiktokapis.com/v2/user/info/",
                        params={"fields": "open_id,display_name"},
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                data = resp.json().get("data", {}).get("user", {})
                return data.get("open_id", "unknown"), data.get("display_name", "TikTok User")

            if platform == Platform.instagram.value:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://graph.instagram.com/me",
                        params={"fields": "id,username", "access_token": access_token},
                    )
                data = resp.json()
                return data.get("id", "unknown"), data.get("username", "Instagram User")

            if platform == Platform.facebook.value:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://graph.facebook.com/me",
                        params={"fields": "id,name", "access_token": access_token},
                    )
                data = resp.json()
                return data.get("id", "unknown"), data.get("name", "Facebook User")
        except Exception as exc:
            logger.warning("Could not fetch profile for platform %s: %s", platform, exc)

        return "unknown", platform.capitalize()

    async def list_accounts(self, *, user_id: uuid.UUID) -> list[SocialAccount]:
        """Return all active social accounts for a user."""
        result = await self._db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def delete_account(
        self, *, account_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Soft-delete a social account (marks is_active=False)."""
        account = await self._db.get(SocialAccount, account_id)
        if account is None:
            raise NotFoundError("SocialAccount", account_id)
        if account.user_id != user_id:
            raise PermissionError("delete", "SocialAccount")
        account.is_active = False
        await self._db.flush()

    async def refresh_token_if_needed(self, account: SocialAccount) -> SocialAccount:
        """Refresh the OAuth token if it is close to expiry (within 5 minutes)."""
        if account.token_expires_at is None:
            return account

        now = datetime.now(tz=timezone.utc)
        if account.token_expires_at > now + timedelta(minutes=5):
            return account

        cfg = _PLATFORM_CONFIG.get(account.platform.value)
        if not cfg or not account.encrypted_refresh_token:
            return account

        refresh_token = decrypt_token(
            account.encrypted_refresh_token,
            encryption_key=settings.ENCRYPTION_KEY,
        )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                cfg["token_url"],
                data={
                    "client_id": _get_platform_setting(cfg, "client_id_key"),
                    "client_secret": _get_platform_setting(cfg, "client_secret_key"),
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )

        if resp.status_code >= 400:
            logger.error(
                "Token refresh failed for account %s: %s", account.id, resp.text
            )
            return account

        token_data = resp.json()
        new_access = token_data.get("access_token", "")
        expires_in = int(token_data.get("expires_in", 3600))

        account.encrypted_access_token = encrypt_token(
            new_access, encryption_key=settings.ENCRYPTION_KEY
        )
        account.token_expires_at = now + timedelta(seconds=expires_in)
        await self._db.flush()
        await self._db.refresh(account)
        return account
