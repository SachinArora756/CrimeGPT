from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class PhotoUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    photo_id: str
    original_filename: str
    file_size: int
    file_hash_sha256: str
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capture_timestamp: Optional[datetime] = None
    device_make: Optional[str] = None
    device_model: Optional[str] = None
    category: Optional[str] = None
    capture_source: str
    created_at: datetime


class PhotoDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    photo_id: str
    case_id: int
    original_filename: str
    file_size: int
    file_hash_sha256: str
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    exif_data: Optional[dict] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capture_timestamp: Optional[datetime] = None
    device_make: Optional[str] = None
    device_model: Optional[str] = None
    category: Optional[str] = None
    scene_zone: Optional[str] = None
    tags: Optional[list] = None
    description: Optional[str] = None
    quality_score: Optional[float] = None
    quality_assessment: Optional[dict] = None
    ai_detected_objects: Optional[dict] = None
    courtroom_readiness: Optional[float] = None
    ai_suggestions: Optional[list] = None
    capture_source: str
    is_original: bool
    parent_photo_id: Optional[int] = None
    chain_of_custody: Optional[list] = None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime


class PhotoUpdateRequest(BaseModel):
    category: Optional[str] = None
    scene_zone: Optional[str] = None
    tags: Optional[list] = None
    description: Optional[str] = None


class PhotoCaptureRequest(BaseModel):
    image_data: str
    filename: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_info: Optional[str] = None


class GuidanceRequest(BaseModel):
    crime_type: str
    scene_description: Optional[str] = None
    existing_photos_count: int = 0


class GuidanceResponse(BaseModel):
    crime_type: str
    minimum_shots: int
    shot_checklist: list[dict]
    mandatory_angles: list[str]
    distance_ranges: list[dict]
    brightness_tips: list[str]
    special_requirements: list[str]
    common_mistakes: list[str]
    indian_law_requirements: list[str]


class QualityAssessmentResponse(BaseModel):
    photo_id: str
    quality_score: float
    courtroom_readiness: float
    technical_metrics: dict
    ai_assessment: Optional[dict] = None
    suggestions: list[str]


class BatchAssessmentResponse(BaseModel):
    case_id: int
    total_photos: int
    assessed: int
    average_quality: float
    photos: list[QualityAssessmentResponse]


class EnhancementRequest(BaseModel):
    enhancement_type: str
    parameters: dict = {}


class EnhancementResponse(BaseModel):
    original_photo_id: str
    enhanced_photo_id: str
    enhancement_type: str
    parameters: dict


class AnnotationCreate(BaseModel):
    annotation_type: str
    canvas_data: dict
    label: Optional[str] = None
    evidence_number: Optional[int] = None


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    photo_id: int
    annotation_type: str
    canvas_data: dict
    label: Optional[str] = None
    evidence_number: Optional[int] = None
    created_by: int
    created_at: datetime


class CoverageZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: int
    zone_key: str
    zone_label: str
    required_shots: int
    actual_shots: int
    status: str


class CoverageStatusResponse(BaseModel):
    case_id: int
    total_zones: int
    completed_zones: int
    zones: list[CoverageZoneResponse]
    overall_status: str


class ObjectDetectionResponse(BaseModel):
    photo_id: str
    objects: list[dict]
    weapons: list[dict]
    vehicles: list[dict]
    persons: list[dict]
    forensic_items: list[dict]


class PhotoGalleryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    photo_id: str
    original_filename: str
    thumbnail_url: str
    category: Optional[str] = None
    quality_score: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capture_timestamp: Optional[datetime] = None
    capture_source: str
    created_at: datetime


class PhotoGalleryResponse(BaseModel):
    case_id: int
    total: int
    page: int
    page_size: int
    photos: list[PhotoGalleryItem]
