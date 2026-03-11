from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AssetType(str, enum.Enum):
    original_video = "original_video"
    edited_video = "edited_video"
    thumbnail = "thumbnail"


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class JobAsset(Base):
    __tablename__ = "job_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type_enum"), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)       # bytes
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    job: Mapped["ContentJob"] = relationship(  # noqa: F821
        "ContentJob",
        back_populates="assets",
        foreign_keys=[job_id],
    )

    def __repr__(self) -> str:
        return f"<JobAsset id={self.id} type={self.asset_type} job_id={self.job_id}>"
