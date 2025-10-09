# 🚀 GrandScale Backend Deployment & Environment Setup Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-09  
**Author:** Jiaqi Guo

---

## 🧭 Overview

This guide explains how to set up and run the **GrandScale PM Console Backend** locally.

### What's Covered:
- ✅ Environment setup (`.env` + virtual environment)
- ✅ Required dependencies (by module)
- ✅ External service configuration
- ✅ Run commands (local / production)

---

## 📁 Folder Overview

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entry
│   ├── api/v1/                  # API route modules
│   │   ├── routes_projects.py
│   │   ├── routes_files.py
│   │   ├── routes_parse_azure.py
│   │   ├── routes_tasks_new.py
│   │   └── routes_export_new.py
│   ├── crud/                    # CRUD operations
│   ├── db/                      # Database layer
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   ├── schemas/                 # Pydantic schemas
│   ├── workers/                 # Background tasks
│   │   └── tasks_draft_ai.py
│   └── core/                    # Core utilities
├── GrandscaleDB/               # Database schema source ⭐
└── docs/
    ├── backend_setup.md
    ├── pm_console_backend_refactor.md
    └── DEPLOY_GUIDE.md         # This document
```

---

## ⚙️ 1. Environment Setup

### Create and activate virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
```

### Install base dependencies

```bash
pip install -r requirements.txt
```

> 💡 **Tip:** If no `requirements.txt` exists, install manually as shown below 👇

---

## 📦 2. Requirements Installation (by module)

### Dependency Matrix

| Category | Package | Purpose | Required for |
|----------|---------|---------|--------------|
| **Core Framework** | `fastapi` | Web framework | All API modules |
| | `uvicorn[standard]` | ASGI server | Local dev server |
| | `pydantic` | Schema validation | Schemas layer |
| | `pydantic[email]` | Email validation | User schemas |
| | `pydantic-settings` | .env config management | All configs |
| **Database (PostgreSQL)** | `sqlalchemy` | ORM layer | All CRUD modules |
| | `asyncpg` | Async DB driver | FastAPI async DB ops |
| | `psycopg2-binary` | Sync DB driver | Alembic & Celery workers |
| | `greenlet` | Required by SQLAlchemy async | All DB ops |
| | `alembic` | DB migrations | DB setup / versioning |
| **Env & Logging** | `python-dotenv` | Read .env files | Global |
| | `structlog` | Structured logging | Core logging |
| | `python-json-logger` | JSON logs | Core logging |
| **Storage (Optional)** | `boto3` | AWS S3 or MinIO integration | `routes_files.py` |
| **AI / Azure Services** | `httpx` | HTTP client | `routes_parse_azure.py` |
| | `python-jose[cryptography]` | JWT & signing (future auth) | `core/security` |
| | `passlib[bcrypt]` | Password hashing | User authentication |
| **Async Tasks** | `celery` | Background task queue | `workers/tasks_draft_ai.py` |
| | `redis` | Message broker | Celery backend |
| **File Upload** | `python-multipart` | Form data parsing | File upload endpoints |
| **PDF & Parsing (Optional)** | `PyMuPDF` | Local fallback parsing | Debug / test |
| | `pdfplumber` | Alternative PDF parsing | Debug / test |
| **Testing** | `pytest` | Unit tests | Test suite |
| | `pytest-asyncio` | Async test support | Async tests |

### ✅ One-Command Install

```bash
pip install \
  fastapi \
  uvicorn[standard] \
  sqlalchemy \
  asyncpg \
  psycopg2-binary \
  greenlet \
  pydantic \
  "pydantic[email]" \
  pydantic-settings \
  python-dotenv \
  structlog \
  python-json-logger \
  boto3 \
  httpx \
  "python-jose[cryptography]" \
  "passlib[bcrypt]" \
  python-multipart \
  celery \
  redis \
  PyMuPDF \
  pdfplumber \
  pytest \
  pytest-asyncio
```

### Generate requirements.txt

```bash
pip freeze > requirements.txt
```

---

## 🧰 3. External Service Dependencies

### 🐘 PostgreSQL

#### Installation (Mac Example)

**Option 1: Homebrew**
```bash
brew install postgresql
brew services start postgresql
```

