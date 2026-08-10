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
