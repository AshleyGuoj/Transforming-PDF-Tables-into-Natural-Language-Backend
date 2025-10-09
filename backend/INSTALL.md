# 📦 GrandScale Backend - 安装指南

快速安装所有依赖的完整指南。

---

## 🚀 快速开始

### 方法 1: 一键安装（推荐）⭐

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 3. 升级 pip
pip install --upgrade pip

# 4. 安装所有依赖（完整版）
pip install -r requirements.txt

# 或安装最小依赖（核心功能）
pip install -r requirements-minimal.txt
```

**完成！** 🎉

---

## 📋 安装选项对比

| 文件 | 包含内容 | 适用场景 | 安装时间 |
|------|---------|---------|---------|
| `requirements.txt` | 所有依赖（含可选功能） | 生产环境、完整开发 | ~5 分钟 |
| `requirements-minimal.txt` | 仅核心依赖 | 快速测试、最小化部署 | ~2 分钟 |

---

## 📦 依赖包说明

### 核心依赖（必须安装）

```bash
# Web 框架
fastapi                 # FastAPI 框架
uvicorn[standard]       # ASGI 服务器
python-multipart        # 文件上传支持

# 数据库
sqlalchemy             # ORM
asyncpg                # 异步 PostgreSQL 驱动
psycopg2-binary        # 同步 PostgreSQL 驱动
greenlet               # 异步支持

# 数据验证
pydantic               # 数据验证
pydantic-settings      # 配置管理
email-validator        # 邮箱验证

# 配置与日志
python-dotenv          # .env 文件支持
structlog              # 结构化日志
python-json-logger     # JSON 日志

# 安全
python-jose[cryptography]  # JWT 令牌
passlib[bcrypt]           # 密码哈希
```

### 可选依赖（按需安装）

```bash
# 云存储（文件上传功能）
pip install boto3

# 后台任务
pip install celery redis

# PDF 处理
pip install PyMuPDF pdfplumber

# Azure 服务
pip install azure-ai-formrecognizer

# AI 模型
pip install openai anthropic

# 测试工具
pip install pytest pytest-asyncio pytest-cov

# 开发工具
pip install black flake8 isort mypy
```

---

## 🔍 验证安装

### 检查所有包是否安装成功

```bash
# 列出已安装的包
pip list

# 检查特定包
pip show fastapi sqlalchemy pydantic
```

### 测试导入

```bash
python3 -c "
import fastapi
import sqlalchemy
import pydantic
print('✅ 核心依赖安装成功！')
"
```

### 测试数据库连接

```bash
python3 -c "
import asyncio
from app.db.session import check_database_connection
result = asyncio.run(check_database_connection())
print('✅ 数据库连接正常' if result else '❌ 数据库连接失败')
"
```

### 启动服务器测试

```bash
uvicorn app.main:app --reload --port 8000
```

访问: http://localhost:8000/docs

---

## 🐛 常见问题

### 问题 1: `pip install` 失败

**原因:** pip 版本过旧

**解决:**
```bash
pip install --upgrade pip
pip install --upgrade setuptools wheel
```

### 问题 2: `psycopg2-binary` 安装失败

**原因:** 缺少 PostgreSQL 开发库

**解决 (Mac):**
```bash
brew install postgresql
```

**解决 (Ubuntu/Debian):**
```bash
sudo apt-get install libpq-dev python3-dev
```

### 问题 3: `cryptography` 编译错误

**原因:** 缺少编译工具

**解决 (Mac):**
```bash
xcode-select --install
```

**解决 (Ubuntu/Debian):**
```bash
sudo apt-get install build-essential libssl-dev libffi-dev
```

### 问题 4: 权限错误

**解决:** 使用虚拟环境（推荐）或添加 `--user` 标志
```bash
pip install --user -r requirements.txt
```

### 问题 5: 网络超时

**解决:** 使用国内镜像源
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📊 安装后的目录结构

```
backend/
├── venv/                    ← 虚拟环境（创建后）
├── app/
│   ├── main.py
│   ├── api/
│   ├── crud/
│   ├── db/
│   └── ...
├── requirements.txt         ← 完整依赖列表 ⭐
├── requirements-minimal.txt ← 最小依赖列表
├── INSTALL.md              ← 本文件
└── .env                    ← 环境配置（需创建）
```

---

## 🔄 更新依赖

### 更新所有包到最新版本

```bash
pip install --upgrade -r requirements.txt
```

### 更新特定包

```bash
pip install --upgrade fastapi sqlalchemy
```

### 生成当前环境的 requirements

```bash
pip freeze > requirements-frozen.txt
```

---

## 🌍 不同环境的安装

### 开发环境

```bash
# 安装所有依赖（包括开发工具）
pip install -r requirements.txt
```

### 生产环境

```bash
# 仅安装核心依赖
pip install -r requirements-minimal.txt

# 根据需要添加可选依赖
pip install boto3 celery redis
```

### Docker 环境

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ✅ 安装完成检查清单

- [ ] Python 3.9+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] pip 已升级到最新版本
- [ ] requirements.txt 所有包已安装
- [ ] 导入测试通过
- [ ] PostgreSQL 已安装并运行
- [ ] `.env` 文件已配置
- [ ] 数据库连接测试通过
- [ ] FastAPI 服务器可以启动
- [ ] `/docs` 页面可以访问

---

## 📞 需要帮助？

如遇到问题：

1. 检查 Python 版本: `python3 --version` (需要 3.9+)
2. 检查 pip 版本: `pip --version`
3. 查看详细日志: `pip install -v -r requirements.txt`
4. 参考 `docs/DEPLOY_GUIDE.md` 获取更多信息
5. 查看 `docs/backend_setup.md` 了解完整设置流程

---

## 🎯 下一步

安装完成后，请参考：

1. **环境配置:** `docs/DEPLOY_GUIDE.md` - 配置 .env 文件
2. **数据库设置:** `docs/backend_setup.md` - 初始化数据库
3. **API 文档:** 启动服务器后访问 `/docs`

---

*最后更新: 2025-10-09*  
*版本: 1.0.0*

