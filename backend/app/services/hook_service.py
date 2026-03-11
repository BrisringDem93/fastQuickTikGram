from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppException, NotFoundError, PermissionError
from app.core.state_machine import ContentJobStateMachine, JobState
from app.models.content_job import ContentJob, JobStatus
from app.models.job_hook import JobHook

logger = logging.getLogger(__name__)

_HOOK_SYSTEM_PROMPT = """You are an expert social media video hook writer for content creators.
A "hook" is the first 3-10 seconds of a video that grabs the viewer's attention.
Generate compelling, platform-agnostic hooks that:
- Create immediate curiosity or emotional engagement
- Are concise (under 15 words ideally)
- Use pattern interrupts, surprising facts, bold claims, or relatable scenarios
- Avoid clickbait that under-delivers

Respond ONLY with valid JSON: a list of objects with keys:
  "text" (string), "rationale" (string), "score" (float 0.0-1.0)
"""


class HookService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_hooks(
        self,
        *,
        job_id: uuid.UUID,
        custom_prompt: str | None = None,
    ) -> list[JobHook]:
        """Call OpenAI to generate 3+ hooks for the job; saves them to DB."""
        result = await self._db.execute(
            select(ContentJob).where(ContentJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundError("ContentJob", job_id)

        user_message = (
            f"Job title: {job.title!r}.\n"
            + (f"Additional context: {custom_prompt}\n" if custom_prompt else "")
            + "Generate exactly 4 high-quality hooks for this video."
        )

        try:
            response = await self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _HOOK_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.8,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "[]"
            parsed: Any = json.loads(raw)
            # Support both {"hooks": [...]} and [...]
            if isinstance(parsed, dict):
                parsed = parsed.get("hooks") or list(parsed.values())[0]
        except Exception as exc:
            logger.exception("OpenAI hook generation failed for job %s", job_id)
            raise AppException(f"Hook generation failed: {exc}") from exc

        hooks: list[JobHook] = []
        for item in parsed:
            hook = JobHook(
                job_id=job.id,
                text=str(item.get("text", "")),
                rationale=str(item.get("rationale", "")),
                score=float(item.get("score", 0.5)),
                is_selected=False,
                is_manually_edited=False,
            )
            self._db.add(hook)
            hooks.append(hook)

        # Advance state to HOOK_PENDING_APPROVAL
        sm = ContentJobStateMachine(job.status.value)
        if sm.can_transition_to(JobState.HOOK_PENDING_APPROVAL):
            sm.transition(JobState.HOOK_PENDING_APPROVAL)
            job.status = JobStatus(sm.state.value)

        await self._db.flush()
        for hook in hooks:
            await self._db.refresh(hook)
        return hooks

    async def approve_hook(
        self,
        *,
        job_id: uuid.UUID,
        hook_id: uuid.UUID,
        user_id: uuid.UUID,
        manual_text: str | None = None,
    ) -> ContentJob:
        """Mark a hook as approved (optionally with manual text) and advance state."""
        job_result = await self._db.execute(
            select(ContentJob).where(ContentJob.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if job is None:
            raise NotFoundError("ContentJob", job_id)
        if job.user_id != user_id:
            raise PermissionError("approve hook on", "ContentJob")

        hook_result = await self._db.execute(
            select(JobHook).where(JobHook.id == hook_id, JobHook.job_id == job_id)
        )
        hook = hook_result.scalar_one_or_none()
        if hook is None:
            raise NotFoundError("JobHook", hook_id)

        # Deselect all other hooks
        all_hooks_result = await self._db.execute(
            select(JobHook).where(JobHook.job_id == job_id)
        )
        for h in all_hooks_result.scalars().all():
            h.is_selected = False

        hook.is_selected = True
        if manual_text:
            hook.text = manual_text
            hook.is_manually_edited = True

        job.approved_hook_id = hook.id

        sm = ContentJobStateMachine(job.status.value)
        sm.transition(JobState.HOOK_APPROVED)
        job.status = JobStatus(sm.state.value)

        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def list_hooks_for_job(
        self,
        *,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[JobHook]:
        """Return all hooks for a job, verifying ownership."""
        job_result = await self._db.execute(
            select(ContentJob).where(ContentJob.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if job is None:
            raise NotFoundError("ContentJob", job_id)
        if job.user_id != user_id:
            raise PermissionError("list hooks for", "ContentJob")

        result = await self._db.execute(
            select(JobHook)
            .where(JobHook.job_id == job_id)
            .order_by(JobHook.score.desc())
        )
        return list(result.scalars().all())
