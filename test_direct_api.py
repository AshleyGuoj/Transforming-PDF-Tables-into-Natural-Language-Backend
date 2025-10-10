#!/usr/bin/env python3
"""Test API directly"""
import sys
import requests
sys.path.insert(0, 'backend')
from app.security.auth_stub import get_dev_admin_token

# Generate token
token = get_dev_admin_token()
print(f"Token: {token[:50]}...")

# Test health endpoint (no auth needed)
print("\n🏥 测试 Health endpoint...")
response = requests.get("http://localhost:8000/health")
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}\n")

# Test projects endpoint (needs auth)
print("📁 测试 Projects endpoint (需要认证)...")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/projects", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ 成功！找到 {len(data)} 个项目")
    if len(data) > 0:
        print(f"第一个项目: {data[0].get('name')}")
else:
    print(f"❌ 失败: {response.json()}")
