from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

MISSING_PERSON_TEMPLATE = TemplateDefinition(
    doc_type="missing_person",
    title="MISSING PERSON REPORT",
    subtitle="(Under Section 175 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 175 BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="DDR / FIR Number"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="fir_date", label="Date of Report"),
            ],
        ),
        TemplateSection(
            id="informant",
            title="Informant / Complainant Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="complainant_name", label="Name"),
                FieldDef(key="complainant_address", label="Address"),
                FieldDef(key="complainant_contact", label="Contact Number"),
                FieldDef(key="informant_relation", label="Relation to Missing Person"),
            ],
        ),
        TemplateSection(
            id="missing_person_details",
            title="Missing Person Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="missing_name", label="Name"),
                FieldDef(key="missing_age", label="Age"),
                FieldDef(key="missing_gender", label="Gender"),
                FieldDef(key="missing_height", label="Height (approx.)"),
                FieldDef(key="missing_complexion", label="Complexion"),
                FieldDef(key="missing_hair", label="Hair"),
                FieldDef(key="missing_id_marks", label="Identification Marks"),
            ],
        ),
        TemplateSection(
            id="last_seen",
            title="Last Seen Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="last_seen_date", label="Date Last Seen"),
                FieldDef(key="last_seen_time", label="Time"),
                FieldDef(key="last_seen_place", label="Place"),
                FieldDef(key="last_seen_clothing", label="Clothing Worn"),
            ],
        ),
        TemplateSection(
            id="circumstances",
            title="Circumstances of Disappearance",
            section_type=SectionType.BODY_TEXT,
            content_key="missing_circumstances",
        ),
        TemplateSection(
            id="action_taken",
            title="Action Taken",
            section_type=SectionType.LIST,
            content_key="missing_action_list",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Informant / Complainant", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(MISSING_PERSON_TEMPLATE)