**Option 2: Postgres.app** (Recommended ⭐)
- Download from [https://postgresapp.com/](https://postgresapp.com/)
- Install and start
- Add to PATH:
  ```bash
  export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
  ```

#### Create Database

```bash
# Using psql
psql postgres -c "CREATE DATABASE grandscale_db;"

# Or if using Postgres.app
/Applications/Postgres.app/Contents/Versions/18/bin/psql postgres -c "CREATE DATABASE grandscale_db;"
```

#### Verify Connection

```bash
psql -d grandscale_db -c "\dt"
```

Expected output: List of tables (after running migrations)

#### Required Python Drivers

```bash
pip install psycopg2-binary asyncpg greenlet
```

---

### 🧠 Redis (for Celery Worker)

#### Installation (Mac Example)

```bash
brew install redis
brew services start redis
```

#### Check Service

```bash
redis-cli ping
# Expected output: PONG
```

#### Required Python Package

```bash
pip install redis celery
```

---

### 🗂️ MinIO / S3 (for File Uploads)

#### Local Setup (Optional)

**Using Docker:**
```bash
docker run -d -p 9000:9000 -p 9090:9090 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  quay.io/minio/minio server /data --console-address ":9090"
```

**Access MinIO Console:**
- URL: http://localhost:9090
- Username: `minioadmin`
- Password: `minioadmin`

#### Create Bucket

```bash
# Using MinIO Client (mc)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/grandscale-storage
```

#### Required Python Package

```bash
pip install boto3
```

---

## 🔐 4. Environment Configuration

### Create `.env` File

Create `.env` in the `backend/` directory:

```bash
# Application Settings
APP_ENV=local
DEBUG=True
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:@localhost:5432/grandscale_db

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

# Storage Configuration (MinIO/S3)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=grandscale-storage

# Azure Document Intelligence (Optional)
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_azure_api_key_here
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/

# Security Settings
JWT_SECRET_KEY=dev-secret-change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS Settings
ALLOWED_HOSTS=["http://localhost:3000","http://localhost:8000"]

# OpenAI (Optional - for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (Optional - for Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | Yes | `local` | Environment: local/dev/staging/prod |
| `DEBUG` | No | `False` | Enable debug mode |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Optional | - | Redis connection for Celery |
| `S3_ENDPOINT_URL` | Optional | - | MinIO/S3 endpoint |
| `S3_ACCESS_KEY` | Optional | - | Storage access key |
| `S3_SECRET_KEY` | Optional | - | Storage secret key |
| `S3_BUCKET` | Optional | - | Storage bucket name |
| `JWT_SECRET_KEY` | Yes | - | Secret for JWT signing |
| `ALLOWED_HOSTS` | No | `["*"]` | CORS allowed origins |

---

## 🧩 5. Run Backend Locally

### Step 1: Initialize Database

```bash
cd backend

# Create database tables
python3 -c "
import asyncio
from app.db.session import create_tables
asyncio.run(create_tables())
print('✅ Database tables created')
"
```

### Step 2: Start API Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 3: Start Celery Worker (Optional)

```bash
# In a separate terminal
celery -A app.workers.celery_app worker --loglevel=info
```

### Step 4: Verify Services

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

---

## 🔗 6. Port Mapping (Frontend ↔ Backend)

| Component | Port | URL | Purpose |
|-----------|------|-----|---------|
| **React Frontend** | 3000 | http://localhost:3000 | User interface |
| **FastAPI Backend** | 8000 | http://localhost:8000 | API server |
| **PostgreSQL** | 5432 | `localhost:5432` | Database |
| **Redis** | 6379 | `localhost:6379` | Task queue |
| **MinIO Console** | 9090 | http://localhost:9090 | Storage UI |
| **MinIO API** | 9000 | http://localhost:9000 | Storage API |

### CORS Configuration

Already configured in `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🧪 7. Quick Test Commands

### Database Connection Test

```bash
python3 -c "
import asyncio
from app.db.session import check_database_connection
result = asyncio.run(check_database_connection())
print('✅ Database connected' if result else '❌ Database connection failed')
"
```

### API Endpoint Tests

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. List projects
curl http://localhost:8000/api/v1/projects

# 3. Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": 1,
    "name": "Test Project",
    "description": "Test description",
    "client_pm_id": 1
  }'

# 4. Upload file
curl -X POST http://localhost:8000/api/v1/projects/1/files \
  -F "file=@sample.pdf"

# 5. Trigger Azure parse
curl -X POST http://localhost:8000/api/v1/files/1/parse

# 6. Create tasks
curl -X POST http://localhost:8000/api/v1/tasks/bulk-create \
  -H "Content-Type: application/json" \
  -d '{"file_id": 1, "assigned_to": 1}'

