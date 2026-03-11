from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class HookResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID
    text: str
    rationale: str | None
    score: float | None
    is_selected: bool
    is_manually_edited: bool
    created_at: datetime


class HookApproveRequest(BaseModel):
    hook_id: uuid.UUID
    manual_text: str | None = Field(
        default=None,
        max_length=500,
        description="If provided, overrides the hook text with this custom text",
    )


class HookListResponse(BaseModel):
    items: list[HookResponse]
    total: int
