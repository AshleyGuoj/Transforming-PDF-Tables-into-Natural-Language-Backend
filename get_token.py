#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
from app.security.auth_stub import get_dev_admin_token
print(get_dev_admin_token())
