from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class JobResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    status: str
    original_video_key: str | None
    edited_video_key: str | None
    approved_hook_id: uuid.UUID | None
    scheduled_at_utc: datetime | None
    user_timezone: str | None
    metadata: dict[str, Any] | None = Field(validation_alias="job_metadata")
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int


class VideoUploadResponse(BaseModel):
    upload_url: str
    storage_key: str
    expires_in_seconds: int


class HookGenerateRequest(BaseModel):
    prompt: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional custom instruction for hook generation",
    )


class DestinationSelectRequest(BaseModel):
    social_account_ids: list[uuid.UUID] = Field(min_length=1)


class PublishNowRequest(BaseModel):
    caption: str | None = Field(default=None, max_length=2200)
    hashtags: list[str] | None = None


class ScheduleRequest(BaseModel):
    scheduled_at: datetime
    user_timezone: str = Field(
        default="UTC",
        description="IANA timezone name e.g. 'America/New_York'",
    )
    caption: str | None = Field(default=None, max_length=2200)
    hashtags: list[str] | None = None
