# CrimeGPT Performance Report

**Date:** 2026-07-03  
**Environment:** Docker Desktop on Windows 11, 4 containers

---

## API Response Times

| Endpoint | Average Response Time | Under Load (10 concurrent) |
|----------|----------------------|---------------------------|
| /api/health | 223ms | 467ms |
| /api/dashboard/stats | 277ms | 610-793ms |
| /api/cases/ | 232ms | ~600ms |
| /api/criminal-intelligence/ | 241ms | ~650ms |
| /api/forensic-toolkit/tools | 252ms | ~700ms |
| /api/admin/users | 240ms | ~650ms |
| /api/ai-investigation/sessions | 232ms | ~600ms |

**Note:** Latency includes Docker network overhead on Windows (typically adds 150-200ms vs native Linux).

---

## Forensic Tool Execution Times (Cached Models)

| Tool | Execution Time |
|------|---------------|
| digital_hash | 15ms |
| digital_metadata | 22ms |
| image_exif | 12ms |
| image_ocr | 633ms |
| image_object_detect | 561ms |
| face_detect | ~300ms |
| face_recognize | ~400ms |
| vehicle_detect | ~500ms |
| license_plate_ocr | ~200ms |
| weapon_detect | ~500ms |
| document_pdf_parse | ~100ms |
| audio_transcribe | ~5000ms (1s audio) |
| crime_scene_analysis | ~2000ms (multi-tool) |

---

## Concurrent Request Handling

| Scenario | Requests | All Success | Max Latency |
|----------|----------|-------------|-------------|
| 10 parallel API calls | 10 | Yes (100%) | 793ms |
| AI Investigation (5 parallel tools) | 5 | Yes (100%) | 633ms (longest tool) |

---

## Resource Usage

| Container | Memory Limit | Typical Usage |
|-----------|-------------|---------------|
| Backend | 4GB | ~800MB (with ML models loaded) |
| Frontend | 1GB | ~300MB (Vite + esbuild) |
| PostgreSQL | 1GB | ~200MB |
| Qdrant | 1GB | ~150MB |

---

## First-Run vs Cached Performance

| Operation | First Run | Cached |
|-----------|-----------|--------|
| YOLO model load | 7s | <100ms |
| InsightFace load | 60s (download) | <1s |
| Whisper model load | 30s (download) | <1s |
| Vite page compile | 2-3s | Instant (HMR) |

---

## Bottlenecks Identified

1. **Docker on Windows:** Adds ~150-200ms overhead per request due to WSL2 networking
2. **First-run model downloads:** Up to 60s for InsightFace; mitigated by caching
3. **Gemini API latency:** 2-5s for report generation (external dependency)
4. **Audio transcription:** ~5s per second of audio (CPU-only Whisper)

---

## Recommendations

1. Pre-warm ML models at container startup (add model download to Dockerfile)
2. For production: use GPU-enabled container for 10x faster ML inference
3. Consider Redis caching for frequently-accessed dashboard stats
4. Database connection pooling (currently direct async connections)
