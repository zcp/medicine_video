# 测试包初始化：确保项目根目录在 sys.path 中
# pytest 加载 tests 包时优先执行此文件，此时设置路径可让后续 conftest.py 正常导入
import sys, os
_sys_path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _sys_path_root not in sys.path:
    sys.path.insert(0, _sys_path_root)
# Docker 兼容：也尝试 /app
if '/app' not in sys.path:
    sys.path.insert(0, '/app')
