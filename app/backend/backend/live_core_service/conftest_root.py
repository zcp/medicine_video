import sys; sys.path.insert(0, '/app')
"""
LiveCore Service - Root Conftest (方案 D)

This conftest.py is placed at the project root (/app) to ensure sys.path
includes /app BEFORE pytest discovers and loads tests/conftest.py.

The sys.path.insert on line 1 runs before the docstring, before any imports,
making /app available to all subsequent module loading.
"""

# 此文件仅用于修复 pytest conftest 发现的 PYTHONPATH 问题
# 实际的 fixtures 定义在 tests/conftest.py 中
