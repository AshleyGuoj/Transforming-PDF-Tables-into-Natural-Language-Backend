# 🐛 PDF 上传功能 Bug 修复总结

## 问题诊断

上传 PDF 按钮的主要问题是：**缺少认证 Token**

所有 API 请求都需要 JWT 认证，但前端没有获取和发送 token。

## ✅ 已完成的修复

### 1. 创建 Dev Token Endpoint (后端)

**文件**: `backend/app/api/v1/routes_dev.py`

- 新增 `/api/dev-token` endpoint
- 自动生成 24 小时有效期的开发 token
- 仅在开发环境启用（生产环境会禁用）

**测试**:
```bash
curl -X POST http://localhost:8000/api/dev-token
```

### 2. 注册 Dev Routes (后端)

**文件**: `backend/app/main.py`

- 导入 `routes_dev`
- 在开发环境自动注册
- 添加安全警告日志

### 3. 自动获取 Token (前端)

**文件**: `frontend_updated/lib/api/index.ts`

添加了 `getDevToken()` 函数：
- 自动从后端获取 token
- 缓存 token 避免重复请求
- 在所有 API 调用中自动添加 Authorization header

### 4. 更新 Files API (前端)

**文件**: `frontend_updated/lib/api/index.ts`

- `FilesAPI.upload()` 自动添加认证
- `fetchAPI()` 统一处理认证
- 所有 API 请求都包含 token

### 5. 增强调试日志 (前端)

**文件**: `frontend_updated/components/console/FilesGuidelines.tsx`

添加详细的调试日志：
- 文件信息
- 上传进度
- API 调用参数
- 错误详情

## 🧪 测试方法

### 方法 1: 使用独立测试页面

打开浏览器访问：
```
file:///path/to/project/test_frontend_api.html
```

步骤：
1. 点击 "测试获取 Token"
2. 选择 PDF 文件
3. 点击 "上传文件"
4. 查看日志和状态

### 方法 2: 使用 Next.js 测试页面

访问：
```
http://localhost:3000/test-upload
```

### 方法 3: 使用实际组件

访问：
```
http://localhost:3000/console/project
```

步骤：
1. 点击任意项目
2. 点击右上角 "上传PDF"
3. 选择文件
4. 查看浏览器控制台 (F12)

## 📋 预期行为

### 成功流程：

```
🔑 Fetching new dev token from backend...
✅ Dev token obtained: Development token generated. Valid for 24 hours.
📡 FilesAPI.upload 开始
📦 FormData 创建完成
📨 收到响应 { status: 201, statusText: 'Created' }
✅ 上传成功: { file_id: 8, file_name: "example.pdf", ... }
🧠 准备触发解析...
✅ 解析已启动
📊 解析状态: processing
📊 解析状态: completed
✅ 解析完成！发现 12 个表格
```

### 控制台输出示例：

```javascript
{
  fileName: "example.pdf",
  fileSize: 524288,
  fileType: "application/pdf",
  selectedProject: { id: 1, name: "测试项目" }
}
```

## 🔧 如果仍有问题

### 检查清单：

#### ✅ 1. 后端运行
```bash
curl http://localhost:8000/health
# 应返回: {"status":"healthy","service":"guideline-transform-ai"}
```

#### ✅ 2. Dev Token Endpoint
```bash
curl -X POST http://localhost:8000/api/dev-token
# 应返回包含 token 的 JSON
```

#### ✅ 3. 前端运行
```bash
curl http://localhost:3000
# 应返回 HTML
```

#### ✅ 4. 浏览器控制台
打开 F12 Developer Tools，检查：
- **Console 标签**: 查看日志和错误
- **Network 标签**: 查看 API 请求/响应

### 常见错误及解决方法：

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `401 Unauthorized` | Token 无效或过期 | 重新加载页面获取新 token |
| `403 Forbidden` | 权限不足 | 检查 token 是否为 admin 角色 |
| `404 Not Found` | 项目不存在 | 检查项目 ID 是否正确 |
| `CORS Error` | 跨域问题 | 检查后端 CORS 配置 |
| `Network Error` | 后端未运行 | 启动后端服务 |

## 📁 修改的文件列表

### 后端：
- ✅ `backend/app/api/v1/routes_dev.py` (新建)
- ✅ `backend/app/main.py` (修改)
- ✅ `backend/app/security/auth_stub.py` (修改 - 修复 org_id 类型)

### 前端：
- ✅ `frontend_updated/lib/api/index.ts` (修改 - 添加认证)
- ✅ `frontend_updated/components/console/FilesGuidelines.tsx` (修改 - 添加日志)
- ✅ `frontend_updated/app/test-upload/page.tsx` (新建 - 测试页面)

### 测试工具：
- ✅ `test_frontend_api.html` (新建 - 独立测试页面)
- ✅ `UPLOAD_DEBUG_GUIDE.md` (新建 - 调试指南)

## 🎯 下一步（可选优化）

1. **实现完整认证流程**
   - 替换 dev token 为真实的登录系统
   - 添加 token 刷新机制
   - 实现用户会话管理

2. **改进错误处理**
   - 显示用户友好的错误消息
   - 添加重试机制
   - 实现上传进度条

3. **增强功能**
   - 支持多文件上传
   - 支持拖拽上传
   - 显示实时解析进度

## 💡 使用提示

- Token 有效期为 24 小时
- 每次页面刷新会自动获取新 token
- Token 会被缓存，避免重复请求
- 所有 API 调用都会自动添加认证

## 🔒 安全注意事项

⚠️ **重要**: Dev token endpoint 仅用于开发！

在生产环境中：
- 设置 `APP_ENV=production`
- Dev token endpoint 会自动禁用
- 必须实现真实的认证系统

## ✅ 验证成功

如果看到以下输出，说明修复成功：

1. **浏览器控制台**：
   ```
   ✅ Dev token obtained: Development token generated. Valid for 24 hours.
   ✅ 上传成功: {file_id: 8, ...}
   ✅ 解析已启动
   ```

2. **页面显示**：
   - 上传进度条
   - "解析中" 状态
   - 最终显示 "已完成" 和表格数量

3. **后端日志**：
   ```
   [info] User 1 uploading file to project 1
   [info] File 8 uploaded successfully
   [info] User 1 triggering parse for file 8
   ```

---

**修复时间**: 2025-10-09
**修复者**: Claude
**状态**: ✅ 完成并测试
