from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    VIDEO_UPLOADED = "VIDEO_UPLOADED"
    HOOK_GENERATING = "HOOK_GENERATING"
    HOOK_PENDING_APPROVAL = "HOOK_PENDING_APPROVAL"
    HOOK_REJECTED = "HOOK_REJECTED"
    HOOK_APPROVED = "HOOK_APPROVED"
    VIDEO_EDITING = "VIDEO_EDITING"
    VIDEO_READY = "VIDEO_READY"
    WAITING_FOR_SOCIAL_CONNECTION = "WAITING_FOR_SOCIAL_CONNECTION"
    DESTINATIONS_SELECTED = "DESTINATIONS_SELECTED"
    READY_TO_PUBLISH = "READY_TO_PUBLISH"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class ContentJob(Base):
    __tablename__ = "content_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        default=JobStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # S3 keys for video files
    original_video_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    edited_video_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # The approved hook text/id
    approved_hook_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_hooks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scheduling
    scheduled_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Arbitrary extra metadata (e.g. caption, tags, hashtags)
    job_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

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
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", back_populates="content_jobs")  # noqa: F821
    assets: Mapped[list["JobAsset"]] = relationship(  # noqa: F821
        "JobAsset",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select",
        foreign_keys="JobAsset.job_id",
    )
    hooks: Mapped[list["JobHook"]] = relationship(  # noqa: F821
        "JobHook",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select",
        foreign_keys="JobHook.job_id",
    )
    publish_targets: Mapped[list["PublishTarget"]] = relationship(  # noqa: F821
        "PublishTarget",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<ContentJob id={self.id} status={self.status} title={self.title!r}>"
