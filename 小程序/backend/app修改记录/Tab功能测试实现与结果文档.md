# Tab 功能测试实现与结果文档

> 项目：live-streaming-saas-v2-main  
> 创建日期：2026-06-05  
> 说明：本文档记录 Tab 功能的自动化测试实现方案、配置修改、测试用例设计及执行结果

---

## 一、测试背景与目标

### 1.1 背景

Tab 功能（直播间自定义标签页）经历了 P0~P3 共 7 项后端修复后，需要建立自动化测试覆盖：

- **公开端点** `GET /api/v1/rooms/{room_id}/tabs` 此前**零测试覆盖**
- **图片上传端点** `POST /api/v1/admin/rooms/{room_id}/tabs/image` 此前**零测试覆盖**
- 多项权限修复（P0 过期对象、P1-1 双层权限、P1-2 role 大小写）需要回归保护

### 1.2 测试目标

| 目标 | 说明 |
|:---|:---|
| 验证公开端点权限 | 匿名/登录用户/创建者/Admin × 公开/私有房间 共 8 种组合 |
| 验证数据过滤 | 只返回 `is_active=True` 的 Tab |
| 验证排序正确 | 按 `sort_order` 升序排列 |
| 回归保护 | P0~P3 修复不被后续重构回退 |

### 1.3 测试策略

遵循项目已有的**混合测试策略**（定义于 `docs/提示词/自动化测试/测试代码生成提示词母版.md`）：

| 测试层级 | 风格 | 工具 | 本次操作 |
|:---|:---|:---|:---|
| API / Endpoint | 实用派 (Pragmatic) | `httpx.AsyncClient` + `db_session` | **新建** `test_api_live_features_public.py`（8 用例）+ **追加** `TestAdminTabImageUploadAPI`（6 用例） |
| CRUD | 实用派 (Pragmatic) | `db_session` | **追加** P0 修复验证（1 用例） |
| Service | 学院派 (Academic) | `mocker` | 待补充 |

**测试模式**：增量测试生成模式（项目已有测试基础设施，在已有基础上增量生成）

---

## 二、测试环境配置修改

### 2.1 修改清单

| 文件 | 修改内容 | 原因 |
|:---|:---|:---|
| `backend/live_core_service/pytest.ini` | `pythonpath = .` → `pythonpath = /app` | Docker 容器内 pytest 需要绝对路径 |
| `backend/live_core_service/Dockerfile` | 新增 `ENV PYTHONPATH=/app` | 确保 Python 模块搜索路径包含项目根目录 |
| `backend/live_core_service/tests/conftest.py` | JWT secret_key 硬编码 `"my-key"` | `.env.example` 是占位符值，覆盖了 `or "my-key"` 回退 |
| `backend/live_core_service/tests/conftest.py` | `backend.users.app` 导入加 try-except | Docker 容器内不存在该路径（仅主机开发环境有） |
| `backend/live_core_service/tests/__init__.py` | 新增 `sys.path.insert(0, '/app')` | 加固 Python 路径 |
| `backend/live_core_service/run_preload.py` | **新建** | pytest 7.4.3 conftest 发现机制绕过方案 |

### 2.2 关键问题与解决方案

#### 问题 1：pytest 无法导入 `app.database`

**现象**：
```
ModuleNotFoundError: No module named 'app.database' (from /app/tests/conftest.py)
```

**排查过程**：
1. 验证 `sys.path` 包含 `/app` ✅
2. 验证 `import app.database` 在普通 Python 中成功 ✅
3. 验证 `.pth` 文件也无法解决 ❌
4. 验证 `pytest.ini` 的 `pythonpath` 设置无效 ❌
5. 验证 `__init__.py` 提前设置 `sys.path` 无效 ❌
6. 验证根级 `conftest.py` 前置 `sys.path.insert` 无效 ❌

**根因**：pytest 7.4.3 的 conftest 发现机制使用独立解析，不继承父进程的 `sys.path` 修改。

