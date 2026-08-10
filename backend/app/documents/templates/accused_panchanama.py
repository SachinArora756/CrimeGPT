from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

ACCUSED_PANCHANAMA_TEMPLATE = TemplateDefinition(
    doc_type="accused_panchanama",
    title="ACCUSED PERSONAL SEARCH PANCHANAMA",
    subtitle="(Under Section 53 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 53 BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="arrest_date", label="Date of Arrest"),
            ],
        ),
        TemplateSection(
            id="accused_personal",
            title="Accused Personal Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="accused_name", label="Name"),
                FieldDef(key="accused_age", label="Age"),
                FieldDef(key="accused_father", label="Father's/Husband's Name"),
                FieldDef(key="accused_address", label="Address"),
                FieldDef(key="accused_height", label="Height (approx.)"),
                FieldDef(key="accused_build", label="Build"),
                FieldDef(key="accused_complexion", label="Complexion"),
            ],
        ),
        TemplateSection(
            id="id_marks",
            title="Identification Marks",
            section_type=SectionType.BODY_TEXT,
            content_key="id_marks_description",
        ),
        TemplateSection(
            id="clothing",
            title="Clothing Worn at Time of Arrest",
            section_type=SectionType.BODY_TEXT,
            content_key="accused_clothing",
        ),
        TemplateSection(
            id="articles_found",
            title="Articles Found on Person",
            section_type=SectionType.LIST,
            content_key="articles_on_person",
        ),
        TemplateSection(
            id="injuries_observed",
            title="Injuries / Marks Observed on Body",
            section_type=SectionType.BODY_TEXT,
            content_key="injuries_description",
        ),
        TemplateSection(
            id="panchanama_body",
            title="Panchanama Proceedings",
            section_type=SectionType.BODY_TEXT,
            content_key="panchanama_body_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Independent Witness 1 (Name & Address)", with_date=True),
        SignatureBlock(title="Independent Witness 2 (Name & Address)", with_date=True),
        SignatureBlock(title="Accused (Signature/Thumb Impression)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(ACCUSED_PANCHANAMA_TEMPLATE)
