import hashlib
import os
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.models.document import Document, CaseDiary
from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentResponse,
    CaseDiaryCreate,
    CaseDiaryResponse,
)
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access, filter_cases_for_user
from app.utils.rate_limiter import limiter

router = APIRouter()


@router.get("/mine")
async def list_my_documents(
    doc_type: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all documents across all cases the current user can access."""
    user_case_ids_q = select(Case.id)
    user_case_ids_q = filter_cases_for_user(user_case_ids_q, current_user)
    user_case_ids_result = await db.execute(user_case_ids_q)
    user_case_ids = [row[0] for row in user_case_ids_result.all()]

    if not user_case_ids:
        return {"documents": [], "total": 0}

    query = select(Document).where(Document.case_id.in_(user_case_ids))

    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if case_id:
        case_result = await db.execute(select(Case.id).where(Case.public_id == case_id))
        case_int_id = case_result.scalar_one_or_none()
        if case_int_id:
            query = query.where(Document.case_id == case_int_id)

    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    query = query.order_by(Document.generated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    docs = result.scalars().all()

    docs_with_case = []
    case_cache = {}
    for d in docs:
        if d.case_id not in case_cache:
            c_result = await db.execute(select(Case.public_id, Case.fir_number).where(Case.id == d.case_id))
            row = c_result.one_or_none()
            case_cache[d.case_id] = {"public_id": row[0] if row else "", "fir_number": row[1] if row else ""}
        cached = case_cache[d.case_id]
        docs_with_case.append({
            "id": d.id,
            "case_id": d.case_id,
            "case_public_id": cached["public_id"],
            "fir_number": cached["fir_number"],
            "doc_type": d.doc_type.value,
            "output_format": d.output_format,
            "file_path": d.file_path,
            "file_hash": d.file_hash,
            "generated_by": d.generated_by,
            "generated_at": d.generated_at.isoformat() if d.generated_at else None,
        })

    return {"documents": docs_with_case, "total": total}


@router.post("/generate/{case_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def generate_document(
    request: Request,
    *,
    case_id: str = Path(),
    doc_request: DocumentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)

    from app.ai.agents.document_gen import generate_legal_document

    try:
        file_path = await generate_legal_document(
            db, case.id, doc_request.doc_type, doc_request.additional_context, doc_request.output_format
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document generation failed")

    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    file_hash = sha.hexdigest()

    doc = Document(
        case_id=case.id,
        doc_type=doc_request.doc_type,
        output_format=doc_request.output_format,
        file_path=file_path,
        file_hash=file_hash,
        generated_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    from app.services.notification_service import notify_document_generated
    await notify_document_generated(db, case, current_user.id, doc_request.doc_type.value)

    return DocumentResponse.model_validate(doc)


@router.get("/case/{case_id}", response_model=list[DocumentResponse])
async def list_documents(
    case_id: str = Path(),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    result = await db.execute(
        select(Document)
        .where(Document.case_id == case.id)
        .order_by(Document.generated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/download/{doc_id}")
async def download_document(
    doc_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await authorize_case_access(db, doc.case_id, current_user)

    base_dir = os.path.realpath(settings.upload_dir)
    real_path = os.path.realpath(doc.file_path)
    if not real_path.startswith(base_dir):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not os.path.exists(real_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    ext = "pdf" if doc.output_format == "pdf" else "docx"
    if ext == "pdf":
        media_type = "application/pdf"
    else:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        real_path,
        filename=f"{doc.doc_type.value}_{doc.case_id}.{ext}",
        media_type=media_type,
    )


@router.post("/diary/{case_id}", response_model=CaseDiaryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_diary_entry(
    request: Request,
    *,
    case_id: str = Path(),
    entry: CaseDiaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    diary = CaseDiary(
        case_id=case.id,
        entry_date=entry.entry_date,
        content=entry.content,
        entry_type=entry.entry_type,
        officer_id=current_user.id,
    )
    db.add(diary)
    await db.commit()
    await db.refresh(diary)
    return CaseDiaryResponse.model_validate(diary)


@router.get("/diary/{case_id}", response_model=list[CaseDiaryResponse])
async def get_diary_entries(
    case_id: str = Path(),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    result = await db.execute(
        select(CaseDiary)
        .where(CaseDiary.case_id == case.id)
        .order_by(CaseDiary.entry_date.desc())
        .offset(offset)
        .limit(limit)
    )
    entries = result.scalars().all()
    return [CaseDiaryResponse.model_validate(e) for e in entries]


@router.post("/recompute-hashes")
async def recompute_document_hashes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Backfill SHA-256 hashes for documents that don't have one yet."""
    from app.models.user import UserRole
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    result = await db.execute(select(Document).where(Document.file_hash.is_(None)))
    docs = result.scalars().all()
    updated = 0
    for doc in docs:
        if os.path.exists(doc.file_path):
            sha = hashlib.sha256()
            with open(doc.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    sha.update(chunk)
            doc.file_hash = sha.hexdigest()
            updated += 1
    await db.commit()
    return {"updated": updated, "total_without_hash": len(docs)}
