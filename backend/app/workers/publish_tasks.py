from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Coroutine
from typing import Any
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.state_machine import ContentJobStateMachine, JobState
from app.database import AsyncSessionLocal
from app.models.content_job import ContentJob, JobStatus
from app.models.publish_attempt import PublishAttempt
from app.models.publish_target import PublishTarget, PublishTargetStatus
from app.models.social_account import SocialAccount
from app.publishers.base import PublisherFactory
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_worker_event_loop: asyncio.AbstractEventLoop | None = None


def _run_in_worker_loop(coro: Coroutine[Any, Any, Any]) -> None:
    """Run async code on a persistent loop for the Celery worker process.

    Celery tasks run in sync context. Using ``asyncio.run`` per task creates
    and closes a fresh event loop every execution, while SQLAlchemy asyncpg
    connections in the pool may still be tied to an earlier loop.
    Reusing one loop per worker process avoids cross-loop errors.
    """
    global _worker_event_loop

    if _worker_event_loop is None or _worker_event_loop.is_closed():
        _worker_event_loop = asyncio.new_event_loop()

    asyncio.set_event_loop(_worker_event_loop)
    _worker_event_loop.run_until_complete(coro)


async def _publish_job_async(job_id: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentJob)
            .options(
                selectinload(ContentJob.publish_targets).selectinload(PublishTarget.social_account),
                selectinload(ContentJob.publish_targets).selectinload(PublishTarget.attempts),
            )
            .where(ContentJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("Job %s not found", job_id)
            return

        if not job.edited_video_key:
            logger.error("Job %s has no edited video key", job_id)
            return

        caption: str = (job.job_metadata or {}).get("caption", job.title)
        hashtags: list[str] = (job.job_metadata or {}).get("hashtags", [])

        success_count = 0
        fail_count = 0

        for target in job.publish_targets:
            if target.status == PublishTargetStatus.published:
                success_count += 1
                continue
            if target.status not in (
                PublishTargetStatus.pending,
                PublishTargetStatus.failed,
                PublishTargetStatus.publishing,
            ):
                continue

            attempt_number = len(target.attempts) + 1
            target.status = PublishTargetStatus.publishing
            await db.flush()

            attempt = PublishAttempt(
                publish_target_id=target.id,
                attempt_number=attempt_number,
                status="in_progress",
            )
            db.add(attempt)
            await db.flush()

            try:
                account: SocialAccount = target.social_account
                publisher = PublisherFactory.get_publisher(target.platform, account=account)

                await publisher.validate_account()
                response = await publisher.create_post(
                    video_key=job.edited_video_key,
                    caption=caption,
                    hashtags=hashtags,
                )

                target.status = PublishTargetStatus.published
                target.published_at = datetime.now(tz=timezone.utc)
                target.external_post_id = response.get("post_id")
                target.external_post_url = response.get("post_url")

                attempt.status = "success"
                attempt.response_data = response
                success_count += 1

            except Exception as exc:
                logger.exception(
                    "Publishing failed for target %s platform=%s", target.id, target.platform
                )
                target.status = PublishTargetStatus.failed
                target.error_message = str(exc)
                attempt.status = "failed"
                attempt.error_message = str(exc)
                fail_count += 1

            await db.flush()

        # Update overall job status
        sm = ContentJobStateMachine(job.status.value)
        if fail_count == 0:
            if sm.can_transition_to(JobState.PUBLISHED):
                sm.transition(JobState.PUBLISHED)
                job.status = JobStatus(sm.state.value)
                job.completed_at = datetime.now(tz=timezone.utc)
        elif success_count > 0:
            if sm.can_transition_to(JobState.PARTIALLY_PUBLISHED):
                sm.transition(JobState.PARTIALLY_PUBLISHED)
                job.status = JobStatus(sm.state.value)
        else:
            if sm.can_transition_to(JobState.FAILED):
                sm.transition(JobState.FAILED)
                job.status = JobStatus(sm.state.value)

        await db.commit()
        logger.info(
            "Publishing complete for job %s: success=%d failed=%d",
            job_id, success_count, fail_count,
        )


async def _scheduler_beat_async() -> None:
    """Find SCHEDULED jobs whose time has come and trigger publishing."""
    now = datetime.now(tz=timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentJob).where(
                ContentJob.status == JobStatus.SCHEDULED,
                ContentJob.scheduled_at_utc <= now,
            )
        )
        jobs = result.scalars().all()
        for job in jobs:
            sm = ContentJobStateMachine(job.status.value)
            if sm.can_transition_to(JobState.PUBLISHING):
                sm.transition(JobState.PUBLISHING)
                job.status = JobStatus(sm.state.value)

        await db.commit()

    for job in jobs:
        logger.info("Scheduler triggering publish for job %s", job.id)
        publish_job_task.delay(str(job.id))


@celery_app.task(
    name="app.workers.publish_tasks.publish_job_task",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def publish_job_task(self, job_id: str) -> None:
    """Celery task: publish a job to all selected destinations."""
    try:
        _run_in_worker_loop(_publish_job_async(job_id))
    except Exception as exc:
        logger.exception("publish_job_task failed for job %s", job_id)
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.publish_tasks.scheduler_beat_task")
def scheduler_beat_task() -> None:
    """Celery Beat task: trigger publishing for any jobs whose scheduled time has passed."""
    _run_in_worker_loop(_scheduler_beat_async())
