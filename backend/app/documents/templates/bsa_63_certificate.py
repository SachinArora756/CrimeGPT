from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

BSA_63_CERTIFICATE_TEMPLATE = TemplateDefinition(
    doc_type="bsa_63_certificate",
    title="CERTIFICATE FOR ELECTRONIC RECORD",
    subtitle="(Under Section 63 Bharatiya Sakshya Adhiniyam, 2023)",
    legal_reference="Section 63 BSA 2023",
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
            id="device_details",
            title="Computer / Device Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="device_description", label="Device Description"),
                FieldDef(key="device_make_model", label="Make / Model"),
                FieldDef(key="device_serial", label="Serial / IMEI / MAC"),
                FieldDef(key="device_owner", label="Owner / Custodian"),
                FieldDef(key="device_location", label="Location of Device"),
            ],
        ),
        TemplateSection(
            id="record_details",
            title="Electronic Record Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="record_description", label="Description of Electronic Record"),
                FieldDef(key="record_hash", label="Hash Value (SHA-256)"),
                FieldDef(key="record_date_produced", label="Date Record Produced"),
                FieldDef(key="record_format", label="File Format / Type"),
            ],
        ),
        TemplateSection(
            id="certificate_body",
            title="Certificate",
            section_type=SectionType.BODY_TEXT,
            content_key="bsa63_certificate_body",
        ),
        TemplateSection(
            id="conditions",
            title="Conditions Satisfied (Section 63(2))",
            section_type=SectionType.LIST,
            content_key="bsa63_conditions_list",
        ),
    ],
    signatures=[
        SignatureBlock(title="Person Occupying Responsible Position (Section 63(4))", with_date=True, with_seal=True),
        SignatureBlock(title="Investigating Officer (Witness)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(BSA_63_CERTIFICATE_TEMPLATE)
