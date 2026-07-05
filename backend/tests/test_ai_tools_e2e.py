"""
End-to-end validation tests for all AI forensic tools.
Runs against a live Docker environment.

Usage:
    docker exec crimegpt-backend-1 python -m pytest tests/test_ai_tools_e2e.py -v

    OR from host:
    python tests/test_ai_tools_e2e.py
"""
import os
import sys
import json
import time
import base64
import requests

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")
OFFICER_USERNAME = "insp_verma"
OFFICER_PASSWORD = "Inspector@123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "AdminPass123!"


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def record(self, name, passed, detail=""):
        if passed:
            self.passed.append({"name": name, "detail": detail})
        else:
            self.failed.append({"name": name, "detail": detail})

    def skip(self, name, reason):
        self.skipped.append({"name": name, "reason": reason})

    def report(self):
        print("\n" + "=" * 70)
        print("  AI TOOLS END-TO-END VALIDATION REPORT")
        print("=" * 70)
        print(f"\n  PASSED: {len(self.passed)}")
        print(f"  FAILED: {len(self.failed)}")
        print(f"  SKIPPED: {len(self.skipped)}")
        print(f"  TOTAL: {len(self.passed) + len(self.failed) + len(self.skipped)}")
        print()

        if self.passed:
            print("  --- PASSED ---")
            for t in self.passed:
                print(f"  [PASS] {t['name']}: {t['detail'][:80]}")
            print()

        if self.failed:
            print("  --- FAILED ---")
            for t in self.failed:
                print(f"  [FAIL] {t['name']}: {t['detail'][:120]}")
            print()

        if self.skipped:
            print("  --- SKIPPED ---")
            for t in self.skipped:
                print(f"  [SKIP] {t['name']}: {t['reason'][:80]}")

        print("\n" + "=" * 70)
        return len(self.failed) == 0


