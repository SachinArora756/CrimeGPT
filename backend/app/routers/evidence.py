from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, UploadFile, File, Form, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.timeline import TimelineEventType
from app.models.notification import NotificationType
from app.schemas.evidence import EvidenceResponse, EvidenceListResponse
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access, filter_cases_for_user
from app.services.timeline_service import add_event
from app.services.notification_service import notify_case_team
from app.services.evidence_service import (
    save_upload_file,
    create_evidence,
    get_evidence_for_case,
    get_evidence_by_id,
    get_file_type,
    is_allowed_file,
    verify_evidence_integrity,
)
from app.services.forensics_service import analyze_evidence
from app.utils.rate_limiter import limiter

router = APIRouter()


class TagsUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        for tag in v:
            if len(tag) > 100 or len(tag) < 1:
                raise ValueError("Each tag must be 1-100 characters")
        return v


@router.get("/mine")
async def list_my_evidence(
    file_type: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all evidence across all cases the current user can access."""
    user_case_ids_q = select(Case.id)
    user_case_ids_q = filter_cases_for_user(user_case_ids_q, current_user)
    user_case_ids_result = await db.execute(user_case_ids_q)
    user_case_ids = [row[0] for row in user_case_ids_result.all()]

    if not user_case_ids:
        return {"evidence": [], "total": 0}

    query = select(Evidence).where(Evidence.case_id.in_(user_case_ids))

    if file_type:
        query = query.where(Evidence.file_type == file_type)
    if case_id:
        case_result = await db.execute(select(Case.id).where(Case.public_id == case_id))
        case_int_id = case_result.scalar_one_or_none()
        if case_int_id:
            query = query.where(Evidence.case_id == case_int_id)
    if search:
        safe_q = search.replace("%", r"\%").replace("_", r"\_")
        pattern = f"%{safe_q}%"
        query = query.where(
            Evidence.original_filename.ilike(pattern, escape="\\")
            | Evidence.description.ilike(pattern, escape="\\")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    query = query.order_by(Evidence.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    case_cache = {}
    evidence_out = []
    for ev in items:
        if ev.case_id not in case_cache:
            c_result = await db.execute(select(Case.public_id, Case.fir_number).where(Case.id == ev.case_id))
            row = c_result.one_or_none()
            case_cache[ev.case_id] = {"public_id": row[0] if row else "", "fir_number": row[1] if row else ""}
        cached = case_cache[ev.case_id]
        evidence_out.append({
            "id": ev.id,
            "case_id": ev.case_id,
            "case_public_id": cached["public_id"],
            "fir_number": cached["fir_number"],
            "file_path": ev.file_path,
            "original_filename": ev.original_filename,
            "file_type": ev.file_type,
            "file_size": ev.file_size,
            "file_hash": ev.file_hash,
            "description": ev.description,
            "tags": ev.tags,
            "uploaded_by": ev.uploaded_by,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        })

    return {"evidence": evidence_out, "total": total}


@router.post("/upload/{case_id}", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_evidence(
    request: Request,
    case_id: str = Path(),
    file: UploadFile = File(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)

    if not file.filename or not is_allowed_file(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")

    try:
        file_path, file_size, file_hash = await save_upload_file(file, case.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))

    file_type = get_file_type(file.filename)
    evidence = await create_evidence(
        db, case.id, file_path, file.filename, file_type, file_size,
        current_user.id, description, file_hash=file_hash,
    )

    await add_event(
        db, case.id, TimelineEventType.EVIDENCE_UPLOADED,
        f"Evidence uploaded: {file.filename}",
        f"{file_type} file ({file_size} bytes) uploaded by {current_user.full_name}",
        actor_id=current_user.id,
    )

    await notify_case_team(
        db, case, NotificationType.EVIDENCE_UPLOADED,
        f"New evidence in case {case.fir_number}",
        f"{current_user.full_name} uploaded {file.filename}",
        exclude_user_id=current_user.id,
    )

    return EvidenceResponse.model_validate(evidence)


@router.get("/case/{case_id}", response_model=EvidenceListResponse)
async def list_evidence(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    evidence_list, total = await get_evidence_for_case(db, case.id)
    return EvidenceListResponse(
        evidence=[EvidenceResponse.model_validate(e) for e in evidence_list],
        total=total,
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    await authorize_case_access(db, evidence.case_id, current_user)
    return EvidenceResponse.model_validate(evidence)


@router.put("/{evidence_id}/tags")
async def update_evidence_tags(
    *,
    evidence_id: int = Path(ge=1),
    body: TagsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    await authorize_case_access(db, evidence.case_id, current_user)
    evidence.tags = body.tags
    await db.commit()
    return {"status": "ok", "tags": body.tags}


@router.get("/{evidence_id}/verify")
async def verify_evidence(
    evidence_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify evidence integrity by re-computing SHA-256 and comparing to stored hash."""
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    await authorize_case_access(db, evidence.case_id, current_user)
    return await verify_evidence_integrity(evidence)


@router.get("/case/{case_id}/verify-all")
async def verify_all_evidence(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify integrity of ALL evidence files in a case."""
    case = await authorize_case_access(db, case_id, current_user)
    evidence_list, _ = await get_evidence_for_case(db, case.id)
    results = []
    tampered_count = 0
    for ev in evidence_list:
        result = await verify_evidence_integrity(ev)
        results.append(result)
        if result.get("tampered"):
            tampered_count += 1
    return {
        "case_id": case_id,
        "total_evidence": len(results),
        "tampered_count": tampered_count,
        "all_intact": tampered_count == 0,
        "results": results,
    }


@router.post("/{evidence_id}/analyze")
@limiter.limit("5/minute")
async def analyze_evidence_file(
    request: Request,
    evidence_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run digital forensics analysis on an evidence file."""
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    await authorize_case_access(db, evidence.case_id, current_user)

    result = await analyze_evidence(evidence)

    evidence.analysis_results = result.get("forensic_data")
    await db.commit()

    return result
