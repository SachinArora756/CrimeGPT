from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

DATA_PRESERVATION_TEMPLATE = TemplateDefinition(
    doc_type="data_preservation",
    title="REQUEST FOR DATA PRESERVATION",
    subtitle="(Under Section 67C Information Technology Act, 2000 read with IT Rules, 2021)",
    legal_reference="Section 67C IT Act 2000",
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
            title="To (Intermediary / Service Provider)",
            section_type=SectionType.BODY_TEXT,
            content_key="preservation_addressee",
        ),
        TemplateSection(
            id="case_ref",
            title="Case Reference",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="offense_type", label="Nature of Offence"),
            ],
        ),
        TemplateSection(
            id="request_body",
            title="Preservation Request",
            section_type=SectionType.BODY_TEXT,
            content_key="preservation_request_body",
        ),
        TemplateSection(
            id="data_details",
            title="Data / Records to be Preserved",
            section_type=SectionType.LIST,
            content_key="preservation_data_list",
        ),
        TemplateSection(
            id="account_details",
            title="Target Account / Identifier",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="target_account", label="Account / User ID / Number"),
                FieldDef(key="target_platform", label="Platform / Service"),
                FieldDef(key="data_period", label="Data Period (From-To)"),
                FieldDef(key="preservation_duration", label="Preservation Duration Requested"),
            ],
        ),
        TemplateSection(
            id="legal_note",
            title="Legal Note",
            section_type=SectionType.LEGAL_FOOTER,
            content_key="preservation_legal_note",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(DATA_PRESERVATION_TEMPLATE)
