# Windows Docker 开发环境设置指南

## 📋 概述

本指南帮助你在 Windows 上使用 Docker 进行本地开发，实现与生产环境一致的开发体验。

## ✅ 为什么使用 Docker 开发？

1. **环境一致性**：本地环境 = 生产环境，减少部署问题
2. **简化部署**：本地测试通过即可直接部署到远程
3. **隔离性**：不污染 Windows 系统，不影响其他软件
4. **快速上手**：新成员无需安装各种依赖，一键启动

---

## 🚀 快速开始

### 1. 安装 Docker Desktop

1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 安装并启动 Docker Desktop
3. 确保启用 **WSL2 后端**（性能更好）

**系统要求**：
- Windows 10/11 64位
- 启用虚拟化（BIOS 中开启）
- 至少 8GB 内存（推荐 16GB）

### 2. 配置 Docker Desktop

1. 打开 Docker Desktop 设置
2. **Resources** → **Advanced**：
   - CPU：至少 4 核
   - Memory：至少 8GB（推荐 16GB）
3. **General** → 启用 "Use the WSL 2 based engine"

### 3. 启动开发环境

```batch
# 启动所有服务
start-dev.bat

# 或者手动启动
docker-compose -f compose-app.windows.yml up -d
```

### 4. 验证服务

访问以下地址验证服务是否正常：

- **Live Core API**: http://localhost:8000
- **Media Download API**: http://localhost:8001
- **User Service API**: http://localhost:8002
- **Nginx (代理)**: http://localhost:8080
- **SRS 控制台**: http://localhost:8080/srs

### 5. 停止开发环境

```batch
stop-dev.bat

# 或者手动停止
docker-compose -f compose-app.windows.yml down
```

---

## 🔧 配置说明

### Windows 开发环境配置

使用 `compose-app.windows.yml` 文件，主要差异：

| 配置项 | 生产环境 | Windows 开发环境 |
|--------|---------|-----------------|
| **端口映射** | 80, 443, 5432, 6379 | 8080, 8443, 5433, 6380 |
| **前端文件** | `/var/www/html/...` | 注释掉（或使用本地构建） |
| **SSL 证书** | `/var/www/mp.dayilive.com` | 不需要 |
| **媒体文件** | `/var/www/html/live-core-media` | `./data/live_core_media` |

### 端口说明

为了避免与 Windows 系统服务冲突，开发环境使用不同端口：

- **8000**: Live Core Service（保持不变）
- **8001**: Media Download Service（保持不变）
- **8002**: User Service（保持不变）
- **8080**: Nginx HTTP（生产环境是 80）
- **8443**: Nginx HTTPS（生产环境是 443）
- **5433**: PostgreSQL（生产环境是 5432）
- **6380**: Redis（生产环境是 6379）

---

## 📝 开发工作流

### 日常开发

1. **启动环境**：
   ```batch
   start-dev.bat
   ```

2. **修改代码**：
   - 在 Windows 上使用 IDE（如 PyCharm）编辑代码
   - 代码修改后需要重建容器

3. **重建服务**（代码修改后）：
   ```batch
   # 仅重建代码，保留数据库
   rebuild.bat -c
   
   # 或完整重建（删除数据库）
   rebuild.bat -f
   ```

4. **查看日志**：
   ```batch
   # 查看所有服务日志
   docker-compose -f compose-app.windows.yml logs -f
   
   # 查看特定服务日志
   docker-compose -f compose-app.windows.yml logs -f live_core_service
   ```

5. **测试 API**：
   ```batch
   # 直接访问服务
   curl http://localhost:8000/api/v1/health
   
   # 通过 Nginx 代理
   curl http://localhost:8080/api/core/health
   ```

6. **停止环境**：
   ```batch
   stop-dev.bat
   ```

### 部署到生产

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

## 🛠️ 常用命令

### 服务管理

```batch
# 启动服务
docker-compose -f compose-app.windows.yml up -d

# 停止服务
docker-compose -f compose-app.windows.yml down

# 重启服务
docker-compose -f compose-app.windows.yml restart

# 查看服务状态
docker-compose -f compose-app.windows.yml ps
```

