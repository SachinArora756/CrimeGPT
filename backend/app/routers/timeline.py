from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access
from app.services.timeline_service import get_timeline
from app.schemas.timeline import TimelineEventResponse

router = APIRouter()


@router.get("/{case_id}", response_model=list[TimelineEventResponse])
async def get_case_timeline(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    events = await get_timeline(db, case.id)
    return [TimelineEventResponse.model_validate(e) for e in events]
