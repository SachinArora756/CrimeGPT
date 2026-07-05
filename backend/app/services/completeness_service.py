from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.document import Document, CaseDiary


CHECKLIST = [
    {"key": "complainant_info", "label": "Complainant Information", "weight": 10},
    {"key": "accused_info", "label": "Accused Person Details", "weight": 10},
    {"key": "incident_details", "label": "Incident Date & Location", "weight": 10},
    {"key": "offense_type", "label": "Offense Classification", "weight": 5},
    {"key": "sections_applied", "label": "Legal Sections Applied", "weight": 10},
    {"key": "evidence_uploaded", "label": "Evidence Collected", "weight": 15},
    {"key": "witness_statements", "label": "Witness Statements", "weight": 10},
    {"key": "fir_generated", "label": "FIR Document Generated", "weight": 10},
    {"key": "investigation_team", "label": "Investigation Team Assigned", "weight": 5},
    {"key": "case_diary", "label": "Case Diary Entries", "weight": 10},
    {"key": "victims_recorded", "label": "Victim Details Recorded", "weight": 5},
]


async def calculate_completeness(db: AsyncSession, case_id: int) -> dict:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        return {"percentage": 0, "items": []}

    items = []
    total_weight = sum(c["weight"] for c in CHECKLIST)
    earned = 0

    checks = {
        "complainant_info": bool(case.complainant_name and case.complainant_contact),
        "accused_info": bool(case.accused_name or (case.accused_persons and len(case.accused_persons) > 0)),
        "incident_details": bool(case.incident_date and case.incident_location),
        "offense_type": bool(case.offense_type),
        "sections_applied": bool(case.sections_applied and len(case.sections_applied) > 0),
        "investigation_team": bool(case.investigation_team and len(case.investigation_team) > 0),
        "victims_recorded": bool(case.victims and len(case.victims) > 0),
    }

    ev_count = await db.execute(
        select(func.count()).select_from(Evidence).where(Evidence.case_id == case_id)
    )
    checks["evidence_uploaded"] = (ev_count.scalar() or 0) > 0

    witness_check = bool(case.witnesses and len(case.witnesses) > 0)
    checks["witness_statements"] = witness_check

    doc_count = await db.execute(
        select(func.count()).select_from(Document)
        .where(Document.case_id == case_id, Document.doc_type == "fir")
    )
    checks["fir_generated"] = (doc_count.scalar() or 0) > 0

    diary_count = await db.execute(
        select(func.count()).select_from(CaseDiary).where(CaseDiary.case_id == case_id)
    )
    checks["case_diary"] = (diary_count.scalar() or 0) > 0

    for c in CHECKLIST:
        completed = checks.get(c["key"], False)
        items.append({
            "key": c["key"],
            "label": c["label"],
            "completed": completed,
            "weight": c["weight"],
        })
        if completed:
            earned += c["weight"]

    percentage = round((earned / total_weight) * 100) if total_weight > 0 else 0

    return {
        "percentage": percentage,
        "total_weight": total_weight,
        "earned_weight": earned,
        "items": items,
    }
