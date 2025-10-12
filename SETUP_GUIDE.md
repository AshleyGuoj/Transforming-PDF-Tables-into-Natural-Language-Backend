# 🚀 项目设置指南 (Setup Guide)

本指南帮助新团队成员从 GitHub clone 项目后，快速设置并运行后端和数据库。

## 📋 前置要求 (Prerequisites)

确保你的系统已安装以下软件：

- **Python 3.9+** - [下载](https://www.python.org/downloads/)
- **Node.js 18+** - [下载](https://nodejs.org/)
- **PostgreSQL 14+** - [下载](https://www.postgresql.org/download/)
- **Git** - [下载](https://git-scm.com/downloads/)

---

## 📥 第 1 步：克隆项目

```bash
git clone https://github.com/AshleyGuoj/Transforming-PDF-Tables-into-Natural-Language-Backend.git
cd Transforming-PDF-Tables-into-Natural-Language-Backend
```

---

## 🗄️ 第 2 步：设置 PostgreSQL 数据库

### 2.1 启动 PostgreSQL 服务

**macOS (使用 Homebrew):**
```bash
brew services start postgresql@14
```

**Linux:**
```bash
sudo systemctl start postgresql
```

**Windows:**
- 打开 pgAdmin 或 PostgreSQL 服务管理器
- 启动 PostgreSQL 服务

### 2.2 创建数据库

```bash
# 连接到 PostgreSQL
psql -U postgres

# 在 psql 提示符中执行：
CREATE DATABASE grandscale_db;

# 验证数据库创建成功
\l

# 退出
\q
```

### 2.3 运行数据库迁移

```bash
cd backend

# 激活虚拟环境（如果还没创建，先创建）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行 Alembic 迁移
alembic upgrade head
```

### 2.4 （可选）添加种子数据

```bash
# 在 backend 目录下，激活虚拟环境后
python -m app.db.seed
```

---

## ⚙️ 第 3 步：配置环境变量

### 3.1 后端环境变量

创建 `backend/.env` 文件：

```bash
cd backend
cp .env.example .env  # 如果有示例文件
# 或者手动创建
nano .env
```

添加以下内容：

```env
# 应用环境
APP_ENV=local
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/grandscale_db

# JWT 密钥（生产环境请更换）
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Azure Document Intelligence (用于 PDF 解析)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-azure-endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-azure-key

# CORS 设置
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8000"]

# OpenAI API（可选，用于 AI 生成功能）
OPENAI_API_KEY=your-openai-key
```

**重要提示：**
- 将 `YOUR_PASSWORD` 替换为你的 PostgreSQL 密码
- 如果 PostgreSQL 没有设置密码，可以省略 `:YOUR_PASSWORD` 部分
- Azure 和 OpenAI 的 key 需要从相应平台获取

### 3.2 前端环境变量

创建 `frontend_updated/.env.local` 文件：

```bash
cd ../frontend_updated
nano .env.local
```

添加以下内容：

```env
# NextAuth 配置
NEXTAUTH_SECRET=nextauth-secret-change-me-in-production
NEXTAUTH_URL=http://localhost:3000

# 后端 API 地址（注意：必须是 NEXT_PUBLIC_API_BASE_URL）
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 🚀 第 4 步：启动服务

### 4.1 启动后端服务

```bash
cd backend
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 启动后端
uvicorn app.main:app --reload --port 8000
```

你应该看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✅ Database connection established
```

**测试后端：**
- 打开浏览器访问 http://localhost:8000/docs
- 你应该看到 FastAPI Swagger UI 文档

### 4.2 启动前端服务

**新开一个终端窗口：**

```bash
cd frontend_updated

# 安装依赖
npm install

# 启动前端
npm run dev
```

你应该看到：
```
✓ Ready in 1.5s
- Local:        http://localhost:3000
- Network:      http://0.0.0.0:3000
```

**访问前端：**
- 打开浏览器访问 http://localhost:3000

---

## ✅ 第 5 步：验证设置

### 5.1 检查数据库连接

```bash
# 在 backend 目录下
python << 'EOF'
import asyncio
import asyncpg

async def test_db():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='',  # 如果有密码，填写在这里
        database='grandscale_db'
    )

    # 检查表
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public';
    """)

    print("✅ 数据库连接成功！")
    print(f"📊 找到 {len(tables)} 个表:")
    for table in tables:
        print(f"   - {table['table_name']}")

    await conn.close()

asyncio.run(test_db())
EOF
```

### 5.2 测试文件上传

1. 访问 http://localhost:3000
2. 登录（开发模式下会自动绕过认证）
3. 进入项目页面
4. 尝试上传一个 PDF 文件
5. 检查是否成功解析表格

---

## 🐛 常见问题 (Troubleshooting)

### 问题 1: 数据库连接失败

**错误信息：** `connection refused` 或 `password authentication failed`

**解决方案：**
```bash
# 1. 确认 PostgreSQL 正在运行
pg_isready

# 2. 检查 PostgreSQL 状态
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# 3. 重置 PostgreSQL 密码（如果需要）
psql -U postgres
ALTER USER postgres PASSWORD 'new_password';
```

### 问题 2: 端口被占用

**错误信息：** `Address already in use`

**解决方案：**
```bash
# 查看占用端口的进程
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 终止进程
kill -9 <PID>
```

### 问题 3: PDF 上传失败 "Failed to fetch"

**解决方案：**
- 检查 `frontend_updated/.env.local` 中的 `NEXT_PUBLIC_API_BASE_URL`
- 确保设置为 `http://localhost:8000/api/v1` (包含 `/api/v1`)
- 重启前端服务使环境变量生效

### 问题 4: Python 依赖安装失败

**解决方案：**
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像（如果需要）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果特定包失败，尝试单独安装
pip install asyncpg
pip install sqlalchemy[asyncio]
```

### 问题 5: Alembic 迁移失败

**错误信息：** `Target database is not up to date`

**解决方案：**
```bash
# 检查当前迁移版本
alembic current

# 查看所有迁移
alembic history

# 强制升级到最新版本
alembic upgrade head

# 如果还是失败，可以重置数据库（⚠️ 会丢失所有数据）
# DROP DATABASE grandscale_db;
# CREATE DATABASE grandscale_db;
# alembic upgrade head
```

---

## 📚 项目结构

```
Transforming-PDF-Tables-into-Natural-Language-Backend/
├── backend/                      # FastAPI 后端
│   ├── app/
│   │   ├── api/                 # API 路由
│   │   ├── core/                # 核心配置
│   │   ├── db/                  # 数据库模型和会话
│   │   ├── security/            # 认证和授权
│   │   └── services/            # 业务逻辑
│   ├── alembic/                 # 数据库迁移
│   ├── uploads/                 # 上传文件存储
│   ├── .env                     # 环境变量
│   └── requirements.txt         # Python 依赖
│
├── frontend_updated/            # Next.js 前端
│   ├── app/                     # Next.js 13+ App Router
│   ├── components/              # React 组件
│   ├── lib/                     # API 客户端
│   ├── .env.local              # 前端环境变量
│   └���─ package.json            # Node 依赖
│
├── GrandscaleDB/               # 数据库模型定义
│   └── models.py
│
└── SETUP_GUIDE.md              # 本文件
```

---

## 🔑 开发模式说明

### 认证绕过

在开发环境下（`APP_ENV=local`），后端会自动绕过 JWT 认证：
- 所有请求都会被视为已认证的管理员用户
- 用户 ID: 1, 组织 ID: 1
- ⚠️ 生产环境必须禁用此功能

### 默认凭据

如果运行了种子数据脚本，可以使用：
- **Email**: `admin@guideline-transform.com`
- **Password**: `admin123`

---

## 📞 需要帮助？

如果遇到问题：
1. 查看上面的 **常见问题** 部分
2. 检查后端日志：终端窗口运行 `uvicorn` 的输出
3. 检查前端日志：浏览器开发者工具 Console
4. 联系团队成员获取帮助

---

## 📝 下一步

设置完成后，你可以：
1. 阅读 [API 文档](http://localhost:8000/docs)
2. 查看 [项目文档](./README.md)
3. 开始开发新功能 🎉

---

**最后更新**: 2025-10-12
**维护者**: GrandScale Team
