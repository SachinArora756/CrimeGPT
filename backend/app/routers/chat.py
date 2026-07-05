from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access
from app.services.chat_service import process_chat, get_chat_history
from app.schemas.chat import ChatMessageResponse
from app.utils.rate_limiter import limiter

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


@router.post("/{case_id}", response_model=ChatMessageResponse)
@limiter.limit("10/minute")
async def send_chat(
    request: Request,
    *,
    case_id: str = Path(),
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    from app.middleware.security import sanitize_input
    sanitized = sanitize_input(chat_request.message)
    try:
        response = await process_chat(db, case.id, current_user.id, sanitized)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service temporarily unavailable")
    return ChatMessageResponse.model_validate(response)


@router.get("/{case_id}/history", response_model=list[ChatMessageResponse])
async def chat_history(
    case_id: str = Path(),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    messages = await get_chat_history(db, case.id, limit=limit, offset=offset)
    return [ChatMessageResponse.model_validate(m) for m in messages]
