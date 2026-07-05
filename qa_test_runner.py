import requests, json, time, os, sys

BASE = 'http://localhost:8000'
TEST_DIR = '/app/data/qa_tests'
RESULTS = []

# Login
r = requests.post(f'{BASE}/api/auth/login', json={'username': 'insp_verma', 'password': 'Inspector@1234'})
if r.status_code != 200:
    print(f"LOGIN FAILED: {r.status_code} {r.text}")
    sys.exit(1)
TOKEN = r.json()['access_token']
HEADERS = {'Authorization': f'Bearer {TOKEN}'}
print(f"Logged in as insp_verma, token: {TOKEN[:20]}...")
print()

def summarize_output(tool_key, data):
    if not data:
        return 'No output'
    err = data.get('error')
    if err:
        return f'ERROR: {str(err)[:100]}'
    try:
        if tool_key == 'digital_hash':
            return f"SHA256={data.get('sha256','?')[:16]}..."
        elif tool_key == 'digital_metadata':
            return f"{data.get('mime_type','?')} {data.get('file_size_readable','?')}"
        elif tool_key == 'digital_file_identify':
            return f"Type={data.get('detected_type','?')}"
        elif tool_key == 'image_ocr':
            return f"Chars={data.get('char_count',0)}, Lines={data.get('line_count',0)}"
        elif tool_key == 'image_object_detect':
            return f"Objects={data.get('objects_detected',0)}"
        elif tool_key == 'image_exif':
            return f"EXIF={data.get('exif_available',False)}, Tags={data.get('exif_tags_count',0)}"
        elif tool_key == 'image_similarity':
            return f"Matches={data.get('matches_found',0)}, DB={data.get('database_records_searched',0)}"
        elif tool_key == 'face_detect':
            return f"Faces={data.get('faces_detected',0)}, Method={data.get('method','?')}"
        elif tool_key == 'face_recognize':
            return f"Faces={data.get('faces_detected',0)}, Matches={data.get('matches_found',0)}"
        elif tool_key == 'fingerprint_match':
            return f"Minutiae={data.get('minutiae_extracted',0)}, Matches={data.get('matches_found',0)}"
        elif tool_key == 'dna_search':
            profile = data.get('extracted_profile', {})
            loci = profile.get('loci', {}) if profile else {}
            return f"Parsed={data.get('report_parsed',False)}, Loci={len(loci)}"
        elif tool_key == 'vehicle_detect':
            return f"Vehicles={data.get('vehicles_detected',0)}"
        elif tool_key == 'license_plate_ocr':
            plates = data.get('plates', [])
            texts = [p.get('text','') for p in plates] if plates else []
            return f"Plates={data.get('plates_detected',0)}, Text={texts}"
        elif tool_key == 'weapon_detect':
            return f"Weapons={data.get('weapons_detected',0)}"
        elif tool_key == 'audio_transcribe':
            return f"Text={data.get('text','')[:50]}"
        elif tool_key == 'document_ocr':
            return f"Chars={data.get('char_count',0)}, Pages={data.get('pages_processed',0)}"
        elif tool_key == 'document_pdf_parse':
            return f"Chars={data.get('char_count',0)}, Pages={data.get('page_count',0)}, Tables={data.get('tables_found',0)}"
        elif tool_key == 'document_summarize':
            return f"Summary={data.get('summary','')[:80]}"
        elif tool_key == 'crime_scene_analysis':
            return f"Persons={data.get('persons_count',0)}, Vehicles={data.get('vehicles_count',0)}, Threat={data.get('threat_assessment','?')}"
    except Exception as ex:
        return f"Parse error: {str(ex)[:60]}"
    return f"Keys: {list(data.keys())[:5]}"

def run_tool(tool_key, filename, case_id=None, params='{}'):
    filepath = f'{TEST_DIR}/{filename}'
    if not os.path.exists(filepath):
        return {'tool': tool_key, 'file': filename, 'status': 'SKIP', 'error': 'File not found', 'runtime_ms': 0}

    start = time.time()
    with open(filepath, 'rb') as f:
        files = {'file': (filename, f)}
        data = {'params': params}
        if case_id:
            data['case_id'] = str(case_id)

        try:
            r = requests.post(f'{BASE}/api/forensic-toolkit/execute/{tool_key}', headers=HEADERS, files=files, data=data, timeout=120)
            elapsed = round((time.time() - start) * 1000)

            if r.status_code in (200, 201):
                result = r.json()
                return {
                    'tool': tool_key,
                    'file': filename,
                    'status': result.get('status', 'unknown'),
                    'execution_id': result.get('execution_id'),
                    'confidence': result.get('confidence_score'),
                    'runtime_ms': result.get('execution_time_ms', elapsed),
                    'output_keys': list(result.get('output_data', {}).keys()) if result.get('output_data') else [],
                    'output_summary': summarize_output(tool_key, result.get('output_data', {})),
                    'error': result.get('error_message'),
                }
            else:
                return {'tool': tool_key, 'file': filename, 'status': 'HTTP_ERROR', 'error': f'{r.status_code}: {r.text[:200]}', 'runtime_ms': elapsed}
        except Exception as e:
            return {'tool': tool_key, 'file': filename, 'status': 'EXCEPTION', 'error': str(e)[:200], 'runtime_ms': round((time.time() - start) * 1000)}

