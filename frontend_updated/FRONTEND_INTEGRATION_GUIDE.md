# 🔗 Frontend ↔ Backend Integration Guide

**Project:** GrandScale PM Console  
**Frontend:** Next.js 14+ (TypeScript)  
**Backend:** FastAPI (Python)  
**Date:** 2025-10-09

---

## 📋 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp env.local.example .env.local

# Edit .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

### 3. Start Development

```bash
# Terminal 1: Start Backend
cd ../backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd ../frontend_updated
npm run dev
```

### 4. Verify Connection

Open browser console and test:

```javascript
import API from '@/lib/api';

// Test health check
await API.health.check();
// Expected: { status: "healthy", database: "connected" }
```

---

## 🗺️ API Integration Guide

### Import API Client

```typescript
import API from '@/lib/api';
// or import specific modules
import { ProjectsAPI, FilesAPI, ParseAPI, TasksAPI, ExportAPI } from '@/lib/api';
```

---

## 📄 Page-to-API Mapping

### 1. Projects Page (`app/console/project/page.tsx`)

**Purpose:** List, create, view, update projects

**API Calls:**

```typescript
import API from '@/lib/api';
import { useState, useEffect } from 'react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch projects on mount
  useEffect(() => {
    async function fetchProjects() {
      try {
        const data = await API.projects.getAll({ page: 1, page_size: 20 });
        setProjects(data.projects);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchProjects();
  }, []);

  // Create new project
  const handleCreateProject = async (formData) => {
    try {
      const newProject = await API.projects.create({
        org_id: 1,
        name: formData.name,
        description: formData.description,
        client_pm_id: formData.pmId,
      });
      
      setProjects([...projects, newProject]);
      alert('Project created successfully!');
    } catch (error) {
      console.error('Failed to create project:', error);
      alert(`Error: ${error.message}`);
    }
  };

  // Update project
  const handleUpdateProject = async (projectId, updates) => {
    try {
      const updated = await API.projects.update(projectId, updates);
      setProjects(projects.map(p => p.project_id === projectId ? updated : p));
    } catch (error) {
      console.error('Failed to update project:', error);
    }
  };

  // Delete project
  const handleDeleteProject = async (projectId) => {
    if (!confirm('Are you sure?')) return;
    
    try {
      await API.projects.delete(projectId);
      setProjects(projects.filter(p => p.project_id !== projectId));
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Projects</h1>
      <button onClick={() => {/* Show create form */}}>
        Create Project
      </button>
      <ul>
        {projects.map(project => (
          <li key={project.project_id}>
            {project.name}
            <button onClick={() => handleUpdateProject(project.project_id, { status: 'active' })}>
              Activate
            </button>
            <button onClick={() => handleDeleteProject(project.project_id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

### 2. File Upload Component (`components/FileUpload.tsx`)

**Purpose:** Upload PDFs to projects

**API Calls:**

```typescript
import API from '@/lib/api';
import { useState } from 'react';

interface FileUploadProps {
  projectId: number;
  onUploadComplete?: (file: any) => void;
}

export default function FileUpload({ projectId, onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.pdf')) {
      alert('Only PDF files are allowed');
      return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      alert('File size must be less than 50MB');
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      const result = await API.files.upload(projectId, file);
      
      alert(`File uploaded successfully!\nFile ID: ${result.file_id}\nVersion: ${result.version}`);
      
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
      setProgress(0);
      event.target.value = ''; // Reset input
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
        disabled={uploading}
      />
      {uploading && (
        <div>
          <progress value={progress} max={100} />
          <span>Uploading... {progress}%</span>
        </div>
      )}
    </div>
  );
}
```

---

### 3. Parse Results Page (`app/export/page.tsx` or custom parse page)

**Purpose:** Trigger PDF parsing and display tables

**API Calls:**

```typescript
'use client';

import API from '@/lib/api';
import { useState, useEffect } from 'react';

