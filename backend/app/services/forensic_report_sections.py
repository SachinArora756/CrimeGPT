"""
PRISM Digital Forensic Investigation Report — Section Definitions & LLM Prompts.

PRISM Framework: Procedural Record of Investigation, Substantiation & Methodology
- P: Provenance — evidence origin, integrity, custody chain
- R: Reconstruction — timeline, event sequence, digital forensics
- I: Interpretation — findings analysis, expert assessment
- S: Substantiation — legal backing, corroboration, evidence grading
- M: Memorandum — conclusions, opinions, professional attestation

Each section defines:
- section_id: unique identifier
- title: heading in the report
- section_number: numbering
- is_llm_generated: whether this section needs LLM content generation
- prompt_template: format string for LLM-generated sections
- max_tokens: per-section token budget for LLM
"""

from dataclasses import dataclass


@dataclass
class ReportSection:
    section_id: str
    title: str
    section_number: str
    is_llm_generated: bool = False
    prompt_template: str = ""
    max_tokens: int = 1024


PRISM_PREAMBLE = """You are a senior digital forensic examiner writing a formal forensic investigation report
for judicial submission under the PRISM framework (Procedural Record of Investigation, Substantiation & Methodology).

Your writing must be:
- Objective and evidence-based — never speculate or assume
- Professional, precise, and formal in tone
- Written in third person passive voice where appropriate
- Suitable for presentation to judicial authorities under Indian law
- Structured for clarity and completeness

Evidence is classified using the following grading system:
- Grade Alpha: Direct primary evidence from the original source
- Grade Beta: Corroborated evidence supported by secondary sources
- Grade Gamma: Circumstantial or indirect evidence requiring further substantiation
- Temporal Verified: Timestamp from authoritative/system source
- Temporal Derived: Computed or calculated timestamp from available data
- Temporal Estimated: Approximate time based on contextual indicators

Do NOT use markdown formatting, bullet points with *, or headers with #.
Write in flowing professional prose with numbered lists where appropriate.
Keep language formal and court-admissible. Reference evidence by exhibit number where applicable.
"""


