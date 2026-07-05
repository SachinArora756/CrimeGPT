from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import get_current_user, require_min_role
from app.ai.rag.retriever import search_legal_provisions
from app.ai.rag.ingestion import ingest_all_legal_documents, get_qdrant_client, COLLECTION_NAME, get_ingestion_status

router = APIRouter()


@router.get("/search")
async def search_legal(
    query: str = Query(..., min_length=3),
    top_k: int = Query(5, ge=1, le=20),
    act: str | None = None,
    category: str | None = None,
    current_user: User = Depends(get_current_user),
):
    results = await search_legal_provisions(
        query, top_k=top_k, act_filter=act, category_filter=category
    )
    return {
        "query": query,
        "results": results,
        "total": len(results),
    }


@router.post("/ingest")
async def ingest_legal_docs(
    force: bool = Query(False),
    admin: User = Depends(require_min_role(UserRole.COMMISSIONER)),
):
    result = await ingest_all_legal_documents(force=force)
    return result


@router.get("/status")
async def rag_status(
    current_user: User = Depends(require_min_role(UserRole.SHO)),
):
    try:
        client = get_qdrant_client()
        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            return {
                "status": "not_initialized",
                "collection": COLLECTION_NAME,
                "total_chunks": 0,
            }
        count = client.count(collection_name=COLLECTION_NAME)
        return {
            "status": "ready",
            "collection": COLLECTION_NAME,
            "total_chunks": count.count,
        }
    except Exception:
        return {
            "status": "error",
            "error": "Unable to connect to vector database",
        }


@router.get("/ingestion-status")
async def ingestion_status_detail(
    admin: User = Depends(require_min_role(UserRole.COMMISSIONER)),
):
    return await get_ingestion_status()
