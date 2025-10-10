# Parse Status Fix Summary

## Problem
The frontend continuously showed "解析中" (parsing) status and never updated to show completed files with their page and table counts.

### Root Cause
1. **Backend**: The Azure parsing logic didn't calculate or store `page_count`
2. **Backend**: The `/parse-status` endpoint didn't return `page_count` in the response
3. **Frontend**: The TypeScript API interface was missing the `page_count` field
4. **Frontend**: File list display hardcoded pages and tables to 0

## Solution Implemented

### 1. Backend Changes ([routes_parse_azure.py](backend/app/api/v1/routes_parse_azure.py))

#### Added Page Count Extraction (Line 214-216)
```python
# Get page count from result
page_count = len(result.pages) if result.pages else 0
logger.info(f"Document has {page_count} pages")
```

#### Updated ParseStatusResponse Model (Line 37-46)
```python
class ParseStatusResponse(BaseModel):
    """Response for parse status."""
    file_id: int
    file_name: str
    status: str
    tables_found: int
    page_count: int  # ✅ ADDED
    processing_error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
```

#### Store Metadata in FileVersion (Line 291-300)
```python
# Update active version with page count (stored in llm_params as metadata)
if file_obj.active_version_id:
    version_obj = await db.get(FileVersion, file_obj.active_version_id)
    if version_obj:
        # Store page_count and table_count in llm_params as metadata
        metadata = version_obj.llm_params or {}
        metadata['page_count'] = page_count
        metadata['table_count'] = len(tables_extracted)
        version_obj.llm_params = metadata
        logger.info(f"Updated version metadata: {page_count} pages, {len(tables_extracted)} tables")
```

#### Retrieve Metadata in get_parse_status (Line 356-363)
```python
# Get page count from active version metadata
page_count = 0
if file_obj.active_version_id:
    version_query = select(FileVersion).where(FileVersion.version_id == file_obj.active_version_id)
    version_result = await db.execute(version_query)
    version_obj = version_result.scalar_one_or_none()
    if version_obj and version_obj.llm_params:
        page_count = version_obj.llm_params.get('page_count', 0)
```

#### Added Logging (Line 374, 303)
```python
logger.info(f"Parse status for file {file_id}: status={status_map.get(file_obj.status, 'pending')}, tables={len(tables)}, pages={page_count}")
logger.info(f"Azure parsing completed for file {file_id}. Extracted {len(tables_extracted)} tables from {page_count} pages.")
```

### 2. Frontend Changes

#### Updated API Type Definition ([lib/api/index.ts](frontend_updated/lib/api/index.ts) Line 315-326)
```typescript
async getStatus(fileId: number) {
  return fetchAPI<{
    file_id: number;
    file_name: string;
    status: string;
    tables_found: number;
    page_count: number;  // ✅ ADDED
    processing_error?: string;
    created_at?: string;
    completed_at?: string;
  }>(`/files/${fileId}/parse-status`);
}
```

#### Updated File Loading Logic ([FilesGuidelines.tsx](frontend_updated/components/console/FilesGuidelines.tsx) Line 76-108)
```typescript
// Transform files to match component structure
const transformedFiles = await Promise.all(
  (filesResult.files || []).map(async (file: any) => {
    // Get parse status for each file to get page count and table count
    let pageCount = 0;
    let tableCount = 0;
    let fileStatus = 'pending';

    try {
      const parseStatus = await API.parse.getStatus(file.file_id);
      pageCount = parseStatus.page_count || 0;
      tableCount = parseStatus.tables_found || 0;
      fileStatus = parseStatus.status || 'pending';
      console.log(`📊 File ${file.file_id} parse status:`, parseStatus);
    } catch (error) {
      console.warn(`⚠️ Could not fetch parse status for file ${file.file_id}:`, error);
    }

    return {
      id: file.file_id,
      name: file.file_name,
      pages: pageCount,        // ✅ Now uses actual data
      tables: tableCount,       // ✅ Now uses actual data
      status: fileStatus,       // ✅ Now uses actual data
      uploadedAt: new Date(file.created_at).toLocaleDateString(),
      size: `${(file.file_size / 1024 / 1024).toFixed(1)} MB`,
      tasks: tableCount,
      completedTasks: 0,
      parsedTables: []
    };
  })
);
```

#### Enhanced Polling Logging ([FilesGuidelines.tsx](frontend_updated/components/console/FilesGuidelines.tsx) Line 327-390)
```typescript
const checkStatus = async () => {
  const status = await API.parse.getStatus(fileId);
  console.log('📊 解析状态更新:', {
    file_id: fileId,
    status: status.status,
    tables_found: status.tables_found,
    page_count: status.page_count,
    timestamp: new Date().toISOString()
  });

  if (status.status === 'completed') {
    console.log('🎉 解析完成！', {
      file_id: fileId,
      fileName: fileName,
      pages: status.page_count,
      tables: status.tables_found
    });
    // ... rest of completion logic
  }
};
```

