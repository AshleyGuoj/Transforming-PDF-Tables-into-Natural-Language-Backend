#!/usr/bin/env python3
"""Test JWT token creation and decoding"""
import sys
sys.path.insert(0, 'backend')
from app.security.auth_stub import get_dev_admin_token, decode_jwt_token

# Generate token
print("🔑 生成 Token...")
token = get_dev_admin_token()
print(f"Token: {token}\n")

# Decode token
print("🔓 解码 Token...")
payload = decode_jwt_token(token)

if payload:
    print("✅ Token 解码成功!")
    print(f"  - user_id: {payload.user_id}")
    print(f"  - email: {payload.email}")
    print(f"  - org_id: {payload.org_id}")
    print(f"  - organization_role: {payload.organization_role}")
    print(f"  - project_id: {payload.project_id}")
    print(f"  - project_role: {payload.project_role}")
    print(f"  - exp: {payload.exp}")
    print(f"  - iat: {payload.iat}")
else:
    print("❌ Token 解码失败!")