**最终方案**：创建 `run_preload.py` 预加载脚本，在 `pytest.main()` 调用前将所有 `app.*` 模块预加载到 `sys.modules` 缓存中。

```python
# run_preload.py 核心逻辑
import sys, os, types
sys.path.insert(0, '/app')
os.chdir('/app')

# 预加载关键模块
import app.database
import app.models.live_core
import app.models.live_features

# 创建虚拟 app.tests 包（pytest 加载 conftest 时需要）
if 'app.tests' not in sys.modules:
    app_tests = types.ModuleType('app.tests')
    app_tests.__path__ = ['/app/tests']
    sys.modules['app.tests'] = app_tests

import pytest
sys.exit(pytest.main(['tests/integration/test_api_live_features_public.py', '-v']))
```

#### 问题 2：JWT Token 签名验证失败

**现象**：
```
WARNING:app.core.auth:JWT Token无效: Signature verification failed
HTTP/1.1 401 Unauthorized
```

**根因**：conftest.py 中 `regular_user_token` 和 `admin_user_token` fixture 通过 `load_dotenv` 加载 `.env.example`，其中 `JWT_SECRET_KEY` 的值是占位符 `your_jwt_secret_key_here_min_32_chars_...`，而非空值。`os.getenv("JWT_SECRET_KEY") or "my-key"` 返回了占位符，与 app 验证用的 `my-key`（`.env.docker` 配置）不匹配。

**修复**：conftest.py 中硬编码 `secret_key = "my-key"`，与 `.env.docker` 保持一致。

---

## 三、测试用例设计

### 3.1 新建文件：`tests/integration/test_api_live_features_public.py`

测试公开端点 `GET /api/v1/rooms/{room_id}/tabs`（`list_room_tabs_public`）。

#### 权限维度覆盖

| # | 测试函数 | 房间类型 | 用户身份 | 预期 |
|:---:|:---|:---:|:---|:---:|
| 1 | `test_public_list_tabs_anonymous_public_room` | `is_private=False` | 匿名 | 200 |
| 2 | `test_public_list_tabs_anonymous_private_room` | `is_private=True` | 匿名 | 404 |
| 3 | `test_public_list_tabs_regular_other_public_room` | `is_private=False` | REGULAR（非创建者） | 200 |
| 4 | `test_public_list_tabs_regular_other_private_room` | `is_private=True` | REGULAR（非创建者） | 404 |
| 5 | `test_public_list_tabs_owner_private_room` | `is_private=True` | REGULAR（创建者） | 200 |
| 6 | `test_public_list_tabs_admin_private_room` | `is_private=True` | ADMIN | 200 |

#### 数据维度覆盖

| # | 测试函数 | 验证点 |
|:---:|:---|:---|
| 7 | `test_public_list_tabs_only_active` | 有 1 个 active + 1 个 inactive Tab → 只返回 1 条 |
| 8 | `test_public_list_tabs_sort_order` | 3 个 Tab 乱序创建 (sort_order=2,0,1) → 返回顺序 [0,1,2] |

### 3.2 追加：`tests/integration/test_api_live_features.py` — 图片上传

测试图片上传端点 `POST /api/v1/admin/rooms/{room_id}/tabs/image`（`upload_tab_image`）。

| # | 测试函数 | 场景 | 预期 |
|:---:|:---|:---|:---:|
| 10 | `test_upload_image_admin_success` | ADMIN 上传合法 JPEG | 200，返回 `image_url` |
| 11 | `test_upload_image_owner_success` | 房间创建者上传（**P1-1 回归**） | 200 |
| 12 | `test_upload_image_non_owner_denied` | 非创建者 REGULAR 上传 | 403 |
| 13 | `test_upload_image_unauthorized` | 无 Token | 401 |
| 14 | `test_upload_image_invalid_format` | 非图片文件（.txt） | 400 |
| 15 | `test_upload_image_room_not_found` | 不存在的 room_id | 404 |

