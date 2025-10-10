# Testing Guide: Parse Status Fix

## Quick Test Steps

### 1. Start the Backend
```bash
cd backend
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 2. Start the Frontend
```bash
cd frontend_updated
npm run dev
```

**Expected output:**
```
▲ Next.js 14.x.x
- Local:        http://localhost:3000
```

### 3. Test the Upload and Parse Flow

#### Step 3.1: Upload a PDF
1. Navigate to http://localhost:3000/console/project
2. Select or create a project
3. Click "Upload File"
4. Select a PDF file (e.g., `test.pdf`)
5. Click "上传并解析" (Upload and Parse)

**What to watch for in browser console:**
```javascript
📡 FilesAPI.upload 开始
✅ 上传成功
🧠 触发文件 X 的解析...
✅ 解析已启动
```

#### Step 3.2: Monitor Parse Status
The frontend will automatically poll every 2 seconds.

**Browser console should show:**
```javascript
📊 解析状态更新: {
  file_id: 1,
  status: "processing",
  tables_found: 0,
  page_count: 0,
  timestamp: "2025-10-10T10:00:00.000Z"
}

⏳ 解析进行中 (processing)，2秒后继续检查...

📊 解析状态更新: {
  file_id: 1,
  status: "processing",
  tables_found: 0,
  page_count: 0,
  timestamp: "2025-10-10T10:00:02.000Z"
}

// ... continues polling ...

📊 解析状态更新: {
  file_id: 1,
  status: "completed",
  tables_found: 3,
  page_count: 15,
  timestamp: "2025-10-10T10:01:30.000Z"
}

🎉 解析完成！ {
  file_id: 1,
  fileName: "test.pdf",
  pages: 15,
  tables: 3
}

🔄 刷新文件列表，显示最新的页数和表格数...
✅ 文件列表已刷新
```

#### Step 3.3: Verify UI Updates
After parsing completes:

**File list should show:**
```
┌─────────────────────────────────────────────────────┐
│ test.pdf                                            │
│ 15 pages | 3 tables | Status: 已完成              │
│ Uploaded: 2025-10-10 | Size: 2.3 MB                │
└─────────────────────────────────────────────────────┘
```

**Backend logs should show:**
```
INFO: Azure analysis completed for file 1
INFO: Document has 15 pages
INFO: Extracted table 1 from page 3 with 8x4 cells
INFO: Extracted table 2 from page 7 with 10x5 cells
INFO: Extracted table 3 from page 12 with 6x3 cells
INFO: Updated version metadata: 15 pages, 3 tables
INFO: Azure parsing completed for file 1. Extracted 3 tables from 15 pages.
```

### 4. API Testing (Manual)

#### Test Parse Status Endpoint
```bash
curl -X GET \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGd1aWRlbGluZS10cmFuc2Zvcm0uY29tIiwib3JnX2lkIjoxLCJvcmdhbml6YXRpb25fcm9sZSI6ImFkbWluIiwicHJvamVjdF9pZCI6MSwicHJvamVjdF9yb2xlIjoiYWRtaW4iLCJleHAiOjE3NjAxOTYyMzIsImlhdCI6MTc2MDEwOTgzMn0.RYIhgbvNbYNwqEukK-_1tv415TMS6KYXKoTyaWy0M3Y" \
  http://localhost:8000/api/v1/files/1/parse-status | jq
```

**Expected response:**
```json
{
  "file_id": 1,
  "file_name": "test.pdf",
  "status": "completed",
  "tables_found": 3,
  "page_count": 15,
  "processing_error": null,
  "created_at": "2025-10-10T10:00:00",
  "completed_at": "2025-10-10T10:01:30"
}
```

#### Or use the test script:
```bash
./test_parse_status_fix.sh 1
```

## Common Issues and Solutions

### Issue 1: Status stays "processing" forever

**Symptoms:**
- Frontend keeps polling
- Status never changes to "completed"
- Page count stays 0

**Debug steps:**
```bash
# Check backend logs
tail -f backend.log

# Look for errors like:
ERROR: Azure parsing failed for file X: <error message>
```

**Solutions:**
- Verify Azure credentials in `backend/.env`:
  ```
  AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://...
  AZURE_DOCUMENT_INTELLIGENCE_KEY=...
  ```
- Check if the file exists at the storage path
- Ensure Azure API quota is not exceeded

### Issue 2: page_count returns 0 even when completed

**Debug steps:**
```bash
# Check database directly (SQLite example)
sqlite3 backend/grandscale.db "SELECT version_id, llm_params FROM file_version WHERE file_id = 1;"
```

**Expected output:**
```
1|{"page_count": 15, "table_count": 3}
```

**Solutions:**
- Verify that `result.pages` exists in Azure response
- Check backend logs for: `INFO: Document has X pages`
- Ensure `await db.commit()` is called in `parse_with_azure()`

### Issue 3: TypeScript errors in frontend

**Error:**
```
Property 'page_count' does not exist on type '...'
```

**Solution:**
- Restart the frontend development server:
  ```bash
  cd frontend_updated
  npm run dev
  ```
- Clear Next.js cache:
  ```bash
  rm -rf .next
  npm run dev
  ```

### Issue 4: File list doesn't refresh

**Symptoms:**
- Parse completes successfully
- Console shows "✅ 解析完成"
- But file list still shows 0 pages/tables

**Debug:**
- Check browser console for errors in `loadProjectFiles()`
- Verify that `handleViewProject()` is called after parsing

**Solution:**
- The fix includes automatic refresh after parsing completes
- Try manually refreshing the page
- Check that `selectedProject` state is set correctly

## Success Criteria

✅ **Backend:**
- Azure parsing extracts page count
- Page count stored in FileVersion.llm_params
- /parse-status returns page_count field
- File.status changes from "in_progress" to "completed"
- Backend logs show page count

✅ **Frontend:**
- Polling starts after upload
- Console logs show status updates every 2s
- Polling stops when status === "completed"
- File list shows actual page count
- File list shows actual table count
- UI updates without manual refresh

✅ **Database:**
- FileVersion.llm_params contains page_count
- FileVersion.llm_params contains table_count
- File.status = "completed"
- FileTable records exist for each extracted table

## Performance Notes

- **Parse time**: Typically 10-60 seconds depending on PDF complexity
- **Polling interval**: 2 seconds (configurable in FilesGuidelines.tsx:387)
- **API calls**: N+1 queries when loading file list (1 for files + N for parse status)
  - Future optimization: Add page_count/table_count to file list endpoint

## Next Steps After Testing

If all tests pass:
1. Commit the changes
2. Push to feature branch
3. Create pull request
4. Consider implementing these improvements:
   - Add WebSocket for real-time status updates
   - Optimize file list loading (single query)
   - Add database migration for dedicated page_count column
   - Add retry logic for failed parses
