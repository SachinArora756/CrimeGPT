from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

REMAND_REQUEST_TEMPLATE = TemplateDefinition(
    doc_type="remand_request",
    title="APPLICATION FOR REMAND",
    subtitle="(Under Section 187 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 187 BNSS",
    sections=[
        TemplateSection(
            id="court_address",
            title="Before the Hon'ble Court",
            section_type=SectionType.BODY_TEXT,
            content_key="court_addressee",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="fir_date", label="FIR Date"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="accused_details",
            title="Accused Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="accused_name", label="Name of Accused"),
                FieldDef(key="accused_age", label="Age"),
                FieldDef(key="accused_father", label="Father's Name"),
                FieldDef(key="accused_address", label="Address"),
                FieldDef(key="arrest_date", label="Date of Arrest"),
            ],
        ),
        TemplateSection(
            id="custody_details",
            title="Custody Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="custody_type", label="Type of Custody Requested"),
                FieldDef(key="custody_days_requested", label="Days of Remand Requested"),
            ],
        ),
        TemplateSection(
            id="remand_grounds",
            title="Grounds for Remand",
            section_type=SectionType.BODY_TEXT,
            content_key="remand_grounds",
        ),
        TemplateSection(
            id="investigation_progress",
            title="Investigation Progress",
            section_type=SectionType.BODY_TEXT,
            content_key="investigation_progress",
        ),
        TemplateSection(
            id="prayer",
            title="Prayer",
            section_type=SectionType.BODY_TEXT,
            content_key="remand_prayer_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Station House Officer", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(REMAND_REQUEST_TEMPLATE)
