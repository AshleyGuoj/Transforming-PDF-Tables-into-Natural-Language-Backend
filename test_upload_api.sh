#!/bin/bash

# Test file upload API endpoint
# This simulates what the frontend does

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGd1aWRlbGluZS10cmFuc2Zvcm0uY29tIiwib3JnX2lkIjoxLCJvcmdhbml6YXRpb25fcm9sZSI6ImFkbWluIiwicHJvamVjdF9pZCI6MSwicHJvamVjdF9yb2xlIjoiYWRtaW4iLCJleHAiOjE3NjAxOTYyMzIsImlhdCI6MTc2MDEwOTgzMn0.RYIhgbvNbYNwqEukK-_1tv415TMS6KYXKoTyaWy0M3Y"

PROJECT_ID=1

echo "🧪 Testing file upload API..."
echo "Project ID: $PROJECT_ID"
echo ""

# Check if test.pdf exists
if [ ! -f "test.pdf" ]; then
    echo "❌ test.pdf not found in current directory"
    exit 1
fi

echo "📤 Uploading test.pdf..."
curl -X POST "http://localhost:8000/api/v1/projects/${PROJECT_ID}/files" \
    -H "Authorization: Bearer ${TOKEN}" \
    -F "file=@test.pdf" \
    -v

echo ""
echo "✅ Upload test complete"
