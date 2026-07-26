"""Background Task Queue — asyncio-based in-process task runner.

Stores intermediate results in memory and persists final state to the database.
Frontend can poll /api/ai-investigation/sessions/{id}/status for progress.
"""
