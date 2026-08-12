from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.user import User
from app.documents.registry import TemplateDefinition, TemplateSection, SectionType


def _format_date(d) -> str:
    if isinstance(d, datetime):
        return d.strftime("%d/%m/%Y")
    if isinstance(d, date):
        return d.strftime("%d/%m/%Y")
    if d:
        return str(d)
    return "---"


def _format_list(items: list | None) -> list[str]:
    if not items:
        return []
    result = []
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            parts = []
            for k, v in item.items():
                if v and k != "id":
                    parts.append(f"{k}: {v}")
            result.append(f"{i}. {', '.join(parts)}")
        else:
            result.append(f"{i}. {item}")
    return result


async def bind_template_data(
    template: TemplateDefinition,
    case: Case,
    db: AsyncSession,
    additional_context: str | None = None,
) -> dict:
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.case_id == case.id)
    )
    evidence_list = list(evidence_result.scalars().all())

    officer = None
    if case.assigned_officer_id:
        officer_result = await db.execute(
            select(User).where(User.id == case.assigned_officer_id)
        )
        officer = officer_result.scalar_one_or_none()

    now = datetime.utcnow()

    data = {
        "fir_number": case.fir_number or "---",
        "fir_date": _format_date(case.created_at),
        "station_id": case.station_id or "---",
        "district": "---",
        "offense_type": case.offense_type or "---",
        "sections_applied": ", ".join(case.sections_applied) if case.sections_applied else "---",
        "incident_date": _format_date(case.incident_date),
        "incident_time": case.incident_time or "---",
        "incident_location": case.incident_location or "---",
        "complainant_name": case.complainant_name or "---",
        "complainant_father_name": "---",
        "complainant_address": case.complainant_address or "---",
        "complainant_contact": case.complainant_contact or "---",
        "accused_name": case.accused_name or "Unknown",
        "accused_details": _build_accused_details(case),
        "accused_father": "---",
        "accused_age": "---",
        "accused_address": "---",
        "accused_occupation": "---",
        "accused_id_marks": "---",
        "description": case.description or "---",

        "chargesheet_date": _format_date(now),
        "court_name": "The Court of the Chief Judicial Magistrate",
        "arrest_date": _format_date(now),
        "arrest_time": now.strftime("%H:%M"),
        "arrest_place": case.incident_location or "---",
        "seizure_date": _format_date(now),
        "seizure_time": now.strftime("%H:%M"),
        "seizure_place": case.incident_location or "---",
        "search_date": _format_date(now),
        "search_time_start": "---",
        "search_time_end": "---",
        "search_place": case.incident_location or "---",
        "search_warrant_no": "---",

        "from_officer": officer.full_name if officer else "---",
        "letter_date": _format_date(now),
        "letter_ref": f"Ref: {case.fir_number}",
        "io_name": officer.full_name if officer else "---",
        "entry_date": _format_date(now),
        "entry_time_start": "---",
        "entry_time_end": "---",
        "places_visited": case.incident_location or "---",
        "diary_number": "---",

        "person_name": case.complainant_name or "---",
        "person_age": "---",
        "person_gender": "---",
        "person_role": "Victim",
        "recording_date": _format_date(now),
        "recording_time": now.strftime("%H:%M"),
        "recording_place": case.station_id or "---",
        "recording_officer": officer.full_name if officer else "---",
        "audio_video": "Yes (as per BNSS Section 179(4))",

        "witness_name": "---",
        "witness_father": "---",
        "witness_age": "---",
        "witness_address": "---",
        "witness_occupation": "---",
        "witness_contact": "---",
        "witness_relation": "---",

        "notice_to_name": case.accused_name or "---",
        "notice_to_address": "---",
        "appearance_date": "---",
        "appearance_time": "---",
        "appearance_place": case.station_id or "---",

        "informed_person_name": "---",
        "informed_person_relation": "---",
        "informed_person_contact": "---",
        "occupant_name": "---",
        "occupant_present": "---",

        # New document type fields
        "custody_type": "Police Custody",
        "custody_days_requested": "---",
        "patient_condition": "---",
        "injuries_description": "---",
        "accused_height": "---",
        "accused_build": "---",
        "accused_complexion": "---",
        "accused_clothing": "---",
        "id_marks_description": "---",
        "parade_date": _format_date(now),
        "parade_time": "---",
        "parade_place": case.station_id or "---",
        "magistrate_name": "---",
        "person_from_whom_seized": case.accused_name or "---",
        "articles_condition": "Articles seized as is where is basis. Condition noted at time of seizure.",

        # Body text content keys
        "action_taken_text": f"FIR registered. Investigation taken up. Case assigned to investigating officer.",
        "grounds_of_arrest": f"The accused is reasonably suspected of having committed the offence of {case.offense_type or 'the registered offence'} punishable under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023, based on the complaint and evidence collected during investigation.",
        "rights_communicated": "The arrested person has been informed of:\n1. The full particulars of the offence for which arrested (Section 39(1) BNSS)\n2. Right to consult and be defended by a legal practitioner of choice (Section 39(2) BNSS)\n3. Right to have a nominated person informed of the arrest (Section 39(3) BNSS)\n4. Right to be released on bail if offence is bailable (Section 39(4) BNSS)\n5. Right to be produced before Magistrate within 24 hours (Section 37 BNSS)",
        "injuries_noted": "No visible injuries noted at the time of arrest. / Injuries noted: ---",
        "seizure_circumstances": f"During the course of investigation of FIR No. {case.fir_number}, the following articles were found and seized from the place of occurrence in the presence of independent witnesses.",
        "video_recording_note": "The entire process has been video-recorded as mandated under Section 185(5) BNSS.",
        "search_grounds": f"Reasonable grounds exist to believe that articles/documents necessary for the investigation of FIR No. {case.fir_number} (under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'}) are present at the specified location and cannot be obtained without undue delay.",
        "witness_statement_text": additional_context or "---",
        "caution_text": "Note: This statement has been recorded under Section 161 BNSS. The witness is cautioned that making a false statement is punishable under Section 229 BNS. The statement is not signed as per Section 180 BNSS.",
        "notice_body_text": f"Whereas in connection with FIR No. {case.fir_number} registered at Police Station {case.station_id or '---'} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023, your presence is required for the purpose of investigation. You are hereby directed to appear at the time and place mentioned below.",
        "non_compliance_warning": "WARNING: Non-compliance with this notice may result in arrest under Section 35(3) of BNSS 2023.",
        "addressee_text": "The Medical Officer,\nDistrict Hospital / Government Hospital\n---",
        "request_text": f"Sir/Madam,\n\nYou are requested to kindly conduct medical examination of the person named below, who is being sent herewith in connection with FIR No. {case.fir_number} registered at this police station under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023.\n\nKindly furnish the medical report at the earliest.",
        "court_addressee": "The Hon'ble Court of the Chief Judicial Magistrate\n---",
        "subject_text": f"Submission of Charge Sheet in FIR No. {case.fir_number} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} BNS 2023",
        "letter_body": f"Respectfully submitted that in connection with FIR No. {case.fir_number} dated {_format_date(case.created_at)}, registered at Police Station {case.station_id or '---'}, investigation has been conducted and completed. The charge sheet along with all relevant documents is hereby submitted for the kind consideration of the Hon'ble Court.",
        "prayer_text": "It is humbly prayed that the Hon'ble Court may kindly take cognizance of the offence and proceed according to law.",
        "investigation_result": f"Investigation reveals that the accused committed the offence of {case.offense_type or '---'} punishable under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023. Sufficient evidence has been collected to establish the case.",
        "diary_content": additional_context or "Investigation proceedings for the day.",
        "observations": "---",
        "treatment_addressee_text": "The Medical Superintendent / Duty Medical Officer,\nDistrict Hospital / Government Hospital\n---",
        "treatment_request_text": f"Sir/Madam,\n\nYou are requested to kindly provide necessary medical treatment to the person named below, who has sustained injuries in connection with FIR No. {case.fir_number} registered at this police station under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023.\n\nKindly admit the patient if required and furnish the medical report at the earliest.",
        "remand_grounds": f"Respectfully submitted that the accused has been arrested in connection with FIR No. {case.fir_number} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023. The investigation is at a crucial stage and the remand of the accused is necessary for the following reasons:\n\n1. Recovery of weapon/property used in the commission of the offence is yet to be effected.\n2. Identification of co-accused persons and their role is under investigation.\n3. The accused may tamper with evidence or influence witnesses if released.\n4. Further forensic examination and confrontation with witnesses is required.",
        "investigation_progress": f"Investigation of FIR No. {case.fir_number} is in progress. Evidence has been collected and statements of witnesses have been recorded. Further investigation is required to establish the complete chain of events.",
        "remand_prayer_text": "It is therefore most humbly prayed that the Hon'ble Court may kindly grant police custody remand of the accused for the period requested to facilitate further investigation in the interest of justice.",
        "custody_grounds": f"Respectfully submitted that the accused arrested in FIR No. {case.fir_number} needs to be remanded to judicial custody as the initial investigation has been completed but the trial is yet to commence. The accused may flee from justice or tamper with evidence if released. It is in the interest of justice that the accused be remanded to judicial custody.",
        "custody_prayer_text": "It is therefore most humbly prayed that the Hon'ble Court may kindly remand the accused to judicial custody for the period deemed appropriate in the interest of justice.",
        "seizure_receipt_acknowledgment": f"This is to acknowledge that the above-mentioned articles have been seized from the undersigned person in connection with FIR No. {case.fir_number} by the Investigating Officer in the presence of independent witnesses. A copy of this receipt has been provided to the person from whom the property has been seized.",
        "panchanama_body_text": f"Today on {_format_date(now)} at the Police Station {case.station_id or '---'}, the personal search of the accused was conducted in the presence of two independent witnesses as per the provisions of Section 53 BNSS. The accused was informed of the grounds of search and the search was conducted with due regard to decency. All articles found on the person of the accused have been duly noted and sealed where required.",
        "identification_result": "---",
        "parade_observations": "The identification parade was conducted in a fair and impartial manner under the supervision of the Presiding Magistrate. The accused was given full liberty to choose a position among the panel members. All precautions were taken to ensure that the identifying witness had no opportunity to see the accused prior to the parade.",

        # List content keys
        "accused_list": _format_list(case.accused_persons) or [f"1. {case.accused_name or 'Unknown'}"],
        "evidence_list": _build_evidence_list(evidence_list),
        "witnesses_list": _build_witnesses_list(case),
        "documents_relied": _build_documents_list(case, evidence_list),
        "seized_articles": _build_evidence_list(evidence_list) or ["(To be listed by the investigating officer)"],
        "items_found": ["(To be listed by the investigating officer)"],
        "examination_types": [
            "General physical examination",
            "Documentation of injuries (if any)",
            "Collection of samples as required for investigation",
            "Medical opinion on nature and duration of injuries",
        ],
        "enclosure_list": _build_enclosures(case, evidence_list),
        "next_steps_list": ["Continue investigation as per case requirements"],
        "treatment_required_list": [
            "Emergency medical treatment as required",
            "Documentation and treatment of injuries",
            "X-ray / CT scan if required",
            "Medico-legal certificate (MLC)",
            "Opinion on nature, duration and cause of injuries",
        ],
        "articles_on_person": ["(To be listed by the investigating officer during personal search)"],
        "identification_panel": [
            "1. Accused (position to be chosen by accused)",
            "2-10. Panel members of similar age, build, and appearance (minimum 9 persons)",
        ],

        # --- Section 94 BNSS Production Order ---
        "officer_designation": officer.full_name if officer else "Investigating Officer",
        "production_addressee": "To,\n(Name and Address of the person / entity in possession of document or thing)\n---",
        "production_order_text": f"WHEREAS, in the course of investigation of FIR No. {case.fir_number} registered at Police Station {case.station_id or '---'} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023, it appears that certain documents/electronic records/things are necessary for the purposes of investigation.\n\nYou are hereby required to produce the below-mentioned documents/things/electronic records at the time and place specified, failing which proceedings as per law may be initiated.",
        "production_items_list": [
            "(Specify exact documents / electronic records / things required)",
            "e.g., CCTV footage from [date] to [date]",
            "e.g., Server logs / IP logs for the specified period",
            "e.g., Transaction records / account statements",
        ],
        "production_date": _format_date(now),
        "production_time": "---",
        "production_place": case.station_id or "---",
        "data_period": "---",
        "production_warning_text": "Non-compliance with this notice/order is punishable under Section 223 of Bharatiya Nyaya Sanhita, 2023 (intentional omission to produce document to public servant). You are advised to comply with this notice within the stipulated time.",

        # --- IT Act Content Removal ---
        "intermediary_addressee": "The Nodal Officer / Grievance Officer,\n(Name of Intermediary / Platform)\n(Registered Address)\n---",
        "content_url": "---",
        "content_type": "---",
        "content_platform": "---",
        "content_account": "---",
        "content_posted_date": "---",
        "compliance_deadline": "72 hours from receipt of this notice",
        "compliance_contact": officer.full_name if officer else "---",
        "content_removal_body": f"WHEREAS, in connection with FIR No. {case.fir_number} registered at Police Station {case.station_id or '---'} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'}, it has come to the notice of the undersigned that certain unlawful content is being hosted/transmitted through your platform/service.\n\nThis constitutes an offence under the applicable provisions of Bharatiya Nyaya Sanhita, 2023 / Information Technology Act, 2000.\n\nYou are hereby notified under Section 79(3)(b) of the Information Technology Act, 2000 read with Rule 3(1)(d) of the IT (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021, to remove/disable access to the following unlawful information/content within the stipulated time.",
        "content_removal_actions": [
            "1. Immediately remove / disable access to the content identified above",
            "2. Preserve all data / logs / metadata related to the offending content and account",
            "3. Provide subscriber information of the account holder as per Section 94 BNSS",
            "4. Furnish compliance report to the undersigned officer within the deadline",
        ],
        "content_removal_warning": "NOTICE: Failure to comply with this notice within the stipulated time will result in loss of safe harbour protection under Section 79(1) of the IT Act, 2000, and may attract liability under the applicable provisions of law. Non-compliance may also constitute an offence under Section 223 BNS 2023.",

        # --- Data Preservation (IT Act §67C) ---
        "preservation_addressee": "The Nodal Officer / Legal Department,\n(Name of Service Provider / Intermediary)\n---",
        "target_account": "---",
        "target_platform": "---",
        "target_email_phone": "---",
        "preservation_duration": "90 days (or until further orders)",
        "preservation_request_body": f"WHEREAS, investigation is being conducted in FIR No. {case.fir_number} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'}. There is reason to believe that electronic records / data / communication logs associated with the below-identified account(s) are relevant to this investigation.\n\nYou are hereby requested to immediately preserve all records/data pertaining to the identified account(s) for the specified period, pending production of formal legal process. This request is made under Section 67C of the Information Technology Act, 2000 read with the IT (Intermediary Guidelines) Rules, 2021.",
        "preservation_data_list": [
            "1. Subscriber / registration information",
            "2. Login history and IP address logs",
            "3. Account activity logs",
            "4. All content posted / uploaded / transmitted",
            "5. Messages / communications (metadata and content)",
            "6. Transaction records (if applicable)",
            "7. Device information and session data",
            "8. Any deleted data recoverable from backup",
        ],
        "preservation_legal_note": "This is a lawful preservation request. The formal production order / court order under Section 94 BNSS shall follow. Destruction or alteration of preserved data may attract criminal liability under Section 65/66 of the IT Act, 2000 and Section 238 BNS 2023 (destruction of evidence).",

        # --- Content Blocking (IT Act §69A) ---
        "blocking_addressee": "The Designated Officer,\nMinistry of Electronics & Information Technology (MeitY),\nGovernment of India\n(Through: State Nodal Officer)",
        "blocking_grounds": f"The content/information identified above, hosted on the specified platform, is in contravention of the provisions of the Information Technology Act, 2000 and constitutes a threat to [sovereignty and integrity of India / defence of India / security of the State / friendly relations with foreign States / public order / preventing incitement to the commission of any cognizable offence] (delete as applicable).\n\nThis content is directly connected to FIR No. {case.fir_number} and its continued availability poses an imminent threat to the above interests.",
        "blocking_urgency": "URGENT: Immediate blocking is requested in view of the serious nature of the offence and ongoing harm to public order / national security / investigation. Delay may cause irreparable damage.",
        "blocking_legal_basis": "Legal basis: Section 69A of the Information Technology Act, 2000 read with the Information Technology (Procedure and Safeguards for Blocking for Access of Information by Public) Rules, 2009. The State Government is empowered under Section 69A(1) to issue directions for blocking where satisfied that it is necessary in the interest of the grounds specified therein.",

        # --- Platform Data Request ---
        "platform_addressee": "The Nodal Officer (Law Enforcement),\n(Name of Social Media Platform / Internet Service Provider)\n---",
        "platform_data_requested": [
            "1. Subscriber / registration details (name, email, phone, DOB)",
            "2. IP address logs with timestamps (login/session IPs)",
            "3. Device identifiers used to access the account",
            "4. Account creation date and method",
            "5. Content posted during the specified period",
            "6. Associated accounts / linked profiles",
            "7. Payment information (if any)",
            "8. Any other information relevant to investigation",
        ],
        "platform_request_body": f"Sir/Madam,\n\nIn connection with the investigation of FIR No. {case.fir_number}, you are requested to furnish the above-mentioned data/records pertaining to the identified account at the earliest. This request is made under the provisions of Section 94 BNSS read with Section 79 of the IT Act, 2000 and IT (Intermediary Guidelines) Rules, 2021.\n\nThe information is urgently required for the purpose of investigation. Kindly treat this as priority.",

        # --- CDR/IPDR Telecom Request ---
        "telecom_addressee": "The Nodal Officer (LEA Requests),\n(Name of Telecom Service Provider)\n---",
        "target_mobile": "---",
        "target_imei": "---",
        "telecom_data_requested": [
            "1. Call Detail Records (CDR) for the specified period",
            "2. Internet Protocol Detail Records (IPDR) for the specified period",
            "3. Customer Application Form (CAF) / KYC documents",
            "4. Recharge history / payment records",
            "5. Cell ID / tower location data",
            "6. IMEI change history",
            "7. SIM swap history",
            "8. SMS records (if applicable under court order)",
        ],
        "telecom_request_body": f"Sir/Madam,\n\nIn connection with the investigation of FIR No. {case.fir_number} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'}, you are requested to provide the above-mentioned records at the earliest. This request is made under the provisions of Section 94 BNSS.\n\nThe records are urgently required for identification of the suspect and establishing the chain of events. Kindly furnish the data in electronic format (CD/DVD/pen drive) with a certificate under Section 63 BSA 2023.",
        "telecom_urgency": "PRIORITY: This matter involves investigation of a serious cognizable offence. Delay in providing records may hamper the investigation. Kindly expedite.",

        # --- Banking Data Request ---
        "bank_addressee": "The Branch Manager / Nodal Officer (LEA),\n(Name of Bank / Payment Service Provider)\n(Branch Address)\n---",
        "bank_account_no": "---",
        "bank_name": "---",
        "bank_branch": "---",
        "bank_holder_name": "---",
        "banking_data_requested": [
            "1. Account opening documents / KYC (PAN, Aadhaar, address proof)",
            "2. Account statement for the specified period",
            "3. Transaction details with UTR / reference numbers",
            "4. Beneficiary details of all transfers",
            "5. IP address / device details used for transactions (net banking/UPI)",
            "6. Linked mobile number and email",
            "7. UPI / wallet linked accounts",
            "8. Fixed deposit / locker details (if any)",
        ],
        "banking_request_body": f"Sir/Madam,\n\nIn connection with FIR No. {case.fir_number} registered under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'}, you are requested to furnish the above details regarding the specified account. This request is made under Section 94 BNSS.\n\nKindly provide certified copies of the records along with a certificate under Section 63 BSA 2023 for electronic records.",
        "bank_freeze_text": "Further, you are requested to place a lien/freeze on the above account pending investigation, to prevent further fraudulent transactions. A formal court order under Section 105(2) BNSS shall be produced within the statutory time.",

        # --- FSL Forwarding ---
        "fsl_addressee": "The Director,\nForensic Science Laboratory\n(State FSL / CFSL Address)\n---",
        "fsl_brief_facts": f"FIR No. {case.fir_number} has been registered at Police Station {case.station_id or '---'} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} of BNS 2023 regarding the offence of {case.offense_type or '---'}. During the course of investigation, certain exhibits have been collected which require forensic examination.",
        "fsl_exhibits_list": _build_evidence_list(evidence_list) or ["(List exhibits with description, seal number, and condition)"],
        "fsl_questions_list": [
            "1. (Specify questions for the forensic expert based on the nature of exhibits)",
            "2. e.g., Whether the substance is a narcotic/psychotropic substance and its weight?",
            "3. e.g., Whether fingerprints match with the specimen provided?",
            "4. e.g., Opinion on the nature and cause of injuries?",
            "5. e.g., Analysis of digital device and recovery of data?",
        ],
        "fsl_seal_details": "All exhibits have been properly sealed with the Police Station seal in the presence of independent witnesses. The seal impressions have been taken on separate paper for comparison. The chain of custody has been maintained.",

        # --- BSA §63 Electronic Evidence Certificate ---
        "device_description": "---",
        "device_make_model": "---",
        "device_serial": "---",
        "device_owner": "---",
        "device_location": "---",
        "record_description": "---",
        "record_hash": "---",
        "record_date_produced": _format_date(now),
        "record_format": "---",
        "bsa63_certificate_body": "I hereby certify that the electronic record described above is a true and accurate reproduction of the information contained in the computer/device identified herein, and that the computer/device was operating properly during the relevant period, or if not, that the reproduction was not affected by any such malfunction.\n\nThis certificate is issued in compliance with the conditions specified under Section 63(2) of the Bharatiya Sakshya Adhiniyam, 2023.",
        "bsa63_conditions_list": [
            "1. The electronic record was produced by the computer during the period over which the computer was used regularly for lawful activities",
            "2. During the said period, information of the kind contained in the electronic record was regularly fed into the computer in the ordinary course of said activities",
            "3. The computer was operating properly throughout the material period, or if not, any malfunction did not affect the electronic record or its accuracy",
            "4. The information contained in the electronic record reproduces or is derived from information fed into the computer in the ordinary course of said activities",
        ],

        # --- Closure Report ---
        "closure_brief_facts": f"FIR No. {case.fir_number} was registered on {_format_date(case.created_at)} at PS {case.station_id or '---'} under Sections {', '.join(case.sections_applied) if case.sections_applied else '---'} BNS 2023 on the complaint of {case.complainant_name or '---'} regarding {case.offense_type or '---'}.",
        "closure_investigation_summary": "During the course of investigation, the scene of crime was visited, statements of witnesses were recorded, available evidence was collected and analyzed, and all possible leads were explored.",
        "closure_steps_list": [
            "1. Scene of crime inspected and panchnama prepared",
            "2. Statement of complainant recorded under Section 180 BNSS",
            "3. Statements of available witnesses recorded",
            "4. Technical / forensic evidence examined",
            "5. CCTV / electronic evidence checked",
            "6. All available leads explored",
        ],
        "closure_reason_text": "After thorough investigation, sufficient evidence could not be collected to establish the commission of the offence / identify the accused. The case is therefore being submitted as UNTRACED / FALSE / MISTAKE OF FACT / CIVIL NATURE (delete as applicable).",
        "closure_prayer_text": "It is most humbly prayed that the Hon'ble Court may kindly accept this closure report and order accordingly.",

        # --- Spot Panchnama ---
        "spot_date": _format_date(now),
        "spot_time_start": "---",
        "spot_time_end": "---",
        "spot_location": case.incident_location or "---",
        "spot_gps": "---",
        "spot_scene_description": "---",
        "spot_evidence_list": ["(To be documented by the investigating officer at the scene)"],
        "spot_photo_note": "Photographs and videography of the scene of crime have been conducted as per Section 176 BNSS. Audio-video recording has been made using mobile phone / body camera.",
        "spot_observations": "---",

        # --- Inquest Report ---
        "inquest_date": _format_date(now),
        "inquest_time": "---",
        "inquest_place": case.incident_location or "---",
        "informant_name": case.complainant_name or "---",
        "informant_relation": "---",
        "deceased_name": "---",
        "deceased_age": "---",
        "deceased_gender": "---",
        "deceased_address": "---",
        "deceased_id_marks": "---",
        "inquest_body_description": "---",
        "inquest_injuries": "---",
        "inquest_apparent_cause": "---",
        "inquest_action": f"The dead body has been sent to the District Hospital / Government Hospital for post-mortem examination. FIR No. {case.fir_number} has been registered. Further investigation is in progress.",

        # --- Missing Person Report ---
        "missing_name": "---",
        "missing_age": "---",
        "missing_gender": "---",
        "missing_height": "---",
        "missing_complexion": "---",
        "missing_hair": "---",
        "missing_id_marks": "---",
        "last_seen_date": "---",
        "last_seen_time": "---",
        "last_seen_place": "---",
        "last_seen_clothing": "---",
        "missing_circumstances": "---",
        "missing_action_list": [
            "1. Entry made in Daily Diary / GD",
            "2. Photograph circulated to all police stations",
            "3. Entry made on CCTNS / Zipnet / Track Child portal",
            "4. CDR/IPDR of missing person's mobile requested",
            "5. CCTV footage of last seen location being obtained",
            "6. Neighboring police stations informed",
        ],

        # --- Property Release ---
        "court_order_date": "---",
        "court_order_no": "---",
        "release_to_name": "---",
        "release_to_address": "---",
        "release_to_relation": "---",
        "release_to_id": "---",
        "release_property_list": ["(List property items to be released as per court order)"],
        "release_conditions": "The property is being released as per the order of the Hon'ble Court. The recipient shall produce the same before the Court as and when required. The recipient shall not dispose of / alienate / alter the property without the permission of the Court.",
    }

    if case.accused_persons:
        first_accused = case.accused_persons[0] if case.accused_persons else {}
        if isinstance(first_accused, dict):
            data["accused_name"] = first_accused.get("name", case.accused_name or "Unknown")
            data["accused_age"] = str(first_accused.get("age", "---"))
            data["accused_address"] = first_accused.get("address", "---")

    if case.witnesses:
        first_witness = case.witnesses[0] if case.witnesses else {}
        if isinstance(first_witness, dict):
            data["witness_name"] = first_witness.get("name", "---")
            data["witness_statement_text"] = first_witness.get("statement", additional_context or "---")

    return data