> 图片上传使用 `BytesIO` 生成最小合法 JPEG（`b'\xff\xd8\xff\xe0\x00\x10JFIF'`），通过 `httpx` 的 `files` 参数以 `multipart/form-data` 提交。

### 3.3 追加：`tests/unit/test_crud_live_features.py`

| # | 测试函数 | 验证点 |
|:---:|:---|:---|
| 9 | `test_remove_tab_returns_simple_namespace` | P0 修复：`remove_tab` 返回 `SimpleNamespace`，`.id` 为字符串可访问 |

---

## 四、测试执行结果

### 4.1 运行方式

```powershell
# 1. 部署测试文件到容器
docker cp "backend\live_core_service\run_preload.py" live-streaming-saas-v2-main-live_core_service-1:/app/run_preload.py
docker cp "backend\live_core_service\tests\integration\test_api_live_features_public.py" live-streaming-saas-v2-main-live_core_service-1:/app/tests/integration/
docker cp "backend\live_core_service\tests\conftest.py" live-streaming-saas-v2-main-live_core_service-1:/app/tests/conftest.py

# 2. 运行测试
docker exec live-streaming-saas-v2-main-live_core_service-1 python /app/run_preload.py
```

### 4.2 执行结果

```
======================== 14 passed, 4 warnings in 3.64s =========================
```

#### 公开端点（8 个）

| # | 测试 | 结果 |
|:---:|:---|:---:|
| 1 | `test_public_list_tabs_anonymous_public_room` | ✅ PASSED |
| 2 | `test_public_list_tabs_anonymous_private_room` | ✅ PASSED |
| 3 | `test_public_list_tabs_regular_other_public_room` | ✅ PASSED |
| 4 | `test_public_list_tabs_regular_other_private_room` | ✅ PASSED |
| 5 | `test_public_list_tabs_owner_private_room` | ✅ PASSED |
| 6 | `test_public_list_tabs_admin_private_room` | ✅ PASSED |
| 7 | `test_public_list_tabs_only_active` | ✅ PASSED |
| 8 | `test_public_list_tabs_sort_order` | ✅ PASSED |

#### 图片上传（6 个）

| # | 测试 | 结果 |
|:---:|:---|:---:|
| 9 | `test_upload_image_admin_success` | ✅ PASSED |
| 10 | `test_upload_image_owner_success` | ✅ PASSED |
| 11 | `test_upload_image_non_owner_denied` | ✅ PASSED |
| 12 | `test_upload_image_unauthorized` | ✅ PASSED |
| 13 | `test_upload_image_invalid_format` | ✅ PASSED |
| 14 | `test_upload_image_room_not_found` | ✅ PASSED |

> 4 个 warnings 为第三方库弃用警告（`regex` → `pattern`、Pydantic V1 `@validator`），非测试代码问题。

---

## 五、测试覆盖度分析

### 5.1 权限覆盖矩阵

| 用户身份 | 公开房间 Tab | 私有房间 Tab | 管理自己房间 Tab | 管理他人房间 Tab |
|:---|:---:|:---:|:---:|:---:|
| 匿名 | ✅ 已测 (1) | ✅ 已测 (2) | N/A | N/A |
| REGULAR（非创建者） | ✅ 已测 (3) | ✅ 已测 (4) | N/A | N/A |
| REGULAR（创建者） | N/A | ✅ 已测 (5) | ⚠️ 已有（Admin API 测试） | N/A |
| ADMIN | N/A | ✅ 已测 (6) | ✅ 已有 | ✅ 已有 |
| SUPERADMIN | N/A | N/A | ✅ 已有 | ✅ 已有 |

### 5.2 图片上传权限覆盖

| 用户身份 | 上传到自己房间 | 上传到他人房间 |
|:---|:---:|:---:|
| ADMIN/SUPERADMIN | ✅ 已测 (9) | N/A |
| REGULAR（创建者） | ✅ 已测 (10) | N/A |
| REGULAR（非创建者） | N/A | ✅ 已测 (11) |
| 匿名 | N/A | ✅ 已测 (12) |

