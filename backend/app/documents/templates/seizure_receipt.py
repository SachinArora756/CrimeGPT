from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

SEIZURE_RECEIPT_TEMPLATE = TemplateDefinition(
    doc_type="seizure_receipt",
    title="SEIZURE RECEIPT",
    subtitle="(Under Section 185/186 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 185-186 BNSS",
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
            id="seizure_details",
            title="Seizure Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="seizure_date", label="Date of Seizure"),
                FieldDef(key="seizure_time", label="Time of Seizure"),
                FieldDef(key="seizure_place", label="Place of Seizure"),
            ],
        ),
        TemplateSection(
            id="person_details",
            title="Person from Whom Property Seized",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="person_from_whom_seized", label="Name"),
                FieldDef(key="accused_address", label="Address"),
            ],
        ),
        TemplateSection(
            id="articles_seized",
            title="Articles / Property Seized",
            section_type=SectionType.LIST,
            content_key="seized_articles",
        ),
        TemplateSection(
            id="articles_condition",
            title="Condition of Articles at Time of Seizure",
            section_type=SectionType.BODY_TEXT,
            content_key="articles_condition",
        ),
        TemplateSection(
            id="acknowledgment",
            title="Acknowledgment",
            section_type=SectionType.BODY_TEXT,
            content_key="seizure_receipt_acknowledgment",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Person from whom property seized", with_date=True),
        SignatureBlock(title="Independent Witness 1 (Name & Address)", with_date=True),
        SignatureBlock(title="Independent Witness 2 (Name & Address)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(SEIZURE_RECEIPT_TEMPLATE)