def _build_accused_details(case: Case) -> str:
    if case.accused_persons:
        parts = []
        for acc in case.accused_persons:
            if isinstance(acc, dict):
                parts.append(acc.get("name", "Unknown"))
        if parts:
            return ", ".join(parts)
    return case.accused_name or "Unknown"


def _build_evidence_list(evidence_list: list) -> list[str]:
    if not evidence_list:
        return ["No evidence uploaded yet"]
    items = []
    for i, ev in enumerate(evidence_list, 1):
        desc = ev.description or ev.original_filename
        items.append(f"{i}. {desc} ({ev.file_type}, Hash: {ev.file_hash[:12] + '...' if ev.file_hash else 'N/A'})")
    return items


def _build_witnesses_list(case: Case) -> list[str]:
    items = [f"1. {case.complainant_name} (Complainant)"]
    if case.witnesses:
        for i, w in enumerate(case.witnesses, 2):
            if isinstance(w, dict):
                items.append(f"{i}. {w.get('name', 'Unknown')} ({w.get('relation', 'Witness')})")
    return items


def _build_documents_list(case: Case, evidence_list: list) -> list[str]:
    docs = [
        "1. Copy of FIR",
        "2. Statement of Complainant (Section 179 BNSS)",
    ]
    if case.witnesses:
        docs.append(f"3. Statements of {len(case.witnesses)} witness(es)")
    if evidence_list:
        docs.append(f"{len(docs)+1}. {len(evidence_list)} item(s) of physical/digital evidence")
    docs.append(f"{len(docs)+1}. Scene of Crime Panchnama")
    return docs


def _build_enclosures(case: Case, evidence_list: list) -> list[str]:
    enc = [
        "1. Original FIR",
        "2. Charge Sheet (in duplicate)",
        "3. Statements of witnesses",
    ]
    if evidence_list:
        enc.append(f"4. List of material evidence ({len(evidence_list)} items)")
    enc.append(f"{len(enc)+1}. Case Diary")
    return enc
