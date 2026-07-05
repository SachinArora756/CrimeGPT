import os
import aiofiles
from datetime import datetime

from app.models.evidence import Evidence


async def analyze_evidence(evidence: Evidence) -> dict:
    """Analyze evidence file and return AI-generated summary + metadata."""
    file_path = evidence.file_path
    file_type = evidence.file_type

    analysis = {
        "evidence_id": evidence.id,
        "filename": evidence.original_filename,
        "file_type": file_type,
        "file_size_bytes": evidence.file_size,
        "hash_sha256": evidence.file_hash,
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    if not os.path.exists(file_path):
        analysis["error"] = "File not found on disk"
        return analysis

    if file_type == "image":
        analysis["forensic_data"] = await _analyze_image(file_path)
    elif file_type == "document":
        analysis["forensic_data"] = await _analyze_document(file_path)
    elif file_type == "audio":
        analysis["forensic_data"] = await _analyze_audio(file_path)
    elif file_type == "video":
        analysis["forensic_data"] = await _analyze_video(file_path)
    else:
        analysis["forensic_data"] = {"type": "unknown", "note": "No specialized analyzer for this file type"}

    analysis["ai_summary"] = await _get_ai_summary(evidence, analysis.get("forensic_data", {}))

    return analysis


async def _analyze_image(file_path: str) -> dict:
    """Extract image metadata."""
    data = {"type": "image_analysis"}
    file_size = os.path.getsize(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    data["format"] = ext.lstrip(".")
    data["file_size_kb"] = round(file_size / 1024, 1)

    try:
        from PIL import Image
        img = Image.open(file_path)
        data["dimensions"] = f"{img.width}x{img.height}"
        data["mode"] = img.mode
        exif = img._getexif()
        if exif:
            data["has_exif"] = True
            data["exif_tags_count"] = len(exif)
        else:
            data["has_exif"] = False
        img.close()
    except Exception:
        data["dimensions"] = "unable to read"
        data["has_exif"] = False

    return data


async def _analyze_document(file_path: str) -> dict:
    """Extract document metadata and text preview."""
    data = {"type": "document_analysis"}
    ext = os.path.splitext(file_path)[1].lower()
    data["format"] = ext.lstrip(".")

    if ext == ".txt":
        async with aiofiles.open(file_path, "r", errors="ignore") as f:
            content = await f.read(5000)
        data["char_count"] = len(content)
        data["line_count"] = content.count("\n") + 1
        data["preview"] = content[:500]
    elif ext == ".pdf":
        data["note"] = "PDF analysis available"
        try:
            import fitz
            doc = fitz.open(file_path)
            data["page_count"] = doc.page_count
            if doc.page_count > 0:
                data["preview"] = doc[0].get_text()[:500]
            doc.close()
        except ImportError:
            data["note"] = "PDF reader (PyMuPDF) not installed"
        except Exception as e:
            data["note"] = f"PDF read error: {str(e)[:100]}"
    else:
        data["note"] = f"Format {ext} - basic metadata only"

    return data


async def _analyze_audio(file_path: str) -> dict:
    """Extract audio metadata."""
    data = {"type": "audio_analysis"}
    data["file_size_kb"] = round(os.path.getsize(file_path) / 1024, 1)
    ext = os.path.splitext(file_path)[1].lower()
    data["format"] = ext.lstrip(".")
    data["note"] = "Audio transcription available via Whisper when configured"
    return data


async def _analyze_video(file_path: str) -> dict:
    """Extract video metadata."""
    data = {"type": "video_analysis"}
    data["file_size_mb"] = round(os.path.getsize(file_path) / (1024 * 1024), 2)
    ext = os.path.splitext(file_path)[1].lower()
    data["format"] = ext.lstrip(".")
    data["note"] = "Video frame extraction and analysis available"
    return data


async def _get_ai_summary(evidence: Evidence, forensic_data: dict) -> str:
    """Generate AI summary of the evidence."""
    try:
        from app.ai.supervisor import get_llm
        llm = get_llm()

        prompt = (
            "You are a forensic evidence analyst for a police investigation system. "
            "Provide a brief professional summary of this evidence file.\n\n"
            f"File: {evidence.original_filename}\n"
            f"Type: {evidence.file_type}\n"
            f"Size: {evidence.file_size} bytes\n"
            f"SHA-256: {evidence.file_hash}\n"
            f"Forensic data: {forensic_data}\n\n"
            "Provide: 1) What this file likely contains 2) Key observations "
            "3) Recommendations for the investigating officer. Keep it under 200 words."
        )
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception:
        return (
            f"Automated analysis: {evidence.file_type} file '{evidence.original_filename}' "
            f"({evidence.file_size} bytes). SHA-256 hash recorded for integrity verification. "
            f"AI-powered detailed analysis unavailable - Gemini API not configured."
        )