REPORT_SECTIONS: list[ReportSection] = [
    # ═══════════════════════════════════════════════════
    # PART I — PROVENANCE
    # ═══════════════════════════════════════════════════

    # Section 1: Document Administration — data-only
    ReportSection(
        section_id="document_administration",
        title="Document Administration",
        section_number="1.0",
        is_llm_generated=False,
    ),

    # Section 2: Investigation Mandate & Authority — LLM generated
    ReportSection(
        section_id="mandate_authority",
        title="Investigation Mandate & Authority",
        section_number="2.0",
        is_llm_generated=True,
        max_tokens=1200,
        prompt_template=PRISM_PREAMBLE + """
Write the "Investigation Mandate & Authority" section of a forensic investigation report.

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
1. MANDATE: The formal request and authorization for this forensic examination
2. JURISDICTION: Under what legal authority the examination was conducted (reference applicable Indian law — BNS 2023, BNSS 2023, BSA 2023, IT Act 2000)
3. SCOPE: The boundaries of the examination — what was and was not examined
4. OBJECTIVES: The specific investigative questions this examination seeks to address
5. CONSTRAINTS: Any limitations placed on the examination by circumstances or resources

Use formal language. Reference the FIR number and legal provisions explicitly.
Begin with: "This forensic examination was commissioned under the authority of..."
""",
    ),

    # Section 3: Examiner Declaration — data-only
    ReportSection(
        section_id="examiner_declaration",
        title="Examiner Declaration & Credentials",
        section_number="3.0",
        is_llm_generated=False,
    ),

    # ═══════════════════════════════════════════════════
    # PART II — RECONSTRUCTION
    # ═══════════════════════════════════════════════════

    # Section 4: Case Synopsis — LLM generated
    ReportSection(
        section_id="case_synopsis",
        title="Case Synopsis",
        section_number="4.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=PRISM_PREAMBLE + """
Write the "Case Synopsis" section of a forensic investigation report.

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

Write 3-4 paragraphs providing:
1. A concise overview of the matter under investigation
2. The nature and scope of the forensic examination conducted
3. A summary of principal findings and their investigative significance
4. The overall conclusion drawn from the examination

Begin with: "This report documents the findings of a comprehensive digital forensic examination undertaken in connection with..."
""",
    ),

    # Section 5: Evidence Inventory & Integrity Verification — data-only
    ReportSection(
        section_id="evidence_inventory",
        title="Evidence Inventory & Integrity Verification",
        section_number="5.0",
        is_llm_generated=False,
    ),

    # Section 6: Technical Infrastructure & Instruments — data-only
    ReportSection(
        section_id="technical_infrastructure",
        title="Technical Infrastructure & Instruments",
        section_number="6.0",
        is_llm_generated=False,
    ),

    # Section 7: Analytical Protocol — LLM generated
    ReportSection(
        section_id="analytical_protocol",
        title="Analytical Protocol",
        section_number="7.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=PRISM_PREAMBLE + """
Write the "Analytical Protocol" section of a forensic investigation report following the PRISM framework.

CASE CONTEXT:
- Offense Type: {offense_type}
- Evidence Types Examined: {evidence_types_summary}
- Forensic Tools Used: {tools_used}
- Analysis Techniques Applied: {analysis_techniques}

Write this section covering:
1. The PRISM framework methodology (Provenance, Reconstruction, Interpretation, Substantiation, Memorandum) and how it was applied
2. Evidence grading system used:
   - Grade Alpha: Direct primary evidence from original source
   - Grade Beta: Corroborated evidence from secondary sources
   - Grade Gamma: Circumstantial or indirect evidence
   - Temporal Verified: Timestamp from authoritative source
   - Temporal Derived: Computed or calculated timestamp
   - Temporal Estimated: Approximate or estimated time
3. The specific analytical procedures applied for each evidence type examined
4. Quality assurance and validation procedures followed
5. Peer review or cross-verification steps undertaken

Explain that findings are classified by evidence grade to indicate reliability, provenance, and evidentiary weight.
""",
    ),

    # Section 8: Temporal Synchronization Framework — LLM generated
    ReportSection(
        section_id="temporal_framework",
        title="Temporal Synchronization Framework",
        section_number="8.0",
        is_llm_generated=True,
        max_tokens=600,
        prompt_template=PRISM_PREAMBLE + """
Write the "Temporal Synchronization Framework" section of a forensic investigation report.

CASE CONTEXT:
- Incident Date: {incident_date}
- Incident Time: {incident_time}
- Incident Location: {incident_location}
- Timeline Events Count: {timeline_count}
- Evidence Sources: {evidence_types_summary}

Write this section explaining:
1. The reference timezone used throughout the report (IST — UTC+05:30)
2. How timestamps from disparate sources were synchronized and reconciled
3. Any clock drift, skew, or synchronization discrepancies identified
4. The notation convention used for all temporal references in the report (DD/MM/YYYY HH:MM:SS IST)
5. Confidence assessment for temporal data from different evidence sources

State: "All temporal references in this report are expressed in Indian Standard Time (IST, UTC+05:30) unless explicitly stated otherwise. The notation format employed is DD/MM/YYYY HH:MM:SS."
""",
    ),

    # Section 9: Detailed Examination Findings — LLM generated (largest section)
    ReportSection(
        section_id="examination_findings",
        title="Detailed Examination Findings",
        section_number="9.0",
        is_llm_generated=True,
        max_tokens=3000,
        prompt_template=PRISM_PREAMBLE + """
Write the "Detailed Examination Findings" section of a forensic investigation report.

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

Write detailed findings organized by evidence item or thematic grouping. For each finding:
1. Identify the evidence examined (with exhibit reference number)
2. Describe what was discovered (factual, objective observations only)
3. Assign the evidence grade (Alpha/Beta/Gamma for source, Verified/Derived/Estimated for temporal)
4. Assess the forensic significance in relation to the investigation objectives

Present findings in logical order — by evidence category or chronological sequence.
Use language such as: "Examination of [exhibit] revealed...", "Analysis demonstrated...", "The extracted data indicates..."
Do NOT speculate on intent, motive, or culpability — only state what the evidence objectively shows.
""",
    ),

    # Section 10: Chronological Event Reconstruction — LLM generated
    ReportSection(
        section_id="event_reconstruction",
        title="Chronological Event Reconstruction",
        section_number="10.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=PRISM_PREAMBLE + """
Write the "Chronological Event Reconstruction" section of a forensic investigation report.

CASE CONTEXT:
- Incident Date: {incident_date}
- Incident Time: {incident_time}

TIMELINE EVENTS:
{timeline_events}

EVIDENCE TIMESTAMPS:
{evidence_timestamps}

DIARY ENTRIES:
{diary_entries}

Reconstruct a chronological sequence of events based on all available evidence and investigative records.
Format as a numbered list with:
- Date and time (DD/MM/YYYY HH:MM IST)
- Event description
- Source/evidence reference (exhibit number or record)
- Temporal grade classification (Verified/Derived/Estimated)

Begin with: "Based on the synthesis of all available evidence and investigative records, the following chronological reconstruction has been established:"

Order strictly by time sequence. Mark gaps, uncertainties, or conflicting timestamps explicitly.
Conclude with an assessment of the reconstruction's overall reliability.
""",
    ),

    # ═══════════════════════════════════════════════════
    # PART III — INTERPRETATION
    # ═══════════════════════════════════════════════════

    # Section 11: Investigative Conclusions — LLM generated
    ReportSection(
        section_id="investigative_conclusions",
        title="Investigative Conclusions",
        section_number="11.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=PRISM_PREAMBLE + """
Write the "Investigative Conclusions" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- FIR Description: {case_description}
- Key Questions to Address: Based on the offense type and FIR, determine the key investigative questions.

KEY FINDINGS:
{key_findings_summary}

EVIDENCE SUMMARY:
{evidence_summary}

For each investigative objective relevant to this case:
1. State the objective or question under investigation
2. Present the conclusion based solely on evidence examined
3. Reference the supporting evidence (exhibit numbers and evidence grades)
4. State the confidence level (High/Moderate/Low) with justification

Use language: "In relation to the objective of determining [X], examination of the available evidence establishes..."
If an objective cannot be resolved from available evidence, state this explicitly with reasons.
Conclude with an overall assessment of how completely the investigation objectives were met.
""",
    ),

    # Section 12: Digital Threat Assessment — LLM generated
    ReportSection(
        section_id="threat_assessment",
        title="Digital Threat Assessment",
        section_number="12.0",
        is_llm_generated=True,
        max_tokens=1000,
        prompt_template=PRISM_PREAMBLE + """
Write the "Digital Threat Assessment" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Digital Evidence: {digital_evidence_summary}
- Analysis Results: {forensic_results}

If this case involves cyber/digital crime, identify and categorize digital threat indicators:
1. Network Indicators (IP addresses, domains, URLs, communication patterns)
2. System Indicators (file hashes, registry modifications, process anomalies)
3. Communication Indicators (sender addresses, subject patterns, attachment signatures)
4. Behavioral Indicators (access patterns, timing anomalies, data exfiltration signatures)

If no digital threat indicators are applicable to this case type, write:
"Given the nature of the offence under examination, no network or system-based threat indicators were identified. The evidentiary material in this matter is primarily [physical/documentary/testimonial] in character, and digital threat assessment is not applicable."

For each indicator identified, document: the indicator value, the source from which it was extracted, and its significance to the investigation.
""",
    ),

    # Section 13: Evidence Strength Evaluation — LLM generated
    ReportSection(
        section_id="strength_evaluation",
        title="Evidence Strength Evaluation",
        section_number="13.0",
        is_llm_generated=True,
        max_tokens=1000,
        prompt_template=PRISM_PREAMBLE + """
Write the "Evidence Strength Evaluation" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- AI Risk Score: {risk_score}/100
- AI Confidence: {ai_confidence}/100
- Sections Applied: {sections_applied}
- Evidence Volume: {evidence_count} items examined

Provide a structured evaluation of evidentiary strength covering:
1. Prosecution viability based on evidence weight and admissibility
2. Severity classification considering the offense type and applicable legal provisions
3. Evidence reliability assessment based on provenance integrity and grading distribution
4. Overall evidentiary strength score with detailed justification

Apply the following assessment scale:
- Compelling (81-100): Overwhelming admissible evidence of high grade
- Strong (61-80): Substantial evidence with clear probative value
- Moderate (41-60): Adequate evidence requiring corroboration in key areas
- Limited (21-40): Insufficient evidence for principal allegations
- Inadequate (0-20): Evidence does not meet minimum evidentiary threshold

Conclude with a summary statement on the overall strength of the case as supported by forensic evidence.
""",
    ),

    # ═══════════════════════════════════════════════════
    # PART IV — SUBSTANTIATION
    # ═══════════════════════════════════════════════════

    # Section 14: Legal Compliance Framework — LLM generated
    ReportSection(
        section_id="legal_compliance",
        title="Legal Compliance Framework",
        section_number="14.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=PRISM_PREAMBLE + """
Write the "Legal Compliance Framework" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Sections Applied: {sections_applied}
- Incident Date: {incident_date}

Write this section documenting the applicable legal framework in India:
1. Bharatiya Nyaya Sanhita (BNS) 2023 — applicable substantive offence provisions
2. Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 — procedural safeguards followed
3. Bharatiya Sakshya Adhiniyam (BSA) 2023 — evidentiary standards and admissibility criteria
4. Information Technology Act, 2000 (if applicable to digital evidence)
5. Any other relevant legislation or regulatory framework

For each applicable provision:
- State the section number and its title
- Explain its relevance and applicability to this case
- Note the evidentiary requirements it imposes
- Assess whether the gathered evidence satisfies those requirements

Conclude with a compliance statement on how the evidence collected and the examination procedures followed conform to applicable legal requirements.
""",
    ),

    # Section 15: Methodological Constraints — LLM generated
    ReportSection(
        section_id="methodological_constraints",
        title="Methodological Constraints & Limitations",
        section_number="15.0",
        is_llm_generated=True,
        max_tokens=800,
        prompt_template=PRISM_PREAMBLE + """
Write the "Methodological Constraints & Limitations" section of a forensic investigation report.

CASE CONTEXT:
- Evidence Items: {evidence_count}
- Evidence Types: {evidence_types_summary}
- Missing Completeness Items: {missing_items}
- Investigation Notes: {investigation_notes}

Write this section documenting:
1. What could NOT be determined from available evidence and why
2. Any evidence that was unavailable, degraded, corrupted, or inaccessible
3. Limitations inherent in the tools, techniques, or methodologies employed
4. Assumptions that could not be independently verified
5. Gaps in the provenance chain or integrity verification (if any)
6. Environmental or circumstantial factors that may affect the reliability of findings

Be transparent and professional. State each constraint clearly and explain its potential impact on the conclusions drawn.
Begin with: "The following methodological constraints and limitations should be considered when evaluating the findings and conclusions of this report..."
""",
    ),

    # Section 16: Preliminary Information & Working Hypotheses — LLM generated
    ReportSection(
        section_id="preliminary_information",
        title="Preliminary Information & Working Hypotheses",
        section_number="16.0",
        is_llm_generated=True,
        max_tokens=800,
        prompt_template=PRISM_PREAMBLE + """
Write the "Preliminary Information & Working Hypotheses" section of a forensic investigation report.

CASE CONTEXT:
- Offense Type: {offense_type}
- Evidence Items: {evidence_count}
- Evidence Types: {evidence_types_summary}
- Case Description: {case_description}
- Stated Information from Investigation: {investigation_notes}

Write this section covering:
1. Information provided to the examiner prior to and at the commencement of the examination
2. Working hypotheses formulated during the examination process
3. How these hypotheses were tested against the evidence
4. Assumptions made during the examination and their basis
5. Standard forensic assumptions regarding evidence integrity, device state, and temporal accuracy

State clearly: "The following information was provided at the outset of the examination, and the following working hypotheses were formulated and tested during the investigative process..."
""",
    ),

    # ═══════════════════════════════════════════════════
    # PART V — MEMORANDUM
    # ═══════════════════════════════════════════════════

    # Section 17: Expert Professional Opinion — LLM generated
    ReportSection(
        section_id="professional_opinion",
        title="Expert Professional Opinion",
        section_number="17.0",
        is_llm_generated=True,
        max_tokens=1500,
        prompt_template=PRISM_PREAMBLE + """
Write the "Expert Professional Opinion" section of a forensic investigation report.

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

Write the expert opinion section. This is where the examiner provides professional conclusions based on the evidence.

Structure as numbered opinions:
1. State each opinion clearly and unambiguously
2. Reference the specific findings and evidence supporting the opinion
3. Express the degree of certainty using appropriate language (e.g., "In my professional opinion...", "The evidence compellingly demonstrates...", "On the balance of available evidence...")

Important:
- Opinions must be directly supportable by the findings documented in this report
- Clearly distinguish between established fact and professional opinion
- Use appropriate qualifying language where certainty is bounded
- Do not exceed the bounds of what the evidence objectively supports
- Address each investigative objective where an opinion can be offered

Conclude with: "These opinions are provided to the best of my professional knowledge, competence, and belief, based solely upon the evidence examined and the analytical procedures applied in this investigation."
""",
    ),

    # Section 18: Evidence Handling & Disposition — data-only
    ReportSection(
        section_id="evidence_disposition",
        title="Evidence Handling & Disposition",
        section_number="18.0",
        is_llm_generated=False,
    ),

    # Section 19: Declaration & Attestation — data-only
    ReportSection(
        section_id="declaration_attestation",
        title="Declaration & Attestation",
        section_number="19.0",
        is_llm_generated=False,
    ),

    # Section 20: Supporting Annexures — data-only
    ReportSection(
        section_id="annexures",
        title="Supporting Annexures",
        section_number="20.0",
        is_llm_generated=False,
    ),
]


def get_llm_sections() -> list[ReportSection]:
    return [s for s in REPORT_SECTIONS if s.is_llm_generated]


def get_data_sections() -> list[ReportSection]:
    return [s for s in REPORT_SECTIONS if not s.is_llm_generated]
