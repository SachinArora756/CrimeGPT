from datetime import datetime
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str | None = None
    case_id: int | None = None


class SendMessageRequest(BaseModel):
    message: str = ""
    case_id: int | None = None


class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    attachments: list[dict] | None = None
    tool_executions: list[dict] | None = None
    metadata: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    session_id: str
    title: str
    case_id: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    session_id: str
    title: str
    case_id: int | None = None
    status: str
    messages: list[MessageResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    file_path: str
    original_filename: str
    file_type: str
    classification: dict
    message_id: str
