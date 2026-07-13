"""
Digital Forensics Toolkit Router

Provides endpoints for executing forensic analysis tools,
managing execution results, bookmarks, and admin statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from app.database import get_db
from app.services.auth_service import get_current_user, require_min_role, require_admin
from app.models.user import User, UserRole
from app.models.forensic_toolkit import (
    ForensicToolDefinition,
    ForensicToolExecution,
    ForensicSavedResult,
    ExecutionStatus,
)
from app.schemas.forensic_toolkit import (
    ToolDefinitionResponse,
    ToolCategoryResponse,
    ExecutionResponse,
    ExecutionListResponse,
    DashboardStatsResponse,
    SavedResultCreate,
    SavedResultResponse,
    LinkCaseRequest,
    PromoteEvidenceRequest,
    AdminStatsResponse,
    AdminOfficerStats,
    AdminToolStats,
    AdminRecentActivity,
)
from app.services.forensic_tools_service import TOOL_HANDLERS, generate_execution_summary
from app.utils.rate_limiter import limiter
import uuid
import os
import hashlib
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Default tool definitions (used when DB has no definitions seeded)
# ---------------------------------------------------------------------------

DEFAULT_TOOL_DEFINITIONS = [
    {
        "tool_key": "image_ocr",
        "display_name": "Image OCR",
        "category": "Image Analysis",
        "description": "Extract text from images using Optical Character Recognition",
        "icon": "FileText",
        "accepted_file_types": ["image/jpeg", "image/png", "image/tiff", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "image_object_detect",
        "display_name": "Object Detection",
        "category": "Image Analysis",
        "description": "Detect and classify objects in images with bounding boxes and labels",
        "icon": "Search",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "image_exif",
        "display_name": "EXIF Data Extraction",
        "category": "Image Analysis",
        "description": "Extract metadata (GPS, camera info, timestamps) from image EXIF data",
        "icon": "MapPin",
        "accepted_file_types": ["image/jpeg", "image/tiff"],
    },
    {
        "tool_key": "audio_transcribe",
        "display_name": "Audio Transcription",
        "category": "Audio/Video",
        "description": "Transcribe speech from audio files to text with timestamps",
        "icon": "Mic",
        "accepted_file_types": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/flac"],
    },
    {
        "tool_key": "document_ocr",
        "display_name": "Document OCR",
        "category": "Document Analysis",
        "description": "Extract text from scanned documents and PDFs using OCR",
        "icon": "FileText",
        "accepted_file_types": ["application/pdf", "image/jpeg", "image/png", "image/tiff"],
    },
    {
        "tool_key": "document_pdf_parse",
        "display_name": "PDF Text Extraction",
        "category": "Document Analysis",
        "description": "Extract text content from PDF documents (native text, not scanned)",
        "icon": "FileText",
        "accepted_file_types": ["application/pdf"],
    },
    {
        "tool_key": "document_summarize",
        "display_name": "Document Summarization",
        "category": "Document Analysis",
        "description": "Generate AI-powered summary of document contents and key findings",
        "icon": "Brain",
        "accepted_file_types": ["application/pdf", "text/plain", "image/jpeg", "image/png", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"],
    },
    {
        "tool_key": "digital_hash",
        "display_name": "File Hash Computation",
        "category": "Digital Forensics",
        "description": "Compute SHA-256, MD5, and SHA-1 cryptographic hashes for evidence integrity",
        "icon": "Shield",
        "accepted_file_types": ["*/*"],
    },
    {
        "tool_key": "digital_metadata",
        "display_name": "File Metadata",
        "category": "Digital Forensics",
        "description": "Extract file size, type, creation date, and other metadata",
        "icon": "Info",
        "accepted_file_types": ["*/*"],
    },
    {
        "tool_key": "digital_file_identify",
        "display_name": "File Type Identification",
        "category": "Digital Forensics",
        "description": "Identify file type by magic bytes (header signature analysis)",
        "icon": "FileQuestion",
        "accepted_file_types": ["*/*"],
    },
    {
        "tool_key": "face_detect",
        "display_name": "Face Detection",
        "category": "Biometric Analysis",
        "description": "Detect and locate faces in images with bounding coordinates",
        "icon": "User",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "face_recognize",
        "display_name": "Face Recognition Search",
        "category": "Biometric Analysis",
        "description": "Search criminal face database for potential matches",
        "icon": "UserSearch",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp"],
    },
    {
        "tool_key": "fingerprint_match",
        "display_name": "Fingerprint Matching",
        "category": "Biometric Analysis",
        "description": "Match fingerprint against criminal fingerprint database",
        "icon": "Fingerprint",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/tiff"],
    },
    {
        "tool_key": "dna_search",
        "display_name": "DNA Profile Search",
        "category": "Biometric Analysis",
        "description": "Parse DNA lab reports via OCR and search criminal DNA database",
        "icon": "Dna",
        "accepted_file_types": ["text/plain", "text/csv", "application/json", "application/pdf", "image/jpeg", "image/png"],
    },
    {
        "tool_key": "vehicle_detect",
        "display_name": "Vehicle Detection",
        "category": "Vehicle Analysis",
        "description": "Detect and classify vehicles (car, truck, bus, motorcycle) in images",
        "icon": "Car",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "license_plate_ocr",
        "display_name": "License Plate OCR",
        "category": "Vehicle Analysis",
        "description": "Detect license plate region and extract plate number via OCR",
        "icon": "CreditCard",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "weapon_detect",
        "display_name": "Weapon Detection",
        "category": "Threat Analysis",
        "description": "Detect weapons (knives, firearms, etc.) in images automatically",
        "icon": "AlertTriangle",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "image_similarity",
        "display_name": "Image Similarity Search",
        "category": "Image Analysis",
        "description": "Find visually similar images in the evidence database",
        "icon": "Images",
        "accepted_file_types": ["image/jpeg", "image/png", "image/bmp", "image/webp"],
    },
    {
        "tool_key": "crime_scene_analysis",
        "display_name": "Crime Scene AI Analysis",
        "category": "Threat Analysis",
        "description": "AI-powered crime scene analysis identifying evidence, conditions, and recommendations",
        "icon": "ScanSearch",
        "accepted_file_types": ["image/jpeg", "image/png", "image/webp"],
    },
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _get_tool_definitions() -> list[dict]:
    """Return default tool definitions."""
    return DEFAULT_TOOL_DEFINITIONS


_HIDDEN_OUTPUT_KEYS = {"model_used", "model_name", "model", "engine"}


def _build_execution_response(execution: ForensicToolExecution) -> dict:
    """Build response dict from execution model."""
    output = execution.output_data
    if isinstance(output, dict):
        output = {k: v for k, v in output.items() if k not in _HIDDEN_OUTPUT_KEYS}
    return {
        "execution_id": execution.execution_id,
        "tool_key": execution.tool_key,
        "status": execution.status.value if isinstance(execution.status, ExecutionStatus) else execution.status,
        "input_filename": execution.input_filename,
        "output_data": output,
        "ai_summary": execution.ai_summary,
        "confidence_score": execution.confidence_score,
        "execution_time_ms": execution.execution_time_ms,
        "error_message": execution.error_message,
        "created_at": execution.created_at,
        "completed_at": execution.completed_at,
        "case_id": execution.case_id,
        "evidence_id": execution.evidence_id,
        "user_id": execution.user_id,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/tools", response_model=list[ToolCategoryResponse])
async def list_tools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tool definitions grouped by category."""
    result = await db.execute(select(ForensicToolDefinition).where(ForensicToolDefinition.is_active == True))
    db_tools = result.scalars().all()

    if db_tools:
        categories: dict[str, list] = {}
        for tool in db_tools:
            cat = tool.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(ToolDefinitionResponse(
                tool_key=tool.tool_key,
                display_name=tool.display_name,
                category=tool.category,
                description=tool.description,
                icon=tool.icon,
                accepted_file_types=tool.accepted_file_types,
                is_active=tool.is_active,
                max_file_size_mb=tool.max_file_size_mb,
            ))
    else:
        categories: dict[str, list] = {}
        for tool_def in DEFAULT_TOOL_DEFINITIONS:
            cat = tool_def["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(ToolDefinitionResponse(
                tool_key=tool_def["tool_key"],
                display_name=tool_def["display_name"],
                category=tool_def["category"],
                description=tool_def["description"],
                icon=tool_def["icon"],
                accepted_file_types=tool_def["accepted_file_types"],
                is_active=True,
                max_file_size_mb=50,
            ))

    return [
        ToolCategoryResponse(category=cat, tools=tools)
        for cat, tools in categories.items()
    ]


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution statistics for the current user's dashboard."""
    base_filter = ForensicToolExecution.user_id == current_user.id

    total_result = await db.execute(
        select(func.count()).select_from(ForensicToolExecution).where(base_filter)
    )
    total = total_result.scalar() or 0

    status_result = await db.execute(
        select(ForensicToolExecution.status, func.count())
        .where(base_filter)
        .group_by(ForensicToolExecution.status)
    )
    by_status = {}
    completed = 0
    failed = 0
    running = 0
    pending = 0
    for row in status_result.all():
        status_val = row[0].value if isinstance(row[0], ExecutionStatus) else row[0]
        by_status[status_val] = row[1]
        if status_val == "completed":
            completed = row[1]
        elif status_val == "failed":
            failed = row[1]
        elif status_val == "running":
            running = row[1]
        elif status_val == "pending":
            pending = row[1]

    tool_result = await db.execute(
        select(ForensicToolExecution.tool_key, func.count())
        .where(base_filter)
        .group_by(ForensicToolExecution.tool_key)
    )
    by_tool = {row[0]: row[1] for row in tool_result.all()}

    avg_time_result = await db.execute(
        select(func.avg(ForensicToolExecution.execution_time_ms))
        .where(and_(base_filter, ForensicToolExecution.status == ExecutionStatus.COMPLETED))
    )
    avg_time = avg_time_result.scalar() or 0.0

    success_rate = round((completed / total * 100), 1) if total > 0 else 0.0

    return DashboardStatsResponse(
        total_executions=total,
        completed=completed,
        failed=failed,
        running=running,
        pending=pending,
        success_rate=success_rate,
        avg_execution_time_ms=round(float(avg_time), 1),
        by_tool=by_tool,
        by_status=by_status,
    )


