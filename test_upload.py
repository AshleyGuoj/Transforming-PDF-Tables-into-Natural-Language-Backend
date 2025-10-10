#!/usr/bin/env python3
"""Test file upload and parse functionality"""
import sys
import requests
import time
sys.path.insert(0, 'backend')
from app.security.auth_stub import get_dev_admin_token

API_BASE = "http://localhost:8000/api/v1"
PROJECT_ID = 1

# Generate token
print("🔑 生成开发 Token...")
token = get_dev_admin_token()
headers = {"Authorization": f"Bearer {token}"}
print("✅ Token 已生成\n")

# Create test PDF
print("📝 创建测试 PDF...")
with open("test.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF")
print("✅ 测试 PDF 已创建\n")

# 1. Upload file
print("1️⃣ 上传 PDF 到项目", PROJECT_ID)
print("-----------------------------------")
try:
    with open("test.pdf", "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = requests.post(
            f"{API_BASE}/projects/{PROJECT_ID}/files",
            headers=headers,
            files=files
        )

    print("状态码:", response.status_code)
    print("响应:", response.json())

    if response.status_code != 201:
        print("❌ 上传失败")
        sys.exit(1)

    file_id = response.json()["file_id"]
    print(f"✅ 上传成功！文件 ID: {file_id}\n")

except Exception as e:
    print(f"❌ 上传失败: {e}")
    sys.exit(1)

# 2. Trigger parse
print("2️⃣ 触发文件解析")
print("-----------------------------------")
try:
    response = requests.post(
        f"{API_BASE}/files/{file_id}/parse",
        headers=headers
    )

    print("状态码:", response.status_code)
    print("响应:", response.json())

    if response.status_code != 200:
        print("❌ 触发解析失败")
        sys.exit(1)

    print("✅ 解析已启动\n")

except Exception as e:
    print(f"❌ 触发解析失败: {e}")
    sys.exit(1)

# 3. Check parse status
print("3️⃣ 检查解析状态")
print("-----------------------------------")
for i in range(5):
    print(f"检查 #{i+1}...")
    try:
        response = requests.get(
            f"{API_BASE}/files/{file_id}/parse-status",
            headers=headers
        )

        data = response.json()
        print("状态:", data.get("status"))

        if data.get("status") in ["completed", "failed"]:
            break

        time.sleep(2)

    except Exception as e:
        print(f"❌ 检查状态失败: {e}")
        break

print()

# 4. Get tables
print("4️⃣ 获取解析的表格")
print("-----------------------------------")
try:
    response = requests.get(
        f"{API_BASE}/files/{file_id}/tables",
        headers=headers
    )

    print("状态码:", response.status_code)
    data = response.json()
    print(f"表格数量: {data.get('total')}")
    print("✅ 测试完成！\n")

except Exception as e:
    print(f"❌ 获取表格失败: {e}")

print("📊 总结：")
print(f"  - 文件 ID: {file_id}")
print(f"  - 前端访问: http://localhost:3000/console/project")
