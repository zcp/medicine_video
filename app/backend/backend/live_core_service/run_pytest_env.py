#!/usr/bin/env python3
"""Set PYTHONPATH in os.environ then run pytest"""
import os, sys
os.environ['PYTHONPATH'] = '/app'
os.chdir('/app')
sys.path.insert(0, '/app')

import pytest
sys.exit(pytest.main([
    'tests/integration/test_api_live_features_public.py',
    '-v', '--tb=short'
]))