export default function ParsePage({ fileId }: { fileId: number }) {
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle');
  const [tables, setTables] = useState([]);
  const [error, setError] = useState<string | null>(null);

  // Start parsing
  const startParsing = async () => {
    try {
      const result = await API.parse.trigger(fileId);
      setStatus('processing');
      
      // Poll for status every 2 seconds
      const intervalId = setInterval(async () => {
        try {
          const statusData = await API.parse.getStatus(fileId);
          setStatus(statusData.status as any);
          
          if (statusData.status === 'completed') {
            clearInterval(intervalId);
            // Fetch tables
            const tablesData = await API.parse.getTables(fileId);
            setTables(tablesData.tables);
          } else if (statusData.status === 'failed') {
            clearInterval(intervalId);
            setError(statusData.processing_error || 'Parsing failed');
          }
        } catch (err) {
          console.error('Status check failed:', err);
        }
      }, 2000);
    } catch (err) {
      console.error('Failed to start parsing:', err);
      setError(err.message);
    }
  };

  // Fetch tables if already parsed
  useEffect(() => {
    async function fetchTables() {
      try {
        const statusData = await API.parse.getStatus(fileId);
        setStatus(statusData.status as any);
        
        if (statusData.status === 'completed') {
          const tablesData = await API.parse.getTables(fileId);
          setTables(tablesData.tables);
        }
      } catch (err) {
        console.error('Failed to fetch tables:', err);
      }
    }
    fetchTables();
  }, [fileId]);

  return (
    <div>
      <h1>Parse Results - File {fileId}</h1>
      
      <div>
        <button 
          onClick={startParsing} 
          disabled={status === 'processing'}
        >
          {status === 'processing' ? 'Parsing...' : 'Start Parsing'}
        </button>
        <span>Status: {status}</span>
      </div>

      {error && <div className="error">{error}</div>}

      {tables.length > 0 && (
        <div>
          <h2>Found {tables.length} Tables</h2>
          {tables.map((table, idx) => (
            <div key={table.table_id} style={{ marginBottom: '2rem' }}>
              <h3>Table {idx + 1} (Page {table.page_number})</h3>
              {table.confidence && <p>Confidence: {(table.confidence * 100).toFixed(1)}%</p>}
              
              <table border={1} cellPadding={8}>
                <thead>
                  {table.headers.map((headerRow, i) => (
                    <tr key={i}>
                      {headerRow.map((cell, j) => (
                        <th key={j}>{cell}</th>
                      ))}
                    </tr>
                  ))}
                </thead>
                <tbody>
                  {table.rows.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td key={j}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

### 4. Tasks Page (Add to `app/console/project/[id]/page.tsx` or create new)

**Purpose:** Create tasks and generate AI drafts

**API Calls:**

```typescript
import API from '@/lib/api';
import { useState, useEffect } from 'react';

export default function TasksPage({ projectId }: { projectId: number }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch tasks
  useEffect(() => {
    async function fetchTasks() {
      try {
        const data = await API.tasks.getAll({ 
          project_id: projectId,
          page: 1,
          page_size: 50 
        });
        setTasks(data.tasks);
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchTasks();
  }, [projectId]);

  // Bulk create tasks for a file
  const createTasksForFile = async (fileId: number) => {
    try {
      const result = await API.tasks.bulkCreate(fileId);
      alert(`Created ${result.total} tasks`);
      
      // Refresh task list
      const data = await API.tasks.getAll({ project_id: projectId });
      setTasks(data.tasks);
    } catch (error) {
      console.error('Failed to create tasks:', error);
      alert(`Error: ${error.message}`);
    }
  };

  // Generate AI draft
  const generateDraft = async (jobId: number) => {
    try {
      const result = await API.tasks.generateDraft(jobId, 'gpt-4');
      alert(`Draft generation started for task ${jobId}`);
      
      // Optionally refresh task to show new status
      const updatedTask = await API.tasks.getById(jobId);
      setTasks(tasks.map(t => t.job_id === jobId ? updatedTask : t));
    } catch (error) {
      console.error('Failed to generate draft:', error);
      alert(`Error: ${error.message}`);
    }
  };

  if (loading) return <div>Loading tasks...</div>;

  return (
    <div>
      <h1>Tasks</h1>
      
      <table>
        <thead>
          <tr>
            <th>Job ID</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map(task => (
            <tr key={task.job_id}>
              <td>{task.job_id}</td>
              <td>{task.status}</td>
              <td>{new Date(task.created_at).toLocaleString()}</td>
              <td>
                <button onClick={() => generateDraft(task.job_id)}>
                  Generate Draft
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

### 5. Export Panel (`components/ExportPanel.tsx`)

**Purpose:** Export project data

**API Calls:**

```typescript
import API from '@/lib/api';
import { useState } from 'react';

interface ExportPanelProps {
  projectId: number;
}

export default function ExportPanel({ projectId }: ExportPanelProps) {
  const [exporting, setExporting] = useState(false);
  const [format, setFormat] = useState<'json' | 'csv' | 'excel'>('json');

  const handleExport = async () => {
    setExporting(true);
    
    try {
      // Create export job
      const result = await API.export.create(projectId, {
        format,
        include_files: true,
        include_tables: true,
        include_annotations: true,
      });
      
      alert(`Export job created: ${result.export_id}`);
      
      // Poll for completion
      const checkInterval = setInterval(async () => {
        try {
          const status = await API.export.getStatus(result.export_id);
          
          if (status.status === 'completed') {
            clearInterval(checkInterval);
            alert('Export ready! Downloading...');
            API.export.download(result.export_id);
            setExporting(false);
          } else if (status.status === 'failed') {
            clearInterval(checkInterval);
            alert('Export failed');
            setExporting(false);
          }
        } catch (err) {
          console.error('Status check failed:', err);
        }
      }, 3000);
      
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Export failed: ${error.message}`);
      setExporting(false);
    }
  };

  return (
    <div>
      <h2>Export Project</h2>
      
      <div>
        <label>
          Format:
          <select 
            value={format} 
            onChange={(e) => setFormat(e.target.value as any)}
            disabled={exporting}
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="excel">Excel</option>
          </select>
        </label>
      </div>

      <button 
        onClick={handleExport} 
        disabled={exporting}
      >
        {exporting ? 'Exporting...' : 'Export'}
      </button>
    </div>
  );
}
```

---

## ✅ Integration Checklist

### Setup
- [ ] `lib/api/index.ts` file created
- [ ] `.env.local` configured with `NEXT_PUBLIC_API_BASE_URL`
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000

### API Testing
- [ ] `API.health.check()` returns success
- [ ] `API.projects.getAll()` returns projects
- [ ] File upload works without CORS errors
- [ ] Parse triggers and status polling works
- [ ] Tasks creation successful
- [ ] Export creates and downloads file

### Browser Console
- [ ] No CORS errors
- [ ] No 404 errors
- [ ] All requests return 200/201/204
- [ ] Response data matches expected structure

---

## 🔧 Troubleshooting

### CORS Errors

**Problem:** "Access-Control-Allow-Origin" error

**Solution:**
1. Check backend `.env` has `ALLOWED_HOSTS=["http://localhost:3000","http://localhost:8000"]`
2. Restart backend: `uvicorn app.main:app --reload`
3. Clear browser cache (Cmd/Ctrl + Shift + R)

### API Not Found (404)

**Problem:** Endpoint returns 404

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check Swagger docs: http://localhost:8000/docs
3. Verify API_BASE_URL in `.env.local`

### TypeScript Errors

**Problem:** Type errors in IDE

**Solution:**
1. Ensure types in `lib/api/index.ts` match backend responses
2. Run `npm run build` to check for type errors
3. Add `// @ts-ignore` temporarily if needed

---

## 📚 Related Documentation

- **Backend Setup:** `../docs/backend_setup.md`
- **Backend Refactor:** `../docs/pm_console_backend_refactor.md`
- **Deployment Guide:** `../docs/DEPLOY_GUIDE.md`
- **Backend API Docs:** http://localhost:8000/docs (when running)

---

## 🚀 Next Steps

1. Test all API endpoints in browser console
2. Integrate API calls into existing pages
3. Add error handling and loading states
4. Add Toast notifications for user feedback
5. Implement authentication if needed
6. Add request caching/SWR for better performance

---

*Last Updated: 2025-10-09*  
*Version: 1.0.0*  
*Status: Ready for Integration*

