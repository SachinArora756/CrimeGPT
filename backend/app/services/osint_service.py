import json
import logging
from app.ai.llm_provider import get_llm, has_any_llm_key

logger = logging.getLogger(__name__)

OSINT_PROMPTS = {
    "phone": """You are an OSINT analyst. Given a phone number, generate realistic intelligence findings.
Phone number: {value}

Return a JSON object with these keys:
- summary: 1-2 sentence overview
- carrier_info: {{provider, circle, type}}
- registered_name: string or null
- linked_accounts: list of {{platform, username}}
- upi_ids: list of strings
- associated_addresses: list of strings
- risk_indicators: list of strings
- recommended_actions: list of strings
- disclaimer: "AI-generated intelligence requires officer verification"

Return ONLY valid JSON, no markdown fences.""",

    "email": """You are an OSINT analyst. Given an email address, generate realistic intelligence findings.
Email: {value}

Return a JSON object with these keys:
- summary: 1-2 sentence overview
- breach_exposure: list of {{breach_name, date, data_exposed}}
- linked_platforms: list of {{platform, profile_url}}
- domain_info: {{registrar, creation_date, hosting}}
- registration_patterns: list of strings
- risk_indicators: list of strings
- recommended_actions: list of strings
- disclaimer: "AI-generated intelligence requires officer verification"

Return ONLY valid JSON, no markdown fences.""",

    "username": """You are an OSINT analyst. Given a username/handle, generate realistic intelligence findings.
Username: {value}

Return a JSON object with these keys:
- summary: 1-2 sentence overview
- cross_platform_profiles: list of {{platform, url, active}}
- activity_patterns: list of strings
- associated_emails: list of strings
- associated_names: list of strings
- risk_indicators: list of strings
- recommended_actions: list of strings
- disclaimer: "AI-generated intelligence requires officer verification"

Return ONLY valid JSON, no markdown fences.""",

    "vehicle_plate": """You are an OSINT analyst. Given a vehicle registration plate, generate realistic intelligence findings.
Vehicle Plate: {value}

Return a JSON object with these keys:
- summary: 1-2 sentence overview
- owner_info: {{name, address, id_type}}
- registration_details: {{rto, date, expiry, vehicle_class, fuel_type}}
- insurance_status: {{provider, valid_until, policy_number}}
- challan_history: list of {{date, offense, amount, status}}
- associated_addresses: list of strings
- risk_indicators: list of strings
- recommended_actions: list of strings
- disclaimer: "AI-generated intelligence requires officer verification"

Return ONLY valid JSON, no markdown fences.""",

    "ip_domain": """You are an OSINT analyst. Given an IP address or domain, generate realistic intelligence findings.
IP/Domain: {value}

Return a JSON object with these keys:
- summary: 1-2 sentence overview
- geolocation: {{country, state, city, coordinates}}
- isp_info: {{name, asn, org}}
- whois_data: {{registrant, registrar, creation_date, expiry_date}}
- hosting_details: {{provider, server_type, cdn}}
- threat_intel: list of {{source, classification, last_seen}}
- associated_domains: list of strings
- risk_indicators: list of strings
- recommended_actions: list of strings
- disclaimer: "AI-generated intelligence requires officer verification"

Return ONLY valid JSON, no markdown fences.""",

    "person_name": """You are an OSINT analyst. Given a person's name, generate realistic intelligence findings from open sources.
Person Name: {value}

Return a JSON object with these keys:
- summary: 1-2 sentence overview
- news_mentions: list of {{headline, source, date, url}}
- court_records: list of {{case_number, court, year, status, offense}}
- social_profiles: list of {{platform, handle, followers}}
- electoral_info: {{constituency, voter_id_partial, address_partial}} or null
- business_associations: list of strings
- risk_indicators: list of strings
- recommended_actions: list of strings
- disclaimer: "AI-generated intelligence requires officer verification"

Return ONLY valid JSON, no markdown fences.""",
}

FALLBACK_RESPONSE = {
    "summary": "AI analysis unavailable - no LLM API key configured",
    "risk_indicators": [],
    "recommended_actions": ["Configure Gemini or OpenRouter API key for AI-powered analysis"],
    "disclaimer": "No AI findings generated - manual investigation required",
}


async def generate_osint_findings(identifier_type: str, identifier_value: str) -> tuple[dict, str | None]:
    if not has_any_llm_key():
        return FALLBACK_RESPONSE, None

    prompt_template = OSINT_PROMPTS.get(identifier_type)
    if not prompt_template:
        return {"summary": f"Unknown identifier type: {identifier_type}", "disclaimer": "Invalid type"}, None

    prompt = prompt_template.format(value=identifier_value)

    try:
        llm = get_llm(temperature=0.4)
        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        findings = json.loads(content)
        model_name = "gemini-2.5-flash"
        return findings, model_name

    except json.JSONDecodeError as e:
        logger.error(f"OSINT JSON parse error: {e}")
        return {
            "summary": "AI generated a response but it could not be parsed as structured data",
            "raw_response": content[:2000] if 'content' in dir() else "No response",
            "risk_indicators": [],
            "recommended_actions": ["Retry the search or investigate manually"],
            "disclaimer": "AI response parsing failed - partial data shown",
        }, "gemini-2.5-flash"

    except Exception as e:
        logger.error(f"OSINT LLM error: {e}")
        return {
            "summary": f"AI analysis failed: {str(e)[:100]}",
            "risk_indicators": [],
            "recommended_actions": ["Retry the search or investigate manually"],
            "disclaimer": "AI generation error - manual investigation required",
        }, None
