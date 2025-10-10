# 🚀 PDF 上传功能快速测试指南

## ✅ Bug 已修复！

主要问题：**缺少认证 Token** ✅ 已解决

## 🧪 立即测试（3 种方法）

### 方法 1: 独立 HTML 测试页面 ⭐ 推荐

最简单的测试方法，无需 Next.js：

```bash
# 在浏览器中打开
open test_frontend_api.html
# 或
file:///path/to/project/test_frontend_api.html
```

**步骤**:
1. 点击 "1. 测试获取 Token" → 应该显示 ✅ Token 已获取
2. 选择一个 PDF 文件
3. 点击 "2. 上传文件"
4. 查看日志和状态

### 方法 2: Next.js 测试页面

```bash
# 访问
http://localhost:3000/test-upload
```

### 方法 3: 实际组件

```bash
# 访问
http://localhost:3000/console/project
```

1. 点击任意项目卡片
2. 点击右上角 "上传PDF" 按钮
3. 选择 PDF 文件
4. 打开浏览器控制台 (F12) 查看详细日志

## 🔍 查看日志

### 浏览器控制台日志：

按 `F12` 打开开发者工具，应该看到：

```javascript
🔑 Fetching new dev token from backend...
✅ Dev token obtained: Development token generated. Valid for 24 hours.
🎯 handleFileUpload 被调用 { fileName: "test.pdf", ... }
📡 FilesAPI.upload 开始
📦 FormData 创建完成
📨 收到响应 { status: 201, statusText: 'Created' }
✅ 上传成功
🧠 准备触发解析...
```

## ❌ 如果遇到错误

### 错误 1: "Failed to fetch" 或 "Network Error"

**原因**: 后端未运行

**解决**:
```bash
# 检查后端
curl http://localhost:8000/health

# 如果没响应，启动后端
cd backend
uvicorn app.main:app --reload
```

### 错误 2: "401 Unauthorized"

**原因**: Token 获取失败（不应该发生了）

**解决**:
```bash
# 测试 dev-token endpoint
curl -X POST http://localhost:8000/api/dev-token
```

### 错误 3: "Database error"

**原因**: 数据库表结构或连接问题

**解决**:
```bash
# 检查数据库连接
psql -U postgres -d guideline_transform -c "SELECT COUNT(*) FROM projects;"
```

### 错误 4: "CORS Error"

**原因**: 跨域配置问题

**检查**: 后端 main.py 中应该有：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🎯 修复内容总结

### ✅ 已完成：

1. **后端**: 添加 `/api/dev-token` endpoint
   - 自动生成 24 小时有效的 admin token
   - 仅在开发环境启用

2. **前端**: 自动获取和使用 token
   - `getDevToken()` 函数自动从后端获取
   - 所有 API 调用自动添加 `Authorization` header
   - Token 会被缓存，避免重复请求

3. **调试**: 增强日志输出
   - 文件信息、上传进度、错误详情
   - 在浏览器控制台可见

### 📁 修改的文件：

**后端**:
- ✅ `backend/app/api/v1/routes_dev.py` (新建)
- ✅ `backend/app/main.py` (添加 dev routes)
- ✅ `backend/app/security/auth_stub.py` (修复 org_id 类型)

**前端**:
- ✅ `frontend_updated/lib/api/index.ts` (自动认证)
- ✅ `frontend_updated/components/console/FilesGuidelines.tsx` (调试日志)
- ✅ `frontend_updated/app/test-upload/page.tsx` (测试页面)

## 🔧 手动测试 Token

如果想手动测试，可以在浏览器控制台运行：

```javascript
// 1. 测试获取 token
fetch('http://localhost:8000/api/dev-token', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    console.log('Token:', data.token);
    window.devToken = data.token;
  });

// 2. 测试上传（选择文件后）
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];
const formData = new FormData();
formData.append('file', file);

fetch('http://localhost:8000/api/v1/projects/1/files', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${window.devToken}` },
  body: formData
})
  .then(r => r.json())
  .then(data => console.log('Upload result:', data));
```

## 📊 预期成功流程

1. ✅ 页面加载 → 自动获取 token
2. ✅ 选择 PDF 文件
3. ✅ 点击上传
4. ✅ 显示上传进度
5. ✅ 上传成功 → 自动触发解析
6. ✅ 轮询解析状态
7. ✅ 显示 "解析完成" 和表格数量

## 💡 提示

- Token 有效期 24 小时
- 每次刷新页面会自动获取新 token
- Token 被缓存，不会重复请求
- 打开浏览器控制台 (F12) 查看详细日志

## 🎉 成功标志

如果看到以下内容，说明一切正常：

**浏览器控制台**:
```
✅ Dev token obtained: Development token generated. Valid for 24 hours.
✅ 上传成功: {file_id: 8, file_name: "test.pdf", ...}
```

**页面显示**:
- 进度条动画
- "解析中" 状态
- 最终显示 "已完成"

## 📞 还有问题？

请提供：
1. 浏览器控制台的完整错误信息 (F12 → Console)
2. 网络请求详情 (F12 → Network → 点击失败的请求)
3. 截图

---

**修复时间**: 2025-10-09
**状态**: ✅ 完成
**测试**: 使用 `test_frontend_api.html` 测试
