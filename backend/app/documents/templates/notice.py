from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

NOTICE_TEMPLATE = TemplateDefinition(
    doc_type="notice",
    title="NOTICE FOR APPEARANCE",
    subtitle="(Under Section 35(2) Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 35(2) BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Law"),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="notice_to_name", label="Name"),
                FieldDef(key="notice_to_address", label="Address"),
            ],
        ),
        TemplateSection(
            id="notice_body",
            title="Notice",
            section_type=SectionType.BODY_TEXT,
            content_key="notice_body_text",
        ),
        TemplateSection(
            id="appearance_details",
            title="Appearance Required",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="appearance_date", label="Date of Appearance"),
                FieldDef(key="appearance_time", label="Time"),
                FieldDef(key="appearance_place", label="Place"),
            ],
        ),
        TemplateSection(
            id="warning",
            title="",
            section_type=SectionType.LEGAL_FOOTER,
            content_key="non_compliance_warning",
        ),
    ],
    signatures=[
        SignatureBlock(title="Officer In-Charge / Investigating Officer", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(NOTICE_TEMPLATE)
