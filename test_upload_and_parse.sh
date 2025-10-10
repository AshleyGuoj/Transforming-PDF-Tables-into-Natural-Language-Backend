#!/bin/bash

echo "=== Testing PDF Upload and Parse ==="

# 1. Upload a new PDF file (using test.pdf from current directory)
echo -e "\n1. Uploading PDF file..."
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/projects/1/files" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool

# Extract file_id from response
FILE_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['file_id'])" 2>/dev/null)

if [ -z "$FILE_ID" ]; then
    echo "❌ Failed to upload file"
    exit 1
fi

echo -e "\n✅ File uploaded successfully. File ID: $FILE_ID"

# 2. Trigger parse
echo -e "\n2. Triggering parse for file $FILE_ID..."
PARSE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/files/$FILE_ID/parse" \
  -H "Content-Type: application/json")

echo "Parse Response:"
echo "$PARSE_RESPONSE" | python3 -m json.tool

# 3. Check parse status (wait a bit first)
echo -e "\n3. Waiting 5 seconds for parsing to complete..."
sleep 5

echo "Checking parse status..."
STATUS_RESPONSE=$(curl -s "http://localhost:8000/api/v1/files/$FILE_ID/parse-status")

echo "Status Response:"
echo "$STATUS_RESPONSE" | python3 -m json.tool

# 4. Check if tables were extracted
TABLES_RESPONSE=$(curl -s "http://localhost:8000/api/v1/files/$FILE_ID/tables")

echo -e "\n4. Extracted tables:"
echo "$TABLES_RESPONSE" | python3 -m json.tool

echo -e "\n=== Test Complete ==="
