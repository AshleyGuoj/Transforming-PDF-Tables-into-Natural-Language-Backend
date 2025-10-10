#!/bin/bash

# Test script to verify parse status fix
# This script tests that the parse status endpoint returns page_count and updates correctly

set -e

API_BASE="http://localhost:8000/api/v1"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGd1aWRlbGluZS10cmFuc2Zvcm0uY29tIiwib3JnX2lkIjoxLCJvcmdhbml6YXRpb25fcm9sZSI6ImFkbWluIiwicHJvamVjdF9pZCI6MSwicHJvamVjdF9yb2xlIjoiYWRtaW4iLCJleHAiOjE3NjAxOTYyMzIsImlhdCI6MTc2MDEwOTgzMn0.RYIhgbvNbYNwqEukK-_1tv415TMS6KYXKoTyaWy0M3Y"

echo "🧪 Testing Parse Status Fix"
echo "=============================="
echo ""

# Check if file_id argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file_id>"
    echo "Example: $0 1"
    exit 1
fi

FILE_ID=$1

echo "📊 Step 1: Checking parse status for file $FILE_ID"
echo "----------------------------------------------"
STATUS_RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "${API_BASE}/files/${FILE_ID}/parse-status")

echo "$STATUS_RESPONSE" | jq .

echo ""
echo "✅ Checking if response contains required fields:"
echo "----------------------------------------------"

# Check if page_count exists
PAGE_COUNT=$(echo "$STATUS_RESPONSE" | jq -r '.page_count')
if [ "$PAGE_COUNT" != "null" ] && [ -n "$PAGE_COUNT" ]; then
    echo "✅ page_count: $PAGE_COUNT"
else
    echo "❌ page_count is missing or null"
fi

# Check if tables_found exists
TABLES_FOUND=$(echo "$STATUS_RESPONSE" | jq -r '.tables_found')
if [ "$TABLES_FOUND" != "null" ] && [ -n "$TABLES_FOUND" ]; then
    echo "✅ tables_found: $TABLES_FOUND"
else
    echo "❌ tables_found is missing or null"
fi

# Check status
STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
echo "📈 Current status: $STATUS"

echo ""
echo "=============================="
echo "Test completed!"
