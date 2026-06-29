from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.evidence import EvidenceResponse, EvidenceListResponse
from app.services.auth_service import get_current_user
from app.services.evidence_service import (
    save_upload_file,
    create_evidence,
    get_evidence_for_case,
    get_evidence_by_id,
    get_file_type,
    is_allowed_file,
)

router = APIRouter()


@router.post("/upload/{case_id}", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: int,
    file: UploadFile = File(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not is_allowed_file(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")

    try:
        file_path, file_size = await save_upload_file(file, case_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))

    file_type = get_file_type(file.filename)
    evidence = await create_evidence(
        db, case_id, file_path, file.filename, file_type, file_size, current_user.id, description
    )
    return EvidenceResponse.model_validate(evidence)


@router.get("/case/{case_id}", response_model=EvidenceListResponse)
async def list_evidence(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence_list, total = await get_evidence_for_case(db, case_id)
    return EvidenceListResponse(
        evidence=[EvidenceResponse.model_validate(e) for e in evidence_list],
        total=total,
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return EvidenceResponse.model_validate(evidence)
