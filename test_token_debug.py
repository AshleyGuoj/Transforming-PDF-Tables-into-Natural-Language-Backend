#!/usr/bin/env python3
"""Debug JWT token decoding"""
import sys
sys.path.insert(0, 'backend')
from app.security.auth_stub import get_dev_admin_token
from app.core.config import get_settings
from jose import jwt, JWTError

settings = get_settings()

# Generate token
token = get_dev_admin_token()
print(f"Token: {token}\n")

# Try to decode without validation first
try:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    print("✅ JWT 解码成功 (raw):")
    for key, value in payload.items():
        print(f"  - {key}: {value} (type: {type(value).__name__})")

except JWTError as e:
    print(f"❌ JWT 解码失败: {e}")
