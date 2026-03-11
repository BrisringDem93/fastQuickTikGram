from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SocialAccountResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    platform: str
    external_account_id: str
    account_name: str | None
    account_avatar_url: str | None
    token_expires_at: datetime | None
    scopes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SocialConnectRequest(BaseModel):
    platform: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None
    error: str | None = None
    error_description: str | None = None
