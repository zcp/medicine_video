#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证 .env.example 文件编码"""

import sys

# 设置标准输出为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    with open('.env.example', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("=" * 60)
    print("✅ .env.example 文件验证结果")
    print("=" * 60)
    print(f"文件行数: {len(lines)}")
    print(f"文件大小: {len(''.join(lines))} 字符")
    print("\n前10行内容预览:")
    print("-" * 60)
    for i, line in enumerate(lines[:10], 1):
        print(f"{i:2d}: {line.rstrip()}")
    print("-" * 60)
    
    # 检查关键内容
    content = ''.join(lines)
    checks = [
        ("包含 'LiveCore Service'", "LiveCore Service" in content),
        ("包含 '环境变量配置模板'", "环境变量配置模板" in content),
        ("包含 'ENVIRONMENT'", "ENVIRONMENT" in content),
        ("包含 'POSTGRES_PASSWORD'", "POSTGRES_PASSWORD" in content),
        ("包含 'JWT_SECRET_KEY'", "JWT_SECRET_KEY" in content),
        ("包含 'CORS_ORIGINS'", "CORS_ORIGINS" in content),
    ]
    
    print("\n内容检查:")
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 文件内容验证通过！编码正确（UTF-8）")
    else:
        print("❌ 文件内容验证失败，请检查文件")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)

