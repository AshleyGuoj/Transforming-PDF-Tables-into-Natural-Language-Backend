#!/bin/bash

# 🚀 GrandScale AI 项目快速设置脚本
# Quick Setup Script for GrandScale AI Project

set -e  # 遇到错误时停止

echo "=========================================="
echo "🚀 GrandScale AI 项目快速设置"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查必需的软件
echo "📋 步骤 1/6: 检查系统依赖..."

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

MISSING_DEPS=0
check_command python3 || MISSING_DEPS=1
check_command node || MISSING_DEPS=1
check_command npm || MISSING_DEPS=1
check_command psql || MISSING_DEPS=1

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${RED}错误: 缺少必需的依赖。请先安装缺失的软件。${NC}"
    echo "查看 SETUP_GUIDE.md 获取安装说明。"
    exit 1
fi

echo ""

# 检查 PostgreSQL 是否运行
echo "🗄️  步骤 2/6: 检查 PostgreSQL..."

if pg_isready -q; then
    echo -e "${GREEN}✓${NC} PostgreSQL 正在运行"
else
    echo -e "${YELLOW}⚠${NC}  PostgreSQL 未运行，尝试启动..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo systemctl start postgresql
    fi

    sleep 2

    if pg_isready -q; then
        echo -e "${GREEN}✓${NC} PostgreSQL 已启动"
    else
        echo -e "${RED}✗${NC} 无法启动 PostgreSQL，请手动启动"
        exit 1
    fi
fi

echo ""

# 创建数据库
echo "🗄️  步骤 3/6: 设置数据库..."

DB_EXISTS=$(psql -U postgres -lqt | cut -d \| -f 1 | grep -w grandscale_db || echo "")

if [ -z "$DB_EXISTS" ]; then
    echo "创建数据库 grandscale_db..."
    psql -U postgres -c "CREATE DATABASE grandscale_db;" 2>/dev/null || {
        echo -e "${YELLOW}⚠${NC}  数据库可能已存在或需要密码"
        echo "请手动创建: psql -U postgres -c 'CREATE DATABASE grandscale_db;'"
    }
    echo -e "${GREEN}✓${NC} 数据库已创建"
else
    echo -e "${GREEN}✓${NC} 数据库已存在"
fi

echo ""

# 设置后端
echo "⚙️  步骤 4/6: 设置后端..."

cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} 虚拟环境已创建"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装 Python 依赖（这可能需要几分钟）..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓${NC} Python 依赖已安装"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  未找到 .env 文件"
    echo "创建示例 .env 文件..."
    cat > .env << 'EOF'
# 应用环境
APP_ENV=local
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:@localhost:5432/grandscale_db

# JWT 密钥
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256

# CORS 设置
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8000"]

# Azure Document Intelligence (可选)
# AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-endpoint
# AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# OpenAI API (可选)
# OPENAI_API_KEY=your-key
EOF
    echo -e "${GREEN}✓${NC} 已创建 .env 文件（请根据需要修改）"
else
    echo -e "${GREEN}✓${NC} .env 文件已存在"
fi

# 运行数据库迁移
echo "运行数据库迁移..."
alembic upgrade head
echo -e "${GREEN}✓${NC} 数据库迁移完成"

cd ..

echo ""

# 设置前端
echo "⚙️  步骤 5/6: 设置前端..."

cd frontend_updated

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装 Node 依赖（这可能需要几分钟）..."
    npm install --silent
    echo -e "${GREEN}✓${NC} Node 依赖已安装"
else
    echo -e "${GREEN}✓${NC} Node 依赖已存在"
fi

# 检查 .env.local
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}⚠${NC}  未找到 .env.local 文件"
    echo "创建 .env.local 文件..."
    cat > .env.local << 'EOF'
# NextAuth 配置
NEXTAUTH_SECRET=nextauth-secret-change-me-in-production
NEXTAUTH_URL=http://localhost:3000

# 后端 API 地址
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
EOF
    echo -e "${GREEN}✓${NC} 已创建 .env.local 文件"
else
    echo -e "${GREEN}✓${NC} .env.local 文件已存在"
fi

cd ..

echo ""

# 完成
echo "=========================================="
echo -e "${GREEN}✅ 设置完成！${NC}"
echo "=========================================="
echo ""
echo "🚀 启动服务:"
echo ""
echo "终端 1 - 启动后端:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "终端 2 - 启动前端:"
echo "  cd frontend_updated"
echo "  npm run dev"
echo ""
echo "📱 访问应用:"
echo "  前端: http://localhost:3000"
echo "  后端 API 文档: http://localhost:8000/docs"
echo ""
echo "📖 详细文档: 查看 SETUP_GUIDE.md"
echo ""
