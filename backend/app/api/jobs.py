from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import AppException, NotFoundError, PermissionError
from app.schemas.hook import HookApproveRequest, HookListResponse, HookResponse
from app.schemas.job import (
    DestinationSelectRequest,
    HookGenerateRequest,
    JobCreate,
    JobListResponse,
    JobResponse,
    PublishNowRequest,
    ScheduleRequest,
    VideoUploadResponse,
)
from app.services.hook_service import HookService
from app.services.job_service import JobService
from app.workers.hook_tasks import generate_hooks_task
from app.workers.publish_tasks import publish_job_task
from app.workers.video_tasks import process_video_hook

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _raise_for_app_exception(exc: AppException) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: DBDep, current_user: CurrentUser) -> JobResponse:
    """Create a new content job in DRAFT state."""
    service = JobService(db)
    try:
        job = await service.create_job(user_id=current_user.id, title=payload.title)
    except AppException as exc:
        _raise_for_app_exception(exc)
    return JobResponse.model_validate(job)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JobListResponse:
    """List all content jobs for the current user."""
    service = JobService(db)
    jobs, total = await service.list_jobs(
        user_id=current_user.id, page=page, page_size=page_size
    )
    return JobListResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: DBDep, current_user: CurrentUser) -> JobResponse:
    """Get a specific job by ID."""
    service = JobService(db)
    try:
        job = await service.get_job(job_id=job_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/upload-video", response_model=VideoUploadResponse)
async def get_upload_url(
    job_id: uuid.UUID, db: DBDep, current_user: CurrentUser
) -> VideoUploadResponse:
    """Generate a presigned S3 upload URL for the job's video."""
    service = JobService(db)
    try:
        result = await service.get_presigned_upload_url(job_id=job_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)
    return result


@router.post("/{job_id}/confirm-upload", response_model=JobResponse)
async def confirm_upload(
    job_id: uuid.UUID, db: DBDep, current_user: CurrentUser
) -> JobResponse:
    """Confirm that the video has been uploaded to S3."""
    service = JobService(db)
    try:
        job = await service.confirm_video_upload(job_id=job_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/generate-hooks", response_model=JobResponse)
async def generate_hooks(
    job_id: uuid.UUID,
    payload: HookGenerateRequest,
    db: DBDep,
    current_user: CurrentUser,
) -> JobResponse:
    """Trigger async hook generation via Celery."""
    service = JobService(db)
    try:
        job = await service.transition_to_hook_generating(
            job_id=job_id, user_id=current_user.id
        )
    except AppException as exc:
        _raise_for_app_exception(exc)

    # Fire-and-forget Celery task
    generate_hooks_task.delay(str(job_id), payload.prompt)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/approve-hook", response_model=JobResponse)
async def approve_hook(
    job_id: uuid.UUID,
    payload: HookApproveRequest,
    db: DBDep,
    current_user: CurrentUser,
) -> JobResponse:
    """Approve a hook and optionally supply custom text, then trigger video editing."""
    hook_service = HookService(db)
    job_service = JobService(db)
    try:
        job = await hook_service.approve_hook(
            job_id=job_id,
            hook_id=payload.hook_id,
            user_id=current_user.id,
            manual_text=payload.manual_text,
        )
    except AppException as exc:
        _raise_for_app_exception(exc)

    # Trigger video-editing Celery task
    process_video_hook.delay(str(job_id))
    return JobResponse.model_validate(job)


@router.post("/{job_id}/select-destinations", response_model=JobResponse)
async def select_destinations(
    job_id: uuid.UUID,
    payload: DestinationSelectRequest,
    db: DBDep,
    current_user: CurrentUser,
) -> JobResponse:
    """Select which social accounts to publish to."""
    service = JobService(db)
    try:
        job = await service.select_destinations(
            job_id=job_id,
            user_id=current_user.id,
            social_account_ids=payload.social_account_ids,
        )
    except AppException as exc:
        _raise_for_app_exception(exc)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/publish-now", response_model=JobResponse)
async def publish_now(
    job_id: uuid.UUID,
    payload: PublishNowRequest,
    db: DBDep,
    current_user: CurrentUser,
) -> JobResponse:
    """Trigger immediate publishing to all selected destinations."""
    service = JobService(db)
    try:
        job = await service.publish_now(
            job_id=job_id,
            user_id=current_user.id,
            caption=payload.caption,
            hashtags=payload.hashtags,
        )
    except AppException as exc:
        _raise_for_app_exception(exc)

    publish_job_task.delay(str(job_id))
    return JobResponse.model_validate(job)


@router.post("/{job_id}/schedule", response_model=JobResponse)
async def schedule_job(
    job_id: uuid.UUID,
    payload: ScheduleRequest,
    db: DBDep,
    current_user: CurrentUser,
) -> JobResponse:
    """Schedule the job for publishing at a future time."""
    service = JobService(db)
    try:
        job = await service.schedule_job(
            job_id=job_id,
            user_id=current_user.id,
            scheduled_at=payload.scheduled_at,
            user_timezone=payload.user_timezone,
            caption=payload.caption,
            hashtags=payload.hashtags,
        )
    except AppException as exc:
        _raise_for_app_exception(exc)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/resume", response_model=JobResponse)
async def resume_job(
    job_id: uuid.UUID, db: DBDep, current_user: CurrentUser
) -> JobResponse:
    """Return the current job state so the wizard can resume from the correct step."""
    service = JobService(db)
    try:
        job = await service.resume_job(job_id=job_id, user_id=current_user.id)
    except AppException as exc:
        _raise_for_app_exception(exc)
    return JobResponse.model_validate(job)
