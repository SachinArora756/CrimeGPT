import json
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agents.supervisor import get_llm, AgentState


LEGAL_RAG_SYSTEM_PROMPT = """You are a legal research assistant specializing in Indian criminal law.
You have access to the following legal frameworks:
- BNS (Bharatiya Nyaya Sanhita, 2023) - replaces IPC
- BNSS (Bharatiya Nagarik Suraksha Sanhita, 2023) - replaces CrPC
- BSA (Bharatiya Sakshya Adhiniyam, 2023) - replaces Indian Evidence Act

Based on the query and any retrieved legal provisions, provide:
1. Relevant sections and their content
2. Analysis of applicability to the case
3. A relevance confidence score

Respond with JSON containing:
- provisions: list of {section, title, content, act} objects
- analysis: text analysis of how these apply
- relevance_score: float 0-1

Always cite specific section numbers."""


async def query_legal_provisions(query: str, case_id: int | None = None) -> dict:
    llm = get_llm()

    retrieved_context = await retrieve_from_qdrant(query)

    context_text = ""
    if retrieved_context:
        context_text = "\n\nRetrieved legal provisions:\n" + "\n".join(
            [f"- {doc}" for doc in retrieved_context]
        )

    messages = [
        SystemMessage(content=LEGAL_RAG_SYSTEM_PROMPT),
        HumanMessage(content=f"Legal query: {query}{context_text}"),
    ]

    response = await llm.ainvoke(messages)
    content = response.content

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        result = json.loads(content.strip())
    except (json.JSONDecodeError, IndexError):
        result = {
            "provisions": [],
            "analysis": "Unable to parse structured response. Please refine query.",
            "relevance_score": 0.0,
        }

    if "provisions" not in result:
        result["provisions"] = []
    if "analysis" not in result:
        result["analysis"] = ""
    if "relevance_score" not in result:
        result["relevance_score"] = 0.5

    return result


async def retrieve_from_qdrant(query: str) -> list[str]:
    try:
        from qdrant_client import QdrantClient
        from app.config import settings
        from app.ai.rag.embeddings import get_embedding

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        query_vector = await get_embedding(query)

        results = client.search(
            collection_name="legal_provisions",
            query_vector=query_vector,
            limit=5,
        )
        return [hit.payload.get("text", "") for hit in results if hit.payload]
    except Exception:
        return []


def legal_rag_node(state: AgentState) -> AgentState:
    state["current_agent"] = "legal_rag"
    state["final_output"] = {"provisions": [], "analysis": "", "relevance_score": 0.0}
    return state