print('=' * 70)
print('  CRIMEGPT AI TOOLKIT - COMPREHENSIVE QA TEST RUN')
print('=' * 70)
print()

# ============ MAIN TOOL TESTS ============
tests = [
    # Digital/Utility tools
    ('digital_hash', 'test_investigation.pdf', 11),
    ('digital_metadata', 'test_investigation.pdf', 11),
    ('digital_file_identify', 'test_investigation.pdf', 11),
    ('digital_file_identify', 'test_corrupt.jpg', None),

    # OCR tools
    ('image_ocr', 'test_ocr_document.png', 11),
    ('document_ocr', 'test_ocr_document.png', 11),
    ('document_pdf_parse', 'test_investigation.pdf', 11),
    ('document_summarize', 'test_investigation.pdf', 12),

    # Image analysis
    ('image_exif', 'test_exif_image.jpg', None),
    ('image_object_detect', 'test_crime_scene.jpg', 11),
    ('image_object_detect', 'test_vehicle_plate.jpg', 11),
    ('image_similarity', 'test_similar_1.jpg', None),

    # Face tools
    ('face_detect', 'test_face_single.jpg', 11),
    ('face_detect', 'test_faces_multiple.jpg', 11),
    ('face_recognize', 'test_face_single.jpg', 11),

    # Fingerprint
    ('fingerprint_match', 'test_fingerprint.png', 12),

    # DNA
    ('dna_search', 'test_dna_report.txt', 12),

    # Vehicle tools
    ('vehicle_detect', 'test_vehicle_plate.jpg', 11),
    ('license_plate_ocr', 'test_vehicle_plate.jpg', 11),
    ('license_plate_ocr', 'test_plate_closeup.jpg', 11),

    # Weapon detection
    ('weapon_detect', 'test_crime_scene.jpg', 11),

    # Audio
    ('audio_transcribe', 'test_audio_silence.wav', None),

    # Crime scene (composite)
    ('crime_scene_analysis', 'test_crime_scene.jpg', 11),
]

for tool_key, filename, case_id in tests:
    print(f'Testing: {tool_key} with {filename}...', end=' ', flush=True)
    result = run_tool(tool_key, filename, case_id)
    RESULTS.append(result)
    status = result['status']
    if status == 'COMPLETED':
        print(f'PASS [{result.get("runtime_ms","?")}ms] conf={result.get("confidence","?")} | {result.get("output_summary","")}')
    elif status == 'FAILED':
        print(f'FAIL [{result.get("runtime_ms","?")}ms] | {result.get("output_summary","") or result.get("error","")}')
    else:
        print(f'{status} | {result.get("error","")}')

print()
print('=' * 70)
print('  ERROR HANDLING TESTS')
print('=' * 70)
print()

# Error handling tests - test with wrong file types / corrupt files
error_tests = [
    ('image_ocr', 'test_corrupt.jpg', None),
    ('face_detect', 'test_corrupt.jpg', None),
    ('image_ocr', 'test_empty.txt', None),
    ('document_pdf_parse', 'test_corrupt.jpg', None),
    ('license_plate_ocr', 'test_fingerprint.png', None),
    ('fingerprint_match', 'test_ocr_document.png', None),
    ('dna_search', 'test_empty.txt', None),
]

for tool_key, filename, case_id in error_tests:
    print(f'Error test: {tool_key} with {filename}...', end=' ', flush=True)
    result = run_tool(tool_key, filename, case_id)
    result['test_type'] = 'error_handling'
    RESULTS.append(result)
    status = result['status']
    error_msg = result.get('output_summary', '') or result.get('error', '')
    print(f'{status} | {error_msg[:80]}')

# Summary
print()
print('=' * 70)
print('  SUMMARY')
print('=' * 70)
completed = sum(1 for r in RESULTS if r['status'] == 'COMPLETED')
failed = sum(1 for r in RESULTS if r['status'] == 'FAILED')
errors = sum(1 for r in RESULTS if r['status'] in ('HTTP_ERROR', 'EXCEPTION', 'SKIP'))
total = len(RESULTS)
print(f'  Total tests: {total}')
print(f'  COMPLETED (tool ran successfully): {completed}')
print(f'  FAILED (tool handled error gracefully): {failed}')
print(f'  ERRORS (unexpected failures): {errors}')
print()

# Save results JSON
with open('/app/data/qa_tests/results.json', 'w') as f:
    json.dump(RESULTS, f, indent=2, default=str)
print('Results saved to /app/data/qa_tests/results.json')
