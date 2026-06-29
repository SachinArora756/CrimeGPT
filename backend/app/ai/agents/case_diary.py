import json
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agents.supervisor import get_llm, AgentState


DIARY_SYSTEM_PROMPT = """You are a case diary assistant for Indian police investigations.
Generate a professional case diary entry based on the provided investigation details.

A case diary entry should include:
- Date and time of activity
- Actions taken by the investigating officer
- Witnesses examined
- Evidence collected
- Observations and findings
- Next steps planned

Write in formal police diary style. Be factual and precise.
Respond with the diary entry text only."""


async def generate_diary_entry(case_data: dict, activities: str) -> str:
    llm = get_llm()

    messages = [
        SystemMessage(content=DIARY_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Generate a case diary entry for:
FIR: {case_data.get('fir_number', 'N/A')}
Date: {datetime.utcnow().strftime('%d/%m/%Y')}
Activities performed: {activities}"""
        ),
    ]

    response = await llm.ainvoke(messages)
    return response.content.strip()


def case_diary_node(state: AgentState) -> AgentState:
    state["current_agent"] = "case_diary"
    return state
