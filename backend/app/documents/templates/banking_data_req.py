from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

BANKING_DATA_REQ_TEMPLATE = TemplateDefinition(
    doc_type="banking_data_req",
    title="REQUEST FOR BANKING / FINANCIAL DATA",
    subtitle="(Under Section 94 BNSS read with RBI Directions & Section 94 Banking Regulation Act)",
    legal_reference="Section 94 BNSS r/w Banking Laws",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Requesting Officer"),
                FieldDef(key="officer_designation", label="Designation"),
                FieldDef(key="station_id", label="Police Station / Unit"),
                FieldDef(key="letter_date", label="Date"),
                FieldDef(key="letter_ref", label="Reference No."),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To (Bank / Financial Institution / Payment Service)",
            section_type=SectionType.BODY_TEXT,
            content_key="bank_addressee",
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
            id="account_details",
            title="Target Account Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="bank_account_no", label="Account Number / UPI ID"),
                FieldDef(key="bank_name", label="Bank / Payment Service Name"),
                FieldDef(key="bank_branch", label="Branch (if known)"),
                FieldDef(key="bank_holder_name", label="Account Holder Name (if known)"),
                FieldDef(key="data_period", label="Transaction Period (From-To)"),
            ],
        ),
        TemplateSection(
            id="data_requested",
            title="Data / Records Requested",
            section_type=SectionType.LIST,
            content_key="banking_data_requested",
        ),
        TemplateSection(
            id="request_body",
            title="Request",
            section_type=SectionType.BODY_TEXT,
            content_key="banking_request_body",
        ),
        TemplateSection(
            id="freeze_request",
            title="Account Freeze / Lien (if applicable)",
            section_type=SectionType.BODY_TEXT,
            content_key="bank_freeze_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Station House Officer / SP (endorsement)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(BANKING_DATA_REQ_TEMPLATE)
