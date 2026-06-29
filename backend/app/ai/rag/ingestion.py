import os
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import settings
from app.ai.rag.embeddings import get_embeddings_batch


COLLECTION_NAME = "legal_provisions"
EMBEDDING_DIM = 384
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_qdrant_client():
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


async def ingest_legal_document(file_path: str, doc_name: str, act_name: str):
    text = extract_text_from_file(file_path)
    if not text:
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = await get_embeddings_batch(chunks)

    client = get_qdrant_client()

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

    existing = client.count(collection_name=COLLECTION_NAME)
    start_id = existing.count

    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=start_id + i,
                vector=embedding,
                payload={
                    "text": chunk,
                    "document": doc_name,
                    "act": act_name,
                    "chunk_index": i,
                    "source_file": os.path.basename(file_path),
                },
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    return len(chunks)


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
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

    return ""


async def ingest_all_legal_documents():
    legal_dir = os.path.join(settings.upload_dir, "..", "legal_docs")
    if not os.path.exists(legal_dir):
        return {"status": "no legal_docs directory found", "ingested": 0}

    total_chunks = 0
    files_processed = []

    act_mapping = {
        "bns": "Bharatiya Nyaya Sanhita (BNS)",
        "bnss": "Bharatiya Nagarik Suraksha Sanhita (BNSS)",
        "bsa": "Bharatiya Sakshya Adhiniyam (BSA)",
    }

    for filename in os.listdir(legal_dir):
        file_path = os.path.join(legal_dir, filename)
        if not os.path.isfile(file_path):
            continue

        doc_name = os.path.splitext(filename)[0]
        act_name = "Unknown Act"
        for key, name in act_mapping.items():
            if key in filename.lower():
                act_name = name
                break

        chunks = await ingest_legal_document(file_path, doc_name, act_name)
        total_chunks += chunks
        files_processed.append({"file": filename, "chunks": chunks})

    return {
        "status": "complete",
        "total_chunks": total_chunks,
        "files": files_processed,
    }
