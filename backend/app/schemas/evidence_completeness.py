"""Schemas for Evidence Completeness Engine and IEAE features."""

from pydantic import BaseModel, ConfigDict


class ChecklistItem(BaseModel):
    category: str
    state: str  # "completed", "not_found", "needs_manual_review", "not_applicable"
    findings_count: int = 0
    confidence: float = 0.0
    details: str = ""


class EvidenceChecklist(BaseModel):
    items: list[ChecklistItem]
    total_categories: int
    completed_count: int
    not_found_count: int
    needs_review_count: int


class AnalysisPass(BaseModel):
    pass_number: int
    pass_name: str
    tool_key: str
    status: str
    confidence: float | None = None
    findings_summary: str = ""
    execution_time_ms: int = 0


class CompletenessScores(BaseModel):
    evidence_collection_score: float
    evidence_analysis_score: float
    evidence_verification_score: float
    overall_completeness: float


class CompletenessReport(BaseModel):
    scores: CompletenessScores
    checklist: EvidenceChecklist
    missing_analyses: list[str]
    recommendations: list[str]


class CorrelationItem(BaseModel):
    source_evidence_id: int
    target_evidence_id: int
    correlation_type: str
    confidence: float
    source_filename: str = ""
    target_filename: str = ""
    details: dict = {}


class CorrelationReport(BaseModel):
    correlations: list[CorrelationItem]
    clusters: dict = {}
    total_links: int = 0


class CaseClosureItem(BaseModel):
    key: str
    label: str
    status: str  # "completed", "missing", "partial", "not_applicable"
    details: str = ""


class CaseClosureReport(BaseModel):
    ready: bool
    checklist: list[CaseClosureItem]
    warnings: list[str]
    completion_percentage: float


class IEAEAdminStats(BaseModel):
    average_completeness: float
    total_investigations: int
    skipped_analyses: list[dict]
    manual_reviews_pending: int
    evidence_quality_avg: float
    common_missing_analyses: list[dict]
    tool_utilization: dict
