from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

CONTENT_BLOCKING_TEMPLATE = TemplateDefinition(
    doc_type="content_blocking",
    title="REQUEST FOR BLOCKING OF INFORMATION / CONTENT",
    subtitle="(Under Section 69A Information Technology Act, 2000 read with Blocking Rules, 2009)",
    legal_reference="Section 69A IT Act r/w IT (Blocking) Rules 2009",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Nodal Officer / Authorised Officer"),
                FieldDef(key="officer_designation", label="Designation"),
                FieldDef(key="station_id", label="Police Station / Unit"),
                FieldDef(key="letter_date", label="Date"),
                FieldDef(key="letter_ref", label="Reference No."),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To",
            section_type=SectionType.BODY_TEXT,
            content_key="blocking_addressee",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="content_info",
            title="Content / Information to be Blocked",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="content_url", label="URL(s) / URI(s)"),
                FieldDef(key="content_platform", label="Platform / Website"),
                FieldDef(key="content_type", label="Type of Content"),
                FieldDef(key="content_account", label="Account / Page"),
            ],
        ),
        TemplateSection(
            id="grounds",
            title="Grounds for Blocking (Section 69A(1))",
            section_type=SectionType.BODY_TEXT,
            content_key="blocking_grounds",
        ),
        TemplateSection(
            id="urgency",
            title="Urgency",
            section_type=SectionType.BODY_TEXT,
            content_key="blocking_urgency",
        ),
        TemplateSection(
            id="legal_basis",
            title="Legal Basis",
            section_type=SectionType.LEGAL_FOOTER,
            content_key="blocking_legal_basis",
        ),
    ],
    signatures=[
        SignatureBlock(title="Nodal Officer (State) / Authorised Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Superintendent of Police (or above)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(CONTENT_BLOCKING_TEMPLATE)
