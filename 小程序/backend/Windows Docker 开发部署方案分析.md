# Windows Docker 开发部署方案分析

## 📋 执行摘要

**结论：✅ 强烈推荐在 Windows 上使用 Docker 进行本地开发测试**

这种方式可以：
- ✅ 实现与生产环境一致的部署环境
- ✅ 减少"在我机器上能跑"的问题
- ✅ 简化部署流程，本地测试通过即可直接部署到远程
- ✅ 隔离开发环境，不影响系统其他软件

---

## 🔍 可行性分析

### ✅ 项目已具备的条件

1. **完整的 Docker 配置**：
   - ✅ 所有服务都有 Dockerfile
   - ✅ 有 `compose-app.yml` 用于本地开发
   - ✅ 有 `docker-compose.prod.yml` 用于生产部署
   - ✅ 已有 Windows 批处理脚本（`rebuild.bat`）

2. **跨平台兼容的配置**：
   - ✅ 使用相对路径：`./data`, `./nginx`, `./logs`
   - ✅ 使用 Docker volumes 管理数据持久化
   - ✅ 使用环境变量配置（`.env.docker`）

### ⚠️ 需要适配的问题

1. **绝对路径问题**（在 `compose-app.yml` 中）：
   ```yaml
   # 这些路径在 Windows 上不存在，需要适配
   - /var/www/html/user-service:/var/www/html/user-service:ro
   - /var/www/html/media-download:/var/www/html/media-download:ro
   - /var/www/html/live-center:/var/www/html/live-center:ro
   - /var/www/mp.dayilive.com:/var/www/mp.dayilive.com:ro
   - /var/www/certbot:/var/www/certbot:ro
   ```

2. **端口冲突**：
   - Windows 上可能已占用 80、443、5432、6379 等端口

3. **文件权限**：
   - Windows 和 Linux 文件权限机制不同（但 Docker Desktop 已处理）

---

## 💡 解决方案

### 方案一：创建 Windows 专用的 compose 文件（推荐）

创建 `compose-app.windows.yml`，专门用于 Windows 本地开发：

```yaml
services:
  live_core_service:
    build: ./backend/live_core_service
    restart: unless-stopped
    ports: ["8000:8000"]
    environment:
      POSTGRES_DB: "live_core_test"
      ROOM_MEDIA_ROOT_PATH: "/app/media"  # 使用绝对路径
    env_file: .env.docker
    volumes:
      # Windows 路径适配：使用相对路径或 Windows 路径格式
      - ./data/live_core_media:/app/media
    depends_on: []
    networks:
      - live-network

  # ... 其他服务配置保持不变 ...

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports: ["8080:80","8443:443"]  # 避免与 Windows 系统端口冲突
    volumes:
      # Windows 本地开发：使用相对路径或注释掉前端文件挂载
      # - ./frontend/user-service/dist:/var/www/html/user-service:ro
      # - ./frontend/media-download/dist:/var/www/html/media-download:ro
      # - ./frontend/live-center/dist:/var/www/html/live-center:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./data/srs:/var/www/srs:ro
      - ./data/live_core_media:/var/www/html/live-core-media:ro  # 媒体文件
      # Windows 开发环境不需要 SSL 证书
      # - /var/www/mp.dayilive.com:/var/www/mp.dayilive.com:ro
      # - /var/www/certbot:/var/www/certbot:ro
    depends_on: [srs]
    networks:
      - live-network

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    ports: ["5433:5432"]  # 避免与本地 PostgreSQL 冲突
    # ... 其他配置保持不变 ...

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports: ["6380:6379"]  # 避免与本地 Redis 冲突
    # ... 其他配置保持不变 ...
```

### 方案二：使用环境变量区分 Windows/Linux

在 `compose-app.yml` 中使用条件配置（需要 Docker Compose v2.0+）：

