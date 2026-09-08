# Docker Compose 结构说明

## 标准入口（请用这个）

| 场景 | Compose 文件组合 |
|------|------------------|
| **Windows 本地开发** | `docker-compose.yml` + `docker-compose.windows.yml` |
| **Linux / 远程服务器** | `docker-compose.yml` |
| **生产部署** | `docker-compose.yml` + `docker-compose.prod.yml` |

### Windows 开发 — 推荐命令

```batch
start-dev.bat

:: 或等价于：
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d --build

:: 快捷封装（任意子命令）：
dc-dev.bat ps
dc-dev.bat logs -f live_core_service
dc-dev.bat exec live_core_service pytest tests/ -v
```

> `docker-compose.windows.yml` **不能单独使用**，它只是覆盖层（端口、路径、nginx 配置）。

## 目录结构

```
docker/
  compose/
    base.yml          # 项目名、networks、volumes
    infra.yml         # postgres + redis（healthcheck）
    apps.yml          # live_core / users / media_download / celery
    edge.yml          # srs + nginx（Linux/服务器默认）
    overrides/
      windows.yml     # Windows 端口与路径覆盖
      prod.yml        # 生产：后端不映射宿主机端口
docker-compose.yml           # 主栈（必用）
docker-compose.windows.yml   # Windows 覆盖（与上叠加）
docker-compose.prod.yml      # 生产覆盖（与上叠加）
```

## 常用命令

### Linux / 远程服务器

```bash
docker compose up -d --build
```

### 生产部署

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 仅数据库 + Redis

```bash
docker compose -f compose-db.yml up -d
```

### 容器内跑测试

```bash
docker compose -f docker-compose.yml -f docker-compose.windows.yml exec live_core_service pytest tests/integration/test_api_live_features.py -v
```

> **说明（Windows / 通用）**：`live_core_service` 已挂载 `backend` → `/backend`，供 `tests/conftest.py` 导入 `backend.users`。  
> 请勿在 `live_core_service` 根目录放置空的 `__init__.py`，否则在容器内会与包名 `app` 冲突导致 pytest 无法导入。  
> 集成测试 JWT 须与 `settings.JWT_SECRET_KEY`（通常来自 `.env.docker` 的 `my-key`）一致。

## 端口对照（Windows）

| 服务 | 端口 |
|------|------|
| live_core_service | 8000 |
| media_download | 8001 |
| user_service | 8002 |
| postgres | 5433 |
| redis | 6380 |
| nginx HTTP | 8080 |

## 已废弃（勿再写进新文档）

`compose-app.yml`、`compose-app.windows.yml` 仅为旧脚本兼容保留，新开发统一用 **`docker-compose.yml` + `docker-compose.windows.yml`**。

## 环境变量

根目录 `.env.docker`，通过各服务 `env_file` 注入容器。  
`docker/compose/apps.yml` 只覆盖编排相关项（容器内主机名、端口、卷），不在 compose 里重复写业务配置。
