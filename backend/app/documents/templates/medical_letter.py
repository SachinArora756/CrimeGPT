from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

MEDICAL_LETTER_TEMPLATE = TemplateDefinition(
    doc_type="medical_letter",
    title="REQUEST FOR MEDICAL EXAMINATION",
    subtitle="(Under Section 53/54 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 53/54 BNSS",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Officer In-Charge"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="letter_date", label="Date"),
                FieldDef(key="letter_ref", label="Reference No."),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To",
            section_type=SectionType.BODY_TEXT,
            content_key="addressee_text",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="sections_applied", label="Sections"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="person_details",
            title="Person to be Examined",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="person_name", label="Name"),
                FieldDef(key="person_age", label="Age"),
                FieldDef(key="person_gender", label="Gender"),
                FieldDef(key="person_role", label="Role (Victim/Accused/Injured)"),
            ],
        ),
        TemplateSection(
            id="request_body",
            title="Request",
            section_type=SectionType.BODY_TEXT,
            content_key="request_text",
        ),
        TemplateSection(
            id="examination_required",
            title="Examination Required",
            section_type=SectionType.LIST,
            content_key="examination_types",
        ),
    ],
    signatures=[
        SignatureBlock(title="Station House Officer / Investigating Officer", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(MEDICAL_LETTER_TEMPLATE)
