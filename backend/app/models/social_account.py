from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
import enum


class Platform(str, enum.Enum):
    youtube = "youtube"
    tiktok = "tiktok"
    instagram = "instagram"
    facebook = "facebook"


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform, name="platform_enum"), nullable=False
    )
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OAuth tokens stored encrypted at rest
    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)  # space-separated list

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", back_populates="social_accounts")  # noqa: F821
    publish_targets: Mapped[list["PublishTarget"]] = relationship(  # noqa: F821
        "PublishTarget",
        back_populates="social_account",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<SocialAccount id={self.id} platform={self.platform} user_id={self.user_id}>"
