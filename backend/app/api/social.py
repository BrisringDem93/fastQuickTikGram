from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import AppException, NotFoundError, PermissionError
from app.schemas.social import OAuthCallbackRequest, SocialAccountResponse
from app.services.social_service import SocialService

router = APIRouter(prefix="/social", tags=["social"])


def _raise_for_app_exception(exc: AppException) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


@router.get("/accounts", response_model=list[SocialAccountResponse])
async def list_accounts(db: DBDep, current_user: CurrentUser) -> list[SocialAccountResponse]:
    """List all social accounts connected by the current user."""
    service = SocialService(db)
    accounts = await service.list_accounts(user_id=current_user.id)
    return [SocialAccountResponse.model_validate(a) for a in accounts]


@router.get("/connect/{platform}")
async def get_oauth_url(
    platform: str,
    db: DBDep,
    current_user: CurrentUser,
) -> dict:
    """Return the OAuth authorization URL for the given platform."""
    service = SocialService(db)
    try:
        oauth_url = await service.get_oauth_url(
            platform=platform, user_id=current_user.id
        )
    except AppException as exc:
        _raise_for_app_exception(exc)
    return {"authorization_url": oauth_url, "platform": platform}


@router.get("/callback/{platform}", response_model=SocialAccountResponse)
async def oauth_callback(
    platform: str,
    request: Request,
    db: DBDep,
    current_user: CurrentUser,
    code: str = Query(...),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> SocialAccountResponse:
    """Handle OAuth redirect callback from the given platform."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error from {platform}: {error_description or error}",
        )
    service = SocialService(db)
    try:
        account = await service.handle_callback(
            platform=platform,
            code=code,
            state=state,
            user_id=current_user.id,
        )
    except AppException as exc:
        _raise_for_app_exception(exc)
    return SocialAccountResponse.model_validate(account)


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_account(
    account_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUser,
) -> None:
    """Disconnect and remove a social account."""
    service = SocialService(db)
    try:
        await service.delete_account(account_id=account_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