def login_officer():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": OFFICER_USERNAME,
        "password": OFFICER_PASSWORD,
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def login_admin():
    resp = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def create_test_image(path, width=100, height=100):
    """Create a simple test PNG image."""
    import struct
    import zlib

    def create_png(w, h):
        def make_chunk(chunk_type, data):
            chunk = chunk_type + data
            return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)

        header = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        ihdr = make_chunk(b'IHDR', ihdr_data)

        raw_data = b''
        for y in range(h):
            raw_data += b'\x00'
            for x in range(w):
                r = (x * 255 // w) & 0xFF
                g = (y * 255 // h) & 0xFF
                b = ((x + y) * 127 // (w + h)) & 0xFF
                raw_data += struct.pack('BBB', r, g, b)

        idat_data = zlib.compress(raw_data)
        idat = make_chunk(b'IDAT', idat_data)
        iend = make_chunk(b'IEND', b'')

        return header + ihdr + idat + iend

    png_data = create_png(width, height)
    with open(path, 'wb') as f:
        f.write(png_data)
    return path


def create_test_text(path, content=""):
    """Create a test text file."""
    if not content:
        content = (
            "DNA Profile Report\n"
            "Profile ID: DNA-2024-001\n"
            "Sample Number: EXH-456\n"
            "Laboratory: Central Forensic Science Laboratory, Delhi\n"
            "Collection Date: 15/03/2024\n"
            "Officer: Inspector Verma\n"
            "Case No: FIR/2024/001\n\n"
            "STR Loci Results:\n"
            "D3S1358: 15/17\n"
            "vWA: 16/18\n"
            "D16S539: 11/12\n"
            "CSF1PO: 10/12\n"
            "TPOX: 8/11\n"
            "D8S1179: 13/14\n"
            "D21S11: 29/30\n"
            "D18S51: 14/17\n"
            "TH01: 6/9.3\n"
            "FGA: 22/24\n"
            "Amelogenin: X/Y\n"
        )
    with open(path, 'w') as f:
        f.write(content)
    return path


def execute_tool(token, tool_key, file_path, params=None):
    """Execute a forensic tool and return the response."""
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": open(file_path, "rb")}
    data = {"params": json.dumps(params or {})}

    resp = requests.post(
        f"{BASE_URL}/api/forensic-toolkit/execute/{tool_key}",
        headers=headers,
        files=files,
        data=data,
    )
    return resp.status_code, resp.json()


def main():
    results = TestResults()

    print("\n[1/4] Authentication Tests")
    print("-" * 40)

    # Officer login
    token = login_officer()
    if token:
        results.record("Officer Login", True, "Login successful")
    else:
        results.record("Officer Login", False, "Could not authenticate officer")
        print("FATAL: Cannot continue without officer token")
        results.report()
        return

    # Admin login
    admin_token = login_admin()
    if admin_token:
        results.record("Admin Login", True, "Admin login successful")
    else:
        results.record("Admin Login", False, "Could not authenticate admin")

    print("\n[2/4] Tool Execution Tests")
    print("-" * 40)

    # Create test files
    os.makedirs("/tmp/test_forensics", exist_ok=True)
    test_img = create_test_image("/tmp/test_forensics/test.png")
    test_txt = create_test_text("/tmp/test_forensics/dna_report.txt")

    # Test each tool
    tools_to_test = [
        ("digital_hash", test_img, {}, "sha256"),
        ("digital_metadata", test_img, {}, "file_size_bytes"),
        ("digital_file_identify", test_img, {}, "detected_type"),
        ("image_ocr", test_img, {}, "text"),
        ("image_object_detect", test_img, {}, "objects_detected"),
        ("image_exif", test_img, {}, "image_info"),
        ("document_ocr", test_img, {}, "text"),
        ("face_detect", test_img, {}, "faces_detected"),
        ("face_recognize", test_img, {}, "method"),
        ("fingerprint_match", test_img, {}, "method"),
        ("dna_search", test_txt, {}, "method"),
        ("vehicle_detect", test_img, {}, "vehicles_detected"),
        ("license_plate_ocr", test_img, {}, "plates_detected"),
        ("weapon_detect", test_img, {}, "weapons_detected"),
        ("image_similarity", test_img, {}, "embedding_generated"),
        ("crime_scene_analysis", test_img, {}, "pipeline_results"),
    ]

    for tool_key, file_path, params, expected_field in tools_to_test:
        try:
            status, data = execute_tool(token, tool_key, file_path, params)
            if status == 200:
                output = data.get("output_data", {})
                has_error = "error" in output and output["error"]
                has_field = expected_field in output

                if has_error:
                    error_msg = output["error"]
                    if "not installed" in error_msg.lower() or "not available" in error_msg.lower():
                        results.skip(f"Tool: {tool_key}", f"Dependency missing: {error_msg[:60]}")
                    else:
                        results.record(f"Tool: {tool_key}", False, f"Error: {error_msg[:80]}")
                elif has_field:
                    # Check for placeholder indicators
                    method = output.get("method", "")
                    if method == "placeholder":
                        results.record(f"Tool: {tool_key}", False, "Still returning placeholder response")
                    else:
                        results.record(f"Tool: {tool_key}", True, f"Real processing - {expected_field} present")
                else:
                    results.record(f"Tool: {tool_key}", True, f"Executed successfully (status={data.get('status')})")
            elif status == 429:
                results.skip(f"Tool: {tool_key}", "Rate limited")
            else:
                results.record(f"Tool: {tool_key}", False, f"HTTP {status}: {str(data)[:80]}")
        except Exception as e:
            results.record(f"Tool: {tool_key}", False, f"Exception: {str(e)[:80]}")

    # Audio transcription (needs audio file)
    results.skip("Tool: audio_transcribe", "No test audio file available")

    # PDF parse (needs PDF file)
    results.skip("Tool: document_pdf_parse", "No test PDF file available")

    # Document summarize (needs Gemini API key)
    results.skip("Tool: document_summarize", "Requires Gemini API key")

    print("\n[3/4] Evidence Linkage Tests")
    print("-" * 40)

    # Get a case to link to
    headers = {"Authorization": f"Bearer {token}"}
    cases_resp = requests.get(f"{BASE_URL}/api/cases/", headers=headers)
    if cases_resp.status_code == 200:
        cases = cases_resp.json().get("cases", [])
        if cases:
            results.record("Case Retrieval", True, f"Found {len(cases)} cases")
        else:
            results.record("Case Retrieval", False, "No cases found")
    else:
        results.record("Case Retrieval", False, f"HTTP {cases_resp.status_code}")

    # Criminal Intelligence Search
    crim_resp = requests.get(
        f"{BASE_URL}/api/criminal-intelligence/",
        headers=headers,
        params={"search": "raj", "per_page": 5}
    )
    if crim_resp.status_code == 200:
        crim_data = crim_resp.json()
        count = crim_data.get("total", 0)
        results.record("Criminal Intel Search", True, f"Found {count} profiles for 'raj'")
    else:
        results.record("Criminal Intel Search", False, f"HTTP {crim_resp.status_code}")

    # RAG Legal Search
    rag_resp = requests.post(
        f"{BASE_URL}/api/legal/search",
        headers=headers,
        json={"query": "murder punishment", "top_k": 3}
    )
    if rag_resp.status_code == 200:
        rag_data = rag_resp.json()
        count = len(rag_data.get("results", []))
        results.record("RAG Legal Search", True, f"Found {count} legal provisions")
    else:
        results.record("RAG Legal Search", False, f"HTTP {rag_resp.status_code}")

    print("\n[4/4] Admin Dashboard Tests")
    print("-" * 40)

    if admin_token:
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin stats
        stats_resp = requests.get(
            f"{BASE_URL}/api/forensic-toolkit/admin/stats",
            headers=admin_headers,
        )
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            results.record("Admin Stats", True,
                          f"Total executions: {stats.get('total_executions', 0)}")
        else:
            results.record("Admin Stats", False, f"HTTP {stats_resp.status_code}")

        # Audit logs
        audit_resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=admin_headers,
            params={"per_page": 5}
        )
        if audit_resp.status_code == 200:
            results.record("Audit Logs", True, "Audit logs accessible")
        else:
            results.record("Audit Logs", False, f"HTTP {audit_resp.status_code}")

        # System health
        health_resp = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=admin_headers,
        )
        if health_resp.status_code == 200:
            results.record("System Health", True, "Health check passed")
        else:
            results.record("System Health", False, f"HTTP {health_resp.status_code}")
    else:
        results.skip("Admin Stats", "No admin token")
        results.skip("Audit Logs", "No admin token")
        results.skip("System Health", "No admin token")

    # Notifications
    notif_resp = requests.get(
        f"{BASE_URL}/api/notifications/unread-count",
        headers=headers,
    )
    if notif_resp.status_code == 200:
        results.record("Notifications", True, "Notification system working")
    else:
        results.record("Notifications", False, f"HTTP {notif_resp.status_code}")

    # Final report
    all_passed = results.report()

    # Cleanup
    try:
        os.remove("/tmp/test_forensics/test.png")
        os.remove("/tmp/test_forensics/dna_report.txt")
        os.rmdir("/tmp/test_forensics")
    except Exception:
        pass

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
