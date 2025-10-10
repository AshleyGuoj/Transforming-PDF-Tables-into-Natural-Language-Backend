#!/usr/bin/env python3
"""Full debug of JWT token decoding"""
import sys
import logging
sys.path.insert(0, 'backend')

# Enable all logging
logging.basicConfig(level=logging.DEBUG)

from app.security.auth_stub import get_dev_admin_token, decode_jwt_token
from datetime import datetime

# Generate token
print("🔑 生成 Token...")
token = get_dev_admin_token()
print(f"Token生成时间: {datetime.utcnow()}")
print(f"Token: {token[:50]}...\n")

# Decode token
print("🔓 解码 Token...")
print(f"当前UTC时间: {datetime.utcnow()}")
payload = decode_jwt_token(token)

if payload:
    print("\n✅ Token 解码成功!")
    print(f"  - user_id: {payload.user_id}")
    print(f"  - org_id: {payload.org_id}")
    print(f"  - exp: {payload.exp}")
else:
    print("\n❌ Token 解码失败!")
    print("检查上面的日志输出")
