from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

CLOSURE_REPORT_TEMPLATE = TemplateDefinition(
    doc_type="closure_report",
    title="FINAL REPORT (CLOSURE / UNTRACED)",
    subtitle="(Under Section 193 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 193 BNSS",
    sections=[
        TemplateSection(
            id="court_address",
            title="Before the Hon'ble Court",
            section_type=SectionType.BODY_TEXT,
            content_key="court_addressee",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Particulars",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="fir_date", label="FIR Date"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="offense_type", label="Nature of Offence"),
                FieldDef(key="complainant_name", label="Complainant"),
            ],
        ),
        TemplateSection(
            id="brief_facts",
            title="Brief Facts",
            section_type=SectionType.BODY_TEXT,
            content_key="closure_brief_facts",
        ),
        TemplateSection(
            id="investigation_summary",
            title="Investigation Summary",
            section_type=SectionType.BODY_TEXT,
            content_key="closure_investigation_summary",
        ),
        TemplateSection(
            id="steps_taken",
            title="Steps Taken During Investigation",
            section_type=SectionType.LIST,
            content_key="closure_steps_list",
        ),
        TemplateSection(
            id="closure_reason",
            title="Reason for Closure",
            section_type=SectionType.BODY_TEXT,
            content_key="closure_reason_text",
        ),
        TemplateSection(
            id="prayer",
            title="Prayer",
            section_type=SectionType.BODY_TEXT,
            content_key="closure_prayer_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Station House Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Superintendent of Police (endorsement)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(CLOSURE_REPORT_TEMPLATE)
