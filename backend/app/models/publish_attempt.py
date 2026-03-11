from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class PublishAttempt(Base):
    __tablename__ = "publish_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    publish_target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("publish_targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    publish_target: Mapped["PublishTarget"] = relationship(  # noqa: F821
        "PublishTarget", back_populates="attempts"
    )

    def __repr__(self) -> str:
        return (
            f"<PublishAttempt id={self.id} attempt={self.attempt_number} status={self.status}>"
        )
