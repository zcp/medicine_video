# Windows Docker 开发环境设置指南

## 📋 概述

本指南帮助你在 Windows 上使用 Docker 进行本地开发。

## ✅ 标准 Compose 入口

**Windows 本地开发固定使用两个文件叠加：**

```batch
docker compose -f docker-compose.yml -f docker-compose.windows.yml <command>
```

| 文件 | 作用 |
|------|------|
| `docker-compose.yml` | 主栈：postgres、redis、后端、nginx、srs |
| `docker-compose.windows.yml` | 覆盖层：5433/6380/8080 端口、本地路径、`nginx.windows.conf` |

> `docker-compose.windows.yml` **不能单独使用**。

快捷方式：`start-dev.bat`、`dc-dev.bat`（见下文）。

---

## 🚀 快速开始

### 1. 安装 Docker Desktop

1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 安装并启动，启用 **WSL2 后端**

### 2. 启动开发环境

```batch
start-dev.bat

:: 或手动：
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d --build

:: 或使用封装脚本（任意子命令）：
dc-dev.bat up -d
dc-dev.bat ps
```

### 3. 验证服务

- **Live Core API**: http://localhost:8000
- **Media Download API**: http://localhost:8001
- **User Service API**: http://localhost:8002
- **Nginx (代理)**: http://localhost:8080

### 4. 停止

```batch
stop-dev.bat

:: 或：
docker compose -f docker-compose.yml -f docker-compose.windows.yml down
```

---

## 🔧 配置说明

| 配置项 | Linux/生产 | Windows 开发 |
|--------|-----------|-------------|
| **Compose** | `docker-compose.yml` [+ `docker-compose.prod.yml`] | `docker-compose.yml` + `docker-compose.windows.yml` |
| **端口** | 80, 443, 5432, 6379 | 8080, 8443, 5433, 6380 |
| **媒体目录** | 命名卷 / 服务器路径 | `./data/live_core_media` |
| **Nginx** | `nginx.conf`（含 SSL） | `nginx.windows.conf`（纯 HTTP） |

---

## 📝 常用命令

以下均使用标准双文件入口；也可把前缀换成 `dc-dev.bat`：

```batch
set DC=-f docker-compose.yml -f docker-compose.windows.yml

docker compose %DC% up -d
docker compose %DC% down
docker compose %DC% ps
docker compose %DC% logs -f live_core_service
docker compose %DC% exec live_core_service bash
docker compose %DC% exec postgres psql -U postgres -d live_core_test
docker compose %DC% up -d --build live_core_service
docker compose %DC% exec live_core_service pytest tests/ -v
```

重建：`rebuild.bat`（已内置上述 compose 组合）。

---

## 🔄 部署到 Linux 生产

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## ⚠️ 常见问题

1. **端口占用**：改 `docker/compose/overrides/windows.yml` 中的端口映射
2. **数据库连不上**：容器内用 `postgres:5432`；宿主机工具用 `localhost:5433`
3. **nginx 起不来**：确认使用的是 `docker-compose.windows.yml`（不要用 prod 覆盖）

---

## 📚 更多说明

详见 [`docker/README.md`](docker/README.md)

**开始使用**：`start-dev.bat`
