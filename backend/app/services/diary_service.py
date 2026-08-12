"""Automated case diary service.

Provides auto-logging of case events and AI-generated daily summaries.
"""

import asyncio
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import CaseDiary

logger = logging.getLogger(__name__)


async def auto_diary_entry(
    db: AsyncSession,
    case_id: int,
    entry_type: str,
    content: str,
    officer_id: int,
) -> CaseDiary:
    """Create an automatic diary entry for a case event."""
    diary = CaseDiary(
        case_id=case_id,
        entry_date=date.today(),
        content=content,
        entry_type=entry_type,
        officer_id=officer_id,
        is_auto=True,
    )
    db.add(diary)
    await db.commit()
    await db.refresh(diary)
    return diary


async def generate_daily_summary(
    db: AsyncSession,
    case_id: int,
    target_date: date,
    officer_id: int,
    case_fir_number: str = "",
) -> CaseDiary | None:
    """Generate an AI narrative summary of all diary entries for a given date."""
    result = await db.execute(
        select(CaseDiary)
        .where(CaseDiary.case_id == case_id, CaseDiary.entry_date == target_date)
        .order_by(CaseDiary.created_at.asc())
    )
    entries = result.scalars().all()

    if not entries:
        return None

    entries_text = "\n".join(
        f"- [{e.entry_type}] {e.content}" for e in entries
    )

    prompt = f"""You are a senior Indian police officer writing a formal Case Diary entry under Section 192 BNSS (Bharatiya Nagarik Suraksha Sanhita, 2023).

Compile the following investigation activities from {target_date.strftime('%d-%m-%Y')} into a single professional narrative case diary entry. Write in first person as the Investigating Officer.

Case: FIR No. {case_fir_number or 'N/A'}
Date: {target_date.strftime('%d-%m-%Y')}

Activities recorded today:
{entries_text}

Write a formal, concise diary entry covering all activities. Use proper legal language. Structure it as:
1. Brief opening (date, time commenced)
2. Summary of all activities in chronological order
3. Key observations/findings
4. Next steps planned

Keep it under 500 words. Do not add fictional details — only summarize what is listed above."""

    from app.ai.llm_provider import generate_text

    summary_text = await asyncio.to_thread(generate_text, prompt, 0.3, 1500)

    diary = CaseDiary(
        case_id=case_id,
        entry_date=target_date,
        content=summary_text,
        entry_type="supervisor_note",
        officer_id=officer_id,
        is_auto=True,
    )
    db.add(diary)
    await db.commit()
    await db.refresh(diary)
    return diary
