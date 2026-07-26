import os
import json
import asyncio
import base64
from typing import Optional

import numpy as np
from PIL import Image

from app.ai.llm_provider import generate_text, generate_vision_base64, has_any_llm_key


async def generate_photography_guidance(
    crime_type: str,
    scene_description: Optional[str] = None,
    existing_photos_count: int = 0,
) -> dict:
    if not has_any_llm_key():
        return _get_fallback_guidance(crime_type)

    scene_ctx = f"\nScene Description: {scene_description}" if scene_description else ""

    prompt = f"""You are an expert forensic photography instructor for Indian police officers (CFSL / BPR&D guidelines).

Crime Type: {crime_type}{scene_ctx}
Photos Already Taken: {existing_photos_count}

Generate a structured photography guidance in JSON format:
{{
  "minimum_shots": <number - total minimum photos required>,
  "shot_checklist": [
    {{"id": 1, "type": "overview|midrange|closeup|measurement", "description": "...", "angle": "bird's eye|eye-level|45-degree|low-angle|ground-level", "distance": "10m+|5-10m|2-5m|1-2m|<1m|macro", "priority": "mandatory|recommended|optional"}}
  ],
  "mandatory_angles": ["bird's eye/overhead", "eye-level from 4 corners", "45-degree approach angle", "low-angle for under-surface details"],
  "distance_ranges": [
    {{"range": "Long-range (10m+)", "purpose": "Establish location context and surroundings"}},
    {{"range": "Mid-range (3-5m)", "purpose": "Show relationship between evidence items"}},
    {{"range": "Close-up (30cm-1m)", "purpose": "Detail individual evidence items"}},
    {{"range": "Macro (<30cm)", "purpose": "Show textures, patterns, marks"}}
  ],
  "brightness_tips": ["Use flash for indoor/poorly lit areas", "Avoid direct flash causing reflections on wet surfaces", "Use oblique/side lighting to reveal impressions and textures"],
  "special_requirements": ["Place evidence markers before close-up shots", "Include L-shaped scale ruler in evidence photos"],
  "common_mistakes": ["Not taking overall context shot first", "Moving evidence before photography"],
  "indian_law_requirements": ["Section 65B IT Act compliance for digital photos", "Maintain chain of custody documentation", "Panchayatdar/witness presence during photography"]
}}

Tailor specifically for crime type: {crime_type}
Follow Indian forensic science lab (CFSL) and National Police Academy (NPA) guidelines.
Return ONLY valid JSON, no markdown formatting."""

    try:
        response = await asyncio.to_thread(generate_text, prompt, 0.2, 3000)
        return _parse_json_response(response)
    except Exception:
        return _get_fallback_guidance(crime_type)


