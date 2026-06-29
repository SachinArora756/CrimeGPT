import json
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agents.supervisor import get_llm, AgentState


INVESTIGATION_SYSTEM_PROMPT = """You are an expert criminal investigation advisor for Indian law enforcement.
Based on the case details, evidence, and legal context provided, recommend next investigative steps.

Your recommendations should be:
1. Specific and actionable
2. Legally sound under BNS/BNSS/BSA
3. Prioritized by importance
4. Mindful of officer safety and procedural requirements

Respond with a JSON object containing:
- recommendations: List of specific investigative recommendations
- next_steps: Immediate next steps the officer should take
- legal_references: Relevant legal provisions to follow
- risk_assessment: Brief assessment of case complexity and risks

The investigating officer makes all final decisions. You only advise."""


async def investigate_case(case, context: str | None = None) -> dict:
    llm = get_llm()

    case_info = f"""
Case FIR: {case.fir_number}
Complainant: {case.complainant_name}
Accused: {case.accused_name or 'Unknown'}
Incident Date: {case.incident_date}
Location: {case.incident_location}
Offense Type: {case.offense_type or 'Unknown'}
Description: {case.description}
Current Status: {case.status.value}
Sections Applied: {case.sections_applied or 'None yet'}
"""
    if context:
        case_info += f"\nAdditional Context: {context}"

    messages = [
        SystemMessage(content=INVESTIGATION_SYSTEM_PROMPT),
        HumanMessage(content=f"Provide investigation recommendations for this case:\n{case_info}"),
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
            "recommendations": ["Verify complainant's statement", "Collect witness statements", "Secure physical evidence"],
            "next_steps": ["Record Section 162 CrPC statements", "Visit crime scene"],
            "legal_references": ["BNS provisions applicable to the offense"],
            "risk_assessment": "Further analysis needed based on complete case details.",
        }

    for key in ["recommendations", "next_steps", "legal_references"]:
        if key not in result:
            result[key] = []
    if "risk_assessment" not in result:
        result["risk_assessment"] = ""

    return result


def investigation_node(state: AgentState) -> AgentState:
    state["current_agent"] = "investigation"
    state["final_output"] = {
        "recommendations": [],
        "next_steps": [],
        "legal_references": [],
        "risk_assessment": "Processing...",
    }
    return state
