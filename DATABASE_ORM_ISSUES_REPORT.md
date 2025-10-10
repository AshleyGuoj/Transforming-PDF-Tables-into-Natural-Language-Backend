# 🐛 GrandScale Database ORM 问题报告

**日期:** 2025年10月9日
**报告人:** Backend Integration Team
**严重程度:** 🔴 **HIGH** - 阻塞API开发
**状态:** ⚠️ 需要立即修复

---

## 📋 问题总结

GrandscaleDB 的 SQLAlchemy ORM 模型存在**多个关系定义错误**，导致：
1. ❌ 无法使用 ORM 查询（所有 `select(Project)` 都失败）
2. ❌ FastAPI 路由无法正常工作
3. ❌ 必须使用原生 SQL 绕过 ORM（临时解决方案）

---

## 🔴 问题 1: File ↔ FileVersion 双向外键冲突

### 错误信息
```
sqlalchemy.exc.AmbiguousForeignKeysError: Could not determine join condition
between parent/child tables on relationship File.versions - there are multiple
foreign key paths linking the tables.
```

### 问题位置
**文件:** `backend/GrandscaleDB/models/project.py`

### 问题代码

#### File 模型 (Line 71-102)
```python
class File(Base, TimestampMixin):
    __tablename__ = "file"

    file_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("project.project_id"))
    active_version_id = Column(Integer, ForeignKey("file_version.version_id"))  # ← FK 1

    # 问题：两个关系都指向 FileVersion，但没有明确 foreign_keys
    versions = relationship("FileVersion", back_populates="file")  # ❌ 模糊
    active_version = relationship("FileVersion", foreign_keys=[active_version_id])  # ✅ 明确
```

#### FileVersion 模型 (Line 108-140)
```python
class FileVersion(Base, TimestampMixin):
    __tablename__ = "file_version"

    version_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file.file_id"))  # ← FK 2

    # 问题：没有指定应该用哪个外键
    file = relationship("File", back_populates="versions")  # ❌ 模糊
```

### 为什么会失败？

SQLAlchemy 看到：
- `File.active_version_id` → `FileVersion.version_id` (FK路径1)
- `FileVersion.file_id` → `File.file_id` (FK路径2)

当定义 `File.versions` 关系时，SQLAlchemy 不知道应该用哪个外键。

### ✅ 正确的写法

```python
# File 模型
class File(Base, TimestampMixin):
    # ... columns ...

    # 明确指定使用 FileVersion.file_id 作为外键
    versions = relationship(
        "FileVersion",
        foreign_keys="FileVersion.file_id",  # ✅ 明确指定
        back_populates="file",
        cascade="all, delete-orphan"
    )

    # 明确指定使用 File.active_version_id 作为外键
    active_version = relationship(
        "FileVersion",
        foreign_keys=[active_version_id],  # ✅ 明确指定
        uselist=False
    )

# FileVersion 模型
class FileVersion(Base, TimestampMixin):
    # ... columns ...

    # 明确指定使用 file_id 列
    file = relationship(
        "File",
        foreign_keys=[file_id],  # ✅ 明确指定
        back_populates="versions"
    )
```

---

## 🔴 问题 2: ExportLog ↔ FileVersion ↔ ExportedFile 重叠关系

### 错误信息
```
SAWarning: relationship 'FileVersion.exported_files' will copy column
file_version.version_id to column exported_file.file_version_id, which
conflicts with relationship(s): 'FileVersion.exports'
```

### 问题位置
**文件:** `backend/GrandscaleDB/models/project.py` (Line 133-139)

### 问题代码

```python
class FileVersion(Base, TimestampMixin):
    # ... columns ...

    # 问题：两个关系都操作同一个中间表 exported_file
    exports = relationship(
        "ExportLog",
        secondary="exported_file",  # ← 使用 exported_file 表
        back_populates="file_versions"
    )

    exported_files = relationship(
        "ExportedFile",  # ← 也是 exported_file 表
        back_populates="file_version",
        cascade="all, delete-orphan"
    )
```

### 为什么会失败？

- `exports` 是多对多关系，通过 `exported_file` 中间表
- `exported_files` 是直接关系到同一个表
- 两者会相互冲突，SQLAlchemy 不知道应该如何处理级联删除和更新

