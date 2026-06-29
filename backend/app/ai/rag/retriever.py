from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams

from app.config import settings
from app.ai.rag.embeddings import get_embedding
from app.ai.rag.ingestion import COLLECTION_NAME


async def search_legal_provisions(query: str, top_k: int = 5, act_filter: str | None = None) -> list[dict]:
    try:
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            return []

        query_vector = await get_embedding(query)

        filter_condition = None
        if act_filter:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            filter_condition = Filter(
                must=[FieldCondition(key="act", match=MatchValue(value=act_filter))]
            )

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filter_condition,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )

        provisions = []
        for hit in results:
            if hit.payload:
                provisions.append({
                    "text": hit.payload.get("text", ""),
                    "document": hit.payload.get("document", ""),
                    "act": hit.payload.get("act", ""),
                    "score": hit.score,
                    "chunk_index": hit.payload.get("chunk_index", 0),
                })

        return provisions
    except Exception:
        return []
