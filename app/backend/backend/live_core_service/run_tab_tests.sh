#!/bin/sh
cd /app
export PYTHONPATH=/app
python -m pytest tests/integration/test_api_live_features_public.py -v --tb=line 2>&1
