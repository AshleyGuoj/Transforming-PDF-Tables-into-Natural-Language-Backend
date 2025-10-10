# PDF 上传功能调试指南

## 🐛 调试步骤

### 1. 检查前端是否运行
```bash
# 访问前端
http://localhost:3000

# 检查进程
lsof -ti:3000
```

### 2. 检查后端是否运行
```bash
# 访问后端健康检查
curl http://localhost:8000/health

# 检查进程
lsof -ti:8000
```

### 3. 使用测试页面
访问: `http://localhost:3000/test-upload`

这是一个简化的测试页面，可以：
- 选择 PDF 文件
- 查看文件信息
- 点击上传并查看结果
- 在控制台查看详细日志

### 4. 检查浏览器控制台
1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 尝试上传文件
4. 查看日志输出：
   - 🎯 handleFileUpload 被调用
   - 📡 FilesAPI.upload 开始
   - 📦 FormData 创建完成
   - 📨 收到响应

### 5. 检查网络请求
在浏览器开发者工具中：
1. 切换到 Network 标签
2. 尝试上传文件
3. 查找 `files` 请求
4. 检查：
   - Request Headers (应该包含 Content-Type: multipart/form-data)
   - Request Payload (应该包含文件)
   - Response Status (应该是 201)
   - Response Body

### 6. 常见问题排查

#### 问题 1: "请先选择项目"
**原因**: `selectedProject` 为 null
**解决**:
1. 确保先点击一个项目卡片
2. 然后再点击"上传PDF"按钮

#### 问题 2: "401 Unauthorized"
**原因**: 缺少认证 token
**当前状态**: API 需要认证，但前端还没实现认证

**临时解决方案** - 在 API 中添加开发 token:

编辑 `frontend_updated/lib/api/index.ts`:

```typescript
// 在文件顶部添加开发 token
const DEV_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGd1aWRlbGluZS10cmFuc2Zvcm0uY29tIiwib3JnX2lkIjoxLCJvcmdhbml6YXRpb25fcm9sZSI6ImFkbWluIiwicHJvamVjdF9pZCI6MSwicHJvamVjdF9yb2xlIjoiYWRtaW4iLCJleHAiOjE3NjAwNTc3MzAsImlhdCI6MTc2MDA1NTkzMH0.o4I6HF9F5EmjVPWMs-yUtQi13y3HyJSGvPAjPrFpNao";

// 在 upload 函数中添加 Authorization header:
async upload(projectId: number, file: globalThis.File) {
  // ...
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/files`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${DEV_TOKEN}`  // 添加这行
    },
    body: formData,
  });
  // ...
}
```

**永久解决方案**: 实现完整的前端认证流程

#### 问题 3: "CORS Error"
**原因**: 跨域请求被阻止
**检查**: 后端 `main.py` 中的 CORS 配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 问题 4: "Network Error"
**原因**: 无法连接到后端
**检查**:
1. 后端是否运行在 `http://localhost:8000`
2. 环境变量 `NEXT_PUBLIC_API_BASE_URL` 是否正确

### 7. 手动测试 API

使用 Python 测试上传功能:

```bash
cd /path/to/project
python3 test_upload.py
```

或使用 curl:

```bash
# 生成 token
TOKEN=$(python3 get_token.py 2>&1 | tail -1)

# 上传文件
curl -X POST "http://localhost:8000/api/v1/projects/1/files" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"
```

### 8. 检查后端日志

如果后端有日志文件：
```bash
tail -f backend/logs/*.log
```

或查看 uvicorn 控制台输出

## 📝 需要的信息

当报告 bug 时，请提供：

1. **错误信息**
   - 浏览器控制台的完整错误
   - 网络请求的状态码和响应

2. **环境信息**
   - 前端是否运行: `lsof -ti:3000`
   - 后端是否运行: `lsof -ti:8000`
   - Node.js 版本: `node -v`
   - Python 版本: `python3 --version`

3. **复现步骤**
   - 具体点击了什么
   - 选择了什么文件
   - 看到了什么错误消息

4. **截图**
   - 浏览器控制台 (Console 标签)
   - 网络请求 (Network 标签)
   - 错误弹窗

## 🔧 快速修复：添加认证 Token

**最可能的问题**是缺少认证。快速修复方法：

1. 生成新的 token (token 会过期):
```bash
cd /path/to/project
python3 get_token.py
```

2. 复制输出的 token

3. 编辑 `frontend_updated/lib/api/index.ts`，在 FilesAPI.upload 中添加:
```typescript
headers: {
  "Authorization": "Bearer <paste_token_here>"
}
```

4. 刷新浏览器页面

5. 再次尝试上传

## 🎯 下一步

如果上传成功，你应该会看到：
- ✅ 上传成功的消息
- 文件 ID
- 自动触发解析
- 解析状态轮询
- 最终显示解析结果（表格列表）
