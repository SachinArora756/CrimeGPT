from dataclasses import dataclass, field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.document import CaseDiary
from app.models.timeline import TimelineEvent


@dataclass
class CaseContext:
    case_id: int
    fir_number: str = ""
    complainant_name: str = ""
    accused_name: str = ""
    incident_date: str = ""
    incident_location: str = ""
    description: str = ""
    offense_type: str = ""
    victims: list[dict] = field(default_factory=list)
    accused_persons: list[dict] = field(default_factory=list)
    witnesses: list[dict] = field(default_factory=list)
    evidence_texts: list[str] = field(default_factory=list)
    evidence_tags: list[str] = field(default_factory=list)
    evidence_analysis: list[str] = field(default_factory=list)
    diary_entries: list[str] = field(default_factory=list)
    timeline_events: list[str] = field(default_factory=list)
    extracted_facts: list[str] = field(default_factory=list)
    sections_already_applied: list[str] = field(default_factory=list)

    def build_summary(self) -> str:
        parts = []
        parts.append(f"FIR: {self.fir_number}")
        parts.append(f"Complainant: {self.complainant_name}")
        if self.accused_name:
            parts.append(f"Accused: {self.accused_name}")
        if self.incident_date:
            parts.append(f"Incident Date: {self.incident_date}")
        if self.incident_location:
            parts.append(f"Location: {self.incident_location}")
        if self.offense_type:
            parts.append(f"Offense Type: {self.offense_type}")
        parts.append(f"\nDescription:\n{self.description[:2000]}")

        if self.victims:
            parts.append(f"\nVictims: {len(self.victims)}")
            for v in self.victims[:5]:
                name = v.get("name", "Unknown") if isinstance(v, dict) else str(v)
                parts.append(f"  - {name}")

        if self.witnesses:
            parts.append(f"\nWitnesses: {len(self.witnesses)}")
            for w in self.witnesses[:5]:
                name = w.get("name", "Unknown") if isinstance(w, dict) else str(w)
                parts.append(f"  - {name}")

        if self.evidence_texts:
            parts.append(f"\nEvidence (OCR/Text): {len(self.evidence_texts)} items")
            for et in self.evidence_texts[:5]:
                parts.append(f"  - {et[:300]}")

        if self.evidence_analysis:
            parts.append(f"\nEvidence Analysis:")
            for ea in self.evidence_analysis[:5]:
                parts.append(f"  - {ea[:300]}")

        if self.diary_entries:
            parts.append(f"\nCase Diary Entries: {len(self.diary_entries)}")
            for de in self.diary_entries[:3]:
                parts.append(f"  - {de[:200]}")

        if self.timeline_events:
            parts.append(f"\nTimeline: {len(self.timeline_events)} events")
            for te in self.timeline_events[:5]:
                parts.append(f"  - {te}")

        if self.extracted_facts:
            parts.append(f"\nExtracted Facts:")
            for f in self.extracted_facts[:10]:
                parts.append(f"  - {f}")

        if self.sections_already_applied:
            parts.append(f"\nSections Already Applied: {', '.join(self.sections_already_applied)}")

        return "\n".join(parts)

    def generate_rag_queries(self, focus_area: str | None = None) -> list[str]:
        queries = []

        if self.description:
            desc_short = self.description[:200]
            queries.append(f"Criminal offense: {desc_short}")

        if self.offense_type:
            queries.append(f"BNS section for {self.offense_type}")
            queries.append(f"Punishment for {self.offense_type} under BNS")

        if self.accused_persons:
            queries.append("Arrest procedure BNSS requirements")

        if self.evidence_tags:
            for tag in self.evidence_tags[:3]:
                queries.append(f"Evidence law {tag} BSA admissibility")

        if any("digital" in t.lower() or "electronic" in t.lower() for t in self.evidence_tags):
            queries.append("Electronic evidence Section 63 BSA certification")

        if self.victims:
            queries.append("Rights of victim criminal procedure")

        queries.append("Investigation procedure BNSS obligations")

        if focus_area:
            queries.append(f"{focus_area} Indian criminal law")

        if self.extracted_facts:
            fact_summary = "; ".join(self.extracted_facts[:5])
            queries.append(f"Legal provisions applicable: {fact_summary[:200]}")

        return queries[:8]


async def build_case_context(db: AsyncSession, case_id: int) -> CaseContext:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    ctx = CaseContext(case_id=case_id)
    ctx.fir_number = case.fir_number or ""
    ctx.complainant_name = case.complainant_name or ""
    ctx.accused_name = case.accused_name or ""
    ctx.incident_date = str(case.incident_date) if case.incident_date else ""
    ctx.incident_location = case.incident_location or ""
    ctx.description = case.description or ""
    ctx.offense_type = case.offense_type or ""
    ctx.victims = case.victims or []
    ctx.accused_persons = case.accused_persons or []
    ctx.witnesses = case.witnesses or []
    ctx.sections_already_applied = case.sections_applied or []

    if case.extracted_data and isinstance(case.extracted_data, dict):
        facts = case.extracted_data.get("key_facts", [])
        if isinstance(facts, list):
            ctx.extracted_facts = [str(f) for f in facts]

    evidence_result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id)
    )
    evidences = evidence_result.scalars().all()
    for ev in evidences:
        if ev.ocr_text:
            ctx.evidence_texts.append(ev.ocr_text[:500])
        if ev.tags:
            ctx.evidence_tags.extend(ev.tags)
        if ev.analysis_results and isinstance(ev.analysis_results, dict):
            summary = ev.analysis_results.get("summary", "")
            if summary:
                ctx.evidence_analysis.append(str(summary)[:500])

    diary_result = await db.execute(
        select(CaseDiary).where(CaseDiary.case_id == case_id).order_by(CaseDiary.entry_date.desc()).limit(10)
    )
    diaries = diary_result.scalars().all()
    for d in diaries:
        ctx.diary_entries.append(f"[{d.entry_date}] {d.content[:300]}")

    timeline_result = await db.execute(
        select(TimelineEvent).where(TimelineEvent.case_id == case_id).order_by(TimelineEvent.created_at.desc()).limit(20)
    )
    events = timeline_result.scalars().all()
    for ev in events:
        desc = ev.description[:150] if ev.description else ev.title
        ctx.timeline_events.append(f"[{ev.created_at}] {ev.event_type.value}: {desc}")

    ctx.evidence_tags = list(set(ctx.evidence_tags))
    return ctx