### 日志查看

```batch
# 查看所有日志
docker-compose -f compose-app.windows.yml logs -f

# 查看特定服务日志
docker-compose -f compose-app.windows.yml logs -f live_core_service
docker-compose -f compose-app.windows.yml logs -f postgres
docker-compose -f compose-app.windows.yml logs -f nginx
```

### 进入容器

```batch
# 进入 live_core_service 容器
docker-compose -f compose-app.windows.yml exec live_core_service bash

# 进入 postgres 容器
docker-compose -f compose-app.windows.yml exec postgres psql -U postgres -d live_core_test
```

### 重建服务

```batch
# 仅重建代码（保留数据库）
rebuild.bat -c

# 完整重建（删除数据库）
rebuild.bat -f
```

---

## ⚠️ 常见问题

### 1. 端口被占用

**问题**：启动时提示端口已被占用

**解决方案**：
- 检查是否有其他服务占用端口
- 修改 `compose-app.windows.yml` 中的端口映射
- 或停止占用端口的服务

### 2. Docker Desktop 未启动

**问题**：提示 "Docker 未运行"

**解决方案**：
- 启动 Docker Desktop
- 等待 Docker Desktop 完全启动（图标不再闪烁）

### 3. 文件权限问题

**问题**：容器无法访问挂载的文件

**解决方案**：
- 检查 Docker Desktop 的文件共享设置
- 确保项目目录在 Docker Desktop 的共享目录中
- Windows 上文件权限由 Docker Desktop 自动处理

### 4. 内存不足

**问题**：容器启动失败或运行缓慢

**解决方案**：
- 增加 Docker Desktop 的内存分配（至少 8GB）
- 关闭不必要的容器
- 减少同时运行的服务

### 5. 数据库连接失败

**问题**：服务无法连接数据库

**解决方案**：
- 检查 PostgreSQL 容器是否正常运行
- 检查 `.env.docker` 中的数据库配置
- 注意端口映射：开发环境使用 5433，不是 5432

---

## 📊 性能优化

### 1. 使用 WSL2 后端

- Docker Desktop 设置 → General → 启用 "Use the WSL 2 based engine"
- WSL2 性能比 Hyper-V 更好

### 2. 文件共享优化

- Docker Desktop 设置 → Resources → File Sharing
- 只添加必要的目录，减少扫描时间

### 3. 使用 .dockerignore

在项目根目录创建 `.dockerignore`：

```
.git
.venv
__pycache__
*.pyc
.pytest_cache
node_modules
*.log
```

### 4. 资源分配

- CPU：至少 4 核
- Memory：至少 8GB（推荐 16GB）
- Swap：2GB

---

## 🔄 与生产环境的差异

| 项目 | 开发环境 (Windows) | 生产环境 (Linux) |
|------|-------------------|----------------|
| **Compose 文件** | `compose-app.windows.yml` | `compose-app.yml` |
| **端口** | 8080, 8443, 5433, 6380 | 80, 443, 5432, 6379 |
| **前端文件** | 本地构建或注释 | `/var/www/html/...` |
| **SSL 证书** | 不需要 | `/var/www/mp.dayilive.com` |
| **媒体文件** | `./data/live_core_media` | `/var/www/html/live-core-media` |

**注意**：代码逻辑完全一致，只是配置不同。

---

## 📚 参考文档

- [Docker Desktop for Windows 文档](https://docs.docker.com/desktop/windows/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目部署重建指南](./部署重建指南.md)
- [Windows Docker 开发部署方案分析](./Windows%20Docker%20开发部署方案分析.md)

---

## ✅ 总结

使用 Docker 在 Windows 上开发可以：

1. ✅ 实现与生产环境一致的开发体验
2. ✅ 简化部署流程
3. ✅ 提高开发效率
4. ✅ 减少环境配置问题

**开始使用**：运行 `start-dev.bat` 即可！

