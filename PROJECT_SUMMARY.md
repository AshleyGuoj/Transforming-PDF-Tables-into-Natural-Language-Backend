# PDF表格转自然语言项目 - 完整实现总结

## 🎯 项目概述

本项目是一个完整的PDF表格提取和自然语言转换系统，包含前端（Next.js）和后端（FastAPI），支持多用户、多组织的协作工作流。

## 🏗️ 系统架构

### 后端 (FastAPI + PostgreSQL)
- **API服务**: FastAPI框架，RESTful API设计
- **数据库**: PostgreSQL + SQLAlchemy ORM
- **认证**: JWT + RBAC权限控制
- **文件处理**: Azure Document Intelligence集成
- **任务管理**: 异步任务处理系统

### 前端 (Next.js + React)
- **框架**: Next.js 14 + React 18
- **UI组件**: Tailwind CSS + 自定义组件
- **状态管理**: React Context + 自定义hooks
- **认证**: NextAuth.js集成
- **API集成**: 统一的API服务层

## ✨ 核心功能

### 1. 项目管理
- ✅ 多组织支持
- ✅ 项目创建、编辑、删除
- ✅ 项目状态跟踪
- ✅ 权限控制

### 2. 文件处理
- ✅ PDF文件上传
- ✅ Azure Document Intelligence集成
- ✅ 表格自动提取
- ✅ 文件版本管理
- ✅ 批量文件处理

### 3. 表格数据管理
- ✅ 表格结构识别
- ✅ 数据提取和存储
- ✅ 表格预览功能
- ✅ 数据导出功能

### 4. 任务分配系统
- ✅ 智能任务分配
- ✅ 任务状态跟踪
- ✅ 用户工作负载管理
- ✅ 任务优先级设置

### 5. 用户界面
- ✅ 响应式设计
- ✅ 多角色控制台
- ✅ 实时数据更新
- ✅ 直观的操作界面

## 📁 项目结构

```
Transforming-PDF-Tables-into-Natural-Language-Backend/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── api/v1/            # API路由
│   │   ├── core/              # 核心配置
│   │   ├── crud/              # 数据库操作
│   │   ├── db/                # 数据库模型
│   │   ├── schemas/           # Pydantic模型
│   │   └── services/          # 业务逻辑
│   ├── requirements.txt       # Python依赖
│   └── seed_initial_data.py   # 初始数据
├── frontend_updated/          # Next.js前端
│   ├── app/                   # 页面路由
│   ├── components/            # React组件
│   ├── lib/                   # 工具函数
│   └── types/                 # TypeScript类型
├── docs/                      # 文档
├── .gitignore                 # Git忽略文件
└── README.md                  # 项目说明
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Azure Document Intelligence服务

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/AshleyGuoj/Transforming-PDF-Tables-into-Natural-Language-Backend.git
cd Transforming-PDF-Tables-into-Natural-Language-Backend
```

2. **后端设置**
```bash
cd backend
pip install -r requirements.txt
cp env.example .env
# 配置环境变量
python seed_initial_data.py
python -m uvicorn app.main:app --reload --port 8000
```

3. **前端设置**
```bash
cd frontend_updated
npm install
cp env.local.example .env.local
# 配置环境变量
npm run dev
```

4. **访问应用**
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 🔧 配置说明

### 环境变量

**后端 (.env)**
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key
JWT_SECRET_KEY=your_secret_key
```

**前端 (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=your_secret_key
NEXTAUTH_URL=http://localhost:3000
```

## 📊 数据库设计

### 核心表结构
- `organization` - 组织管理
- `user` - 用户管理
- `project` - 项目管理
- `file` - 文件管理
- `file_table` - 表格数据
- `annotation_job` - 任务分配

### 关系设计
- 多对多用户-组织关系
- 一对多组织-项目关系
- 一对多项目-文件关系
- 一对多文件-表格关系

## 🔐 安全特性

- JWT令牌认证
- 基于角色的访问控制(RBAC)
- 组织级数据隔离
- 文件上传安全验证
- API请求限流

## 📈 性能优化

- 数据库查询优化
- 异步任务处理
- 文件缓存机制
- 前端组件懒加载
- API响应缓存

## 🧪 测试覆盖

- 单元测试
- 集成测试
- API端点测试
- 前端组件测试
- 端到端测试

## 📚 文档资源

- [GITHUB_SYNC_CHECKLIST.md](GITHUB_SYNC_CHECKLIST.md) - 团队协作设置指南
- [TABLE_INTEGRATION_SUMMARY.md](TABLE_INTEGRATION_SUMMARY.md) - 表格功能说明
- [TASK_SYNC_GUIDE.md](TASK_SYNC_GUIDE.md) - 任务管理指南
- [VIEW_FEATURES_IMPLEMENTATION.md](VIEW_FEATURES_IMPLEMENTATION.md) - 视图功能实现
- [FRONTEND_INTEGRATION_GUIDE.md](frontend_updated/FRONTEND_INTEGRATION_GUIDE.md) - 前端集成指南

## 🚀 部署指南

### Docker部署
```bash
docker-compose up -d
```

### 生产环境
- 使用环境变量配置
- 设置HTTPS
- 配置数据库备份
- 监控和日志

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

MIT License

## 👥 团队

- 后端开发: FastAPI + PostgreSQL
- 前端开发: Next.js + React
- 数据库设计: 规范化设计
- 文档维护: 完整的技术文档

## 🎉 项目亮点

1. **完整的全栈解决方案** - 从数据库到用户界面的完整实现
2. **企业级架构** - 支持多组织、多用户、权限控制
3. **现代化技术栈** - 使用最新的前后端技术
4. **详细的文档** - 完整的设置和使用指南
5. **可扩展设计** - 模块化架构，易于扩展和维护

---

**项目状态**: ✅ 完成
**最后更新**: 2025-01-17
**版本**: v1.0.0
