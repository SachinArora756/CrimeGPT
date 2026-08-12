from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

FSL_FORWARDING_TEMPLATE = TemplateDefinition(
    doc_type="fsl_forwarding",
    title="FORWARDING LETTER TO FORENSIC SCIENCE LABORATORY",
    subtitle="(Under Section 176/349 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 176/349 BNSS",
    sections=[
        TemplateSection(
            id="header_info",
            title="From",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="from_officer", label="Forwarding Officer"),
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
            content_key="fsl_addressee",
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
            id="brief_facts",
            title="Brief Facts of Case",
            section_type=SectionType.BODY_TEXT,
            content_key="fsl_brief_facts",
        ),
        TemplateSection(
            id="exhibits",
            title="Exhibits Forwarded",
            section_type=SectionType.LIST,
            content_key="fsl_exhibits_list",
        ),
        TemplateSection(
            id="examination_required",
            title="Examination Required / Questions for Expert",
            section_type=SectionType.LIST,
            content_key="fsl_questions_list",
        ),
        TemplateSection(
            id="seal_details",
            title="Seal / Packing Details",
            section_type=SectionType.BODY_TEXT,
            content_key="fsl_seal_details",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True, with_seal=True),
        SignatureBlock(title="Station House Officer (endorsement)", with_date=True, with_seal=True),
    ],
    seal_placeholder=True,
)

register_template(FSL_FORWARDING_TEMPLATE)
