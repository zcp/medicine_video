#!/usr/bin/env python3
"""Truncate conftest.py to remove duplicate fixtures from line ~260 onwards"""
import os

conftest_path = os.path.join(os.path.dirname(__file__), 'backend', 'live_core_service', 'tests', 'conftest.py')
conftest_path = r'd:\live-streaming-saas-v2-main\backend\live_core_service\tests\conftest.py'

with open(conftest_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "break" after test_user (this is the last unique fixture)
# Then find the next blank line followed by the duplicate section
cut_line = None
for i, line in enumerate(lines):
    # After the test_user fixture's break, look for the duplicate section marker
    if i > 255 and line.strip() == 'break':
        # This should be the break inside test_user
        # The next few lines should be blank + duplicate content
        cut_line = i + 1  # cut after this line
        # Verify: next non-blank line should be duplicate fixture
        for j in range(i+1, min(i+10, len(lines))):
            if lines[j].strip().startswith('@pytest.fixture') or lines[j].strip().startswith('def mock'):
                print(f"Found duplicate at line {j+1}: {lines[j].strip()[:60]}")
                break
        break

if cut_line:
    new_content = ''.join(lines[:cut_line]) + '\n'
    with open(conftest_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Truncated at line {cut_line}. Kept {cut_line} lines, removed {len(lines) - cut_line} lines.")
else:
    print("Could not find cut point!")
