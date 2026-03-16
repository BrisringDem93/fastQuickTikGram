from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException, NotFoundError, PermissionError
from app.core.state_machine import ContentJobStateMachine, JobState
from app.models.content_job import ContentJob, JobStatus
from app.models.publish_target import PublishTarget, PublishTargetStatus
from app.models.social_account import SocialAccount
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    async def create_job(self, *, user_id: uuid.UUID, title: str) -> ContentJob:
        """Create a new ContentJob in DRAFT state."""
        job = ContentJob(user_id=user_id, title=title, status=JobStatus.DRAFT)
        self._db.add(job)
        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def get_job(
        self,
        *,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ContentJob:
        """Fetch a job and verify ownership."""
        result = await self._db.execute(
            select(ContentJob)
            .options(
                selectinload(ContentJob.hooks),
                selectinload(ContentJob.assets),
                selectinload(ContentJob.publish_targets).selectinload(
                    PublishTarget.attempts
                ),
            )
            .where(ContentJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundError("ContentJob", job_id)
        if job.user_id != user_id:
            raise PermissionError("access", "ContentJob")
        return job

    async def list_jobs(
        self,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ContentJob], int]:
        """Return a page of jobs for *user_id* and the total count."""
        count_result = await self._db.scalar(
            select(func.count(ContentJob.id)).where(ContentJob.user_id == user_id)
        )
        total = count_result or 0

        result = await self._db.execute(
            select(ContentJob)
            .where(ContentJob.user_id == user_id)
            .order_by(ContentJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        jobs = list(result.scalars().all())
        return jobs, total

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    async def _transition(
        self, job: ContentJob, target: JobState
    ) -> ContentJob:
        """Apply state-machine transition and persist."""
        sm = ContentJobStateMachine(job.status.value)
        sm.transition(target)
        job.status = JobStatus(sm.state.value)
        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def save_uploaded_video(
        self, *, job_id: uuid.UUID, user_id: uuid.UUID, file: UploadFile
    ) -> ContentJob:
        """Save an uploaded video file locally and transition DRAFT → VIDEO_UPLOADED."""
        job = await self.get_job(job_id=job_id, user_id=user_id)
        storage = StorageService()
        storage_key = f"videos/{user_id}/{job_id}/original.mp4"
        storage.store_fileobj(file.file, storage_key)
        job.original_video_key = storage_key
        await self._db.flush()
        return await self._transition(job, JobState.VIDEO_UPLOADED)

    async def confirm_video_upload(
        self, *, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> ContentJob:
        """Return the job after confirming the video has been uploaded.

        This endpoint is kept for backward compatibility.  The upload-video
        endpoint now stores the file *and* advances the state in a single
        request, so calling this afterwards is a no-op if the job is already
        in VIDEO_UPLOADED (or a later) state.
        """
        job = await self.get_job(job_id=job_id, user_id=user_id)
        if not job.original_video_key:
            raise AppException("No video upload key found; call upload-video first")
        sm = ContentJobStateMachine(job.status.value)
        if sm.can_transition_to(JobState.VIDEO_UPLOADED):
            return await self._transition(job, JobState.VIDEO_UPLOADED)
        # Already at VIDEO_UPLOADED or beyond — return as-is
        return job

    async def transition_to_hook_generating(
        self, *, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> ContentJob:
        """Transition VIDEO_UPLOADED (or HOOK_REJECTED) → HOOK_GENERATING."""
        job = await self.get_job(job_id=job_id, user_id=user_id)
        return await self._transition(job, JobState.HOOK_GENERATING)

    async def select_destinations(
        self,
        *,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        social_account_ids: list[uuid.UUID],
    ) -> ContentJob:
        """Attach social accounts as publish targets and advance state."""
        job = await self.get_job(job_id=job_id, user_id=user_id)

        # Validate that all accounts belong to the user
        result = await self._db.execute(
            select(SocialAccount).where(
                SocialAccount.id.in_(social_account_ids),
                SocialAccount.user_id == user_id,
                SocialAccount.is_active.is_(True),
            )
        )
        accounts = list(result.scalars().all())
        found_ids = {a.id for a in accounts}
        missing = set(social_account_ids) - found_ids
        if missing:
            raise AppException(
                f"Social accounts not found or not owned by you: {missing}"
            )

        # Remove existing pending targets and recreate
        for target in list(job.publish_targets):
            if target.status == PublishTargetStatus.pending:
                await self._db.delete(target)

        for account in accounts:
            target = PublishTarget(
                job_id=job.id,
                social_account_id=account.id,
                platform=account.platform.value,
                status=PublishTargetStatus.pending,
            )
            self._db.add(target)

        await self._db.flush()

        # State transition: VIDEO_READY or WAITING_FOR_SOCIAL_CONNECTION → DESTINATIONS_SELECTED → READY_TO_PUBLISH
        sm = ContentJobStateMachine(job.status.value)
        if sm.can_transition_to(JobState.DESTINATIONS_SELECTED):
            sm.transition(JobState.DESTINATIONS_SELECTED)
        sm.transition(JobState.READY_TO_PUBLISH)
        job.status = JobStatus(sm.state.value)
        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def publish_now(
        self,
        *,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        caption: str | None = None,
        hashtags: list[str] | None = None,
    ) -> ContentJob:
        """Transition to PUBLISHING and store caption metadata."""
        job = await self.get_job(job_id=job_id, user_id=user_id)
        meta: dict[str, Any] = dict(job.job_metadata or {})
        if caption:
            meta["caption"] = caption
        if hashtags:
            meta["hashtags"] = hashtags
        job.job_metadata = meta
        return await self._transition(job, JobState.PUBLISHING)

    async def schedule_job(
        self,
        *,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        scheduled_at: datetime,
        user_timezone: str = "UTC",
        caption: str | None = None,
        hashtags: list[str] | None = None,
    ) -> ContentJob:
        """Schedule the job for future publishing."""
        job = await self.get_job(job_id=job_id, user_id=user_id)
        if scheduled_at <= datetime.now(tz=timezone.utc):
            raise AppException("Scheduled time must be in the future")

        meta: dict[str, Any] = dict(job.job_metadata or {})
        if caption:
            meta["caption"] = caption
        if hashtags:
            meta["hashtags"] = hashtags
        job.job_metadata = meta
        job.scheduled_at_utc = scheduled_at
        job.user_timezone = user_timezone

        # Update publish_target schedules
        for target in job.publish_targets:
            if target.status in (PublishTargetStatus.pending, PublishTargetStatus.scheduled):
                target.status = PublishTargetStatus.scheduled
                target.scheduled_at_utc = scheduled_at

        return await self._transition(job, JobState.SCHEDULED)

    async def resume_job(
        self, *, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> ContentJob:
        """Return job state to allow the wizard to resume from the correct step."""
        return await self.get_job(job_id=job_id, user_id=user_id)

    async def mark_published(
        self,
        *,
        job_id: uuid.UUID,
        all_published: bool = True,
    ) -> ContentJob:
        """Called by publish workers to finalize job status."""
        result = await self._db.execute(
            select(ContentJob).where(ContentJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundError("ContentJob", job_id)

        target_state = JobState.PUBLISHED if all_published else JobState.PARTIALLY_PUBLISHED
        sm = ContentJobStateMachine(job.status.value)
        if sm.can_transition_to(target_state):
            sm.transition(target_state)
            job.status = JobStatus(sm.state.value)
            if all_published:
                job.completed_at = datetime.now(tz=timezone.utc)
        await self._db.flush()
        await self._db.refresh(job)
        return job