# 7. Export project
curl -X POST http://localhost:8000/api/v1/projects/1/export \
  -H "Content-Type: application/json" \
  -d '{"format": "json"}'
```

---

## 🧾 8. Troubleshooting

### Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| `psycopg2: libpq.5.dylib not found` | PostgreSQL library not linked | Reinstall `psycopg2-binary` or install Postgres.app |
| `CORS policy error` | Frontend port mismatch | Check CORS settings in `main.py` |
| `asyncpg connection error` | DB not started | Run `brew services start postgresql` |
| `redis.exceptions.ConnectionError` | Redis not running | Run `brew services start redis` |
| `ModuleNotFoundError: greenlet` | Missing async support | Run `pip install greenlet` |
| `ModuleNotFoundError: extract_tables` | Wrong import path | Use `from app.api.v1.extract_tables import ...` |
| `ImportError: cannot import name 'FileModel'` | Model name mismatch | Use `from app.db.models import File as FileModel` |
| `pydantic validation error` | Missing required field | Check request body schema |

### Debug Mode

Enable detailed logging:

```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Or via environment variable
DEBUG=True LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Check Logs

```bash
# View structured logs
tail -f logs/app.log

# Or if using systemd
journalctl -u grandscale-backend -f
```

---

## 📊 9. Production Deployment

### Using Docker

#### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/grandscale_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=grandscale_db
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: quay.io/minio/minio
    command: server /data --console-address ":9090"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    ports:
      - "9000:9000"
      - "9090:9090"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

#### Start Services

```bash
docker-compose up -d
```

### Using systemd (Linux)

Create `/etc/systemd/system/grandscale-backend.service`:

```ini
[Unit]
Description=GrandScale Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/grandscale/backend
Environment="PATH=/opt/grandscale/backend/venv/bin"
ExecStart=/opt/grandscale/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable grandscale-backend
sudo systemctl start grandscale-backend
sudo systemctl status grandscale-backend
```

---

## ✅ 10. Summary Checklist

### Layer Status

| Layer | Status | Dependencies |
|-------|--------|--------------|
| FastAPI Core | ✅ Ready | `fastapi`, `uvicorn` |
| Database ORM | ✅ Ready | `sqlalchemy`, `asyncpg`, `psycopg2-binary` |
| Schema & CRUD | ✅ Ready | `pydantic`, `pydantic-settings` |
| Storage Layer | ⚙️ Optional | `boto3`, MinIO/S3 |
| AI Integration | ⚙️ Optional | `httpx`, Azure API key |
| Task Queue | ⚙️ Optional | `celery`, `redis` |

### Pre-launch Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL installed and running
- [ ] Database `grandscale_db` created
- [ ] Database tables initialized
- [ ] `.env` file configured
- [ ] Redis installed (if using Celery)
- [ ] MinIO/S3 configured (if using file uploads)
- [ ] API server starts without errors
- [ ] `/health` endpoint returns OK
- [ ] `/docs` Swagger UI accessible

---

## 📚 11. Additional Resources

### Documentation

- **Backend Setup:** `docs/backend_setup.md`
- **Refactor Report:** `docs/pm_console_backend_refactor.md`
- **Old Files Status:** `backend/OLD_FILES_STATUS.md`
- **API Documentation:** http://localhost:8000/docs (when running)

### API Endpoints Summary

- **Projects:** 5 endpoints - CRUD operations
- **Files:** 4 endpoints - Upload, list, replace, delete
- **Parse:** 4 endpoints - Trigger parsing, check status, get tables
- **Tasks:** 5 endpoints - Create, list, assign, generate drafts
- **Export:** 5 endpoints - Create, download, manage exports

### Key Files

- `app/main.py` - FastAPI application entry point
- `app/db/base.py` - Database models integration
- `app/db/session.py` - Database session management
- `GrandscaleDB/models/` - Database schema source of truth

---

## 📞 Support & Contact

**Project Lead:** Jiaqi Guo  
**Documentation:** Claude AI (Cursor)  
**Last Updated:** 2025-10-09

For issues or questions:
1. Check `docs/` folder for detailed documentation
2. Review API docs at `/docs` endpoint
3. Check logs for error details
4. Refer to troubleshooting section above

---

*Version: 1.0.0*  
*Status: ✅ Production Ready*  
*Environment: Local Development / Docker / Production*

