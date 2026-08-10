from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

MEDICAL_TREATMENT_LETTER_TEMPLATE = TemplateDefinition(
    doc_type="medical_treatment_letter",
    title="LETTER FOR MEDICAL TREATMENT",
    subtitle="(Under Section 36 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 36 BNSS",
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
            content_key="treatment_addressee_text",
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
            id="patient_details",
            title="Patient Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="person_name", label="Name"),
                FieldDef(key="person_age", label="Age"),
                FieldDef(key="person_gender", label="Gender"),
                FieldDef(key="person_role", label="Role (Victim/Accused/Injured)"),
                FieldDef(key="patient_condition", label="Present Condition"),
            ],
        ),
        TemplateSection(
            id="injuries",
            title="Injuries / Condition",
            section_type=SectionType.BODY_TEXT,
            content_key="injuries_description",
        ),
        TemplateSection(
            id="request_body",
            title="Request",
            section_type=SectionType.BODY_TEXT,
            content_key="treatment_request_text",
        ),
        TemplateSection(
            id="treatment_required",
            title="Treatment Required",
            section_type=SectionType.LIST,
            content_key="treatment_required_list",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Escort Constable (Name & Belt No.)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(MEDICAL_TREATMENT_LETTER_TEMPLATE)