```yaml
services:
  nginx:
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data/srs:/var/www/srs:ro
      # 使用环境变量控制
      ${NGINX_VOLUMES:-}
```

然后创建 `.env.windows` 和 `.env.linux` 文件。

### 方案三：使用 Docker Compose profiles（推荐用于多环境）

```yaml
services:
  nginx:
    profiles: ["production"]  # 只在生产环境加载
    volumes:
      - /var/www/html/user-service:/var/www/html/user-service:ro
      # ...

  nginx-dev:
    profiles: ["development"]  # 开发环境配置
    volumes:
      - ./frontend/user-service/dist:/var/www/html/user-service:ro
      # ...
```

---

## 📊 优缺点对比

### ✅ 优点

1. **环境一致性**：
   - 本地和生产环境完全一致
   - 减少部署时的环境差异问题

2. **隔离性**：
   - 不污染 Windows 系统
   - 可以同时运行多个项目版本

3. **简化部署**：
   - 本地测试通过 = 生产环境可用
   - 减少配置错误

4. **团队协作**：
   - 新成员快速上手
   - 统一的开发环境

5. **依赖管理**：
   - 不需要在 Windows 上安装 PostgreSQL、Redis、Nginx 等
   - 所有依赖都在容器中

### ⚠️ 缺点

1. **资源消耗**：
   - Docker Desktop 需要较多内存（建议 8GB+）
   - 多个容器同时运行占用资源

2. **性能开销**：
   - Windows 上 Docker 有性能开销（WSL2 已优化）
   - 文件 I/O 可能比原生慢

3. **学习曲线**：
   - 需要了解 Docker 基本概念
   - 调试容器内问题需要额外技能

4. **路径适配**：
   - 需要处理 Windows/Linux 路径差异
   - 某些绝对路径需要适配

---

## 🚀 实施步骤

### 步骤 1：安装 Docker Desktop for Windows

1. 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. 确保启用 WSL2 后端（性能更好）
3. 分配足够资源（建议：CPU 4核，内存 8GB+）

### 步骤 2：创建 Windows 开发配置

创建 `compose-app.windows.yml`（见上面的方案一）

### 步骤 3：适配 nginx 配置

创建 `nginx/nginx.windows.conf`，修改端口和路径：

```nginx
server {
    listen 8080;  # 改为 8080，避免与 Windows 80 端口冲突
    server_name localhost;
    
    # ... 其他配置 ...
    
    location /media/ {
        alias /var/www/html/live-core-media/;
        # ... 其他配置 ...
    }
}
```

### 步骤 4：创建启动脚本

创建 `start-dev.bat`：

```batch
@echo off
echo === 启动 Windows 开发环境 ===

REM 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

REM 创建必要的目录
if not exist "data\live_core_media\rooms" mkdir "data\live_core_media\rooms"
if not exist "data\live_core_media\topics" mkdir "data\live_core_media\topics"
if not exist "data\srs" mkdir "data\srs"
if not exist "logs\srs" mkdir "logs\srs"

REM 启动服务
docker-compose -f compose-app.windows.yml up -d

echo.
echo ✅ 服务已启动
echo 📝 访问地址：
echo    - API: http://localhost:8000
echo    - Nginx: http://localhost:8080
echo.
echo 查看日志: docker-compose -f compose-app.windows.yml logs -f
pause
```

### 步骤 5：创建停止脚本

创建 `stop-dev.bat`：

```batch
@echo off
echo === 停止 Windows 开发环境 ===
docker-compose -f compose-app.windows.yml down
echo ✅ 服务已停止
pause
```

---

## 🔧 配置差异对比

| 配置项 | 生产环境 (Linux) | Windows 开发环境 |
|--------|-----------------|-----------------|
| **compose 文件** | `compose-app.yml` | `compose-app.windows.yml` |
| **Nginx 端口** | 80, 443 | 8080, 8443 |
| **PostgreSQL 端口** | 5432 | 5433 |
| **Redis 端口** | 6379 | 6380 |
| **前端文件路径** | `/var/www/html/...` | `./frontend/.../dist` 或注释 |
| **SSL 证书** | `/var/www/mp.dayilive.com` | 不需要（开发环境） |
| **媒体文件路径** | `/var/www/html/live-core-media` | `./data/live_core_media` |

