#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 .env 文件加载"""

from dotenv import load_dotenv
import os

# 测试加载 .env 文件
try:
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)
    print("Success: .env file loaded correctly")
    
    # 检查几个关键环境变量
    env_vars = ['ENVIRONMENT', 'POSTGRES_PASSWORD', 'JWT_SECRET_KEY', 'CORS_ORIGINS']
    print("\nEnvironment variables check:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏敏感信息
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                display_value = f"{'*' * min(len(value), 10)} (length: {len(value)})"
            else:
                display_value = value
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: (not set)")
    
    print("\nAll checks passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

