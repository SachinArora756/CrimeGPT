from pydantic import BaseModel
from datetime import datetime
from app.models.chat import ChatRole


class ChatMessageResponse(BaseModel):
    id: int
    case_id: int
    user_id: int
    role: ChatRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
