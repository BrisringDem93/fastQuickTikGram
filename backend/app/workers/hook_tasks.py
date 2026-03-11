from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import select

from app.core.state_machine import ContentJobStateMachine, JobState
from app.database import AsyncSessionLocal
from app.models.content_job import ContentJob, JobStatus
from app.services.hook_service import HookService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _generate_hooks_async(job_id: str, custom_prompt: str | None) -> None:
    async with AsyncSessionLocal() as db:
        service = HookService(db)
        try:
            hooks = await service.generate_hooks(
                job_id=uuid.UUID(job_id),
                custom_prompt=custom_prompt,
            )
            await db.commit()
            logger.info(
                "Generated %d hooks for job %s", len(hooks), job_id
            )
        except Exception as exc:
            logger.exception("Hook generation failed for job %s", job_id)
            # Mark job as FAILED
            result = await db.execute(
                select(ContentJob).where(ContentJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()
            if job:
                sm = ContentJobStateMachine(job.status.value)
                if sm.can_transition_to(JobState.FAILED):
                    sm.transition(JobState.FAILED)
                    job.status = JobStatus(sm.state.value)
                await db.commit()
            raise


@celery_app.task(
    name="app.workers.hook_tasks.generate_hooks_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def generate_hooks_task(self, job_id: str, custom_prompt: str | None = None) -> None:
    """Celery task: generate hooks using OpenAI and save them to the DB."""
    try:
        asyncio.run(_generate_hooks_async(job_id, custom_prompt))
    except Exception as exc:
        logger.exception("generate_hooks_task failed for job %s", job_id)
        raise self.retry(exc=exc)
