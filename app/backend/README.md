# LiveCore 后端服务（app/backend）

本目录为直播 SaaS 平台后端服务的快照仓库（完整历史保留于原仓库 `app_wechat_backend`）。包含三个 FastAPI 服务及完整部署配置：

| 目录 | 服务 | 端口（宿主） |
|---|---|---|
| `backend/live_core_service/` | 直播核心服务（房间/场次/专家/搜索/品牌） | 8010 -> 8000 |
| `backend/users/` | 用户与会员服务 | 8002 |
| `backend/media_download_service/` | 媒体下载服务（微赞爬取） | 8001 |
| `frontend/` | Vue Web 管理端（与 `app/frontend` 的 uni-app 移动端是不同项目） | - |
| `nginx/` `srs/` | 反向代理与流媒体服务器配置 | - |

## 一、Docker Compose 快速启动

> 前置：仅需 Docker（服务端代码全部容器化，Python 3.9 已在镜像内）。

```bash
# 1) 创建环境变量文件（模板已入库，含全部 48 个变量及说明）
cp .env.docker.example .env.docker
#    然后编辑 .env.docker，填写所有 <必填> / <CHANGE_ME> / <你的域名> 项
#    （.env.docker 已被 .gitignore 排除，不会提交）

# 2) 启动数据库（postgres:15 + redis:7，init-db.sh 自动创建三个库：
#    live_core_test / media_download_test / users_service_test）
docker compose -f compose-db.yml up -d

# 3) 启动后端服务（entrypoint 自动执行建表迁移/种子；host 8010 -> 容器 8000）
docker compose -f compose-app.yml up -d live_core_service
#    也可一并启动 user_service / media_download_service / celery_worker / celery_beat
```

健康检查：`curl http://localhost:8010/api/v1/health`

## 二、运行测试

### 方式 A：容器内跑（推荐，与生产布局一致）

```bash
docker compose -f compose-app.yml up -d live_core_service
docker compose -f compose-app.yml exec live_core_service pytest -q
# 指定目录/用例：
docker compose -f compose-app.yml exec live_core_service pytest tests/unit -q
```

> 容器内测试口令由 `.env.docker` 的 `POSTGRES_PASSWORD` 自动注入，无需额外配置。

### 方式 B：本机 venv 直跑

```bash
cd backend/live_core_service
python -m venv venv && venv\Scripts\activate   # Windows；Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
# 环境变量（口令须与自建数据库一致，仓库不含任何真实口令）：
export POSTGRES_SERVER=localhost POSTGRES_PASSWORD=你的数据库口令   # Windows: set ...
pytest -q
```

> 注意：`pytest.ini` 按容器布局 `pythonpath=/app`，本机跑请从 `backend/live_core_service` 目录执行
> 并保证该目录在 PYTHONPATH（或直接 `python -m pytest`）。
> `tests/conftest.py` 中数据库口令默认值为 `CHANGE_ME`（脱敏占位），本机跑必须显式设置
> `POSTGRES_PASSWORD` 等变量，否则连接失败属预期行为。

## 三、常见问题

| 问题 | 说明 |
|---|---|
| `env file .env.docker not found` | 忘记执行 `cp .env.docker.example .env.docker` |
| 测试连不上数据库 | 本机跑需 `export POSTGRES_*`；容器内跑需先 `compose-db.yml up` |
| `pythonpath=/app` 导入失败 | 容器外需自行确保 sys.path 包含 `backend/live_core_service` |
| 一键登录（univerify） | 云函数在 `app/frontend/uniCloud-aliyun/`，需 uniCloud 控制台配置 `UNIVERIFY_PSK` 环境变量 |
| 内容安全/短信等外部依赖 | `POLITICAL_TEXT_API_KEY`、`CARRIER_AUTH_PROVIDER` 等需对接外部服务，未配置时相关功能降级/报错属预期 |

## 四、前端（app/frontend）测试快速参考

```bash
cd ../frontend          # 即仓库根 app/frontend
pnpm install
pnpm test:run           # vitest 单测（无需后端）
pnpm dev:h5             # H5 联调需先自行配置 .env.development（模板见 env.example）
```
