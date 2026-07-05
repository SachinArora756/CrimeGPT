from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

CASE_DIARY_TEMPLATE = TemplateDefinition(
    doc_type="case_diary",
    title="CASE DIARY",
    subtitle="(Under Section 183 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 183 BNSS",
    sections=[
        TemplateSection(
            id="case_ref",
            title="Case Particulars",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="fir_number", label="FIR Number"),
                FieldDef(key="station_id", label="Police Station"),
                FieldDef(key="sections_applied", label="Sections"),
                FieldDef(key="io_name", label="Investigating Officer"),
                FieldDef(key="diary_number", label="Diary Entry No."),
            ],
        ),
        TemplateSection(
            id="entry_details",
            title="Entry Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="entry_date", label="Date"),
                FieldDef(key="entry_time_start", label="Time Commenced"),
                FieldDef(key="entry_time_end", label="Time Concluded"),
                FieldDef(key="places_visited", label="Places Visited"),
            ],
        ),
        TemplateSection(
            id="proceedings",
            title="Proceedings / Actions Taken",
            section_type=SectionType.BODY_TEXT,
            content_key="diary_content",
        ),
        TemplateSection(
            id="results",
            title="Results / Observations",
            section_type=SectionType.BODY_TEXT,
            content_key="observations",
        ),
        TemplateSection(
            id="next_steps",
            title="Next Steps Planned",
            section_type=SectionType.LIST,
            content_key="next_steps_list",
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer", with_date=True),
    ],
    seal_placeholder=False,
)

register_template(CASE_DIARY_TEMPLATE)
