import os
import hashlib
import uuid
from typing import List
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sqlalchemy import select

from app.config import settings
from app.ai.rag.embeddings import get_embeddings_batch
from app.ai.rag.chunking import chunk_text_section_aware
from app.ai.rag.metadata_extractor import extract_metadata


COLLECTION_NAME = "legal_provisions"
EMBEDDING_DIM = 384

ACT_MAPPING = {
    "bns": "Bharatiya Nyaya Sanhita (BNS) 2023",
    "bnss": "Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023",
    "bsa": "Bharatiya Sakshya Adhiniyam (BSA) 2023",
    "constitution": "Constitution of India",
    "police_manual": "Police Investigation Manual",
    "investigation": "Investigation Procedures",
}


def get_qdrant_client():
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def compute_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
            doc.close()
            if text_parts:
                return "\n\n".join(text_parts)
        except Exception:
            pass
        try:
            import pytesseract
            from pdf2image import convert_from_path
            pages = convert_from_path(file_path)
            text_parts = []
            for page in pages:
                text = pytesseract.image_to_string(page, lang="eng")
                text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception:
            return ""

    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    elif ext == ".csv":
        try:
            import csv
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = [", ".join(row) for row in reader]
            return "\n".join(rows)
        except Exception:
            return ""

    elif ext == ".html":
        try:
            import re
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception:
            return ""

    elif ext == ".json":
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            return ""

    elif ext == ".xml":
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            return " ".join(tree.getroot().itertext())
        except Exception:
            return ""

    elif ext == ".rtf":
        try:
            import re
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                rtf = f.read()
            text = re.sub(r"\\[a-z]+\d*\s?", "", rtf)
            text = re.sub(r"[{}]", "", text)
            return text.strip()
        except Exception:
            return ""

    return ""


def get_pdf_page_count(file_path: str) -> int:
    try:
        import fitz
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0


def _detect_act_name(filename: str) -> str:
    filename_lower = filename.lower()
    for key, name in ACT_MAPPING.items():
        if key in filename_lower:
            return name
    return "Unknown Act"


async def ingest_legal_document(file_path: str, doc_name: str, act_name: str) -> int:
    text = extract_text_from_file(file_path)
    if not text:
        return 0

    chunks = chunk_text_section_aware(text)
    if not chunks:
        return 0

    chunk_texts = [c.text for c in chunks]
    embeddings = await get_embeddings_batch(chunk_texts)

    client = get_qdrant_client()

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

    source_file = os.path.basename(file_path)
    _delete_file_chunks(client, source_file)

    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        metadata = extract_metadata(chunk, act_name, source_file)
        metadata["document"] = doc_name
        metadata["chunk_index"] = i

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=metadata,
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i: i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    return len(chunks)


def _delete_file_chunks(client: QdrantClient, source_file: str):
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="source_file", match=MatchValue(value=source_file))]
            ),
        )
    except Exception:
        pass


async def ingest_all_legal_documents(force: bool = False):
    possible_paths = [
        "/app/data/legal_docs",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "legal_docs"),
        os.path.join(settings.upload_dir, "..", "legal_docs"),
    ]
    legal_dir = None
    for p in possible_paths:
        if os.path.exists(p) and os.listdir(p):
            legal_dir = p
            break
    if not legal_dir:
        return {"status": "no legal_docs directory found", "ingested": 0, "searched": possible_paths}

    from app.database import async_session
    from app.models.ingestion_log import IngestionLog

    total_chunks = 0
    files_processed = []
    files_skipped = []

    async with async_session() as db:
        for filename in sorted(os.listdir(legal_dir)):
            file_path = os.path.join(legal_dir, filename)
            if not os.path.isfile(file_path):
                continue

            file_hash = compute_file_hash(file_path)
            file_size = os.path.getsize(file_path)

            if not force:
                result = await db.execute(
                    select(IngestionLog).where(IngestionLog.filename == filename)
                )
                existing = result.scalar_one_or_none()
                if existing and existing.file_hash == file_hash:
                    files_skipped.append({"file": filename, "reason": "unchanged"})
                    total_chunks += existing.chunk_count
                    continue

            doc_name = os.path.splitext(filename)[0]
            act_name = _detect_act_name(filename)

            chunks = await ingest_legal_document(file_path, doc_name, act_name)
            total_chunks += chunks
            files_processed.append({"file": filename, "chunks": chunks, "act": act_name})

            result = await db.execute(
                select(IngestionLog).where(IngestionLog.filename == filename)
            )
            log_entry = result.scalar_one_or_none()
            if log_entry:
                log_entry.file_hash = file_hash
                log_entry.chunk_count = chunks
                log_entry.file_size = file_size
                log_entry.ingested_at = datetime.utcnow()
            else:
                log_entry = IngestionLog(
                    filename=filename,
                    file_hash=file_hash,
                    chunk_count=chunks,
                    file_size=file_size,
                    collection_name=COLLECTION_NAME,
                )
                db.add(log_entry)

        await db.commit()

    return {
        "status": "complete",
        "total_chunks": total_chunks,
        "files_processed": files_processed,
        "files_skipped": files_skipped,
    }


