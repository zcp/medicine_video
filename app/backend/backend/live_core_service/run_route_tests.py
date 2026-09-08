"""预加载关键模块后运行 pytest —— 绕过 pytest 7.4.3 conftest 发现机制的 PYTHONPATH 问题"""
import sys, os, types

sys.path.insert(0, '/app')
os.chdir('/app')

# 预加载关键模块到 sys.modules 缓存
import app.database
import app.models.live_core
import app.models.live_features

# 创建虚拟 app.tests 包（pytest 加载 conftest 时需要）
if 'app.tests' not in sys.modules:
    app_tests = types.ModuleType('app.tests')
    app_tests.__path__ = ['/app/tests']
    sys.modules['app.tests'] = app_tests

import pytest
sys.exit(pytest.main([
    'tests/integration/test_api_homepage_search.py',
    'tests/integration/test_api_content_management.py',
    'tests/integration/test_api_liveroom_official_accounts.py',
    'tests/integration/test_internal_callbacks_local.py',
    'tests/integration/test_internal_callbacks_remote.py',
    'tests/integration/test_internal_callbacks_sync.py',
    '-v', '--tb=short',
]))
