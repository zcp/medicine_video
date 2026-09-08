#!/usr/bin/env python3
"""Tab 测试运行脚本 - 修复路径后调用 pytest"""
import sys, os
sys.path.insert(0, '/app')
os.chdir('/app')

import pytest
exit_code = pytest.main([
    'tests/integration/test_api_live_features_public.py',
    '-v', '--tb=short', '--no-header',
    '-p', 'no:cacheprovider',
    '--rootdir=/app'
])
sys.exit(exit_code)
