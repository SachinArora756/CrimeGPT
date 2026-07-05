from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

COURT_LETTER_TEMPLATE = TemplateDefinition(
    doc_type="court_letter",
    title="FORWARDING LETTER TO COURT",
    subtitle="(For Submission of Charge Sheet / Remand Application / Other Applications)",
    legal_reference="Section 193/194 BNSS",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Officer In-Charge"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="letter_date", label="Date"),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To",
            section_type=SectionType.BODY_TEXT,
            content_key="court_addressee",
        ),
        TemplateSection(
            id="subject",
            title="Subject",
            section_type=SectionType.BODY_TEXT,
            content_key="subject_text",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="fir_date", label="Date of FIR"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="accused_details", label="Accused Person(s)"),
            ],
        ),
        TemplateSection(
            id="body",
            title="Respectfully Submitted",
            section_type=SectionType.BODY_TEXT,
            content_key="letter_body",
        ),
        TemplateSection(
            id="enclosures",
            title="Enclosures",
            section_type=SectionType.LIST,
            content_key="enclosure_list",
        ),
        TemplateSection(
            id="prayer",
            title="Prayer",
            section_type=SectionType.BODY_TEXT,
            content_key="prayer_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Station House Officer (Verification)", with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(COURT_LETTER_TEMPLATE)
