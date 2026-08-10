from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

FACE_IDENTIFICATION_TEMPLATE = TemplateDefinition(
    doc_type="face_identification",
    title="TEST IDENTIFICATION PARADE PROCEEDINGS",
    subtitle="(Under Section 9 Bharatiya Sakshya Adhiniyam, 2023)",
    legal_reference="Section 9 BSA 2023",
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
            id="parade_details",
            title="Identification Parade Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="parade_date", label="Date of Parade"),
                FieldDef(key="parade_time", label="Time of Parade"),
                FieldDef(key="parade_place", label="Place of Parade"),
                FieldDef(key="magistrate_name", label="Presiding Magistrate"),
            ],
        ),
        TemplateSection(
            id="accused_details",
            title="Accused / Person to be Identified",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="accused_name", label="Name"),
                FieldDef(key="accused_age", label="Age"),
                FieldDef(key="accused_father", label="Father's Name"),
                FieldDef(key="accused_address", label="Address"),
            ],
        ),
        TemplateSection(
            id="parade_panel",
            title="Identification Panel (Persons in Parade)",
            section_type=SectionType.LIST,
            content_key="identification_panel",
        ),
        TemplateSection(
            id="witness_details",
            title="Identifying Witness Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="witness_name", label="Witness Name"),
                FieldDef(key="witness_father", label="Father's Name"),
                FieldDef(key="witness_address", label="Address"),
                FieldDef(key="witness_relation", label="Relation to Case"),
            ],
        ),
        TemplateSection(
            id="identification_result",
            title="Identification Result",
            section_type=SectionType.BODY_TEXT,
            content_key="identification_result",
        ),
        TemplateSection(
            id="observations",
            title="Observations",
            section_type=SectionType.BODY_TEXT,
            content_key="parade_observations",
        ),
    ],
    signatures=[
        SignatureBlock(title="Presiding Magistrate", with_date=True, with_seal=True),
        SignatureBlock(title="Investigating Officer", with_date=True),
        SignatureBlock(title="Identifying Witness", with_date=True),
        SignatureBlock(title="Accused (Signature/Thumb Impression)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(FACE_IDENTIFICATION_TEMPLATE)
