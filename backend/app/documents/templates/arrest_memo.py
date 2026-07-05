from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

ARREST_MEMO_TEMPLATE = TemplateDefinition(
    doc_type="arrest_memo",
    title="ARREST MEMO",
    subtitle="(Under Section 35/36 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 35-36 BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections of Offence"),
            ],
        ),
        TemplateSection(
            id="arrest_details",
            title="Arrest Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="arrest_date", label="Date of Arrest"),
                FieldDef(key="arrest_time", label="Time of Arrest"),
                FieldDef(key="arrest_place", label="Place of Arrest"),
            ],
        ),
        TemplateSection(
            id="arrested_person",
            title="Particulars of Arrested Person",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="accused_name", label="Name"),
                FieldDef(key="accused_father", label="Father's / Husband's Name"),
                FieldDef(key="accused_age", label="Age"),
                FieldDef(key="accused_address", label="Address"),
                FieldDef(key="accused_occupation", label="Occupation"),
                FieldDef(key="accused_id_marks", label="Identification Marks"),
            ],
        ),
        TemplateSection(
            id="grounds",
            title="Grounds of Arrest",
            section_type=SectionType.BODY_TEXT,
            content_key="grounds_of_arrest",
        ),
        TemplateSection(
            id="rights",
            title="Rights Communicated to Arrested Person",
            section_type=SectionType.BODY_TEXT,
            content_key="rights_communicated",
        ),
        TemplateSection(
            id="injuries",
            title="Physical Condition / Injuries at Time of Arrest",
            section_type=SectionType.BODY_TEXT,
            content_key="injuries_noted",
        ),
        TemplateSection(
            id="person_informed",
            title="Person Informed of Arrest",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="informed_person_name", label="Name"),
                FieldDef(key="informed_person_relation", label="Relation"),
                FieldDef(key="informed_person_contact", label="Contact Number"),
            ],
        ),
    ],
    signatures=[
        SignatureBlock(title="Arrested Person (Acknowledgment of Rights)", with_date=True),
        SignatureBlock(title="Arresting Officer (Name, Rank, Belt No.)", with_date=True, with_seal=True),
        SignatureBlock(title="Witness (Attestation)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(ARREST_MEMO_TEMPLATE)
