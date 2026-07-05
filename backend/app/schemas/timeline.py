from pydantic import BaseModel
from datetime import datetime
from app.models.timeline import TimelineEventType


class TimelineEventResponse(BaseModel):
    id: int
    case_id: int
    event_type: TimelineEventType
    title: str
    description: str | None
    actor_id: int | None
    extra_data: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