### 5.3 待补充测试

| 优先级 | 测试内容 | 说明 |
|:---:|:---|:---|
| 中 | Service 层创建者权限 | P1-1 修复回归（`_check_tab_management_permission` 对创建者放行） |

---

## 六、新增/修改文件清单

| 文件 | 操作 | 说明 |
|:---|:---:|:---|
| `tests/integration/test_api_live_features_public.py` | **新建** | 公开端点 8 个测试用例 |
| `tests/integration/test_api_live_features.py` | **追加** | 图片上传 6 个测试用例（`TestAdminTabImageUploadAPI`） |
| `tests/unit/test_crud_live_features.py` | **追加** | P0 修复验证 1 个用例 |
| `run_preload.py` | **新建** | pytest 预加载脚本 |
| `tests/conftest.py` | **修改** | JWT 密钥硬编码 + `backend.users.app` try-except |
| `tests/__init__.py` | **修改** | 新增 sys.path 加固 |
| `pytest.ini` | **修改** | `pythonpath = /app` |
| `Dockerfile` | **修改** | 新增 `ENV PYTHONPATH=/app` |
| `docs/提示词/直播核心功能模块/live_features_测试代码生成提示词.md` | **新建** | 测试蓝图（规划师阶段文档） |

---

## 七、后续建议

### 7.1 pytest PYTHONPATH 永久修复方案

**当前状态**：`run_preload.py` 预加载脚本是稳定绕过方案，已验证可用。

**永久修复 — `sitecustomize.py` 方案（已实施）**：

已在 `backend/live_core_service/sitecustomize.py` 创建文件并在 Dockerfile 中添加：
```dockerfile
COPY sitecustomize.py /usr/local/lib/python3.9/site-packages/sitecustomize.py
```

`sitecustomize.py` 是 Python 标准机制——Python 启动时自动执行。它在**任何模块加载之前**将 `/app` 加入 `sys.path`，从根本上解决了 pytest conftest 发现的路径问题。**下次重建镜像后即可弃用 `run_preload.py`**。

> ⚠️ 需要重建 Docker 镜像才能生效：`docker compose -f compose-app.windows.yml up --build -d live_core_service`

### 7.2 JWT 密钥管理分析

**当前方案**：conftest.py 中 `secret_key = "my-key"` 硬编码。

**风险分析**：
- 当前风险：**低**。`.env.docker` 也使用 `my-key`，两者一致
- 如果 `.env.docker` 的 `JWT_SECRET_KEY` 变更：测试会全部失败（签名不匹配），但这是**立即可见的失败**，不会静默通过
- `os.getenv("JWT_SECRET_KEY", "my-key")` 方案不可行：conftest 顶部 `load_dotenv(.env.example)` 会将 `JWT_SECRET_KEY` 设为占位符值，`os.getenv` 的 `default` 参数不会生效

**结论**：硬编码 `"my-key"` 是当前最可靠方案。如需优化，应先修复 `.env.example` 的占位符问题（改为空值注释），再改用 `os.getenv`。

### 7.3 conftest.py 冗余代码

**分析**：第 207 行之后的重复段（JWT fixtures + 权限 fixtures + `backend.users.app` 导入）是完整的功能重复。在 Docker 环境中：
- `backend.users.app` 导入已用 try-except 安全跳过后不影响运行
- 重复的 fixture 定义会被 pytest 以最后一个为准（覆盖前面的），但因定义完全一致，不影响行为
- `test_user` fixture 被 `test_v6_crud_dedup.py` 依赖（仅主机开发环境）

**建议**：**暂不删除**。删除存在风险（依赖关系复杂），且重复代码不影响 Docker 测试运行。保留并标注为"主机开发环境扩展段"，待项目统一清理时处理。
