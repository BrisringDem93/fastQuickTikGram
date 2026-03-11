from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PublishAttemptResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    publish_target_id: uuid.UUID
    attempt_number: int
    status: str
    error_message: str | None
    response_data: dict[str, Any] | None
    attempted_at: datetime


class PublishTargetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID
    social_account_id: uuid.UUID
    platform: str
    status: str
    scheduled_at_utc: datetime | None
    published_at: datetime | None
    external_post_id: str | None
    external_post_url: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    attempts: list[PublishAttemptResponse] = []


class PublishStatusResponse(BaseModel):
    job_id: uuid.UUID
    overall_status: str
    targets: list[PublishTargetResponse]
    published_count: int
    failed_count: int
    pending_count: int
