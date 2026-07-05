from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

WITNESS_STATEMENT_TEMPLATE = TemplateDefinition(
    doc_type="witness_statement",
    title="STATEMENT OF WITNESS",
    subtitle="(Under Section 161/162 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 161/162 BNSS (previously Section 161 CrPC)",
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
            id="witness_details",
            title="Witness Particulars",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="witness_name", label="Name of Witness"),
                FieldDef(key="witness_father", label="Father's / Husband's Name"),
                FieldDef(key="witness_age", label="Age"),
                FieldDef(key="witness_address", label="Address"),
                FieldDef(key="witness_occupation", label="Occupation"),
                FieldDef(key="witness_contact", label="Contact Number"),
                FieldDef(key="witness_relation", label="Relation to Complainant/Accused"),
            ],
        ),
        TemplateSection(
            id="recording_details",
            title="Recording Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="recording_date", label="Date of Recording"),
                FieldDef(key="recording_time", label="Time of Recording"),
                FieldDef(key="recording_place", label="Place of Recording"),
                FieldDef(key="recording_officer", label="Recording Officer (Name & Rank)"),
                FieldDef(key="audio_video", label="Audio-Video Recording (Yes/No)"),
            ],
        ),
        TemplateSection(
            id="statement_body",
            title="Statement",
            section_type=SectionType.BODY_TEXT,
            content_key="witness_statement_text",
        ),
        TemplateSection(
            id="caution_note",
            title="",
            section_type=SectionType.LEGAL_FOOTER,
            content_key="caution_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Witness (Signature / Thumb Impression)", with_date=True),
        SignatureBlock(title="Recording Officer (Name, Rank, Belt No.)", with_date=True),
    ],
    seal_placeholder=False,
)

register_template(WITNESS_STATEMENT_TEMPLATE)
