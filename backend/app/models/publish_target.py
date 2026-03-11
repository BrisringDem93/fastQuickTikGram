from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PublishTargetStatus(str, enum.Enum):
    pending = "pending"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    scheduled = "scheduled"


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class PublishTarget(Base):
    __tablename__ = "publish_targets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[PublishTargetStatus] = mapped_column(
        Enum(PublishTargetStatus, name="publish_target_status_enum"),
        default=PublishTargetStatus.pending,
        nullable=False,
    )
    scheduled_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    job: Mapped["ContentJob"] = relationship("ContentJob", back_populates="publish_targets")  # noqa: F821
    social_account: Mapped["SocialAccount"] = relationship(  # noqa: F821
        "SocialAccount", back_populates="publish_targets"
    )
    attempts: Mapped[list["PublishAttempt"]] = relationship(  # noqa: F821
        "PublishAttempt",
        back_populates="publish_target",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<PublishTarget id={self.id} platform={self.platform} status={self.status}>"
