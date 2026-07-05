"""End-to-end test of all forensic tools via API."""
import os
import sys
import json
import time
import requests

BASE_URL = "http://localhost:8000"
TEMP = os.environ.get("TEMP", "/tmp")

# Login
resp = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "insp_verma",
    "password": "Inspector@1234"
})
if resp.status_code != 200:
    print(f"LOGIN FAILED: {resp.status_code} {resp.text[:200]}")
    sys.exit(1)

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("LOGIN OK\n")

results = {}

def test_tool(tool_key, filepath, extra_params=None):
    """Execute a tool and report results."""
    print(f"--- {tool_key} ---")
    start = time.time()

    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f)}
        data = extra_params or {}
        resp = requests.post(
            f"{BASE_URL}/api/forensic-toolkit/execute/{tool_key}",
            headers=headers,
            files=files,
            data=data
        )

    elapsed = time.time() - start

    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
        results[tool_key] = {"status": "HTTP_ERROR", "code": resp.status_code}
        return

    d = resp.json()
    status = d.get("status", "unknown")
    error = d.get("error_message") or d.get("output_data", {}).get("error", "")
    exec_time = d.get("execution_time_ms", 0)
    confidence = d.get("confidence_score")
    output = d.get("output_data", {})

    # Key fields to display
    key_fields = {}
    for k in ["method", "model_used", "text", "faces_detected", "minutiae_extracted",
              "loci_found", "embedding_generated", "page_count", "objects_detected",
              "hash_sha256", "language_detected", "segment_count", "pipeline_results"]:
        if k in output:
            v = output[k]
            if isinstance(v, str) and len(v) > 80:
                key_fields[k] = v[:80] + "..."
            elif isinstance(v, dict):
                key_fields[k] = f"(dict: {len(v)} keys)"
            elif isinstance(v, list):
                key_fields[k] = f"(list: {len(v)} items)"
            else:
                key_fields[k] = v

    print(f"  Status: {status} | Time: {exec_time}ms | Confidence: {confidence}")
    if error:
        print(f"  Error: {error}")
    for k, v in key_fields.items():
        print(f"  {k}: {v}")
    print()

    results[tool_key] = {
        "status": status,
        "execution_time_ms": exec_time,
        "confidence": confidence,
        "error": error if error else None,
        "key_output": key_fields
    }

# Test all tools
pdf_path = os.path.join(TEMP, "test.pdf")
img_path = os.path.join(TEMP, "test_image.png")
fp_path = os.path.join(TEMP, "test_fingerprint.png")
dna_path = os.path.join(TEMP, "test_dna.txt")
audio_path = os.path.join(TEMP, "test_audio.wav")

# Phase 1: Quick tools
test_tool("document_pdf_parse", pdf_path)
test_tool("image_ocr", img_path)
test_tool("image_exif", img_path)
test_tool("digital_hash", pdf_path)

# Phase 2: AI tools
test_tool("image_object_detect", img_path)
test_tool("face_detect", img_path)
test_tool("fingerprint_match", fp_path)
test_tool("dna_search", dna_path)

# Phase 3: Heavy AI tools
test_tool("face_recognize", img_path)
test_tool("image_similarity", img_path)
test_tool("audio_transcribe", audio_path)

# Phase 4: Multi-model pipeline
test_tool("crime_scene_analysis", img_path)

# Summary
print("\n" + "=" * 60)
print("FINAL RESULTS SUMMARY")
print("=" * 60)
passed = 0
failed = 0
for tool, r in results.items():
    status_icon = "PASS" if r["status"] == "completed" else "FAIL"
    if r["status"] == "completed":
        passed += 1
    else:
        failed += 1
    print(f"  [{status_icon}] {tool}: {r['status']} ({r.get('execution_time_ms',0)}ms)")
    if r.get("error"):
        print(f"         Error: {r['error']}")

print(f"\nTotal: {passed + failed} | Passed: {passed} | Failed: {failed}")
print(f"Pass Rate: {passed/(passed+failed)*100:.0f}%")
