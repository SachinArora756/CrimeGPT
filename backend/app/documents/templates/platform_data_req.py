from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

PLATFORM_DATA_REQ_TEMPLATE = TemplateDefinition(
    doc_type="platform_data_req",
    title="REQUEST FOR SUBSCRIBER / USER DATA FROM INTERMEDIARY",
    subtitle="(Under Section 94 BNSS read with Section 79 IT Act, 2000 & IT Rules, 2021)",
    legal_reference="Section 94 BNSS r/w Section 79 IT Act",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Requesting Officer"),
                FieldDef(key="officer_designation", label="Designation"),
                FieldDef(key="station_id", label="Police Station / Cyber Cell"),
                FieldDef(key="letter_date", label="Date"),
                FieldDef(key="letter_ref", label="Reference No."),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To (Platform / Service Provider)",
            section_type=SectionType.BODY_TEXT,
            content_key="platform_addressee",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="fir_date", label="FIR Date"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="target_details",
            title="Target Account / Identifier",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="target_account", label="Account / Username / ID"),
                FieldDef(key="target_platform", label="Platform Name"),
                FieldDef(key="target_email_phone", label="Associated Email / Phone"),
                FieldDef(key="data_period", label="Data Period (From-To)"),
            ],
        ),
        TemplateSection(
            id="data_requested",
            title="Data / Information Requested",
            section_type=SectionType.LIST,
            content_key="platform_data_requested",
        ),
        TemplateSection(
            id="request_body",
            title="Request",
            section_type=SectionType.BODY_TEXT,
            content_key="platform_request_body",
        ),
        TemplateSection(
            id="delivery_info",
            title="Delivery",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="compliance_deadline", label="Required By"),
                FieldDef(key="compliance_contact", label="Contact Officer / Email"),
            ],
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Station House Officer / SP (endorsement)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(PLATFORM_DATA_REQ_TEMPLATE)
