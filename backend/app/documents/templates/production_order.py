from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

PRODUCTION_ORDER_TEMPLATE = TemplateDefinition(
    doc_type="production_order",
    title="NOTICE / SUMMONS TO PRODUCE DOCUMENT OR THING",
    subtitle="(Under Section 94 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 94 BNSS",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Issuing Officer"),
                FieldDef(key="officer_designation", label="Designation"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="letter_date", label="Date"),
                FieldDef(key="letter_ref", label="Reference No."),
            ],
        ),
        TemplateSection(
            id="addressee",
            title="To",
            section_type=SectionType.BODY_TEXT,
            content_key="production_addressee",
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
            id="order_body",
            title="Order",
            section_type=SectionType.BODY_TEXT,
            content_key="production_order_text",
        ),
        TemplateSection(
            id="documents_required",
            title="Documents / Things Required to be Produced",
            section_type=SectionType.LIST,
            content_key="production_items_list",
        ),
        TemplateSection(
            id="production_details",
            title="Production Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="production_date", label="Date of Production"),
                FieldDef(key="production_time", label="Time"),
                FieldDef(key="production_place", label="Place"),
                FieldDef(key="data_period", label="Data Period (From-To)"),
            ],
        ),
        TemplateSection(
            id="legal_warning",
            title="Warning",
            section_type=SectionType.LEGAL_FOOTER,
            content_key="production_warning_text",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer / Competent Authority", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(PRODUCTION_ORDER_TEMPLATE)
