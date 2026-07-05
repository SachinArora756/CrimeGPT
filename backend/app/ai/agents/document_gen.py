import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.case import Case
from app.models.document import DocType
from app.ai.agents.supervisor import AgentState
from app.documents.registry import get_template
from app.documents.data_binder import bind_template_data
from app.documents.docx_renderer import render_docx
from app.documents.pdf_renderer import render_pdf


async def generate_legal_document(
    db: AsyncSession,
    case_id: int,
    doc_type: DocType,
    additional_context: str | None = None,
    output_format: str = "docx",
) -> str:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    template = get_template(doc_type.value)
    if not template:
        raise ValueError(f"No template found for document type: {doc_type.value}")

    data = await bind_template_data(template, case, db, additional_context)

    doc_dir = os.path.join(settings.upload_dir, str(case_id), "documents")
    os.makedirs(doc_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ext = "pdf" if output_format == "pdf" else "docx"
    filename = f"{doc_type.value}_{timestamp}.{ext}"
    file_path = os.path.join(doc_dir, filename)

    if output_format == "pdf":
        render_pdf(template, data, file_path)
    else:
        render_docx(template, data, file_path)

    return file_path


def document_gen_node(state: AgentState) -> AgentState:
    state["current_agent"] = "document_gen"
    return state
