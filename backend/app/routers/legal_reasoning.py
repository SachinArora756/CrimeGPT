from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.models.legal_recommendation import LegalRecommendation, RecommendationStatus
from app.models.timeline import TimelineEvent, TimelineEventType
from app.schemas.legal_reasoning import (
    RecommendationResponse,
    RecommendationGenerateRequest,
    ApprovalRequest,
    SectionRecommendation,
)
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access
from app.services.legal_reasoning_service import generate_recommendations, approve_recommendations
from app.utils.rate_limiter import limiter

router = APIRouter()


def _build_response(rec: LegalRecommendation) -> RecommendationResponse:
    recs_data = rec.recommendations or {}
    recommendations_raw = recs_data.get("recommendations", [])
    recommendations = []
    for r in recommendations_raw:
        recommendations.append(SectionRecommendation(
            section=r.get("section", ""),
            act=r.get("act", ""),
            title=r.get("title", ""),
            explanation=r.get("explanation", ""),
            supporting_evidence=r.get("supporting_evidence", []),
            confidence=r.get("confidence", 0.5),
            punishment_range=r.get("punishment_range", ""),
            is_primary=r.get("is_primary", True),
        ))

    return RecommendationResponse(
        id=rec.id,
        case_id=rec.case_id,
        recommendations=recommendations,
        procedural_notes=recs_data.get("procedural_notes", []),
        evidence_gaps=recs_data.get("evidence_gaps", []),
        overall_confidence=rec.overall_confidence,
        status=rec.status.value,
        approved_sections=rec.approved_sections,
        officer_notes=rec.officer_notes,
        approved_by=rec.approved_by,
        approved_at=rec.approved_at,
        created_by=rec.created_by,
        created_at=rec.created_at,
    )


@router.post("/recommend/{case_id}", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_recommendation(
    request: Request,
    *,
    case_id: str = Path(),
    rec_request: RecommendationGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)

    rec = await generate_recommendations(
        db, case.id, current_user.id, rec_request.focus_area
    )
    return _build_response(rec)


@router.get("/recommend/{case_id}", response_model=RecommendationResponse)
async def get_latest_recommendation(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)

    result = await db.execute(
        select(LegalRecommendation)
        .where(LegalRecommendation.case_id == case.id)
        .order_by(LegalRecommendation.created_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations found for this case",
        )
    return _build_response(rec)


@router.get("/recommend/{case_id}/history", response_model=list[RecommendationResponse])
async def get_recommendation_history(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)

    result = await db.execute(
        select(LegalRecommendation)
        .where(LegalRecommendation.case_id == case.id)
        .order_by(LegalRecommendation.created_at.desc())
    )
    recs = result.scalars().all()
    return [_build_response(r) for r in recs]


@router.put("/recommend/{case_id}/approve", response_model=RecommendationResponse)
async def approve_recommendation(
    *,
    case_id: str = Path(),
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)

    result = await db.execute(
        select(LegalRecommendation)
        .where(LegalRecommendation.case_id == case.id)
        .order_by(LegalRecommendation.created_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations found for this case",
        )

    if rec.status != RecommendationStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recommendation already {rec.status.value}",
        )

    rec = await approve_recommendations(
        db, rec, request.approved_sections, request.notes, current_user.id
    )

    if request.approved_sections:
        existing = case.sections_applied or []
        merged = list(set(existing + request.approved_sections))
        case.sections_applied = merged
        await db.commit()

        timeline_event = TimelineEvent(
            case_id=case.id,
            event_type=TimelineEventType.INVESTIGATION_UPDATE,
            title="Legal Sections Approved",
            description=f"Legal sections approved: {', '.join(request.approved_sections)}",
            actor_id=current_user.id,
        )
        db.add(timeline_event)
        await db.commit()

    return _build_response(rec)
