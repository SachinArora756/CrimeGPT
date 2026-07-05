from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

FIR_TEMPLATE = TemplateDefinition(
    doc_type="fir",
    title="FIRST INFORMATION REPORT",
    subtitle="(Under Section 173 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    form_number="Form No. 24.3",
    legal_reference="Section 173 BNSS",
    sections=[
        TemplateSection(
            id="case_info",
            title="Case Information",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number / Year"),
                FieldDef(key="fir_date", label="Date & Time of FIR"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="district", label="District"),
            ],
        ),
        TemplateSection(
            id="offense_info",
            title="Offence Information",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="offense_type", label="Type of Offence"),
                FieldDef(key="sections_applied", label="Sections Applied (BNS/Special Acts)"),
                FieldDef(key="incident_date", label="Date of Occurrence"),
                FieldDef(key="incident_time", label="Time of Occurrence (Approx.)"),
                FieldDef(key="incident_location", label="Place of Occurrence"),
            ],
        ),
        TemplateSection(
            id="complainant_info",
            title="Complainant / Informant Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="complainant_name", label="Name"),
                FieldDef(key="complainant_father_name", label="Father's / Husband's Name"),
                FieldDef(key="complainant_address", label="Address"),
                FieldDef(key="complainant_contact", label="Contact Number"),
            ],
        ),
        TemplateSection(
            id="accused_info",
            title="Details of Known / Suspected / Unknown Accused",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="accused_details", label="Name(s) & Description"),
            ],
        ),
        TemplateSection(
            id="complaint_details",
            title="Details of Complaint / Information",
            section_type=SectionType.BODY_TEXT,
            content_key="description",
        ),
        TemplateSection(
            id="action_taken",
            title="Action Taken",
            section_type=SectionType.BODY_TEXT,
            content_key="action_taken_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Signature / Thumb Impression of the Complainant", with_date=True),
        SignatureBlock(title="Signature of the Officer Recording FIR", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(FIR_TEMPLATE)