## Key Changes Summary

| Component | File | Change |
|-----------|------|--------|
| Backend Model | `routes_parse_azure.py:43` | Added `page_count: int` to ParseStatusResponse |
| Backend Parsing | `routes_parse_azure.py:214-216` | Extract page count from Azure result |
| Backend Storage | `routes_parse_azure.py:291-300` | Store page_count in FileVersion.llm_params |
| Backend Retrieval | `routes_parse_azure.py:356-363` | Retrieve page_count from metadata |
| Backend Logging | `routes_parse_azure.py:303,374` | Log page count in parsing completion and status |
| Frontend API Type | `lib/api/index.ts:321` | Added `page_count: number` to getStatus response type |
| Frontend Display | `FilesGuidelines.tsx:76-108` | Fetch and use actual parse status data |
| Frontend Polling | `FilesGuidelines.tsx:327-390` | Enhanced logging for status updates |

## Testing

### Manual Testing
1. **Start Backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   cd frontend_updated
   npm run dev
   ```

3. **Test Flow**:
   - Upload a PDF file
   - Trigger parsing
   - Watch console logs for status updates
   - Verify that:
     - Status changes from "processing" → "completed"
     - Page count appears in file list
     - Table count appears in file list
     - Frontend stops polling after completion

### API Testing Script
Run the provided test script:
```bash
./test_parse_status_fix.sh <file_id>
```

Example:
```bash
./test_parse_status_fix.sh 1
```

Expected output:
```json
{
  "file_id": 1,
  "file_name": "test.pdf",
  "status": "completed",
  "tables_found": 3,
  "page_count": 15,
  "created_at": "2025-10-10T10:00:00",
  "completed_at": "2025-10-10T10:01:30"
}
```

### Verification Checklist
- ✅ Backend extracts page count from Azure result
- ✅ Backend stores page_count in FileVersion metadata
- ✅ Backend returns page_count in /parse-status response
- ✅ Frontend TypeScript types include page_count
- ✅ Frontend displays actual page and table counts
- ✅ Frontend polling stops when status is "completed"
- ✅ File list refreshes with updated counts
- ✅ Console logs show progress throughout the flow

## Data Flow

```
1. User uploads PDF
   ↓
2. POST /files/{file_id}/parse
   ↓
3. Background task: parse_with_azure()
   ├── Calls Azure Document Intelligence API
   ├── Extracts page_count = len(result.pages)
   ├── Extracts tables from result.tables
   ├── Stores metadata in FileVersion.llm_params
   └── Updates File.status = "completed"
   ↓
4. Frontend polls: GET /files/{file_id}/parse-status
   ├── Returns: { status, page_count, tables_found }
   └── Frontend updates UI
   ↓
5. When status === "completed":
   ├── Frontend stops polling
   ├── Refreshes file list with actual counts
   └── User sees page count and table count
```

## Notes

### Why use llm_params for storage?
- The `FileVersion` model doesn't have dedicated `page_count` or `table_count` fields
- Adding new database columns would require Alembic migrations
- Using the existing `llm_params` JSON field is a quick, non-breaking solution
- `llm_params` is designed to store flexible metadata

### Future Improvements
1. **Add dedicated columns**: Create a migration to add `page_count` and `table_count` columns to FileVersion
2. **Optimize file list loading**: Consider caching parse status to reduce API calls
3. **WebSocket support**: Replace polling with real-time updates via WebSocket
4. **Progress tracking**: Show granular progress (e.g., "Processing page 5 of 15")

## Files Modified

### Backend
- `backend/app/api/v1/routes_parse_azure.py` - Main parsing logic and status endpoint

### Frontend
- `frontend_updated/lib/api/index.ts` - API client type definitions
- `frontend_updated/components/console/FilesGuidelines.tsx` - File list display and polling logic

### Testing
- `test_parse_status_fix.sh` - New test script for verification

## Commit Message
```
fix: Update parse status to return page_count and refresh UI

- Backend: Extract page_count from Azure Document Intelligence result
- Backend: Store page_count and table_count in FileVersion.llm_params
- Backend: Return page_count in ParseStatusResponse
- Frontend: Add page_count to TypeScript API types
- Frontend: Fetch and display actual page/table counts in file list
- Frontend: Enhanced logging for parse status polling
- Testing: Add test_parse_status_fix.sh script

Fixes issue where frontend showed "解析中" indefinitely and never
displayed page/table counts after parsing completed.
```
