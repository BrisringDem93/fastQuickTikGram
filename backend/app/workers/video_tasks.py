from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.state_machine import ContentJobStateMachine, JobState
from app.database import AsyncSessionLocal
from app.models.content_job import ContentJob, JobStatus
from app.models.job_hook import JobHook
from app.services.storage_service import StorageService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess:
    """Run an ffmpeg command, raising CalledProcessError on failure."""
    cmd = ["ffmpeg", "-y"] + args
    logger.debug("Running FFmpeg: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        logger.error("FFmpeg stderr: %s", result.stderr)
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )
    return result


async def _process_video_hook_async(job_id: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentJob).where(ContentJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("Job %s not found", job_id)
            return

        # Fetch the approved hook text
        hook_result = await db.execute(
            select(JobHook).where(
                JobHook.job_id == job.id,
                JobHook.is_selected.is_(True),
            )
        )
        hook = hook_result.scalar_one_or_none()
        hook_text = hook.text if hook else ""

        storage = StorageService()

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, "output.mp4")

            try:
                # Transition → VIDEO_EDITING
                sm = ContentJobStateMachine(job.status.value)
                if sm.can_transition_to(JobState.VIDEO_EDITING):
                    sm.transition(JobState.VIDEO_EDITING)
                    job.status = JobStatus(sm.state.value)
                    await db.flush()

                # Download original video from S3
                if not job.original_video_key:
                    raise ValueError("No original_video_key set on job")
                storage.download_file(job.original_video_key, input_path)

                # Build FFmpeg drawtext overlay for hook intro
                safe_hook_text = hook_text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
                drawtext_filter = (
                    f"drawtext=text='{safe_hook_text}':"
                    "fontsize=48:"
                    "fontcolor=white:"
                    "borderw=3:"
                    "bordercolor=black:"
                    "x=(w-text_w)/2:"
                    "y=(h-text_h)/2:"
                    "enable='lte(t,4)'"  # show overlay for first 4 seconds
                )

                _run_ffmpeg([
                    "-i", input_path,
                    "-vf", drawtext_filter,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "22",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-movflags", "+faststart",
                    output_path,
                ])

                # Upload edited video to S3
                edited_key = f"videos/{job.user_id}/{job.id}/edited.mp4"
                storage.upload_file(output_path, edited_key)

                job.edited_video_key = edited_key

                # Transition → VIDEO_READY
                sm2 = ContentJobStateMachine(job.status.value)
                sm2.transition(JobState.VIDEO_READY)
                job.status = JobStatus(sm2.state.value)
                await db.commit()
                logger.info("Video processing complete for job %s", job_id)

            except Exception as exc:
                logger.exception("Video processing failed for job %s", job_id)
                sm_fail = ContentJobStateMachine(job.status.value)
                if sm_fail.can_transition_to(JobState.FAILED):
                    sm_fail.transition(JobState.FAILED)
                    job.status = JobStatus(sm_fail.state.value)
                await db.commit()
                raise


@celery_app.task(
    name="app.workers.video_tasks.process_video_hook",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def process_video_hook(self, job_id: str) -> None:
    """Celery task: add hook text overlay to the video using FFmpeg."""
    try:
        asyncio.run(_process_video_hook_async(job_id))
    except Exception as exc:
        logger.exception("process_video_hook failed for job %s, retrying...", job_id)
        raise self.retry(exc=exc)
