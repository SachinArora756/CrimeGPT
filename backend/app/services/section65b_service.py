"""Section 65B Indian Evidence Act — Digital Evidence Certificate Generation.

Section 65B requires a certificate for computer-generated electronic records
to be admissible in court. This service generates compliant certificates.
"""

import hashlib
import os
import asyncio
from datetime import datetime, timezone
from typing import Any

import aiofiles


async def generate_section65b_certificate(
    evidence_id: int,
    file_path: str,
    original_filename: str,
    file_hash: str | None,
    officer_id: int,
    officer_name: str,
    officer_designation: str,
    device_description: str = "CrimeGPT Forensic Platform",
    additional_notes: str = "",
) -> dict[str, Any]:
    """Generate a Section 65B certificate for digital evidence."""

    current_hash = await _compute_file_hash(file_path)
    hash_matches = current_hash == file_hash if file_hash else None
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

    now = datetime.now(timezone.utc)

    certificate = {
        "certificate_type": "Section 65B - Indian Evidence Act, 1872",
        "generated_at": now.isoformat(),
        "evidence_id": evidence_id,
        "file_details": {
            "original_filename": original_filename,
            "file_size_bytes": file_size,
            "sha256_hash_at_upload": file_hash,
            "sha256_hash_at_certification": current_hash,
            "integrity_verified": hash_matches,
        },
        "certifying_officer": {
            "user_id": officer_id,
            "name": officer_name,
            "designation": officer_designation,
        },
        "device_source": {
            "description": device_description,
            "platform": "CrimeGPT Digital Forensics Platform",
            "server_time_utc": now.isoformat(),
        },
        "section_65b_conditions": {
            "condition_a": "The computer output was produced during the period the computer was regularly used to store or process information for lawful activities.",
            "condition_b": "Information was regularly fed into the computer in the ordinary course of activities.",
            "condition_c": "The computer was operating properly during the material period; any malfunction did not affect the electronic record.",
            "condition_d": "The information reproduced is such as is fed into the computer in the ordinary course of activities.",
            "all_conditions_met": True,
        },
        "declaration": (
            f"I, {officer_name}, {officer_designation}, hereby certify that the electronic record "
            f"identified as '{original_filename}' (Evidence ID: {evidence_id}) is a true and accurate "
            f"reproduction of the original digital evidence. The conditions specified under Section 65B(2) "
            f"of the Indian Evidence Act, 1872, as applicable to this computer output, are satisfied. "
            f"This certificate is issued on {now.strftime('%d %B %Y at %H:%M UTC')}."
        ),
        "additional_notes": additional_notes or None,
        "legal_notice": "This certificate must be signed by a person occupying a responsible official position in relation to the operation of the relevant device or the management of the relevant activities.",
    }

    return certificate


async def compute_perceptual_hash(file_path: str) -> dict[str, Any]:
    """Compute perceptual hash (pHash) for an image — survives crops, compression, resizing."""
    def _compute():
        try:
            from PIL import Image
            import numpy as np
        except ImportError:
            return {"error": "Pillow/numpy not available", "phash": None}

        try:
            img = Image.open(file_path).convert("L").resize((32, 32), Image.LANCZOS)
            pixels = np.array(img, dtype=np.float64)

            # DCT-based perceptual hash
            from scipy.fft import dct
            dct_result = dct(dct(pixels, axis=0, norm="ortho"), axis=1, norm="ortho")
            dct_low = dct_result[:8, :8]
            median = np.median(dct_low)
            phash_bits = (dct_low > median).flatten()
            phash_hex = "".join("1" if b else "0" for b in phash_bits)
            phash_int = int(phash_hex, 2)
            phash_str = f"{phash_int:016x}"

            return {"phash": phash_str, "method": "dct_8x8", "bits": 64}
        except ImportError:
            # Fallback: average hash (no scipy needed)
            img = Image.open(file_path).convert("L").resize((8, 8), Image.LANCZOS)
            pixels = np.array(img, dtype=np.float64)
            avg = pixels.mean()
            bits = (pixels > avg).flatten()
            ahash_hex = "".join("1" if b else "0" for b in bits)
            ahash_int = int(ahash_hex, 2)
            ahash_str = f"{ahash_int:016x}"
            return {"phash": ahash_str, "method": "average_hash_8x8", "bits": 64}
        except Exception as e:
            return {"error": str(e), "phash": None}

    return await asyncio.to_thread(_compute)


def compare_perceptual_hashes(hash_a: str, hash_b: str) -> dict[str, Any]:
    """Compare two perceptual hashes and return similarity."""
    try:
        int_a = int(hash_a, 16)
        int_b = int(hash_b, 16)
        xor = int_a ^ int_b
        hamming_distance = bin(xor).count("1")
        similarity = 1.0 - (hamming_distance / 64.0)

        if hamming_distance <= 5:
            verdict = "near_identical"
        elif hamming_distance <= 10:
            verdict = "visually_similar"
        elif hamming_distance <= 20:
            verdict = "possibly_related"
        else:
            verdict = "different"

        return {
            "hamming_distance": hamming_distance,
            "similarity": round(similarity, 4),
            "verdict": verdict,
            "max_bits": 64,
        }
    except (ValueError, TypeError) as e:
        return {"error": str(e), "similarity": None}


async def _compute_file_hash(file_path: str) -> str | None:
    """Compute SHA-256 of file on disk."""
    if not os.path.exists(file_path):
        return None
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(1024 * 1024):
            sha256.update(chunk)
    return sha256.hexdigest()
