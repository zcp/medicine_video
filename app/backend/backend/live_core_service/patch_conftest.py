#!/usr/bin/env python3
"""修补容器内的 conftest.py 以添加 /app 到 sys.path 最前面"""
conftest_path = '/app/tests/conftest.py'

with open(conftest_path, 'r') as f:
    content = f.read()

# 在 docstring 之后、第一个 import 之前插入 sys.path.insert
patch_line = '\nimport sys; sys.path.insert(0, "/app")\n'
insert_point = content.find('\nimport os')
if insert_point > 0:
    content = content[:insert_point] + patch_line + content[insert_point:]
    with open(conftest_path, 'w') as f:
        f.write(content)
    print('conftest.py patched successfully')
else:
    print('Could not find insertion point')
