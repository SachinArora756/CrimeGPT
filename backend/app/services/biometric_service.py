"""
Biometric processing service for criminal profiles.

Handles face embedding generation (InsightFace), fingerprint template
extraction (OpenCV ORB), and Qdrant vector upserts.
"""

import asyncio
import logging
import numpy as np

logger = logging.getLogger(__name__)

FACE_EMBEDDING_DIM = 512


def _get_insightface():
    from app.services.forensic_tools_service import _get_insightface as _get_app
    return _get_app()


async def generate_face_embedding(file_path: str) -> tuple[list[float], float]:
    """
    Run InsightFace on an image file and return (embedding, quality_score).
    Raises ValueError if no face is detected or multiple faces found.
    """

    def _extract():
        import cv2
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError("Could not read image file")

        app = _get_insightface()
        faces = app.get(img)

        if not faces:
            raise ValueError("No face detected in the uploaded image")

        if len(faces) > 1:
            faces = sorted(faces, key=lambda f: f.det_score, reverse=True)

        face = faces[0]
        embedding = face.normed_embedding.tolist()
        quality = round(float(face.det_score), 4)
        return embedding, quality

    return await asyncio.to_thread(_extract)


async def generate_fingerprint_template(file_path: str) -> tuple[dict, float]:
    """
    Extract ORB fingerprint template from an image.
    Returns (template_data_dict, quality_score).
    Raises ValueError if insufficient minutiae are found.
    """

    def _extract():
        import cv2

        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("Could not read fingerprint image")

        equalized = cv2.equalizeHist(img)
        blurred = cv2.GaussianBlur(equalized, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        if hasattr(cv2, "ximgproc"):
            thinned = cv2.ximgproc.thinning(cleaned)
        else:
            thinned = cleaned

        orb = cv2.ORB_create(nfeatures=500, scaleFactor=1.2, nlevels=8)
        keypoints, descriptors = orb.detectAndCompute(thinned, None)

        if descriptors is None or len(keypoints) < 10:
            try:
                sift = cv2.SIFT_create(nfeatures=500)
                keypoints, descriptors = sift.detectAndCompute(img, None)
            except Exception:
                pass

        if descriptors is None or len(keypoints) < 5:
            raise ValueError(
                f"Insufficient fingerprint features detected ({len(keypoints) if keypoints else 0} minutiae). "
                "Image quality too low."
            )

        minutiae_count = len(keypoints)
        if minutiae_count >= 100:
            quality_score = 0.95
        elif minutiae_count >= 50:
            quality_score = 0.8
        elif minutiae_count >= 20:
            quality_score = 0.6
        else:
            quality_score = 0.3

        template = {
            "minutiae_count": minutiae_count,
            "descriptors": descriptors.tolist()[:200],
            "keypoints": [
                {"x": round(kp.pt[0], 1), "y": round(kp.pt[1], 1),
                 "size": round(kp.size, 1), "angle": round(kp.angle, 1)}
                for kp in keypoints[:200]
            ],
        }

        return template, quality_score

    return await asyncio.to_thread(_extract)


def upsert_face_to_qdrant(
    point_id: int,
    embedding: list[float],
    criminal_db_id: int,
    criminal_public_id: str,
    full_name: str,
    image_path: str,
    wanted_status: str | None = None,
    danger_level: str | None = None,
    gang_name: str | None = None,
):
    """Best-effort upsert a face embedding point into Qdrant."""
    try:
        from app.services.forensic_tools_service import (
            _get_qdrant_client, _ensure_qdrant_collection,
            FACE_COLLECTION, FACE_EMBEDDING_DIM,
        )
        from qdrant_client.models import PointStruct

        client = _get_qdrant_client()
        _ensure_qdrant_collection(client, FACE_COLLECTION, FACE_EMBEDDING_DIM)

        client.upsert(
            collection_name=FACE_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "criminal_db_id": criminal_db_id,
                        "criminal_id": criminal_public_id,
                        "full_name": full_name,
                        "image_path": image_path,
                        "wanted_status": wanted_status or "",
                        "danger_level": danger_level or "",
                        "gang_name": gang_name,
                    },
                )
            ],
        )
        logger.info(f"Upserted face embedding to Qdrant for {criminal_public_id}")
    except Exception as e:
        logger.warning(f"Qdrant upsert failed (non-fatal): {e}")
