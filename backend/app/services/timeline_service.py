from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timeline import TimelineEvent, TimelineEventType


async def add_event(
    db: AsyncSession,
    case_id: int,
    event_type: TimelineEventType,
    title: str,
    description: str | None = None,
    actor_id: int | None = None,
    extra_data: dict | None = None,
) -> TimelineEvent:
    event = TimelineEvent(
        case_id=case_id,
        event_type=event_type,
        title=title,
        description=description,
        actor_id=actor_id,
        extra_data=extra_data,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_timeline(db: AsyncSession, case_id: int) -> list[TimelineEvent]:
    result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.created_at.desc())
    )
    return list(result.scalars().all())
