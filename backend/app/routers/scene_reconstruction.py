import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scene_reconstruction import SceneReconstruction
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.scene_reconstruction_service import generate_reconstruction, export_html

router = APIRouter(prefix="/api/scene-reconstruction", tags=["Scene Reconstruction"])


@router.post("/generate/{case_id}")
async def start_generation(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start 3D scene reconstruction generation as background task."""
    # Reset stuck "generating" records older than 10 minutes
    stale_cutoff = datetime.utcnow() - timedelta(minutes=10)
    stale_result = await db.execute(
        select(SceneReconstruction).where(
            SceneReconstruction.case_id == case_id,
            SceneReconstruction.status == "generating",
            SceneReconstruction.updated_at < stale_cutoff,
        )
    )
    for stale_rec in stale_result.scalars().all():
        stale_rec.status = "failed"
        stale_rec.extra_metadata = {"error": "Generation timed out (stuck)"}
    await db.commit()

    existing = await db.execute(
        select(SceneReconstruction).where(
            SceneReconstruction.case_id == case_id,
            SceneReconstruction.status.in_(["pending", "generating"]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Generation already in progress for this case")

    reconstruction = SceneReconstruction(
        reconstruction_id=str(uuid.uuid4()),
        case_id=case_id,
        status="pending",
        generated_by=current_user.id,
    )
    db.add(reconstruction)
    await db.commit()
    await db.refresh(reconstruction)

    asyncio.create_task(generate_reconstruction(case_id, current_user.id))

    return {
        "reconstruction_id": reconstruction.reconstruction_id,
        "status": "pending",
        "message": "3D scene reconstruction generation started",
    }


@router.get("/status/{reconstruction_id}")
async def get_status(
    reconstruction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll generation status."""
    stmt = select(SceneReconstruction).where(
        SceneReconstruction.reconstruction_id == reconstruction_id
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Reconstruction not found")

    return {
        "reconstruction_id": rec.reconstruction_id,
        "status": rec.status,
        "metadata": rec.extra_metadata,
        "created_at": rec.created_at.isoformat(),
    }


@router.get("/case/{case_id}")
async def get_case_reconstruction(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest reconstruction for a case."""
    stmt = (
        select(SceneReconstruction)
        .where(SceneReconstruction.case_id == case_id)
        .order_by(SceneReconstruction.created_at.desc())
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        return {"reconstruction": None}

    return {
        "reconstruction": {
            "reconstruction_id": rec.reconstruction_id,
            "status": rec.status,
            "metadata": rec.extra_metadata,
            "export_html_path": rec.export_html_path,
            "export_video_path": rec.export_video_path,
            "created_at": rec.created_at.isoformat(),
            "updated_at": rec.updated_at.isoformat(),
        }
    }


@router.get("/{reconstruction_id}/data")
async def get_scene_data(
    reconstruction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full scene JSON for the 3D viewer."""
    stmt = select(SceneReconstruction).where(
        SceneReconstruction.reconstruction_id == reconstruction_id
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Reconstruction not found")
    if rec.status != "completed":
        raise HTTPException(400, "Reconstruction not yet completed")

    return {
        "reconstruction_id": rec.reconstruction_id,
        "scene_layout": rec.scene_layout,
        "objects": rec.objects_placed,
        "surfaces": rec.photo_textures,
        "events": rec.timeline_events,
        "metadata": rec.extra_metadata,
    }


@router.post("/{reconstruction_id}/export/html")
async def export_html_file(
    reconstruction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return path to HTML export."""
    try:
        html_path = await export_html(reconstruction_id, db)
        return {"path": html_path, "message": "HTML export ready"}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{reconstruction_id}/download/{format}")
async def download_export(
    reconstruction_id: str,
    format: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download exported file (html or mp4)."""
    stmt = select(SceneReconstruction).where(
        SceneReconstruction.reconstruction_id == reconstruction_id
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Reconstruction not found")

    if format == "html":
        if not rec.export_html_path or not os.path.exists(rec.export_html_path):
            raise HTTPException(400, "HTML export not available. Generate it first.")
        return FileResponse(
            rec.export_html_path,
            media_type="text/html",
            filename=f"crime_scene_{reconstruction_id}.html",
        )
    elif format == "mp4":
        if not rec.export_video_path or not os.path.exists(rec.export_video_path):
            raise HTTPException(400, "Video export not available. Generate it first.")
        return FileResponse(
            rec.export_video_path,
            media_type="video/mp4",
            filename=f"crime_scene_{reconstruction_id}.mp4",
        )
    else:
        raise HTTPException(400, "Unsupported format. Use 'html' or 'mp4'.")


@router.get("/list/{case_id}")
async def list_reconstructions(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reconstructions for a case."""
    stmt = (
        select(SceneReconstruction)
        .where(SceneReconstruction.case_id == case_id)
        .order_by(SceneReconstruction.created_at.desc())
    )
    result = await db.execute(stmt)
    recs = result.scalars().all()

    return {
        "reconstructions": [
            {
                "reconstruction_id": r.reconstruction_id,
                "status": r.status,
                "metadata": r.extra_metadata,
                "created_at": r.created_at.isoformat(),
            }
            for r in recs
        ]
    }


@router.delete("/{reconstruction_id}")
async def delete_reconstruction(
    reconstruction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a reconstruction."""
    stmt = select(SceneReconstruction).where(
        SceneReconstruction.reconstruction_id == reconstruction_id
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Reconstruction not found")

    if rec.export_html_path and os.path.exists(rec.export_html_path):
        os.remove(rec.export_html_path)
    if rec.export_video_path and os.path.exists(rec.export_video_path):
        os.remove(rec.export_video_path)

    await db.delete(rec)
    await db.commit()
    return {"message": "Reconstruction deleted"}
