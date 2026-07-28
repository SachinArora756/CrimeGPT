import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.forensic_photography import ForensicPhoto, PhotoEnhancementHistory
from app.services.photo_ai_service import _compute_technical_metrics
from app.services.photo_enhancement_service import enhance_photo
from app.services.forensic_photography_service import PHOTO_UPLOAD_DIR

logger = logging.getLogger(__name__)

BLUR_THRESHOLD = 30
UNDEREXPOSURE_THRESHOLD = 50
OVEREXPOSURE_THRESHOLD = 200
CONTRAST_THRESHOLD = 30


async def run_auto_enhance(photo_id: int, file_path: str, case_id: int, user_id: int):
    """Background task: assess quality and auto-enhance if issues found."""
    try:
        async with async_session() as db:
            stmt = select(ForensicPhoto).where(ForensicPhoto.id == photo_id)
            result = await db.execute(stmt)
            photo = result.scalar_one_or_none()
            if not photo:
                logger.warning(f"Auto-enhance: photo {photo_id} not found")
                return

            photo.auto_enhance_status = "processing"
            await db.commit()

            metrics = await asyncio.to_thread(_compute_technical_metrics, file_path)

            issues = []
            enhancements_to_apply = []

            blur_score = metrics.get("blur_score", 100)
            if blur_score < BLUR_THRESHOLD:
                issues.append({"type": "blur", "severity": "high" if blur_score < 15 else "medium", "score": blur_score})
                enhancements_to_apply.append(("deblur", {"amount": 2.0}))
                enhancements_to_apply.append(("sharpness", {"value": 2.0}))

            exposure = metrics.get("exposure_issue", "normal")
            if exposure == "underexposed":
                issues.append({"type": "underexposure", "severity": "high", "brightness": metrics.get("mean_brightness")})
                enhancements_to_apply.append(("low_light", {}))
            elif exposure == "overexposed":
                issues.append({"type": "overexposure", "severity": "medium", "brightness": metrics.get("mean_brightness")})
                enhancements_to_apply.append(("auto_levels", {}))

            contrast_score = metrics.get("contrast_score", 100)
            if contrast_score < CONTRAST_THRESHOLD:
                issues.append({"type": "low_contrast", "severity": "medium", "score": contrast_score})
                enhancements_to_apply.append(("contrast", {"value": 1.5}))

            quality_score = metrics.get("estimated_quality", 50)
            photo.quality_score = quality_score
            photo.quality_assessment = {
                "technical_metrics": metrics,
                "issues": issues,
                "auto_assessed_at": datetime.utcnow().isoformat(),
            }

            if not enhancements_to_apply:
                photo.auto_enhance_status = "no_issues"
                photo.auto_enhanced = False
                await db.commit()
                logger.info(f"Auto-enhance: photo {photo_id} has no issues (score={quality_score})")
                return

            current_path = file_path
            applied = []

            for enhancement_type, params in enhancements_to_apply:
                try:
                    enhanced_path, thumb_path, file_hash = await enhance_photo(
                        file_path=current_path,
                        enhancement_type=enhancement_type,
                        parameters=params,
                        case_id=case_id,
                    )
                    current_path = enhanced_path
                    applied.append({"type": enhancement_type, "params": params})
                except Exception as e:
                    logger.warning(f"Auto-enhance step {enhancement_type} failed: {e}")
                    continue

            if not applied:
                photo.auto_enhance_status = "no_issues"
                await db.commit()
                return

            file_size = os.path.getsize(current_path)
            from PIL import Image
            img = Image.open(current_path)
            width, height = img.size
            img.close()

            import hashlib
            with open(current_path, "rb") as f:
                final_hash = hashlib.sha256(f.read()).hexdigest()

            enhanced_photo = ForensicPhoto(
                photo_id=str(__import__("uuid").uuid4()),
                case_id=case_id,
                file_path=current_path,
                thumbnail_path=thumb_path,
                original_filename=f"auto_enhanced_{photo.original_filename}",
                file_size=file_size,
                file_hash_sha256=final_hash,
                mime_type="image/jpeg",
                width=width,
                height=height,
                category=photo.category,
                scene_zone=photo.scene_zone,
                capture_source=photo.capture_source,
                is_original=False,
                parent_photo_id=photo.id,
                auto_enhanced=True,
                auto_enhance_status="completed",
                uploaded_by=user_id,
                chain_of_custody=[{
                    "action": "auto_enhanced",
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "details": f"Auto-enhancement applied: {', '.join(a['type'] for a in applied)}",
                }],
            )
            db.add(enhanced_photo)
            await db.flush()

            history = PhotoEnhancementHistory(
                original_photo_id=photo.id,
                enhanced_photo_id=enhanced_photo.id,
                enhancement_type="auto_enhance",
                parameters={
                    "enhancements_applied": applied,
                    "issues_detected": issues,
                    "original_quality_score": quality_score,
                },
                performed_by=user_id,
            )
            db.add(history)

            photo.auto_enhanced = True
            photo.auto_enhance_status = "completed"

            await db.commit()
            logger.info(
                f"Auto-enhance: photo {photo_id} enhanced successfully "
                f"(issues={len(issues)}, enhancements={len(applied)}, new_id={enhanced_photo.photo_id})"
            )

    except Exception as e:
        logger.error(f"Auto-enhance failed for photo {photo_id}: {e}")
        try:
            async with async_session() as db:
                stmt = select(ForensicPhoto).where(ForensicPhoto.id == photo_id)
                result = await db.execute(stmt)
                photo = result.scalar_one_or_none()
                if photo:
                    photo.auto_enhance_status = "no_issues"
                    await db.commit()
        except Exception:
            pass
