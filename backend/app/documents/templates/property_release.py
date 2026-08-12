from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

PROPERTY_RELEASE_TEMPLATE = TemplateDefinition(
    doc_type="property_release",
    title="ORDER FOR RELEASE OF PROPERTY / CASE PROPERTY",
    subtitle="(Under Section 451/457 BNSS read with Court Orders)",
    legal_reference="Section 451/457 BNSS",
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
            id="court_order",
            title="Court Order Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="court_order_date", label="Date of Court Order"),
                FieldDef(key="court_name", label="Court Name"),
                FieldDef(key="court_order_no", label="Order Number"),
            ],
        ),
        TemplateSection(
            id="property_details",
            title="Property to be Released",
            section_type=SectionType.LIST,
            content_key="release_property_list",
        ),
        TemplateSection(
            id="recipient",
            title="Released To",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="release_to_name", label="Name"),
                FieldDef(key="release_to_address", label="Address"),
                FieldDef(key="release_to_relation", label="Relation / Capacity"),
                FieldDef(key="release_to_id", label="ID Proof"),
            ],
        ),
        TemplateSection(
            id="conditions",
            title="Conditions of Release",
            section_type=SectionType.BODY_TEXT,
            content_key="release_conditions",
        ),
    ],
    signatures=[
        SignatureBlock(title="Station House Officer / IO", with_date=True, with_seal=True),
        SignatureBlock(title="Malkhana In-charge", with_date=True),
        SignatureBlock(title="Recipient (Acknowledgement)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(PROPERTY_RELEASE_TEMPLATE)
