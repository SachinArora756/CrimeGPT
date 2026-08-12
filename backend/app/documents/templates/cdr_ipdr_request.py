from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

CDR_IPDR_REQUEST_TEMPLATE = TemplateDefinition(
    doc_type="cdr_ipdr_request",
    title="REQUEST FOR CDR / IPDR / CAF FROM TELECOM SERVICE PROVIDER",
    subtitle="(Under Section 94 BNSS read with Telecom Regulatory Provisions)",
    legal_reference="Section 94 BNSS r/w DoT/TRAI Guidelines",
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
            title="To (Telecom Service Provider)",
            section_type=SectionType.BODY_TEXT,
            content_key="telecom_addressee",
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
            title="Target Mobile / Connection Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="target_mobile", label="Mobile Number(s)"),
                FieldDef(key="target_imei", label="IMEI Number(s)"),
                FieldDef(key="target_account", label="Subscriber Name (if known)"),
                FieldDef(key="data_period", label="Data Period (From-To)"),
            ],
        ),
        TemplateSection(
            id="data_requested",
            title="Records Requested",
            section_type=SectionType.LIST,
            content_key="telecom_data_requested",
        ),
        TemplateSection(
            id="request_body",
            title="Request",
            section_type=SectionType.BODY_TEXT,
            content_key="telecom_request_body",
        ),
        TemplateSection(
            id="urgency",
            title="Urgency / Priority",
            section_type=SectionType.BODY_TEXT,
            content_key="telecom_urgency",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Superintendent of Police (Authorisation)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(CDR_IPDR_REQUEST_TEMPLATE)