@router.get("/dashboard/recent")
async def get_dashboard_recent(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent executions for dashboard."""
    result = await db.execute(
        select(ForensicToolExecution)
        .where(ForensicToolExecution.user_id == current_user.id)
        .order_by(desc(ForensicToolExecution.created_at))
        .limit(limit)
    )
    executions = result.scalars().all()
    return [_build_execution_response(ex) for ex in executions]


@router.post("/execute/{tool_key}")
@limiter.limit("30/minute")
async def execute_tool(
    request: Request,
    tool_key: str,
    file: UploadFile = File(...),
    params: str = Form(default="{}"),
    case_id: int | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Execute a forensic tool on an uploaded file."""
    if tool_key not in TOOL_HANDLERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tool: '{tool_key}'. Available tools: {list(TOOL_HANDLERS.keys())}",
        )

    try:
        tool_params = json.loads(params) if params else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in params field")

    execution_id = str(uuid.uuid4())

    execution = ForensicToolExecution(
        execution_id=execution_id,
        tool_key=tool_key,
        user_id=current_user.id,
        case_id=case_id,
        status=ExecutionStatus.PENDING,
        input_filename=file.filename,
        input_metadata={"content_type": file.content_type, "params": tool_params},
        ip_address=request.client.host if request.client else None,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    exec_dir = os.path.join("data", "forensics", "executions", execution_id)
    os.makedirs(exec_dir, exist_ok=True)

    safe_filename = file.filename or "uploaded_file"
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._- ")[:255]
    if not safe_filename:
        safe_filename = "uploaded_file"

    file_path = os.path.join(exec_dir, safe_filename)

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = f"File save failed: {str(e)}"
        execution.completed_at = datetime.utcnow()
        await db.commit()
        return _build_execution_response(execution)

    execution.input_file_path = file_path
    execution.status = ExecutionStatus.RUNNING
    await db.commit()

    start_time = time.time()

    try:
        handler = TOOL_HANDLERS[tool_key]
        output_data, confidence = await handler(file_path, tool_params)

        elapsed_ms = int((time.time() - start_time) * 1000)

        execution.output_data = output_data
        execution.confidence_score = confidence
        execution.execution_time_ms = elapsed_ms
        execution.completed_at = datetime.utcnow()

        if output_data.get("error"):
            execution.status = ExecutionStatus.FAILED
            execution.error_message = output_data["error"]
        else:
            execution.status = ExecutionStatus.COMPLETED

        await db.commit()
        await db.refresh(execution)

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        execution.status = ExecutionStatus.FAILED
        execution.error_message = f"Execution error: {str(e)}"
        execution.execution_time_ms = elapsed_ms
        execution.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(execution)

    return _build_execution_response(execution)


@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    tool_key: str | None = Query(default=None),
    status: str | None = Query(default=None),
    case_id: int | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List executions with pagination and filters."""
    query = select(ForensicToolExecution).where(
        ForensicToolExecution.user_id == current_user.id
    )

    if tool_key:
        query = query.where(ForensicToolExecution.tool_key == tool_key)
    if status:
        try:
            status_enum = ExecutionStatus(status)
            query = query.where(ForensicToolExecution.status == status_enum)
        except ValueError:
            pass
    if case_id:
        query = query.where(ForensicToolExecution.case_id == case_id)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.where(ForensicToolExecution.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.where(ForensicToolExecution.created_at <= dt_to)
        except ValueError:
            pass

    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    query = query.order_by(desc(ForensicToolExecution.created_at)).offset(offset).limit(per_page)

    result = await db.execute(query)
    executions = result.scalars().all()

    items = [ExecutionResponse(**_build_execution_response(ex)) for ex in executions]

    return ExecutionListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single execution detail."""
    result = await db.execute(
        select(ForensicToolExecution).where(
            ForensicToolExecution.execution_id == execution_id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.user_id != current_user.id:
        from app.models.user import ROLE_HIERARCHY
        if ROLE_HIERARCHY.get(current_user.role, 0) < ROLE_HIERARCHY.get(UserRole.INSPECTOR, 3):
            raise HTTPException(status_code=403, detail="Access denied")

    return _build_execution_response(execution)


@router.post("/executions/{execution_id}/link-case")
async def link_execution_to_case(
    execution_id: str,
    body: LinkCaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Link an execution result to a case."""
    result = await db.execute(
        select(ForensicToolExecution).where(
            ForensicToolExecution.execution_id == execution_id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.models.case import Case
    case_result = await db.execute(select(Case).where(Case.id == body.case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    execution.case_id = body.case_id
    await db.commit()

    return {"status": "ok", "execution_id": execution_id, "case_id": body.case_id}


@router.post("/executions/{execution_id}/promote-evidence")
async def promote_to_evidence(
    execution_id: str,
    body: PromoteEvidenceRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an Evidence record from an execution result."""
    result = await db.execute(
        select(ForensicToolExecution).where(
            ForensicToolExecution.execution_id == execution_id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not execution.case_id:
        raise HTTPException(
            status_code=400,
            detail="Execution must be linked to a case before promoting to evidence. Use link-case first.",
        )
    if execution.evidence_id:
        raise HTTPException(status_code=400, detail="Execution already promoted to evidence")

    from app.models.evidence import Evidence

    file_path = execution.input_file_path or ""
    file_size = 0
    file_hash = ""
    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)
        file_hash = sha256.hexdigest()

    ext = os.path.splitext(execution.input_filename or "")[1].lower()
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    audio_exts = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
    video_exts = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}
    doc_exts = {".pdf", ".doc", ".docx", ".txt", ".xlsx", ".csv"}

    if ext in image_exts:
        file_type = "image"
    elif ext in audio_exts:
        file_type = "audio"
    elif ext in video_exts:
        file_type = "video"
    elif ext in doc_exts:
        file_type = "document"
    else:
        file_type = "other"

    description = ""
    if body and body.description:
        description = body.description
    else:
        description = f"Forensic toolkit result: {execution.tool_key} on {execution.input_filename}"

    evidence = Evidence(
        case_id=execution.case_id,
        file_path=file_path,
        original_filename=execution.input_filename or "unknown",
        file_type=file_type,
        file_size=file_size,
        file_hash=file_hash,
        description=description,
        tags=body.tags if body and body.tags else [execution.tool_key, "forensic_toolkit"],
        uploaded_by=current_user.id,
        analysis_results=execution.output_data,
    )
    db.add(evidence)
    await db.flush()

    execution.evidence_id = evidence.id
    await db.commit()
    await db.refresh(evidence)

    return {
        "status": "ok",
        "evidence_id": evidence.id,
        "execution_id": execution_id,
        "case_id": execution.case_id,
    }


@router.post("/executions/{execution_id}/summarize")
@limiter.limit("10/minute")
async def summarize_execution(
    request: Request,
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI summary of execution results using Gemini."""
    result = await db.execute(
        select(ForensicToolExecution).where(
            ForensicToolExecution.execution_id == execution_id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not execution.output_data:
        raise HTTPException(status_code=400, detail="No output data to summarize")

    summary = await generate_execution_summary(
        execution.output_data,
        execution.tool_key,
        execution.input_filename or "unknown",
    )

    execution.ai_summary = summary
    await db.commit()

    return {
        "status": "ok",
        "execution_id": execution_id,
        "ai_summary": summary,
    }


@router.get("/saved")
async def list_saved_results(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List bookmarked/saved results for the current user."""
    query = (
        select(ForensicSavedResult)
        .where(ForensicSavedResult.user_id == current_user.id)
        .order_by(desc(ForensicSavedResult.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    saved_items = result.scalars().all()

    count_result = await db.execute(
        select(func.count())
        .select_from(ForensicSavedResult)
        .where(ForensicSavedResult.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    items = []
    for item in saved_items:
        items.append({
            "id": item.id,
            "execution_id": item.execution_id,
            "title": item.title,
            "notes": item.notes,
            "is_bookmarked": item.is_bookmarked,
            "linked_case_id": item.linked_case_id,
            "created_at": item.created_at,
        })

    return {"items": items, "total": total}


@router.post("/saved", status_code=201)
async def save_result(
    body: SavedResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bookmark an execution result."""
    exec_result = await db.execute(
        select(ForensicToolExecution).where(
            ForensicToolExecution.execution_id == body.execution_id
        )
    )
    execution = exec_result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    existing = await db.execute(
        select(ForensicSavedResult).where(
            and_(
                ForensicSavedResult.execution_id == execution.id,
                ForensicSavedResult.user_id == current_user.id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Result already bookmarked")

    saved = ForensicSavedResult(
        execution_id=execution.id,
        user_id=current_user.id,
        title=body.title,
        notes=body.notes,
        is_bookmarked=True,
        linked_case_id=execution.case_id,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)

    return {
        "id": saved.id,
        "execution_id": saved.execution_id,
        "title": saved.title,
        "notes": saved.notes,
        "is_bookmarked": saved.is_bookmarked,
        "linked_case_id": saved.linked_case_id,
        "created_at": saved.created_at,
    }


@router.delete("/saved/{saved_id}")
async def delete_saved_result(
    saved_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a bookmark."""
    result = await db.execute(
        select(ForensicSavedResult).where(
            and_(
                ForensicSavedResult.id == saved_id,
                ForensicSavedResult.user_id == current_user.id,
            )
        )
    )
    saved = result.scalar_one_or_none()

    if not saved:
        raise HTTPException(status_code=404, detail="Saved result not found")

    await db.delete(saved)
    await db.commit()

    return {"status": "ok", "deleted_id": saved_id}


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin view: per-officer stats, tool usage, success/failure rates."""
    total_result = await db.execute(
        select(func.count()).select_from(ForensicToolExecution)
    )
    total_executions = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count())
        .select_from(ForensicToolExecution)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
    )
    completed_count = completed_result.scalar() or 0
    success_rate = round((completed_count / total_executions * 100), 1) if total_executions > 0 else 0.0

    officer_result = await db.execute(
        select(
            ForensicToolExecution.user_id,
            func.count().label("total"),
            func.count().filter(ForensicToolExecution.status == ExecutionStatus.COMPLETED).label("completed"),
            func.count().filter(ForensicToolExecution.status == ExecutionStatus.FAILED).label("failed"),
        )
        .group_by(ForensicToolExecution.user_id)
        .order_by(desc("total"))
        .limit(50)
    )
    officer_rows = officer_result.all()

    by_officer = []
    for row in officer_rows:
        user_result = await db.execute(select(User).where(User.id == row[0]))
        user = user_result.scalar_one_or_none()
        if user:
            officer_total = row[1]
            officer_completed = row[2]
            officer_failed = row[3]
            by_officer.append(AdminOfficerStats(
                user_id=user.id,
                full_name=user.full_name,
                username=user.username,
                total_executions=officer_total,
                completed=officer_completed,
                failed=officer_failed,
                success_rate=round((officer_completed / officer_total * 100), 1) if officer_total > 0 else 0.0,
            ))

    tool_result = await db.execute(
        select(
            ForensicToolExecution.tool_key,
            func.count().label("total"),
            func.count().filter(ForensicToolExecution.status == ExecutionStatus.COMPLETED).label("completed"),
            func.count().filter(ForensicToolExecution.status == ExecutionStatus.FAILED).label("failed"),
            func.avg(ForensicToolExecution.execution_time_ms).label("avg_time"),
        )
        .group_by(ForensicToolExecution.tool_key)
        .order_by(desc("total"))
    )
    tool_rows = tool_result.all()

    by_tool = []
    for row in tool_rows:
        by_tool.append(AdminToolStats(
            tool_key=row[0],
            total_executions=row[1],
            completed=row[2],
            failed=row[3],
            avg_time_ms=round(float(row[4] or 0), 1),
        ))

    recent_result = await db.execute(
        select(ForensicToolExecution)
        .order_by(desc(ForensicToolExecution.created_at))
        .limit(20)
    )
    recent_executions = recent_result.scalars().all()

    recent_activity = []
    for ex in recent_executions:
        user_result = await db.execute(select(User).where(User.id == ex.user_id))
        user = user_result.scalar_one_or_none()
        recent_activity.append(AdminRecentActivity(
            execution_id=ex.execution_id,
            tool_key=ex.tool_key,
            status=ex.status.value if isinstance(ex.status, ExecutionStatus) else ex.status,
            user_full_name=user.full_name if user else "Unknown",
            created_at=ex.created_at,
        ))

    return AdminStatsResponse(
        total_executions=total_executions,
        by_officer=by_officer,
        by_tool=by_tool,
        success_rate=success_rate,
        recent_activity=recent_activity,
    )


@router.post("/investigation-report/{case_id}")
@limiter.limit("5/minute")
async def generate_investigation_report(
    request: Request,
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Generate comprehensive AI investigation report correlating all evidence for a case."""
    from app.models.case import Case
    from app.models.evidence import Evidence

    # Verify case exists
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Gather all forensic executions for this case
    exec_result = await db.execute(
        select(ForensicToolExecution)
        .where(
            and_(
                ForensicToolExecution.case_id == case_id,
                ForensicToolExecution.status == ExecutionStatus.COMPLETED,
            )
        )
        .order_by(ForensicToolExecution.created_at)
    )
    executions = exec_result.scalars().all()

    # Gather all evidence
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id)
    )
    evidence_items = evidence_result.scalars().all()

    # Compile evidence by category
    face_results = []
    fingerprint_results = []
    vehicle_results = []
    weapon_results = []
    dna_results = []
    ocr_results = []
    document_results = []
    other_results = []

    for ex in executions:
        output = ex.output_data or {}
        entry = {
            "tool": ex.tool_key,
            "filename": ex.input_filename,
            "confidence": ex.confidence_score,
            "executed_at": ex.created_at.isoformat() if ex.created_at else None,
            "data": output,
        }

        if ex.tool_key in ("face_detect", "face_recognize"):
            face_results.append(entry)
        elif ex.tool_key == "fingerprint_match":
            fingerprint_results.append(entry)
        elif ex.tool_key in ("vehicle_detect", "license_plate_ocr"):
            vehicle_results.append(entry)
        elif ex.tool_key == "weapon_detect":
            weapon_results.append(entry)
        elif ex.tool_key == "dna_search":
            dna_results.append(entry)
        elif ex.tool_key in ("image_ocr", "document_ocr"):
            ocr_results.append(entry)
        elif ex.tool_key in ("document_pdf_parse", "document_summarize"):
            document_results.append(entry)
        else:
            other_results.append(entry)

    # Search criminal repository for any matched IDs
    criminal_matches = set()
    for face_entry in face_results:
        for match in face_entry["data"].get("matches", []):
            criminal_matches.add(match.get("criminal_id", ""))
    for fp_entry in fingerprint_results:
        for match in fp_entry["data"].get("matches", []):
            criminal_matches.add(match.get("criminal_id", ""))
    for dna_entry in dna_results:
        for match in dna_entry["data"].get("matches", []):
            criminal_matches.add(match.get("criminal_id", ""))

    criminal_matches.discard("")

    # Fetch criminal profiles for matched IDs
    criminal_profiles = []
    if criminal_matches:
        from sqlalchemy import text
        crim_ids = "','".join(str(cid) for cid in criminal_matches)
        crim_result = await db.execute(
            text(f"""
                SELECT criminal_id, full_name, father_name, gender, wanted_status,
                       danger_level, gang_name, gang_role, crime_categories,
                       modus_operandi, total_arrests, total_firs, identifying_marks
                FROM criminal_profiles
                WHERE criminal_id IN ('{crim_ids}') AND is_active = true
            """)
        )
        for row in crim_result.fetchall():
            criminal_profiles.append({
                "criminal_id": row[0],
                "full_name": row[1],
                "father_name": row[2],
                "gender": row[3],
                "wanted_status": row[4],
                "danger_level": row[5],
                "gang_name": row[6],
                "gang_role": row[7],
                "crime_categories": row[8],
                "modus_operandi": row[9],
                "total_arrests": row[10],
                "total_firs": row[11],
                "identifying_marks": row[12],
            })

    # Search RAG for relevant BNS sections
    legal_references = []
    try:
        from app.ai.rag.retriever import search_legal_provisions
        case_desc = getattr(case, "description", "") or getattr(case, "brief_description", "") or ""
        if case_desc:
            legal_results = await search_legal_provisions(case_desc[:500], top_k=5)
            for lr in legal_results:
                legal_references.append({
                    "section": lr.payload.get("section_number", ""),
                    "act": lr.payload.get("act", ""),
                    "heading": lr.payload.get("heading", ""),
                    "text": lr.payload.get("text", "")[:300],
                    "relevance_score": round(lr.score, 3),
                })
    except Exception as e:
        logger.warning(f"RAG search failed for investigation report: {e}")

    # Compile the report data
    report_data = {
        "case_id": case_id,
        "case_public_id": getattr(case, "public_id", str(case_id)),
        "case_title": getattr(case, "title", ""),
        "total_evidence_items": len(evidence_items),
        "total_forensic_executions": len(executions),
        "face_analysis": {
            "executions": len(face_results),
            "faces_detected": sum(e["data"].get("faces_detected", 0) for e in face_results),
            "matches_found": sum(e["data"].get("matches_found", 0) for e in face_results),
            "top_matches": [
                m for entry in face_results
                for m in entry["data"].get("matches", [])[:3]
            ][:5],
        },
        "fingerprint_analysis": {
            "executions": len(fingerprint_results),
            "matches_found": sum(e["data"].get("matches_found", 0) for e in fingerprint_results),
            "top_matches": [
                m for entry in fingerprint_results
                for m in entry["data"].get("matches", [])[:3]
            ][:5],
        },
        "vehicle_analysis": {
            "executions": len(vehicle_results),
            "vehicles_detected": sum(e["data"].get("vehicles_detected", 0) for e in vehicle_results),
            "plates_detected": sum(e["data"].get("plates_detected", 0) for e in vehicle_results),
            "plates": [
                p for entry in vehicle_results
                for p in entry["data"].get("plates", [])
            ][:10],
        },
        "weapon_analysis": {
            "executions": len(weapon_results),
            "weapons_detected": sum(e["data"].get("weapons_detected", 0) for e in weapon_results),
            "weapons": [
                w for entry in weapon_results
                for w in entry["data"].get("weapons", [])
            ][:10],
        },
        "dna_analysis": {
            "executions": len(dna_results),
            "matches_found": sum(e["data"].get("matches_found", 0) for e in dna_results),
            "top_matches": [
                m for entry in dna_results
                for m in entry["data"].get("matches", [])[:3]
            ][:5],
        },
        "ocr_and_documents": {
            "executions": len(ocr_results) + len(document_results),
            "text_extracted": any(e["data"].get("text", "") for e in ocr_results + document_results),
        },
        "criminal_suspects": criminal_profiles,
        "legal_references": legal_references,
    }

    # Generate AI summary
    ai_summary = None
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if has_any_llm_key():
            report_json = json.dumps(report_data, indent=2, default=str)[:8000]

            prompt = (
                "You are a senior police investigation analyst. Based on the following forensic evidence "
                "data from a criminal case, generate a comprehensive Investigation Summary Report.\n\n"
                f"Evidence Data:\n{report_json}\n\n"
                "Generate the following sections:\n\n"
                "## Investigation Summary\n"
                "Brief overview of the case evidence collected.\n\n"
                "## Possible Suspects\n"
                "Based on face recognition, fingerprint, and DNA matches. Include confidence levels.\n\n"
                "## Evidence Correlation\n"
                "How different pieces of evidence connect to each other.\n\n"
                "## Vehicle Intelligence\n"
                "Any vehicles or license plates identified and their relevance.\n\n"
                "## Weapon Assessment\n"
                "Weapons detected and threat level.\n\n"
                "## Known Associates\n"
                "Based on criminal profiles found.\n\n"
                "## Timeline\n"
                "Chronological order of evidence collection.\n\n"
                "## Recommended Investigation Steps\n"
                "Next actions for the investigating team.\n\n"
                "## Relevant BNS Sections\n"
                "Applicable legal sections based on evidence.\n\n"
                "## Confidence Assessment\n"
                "Overall confidence level in the findings.\n\n"
                "Be professional, factual, and actionable."
            )

            import asyncio
            ai_summary = await asyncio.to_thread(generate_text, prompt, 0.3, 2048)
    except Exception as e:
        ai_summary = f"AI report generation unavailable: {str(e)}"

    report_data["ai_investigation_summary"] = ai_summary
    report_data["generated_at"] = datetime.utcnow().isoformat()
    report_data["generated_by"] = current_user.full_name

    # Save as execution record
    report_execution = ForensicToolExecution(
        execution_id=str(uuid.uuid4()),
        tool_key="investigation_report",
        user_id=current_user.id,
        case_id=case_id,
        status=ExecutionStatus.COMPLETED,
        input_filename=f"investigation_report_case_{case_id}.json",
        output_data=report_data,
        confidence_score=0.85 if criminal_profiles else 0.5,
        execution_time_ms=0,
        completed_at=datetime.utcnow(),
    )
    db.add(report_execution)
    await db.commit()

    return report_data


@router.get("/admin/officer-activity")
async def get_officer_activity(
    user_id: int | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin: officer activity log."""
    since = datetime.utcnow() - timedelta(days=days)

    query = select(ForensicToolExecution).where(
        ForensicToolExecution.created_at >= since
    )

    if user_id:
        query = query.where(ForensicToolExecution.user_id == user_id)

    query = query.order_by(desc(ForensicToolExecution.created_at)).limit(limit)

    result = await db.execute(query)
    executions = result.scalars().all()

    activity = []
    user_cache: dict[int, str] = {}
    for ex in executions:
        if ex.user_id not in user_cache:
            user_result = await db.execute(select(User).where(User.id == ex.user_id))
            user = user_result.scalar_one_or_none()
            user_cache[ex.user_id] = user.full_name if user else "Unknown"

        activity.append({
            "execution_id": ex.execution_id,
            "tool_key": ex.tool_key,
            "status": ex.status.value if isinstance(ex.status, ExecutionStatus) else ex.status,
            "user_id": ex.user_id,
            "user_full_name": user_cache[ex.user_id],
            "input_filename": ex.input_filename,
            "execution_time_ms": ex.execution_time_ms,
            "case_id": ex.case_id,
            "created_at": ex.created_at.isoformat() if ex.created_at else None,
            "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
            "ip_address": ex.ip_address,
        })

    return {"activity": activity, "total": len(activity), "days": days}
