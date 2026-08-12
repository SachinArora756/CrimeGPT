from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

INQUEST_REPORT_TEMPLATE = TemplateDefinition(
    doc_type="inquest_report",
    title="INQUEST REPORT",
    subtitle="(Under Section 194 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 194 BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number (if registered)"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Law"),
            ],
        ),
        TemplateSection(
            id="inquest_details",
            title="Inquest Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="inquest_date", label="Date of Inquest"),
                FieldDef(key="inquest_time", label="Time"),
                FieldDef(key="inquest_place", label="Place Where Body Found"),
                FieldDef(key="informant_name", label="Informant Name"),
                FieldDef(key="informant_relation", label="Relation to Deceased"),
            ],
        ),
        TemplateSection(
            id="deceased_details",
            title="Deceased Person Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="deceased_name", label="Name (if identified)"),
                FieldDef(key="deceased_age", label="Apparent Age"),
                FieldDef(key="deceased_gender", label="Gender"),
                FieldDef(key="deceased_address", label="Address"),
                FieldDef(key="deceased_id_marks", label="Identification Marks"),
            ],
        ),
        TemplateSection(
            id="body_description",
            title="Description of Body / External Appearance",
            section_type=SectionType.BODY_TEXT,
            content_key="inquest_body_description",
        ),
        TemplateSection(
            id="injuries_visible",
            title="Visible Injuries / Marks",
            section_type=SectionType.BODY_TEXT,
            content_key="inquest_injuries",
        ),
        TemplateSection(
            id="apparent_cause",
            title="Apparent Cause of Death",
            section_type=SectionType.BODY_TEXT,
            content_key="inquest_apparent_cause",
        ),
        TemplateSection(
            id="action_taken",
            title="Action Taken",
            section_type=SectionType.BODY_TEXT,
            content_key="inquest_action",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Panch Witness 1 (Name & Address)", with_date=True),
        SignatureBlock(title="Panch Witness 2 (Name & Address)", with_date=True),
        SignatureBlock(title="Relative / Identifier (if present)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(INQUEST_REPORT_TEMPLATE)
