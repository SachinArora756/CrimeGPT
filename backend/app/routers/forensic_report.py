"""Forensic Investigation Report — API Router.

Endpoints for checking readiness, generating, listing, and downloading
PRISM-format forensic investigation reports.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document, DocType
from app.models.user import User
from app.schemas.forensic_report import (
    ReportReadinessResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportListItem,
)
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access
from app.services.forensic_report_service import (
    check_report_readiness,
    generate_forensic_report_doc,
)
from app.utils.rate_limiter import limiter

router = APIRouter()


@router.get("/report/{case_id}/readiness", response_model=ReportReadinessResponse)
async def get_report_readiness(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check whether the case is ready for forensic report generation."""
    case = await authorize_case_access(db, case_id, current_user)
    readiness = await check_report_readiness(db, case.id)
    return readiness


@router.post("/report/{case_id}/generate", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def generate_report(
    request: Request,
    *,
    case_id: str = Path(),
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a PRISM forensic investigation report for the case."""
    case = await authorize_case_access(db, case_id, current_user)

    try:
        result = await generate_forensic_report_doc(
            db, case.id, current_user.id, body.output_format
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forensic report: {str(e)}",
        )

    return result


@router.get("/report/{case_id}/list", response_model=list[ReportListItem])
async def list_reports(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all previously generated forensic reports for a case."""
    case = await authorize_case_access(db, case_id, current_user)

    result = await db.execute(
        select(Document)
        .where(Document.case_id == case.id, Document.doc_type == DocType.FORENSIC_REPORT)
        .order_by(Document.generated_at.desc())
    )
    docs = result.scalars().all()
    return docs


@router.get("/report/{case_id}/download/{doc_id}")
async def download_report(
    case_id: str = Path(),
    doc_id: int = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a generated forensic report."""
    case = await authorize_case_access(db, case_id, current_user)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.case_id == case.id,
            Document.doc_type == DocType.FORENSIC_REPORT,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    file_path = doc.file_path
    if not os.path.isabs(file_path):
        file_path = os.path.join(settings.upload_dir, file_path)

    real_path = os.path.realpath(file_path)
    upload_real = os.path.realpath(settings.upload_dir)
    if not real_path.startswith(upload_real):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if not os.path.exists(real_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on disk",
        )

    filename = f"PRISM_Forensic_Report_{case.fir_number}.{doc.output_format}"
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if doc.output_format == "docx"
        else "application/pdf"
    )

    return FileResponse(
        path=real_path,
        filename=filename,
        media_type=media_type,
    )


@router.delete("/report/{case_id}/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    case_id: str = Path(),
    doc_id: int = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a generated forensic report."""
    case = await authorize_case_access(db, case_id, current_user)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.case_id == case.id,
            Document.doc_type == DocType.FORENSIC_REPORT,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    file_path = doc.file_path
    if not os.path.isabs(file_path):
        file_path = os.path.join(settings.upload_dir, file_path)

    real_path = os.path.realpath(file_path)
    if os.path.exists(real_path):
        os.remove(real_path)

    await db.delete(doc)
    await db.commit()