### ✅ 正确的写法（方案A - 推荐）

只保留一个关系，删除重复的：

```python
class FileVersion(Base, TimestampMixin):
    # ... columns ...

    # 只保留直接关系
    exported_files = relationship(
        "ExportedFile",
        back_populates="file_version",
        cascade="all, delete-orphan"
    )

    # 通过 exported_files 访问 exports
    # 不需要单独的 exports 关系
```

### ✅ 正确的写法（方案B - 如果两者都需要）

使用 `overlaps` 参数：

```python
class FileVersion(Base, TimestampMixin):
    # ... columns ...

    exports = relationship(
        "ExportLog",
        secondary="exported_file",
        back_populates="file_versions",
        overlaps="exported_files"  # ✅ 告诉 SQLAlchemy 允许重叠
    )

    exported_files = relationship(
        "ExportedFile",
        back_populates="file_version",
        cascade="all, delete-orphan",
        overlaps="exports"  # ✅ 告诉 SQLAlchemy 允许重叠
    )
```

---

## 🔴 问题 3: AnnotationJob 中的未定义关系

### 错误信息
```
sqlalchemy.exc.InvalidRequestError: When initializing mapper
Mapper[AnnotationJob(annotation_job)], expression 'job_previous_annotators'
failed to locate a name ("name 'job_previous_annotators' is not defined")
```

### 问题位置
**文件:** `backend/GrandscaleDB/models/annotation.py` (推测)

### 问题原因

在 `AnnotationJob` 模型中，有一个关系引用了不存在的表或模型：

```python
class AnnotationJob(Base):
    # ... columns ...

    # ❌ 错误：job_previous_annotators 表/模型不存在
    previous_annotators = relationship("job_previous_annotators", ...)
```

### ✅ 需要检查的内容

1. 确认 `job_previous_annotators` 是表名还是模型名
2. 如果是表名，应该用 `secondary="job_previous_annotators"`
3. 如果是模型名，确保该模型已经定义
4. 检查是否有拼写错误

---

## 📊 影响范围

### 当前无法使用的功能
- ❌ `GET /api/v1/projects` (使用 ORM)
- ❌ `POST /api/v1/projects` (使用 ORM)
- ❌ 任何涉及 Project 的关系查询（files, jobs, events）
- ❌ 任何涉及 File 的关系查询（versions, tables）
- ❌ 任何涉及 FileVersion 的关系查询（exports）

### 当前的临时解决方案
✅ 使用原生 SQL 查询（`routes_projects_simple.py`）

```python
# 当前解决方案
query = text("""
    SELECT project_id, org_id, name, description, status
    FROM project
    WHERE is_active = true
""")
result = await db.execute(query)
```

**缺点:**
- 无法使用 ORM 的便利功能（关系加载、级联操作等）
- 手动编写 SQL 容易出错
- 没有类型检查
- 维护成本高

---

## 🛠️ 修复建议

### 立即修复（Critical）

**文件:** `backend/GrandscaleDB/models/project.py`

#### 修复 1: File ↔ FileVersion 关系

```python
# Line 99 - File.versions 关系
versions = relationship(
    "FileVersion",
    foreign_keys="FileVersion.file_id",  # 添加这行
    back_populates="file",
    cascade="all, delete-orphan"
)

# Line 134 - FileVersion.file 关系
file = relationship(
    "File",
    foreign_keys=[file_id],  # 添加这行
    back_populates="versions"
)
```

#### 修复 2: FileVersion exports 关系冲突

**选项A（推荐）- 删除重复关系:**
```python
# Line 137-139 - 删除 exports 关系，只保留 exported_files
# exports = relationship(...)  # 删除这行

exported_files = relationship(
    "ExportedFile",
    back_populates="file_version",
    cascade="all, delete-orphan"
)
```

**选项B - 添加 overlaps:**
```python
exports = relationship(
    "ExportLog",
    secondary="exported_file",
    back_populates="file_versions",
    overlaps="exported_files"  # 添加这行
)

exported_files = relationship(
    "ExportedFile",
    back_populates="file_version",
    cascade="all, delete-orphan",
    overlaps="exports"  # 添加这行
)
```

