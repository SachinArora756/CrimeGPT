import re
from app.ai.rag.chunking import ChunkResult


OFFENSE_CATEGORIES = {
    "against_person": ["murder", "homicide", "hurt", "grievous", "death", "assault", "attempt to murder", "negligence", "suicide", "abetment"],
    "sexual_offences": ["rape", "sexual", "modesty", "outraging", "stalking", "voyeurism", "harassment", "disrobe", "intercourse"],
    "against_property": ["theft", "robbery", "dacoity", "extortion", "cheating", "fraud", "trespass", "mischief", "breach of trust", "snatching", "forgery"],
    "kidnapping": ["kidnap", "abduct", "wrongful confinement", "wrongful restraint"],
    "public_order": ["unlawful assembly", "rioting", "affray", "public tranquility"],
    "terrorism_organised": ["terrorist", "organised crime", "syndicate"],
    "women_children": ["dowry", "cruelty", "marriage", "child", "woman", "female"],
    "defamation_intimidation": ["defamation", "intimidation", "insult", "annoyance"],
    "procedural": ["fir", "investigation", "arrest", "bail", "chargesheet", "search", "seizure", "summons", "warrant"],
    "evidence_law": ["evidence", "admissibility", "witness", "confession", "document", "electronic record", "presumption", "burden of proof"],
    "constitutional": ["fundamental", "article", "right", "equality", "liberty", "protection"],
    "forensic": ["forensic", "dna", "ballistic", "fingerprint", "digital evidence", "crime scene"],
}


def extract_metadata(chunk: ChunkResult, act_name: str, source_file: str) -> dict:
    text_lower = chunk.text.lower()

    offense_category = _detect_category(text_lower)
    punishment_range = _extract_punishment(chunk.text)
    keywords = _extract_keywords(text_lower)
    is_procedure = _is_procedural(act_name, text_lower)

    return {
        "text": chunk.text,
        "act": act_name,
        "source_file": source_file,
        "section_number": chunk.section_number or "",
        "chapter": chunk.chapter or "",
        "heading": chunk.heading or "",
        "offense_category": offense_category,
        "punishment_range": punishment_range,
        "keywords": keywords,
        "is_procedure": is_procedure,
    }


def _detect_category(text_lower: str) -> str:
    scores = {}
    for category, terms in OFFENSE_CATEGORIES.items():
        score = sum(1 for term in terms if term in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "general"
    return max(scores, key=scores.get)


def _extract_punishment(text: str) -> str:
    patterns = [
        r'Punishment:\s*(.+?)(?:\n|$)',
        r'shall be punished with\s+(.+?)(?:\.|$)',
        r'punishable with\s+(.+?)(?:\.|$)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            punishment = m.group(1).strip()
            if len(punishment) > 200:
                punishment = punishment[:200] + "..."
            return punishment
    return ""


def _extract_keywords(text_lower: str) -> list[str]:
    all_terms = []
    for terms in OFFENSE_CATEGORIES.values():
        for term in terms:
            if term in text_lower:
                all_terms.append(term)

    legal_terms = [
        "cognizable", "non-bailable", "bailable", "warrant",
        "magistrate", "sessions court", "high court",
        "imprisonment for life", "death", "fine",
        "rigorous imprisonment", "simple imprisonment",
    ]
    for term in legal_terms:
        if term in text_lower:
            all_terms.append(term)

    return list(set(all_terms))[:15]


def _is_procedural(act_name: str, text_lower: str) -> bool:
    procedural_acts = ["BNSS", "Police Manual", "Investigation Procedures"]
    if any(a.lower() in act_name.lower() for a in procedural_acts):
        return True

    procedural_indicators = ["procedure", "shall be", "the officer shall", "timeline:", "requirements:", "steps:"]
    return sum(1 for ind in procedural_indicators if ind in text_lower) >= 2
