from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import AppException, NotFoundError, PermissionError
from app.schemas.publishing import PublishStatusResponse, PublishTargetResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/publishing", tags=["publishing"])


def _raise_for_app_exception(exc: AppException) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


@router.get("/{job_id}/status", response_model=PublishStatusResponse)
async def get_publish_status(
    job_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUser,
) -> PublishStatusResponse:
    """Get aggregated publish status across all platforms for a job."""
    service = JobService(db)
    try:
        job = await service.get_job(job_id=job_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)

    targets = job.publish_targets
    published = sum(1 for t in targets if t.status.value == "published")
    failed = sum(1 for t in targets if t.status.value == "failed")
    pending = sum(1 for t in targets if t.status.value in ("pending", "publishing", "scheduled"))

    return PublishStatusResponse(
        job_id=job.id,
        overall_status=job.status.value,
        targets=[PublishTargetResponse.model_validate(t) for t in targets],
        published_count=published,
        failed_count=failed,
        pending_count=pending,
    )


@router.get("/{job_id}/targets", response_model=list[PublishTargetResponse])
async def list_publish_targets(
    job_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUser,
) -> list[PublishTargetResponse]:
    """List all publish targets (per-platform status) for a job."""
    service = JobService(db)
    try:
        job = await service.get_job(job_id=job_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)

    return [PublishTargetResponse.model_validate(t) for t in job.publish_targets]
