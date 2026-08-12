from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

CONTENT_REMOVAL_TEMPLATE = TemplateDefinition(
    doc_type="content_removal",
    title="NOTICE FOR CONTENT REMOVAL / DISABLEMENT",
    subtitle="(Under Section 79(3)(b) Information Technology Act, 2000 read with IT Rules, 2021)",
    legal_reference="Section 79(3)(b) IT Act r/w IT Rules 2021",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Authorised Officer"),
                FieldDef(key="officer_designation", label="Designation / Rank"),
                FieldDef(key="station_id", label="Police Station / Unit"),
                FieldDef(key="letter_date", label="Date"),
                FieldDef(key="letter_ref", label="Reference No."),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To (Intermediary / Platform)",
            section_type=SectionType.BODY_TEXT,
            content_key="intermediary_addressee",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="sections_applied", label="Sections of Law (BNS/IT Act)"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="content_details",
            title="Details of Unlawful Content",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="content_url", label="URL(s) / Content Identifier"),
                FieldDef(key="content_type", label="Type of Content"),
                FieldDef(key="content_platform", label="Platform / Service"),
                FieldDef(key="content_account", label="Account / User ID"),
                FieldDef(key="content_posted_date", label="Date of Posting (approx.)"),
            ],
        ),
        TemplateSection(
            id="notice_body",
            title="Notice",
            section_type=SectionType.BODY_TEXT,
            content_key="content_removal_body",
        ),
        TemplateSection(
            id="action_required",
            title="Action Required",
            section_type=SectionType.LIST,
            content_key="content_removal_actions",
        ),
        TemplateSection(
            id="compliance_deadline",
            title="Compliance",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="compliance_deadline", label="Compliance Deadline"),
                FieldDef(key="compliance_contact", label="Contact for Compliance Report"),
            ],
        ),
        TemplateSection(
            id="legal_warning",
            title="Legal Consequences",
            section_type=SectionType.LEGAL_FOOTER,
            content_key="content_removal_warning",
        ),
    ],
    signatures=[
        SignatureBlock(title="Authorised Officer (SP rank and above)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(CONTENT_REMOVAL_TEMPLATE)
