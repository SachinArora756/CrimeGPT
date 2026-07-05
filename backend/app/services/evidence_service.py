import os
import uuid
import hashlib
import aiofiles
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.evidence import Evidence


ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    "document": [".pdf", ".doc", ".docx", ".txt"],
    "video": [".mp4", ".avi", ".mov", ".mkv"],
    "audio": [".mp3", ".wav", ".m4a", ".ogg"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return "other"


def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    all_extensions = [e for exts in ALLOWED_EXTENSIONS.values() for e in exts]
    return ext in all_extensions


async def save_upload_file(file: UploadFile, case_id: int) -> tuple[str, int]:
    case_dir = os.path.join(settings.upload_dir, str(case_id))
    os.makedirs(case_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(case_dir, unique_filename)

    file_size = 0
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                os.remove(file_path)
                raise ValueError("File too large (max 50MB)")
            sha256.update(chunk)
            await f.write(chunk)

    return file_path, file_size, sha256.hexdigest()


async def create_evidence(
    db: AsyncSession, case_id: int, file_path: str, original_filename: str,
    file_type: str, file_size: int, user_id: int, description: str | None = None,
    file_hash: str | None = None,
) -> Evidence:
    evidence = Evidence(
        case_id=case_id,
        file_path=file_path,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        uploaded_by=user_id,
        description=description,
        file_hash=file_hash,
        chain_of_custody=[{
            "action": "uploaded",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


async def get_evidence_for_case(db: AsyncSession, case_id: int):
    result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at.desc())
    )
    evidence_list = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(Evidence.case_id == case_id)
    )
    total = count_result.scalar()

    return evidence_list, total


async def get_evidence_by_id(db: AsyncSession, evidence_id: int) -> Evidence | None:
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    return result.scalar_one_or_none()


async def verify_evidence_integrity(evidence: Evidence) -> dict:
    """Re-compute SHA-256 of the file on disk and compare to stored hash."""
    if not evidence.file_hash:
        return {
            "evidence_id": evidence.id,
            "status": "no_hash",
            "message": "No original hash stored for this evidence",
            "tampered": None,
        }

    if not os.path.exists(evidence.file_path):
        return {
            "evidence_id": evidence.id,
            "status": "file_missing",
            "message": "Evidence file not found on disk",
            "tampered": None,
            "original_hash": evidence.file_hash,
        }

    sha256 = hashlib.sha256()
    async with aiofiles.open(evidence.file_path, "rb") as f:
        while chunk := await f.read(1024 * 1024):
            sha256.update(chunk)

    current_hash = sha256.hexdigest()
    tampered = current_hash != evidence.file_hash

    return {
        "evidence_id": evidence.id,
        "original_filename": evidence.original_filename,
        "status": "tampered" if tampered else "intact",
        "tampered": tampered,
        "original_hash": evidence.file_hash,
        "current_hash": current_hash,
        "message": "WARNING: Evidence file has been modified!" if tampered else "Evidence integrity verified - file is untampered",
    }
