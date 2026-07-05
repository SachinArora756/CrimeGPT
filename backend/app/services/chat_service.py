from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatRole
from app.models.case import Case


async def get_chat_history(db: AsyncSession, case_id: int, limit: int = 50, offset: int = 0) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.case_id == case_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def process_chat(db: AsyncSession, case_id: int, user_id: int, message: str) -> ChatMessage:
    user_msg = ChatMessage(
        case_id=case_id,
        user_id=user_id,
        role=ChatRole.USER,
        content=message,
    )
    db.add(user_msg)
    await db.flush()

    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()

    context = _build_context(case)
    ai_response = await _call_ai(context, message)

    assistant_msg = ChatMessage(
        case_id=case_id,
        user_id=user_id,
        role=ChatRole.ASSISTANT,
        content=ai_response,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    return assistant_msg


def _build_context(case) -> str:
    if not case:
        return "No case context available."
    parts = [
        f"FIR Number: {case.fir_number}",
        f"Status: {case.status.value}",
        f"Complainant: {case.complainant_name}",
        f"Description: {case.description}",
    ]
    if case.offense_type:
        parts.append(f"Offense Type: {case.offense_type}")
    if case.incident_location:
        parts.append(f"Location: {case.incident_location}")
    if case.accused_name:
        parts.append(f"Accused: {case.accused_name}")
    if case.sections_applied:
        parts.append(f"Sections: {', '.join(str(s) for s in case.sections_applied)}")
    return "\n".join(parts)


async def _call_ai(context: str, user_message: str) -> str:
    legal_context = ""
    try:
        from app.ai.rag.retriever import search_legal_provisions
        results = await search_legal_provisions(user_message, top_k=3)
        if results:
            legal_context = "\n\nRELEVANT LEGAL PROVISIONS:\n"
            for r in results:
                legal_context += f"[{r['act']}] {r['text'][:300]}\n\n"
    except Exception:
        pass

    try:
        from app.ai.agents.supervisor import get_llm
        llm = get_llm()
        prompt = (
            "You are CrimeGPT, an AI assistant for police investigation. "
            "Answer based on the case context and legal provisions provided. "
            "Be precise, professional, and helpful. Cite specific sections when applicable.\n\n"
            f"CASE CONTEXT:\n{context}\n"
            f"{legal_context}\n"
            f"USER QUERY: {user_message}"
        )
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as e:
        return (
            f"I'm currently unable to process AI queries (service unavailable). "
            f"Please try again later or contact your system administrator.\n\n"
            f"Your question has been recorded for the case record."
        )
