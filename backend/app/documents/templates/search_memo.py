from app.documents.registry import (
    TemplateDefinition, TemplateSection, FieldDef, SignatureBlock, SectionType, register_template
)

SEARCH_MEMO_TEMPLATE = TemplateDefinition(
    doc_type="search_memo",
    title="SEARCH MEMO / PANCHNAMA",
    subtitle="(Under Section 185-190 Bharatiya Nagarik Suraksha Sanhita, 2023)",
    legal_reference="Section 185-190 BNSS",
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
            id="search_details",
            title="Search Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="search_date", label="Date of Search"),
                FieldDef(key="search_time_start", label="Time Commenced"),
                FieldDef(key="search_time_end", label="Time Concluded"),
                FieldDef(key="search_place", label="Place Searched (Full Address)"),
                FieldDef(key="search_warrant_no", label="Search Warrant Number (if applicable)"),
            ],
        ),
        TemplateSection(
            id="grounds",
            title="Grounds for Search (Recorded in Writing Before Search)",
            section_type=SectionType.BODY_TEXT,
            content_key="search_grounds",
        ),
        TemplateSection(
            id="articles_found",
            title="Articles / Items Found and Seized During Search",
            section_type=SectionType.LIST,
            content_key="items_found",
        ),
        TemplateSection(
            id="video_note",
            title="Video Recording",
            section_type=SectionType.BODY_TEXT,
            content_key="video_recording_note",
        ),
        TemplateSection(
            id="occupant",
            title="Occupant / Owner Details",
            section_type=SectionType.METADATA_TABLE,
            fields=[
                FieldDef(key="occupant_name", label="Name of Occupant/Owner"),
                FieldDef(key="occupant_present", label="Present During Search (Yes/No)"),
            ],
            mandatory=False,
        ),
    ],
    signatures=[
        SignatureBlock(title="Investigating Officer (Name, Rank, Belt No.)", with_date=True, with_seal=True),
        SignatureBlock(title="Independent Witness 1 (Name & Address)", with_date=True),
        SignatureBlock(title="Independent Witness 2 (Name & Address)", with_date=True),
        SignatureBlock(title="Occupant / Owner (if present)", with_date=True),
    ],
    seal_placeholder=True,
)

register_template(SEARCH_MEMO_TEMPLATE)