---

## 📝 开发工作流

### 日常开发流程

1. **启动开发环境**：
   ```batch
   start-dev.bat
   ```

2. **修改代码**：
   - 在 Windows 上使用 IDE 编辑代码
   - 代码在项目目录中

3. **重建服务**（代码修改后）：
   ```batch
   rebuild.bat -c
   ```

4. **查看日志**：
   ```batch
   docker-compose -f compose-app.windows.yml logs -f live_core_service
   ```

5. **测试 API**：
   - 访问 `http://localhost:8000/api/v1/...`
   - 或通过 Nginx：`http://localhost:8080/api/core/...`

6. **停止环境**：
   ```batch
   stop-dev.bat
   ```

### 部署到生产环境

1. **本地测试通过后**：
   ```batch
   # 确保所有测试通过
   docker-compose -f compose-app.windows.yml logs live_core_service
   ```

2. **提交代码**：
   ```batch
   git add .
   git commit -m "功能开发完成"
   git push
   ```

3. **远程部署**：
   ```bash
   # 在远程服务器上
   git pull
   docker-compose -f compose-app.yml up -d --build
   ```

---

## ⚠️ 注意事项

### 1. 端口冲突

如果 Windows 上已安装：
- **PostgreSQL**：修改 compose 文件中的端口映射为 `5433:5432`
- **Redis**：修改为 `6380:6379`
- **Nginx/Apache**：修改为 `8080:80`

### 2. 文件路径

- ✅ **相对路径**：`./data`, `./nginx` - 跨平台兼容
- ⚠️ **绝对路径**：`/var/www/html/...` - 需要适配或注释

### 3. 文件权限

- Windows 上文件权限由 Docker Desktop 处理
- 如果遇到权限问题，检查 Docker Desktop 的文件共享设置

### 4. 性能优化

- 使用 WSL2 后端（Docker Desktop 设置）
- 将项目目录添加到 Docker Desktop 的文件共享中
- 使用 `.dockerignore` 减少构建上下文

### 5. 数据持久化

- 使用 Docker volumes（如 `pgdata`）确保数据不丢失
- 本地开发的数据不会影响生产环境

---

## 🎯 推荐方案

### 最佳实践

1. **创建 `compose-app.windows.yml`**：
   - 适配 Windows 路径和端口
   - 简化开发环境配置

2. **使用环境变量**：
   - 创建 `.env.windows` 和 `.env.linux`
   - 区分开发和生产配置

3. **统一脚本**：
   - `start-dev.bat` - 启动开发环境
   - `stop-dev.bat` - 停止开发环境
   - `rebuild.bat` - 重建服务（已存在）

4. **文档化**：
   - 在 README 中说明 Windows 开发环境设置
   - 记录常见问题和解决方案

---

## ✅ 总结

**强烈推荐在 Windows 上使用 Docker 进行本地开发**，因为：

1. ✅ **环境一致性**：本地 = 生产，减少部署问题
2. ✅ **简化部署**：测试通过即可部署
3. ✅ **隔离性**：不污染系统环境
4. ✅ **团队协作**：统一开发环境

**需要做的工作**：
1. 创建 `compose-app.windows.yml`（适配 Windows）
2. 创建启动/停止脚本
3. 适配 nginx 配置（端口、路径）

**预计时间**：1-2 小时完成配置，之后开发效率大幅提升。

---

## 📚 参考资源

- [Docker Desktop for Windows 文档](https://docs.docker.com/desktop/windows/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [WSL2 后端说明](https://docs.docker.com/desktop/windows/wsl/)

