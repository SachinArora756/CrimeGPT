"""
TRACE Digital Forensic Examination Report — Section Definitions & LLM Prompts.

Each section defines:
- section_id: unique identifier
- title: heading in the report
- section_number: numbering (1.0, 2.0, etc.)
- is_llm_generated: whether this section needs LLM content generation
- prompt_template: format string for LLM-generated sections
- max_tokens: per-section token budget for LLM
"""

from dataclasses import dataclass, field


@dataclass
class ReportSection:
    section_id: str
    title: str
    section_number: str
    is_llm_generated: bool = False
    prompt_template: str = ""
    max_tokens: int = 1024


TRACE_PREAMBLE = """You are a senior digital forensic examiner writing a formal forensic investigation report
for court submission. Your writing must be:
- Objective and evidence-based — never speculate or assume
- Professional, precise, and formal in tone
- Written in third person passive voice where appropriate
- Following the TRACE (Terms, Record integrity, Analysis, Claims, Exhibits) framework
- Suitable for presentation to judicial authorities

Do NOT use markdown formatting, bullet points with *, or headers with #.
Write in flowing professional prose with numbered lists where appropriate.
Keep language formal and court-admissible. Reference evidence by exhibit number where applicable.
"""


REPORT_SECTIONS: list[ReportSection] = [
    # Section 1: Document Control — data-only
    ReportSection(
        section_id="document_control",
        title="Document Control",
        section_number="1.0",
        is_llm_generated=False,
    ),

    # Section 2: Executive Summary — LLM generated
    ReportSection(
        section_id="executive_summary",
        title="Executive Summary",
        section_number="2.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=TRACE_PREAMBLE + """
Write the Executive Summary section of a forensic investigation report.

CASE CONTEXT:
- FIR Number: {fir_number}
- Offense Type: {offense_type}
- Incident Date: {incident_date}
- Incident Location: {incident_location}
- Complainant: {complainant_name}
- Accused: {accused_details}
- Legal Sections Applied: {sections_applied}
- Investigation Period: {investigation_period}
- Total Evidence Items: {evidence_count}
- Key Findings Summary: {key_findings_summary}

Write 2-3 paragraphs providing a high-level overview of:
1. The nature and scope of the examination conducted
2. The key findings and their significance
3. The overall conclusion of the investigation

Begin with: "This report presents the findings of a digital forensic examination conducted in relation to..."
""",
    ),

    # Section 3: Examiner Identity — data-only
    ReportSection(
        section_id="examiner_identity",
        title="Examiner Identity & Qualifications",
        section_number="3.0",
        is_llm_generated=False,
    ),

    # Section 4: Request, Authority, Purpose, Scope — LLM generated
    ReportSection(
        section_id="request_authority",
        title="Request, Authority, Purpose & Scope",
        section_number="4.0",
        is_llm_generated=True,
        max_tokens=1200,
        prompt_template=TRACE_PREAMBLE + """
Write the "Request, Authority, Purpose & Scope" section of a forensic investigation report.

CASE CONTEXT:
- FIR Number: {fir_number}
- Police Station: {station_id}
- Investigating Officer: {io_name}
- Offense Type: {offense_type}
- Legal Sections: {sections_applied}
- Complainant: {complainant_name}
- Incident Date: {incident_date}
- Case Registration Date: {case_created_at}
- Scope of Evidence: {evidence_types_summary}

Write this section covering:
1. REQUEST: Who requested the examination and when
2. AUTHORITY: Under what legal authority the examination was conducted (reference applicable Indian law — BNS 2023, BNSS 2023, BSA 2023, IT Act 2000)
3. PURPOSE: The specific questions the examination aims to answer
4. SCOPE: What was and was not examined, including any limitations

Use formal language. Reference the FIR number and legal provisions explicitly.
""",
    ),

    # Section 5: Information and Assumptions — LLM generated
    ReportSection(
        section_id="information_assumptions",
        title="Information and Assumptions",
        section_number="5.0",
        is_llm_generated=True,
        max_tokens=800,
        prompt_template=TRACE_PREAMBLE + """
Write the "Information and Assumptions" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Evidence Items: {evidence_count}
- Evidence Types: {evidence_types_summary}
- Case Description: {case_description}
- Stated Assumptions from Investigation: {investigation_notes}

Write this section covering:
1. Information provided to the examiner at the commencement of the examination
2. Any assumptions made during the examination process
3. Constraints or limitations that may affect the findings

State clearly: "The following assumptions have been made in the preparation of this report..."
Include standard forensic assumptions about evidence integrity, device state, and timestamp accuracy.
""",
    ),

    # Section 6: Evidence Integrity Ledger — data-only
    ReportSection(
        section_id="evidence_integrity",
        title="Evidence Integrity Ledger",
        section_number="6.0",
        is_llm_generated=False,
    ),

    # Section 7: Examination Environment — data-only
    ReportSection(
        section_id="examination_environment",
        title="Examination Environment",
        section_number="7.0",
        is_llm_generated=False,
    ),

    # Section 8: Methodology — LLM generated
    ReportSection(
        section_id="methodology",
        title="Methodology",
        section_number="8.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=TRACE_PREAMBLE + """
Write the "Methodology" section of a forensic investigation report following the TRACE framework.

CASE CONTEXT:
- Offense Type: {offense_type}
- Evidence Types Examined: {evidence_types_summary}
- Forensic Tools Used: {tools_used}
- Analysis Techniques Applied: {analysis_techniques}

Write this section covering:
1. The TRACE framework explanation (Terms, Record integrity, Analysis, Claims, Exhibits)
2. Evidence classification tiers used:
   - S1 (Source Tier 1): Direct digital evidence from primary source
   - S2 (Source Tier 2): Corroborated evidence from secondary sources
   - S3 (Source Tier 3): Circumstantial or indirect evidence
   - T1 (Temporal Tier 1): Timestamp from authoritative source
   - T2 (Temporal Tier 2): Derived or calculated timestamp
   - T3 (Temporal Tier 3): Approximate or estimated time
3. The specific methodology applied for each evidence type examined
4. Quality assurance procedures followed

Explain that findings are classified by evidence tier to indicate reliability and provenance.
""",
    ),

    # Section 9: Time/Date Normalisation — LLM generated
    ReportSection(
        section_id="time_normalisation",
        title="Time and Date Normalisation",
        section_number="9.0",
        is_llm_generated=True,
        max_tokens=600,
        prompt_template=TRACE_PREAMBLE + """
Write the "Time and Date Normalisation" section of a forensic investigation report.

CASE CONTEXT:
- Incident Date: {incident_date}
- Incident Time: {incident_time}
- Incident Location: {incident_location}
- Timeline Events Count: {timeline_count}
- Evidence Sources: {evidence_types_summary}

Write this section explaining:
1. The reference timezone used throughout the report (IST — UTC+05:30)
2. How timestamps from different sources were normalised
3. Any clock drift or synchronisation issues identified
4. The notation convention used for all dates/times in the report (DD/MM/YYYY HH:MM:SS IST)

State: "All times referenced in this report are expressed in Indian Standard Time (IST, UTC+05:30) unless explicitly stated otherwise."
""",
    ),

    # Section 10: Findings — LLM generated (largest section)
    ReportSection(
        section_id="findings",
        title="Findings",
        section_number="10.0",
        is_llm_generated=True,
        max_tokens=4000,
        prompt_template=TRACE_PREAMBLE + """
Write the "Findings" section of a forensic investigation report.

CASE CONTEXT:
- FIR Number: {fir_number}
- Offense Type: {offense_type}
- Incident Date: {incident_date}
- Accused: {accused_details}

EVIDENCE EXAMINED:
{evidence_details}

FORENSIC ANALYSIS RESULTS:
{forensic_results}

INVESTIGATION FINDINGS:
{investigation_findings}

EVIDENCE CORRELATIONS:
{correlations}

Write detailed findings organized by evidence item or theme. For each finding:
1. Describe the evidence examined (with exhibit reference)
2. State what was found (factual, objective)
3. Classify the evidence tier (S1/S2/S3 for source, T1/T2/T3 for temporal)
4. Note the forensic significance

Present findings in logical order — typically chronological or by evidence category.
Use language like "Examination revealed...", "Analysis of [exhibit] demonstrated...", "The data indicates..."
Do NOT speculate on intent or motive — only state what the evidence shows.
""",
    ),

    # Section 11: Consolidated Timeline — LLM generated
    ReportSection(
        section_id="consolidated_timeline",
        title="Consolidated Timeline",
        section_number="11.0",
        is_llm_generated=True,
        max_tokens=2000,
        prompt_template=TRACE_PREAMBLE + """
Write the "Consolidated Timeline" section of a forensic investigation report.

CASE CONTEXT:
- Incident Date: {incident_date}
- Incident Time: {incident_time}

TIMELINE EVENTS:
{timeline_events}

EVIDENCE TIMESTAMPS:
{evidence_timestamps}

DIARY ENTRIES:
{diary_entries}

Reconstruct a chronological timeline of events based on all available evidence and records.
Format as a numbered list with:
- Date and time (DD/MM/YYYY HH:MM IST)
- Event description
- Source/evidence reference
- Temporal tier classification (T1/T2/T3)

Begin with: "Based on the examination of all available evidence, the following consolidated timeline has been reconstructed:"

Order strictly chronologically. Mark gaps or uncertainties explicitly.
""",
    ),

    # Section 12: Responses to Instructions — LLM generated
    ReportSection(
        section_id="responses_to_instructions",
        title="Responses to Instructions",
        section_number="12.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=TRACE_PREAMBLE + """
Write the "Responses to Instructions" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- FIR Description: {case_description}
- Key Questions to Address: Based on the offense type and FIR, determine the key investigative questions.

KEY FINDINGS:
{key_findings_summary}

EVIDENCE SUMMARY:
{evidence_summary}

For each investigative question relevant to this case:
1. State the question/instruction
2. Provide the response based solely on evidence examined
3. Reference the supporting evidence (exhibit numbers)
4. State confidence level (High/Medium/Low) based on evidence tier

Use language: "In response to the instruction to determine [X], examination of the evidence reveals..."
If a question cannot be answered from available evidence, state this explicitly with reasons.
""",
    ),

    # Section 13: IOC Summary — LLM generated (conditional on digital crime)
    ReportSection(
        section_id="ioc_summary",
        title="Indicators of Compromise (IOC) Summary",
        section_number="13.0",
        is_llm_generated=True,
        max_tokens=1000,
        prompt_template=TRACE_PREAMBLE + """
Write the "Indicators of Compromise Summary" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Digital Evidence: {digital_evidence_summary}
- Analysis Results: {forensic_results}

If this case involves cyber/digital crime, list identified IOCs in categories:
1. Network Indicators (IP addresses, domains, URLs)
2. Host-Based Indicators (file hashes, registry keys, processes)
3. Email Indicators (sender addresses, subject lines, attachment hashes)
4. Behavioral Indicators (patterns of activity, timestamps)

If no digital IOCs are applicable to this case type, write:
"Given the nature of the offence under examination, no network or host-based indicators of compromise were identified. The evidence in this matter is primarily [physical/documentary/testimonial] in nature."

For each IOC identified, note: the indicator value, where it was found, and its significance.
""",
    ),

    # Section 14: Risk Score Matrix — LLM generated
    ReportSection(
        section_id="risk_score_matrix",
        title="Risk Score Matrix",
        section_number="14.0",
        is_llm_generated=True,
        max_tokens=1000,
        prompt_template=TRACE_PREAMBLE + """
Write the "Risk Score Matrix" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- AI Risk Score: {risk_score}/100
- AI Confidence: {ai_confidence}/100
- Sections Applied: {sections_applied}
- Evidence Strength: {evidence_count} items examined

Provide a risk assessment matrix covering:
1. Likelihood of successful prosecution based on evidence strength
2. Impact severity classification (considering the offense type and applicable sections)
3. Evidence reliability rating (based on chain of custody integrity and evidence tiers)
4. Overall risk score with justification

Present as a structured assessment. Use the following scale:
- Critical (81-100): Overwhelming evidence, high impact
- High (61-80): Strong evidence, significant impact
- Medium (41-60): Moderate evidence, moderate impact
- Low (21-40): Limited evidence, lower impact
- Minimal (0-20): Insufficient evidence

Conclude with an overall assessment statement.
""",
    ),

    # Section 15: Legal Framework — LLM generated
    ReportSection(
        section_id="legal_framework",
        title="Legal Framework",
        section_number="15.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=TRACE_PREAMBLE + """
Write the "Legal Framework" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Sections Applied: {sections_applied}
- Incident Date: {incident_date}

Write this section covering the applicable legal framework in India:
1. Bharatiya Nyaya Sanhita (BNS) 2023 — applicable substantive offence sections
2. Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 — procedural provisions followed
3. Bharatiya Sakshya Adhiniyam (BSA) 2023 — evidentiary standards applied
4. Information Technology Act, 2000 (if applicable to digital evidence)
5. Any other relevant legislation

For each applicable section:
- State the section number and title
- Briefly explain its relevance to this case
- Note the evidentiary requirements it imposes

Conclude with a statement on how the evidence gathered satisfies the legal requirements for the applied sections.
""",
    ),

    # Section 16: Evidentiary Limitations — LLM generated
    ReportSection(
        section_id="evidentiary_limitations",
        title="Evidentiary Limitations",
        section_number="16.0",
        is_llm_generated=True,
        max_tokens=800,
        prompt_template=TRACE_PREAMBLE + """
Write the "Evidentiary Limitations" section of a forensic investigation report.

CASE CONTEXT:
- Evidence Items: {evidence_count}
- Evidence Types: {evidence_types_summary}
- Missing Completeness Items: {missing_items}
- Investigation Notes: {investigation_notes}

Write this section documenting:
1. What could NOT be determined from available evidence
2. Any evidence that was unavailable, damaged, or inaccessible
3. Limitations of tools or techniques employed
4. Any assumptions that could not be verified
5. Gaps in the chain of custody (if any)

Be transparent and professional. State each limitation clearly and explain its potential impact on conclusions.
Begin with: "The following limitations should be noted when considering the findings of this report..."
""",
    ),

    # Section 17: Opinions — LLM generated
    ReportSection(
        section_id="opinions",
        title="Opinions",
        section_number="17.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=TRACE_PREAMBLE + """
Write the "Opinions" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Sections Applied: {sections_applied}
- Accused: {accused_details}

KEY FINDINGS:
{key_findings_summary}

EVIDENCE STRENGTH:
- Total evidence items: {evidence_count}
- AI Confidence Score: {ai_confidence}/100
- Correlations Found: {correlation_count}

Write the expert opinion section. This is where the examiner provides professional conclusions.

Structure as numbered opinions:
1. State each opinion clearly
2. Reference the supporting findings/evidence
3. Express the level of certainty (e.g., "In my opinion...", "The evidence strongly suggests...", "On the balance of probability...")

Important:
- Opinions must be supportable by the findings section
- Clearly distinguish between fact and opinion
- Use appropriate hedging language where certainty is limited
- Do not exceed the bounds of what the evidence supports

Conclude with: "These opinions are offered to the best of my professional knowledge and belief, based solely on the evidence examined."
""",
    ),

    # Section 18: Evidence Disposition — data-only
    ReportSection(
        section_id="evidence_disposition",
        title="Evidence Disposition",
        section_number="18.0",
        is_llm_generated=False,
    ),

    # Section 19: Statement of Truth — data-only
    ReportSection(
        section_id="statement_of_truth",
        title="Statement of Truth",
        section_number="19.0",
        is_llm_generated=False,
    ),

    # Section 20: Appendices — data-only
    ReportSection(
        section_id="appendices",
        title="Appendices",
        section_number="20.0",
        is_llm_generated=False,
    ),
]


def get_llm_sections() -> list[ReportSection]:
    return [s for s in REPORT_SECTIONS if s.is_llm_generated]


def get_data_sections() -> list[ReportSection]:
    return [s for s in REPORT_SECTIONS if not s.is_llm_generated]
