#!/usr/bin/env python3
"""运行单个失败测试以查看详细错误"""
import sys, os, types
sys.path.insert(0, '/app')
os.chdir('/app')

import app.database
import app.models.live_core
import app.models.live_features
if 'app.tests' not in sys.modules:
    app_tests = types.ModuleType('app.tests')
    app_tests.__path__ = ['/app/tests']
    sys.modules['app.tests'] = app_tests

import pytest
sys.exit(pytest.main([
    'tests/integration/test_api_live_features_public.py::test_public_list_tabs_regular_other_public_room',
    '-v', '--tb=long'
]))
