import os
import shutil
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.ingestion_log import IngestionLog, KBActivityLog
from app.services.auth_service import require_min_role
from app.ai.rag.ingestion import (
    get_qdrant_client, ingest_single_upload, compute_file_hash,
    _delete_file_chunks, COLLECTION_NAME, EMBEDDING_DIM, ALLOWED_EXTENSIONS,
    extract_text_from_file, ingest_legal_document, _detect_act_name,
)
from app.ai.rag.retriever import search_legal_provisions

router = APIRouter()

LEGAL_DOCS_DIR = "/app/data/legal_docs"


def _ensure_legal_docs_dir():
    os.makedirs(LEGAL_DOCS_DIR, exist_ok=True)


async def _log_activity(
    db: AsyncSession,
    user: User,
    action: str,
    document_name: str = None,
    collection_name: str = None,
    details: dict = None,
):
    log = KBActivityLog(
        user_id=user.id,
        username=user.username,
        action=action,
        document_name=document_name,
        collection_name=collection_name,
        details=details,
    )
    db.add(log)
    await db.commit()


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: Optional[str] = Form(None),
    collection: Optional[str] = Form(None),
    current_user: User = Depends(require_min_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    _ensure_legal_docs_dir()
    collection_name = collection or COLLECTION_NAME
    results = []

    for upload_file in files:
        ext = os.path.splitext(upload_file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": upload_file.filename,
                "status": "rejected",
                "message": f"Unsupported file type: {ext}",
            })
            continue

        dest_path = os.path.join(LEGAL_DOCS_DIR, upload_file.filename)
        version = 1
        base_name = os.path.splitext(upload_file.filename)[0]
        while os.path.exists(dest_path):
            version += 1
            dest_path = os.path.join(LEGAL_DOCS_DIR, f"{base_name}_v{version}{ext}")

        with open(dest_path, "wb") as f:
            content = await upload_file.read()
            f.write(content)

        result = await ingest_single_upload(
            file_path=dest_path,
            doc_name=base_name,
            category=category,
            collection_name=collection_name,
            user_id=current_user.id,
            original_filename=upload_file.filename,
        )

        results.append({"filename": upload_file.filename, **result})

        await _log_activity(
            db, current_user, "upload",
            document_name=upload_file.filename,
            collection_name=collection_name,
            details={"category": category, "result": result.get("status")},
        )

    return {"results": results}


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
    db: AsyncSession = Depends(get_db),
):
    query = select(IngestionLog)

    if search:
        query = query.where(
            IngestionLog.filename.ilike(f"%{search}%")
            | IngestionLog.original_filename.ilike(f"%{search}%")
        )
    if category:
        query = query.where(IngestionLog.category == category)
    if status:
        query = query.where(IngestionLog.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    query = query.order_by(desc(IngestionLog.ingested_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    docs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "original_filename": d.original_filename or d.filename,
                "file_hash": d.file_hash,
                "chunk_count": d.chunk_count,
                "file_size": d.file_size,
                "collection_name": d.collection_name,
                "category": d.category or "Uncategorized",
                "status": d.status or "active",
                "uploaded_by": d.uploaded_by,
                "version": d.version or 1,
                "mime_type": d.mime_type,
                "page_count": d.page_count,
                "embedding_model": d.embedding_model or "BAAI/bge-small-en-v1.5",
                "ingested_at": d.ingested_at.isoformat() if d.ingested_at else None,
            }
            for d in docs
        ],
    }


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: int,
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IngestionLog).where(IngestionLog.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "original_filename": doc.original_filename or doc.filename,
        "file_hash": doc.file_hash,
        "chunk_count": doc.chunk_count,
        "file_size": doc.file_size,
        "collection_name": doc.collection_name,
        "category": doc.category or "Uncategorized",
        "status": doc.status or "active",
        "uploaded_by": doc.uploaded_by,
        "version": doc.version or 1,
        "mime_type": doc.mime_type,
        "page_count": doc.page_count,
        "embedding_model": doc.embedding_model or "BAAI/bge-small-en-v1.5",
        "ingested_at": doc.ingested_at.isoformat() if doc.ingested_at else None,
    }


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(require_min_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IngestionLog).where(IngestionLog.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    client = get_qdrant_client()
    _delete_file_chunks(client, doc.filename)

    file_path = os.path.join(LEGAL_DOCS_DIR, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    await _log_activity(
        db, current_user, "delete",
        document_name=doc.filename,
        collection_name=doc.collection_name,
    )

    await db.delete(doc)
    await db.commit()

    return {"status": "deleted", "filename": doc.filename}


@router.post("/documents/bulk-delete")
async def bulk_delete_documents(
    ids: List[int],
    current_user: User = Depends(require_min_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IngestionLog).where(IngestionLog.id.in_(ids)))
    docs = list(result.scalars().all())

    client = get_qdrant_client()
    deleted = []

    for doc in docs:
        _delete_file_chunks(client, doc.filename)
        file_path = os.path.join(LEGAL_DOCS_DIR, doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        deleted.append(doc.filename)
        await db.delete(doc)

    await db.commit()

    await _log_activity(
        db, current_user, "bulk_delete",
        details={"deleted_files": deleted, "count": len(deleted)},
    )

    return {"status": "deleted", "count": len(deleted), "files": deleted}


@router.post("/documents/{doc_id}/reingest")
async def reingest_document(
    doc_id: int,
    current_user: User = Depends(require_min_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IngestionLog).where(IngestionLog.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(LEGAL_DOCS_DIR, doc.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Source file not found on disk")

    client = get_qdrant_client()
    _delete_file_chunks(client, doc.filename)

    act_name = doc.category or _detect_act_name(doc.filename)
    chunk_count = await ingest_legal_document(file_path, doc.filename, act_name)

    doc.chunk_count = chunk_count
    doc.ingested_at = datetime.utcnow()
    doc.status = "active"
    await db.commit()

    await _log_activity(
        db, current_user, "reingest",
        document_name=doc.filename,
        collection_name=doc.collection_name,
        details={"new_chunk_count": chunk_count},
    )

    return {"status": "reingested", "chunk_count": chunk_count}


@router.get("/documents/{doc_id}/preview")
async def preview_document(
    doc_id: int,
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IngestionLog).where(IngestionLog.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(LEGAL_DOCS_DIR, doc.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    ext = os.path.splitext(doc.filename)[1].lower()

    if ext in (".txt", ".md", ".csv", ".json", ".xml", ".rtf", ".html"):
        text = extract_text_from_file(file_path)
        return {"type": "text", "content": text[:50000], "filename": doc.filename}

    elif ext == ".pdf":
        def file_iter():
            with open(file_path, "rb") as f:
                yield from iter(lambda: f.read(65536), b"")

        return StreamingResponse(
            file_iter(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={doc.filename}"},
        )

    elif ext == ".docx":
        text = extract_text_from_file(file_path)
        return {"type": "text", "content": text[:50000], "filename": doc.filename}

    return {"type": "unsupported", "filename": doc.filename}


@router.get("/collections")
async def list_collections(
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
):
    client = get_qdrant_client()
    collections = client.get_collections().collections

    result = []
    for col in collections:
        try:
            info = client.get_collection(col.name)
            result.append({
                "name": col.name,
                "vectors_count": info.vectors_count or 0,
                "points_count": info.points_count or 0,
                "status": str(info.status),
                "config": {
                    "size": info.config.params.vectors.size if info.config.params.vectors else EMBEDDING_DIM,
                    "distance": str(info.config.params.vectors.distance) if info.config.params.vectors else "Cosine",
                },
            })
        except Exception:
            result.append({"name": col.name, "vectors_count": 0, "status": "unknown"})

    return {"collections": result}


@router.post("/collections")
async def create_collection(
    name: str = Form(...),
    dimension: int = Form(384),
    current_user: User = Depends(require_min_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    from qdrant_client.models import Distance, VectorParams

    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if name in existing:
        raise HTTPException(status_code=409, detail="Collection already exists")

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    await _log_activity(
        db, current_user, "create_collection",
        collection_name=name,
        details={"dimension": dimension},
    )

    return {"status": "created", "name": name, "dimension": dimension}


@router.delete("/collections/{name}")
async def delete_collection(
    name: str,
    confirm_name: str = Query(...),
    current_user: User = Depends(require_min_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if confirm_name != name:
        raise HTTPException(status_code=400, detail="Confirmation name does not match")

    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    client.delete_collection(name)

    await _log_activity(
        db, current_user, "delete_collection",
        collection_name=name,
    )

    return {"status": "deleted", "name": name}


@router.post("/test-query")
async def test_query(
    query: str = Form(...),
    top_k: int = Form(5),
    collection: Optional[str] = Form(None),
    category_filter: Optional[str] = Form(None),
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
):
    results = await search_legal_provisions(
        query=query,
        top_k=top_k,
        act_filter=category_filter,
    )

    return {
        "query": query,
        "top_k": top_k,
        "results": results,
    }


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
    db: AsyncSession = Depends(get_db),
):
    total_docs_result = await db.execute(
        select(func.count()).select_from(IngestionLog).where(IngestionLog.status != "deleted")
    )
    total_docs = total_docs_result.scalar() or 0

    chunks_result = await db.execute(
        select(func.sum(IngestionLog.chunk_count)).where(IngestionLog.status != "deleted")
    )
    total_chunks = chunks_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count()).select_from(IngestionLog).where(IngestionLog.status == "failed")
    )
    failed_count = failed_result.scalar() or 0

    latest_result = await db.execute(
        select(IngestionLog.ingested_at).order_by(desc(IngestionLog.ingested_at)).limit(1)
    )
    latest_upload = latest_result.scalar()

    client = get_qdrant_client()
    collections = client.get_collections().collections
    total_vectors = 0
    for col in collections:
        try:
            info = client.get_collection(col.name)
            total_vectors += info.vectors_count or 0
        except Exception:
            pass

    avg_chunk_size = 0
    if total_docs > 0 and total_chunks > 0:
        size_result = await db.execute(
            select(func.sum(IngestionLog.file_size)).where(IngestionLog.status != "deleted")
        )
        total_size = size_result.scalar() or 0
        avg_chunk_size = int(total_size / total_chunks) if total_chunks else 0

    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "total_vectors": total_vectors,
        "collections_count": len(collections),
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "latest_upload": latest_upload.isoformat() if latest_upload else None,
        "failed_count": failed_count,
        "avg_chunk_size": avg_chunk_size,
    }


@router.get("/activity-log")
async def get_activity_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    current_user: User = Depends(require_min_role(UserRole.COMMISSIONER)),
    db: AsyncSession = Depends(get_db),
):
    query = select(KBActivityLog)
    if action:
        query = query.where(KBActivityLog.action == action)

    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    query = query.order_by(desc(KBActivityLog.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "logs": [
            {
                "id": l.id,
                "user_id": l.user_id,
                "username": l.username,
                "action": l.action,
                "document_name": l.document_name,
                "collection_name": l.collection_name,
                "details": l.details,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }
