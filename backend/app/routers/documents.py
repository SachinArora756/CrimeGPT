from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.document import Document, CaseDiary
from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentResponse,
    CaseDiaryCreate,
    CaseDiaryResponse,
)
from app.services.auth_service import get_current_user

router = APIRouter()


@router.post("/generate/{case_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def generate_document(
    case_id: int,
    request: DocumentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.ai.agents.document_gen import generate_legal_document

    file_path = await generate_legal_document(db, case_id, request.doc_type, request.additional_context)

    doc = Document(
        case_id=case_id,
        doc_type=request.doc_type,
        file_path=file_path,
        generated_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.get("/case/{case_id}", response_model=list[DocumentResponse])
async def list_documents(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.generated_at.desc())
    )
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/download/{doc_id}")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return FileResponse(doc.file_path, filename=f"{doc.doc_type.value}_{doc.case_id}.docx")


@router.post("/diary/{case_id}", response_model=CaseDiaryResponse, status_code=status.HTTP_201_CREATED)
async def create_diary_entry(
    case_id: int,
    entry: CaseDiaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary = CaseDiary(
        case_id=case_id,
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
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CaseDiary).where(CaseDiary.case_id == case_id).order_by(CaseDiary.entry_date.desc())
    )
    entries = result.scalars().all()
    return [CaseDiaryResponse.model_validate(e) for e in entries]