async def assess_photo_quality(file_path: str, crime_type: Optional[str] = None) -> dict:
    technical = await asyncio.to_thread(_compute_technical_metrics, file_path)

    if not has_any_llm_key():
        return {
            "quality_score": technical.get("estimated_quality", 50),
            "courtroom_readiness": technical.get("estimated_quality", 50),
            "technical_metrics": technical,
            "ai_assessment": None,
            "suggestions": _basic_suggestions_from_technical(technical),
        }

    with open(file_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".bmp": "image/bmp", ".tiff": "image/tiff", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    crime_ctx = f"\nThis is a {crime_type} crime scene photo." if crime_type else ""

    prompt = f"""Analyze this crime scene photograph for forensic documentation quality.{crime_ctx}

Provide a JSON response:
{{
  "overall_quality_score": <0-100>,
  "courtroom_readiness_score": <0-100>,
  "issues": {{
    "blur": {{"detected": true/false, "severity": "none|mild|severe", "affected_area": "description"}},
    "exposure": {{"issue": "none|overexposed|underexposed|uneven", "severity": "none|mild|severe"}},
    "angle": {{"appropriate": true/false, "current_angle": "description", "suggested_angle": "description"}},
    "scale_reference": {{"present": true/false, "suggestion": "Include L-shaped ruler/scale marker"}},
    "composition": {{"centered": true/false, "issues": [], "suggestions": []}},
    "focus": {{"subject_in_focus": true/false, "depth_adequate": true/false}},
    "lighting": {{"adequate": true/false, "shadows_obstructing": true/false, "suggestion": ""}},
    "evidence_visibility": {{"clearly_visible": true/false, "obstructions": []}}
  }},
  "missing_elements": ["description of what else should be photographed"],
  "retake_suggestions": ["specific actionable suggestions for retaking"],
  "strengths": ["what the photo does well"],
  "drawbacks": ["specific problems with this photo"]
}}

Assess as a forensic photography expert would for court admissibility.
Return ONLY valid JSON."""

    try:
        response = await asyncio.to_thread(generate_vision_base64, image_b64, mime_type, prompt, 0.1, 2048)
        ai_result = _parse_json_response(response)

        quality_score = ai_result.get("overall_quality_score", 50)
        courtroom_readiness = ai_result.get("courtroom_readiness_score", 50)

        suggestions = ai_result.get("retake_suggestions", [])
        if not suggestions:
            suggestions = _basic_suggestions_from_technical(technical)

        return {
            "quality_score": quality_score,
            "courtroom_readiness": courtroom_readiness,
            "technical_metrics": technical,
            "ai_assessment": ai_result,
            "suggestions": suggestions,
        }
    except Exception as e:
        return {
            "quality_score": technical.get("estimated_quality", 50),
            "courtroom_readiness": technical.get("estimated_quality", 50),
            "technical_metrics": technical,
            "ai_assessment": None,
            "suggestions": _basic_suggestions_from_technical(technical),
            "error": str(e),
        }


async def detect_objects_in_photo(file_path: str) -> dict:
    if not has_any_llm_key():
        return {"objects": [], "weapons": [], "vehicles": [], "persons": [], "forensic_items": []}

    with open(file_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".bmp": "image/bmp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    prompt = """Analyze this crime scene photograph and detect all objects relevant to forensic investigation.

Return JSON:
{
  "objects": [{"label": "...", "confidence": 0.0-1.0, "location": "description of position in image"}],
  "weapons": [{"type": "...", "description": "...", "confidence": 0.0-1.0, "location": "..."}],
  "vehicles": [{"type": "...", "color": "...", "license_plate": "if visible", "confidence": 0.0-1.0}],
  "persons": [{"description": "...", "position": "...", "confidence": 0.0-1.0}],
  "forensic_items": [{"type": "bloodstain|footprint|fingerprint|tool_mark|fiber|hair|glass|chemical|other", "description": "...", "confidence": 0.0-1.0, "location": "..."}]
}

Focus on forensically relevant items. Return ONLY valid JSON."""

    try:
        response = await asyncio.to_thread(generate_vision_base64, image_b64, mime_type, prompt, 0.1, 2048)
        return _parse_json_response(response)
    except Exception:
        return {"objects": [], "weapons": [], "vehicles": [], "persons": [], "forensic_items": []}


def _compute_technical_metrics(file_path: str) -> dict:
    try:
        img = Image.open(file_path)
        img_array = np.array(img.convert("L"))

        laplacian_var = float(np.var(np.gradient(np.gradient(img_array, axis=0), axis=1)))
        blur_score = min(100, laplacian_var / 10.0)

        histogram = np.histogram(img_array, bins=256, range=(0, 256))[0]
        histogram = histogram / histogram.sum()
        mean_brightness = float(np.mean(img_array))
        std_brightness = float(np.std(img_array))

        if mean_brightness < 50:
            exposure_issue = "underexposed"
        elif mean_brightness > 200:
            exposure_issue = "overexposed"
        else:
            exposure_issue = "normal"

        contrast_score = min(100, std_brightness * 2)

        estimated_quality = (blur_score * 0.4 + contrast_score * 0.3 + (100 - abs(mean_brightness - 128)) * 0.3)
        estimated_quality = max(0, min(100, estimated_quality))

        width, height = img.size
        img.close()

        return {
            "blur_score": round(blur_score, 1),
            "mean_brightness": round(mean_brightness, 1),
            "std_brightness": round(std_brightness, 1),
            "contrast_score": round(contrast_score, 1),
            "exposure_issue": exposure_issue,
            "resolution": f"{width}x{height}",
            "megapixels": round((width * height) / 1_000_000, 1),
            "estimated_quality": round(estimated_quality, 1),
        }
    except Exception:
        return {"blur_score": 0, "mean_brightness": 0, "exposure_issue": "unknown", "estimated_quality": 50}


def _basic_suggestions_from_technical(metrics: dict) -> list[str]:
    suggestions = []
    if metrics.get("blur_score", 100) < 30:
        suggestions.append("Image appears blurry. Use a steadier grip or tripod. Ensure camera is focused before shooting.")
    if metrics.get("exposure_issue") == "underexposed":
        suggestions.append("Image is too dark. Use flash or increase exposure. Ensure adequate lighting.")
    elif metrics.get("exposure_issue") == "overexposed":
        suggestions.append("Image is too bright/washed out. Reduce flash intensity or adjust exposure.")
    if metrics.get("contrast_score", 100) < 30:
        suggestions.append("Low contrast detected. This may affect evidence visibility in prints.")
    if metrics.get("megapixels", 10) < 2:
        suggestions.append("Resolution is low. Use a higher resolution camera setting for court-quality documentation.")
    if not suggestions:
        suggestions.append("Photo meets basic technical requirements.")
    return suggestions


def _get_fallback_guidance(crime_type: str) -> dict:
    return {
        "minimum_shots": 20,
        "shot_checklist": [
            {"id": 1, "type": "overview", "description": "Wide establishing shot of entire scene from 4 directions", "angle": "eye-level", "distance": "10m+", "priority": "mandatory"},
            {"id": 2, "type": "overview", "description": "Overhead/bird's eye view if possible", "angle": "bird's eye", "distance": "5-10m", "priority": "mandatory"},
            {"id": 3, "type": "midrange", "description": "Mid-range shots showing evidence in context", "angle": "eye-level", "distance": "2-5m", "priority": "mandatory"},
            {"id": 4, "type": "closeup", "description": "Close-up of each evidence item with scale", "angle": "90-degree overhead", "distance": "<1m", "priority": "mandatory"},
            {"id": 5, "type": "measurement", "description": "Evidence items with L-ruler for scale", "angle": "90-degree", "distance": "<1m", "priority": "mandatory"},
            {"id": 6, "type": "overview", "description": "Entry and exit points of scene", "angle": "eye-level", "distance": "2-5m", "priority": "mandatory"},
        ],
        "mandatory_angles": ["Bird's eye / Overhead", "Eye-level from 4 corners (N/S/E/W)", "45-degree approach angle", "Low-angle (ground-level) for tire tracks / footprints"],
        "distance_ranges": [
            {"range": "Long-range (10m+)", "purpose": "Establish location, show surroundings, landmarks"},
            {"range": "Mid-range (3-5m)", "purpose": "Show spatial relationship between evidence items"},
            {"range": "Close-up (30cm-1m)", "purpose": "Individual evidence with context visible"},
            {"range": "Macro (<30cm)", "purpose": "Fine details: serial numbers, textures, marks"},
        ],
        "brightness_tips": [
            "Use flash for indoor or poorly lit scenes",
            "Use side/oblique lighting to reveal impressions, scratches, footprints",
            "Avoid direct flash on reflective/wet surfaces (angle flash 45 degrees)",
            "For outdoor daytime: use fill flash to reduce harsh shadows",
            "Night scenes: use multiple light sources from different angles",
        ],
        "special_requirements": [
            "Place numbered evidence markers before photographing close-ups",
            "Include L-shaped scale ruler adjacent to evidence in close-up photos",
            "Photograph evidence items both with and without markers",
            "Take each evidence photo from at least 2 angles",
            "Do NOT move or touch evidence before photography is complete",
        ],
        "common_mistakes": [
            "Not taking overall establishing shots before close-ups",
            "Moving or disturbing evidence before photographing in situ",
            "No scale reference in close-up photographs",
            "Photographs out of focus or motion-blurred",
            "Shadows obscuring critical evidence details",
            "Not photographing entry/exit points",
            "Incomplete coverage (zones left undocumented)",
        ],
        "indian_law_requirements": [
            "Section 65B Indian Evidence Act: electronic record must have certificate",
            "Document GPS coordinates and timestamp for each photo",
            "Maintain continuous chain of custody record",
            "Panchayatdar/independent witness should be present during photography",
            "Officer must sign photographic record register",
            "Original images must be preserved unedited on sealed media",
        ],
    }


def _parse_json_response(response: str) -> dict:
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass
        return {}
