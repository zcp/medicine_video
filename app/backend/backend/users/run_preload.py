"""
Pytest 预加载脚本（用于 Docker 容器内测试）

pytest 7.4.3 的 conftest 发现机制使用独立解析器，不继承父进程的 sys.path 修改。
本脚本在 pytest.main() 调用前将关键模块预加载到 sys.modules 缓存中，
使 conftest.py 导入 app.* 模块时直接从缓存获取，绕开路径查找问题。

用法：
    docker exec <container> python /app/run_preload.py [pytest_args...]

参考：
    Tab 功能测试文档（app修改记录/Tab功能测试实现与结果文档.md）第 2.2 节
"""
import sys
import os
import types

# 1. 确保 /app 在路径中
if '/app' not in sys.path:
    sys.path.insert(0, '/app')
os.chdir('/app')

# 2. 预加载 app.* 模块（按依赖顺序）
import app  # noqa
import app.database  # conftest.py:39 直接依赖
import app.exceptions  # conftest 间接依赖
import app.models  # noqa
import app.models.users
import app.core  # noqa
import app.core.password
import app.core.redis_client
import app.core.responses
import app.services  # noqa
import app.services.auth_service
import app.services.sms_provider
import app.services.carrier_auth_provider
import app.schemas  # noqa
import app.schemas.auth
import app.schemas.users
import app.crud  # noqa
import app.crud.crud_user

# 3. 创建虚拟 app.tests 包（pytest 加载 conftest 时需要）
if 'app.tests' not in sys.modules:
    app_tests = types.ModuleType('app.tests')
    app_tests.__path__ = ['/app/tests']
    sys.modules['app.tests'] = app_tests

# 4. 确保运行时环境为 development（避免模块级 settings = Settings() 触发生产配置校验）
#    Settings.__init__() 在实例化时会重新读取 os.getenv()，因此 monkeypatch 在
#    测试函数内设置的环境变量能被正确读取，无需清除 sys.modules 缓存。
#    注：此前通过 del sys.modules['app.core.config'] 清除缓存的策略会导致
#    测试收集阶段重新执行模块级 settings = Settings()，若 Docker 环境变量中
#    含有生产相关配置会引发 ValueError 阻断整个测试套件。
os.environ.setdefault("ENVIRONMENT", "development")

# 5. 启动 pytest
import pytest
sys.exit(pytest.main(sys.argv[1:] if len(sys.argv) > 1 else [
    'tests/test_api_auth.py::TestSendVerificationCode::test_send_verification_code_sms_provider_failure',
    'tests/test_auth_service.py::TestSettingsProductionValidation',
    '-v', '--tb=short',
]))
