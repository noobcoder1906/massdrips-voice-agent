#!/bin/bash
# This script triggers an outbound call to your phone number using the FastAPI backend.
# Ensure your backend is running (uvicorn backend.main:app) before executing this.

curl -X POST http://localhost:8000/api/v1/calls/single \
-H "Content-Type: application/json" \
-d '{
    "to_number": "+918838600208", 
    "tenant_id": "tenant_123"
}'

echo ""
echo "Call triggered! Check your phone."
