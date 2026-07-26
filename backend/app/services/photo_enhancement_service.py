import os
import uuid
import hashlib
import asyncio
from typing import Optional
from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from app.config import settings
from app.services.forensic_photography_service import PHOTO_UPLOAD_DIR, _generate_thumbnail


async def enhance_photo(
    file_path: str,
    enhancement_type: str,
    parameters: dict,
    case_id: int,
) -> tuple[str, str, str]:
    """
    Apply enhancement to a photo. Returns (enhanced_file_path, thumbnail_path, new_hash).
    Never modifies the original file.
    """
    img = await asyncio.to_thread(Image.open, file_path)
    img = img.convert("RGB")

    if enhancement_type == "brightness":
        value = parameters.get("value", 1.0)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(value)

    elif enhancement_type == "contrast":
        value = parameters.get("value", 1.0)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(value)

    elif enhancement_type == "sharpness":
        value = parameters.get("value", 1.0)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(value)

    elif enhancement_type == "denoise":
        strength = parameters.get("strength", 5)
        img_array = np.array(img)
        from PIL import ImageFilter as IF
        for _ in range(min(strength, 3)):
            img = img.filter(IF.MedianFilter(size=3))

    elif enhancement_type == "deblur":
        amount = parameters.get("amount", 2.0)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(amount * 100), threshold=3))

    elif enhancement_type == "low_light":
        img_array = np.array(img).astype(np.float32)
        for c in range(3):
            channel = img_array[:, :, c]
            min_val = np.percentile(channel, 2)
            max_val = np.percentile(channel, 98)
            if max_val > min_val:
                channel = (channel - min_val) / (max_val - min_val) * 255.0
            img_array[:, :, c] = np.clip(channel, 0, 255)
        img = Image.fromarray(img_array.astype(np.uint8))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)

    elif enhancement_type == "auto_levels":
        img_array = np.array(img).astype(np.float32)
        for c in range(3):
            channel = img_array[:, :, c]
            min_val = np.percentile(channel, 1)
            max_val = np.percentile(channel, 99)
            if max_val > min_val:
                channel = (channel - min_val) / (max_val - min_val) * 255.0
            img_array[:, :, c] = np.clip(channel, 0, 255)
        img = Image.fromarray(img_array.astype(np.uint8))

    else:
        raise ValueError(f"Unknown enhancement type: {enhancement_type}")

    enhanced_uuid = str(uuid.uuid4())
    case_photo_dir = os.path.join(PHOTO_UPLOAD_DIR, str(case_id))
    os.makedirs(case_photo_dir, exist_ok=True)
    enhanced_path = os.path.join(case_photo_dir, f"{enhanced_uuid}.jpg")

    img.save(enhanced_path, "JPEG", quality=95)
    img.close()

    with open(enhanced_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    thumbnail_path = _generate_thumbnail(enhanced_path, enhanced_uuid)

    return enhanced_path, thumbnail_path or "", file_hash


async def render_annotations_on_image(
    file_path: str,
    annotations: list[dict],
    case_id: int,
) -> tuple[str, str]:
    """Render annotations onto an image and save as a new file. Returns (path, hash)."""
    from PIL import ImageDraw, ImageFont

    img = await asyncio.to_thread(Image.open, file_path)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_small = font

    for ann in annotations:
        data = ann.get("canvas_data", {})
        ann_type = ann.get("annotation_type", "")
        color = data.get("color", "#FF0000")
        stroke_width = data.get("strokeWidth", 2)

        if ann_type == "arrow":
            x1, y1 = data.get("startX", 0), data.get("startY", 0)
            x2, y2 = data.get("endX", 0), data.get("endY", 0)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=stroke_width)
            _draw_arrowhead(draw, x1, y1, x2, y2, color, stroke_width)

        elif ann_type == "circle":
            cx, cy = data.get("centerX", 0), data.get("centerY", 0)
            radius = data.get("radius", 20)
            draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=color, width=stroke_width)

        elif ann_type == "rectangle":
            x, y = data.get("x", 0), data.get("y", 0)
            w, h = data.get("width", 50), data.get("height", 50)
            draw.rectangle([(x, y), (x + w, y + h)], outline=color, width=stroke_width)

        elif ann_type == "text":
            x, y = data.get("x", 0), data.get("y", 0)
            text = data.get("text", "")
            draw.text((x, y), text, fill=color, font=font)

        elif ann_type == "measurement":
            x1, y1 = data.get("startX", 0), data.get("startY", 0)
            x2, y2 = data.get("endX", 0), data.get("endY", 0)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=stroke_width)
            draw.line([(x1, y1 - 5), (x1, y1 + 5)], fill=color, width=stroke_width)
            draw.line([(x2, y2 - 5), (x2, y2 + 5)], fill=color, width=stroke_width)
            label = data.get("measurement_text", "")
            if label:
                mid_x = (x1 + x2) // 2
                mid_y = (y1 + y2) // 2
                draw.text((mid_x, mid_y - 15), label, fill=color, font=font_small)

        elif ann_type == "marker":
            x, y = data.get("x", 0), data.get("y", 0)
            number = ann.get("evidence_number", 0)
            draw.ellipse([(x - 15, y - 15), (x + 15, y + 15)], fill="#FFD700", outline="#000000", width=2)
            draw.text((x - 5, y - 8), str(number), fill="#000000", font=font)

        elif ann_type == "freehand":
            points = data.get("points", [])
            if len(points) >= 2:
                point_tuples = [(p.get("x", 0), p.get("y", 0)) for p in points]
                draw.line(point_tuples, fill=color, width=stroke_width)

    annotated_uuid = str(uuid.uuid4())
    case_photo_dir = os.path.join(PHOTO_UPLOAD_DIR, str(case_id))
    os.makedirs(case_photo_dir, exist_ok=True)
    annotated_path = os.path.join(case_photo_dir, f"{annotated_uuid}_annotated.jpg")

    img.save(annotated_path, "JPEG", quality=95)
    img.close()

    with open(annotated_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    return annotated_path, file_hash


def _draw_arrowhead(draw, x1, y1, x2, y2, color, width):
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 15
    arrow_angle = math.pi / 6
    p1x = x2 - arrow_len * math.cos(angle - arrow_angle)
    p1y = y2 - arrow_len * math.sin(angle - arrow_angle)
    p2x = x2 - arrow_len * math.cos(angle + arrow_angle)
    p2y = y2 - arrow_len * math.sin(angle + arrow_angle)
    draw.polygon([(x2, y2), (p1x, p1y), (p2x, p2y)], fill=color)
