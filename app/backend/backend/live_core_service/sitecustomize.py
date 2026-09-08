# sitecustomize.py — Python 启动时自动执行
# 确保项目根目录在 sys.path 中，解决 pytest 7.4.3 conftest 发现时的路径问题
import sys, os

_project_root = '/app'
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 为 pytest conftest 发现机制创建虚拟 app.tests 包
# pytest 加载 /app/tests/conftest.py 时可能尝试 import app.tests
try:
    import types
    if 'app.tests' not in sys.modules:
        _app_tests = types.ModuleType('app.tests')
        _app_tests.__path__ = [os.path.join(_project_root, 'tests')]
        sys.modules['app.tests'] = _app_tests
except Exception:
    pass
