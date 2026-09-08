import sys, os

# 模拟 conftest.py 的行为
sys.path.insert(0, '/app')
print('sys.path[0]:', sys.path[0])

conftest_file = '/app/tests/conftest.py'
appended = os.path.dirname(os.path.dirname(os.path.abspath(conftest_file)))
print('conftest appends:', appended)

sys.path.append(appended)
print('After append, can find /app/app?:', os.path.exists('/app/app/database.py'))

try:
    from app.database import Base
    print('app.database import: OK')
except Exception as e:
    print('app.database import: FAILED -', e)

# 检查 pytest 实际运行时的路径
print('\nsys.path:', sys.path)
