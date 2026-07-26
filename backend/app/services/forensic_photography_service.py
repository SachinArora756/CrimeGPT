import os
import uuid
import hashlib
import base64
import asyncio
import aiofiles
from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image, ExifTags
from PIL.ExifTags import GPSTAGS

from app.config import settings
from app.models.forensic_photography import (
    ForensicPhoto, PhotoAnnotation, SceneCoverageZone, PhotoEnhancementHistory
)

PHOTO_UPLOAD_DIR = os.path.join(settings.upload_dir, "forensic_photos")
THUMBNAIL_DIR = os.path.join(settings.upload_dir, "forensic_photos", "thumbnails")
MAX_PHOTO_SIZE = 20 * 1024 * 1024  # 20MB

ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


def _ensure_dirs():
    os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def _is_allowed_image(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def _get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_MAP.get(ext, "image/jpeg")


def _extract_exif(img: Image.Image) -> dict:
    exif_data = {}
    try:
        raw_exif = img._getexif()
        if not raw_exif:
            return {}
        for tag_id, value in raw_exif.items():
            tag_name = ExifTags.Base(tag_id).name if tag_id in ExifTags.Base._value2member_map_ else str(tag_id)
            if isinstance(value, bytes):
                continue
            exif_data[tag_name] = str(value)
    except Exception:
        pass
    return exif_data


def _extract_gps(img: Image.Image) -> tuple[Optional[float], Optional[float]]:
    try:
        raw_exif = img._getexif()
        if not raw_exif:
            return None, None
        gps_info = {}
        for tag_id, value in raw_exif.items():
            if tag_id == ExifTags.Base.GPSInfo.value:
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                    gps_info[gps_tag] = gps_value

        if not gps_info:
            return None, None

        def dms_to_decimal(dms, ref):
            degrees = float(dms[0])
            minutes = float(dms[1])
            seconds = float(dms[2])
            decimal = degrees + minutes / 60.0 + seconds / 3600.0
            if ref in ("S", "W"):
                decimal = -decimal
            return decimal

        lat = None
        lng = None
        if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
            lat = dms_to_decimal(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
        if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
            lng = dms_to_decimal(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
        return lat, lng
    except Exception:
        return None, None


def _extract_capture_timestamp(exif_data: dict) -> Optional[datetime]:
    for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
        if key in exif_data:
            try:
                return datetime.strptime(exif_data[key], "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                continue
    return None


def _generate_thumbnail(file_path: str, photo_id: str) -> Optional[str]:
    try:
        _ensure_dirs()
        thumb_filename = f"{photo_id}_thumb.jpg"
        thumb_path = os.path.join(THUMBNAIL_DIR, thumb_filename)
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.thumbnail((300, 300))
            img.save(thumb_path, "JPEG", quality=75)
        return thumb_path
    except Exception:
        return None


async def upload_photo(
    db: AsyncSession,
    file: UploadFile,
    case_id: int,
    user_id: int,
    category: Optional[str] = None,
    scene_zone: Optional[str] = None,
    description: Optional[str] = None,
) -> ForensicPhoto:
    if not _is_allowed_image(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    _ensure_dirs()
    photo_uuid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower()
    case_photo_dir = os.path.join(PHOTO_UPLOAD_DIR, str(case_id))
    os.makedirs(case_photo_dir, exist_ok=True)

    save_filename = f"{photo_uuid}{ext}"
    file_path = os.path.join(case_photo_dir, save_filename)

    file_size = 0
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > MAX_PHOTO_SIZE:
                os.remove(file_path)
                raise ValueError("File too large (max 20MB)")
            sha256.update(chunk)
            await f.write(chunk)

    img = await asyncio.to_thread(Image.open, file_path)
    width, height = img.size
    exif_data = await asyncio.to_thread(_extract_exif, img)
    gps_lat, gps_lng = await asyncio.to_thread(_extract_gps, img)
    capture_ts = _extract_capture_timestamp(exif_data)
    device_make = exif_data.get("Make")
    device_model = exif_data.get("Model")
    img.close()

    thumbnail_path = await asyncio.to_thread(_generate_thumbnail, file_path, photo_uuid)

    photo = ForensicPhoto(
        photo_id=photo_uuid,
        case_id=case_id,
        file_path=file_path,
        thumbnail_path=thumbnail_path,
        original_filename=file.filename,
        file_size=file_size,
        file_hash_sha256=sha256.hexdigest(),
        mime_type=_get_mime_type(file.filename),
        width=width,
        height=height,
        exif_data=exif_data if exif_data else None,
        gps_latitude=gps_lat,
        gps_longitude=gps_lng,
        capture_timestamp=capture_ts,
        device_make=device_make,
        device_model=device_model,
        category=category,
        scene_zone=scene_zone,
        description=description,
        capture_source="upload",
        is_original=True,
        uploaded_by=user_id,
        chain_of_custody=[{
            "action": "uploaded",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "upload",
        }],
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


async def capture_photo(
    db: AsyncSession,
    image_data_b64: str,
    case_id: int,
    user_id: int,
    filename: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    device_info: Optional[str] = None,
    category: Optional[str] = None,
) -> ForensicPhoto:
    _ensure_dirs()
    photo_uuid = str(uuid.uuid4())

    if "," in image_data_b64:
        image_data_b64 = image_data_b64.split(",", 1)[1]
    image_bytes = base64.b64decode(image_data_b64)

    file_size = len(image_bytes)
    if file_size > MAX_PHOTO_SIZE:
        raise ValueError("Captured image too large (max 20MB)")

    sha256 = hashlib.sha256(image_bytes).hexdigest()

    case_photo_dir = os.path.join(PHOTO_UPLOAD_DIR, str(case_id))
    os.makedirs(case_photo_dir, exist_ok=True)

    save_filename = filename or f"capture_{photo_uuid}.jpg"
    ext = os.path.splitext(save_filename)[1].lower() or ".jpg"
    save_filename = f"{photo_uuid}{ext}"
    file_path = os.path.join(case_photo_dir, save_filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(image_bytes)

    img = Image.open(BytesIO(image_bytes))
    width, height = img.size
    img.close()

    thumbnail_path = await asyncio.to_thread(_generate_thumbnail, file_path, photo_uuid)

    photo = ForensicPhoto(
        photo_id=photo_uuid,
        case_id=case_id,
        file_path=file_path,
        thumbnail_path=thumbnail_path,
        original_filename=save_filename,
        file_size=file_size,
        file_hash_sha256=sha256,
        mime_type=_get_mime_type(save_filename),
        width=width,
        height=height,
        gps_latitude=latitude,
        gps_longitude=longitude,
        capture_timestamp=datetime.utcnow(),
        device_make=device_info,
        category=category,
        capture_source="camera",
        is_original=True,
        uploaded_by=user_id,
        chain_of_custody=[{
            "action": "captured",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "camera",
            "device": device_info,
        }],
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


async def get_photo_by_id(db: AsyncSession, photo_id: str) -> Optional[ForensicPhoto]:
    result = await db.execute(
        select(ForensicPhoto).where(ForensicPhoto.photo_id == photo_id)
    )
    return result.scalar_one_or_none()


async def get_photos_for_case(
    db: AsyncSession,
    case_id: int,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    scene_zone: Optional[str] = None,
) -> tuple[list[ForensicPhoto], int]:
    query = select(ForensicPhoto).where(ForensicPhoto.case_id == case_id)
    count_query = select(func.count(ForensicPhoto.id)).where(ForensicPhoto.case_id == case_id)

    if category:
        query = query.where(ForensicPhoto.category == category)
        count_query = count_query.where(ForensicPhoto.category == category)
    if scene_zone:
        query = query.where(ForensicPhoto.scene_zone == scene_zone)
        count_query = count_query.where(ForensicPhoto.scene_zone == scene_zone)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(ForensicPhoto.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    photos = list(result.scalars().all())
    return photos, total


async def update_photo(
    db: AsyncSession,
    photo: ForensicPhoto,
    category: Optional[str] = None,
    scene_zone: Optional[str] = None,
    tags: Optional[list] = None,
    description: Optional[str] = None,
) -> ForensicPhoto:
    if category is not None:
        photo.category = category
    if scene_zone is not None:
        photo.scene_zone = scene_zone
    if tags is not None:
        photo.tags = tags
    if description is not None:
        photo.description = description
    await db.commit()
    await db.refresh(photo)
    return photo


async def delete_photo(db: AsyncSession, photo: ForensicPhoto) -> None:
    if photo.file_path and os.path.exists(photo.file_path):
        os.remove(photo.file_path)
    if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
        os.remove(photo.thumbnail_path)
    await db.delete(photo)
    await db.commit()


async def add_annotation(
    db: AsyncSession,
    photo_id: int,
    annotation_type: str,
    canvas_data: dict,
    user_id: int,
    label: Optional[str] = None,
    evidence_number: Optional[int] = None,
) -> PhotoAnnotation:
    annotation = PhotoAnnotation(
        photo_id=photo_id,
        annotation_type=annotation_type,
        canvas_data=canvas_data,
        label=label,
        evidence_number=evidence_number,
        created_by=user_id,
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    return annotation


async def get_annotations(db: AsyncSession, photo_id: int) -> list[PhotoAnnotation]:
    result = await db.execute(
        select(PhotoAnnotation).where(PhotoAnnotation.photo_id == photo_id).order_by(PhotoAnnotation.created_at)
    )
    return list(result.scalars().all())


async def delete_annotation(db: AsyncSession, annotation_id: int) -> None:
    result = await db.execute(select(PhotoAnnotation).where(PhotoAnnotation.id == annotation_id))
    annotation = result.scalar_one_or_none()
    if annotation:
        await db.delete(annotation)
        await db.commit()


async def get_coverage_zones(db: AsyncSession, case_id: int) -> list[SceneCoverageZone]:
    result = await db.execute(
        select(SceneCoverageZone).where(SceneCoverageZone.case_id == case_id)
    )
    return list(result.scalars().all())


async def initialize_coverage_zones(db: AsyncSession, case_id: int, crime_type: str) -> list[SceneCoverageZone]:
    zone_templates = _get_zone_template(crime_type)
    zones = []
    for zt in zone_templates:
        zone = SceneCoverageZone(
            case_id=case_id,
            zone_key=zt["key"],
            zone_label=zt["label"],
            required_shots=zt["required"],
        )
        db.add(zone)
        zones.append(zone)
    await db.commit()
    for z in zones:
        await db.refresh(z)
    return zones


async def update_coverage_zone(
    db: AsyncSession,
    case_id: int,
    zone_key: str,
    actual_shots: Optional[int] = None,
) -> Optional[SceneCoverageZone]:
    result = await db.execute(
        select(SceneCoverageZone).where(
            and_(SceneCoverageZone.case_id == case_id, SceneCoverageZone.zone_key == zone_key)
        )
    )
    zone = result.scalar_one_or_none()
    if not zone:
        return None
    if actual_shots is not None:
        zone.actual_shots = actual_shots
        if actual_shots >= zone.required_shots:
            zone.status = "green"
        elif actual_shots > 0:
            zone.status = "yellow"
        else:
            zone.status = "red"
    await db.commit()
    await db.refresh(zone)
    return zone


def _get_zone_template(crime_type: str) -> list[dict]:
    templates = {
        "murder": [
            {"key": "overall_scene", "label": "Overall Scene (Wide Shots)", "required": 4},
            {"key": "body_location", "label": "Body/Victim Location", "required": 6},
            {"key": "entry_exit_points", "label": "Entry & Exit Points", "required": 4},
            {"key": "weapon_location", "label": "Weapon/Instrument Location", "required": 3},
            {"key": "blood_stains", "label": "Blood Stains & Spatter", "required": 5},
            {"key": "surroundings", "label": "Surrounding Area & Context", "required": 3},
            {"key": "evidence_markers", "label": "Evidence Markers Close-up", "required": 4},
            {"key": "measurement_scale", "label": "Measurement & Scale Photos", "required": 3},
        ],
        "robbery": [
            {"key": "overall_scene", "label": "Overall Scene (Wide Shots)", "required": 4},
            {"key": "point_of_entry", "label": "Point of Entry/Forced Entry", "required": 4},
            {"key": "valuables_area", "label": "Area Where Valuables Kept", "required": 3},
            {"key": "tool_marks", "label": "Tool Marks & Damage", "required": 3},
            {"key": "footprints", "label": "Footprints/Shoe Marks", "required": 3},
            {"key": "cctv_locations", "label": "CCTV Camera Locations", "required": 2},
            {"key": "escape_route", "label": "Escape Route", "required": 3},
        ],
        "accident": [
            {"key": "overall_scene", "label": "Overall Road/Scene", "required": 4},
            {"key": "vehicle_damage", "label": "Vehicle Damage (All Angles)", "required": 6},
            {"key": "skid_marks", "label": "Skid Marks & Road Marks", "required": 3},
            {"key": "traffic_signs", "label": "Traffic Signs & Signals", "required": 3},
            {"key": "victim_position", "label": "Victim/Injury Position", "required": 3},
            {"key": "debris_field", "label": "Debris & Glass Fragments", "required": 3},
            {"key": "road_conditions", "label": "Road Conditions & Visibility", "required": 2},
        ],
        "theft": [
            {"key": "overall_scene", "label": "Overall Scene", "required": 3},
            {"key": "point_of_entry", "label": "Point of Entry", "required": 4},
            {"key": "disturbed_area", "label": "Disturbed/Ransacked Area", "required": 4},
            {"key": "fingerprints", "label": "Potential Fingerprint Surfaces", "required": 3},
            {"key": "tool_marks", "label": "Tool Marks on Locks/Doors", "required": 3},
            {"key": "escape_route", "label": "Escape Route", "required": 2},
        ],
        "sexual_assault": [
            {"key": "overall_scene", "label": "Overall Scene", "required": 3},
            {"key": "location_detail", "label": "Location Details", "required": 4},
            {"key": "evidence_items", "label": "Evidence Items (Clothing, etc.)", "required": 4},
            {"key": "entry_exit", "label": "Entry & Exit Points", "required": 3},
            {"key": "surrounding_area", "label": "Surrounding Area", "required": 3},
        ],
        "arson": [
            {"key": "overall_scene", "label": "Overall Fire Scene", "required": 4},
            {"key": "point_of_origin", "label": "Point of Origin", "required": 5},
            {"key": "burn_patterns", "label": "Burn Patterns & Char", "required": 4},
            {"key": "accelerant_traces", "label": "Accelerant Traces", "required": 3},
            {"key": "structural_damage", "label": "Structural Damage", "required": 3},
            {"key": "surrounding_area", "label": "Surrounding Unburned Area", "required": 3},
        ],
        "drug_seizure": [
            {"key": "overall_scene", "label": "Overall Location", "required": 3},
            {"key": "contraband", "label": "Contraband/Substances", "required": 5},
            {"key": "packaging", "label": "Packaging & Containers", "required": 3},
            {"key": "weighing", "label": "Weighing & Measurement", "required": 3},
            {"key": "hiding_spots", "label": "Hiding Spots/Concealment", "required": 3},
            {"key": "paraphernalia", "label": "Drug Paraphernalia", "required": 2},
        ],
    }
    default_template = [
        {"key": "overall_scene", "label": "Overall Scene (Wide Shots)", "required": 4},
        {"key": "primary_evidence", "label": "Primary Evidence Area", "required": 4},
        {"key": "entry_exit_points", "label": "Entry & Exit Points", "required": 3},
        {"key": "evidence_closeup", "label": "Evidence Close-ups", "required": 4},
        {"key": "surroundings", "label": "Surrounding Area", "required": 3},
        {"key": "measurement_scale", "label": "Measurement & Scale Photos", "required": 2},
    ]
    return templates.get(crime_type.lower().replace(" ", "_"), default_template)