#### 修复 3: 检查 AnnotationJob

**文件:** `backend/GrandscaleDB/models/annotation.py`

搜索 `job_previous_annotators` 并修复引用错误。

---

## ✅ 修复后的测试步骤

### 1. 测试 ORM 能否加载
```python
import asyncio
from app.db.session import get_async_session
from app.db.models import Project
from sqlalchemy import select

async def test():
    async with get_async_session() as session:
        result = await session.execute(select(Project))
        projects = result.scalars().all()
        print(f'✅ 成功加载 {len(projects)} 个项目')

asyncio.run(test())
```

**期望结果:** 没有任何 SQLAlchemy 错误

### 2. 测试关系加载
```python
async def test():
    async with get_async_session() as session:
        result = await session.execute(
            select(Project).where(Project.project_id == 1)
        )
        project = result.scalar_one()

        # 测试关系
        print(f'项目名称: {project.name}')
        print(f'文件数量: {len(project.files)}')  # 应该能加载关系

asyncio.run(test())
```

**期望结果:** 能够访问 `project.files` 而不报错

### 3. 测试 API 端点
```bash
# 应该能用 ORM routes 而不是 simple routes
curl http://localhost:8000/api/v1/projects
```

**期望结果:** 返回项目列表，没有数据库错误

---

## 📝 长期改进建议

### 1. 添加关系测试
**文件:** `backend/GrandscaleDB/test_relationships.py` (新建)

```python
import pytest
from sqlalchemy import select
from models.project import Project, File, FileVersion

def test_file_versions_relationship(db_session):
    """测试 File ↔ FileVersion 双向关系"""
    file = db_session.query(File).first()

    # 应该能访问 versions
    assert hasattr(file, 'versions')
    assert isinstance(file.versions, list)

    # 应该能访问 active_version
    assert hasattr(file, 'active_version')

def test_no_relationship_conflicts(db_session):
    """测试没有关系冲突"""
    # 这个查询应该不产生警告
    with pytest.warns(None) as warning_list:
        project = db_session.query(Project).first()
        _ = project.files

    assert len(warning_list) == 0, "不应该有 SQLAlchemy 关系警告"
```

### 2. 使用类型注解

```python
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship

class File(Base):
    # 使用 Mapped 类型注解（SQLAlchemy 2.0 推荐）
    versions: Mapped[List["FileVersion"]] = relationship(
        foreign_keys="FileVersion.file_id",
        back_populates="file"
    )

    active_version: Mapped[Optional["FileVersion"]] = relationship(
        foreign_keys="active_version_id",
        uselist=False
    )
```

### 3. 文档化关系

在每个模型顶部添加注释：

```python
class File(Base, TimestampMixin):
    """
    文件模型

    关系:
    - versions (1:N) → FileVersion [通过 FileVersion.file_id]
    - active_version (1:1) → FileVersion [通过 File.active_version_id]
    - project (N:1) ← Project
    - tables (1:N) → FileTable
    """
```

---

## 🎯 优先级

| 问题 | 优先级 | 影响 | 修复时间估计 |
|------|--------|------|------------|
| File ↔ FileVersion 关系 | 🔴 P0 | 阻塞所有 ORM 查询 | 5分钟 |
| FileVersion exports 冲突 | 🟡 P1 | 导出功能无法使用 | 3分钟 |
| AnnotationJob 未定义关系 | 🟡 P1 | 标注功能无法使用 | 10分钟 |
| 添加测试 | 🟢 P2 | 预防未来问题 | 30分钟 |
| 类型注解 | 🟢 P3 | 代码质量提升 | 1小时 |

---

## 📞 联系信息

**如有疑问，请联系:**
- Backend Team: [你的联系方式]
- 参考文档: [SQLAlchemy Relationship Configuration](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html)

**相关文件:**
- `backend/GrandscaleDB/models/project.py` - 主要修复位置
- `backend/GrandscaleDB/models/annotation.py` - 需要检查
- `backend/app/api/v1/routes_projects_simple.py` - 当前临时方案
- `backend/app/api/v1/routes_projects.py` - 修复后应使用的版本

---

**生成时间:** 2025-10-09
**报告版本:** 1.0
**状态:** ⚠️ 等待数据库团队修复