async def get_ingestion_status():
    from app.database import async_session
    from app.models.ingestion_log import IngestionLog

    async with async_session() as db:
        result = await db.execute(select(IngestionLog))
        logs = list(result.scalars().all())

    return {
        "total_files": len(logs),
        "total_chunks": sum(l.chunk_count for l in logs),
        "files": [
            {
                "filename": l.filename,
                "file_hash": l.file_hash[:12] + "...",
                "chunk_count": l.chunk_count,
                "file_size": l.file_size,
                "ingested_at": l.ingested_at.isoformat() if l.ingested_at else None,
            }
            for l in logs
        ],
    }


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".rtf", ".html", ".json", ".xml"}


async def ingest_single_upload(
    file_path: str,
    doc_name: str,
    category: str | None = None,
    collection_name: str = COLLECTION_NAME,
    user_id: int | None = None,
    original_filename: str | None = None,
) -> dict:
    from app.database import async_session
    from app.models.ingestion_log import IngestionLog

    file_hash = compute_file_hash(file_path)
    file_size = os.path.getsize(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    async with async_session() as db:
        result = await db.execute(
            select(IngestionLog).where(IngestionLog.file_hash == file_hash)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return {
                "status": "duplicate",
                "message": f"File identical to '{existing.filename}' already ingested",
                "existing_id": existing.id,
            }

    text = extract_text_from_file(file_path)
    if not text:
        return {"status": "failed", "message": "Could not extract text from file"}

    chunks = chunk_text_section_aware(text)
    if not chunks:
        return {"status": "failed", "message": "No chunks produced from text"}

    chunk_texts = [c.text for c in chunks]
    embeddings = await get_embeddings_batch(chunk_texts)

    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

    source_file = os.path.basename(file_path)
    _delete_file_chunks(client, source_file)

    act_name = _detect_act_name(source_file)
    if category:
        act_name = category

    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        metadata = extract_metadata(chunk, act_name, source_file)
        metadata["document"] = doc_name
        metadata["chunk_index"] = i
        metadata["category"] = category or "Uncategorized"

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=metadata,
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i: i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)

    page_count = get_pdf_page_count(file_path) if ext == ".pdf" else None

    import mimetypes
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    async with async_session() as db:
        filename = os.path.basename(file_path)
        result = await db.execute(
            select(IngestionLog).where(IngestionLog.filename == filename)
        )
        log_entry = result.scalar_one_or_none()

        if log_entry:
            log_entry.file_hash = file_hash
            log_entry.chunk_count = len(chunks)
            log_entry.file_size = file_size
            log_entry.ingested_at = datetime.utcnow()
            log_entry.category = category
            log_entry.uploaded_by = user_id
            log_entry.status = "active"
            log_entry.mime_type = mime_type
            log_entry.page_count = page_count
            log_entry.collection_name = collection_name
            log_entry.original_filename = original_filename or filename
        else:
            log_entry = IngestionLog(
                filename=filename,
                file_hash=file_hash,
                chunk_count=len(chunks),
                file_size=file_size,
                collection_name=collection_name,
                category=category,
                uploaded_by=user_id,
                original_filename=original_filename or filename,
                status="active",
                mime_type=mime_type,
                page_count=page_count,
            )
            db.add(log_entry)

        await db.commit()
        await db.refresh(log_entry)

    return {
        "status": "success",
        "document_id": log_entry.id,
        "chunk_count": len(chunks),
        "file_size": file_size,
    }
