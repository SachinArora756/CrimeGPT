# CrimeGPT Bug Fix Report

**Date:** 2026-07-03  
**Testing Phase:** Full QA Cycle

---

## Bugs Found and Fixed

### BUG-001: Frontend Infinite Loading (Critical)

**Symptom:** Clicking any sidebar section shows loading skeleton but never renders the page content.

**Root Cause:** Frontend Docker container inherited a 256MB memory limit from the production `docker-compose.yml`. The development override uses Vite + esbuild for on-the-fly TypeScript transformation. esbuild's child process was being OOM-killed by Docker's memory cgroup, causing the error "The service is no longer running" from the `vite:esbuild` plugin. Once esbuild died, all lazy-loaded page components hung in `<Suspense>` fallback indefinitely.

**Fix:** Added `deploy.resources.limits.memory: 1G` to the frontend service in `docker-compose.override.yml`.

**File Changed:** `docker-compose.override.yml`

**Verification:**
- All 20 frontend page modules now compile and serve (HTTP 200)
- Container stays healthy under sustained use
- Zero TypeScript compilation errors

---

### BUG-002: AI Investigation Parallel Tool Execution Failure (Critical)

**Symptom:** During AI Investigation, tools executed in parallel (via `asyncio.gather`) would fail with "Session is already flushing" error. Only the first tool in each parallel group would succeed; the rest would report "failed".

**Root Cause:** The `execute_single_tool` function received a shared `AsyncSession` parameter and called `await db.flush()` multiple times. When tools ran concurrently via `asyncio.gather`, multiple coroutines attempted to flush the same session simultaneously, violating SQLAlchemy's async session contract (one operation at a time per session).

**Fix:** Modified `execute_single_tool` in `ai_investigation_service.py` to create its own independent database session using `async with async_session() as own_db:` instead of sharing the caller's session. Each parallel tool now has complete session isolation.

**File Changed:** `backend/app/services/ai_investigation_service.py`

**Verification:**
- Ran investigation 3 times with 5 parallel tools each
- All tools complete successfully (0 failures)
- Execution records properly stored in database
- No "Session is already flushing" errors in logs

---

### BUG-003: TypeScript Type Error (Low)

**Symptom:** `npx tsc --noEmit` reported: `Argument of type 'string | null' is not assignable to parameter of type 'string'` at line 150 of AIInvestigationPage.tsx.

**Root Cause:** `sessionId` variable is typed as `string | null` (initialized from `activeSession` state which starts null). However, by line 150, it's always guaranteed to be a string (either it was already set, or it was assigned from the API response 27 lines earlier).

**Fix:** Added non-null assertion operator (`!`) — `startInvestigation(sessionId!)`.

**File Changed:** `frontend/src/pages/forensics/AIInvestigationPage.tsx`

**Verification:** `npx tsc --noEmit` produces zero errors.

---

## Regression Testing

After all fixes were applied:

| Test | Result |
|------|--------|
| All containers healthy | PASS |
| All frontend pages load | PASS |
| All backend endpoints respond | PASS |
| AI Investigation full pipeline | PASS |
| All 19 forensic tools | PASS |
| Authentication flows | PASS |
| TypeScript compilation | 0 errors |
| Backend auto-reload | PASS |
