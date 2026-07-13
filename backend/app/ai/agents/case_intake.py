import json
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agents.supervisor import get_llm, AgentState


INTAKE_SYSTEM_PROMPT = """You are a police case intake assistant. Your job is to extract structured information from a complaint statement.

Extract the following fields from the complaint text:
- complainant_name: Name of the person filing the complaint
- accused_name: Name of the accused person(s)
- incident_date: Date of the incident (YYYY-MM-DD format if possible)
- incident_location: Location where the incident occurred
- offense_type: Type of offense (theft, assault, murder, fraud, etc.)
- suggested_sections: Relevant sections of BNS (Bharatiya Nyaya Sanhita) that may apply
- summary: A brief 2-3 sentence summary

Respond ONLY with a JSON object containing these fields. If a field cannot be determined, use null.
Do NOT include any explanation outside the JSON."""


async def extract_case_data(complaint_text: str, language: str = "en") -> dict:
    llm = get_llm()

    messages = [
        SystemMessage(content=INTAKE_SYSTEM_PROMPT),
        HumanMessage(content=f"Extract structured data from this complaint:\n\n{complaint_text}"),
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
            "complainant_name": None,
            "accused_name": None,
            "incident_date": None,
            "incident_location": None,
            "offense_type": None,
            "suggested_sections": [],
            "summary": complaint_text[:200],
        }

    if "suggested_sections" not in result:
        result["suggested_sections"] = []
    if "summary" not in result:
        result["summary"] = ""

    # Sanitize accused_name — reject numeric or count-like values
    accused = result.get("accused_name")
    if accused is not None:
        accused_str = str(accused).strip()
        if accused_str.isdigit() or accused_str.lower() in ("unknown", "none", "null", "n/a", "0"):
            result["accused_name"] = None
        else:
            result["accused_name"] = accused_str

    return result


def case_intake_node(state: AgentState) -> AgentState:
    import asyncio
    task = state.get("task", "")
    case_data = state.get("case_data", {})
    complaint_text = case_data.get("description", task)

    result = asyncio.run(extract_case_data(complaint_text))
    state["final_output"] = result
    state["current_agent"] = "case_intake"
    return state
