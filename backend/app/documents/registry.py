from dataclasses import dataclass, field
from enum import Enum


class SectionType(str, Enum):
    HEADER = "header"
    METADATA_TABLE = "metadata_table"
    BODY_TEXT = "body_text"
    LIST = "list"
    SIGNATURE_BLOCK = "signature_block"
    LEGAL_FOOTER = "legal_footer"


@dataclass
class FieldDef:
    key: str
    label: str
    fallback: str = "---"


@dataclass
class TemplateSection:
    id: str
    title: str
    section_type: SectionType
    fields: list[FieldDef] = field(default_factory=list)
    mandatory: bool = True
    content_key: str | None = None


@dataclass
class SignatureBlock:
    title: str
    with_date: bool = False
    with_seal: bool = False


@dataclass
class TemplateDefinition:
    doc_type: str
    title: str
    subtitle: str | None = None
    form_number: str | None = None
    legal_reference: str = ""
    sections: list[TemplateSection] = field(default_factory=list)
    signatures: list[SignatureBlock] = field(default_factory=list)
    seal_placeholder: bool = True


TEMPLATE_REGISTRY: dict[str, TemplateDefinition] = {}


def register_template(template: TemplateDefinition):
    TEMPLATE_REGISTRY[template.doc_type] = template


def get_template(doc_type: str) -> TemplateDefinition | None:
    return TEMPLATE_REGISTRY.get(doc_type)


from app.documents.templates import fir, chargesheet, arrest_memo, seizure_memo  # noqa: E402, F401
from app.documents.templates import search_memo, witness_statement, notice  # noqa: E402, F401
from app.documents.templates import medical_letter, court_letter, case_diary  # noqa: E402, F401
