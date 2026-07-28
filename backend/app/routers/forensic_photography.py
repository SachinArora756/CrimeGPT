"""
Forensic Photography Router

Provides endpoints for crime scene photo upload, camera capture,
AI photography guidance, quality assessment, annotation, enhancement,
scene coverage tracking, object detection, and report generation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.services.auth_service import get_current_user, require_min_role
from app.models.user import User, UserRole
from app.models.forensic_photography import (
    ForensicPhoto, PhotoAnnotation, SceneCoverageZone, PhotoEnhancementHistory
)
from app.schemas.forensic_photography import (
    PhotoUploadResponse, PhotoDetailResponse, PhotoUpdateRequest,
    PhotoCaptureRequest, GuidanceRequest, GuidanceResponse,
    QualityAssessmentResponse, EnhancementRequest, EnhancementResponse,
    AnnotationCreate, AnnotationResponse, CoverageZoneResponse,
    CoverageStatusResponse, ObjectDetectionResponse,
    PhotoGalleryItem, PhotoGalleryResponse, BatchAssessmentResponse,
)
from app.services.forensic_photography_service import (
    upload_photo, capture_photo, get_photo_by_id, get_photos_for_case,
    update_photo, delete_photo, add_annotation, get_annotations,
    delete_annotation, get_coverage_zones, initialize_coverage_zones,
    update_coverage_zone,
)
from app.services.photo_ai_service import (
    generate_photography_guidance, assess_photo_quality, detect_objects_in_photo,
)
from app.services.photo_enhancement_service import (
    enhance_photo, render_annotations_on_image,
)
from app.services.photo_auto_enhance_service import run_auto_enhance
from app.utils.rate_limiter import limiter
import asyncio
import uuid
import os
import hashlib
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Photo Upload & Capture
# ---------------------------------------------------------------------------

@router.post("/photos/upload/{case_id}", response_model=list[PhotoUploadResponse])
@limiter.limit("20/minute")
async def upload_photos(
    request: Request,
    case_id: int,
    files: list[UploadFile] = File(...),
    category: Optional[str] = Form(None),
    scene_zone: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    results = []
    for file in files:
        try:
            photo = await upload_photo(
                db=db,
                file=file,
                case_id=case_id,
                user_id=current_user.id,
                category=category,
                scene_zone=scene_zone,
                description=description,
            )
            asyncio.create_task(
                run_auto_enhance(photo.id, photo.file_path, case_id, current_user.id)
            )
            results.append(PhotoUploadResponse(
                photo_id=photo.photo_id,
                original_filename=photo.original_filename,
                file_size=photo.file_size,
                file_hash_sha256=photo.file_hash_sha256,
                mime_type=photo.mime_type,
                width=photo.width,
                height=photo.height,
                gps_latitude=photo.gps_latitude,
                gps_longitude=photo.gps_longitude,
                capture_timestamp=photo.capture_timestamp,
                device_make=photo.device_make,
                device_model=photo.device_model,
                category=photo.category,
                capture_source=photo.capture_source,
                created_at=photo.created_at,
            ))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return results


@router.post("/photos/capture/{case_id}", response_model=PhotoUploadResponse)
@limiter.limit("30/minute")
async def capture_photo_endpoint(
    request: Request,
    case_id: int,
    body: PhotoCaptureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    try:
        photo = await capture_photo(
            db=db,
            image_data_b64=body.image_data,
            case_id=case_id,
            user_id=current_user.id,
            filename=body.filename,
            latitude=body.latitude,
            longitude=body.longitude,
            device_info=body.device_info,
        )
        asyncio.create_task(
            run_auto_enhance(photo.id, photo.file_path, case_id, current_user.id)
        )
        return PhotoUploadResponse(
            photo_id=photo.photo_id,
            original_filename=photo.original_filename,
            file_size=photo.file_size,
            file_hash_sha256=photo.file_hash_sha256,
            mime_type=photo.mime_type,
            width=photo.width,
            height=photo.height,
            gps_latitude=photo.gps_latitude,
            gps_longitude=photo.gps_longitude,
            capture_timestamp=photo.capture_timestamp,
            device_make=photo.device_make,
            device_model=photo.device_model,
            category=photo.category,
            capture_source=photo.capture_source,
            created_at=photo.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Auto-Enhancement Status
# ---------------------------------------------------------------------------

@router.get("/photos/{photo_id}/auto-enhance-status")
async def get_auto_enhance_status(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    stmt = select(ForensicPhoto).where(ForensicPhoto.photo_id == photo_id)
    result = await db.execute(stmt)
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    response = {
        "photo_id": photo.photo_id,
        "status": photo.auto_enhance_status,
        "auto_enhanced": photo.auto_enhanced,
        "quality_score": photo.quality_score,
        "issues": photo.quality_assessment.get("issues", []) if photo.quality_assessment else [],
        "enhanced_photo_id": None,
    }

    if photo.auto_enhanced:
        stmt2 = select(ForensicPhoto).where(
            ForensicPhoto.parent_photo_id == photo.id,
            ForensicPhoto.auto_enhanced == True,
        )
        result2 = await db.execute(stmt2)
        enhanced = result2.scalar_one_or_none()
        if enhanced:
            response["enhanced_photo_id"] = enhanced.photo_id

    return response


# ---------------------------------------------------------------------------
# Photo CRUD
# ---------------------------------------------------------------------------

@router.get("/photos/case/{case_id}", response_model=PhotoGalleryResponse)
async def list_photos(
    case_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    scene_zone: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photos, total = await get_photos_for_case(db, case_id, page, page_size, category, scene_zone)
    items = [
        PhotoGalleryItem(
            photo_id=p.photo_id,
            original_filename=p.original_filename,
            thumbnail_url=f"/api/forensic-photography/photos/{p.photo_id}/thumbnail",
            category=p.category,
            quality_score=p.quality_score,
            gps_latitude=p.gps_latitude,
            gps_longitude=p.gps_longitude,
            capture_timestamp=p.capture_timestamp,
            capture_source=p.capture_source,
            created_at=p.created_at,
        )
        for p in photos
    ]
    return PhotoGalleryResponse(case_id=case_id, total=total, page=page, page_size=page_size, photos=items)


@router.get("/photos/{photo_id}", response_model=PhotoDetailResponse)
async def get_photo(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return PhotoDetailResponse.model_validate(photo)


@router.get("/photos/{photo_id}/file")
async def serve_photo_file(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if not os.path.exists(photo.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(photo.file_path, media_type=photo.mime_type, filename=photo.original_filename)


@router.get("/photos/{photo_id}/thumbnail")
async def serve_thumbnail(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
        return FileResponse(photo.thumbnail_path, media_type="image/jpeg")
    if os.path.exists(photo.file_path):
        return FileResponse(photo.file_path, media_type=photo.mime_type)
    raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.patch("/photos/{photo_id}", response_model=PhotoDetailResponse)
async def update_photo_metadata(
    photo_id: str,
    body: PhotoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    photo = await update_photo(db, photo, body.category, body.scene_zone, body.tags, body.description)
    return PhotoDetailResponse.model_validate(photo)


@router.delete("/photos/{photo_id}")
async def delete_photo_endpoint(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    await delete_photo(db, photo)
    return {"detail": "Photo deleted"}


# ---------------------------------------------------------------------------
# AI Photography Guidance
# ---------------------------------------------------------------------------

@router.post("/guidance/generate", response_model=GuidanceResponse)
@limiter.limit("10/minute")
async def generate_guidance(
    request: Request,
    body: GuidanceRequest,
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    result = await generate_photography_guidance(
        crime_type=body.crime_type,
        scene_description=body.scene_description,
        existing_photos_count=body.existing_photos_count,
    )
    return GuidanceResponse(
        crime_type=body.crime_type,
        minimum_shots=result.get("minimum_shots", 20),
        shot_checklist=result.get("shot_checklist", []),
        mandatory_angles=result.get("mandatory_angles", []),
        distance_ranges=result.get("distance_ranges", []),
        brightness_tips=result.get("brightness_tips", []),
        special_requirements=result.get("special_requirements", []),
        common_mistakes=result.get("common_mistakes", []),
        indian_law_requirements=result.get("indian_law_requirements", []),
    )


# ---------------------------------------------------------------------------
# AI Quality Assessment
# ---------------------------------------------------------------------------

@router.post("/quality/assess/{photo_id}", response_model=QualityAssessmentResponse)
@limiter.limit("15/minute")
async def assess_quality(
    request: Request,
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    result = await assess_photo_quality(photo.file_path)

    photo.quality_score = result.get("quality_score")
    photo.courtroom_readiness = result.get("courtroom_readiness")
    photo.quality_assessment = result.get("ai_assessment")
    photo.ai_suggestions = result.get("suggestions")
    await db.commit()

    return QualityAssessmentResponse(
        photo_id=photo_id,
        quality_score=result.get("quality_score", 0),
        courtroom_readiness=result.get("courtroom_readiness", 0),
        technical_metrics=result.get("technical_metrics", {}),
        ai_assessment=result.get("ai_assessment"),
        suggestions=result.get("suggestions", []),
    )


@router.post("/quality/batch-assess/{case_id}", response_model=BatchAssessmentResponse)
@limiter.limit("5/minute")
async def batch_assess_quality(
    request: Request,
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    photos, total = await get_photos_for_case(db, case_id, page=1, page_size=50)
    results = []
    for photo in photos:
        try:
            result = await assess_photo_quality(photo.file_path)
            photo.quality_score = result.get("quality_score")
            photo.courtroom_readiness = result.get("courtroom_readiness")
            photo.quality_assessment = result.get("ai_assessment")
            photo.ai_suggestions = result.get("suggestions")
            results.append(QualityAssessmentResponse(
                photo_id=photo.photo_id,
                quality_score=result.get("quality_score", 0),
                courtroom_readiness=result.get("courtroom_readiness", 0),
                technical_metrics=result.get("technical_metrics", {}),
                ai_assessment=result.get("ai_assessment"),
                suggestions=result.get("suggestions", []),
            ))
        except Exception as e:
            logger.warning(f"Failed to assess photo {photo.photo_id}: {e}")
    await db.commit()

    avg_quality = sum(r.quality_score for r in results) / len(results) if results else 0
    return BatchAssessmentResponse(
        case_id=case_id,
        total_photos=total,
        assessed=len(results),
        average_quality=round(avg_quality, 1),
        photos=results,
    )


# ---------------------------------------------------------------------------
# Object Detection
# ---------------------------------------------------------------------------

@router.post("/detect-objects/{photo_id}", response_model=ObjectDetectionResponse)
@limiter.limit("10/minute")
async def detect_objects(
    request: Request,
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    result = await detect_objects_in_photo(photo.file_path)
    photo.ai_detected_objects = result
    await db.commit()

    return ObjectDetectionResponse(
        photo_id=photo_id,
        objects=result.get("objects", []),
        weapons=result.get("weapons", []),
        vehicles=result.get("vehicles", []),
        persons=result.get("persons", []),
        forensic_items=result.get("forensic_items", []),
    )


# ---------------------------------------------------------------------------
# Image Enhancement
# ---------------------------------------------------------------------------

@router.post("/enhance/{photo_id}", response_model=EnhancementResponse)
@limiter.limit("15/minute")
async def enhance_photo_endpoint(
    request: Request,
    photo_id: str,
    body: EnhancementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    enhanced_path, thumb_path, file_hash = await enhance_photo(
        file_path=photo.file_path,
        enhancement_type=body.enhancement_type,
        parameters=body.parameters,
        case_id=photo.case_id,
    )

    enhanced_photo = ForensicPhoto(
        photo_id=str(uuid.uuid4()),
        case_id=photo.case_id,
        file_path=enhanced_path,
        thumbnail_path=thumb_path,
        original_filename=f"enhanced_{photo.original_filename}",
        file_size=os.path.getsize(enhanced_path),
        file_hash_sha256=file_hash,
        mime_type="image/jpeg",
        width=photo.width,
        height=photo.height,
        category=photo.category,
        scene_zone=photo.scene_zone,
        capture_source=photo.capture_source,
        is_original=False,
        parent_photo_id=photo.id,
        uploaded_by=current_user.id,
        chain_of_custody=[{
            "action": "enhanced",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "enhancement_type": body.enhancement_type,
            "parameters": body.parameters,
        }],
    )
    db.add(enhanced_photo)

    history = PhotoEnhancementHistory(
        original_photo_id=photo.id,
        enhancement_type=body.enhancement_type,
        parameters=body.parameters,
        performed_by=current_user.id,
    )
    db.add(history)
    await db.commit()
    await db.refresh(enhanced_photo)

    history.enhanced_photo_id = enhanced_photo.id
    await db.commit()

    return EnhancementResponse(
        original_photo_id=photo.photo_id,
        enhanced_photo_id=enhanced_photo.photo_id,
        enhancement_type=body.enhancement_type,
        parameters=body.parameters,
    )


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------

@router.get("/annotations/{photo_id}", response_model=list[AnnotationResponse])
async def get_photo_annotations(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    annotations = await get_annotations(db, photo.id)
    return [AnnotationResponse.model_validate(a) for a in annotations]


@router.post("/annotations/{photo_id}", response_model=AnnotationResponse)
async def create_annotation(
    photo_id: str,
    body: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    annotation = await add_annotation(
        db=db,
        photo_id=photo.id,
        annotation_type=body.annotation_type,
        canvas_data=body.canvas_data,
        user_id=current_user.id,
        label=body.label,
        evidence_number=body.evidence_number,
    )
    return AnnotationResponse.model_validate(annotation)


@router.delete("/annotations/{annotation_id}")
async def delete_annotation_endpoint(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    await delete_annotation(db, annotation_id)
    return {"detail": "Annotation deleted"}


@router.post("/annotations/{photo_id}/export")
async def export_annotated_image(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photo = await get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    annotations = await get_annotations(db, photo.id)
    if not annotations:
        raise HTTPException(status_code=400, detail="No annotations to export")

    ann_dicts = [{"annotation_type": a.annotation_type, "canvas_data": a.canvas_data, "evidence_number": a.evidence_number} for a in annotations]
    annotated_path, file_hash = await render_annotations_on_image(photo.file_path, ann_dicts, photo.case_id)

    annotated_photo = ForensicPhoto(
        photo_id=str(uuid.uuid4()),
        case_id=photo.case_id,
        file_path=annotated_path,
        original_filename=f"annotated_{photo.original_filename}",
        file_size=os.path.getsize(annotated_path),
        file_hash_sha256=file_hash,
        mime_type="image/jpeg",
        width=photo.width,
        height=photo.height,
        category=photo.category,
        capture_source=photo.capture_source,
        is_original=False,
        parent_photo_id=photo.id,
        uploaded_by=current_user.id,
        chain_of_custody=[{
            "action": "annotations_exported",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "annotation_count": len(annotations),
        }],
    )
    db.add(annotated_photo)
    await db.commit()
    await db.refresh(annotated_photo)

    return {"photo_id": annotated_photo.photo_id, "file_hash": file_hash}


# ---------------------------------------------------------------------------
# Scene Coverage
# ---------------------------------------------------------------------------

@router.get("/coverage/{case_id}", response_model=CoverageStatusResponse)
async def get_coverage_status(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    zones = await get_coverage_zones(db, case_id)
    completed = sum(1 for z in zones if z.status == "green")
    overall = "green" if completed == len(zones) and zones else ("yellow" if completed > 0 else "red")
    return CoverageStatusResponse(
        case_id=case_id,
        total_zones=len(zones),
        completed_zones=completed,
        zones=[CoverageZoneResponse.model_validate(z) for z in zones],
        overall_status=overall if zones else "not_initialized",
    )


@router.post("/coverage/{case_id}/zones", response_model=list[CoverageZoneResponse])
async def init_coverage_zones(
    case_id: int,
    crime_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    existing = await get_coverage_zones(db, case_id)
    if existing:
        raise HTTPException(status_code=400, detail="Coverage zones already initialized for this case")
    zones = await initialize_coverage_zones(db, case_id, crime_type)
    return [CoverageZoneResponse.model_validate(z) for z in zones]


@router.patch("/coverage/{case_id}/zones/{zone_key}", response_model=CoverageZoneResponse)
async def update_zone(
    case_id: int,
    zone_key: str,
    actual_shots: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    zone = await update_coverage_zone(db, case_id, zone_key, actual_shots)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return CoverageZoneResponse.model_validate(zone)


# ---------------------------------------------------------------------------
# Gallery Endpoints
# ---------------------------------------------------------------------------

@router.get("/gallery/{case_id}/timeline")
async def gallery_timeline(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photos, _ = await get_photos_for_case(db, case_id, page=1, page_size=200)
    timeline = [
        {
            "photo_id": p.photo_id,
            "thumbnail_url": f"/api/forensic-photography/photos/{p.photo_id}/thumbnail",
            "timestamp": (p.capture_timestamp or p.created_at).isoformat(),
            "category": p.category,
            "quality_score": p.quality_score,
        }
        for p in sorted(photos, key=lambda x: x.capture_timestamp or x.created_at)
    ]
    return {"case_id": case_id, "timeline": timeline}


@router.get("/gallery/{case_id}/map")
async def gallery_map(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.CONSTABLE)),
):
    photos, _ = await get_photos_for_case(db, case_id, page=1, page_size=200)
    markers = [
        {
            "photo_id": p.photo_id,
            "thumbnail_url": f"/api/forensic-photography/photos/{p.photo_id}/thumbnail",
            "latitude": p.gps_latitude,
            "longitude": p.gps_longitude,
            "category": p.category,
            "filename": p.original_filename,
        }
        for p in photos
        if p.gps_latitude is not None and p.gps_longitude is not None
    ]
    return {"case_id": case_id, "markers": markers}
