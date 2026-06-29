import os
from app.ai.agents.supervisor import AgentState


async def analyze_evidence(file_path: str, file_type: str) -> dict:
    results = {"analysis_type": file_type, "findings": []}

    if file_type == "image":
        ocr_text = await run_ocr(file_path)
        vision_results = await run_object_detection(file_path)
        results["ocr_text"] = ocr_text
        results["objects_detected"] = vision_results
        results["findings"].append(f"OCR extracted {len(ocr_text)} characters")
        if vision_results:
            results["findings"].append(f"Detected {len(vision_results)} objects")

    elif file_type == "document":
        if file_path.lower().endswith(".pdf"):
            ocr_text = await extract_pdf_text(file_path)
        else:
            ocr_text = await run_ocr(file_path)
        results["ocr_text"] = ocr_text
        results["findings"].append(f"Extracted {len(ocr_text)} characters from document")

    elif file_type == "audio":
        transcript = await transcribe_audio(file_path)
        results["transcript"] = transcript
        results["findings"].append(f"Transcribed {len(transcript)} characters from audio")

    metadata = extract_file_metadata(file_path)
    results["metadata"] = metadata

    return results


async def run_ocr(file_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang="eng+hin")
        return text.strip()
    except Exception as e:
        return f"OCR failed: {str(e)}"


async def run_object_detection(file_path: str) -> list[dict]:
    try:
        from ultralytics import YOLO

        model = YOLO("yolov8n.pt")
        results = model(file_path, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    "class": result.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist(),
                })
        return detections
    except Exception:
        return []


async def extract_pdf_text(file_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        from pdf2image import convert_from_path

        pages = convert_from_path(file_path, first_page=1, last_page=10)
        text_parts = []
        for page in pages:
            text = pytesseract.image_to_string(page, lang="eng+hin")
            text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        return f"PDF extraction failed: {str(e)}"


async def transcribe_audio(file_path: str) -> str:
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        return result["text"]
    except Exception as e:
        return f"Transcription failed: {str(e)}"


def extract_file_metadata(file_path: str) -> dict:
    try:
        stat = os.stat(file_path)
        return {
            "file_size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": os.path.splitext(file_path)[1],
        }
    except Exception:
        return {}


def evidence_analysis_node(state: AgentState) -> AgentState:
    state["current_agent"] = "evidence_analysis"
    return state
