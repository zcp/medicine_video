"""修复容器内 conftest.py 的路径问题"""
import sys
sys.path.insert(0, '/app')
# 直接调用 pytest，在调用前确保 /app 在 sys.path 中
import pytest
import os
os.chdir('/app')
sys.exit(pytest.main([
    'tests/integration/test_api_live_features_public.py',
    '-v', '--tb=short'
]))
