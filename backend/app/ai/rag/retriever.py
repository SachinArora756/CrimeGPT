from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams, Filter, FieldCondition, MatchValue

from app.config import settings
from app.ai.rag.embeddings import get_embedding, get_embeddings_batch
from app.ai.rag.ingestion import COLLECTION_NAME


def _get_client():
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def _collection_exists(client) -> bool:
    collections = [c.name for c in client.get_collections().collections]
    return COLLECTION_NAME in collections


def _build_filter(act_filter: str | None = None, category_filter: str | None = None, is_procedure: bool | None = None) -> Filter | None:
    conditions = []
    if act_filter:
        conditions.append(FieldCondition(key="act", match=MatchValue(value=act_filter)))
    if category_filter:
        conditions.append(FieldCondition(key="offense_category", match=MatchValue(value=category_filter)))
    if is_procedure is not None:
        conditions.append(FieldCondition(key="is_procedure", match=MatchValue(value=is_procedure)))

    if conditions:
        return Filter(must=conditions)
    return None


def _format_result(hit) -> dict:
    if not hit.payload:
        return None
    return {
        "text": hit.payload.get("text", ""),
        "document": hit.payload.get("document", ""),
        "act": hit.payload.get("act", ""),
        "section_number": hit.payload.get("section_number", ""),
        "chapter": hit.payload.get("chapter", ""),
        "heading": hit.payload.get("heading", ""),
        "offense_category": hit.payload.get("offense_category", ""),
        "punishment_range": hit.payload.get("punishment_range", ""),
        "keywords": hit.payload.get("keywords", []),
        "is_procedure": hit.payload.get("is_procedure", False),
        "score": hit.score,
        "chunk_index": hit.payload.get("chunk_index", 0),
    }


async def search_legal_provisions(
    query: str,
    top_k: int = 5,
    act_filter: str | None = None,
    category_filter: str | None = None,
    is_procedure: bool | None = None,
) -> list[dict]:
    try:
        client = _get_client()
        if not _collection_exists(client):
            return []

        query_vector = await get_embedding(query)
        filter_condition = _build_filter(act_filter, category_filter, is_procedure)

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filter_condition,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )

        provisions = []
        for hit in results:
            formatted = _format_result(hit)
            if formatted:
                provisions.append(formatted)

        return provisions
    except Exception:
        return []


async def multi_query_search(
    queries: list[str],
    top_k_per_query: int = 5,
    act_filter: str | None = None,
    category_filter: str | None = None,
    is_procedure: bool | None = None,
    deduplicate: bool = True,
) -> list[dict]:
    try:
        client = _get_client()
        if not _collection_exists(client):
            return []

        embeddings = await get_embeddings_batch(queries)
        filter_condition = _build_filter(act_filter, category_filter, is_procedure)

        all_results = []
        seen_texts = set()

        for query_vector in embeddings:
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=top_k_per_query,
                query_filter=filter_condition,
                search_params=SearchParams(hnsw_ef=128, exact=False),
            )

            for hit in results:
                formatted = _format_result(hit)
                if not formatted:
                    continue
                text_key = formatted["text"][:100]
                if deduplicate and text_key in seen_texts:
                    continue
                seen_texts.add(text_key)
                all_results.append(formatted)

        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results
    except Exception:
        return []


async def hybrid_search(
    query: str,
    keywords: list[str],
    top_k: int = 10,
    keyword_boost: float = 0.15,
    act_filter: str | None = None,
) -> list[dict]:
    try:
        client = _get_client()
        if not _collection_exists(client):
            return []

        query_vector = await get_embedding(query)
        filter_condition = _build_filter(act_filter)

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k * 2,
            query_filter=filter_condition,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )

        scored_results = []
        keywords_lower = [k.lower() for k in keywords]

        for hit in results:
            formatted = _format_result(hit)
            if not formatted:
                continue

            base_score = hit.score
            hit_keywords = [k.lower() for k in formatted.get("keywords", [])]
            hit_text_lower = formatted["text"].lower()

            keyword_matches = sum(
                1 for kw in keywords_lower
                if kw in hit_keywords or kw in hit_text_lower
            )

            if keywords_lower:
                boost = keyword_boost * (keyword_matches / len(keywords_lower))
                formatted["score"] = min(1.0, base_score + boost)

            scored_results.append(formatted)

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
    except Exception:
        return []
