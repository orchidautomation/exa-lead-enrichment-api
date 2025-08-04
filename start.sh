#!/bin/bash
# Startup script for exa-lead-enrichment-api

echo "Starting Exa Lead Enrichment API..."
echo "Checking environment variables..."

# Only check for the required variables for THIS service
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY is not set"
    exit 1
fi

if [ -z "$EXA_API_KEY" ]; then
    echo "ERROR: EXA_API_KEY is not set"
    exit 1
fi

echo "✓ OPENROUTER_API_KEY is set"
echo "✓ EXA_API_KEY is set"
echo "Starting gunicorn..."

# Start the service
exec gunicorn wsgi:app --bind 0.0.0.0:${PORT:-5001} --workers 1 --timeout 120 --preload --access-logfile - --error-logfile -