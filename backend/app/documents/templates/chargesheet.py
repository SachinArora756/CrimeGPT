from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

CHARGESHEET_TEMPLATE = TemplateDefinition(
    doc_type="chargesheet",
    title="CHARGE SHEET",
    subtitle="(Under Section 193 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    form_number="Form No. 25.57(1)",
    legal_reference="Section 193 BNSS",
    sections=[
        TemplateSection(
            id="case_info",
            title="Case Particulars",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number / Year"),
                FieldDef(key="fir_date", label="Date of FIR"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="chargesheet_date", label="Date of Filing Charge Sheet"),
                FieldDef(key="court_name", label="Court to which submitted"),
            ],
        ),
        TemplateSection(
            id="offense_details",
            title="Offence Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="offense_type", label="Nature of Offence"),
                FieldDef(key="sections_applied", label="Sections of Law"),
                FieldDef(key="incident_date", label="Date of Occurrence"),
                FieldDef(key="incident_location", label="Place of Occurrence"),
            ],
        ),
        TemplateSection(
            id="accused_particulars",
            title="Particulars of the Accused Person(s)",
            section_type=SectionType.LIST,
            content_key="accused_list",
        ),
        TemplateSection(
            id="complainant_info",
            title="Particulars of Complainant / Informant",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="complainant_name", label="Name"),
                FieldDef(key="complainant_address", label="Address"),
            ],
        ),
        TemplateSection(
            id="brief_facts",
            title="Brief Facts of the Case",
            section_type=SectionType.BODY_TEXT,
            content_key="description",
        ),
        TemplateSection(
            id="evidence_summary",
            title="Evidence / Material Objects",
            section_type=SectionType.LIST,
            content_key="evidence_list",
        ),
        TemplateSection(
            id="witness_list",
            title="List of Witnesses",
            section_type=SectionType.LIST,
            content_key="witnesses_list",
        ),
        TemplateSection(
            id="documents_list",
            title="List of Documents Relied Upon",
            section_type=SectionType.LIST,
            content_key="documents_relied",
        ),
        TemplateSection(
            id="result",
            title="Result of Investigation",
            section_type=SectionType.BODY_TEXT,
            content_key="investigation_result",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Officer In-Charge, Police Station", with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(CHARGESHEET_TEMPLATE)
