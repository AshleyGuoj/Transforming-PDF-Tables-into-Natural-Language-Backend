# 旧文件状态报告

**日期:** 2025年10月8日  
**状态:** 部分文件需要更新以适配 GrandscaleDB 模型

---

## 📋 问题总结

在将后端从旧的 UUID 模型迁移到 GrandscaleDB 的 Integer ID 模型后，以下文件包含对**不存在的类型和模型**的引用，需要更新或暂时禁用。

---

## 🔴 需要更新的文件

### 1. API 路由文件（旧代码）

这些文件是原始项目的一部分，引用了不存在于 GrandscaleDB 中的模型和枚举：

#### **`app/api/v1/routes_tasks.py`**
- **问题:** 引用了 `Task`, `TaskStatus`, `DraftStatus`, `AIDraft` 等
- **GrandscaleDB 等价物:** 应该使用 `AnnotationJob`, `AnnotationJobStatus`
- **缺失的类型:**
  - `TaskStatus` (枚举) - 不存在
  - `DraftStatus` (枚举) - 不存在
  - `AIDraft` (模型) - 不存在
  - `Task` (模型) - 应改为 `AnnotationJob`

#### **`app/api/v1/routes_drafts.py`**
- **问题:** 引用了 `Task`, `TaskStatus`, `DraftStatus`, `AIDraft`
- **状态:** 需要重构以使用 `AnnotationJob` 或禁用

#### **`app/api/v1/routes_export.py`**
- **问题:** 引用了 `ExportType`, `Task`, `AIDraft`, `HumanEdit`, `QACheck`
- **GrandscaleDB 等价物:**
  - `ExportLog` 存在，但没有 `ExportType` 枚举
  - `AIDraft`, `HumanEdit`, `QACheck` 不存在

#### **`app/api/v1/routes_parse.py`**
- **状态:** ✅ 已部分修复
- **修复:** 
  - `File` 改为 `FileModel`（避免与 FastAPI 的 `File` 冲突）
  - 使用别名 `PDFFile` → `File`, `ParsedTable` → `FileTable`
- **剩余问题:** 可能需要进一步测试

### 2. Worker 文件

#### **`app/workers/tasks_draft.py`**
- **问题:** 引用 `Task`, `TaskStatus`, `DraftStatus`, `AIDraft`
- **状态:** 需要重构

#### **`app/workers/tasks_parse.py`**
- **问题:** 引用 `Task`, `TaskStatus`, `DraftStatus`
- **状态:** 需要重构

---

## ✅ 已完成的修复

### 1. 模型导入统一
- **文件:** `app/db/models/__init__.py`
- **修复:** 添加了向后兼容的别名
  ```python
  PDFFile = File  # 旧名称 → 新名称
  ParsedTable = FileTable  # 旧名称 → 新名称
  ```

### 2. 导入路径更新
- 所有 `from app.db.models.files import ...` → `from app.db.models import ...`
- 所有 `from app.db.models.projects import ...` → `from app.db.models import ...`

### 3. 命名冲突解决
- `routes_parse.py`: FastAPI 的 `File` → `FastAPIFile`
- `routes_parse.py`: 模型的 `File` → `FileModel`

---

## 🎯 推荐方案

### 方案 A: 暂时禁用旧路由（推荐）✅

**优点:**
- 快速启动后端
- 专注于新的 Project CRUD API
- 避免复杂的重构

**操作:**
1. 在 `app/main.py` 中注释掉旧路由的导入
2. 只保留 `routes_projects`（新的，完全兼容）

```python
# 暂时注释掉旧路由
# from app.api.v1 import routes_parse, routes_tasks, routes_drafts, routes_export
from app.api.v1 import routes_projects  # 只加载新路由

# app.include_router(routes_parse.router, ...)  # 禁用
# app.include_router(routes_tasks.router, ...)  # 禁用
# app.include_router(routes_drafts.router, ...)  # 禁用
# app.include_router(routes_export.router, ...)  # 禁用
app.include_router(routes_projects.router, ...)  # 保留
```

### 方案 B: 完全重构旧路由

**工作量:**
- 创建缺失的枚举类型 (`TaskStatus`, `DraftStatus`, `ExportType`)
- 或将这些枚举映射到 GrandscaleDB 的现有枚举
- 重写所有查询以使用 `AnnotationJob` 而不是 `Task`
- 估计时间: 4-6 小时

**不推荐原因:** 
- 这些路由可能不是当前项目的核心功能
- GrandscaleDB 的设计可能与原始设计不同

---

## 📊 当前文件清单

### ✅ 可用文件（已验证）

```
✅ app/db/base.py              - GrandscaleDB 集成
✅ app/db/session.py           - 数据库会话管理
✅ app/db/models/__init__.py   - 模型导出（含别名）
✅ app/crud/project.py         - Project CRUD
✅ app/crud/organization.py    - Organization CRUD
✅ app/crud/user.py            - User CRUD
✅ app/crud/file.py            - File CRUD
✅ app/crud/annotation.py      - Annotation CRUD
✅ app/schemas/project.py      - Project schemas
✅ app/schemas/organization.py - Organization schemas
✅ app/schemas/user.py         - User schemas
✅ app/schemas/file.py         - File schemas
✅ app/schemas/annotation.py   - Annotation schemas
✅ app/api/v1/routes_projects.py - Project API (新)
```

### ⚠️ 有问题的文件（旧代码）

```
⚠️ app/api/v1/routes_parse.py   - 引用旧模型名称
⚠️ app/api/v1/routes_tasks.py   - 引用不存在的 Task/TaskStatus
⚠️ app/api/v1/routes_drafts.py  - 引用不存在的 DraftStatus
⚠️ app/api/v1/routes_export.py  - 引用不存在的 ExportType
⚠️ app/workers/tasks_draft.py   - 引用不存在的类型
⚠️ app/workers/tasks_parse.py   - 引用不存在的类型
```

---

## 🚀 立即行动建议

### 步骤 1: 暂时禁用有问题的路由

修改 `app/main.py`:

```python
# 只导入可用的路由
from app.api.v1 import routes_projects

# 原始导入（暂时注释）
# from app.api.v1 import routes_parse, routes_tasks, routes_drafts, routes_export

# 只注册可用的路由
app.include_router(
    routes_projects.router,
    prefix="/api/v1",
    tags=["Projects"]
)
```

### 步骤 2: 测试后端启动

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 步骤 3: 验证可用的 API

访问: http://localhost:8000/docs

应该看到:
- ✅ GET /api/v1/projects
- ✅ POST /api/v1/projects
- ✅ GET /api/v1/projects/{project_id}
- ✅ PUT /api/v1/projects/{project_id}
- ✅ DELETE /api/v1/projects/{project_id}
- ✅ /health
- ✅ /

---

## 📝 未来工作

如果需要恢复旧路由功能：

1. **分析需求:** 确定哪些路由是必需的
2. **设计映射:** 将旧的概念映射到 GrandscaleDB 的模型
3. **创建枚举:** 如果需要，在 GrandscaleDB 中添加缺失的枚举
4. **重写逻辑:** 使用 `AnnotationJob` 而不是 `Task`
5. **测试验证:** 确保所有功能正常

---

## 📚 相关文档

- **完整设置指南:** `docs/backend_setup.md`
- **设置完成报告:** `SETUP_COMPLETE.md`
- **GrandscaleDB 模型:** `backend/GrandscaleDB/models/`
- **连接测试:** `backend/tests/connection_test.py`

---

*最后更新: 2025年10月8日*  
*状态: 建议暂时禁用旧路由，专注于新的 Project API*

