"""Background investigation task runner.

Allows investigations to continue even if the SSE client disconnects.
Results are stored in memory and persisted to the database on completion.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from app.database import async_session

logger = logging.getLogger(__name__)


class InvestigationTask:
    __slots__ = ("task_id", "session_id", "status", "events", "error", "started_at", "completed_at", "_task")

    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self.status: str = "pending"
        self.events: list[dict] = []
        self.error: str | None = None
        self.started_at: datetime = datetime.utcnow()
        self.completed_at: datetime | None = None
        self._task: asyncio.Task | None = None


_active_tasks: dict[str, InvestigationTask] = {}


def get_task(task_id: str) -> InvestigationTask | None:
    return _active_tasks.get(task_id)


def get_task_by_session(session_id: str) -> InvestigationTask | None:
    for t in _active_tasks.values():
        if t.session_id == session_id and t.status in ("pending", "running"):
            return t
    return None


def get_task_events_since(task_id: str, after_index: int = 0) -> list[dict]:
    task = _active_tasks.get(task_id)
    if not task:
        return []
    return task.events[after_index:]


async def start_investigation_task(
    session_id: str,
    file_path: str,
    original_filename: str,
    user_message: str | None,
    user_id: int,
    case_id: int | None,
    db_session_id: int,
) -> str:
    """Launch investigation as a background asyncio task. Returns task_id for polling."""
    existing = get_task_by_session(session_id)
    if existing:
        return existing.task_id

    task_id = f"inv_{uuid.uuid4().hex[:12]}"
    inv_task = InvestigationTask(task_id=task_id, session_id=session_id)
    _active_tasks[task_id] = inv_task

    async def _run():
        inv_task.status = "running"
        try:
            from app.services.ai_investigation_service import run_investigation

            async with async_session() as db:
                async for event in run_investigation(
                    file_path=file_path,
                    original_filename=original_filename,
                    user_message=user_message,
                    user_id=user_id,
                    case_id=case_id,
                    db=db,
                ):
                    inv_task.events.append(event)

                # Persist final results
                final_event = inv_task.events[-1] if inv_task.events else None
                if final_event and final_event.get("event") == "complete":
                    from app.models.ai_investigation import AIInvestigationSession, AIInvestigationMessage
                    from sqlalchemy import select

                    stmt = select(AIInvestigationSession).where(
                        AIInvestigationSession.id == db_session_id
                    )
                    result = await db.execute(stmt)
                    session = result.scalar_one_or_none()

                    if session:
                        complete_data = final_event["data"]
                        msg = AIInvestigationMessage(
                            message_id=str(uuid.uuid4()),
                            session_id=session.id,
                            role="assistant",
                            content=complete_data.get("report", ""),
                            tool_executions=complete_data.get("tool_results"),
                            metadata_={
                                "classification": complete_data.get("classification"),
                                "criminal_matches": complete_data.get("criminal_matches"),
                                "background_task_id": task_id,
                            },
                        )
                        db.add(msg)
                        session.updated_at = datetime.utcnow()
                        await db.commit()

            inv_task.status = "completed"
            inv_task.completed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Background investigation failed: {e}", exc_info=True)
            inv_task.status = "failed"
            inv_task.error = str(e)[:500]
            inv_task.completed_at = datetime.utcnow()

    inv_task._task = asyncio.create_task(_run())
    return task_id


def cleanup_old_tasks(max_age_seconds: int = 3600):
    """Remove completed tasks older than max_age_seconds."""
    now = datetime.utcnow()
    to_remove = []
    for tid, task in _active_tasks.items():
        if task.completed_at and (now - task.completed_at).total_seconds() > max_age_seconds:
            to_remove.append(tid)
    for tid in to_remove:
        del _active_tasks[tid]
