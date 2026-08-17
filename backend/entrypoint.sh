#!/bin/sh
# Ensure data directories exist and are writable by appuser
mkdir -p /app/data/forensics/executions /app/data/uploads /app/data/legal_docs /app/data/ai-investigation

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
