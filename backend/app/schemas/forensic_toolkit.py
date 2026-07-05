from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any


class ToolDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tool_key: str
    display_name: str
    category: str
    description: str | None = None
    icon: str | None = None
    accepted_file_types: list[str] | None = None
    is_active: bool = True
    max_file_size_mb: int = 50


class ToolCategoryResponse(BaseModel):
    category: str
    icon: str | None = None
    tools: list[ToolDefinitionResponse]


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    execution_id: str
    tool_key: str
    status: str
    input_filename: str | None = None
    output_data: dict[str, Any] | None = None
    ai_summary: str | None = None
    confidence_score: float | None = None
    execution_time_ms: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    case_id: int | None = None
    evidence_id: int | None = None
    user_id: int | None = None


class ExecutionListResponse(BaseModel):
    items: list[ExecutionResponse]
    total: int
    page: int
    per_page: int


class DashboardStatsResponse(BaseModel):
    total_executions: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    pending: int = 0
    success_rate: float = 0.0
    avg_execution_time_ms: float = 0.0
    by_tool: dict[str, int] = {}
    by_status: dict[str, int] = {}


class SavedResultCreate(BaseModel):
    execution_id: str
    title: str
    notes: str | None = None


class SavedResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: int
    title: str
    notes: str | None = None
    is_bookmarked: bool = True
    linked_case_id: int | None = None
    created_at: datetime | None = None


class LinkCaseRequest(BaseModel):
    case_id: int


class PromoteEvidenceRequest(BaseModel):
    description: str | None = None
    tags: list[str] | None = None


class AdminOfficerStats(BaseModel):
    user_id: int
    full_name: str
    username: str
    total_executions: int
    completed: int
    failed: int
    success_rate: float


class AdminToolStats(BaseModel):
    tool_key: str
    total_executions: int
    completed: int
    failed: int
    avg_time_ms: float


class AdminRecentActivity(BaseModel):
    execution_id: str
    tool_key: str
    status: str
    user_full_name: str
    created_at: datetime | None = None


class AdminStatsResponse(BaseModel):
    total_executions: int
    by_officer: list[AdminOfficerStats]
    by_tool: list[AdminToolStats]
    success_rate: float
    recent_activity: list[AdminRecentActivity]
