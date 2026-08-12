from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

SPOT_PANCHNAMA_TEMPLATE = TemplateDefinition(
    doc_type="spot_panchnama",
    title="SPOT INSPECTION / SCENE OF CRIME PANCHNAMA",
    subtitle="(Under Section 176/185 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 176/185 BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="inspection_details",
            title="Inspection Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="spot_date", label="Date of Inspection"),
                FieldDef(key="spot_time_start", label="Time of Arrival"),
                FieldDef(key="spot_time_end", label="Time of Departure"),
                FieldDef(key="spot_location", label="Location / Address"),
                FieldDef(key="spot_gps", label="GPS Coordinates (if available)"),
            ],
        ),
        TemplateSection(
            id="scene_description",
            title="Description of Scene",
            section_type=SectionType.BODY_TEXT,
            content_key="spot_scene_description",
        ),
        TemplateSection(
            id="evidence_found",
            title="Articles / Evidence Found at Scene",
            section_type=SectionType.LIST,
            content_key="spot_evidence_list",
        ),
        TemplateSection(
            id="photographs",
            title="Photographs / Videography",
            section_type=SectionType.BODY_TEXT,
            content_key="spot_photo_note",
        ),
        TemplateSection(
            id="observations",
            title="Observations",
            section_type=SectionType.BODY_TEXT,
            content_key="spot_observations",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Independent Witness 1 (Name & Address)", with_date=True),
        SignatureBlock(title="Independent Witness 2 (Name & Address)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(SPOT_PANCHNAMA_TEMPLATE)
