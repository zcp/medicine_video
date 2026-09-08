#!/usr/bin/env python3
"""预加载关键模块到 sys.modules，再运行 pytest"""
import sys, os
sys.path.insert(0, '/app')
os.chdir('/app')

# 关键：在 pytest 启动前预加载所有需要的模块到 sys.modules 缓存
import app.database
import app.models.live_core
import app.models.live_features
# pytest 尝试 import app.tests.conftest 时，需要 app.tests 存在
# 创建一个虚拟的 app.tests 包
import types
if 'app.tests' not in sys.modules:
    app_tests = types.ModuleType('app.tests')
    app_tests.__path__ = ['/app/tests']
    sys.modules['app.tests'] = app_tests
print("Preloaded: app.database, app.models.live_core, app.models.live_features, app.tests")

import pytest
sys.exit(pytest.main([
    'tests/integration/test_api_live_features_public.py',
    'tests/integration/test_api_live_features.py::TestAdminTabImageUploadAPI',
    '-v', '--tb=short'
]))
