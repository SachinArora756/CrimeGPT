from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END

from app.ai.llm_provider import get_llm as _get_llm


class AgentState(TypedDict):
    task: str
    case_data: dict
    evidence_data: list
    legal_context: list
    investigation_results: dict
    documents_generated: list
    diary_entries: list
    current_agent: str
    messages: list
    final_output: dict


def get_llm():
    return _get_llm()


def route_task(state: AgentState) -> Literal["case_intake", "investigation", "legal_rag", "document_gen", "evidence_analysis", "case_diary", "end"]:
    task = state.get("task", "")
    if "intake" in task or "extract" in task:
        return "case_intake"
    elif "investigate" in task or "recommend" in task:
        return "investigation"
    elif "legal" in task or "section" in task or "provision" in task:
        return "legal_rag"
    elif "document" in task or "generate" in task or "fir" in task:
        return "document_gen"
    elif "evidence" in task or "analyze" in task or "ocr" in task:
        return "evidence_analysis"
    elif "diary" in task:
        return "case_diary"
    return "end"


def create_supervisor_graph():
    from app.ai.agents.case_intake import case_intake_node
    from app.ai.agents.investigation import investigation_node
    from app.ai.agents.legal_rag import legal_rag_node
    from app.ai.agents.document_gen import document_gen_node
    from app.ai.agents.evidence_analysis import evidence_analysis_node
    from app.ai.agents.case_diary import case_diary_node

    graph = StateGraph(AgentState)

    graph.add_node("case_intake", case_intake_node)
    graph.add_node("investigation", investigation_node)
    graph.add_node("legal_rag", legal_rag_node)
    graph.add_node("document_gen", document_gen_node)
    graph.add_node("evidence_analysis", evidence_analysis_node)
    graph.add_node("case_diary", case_diary_node)

    graph.set_conditional_entry_point(route_task)

    graph.add_edge("case_intake", END)
    graph.add_edge("investigation", END)
    graph.add_edge("legal_rag", END)
    graph.add_edge("document_gen", END)
    graph.add_edge("evidence_analysis", END)
    graph.add_edge("case_diary", END)

    return graph.compile()
