# compose-app.yml 配置修改示例

## 基于你的实际 compose-app.yml 的修改

### 1. live_core_service 服务修改

**当前配置**（第 2-11 行）：
```yaml
live_core_service:
  build: ./backend/live_core_service
  restart: unless-stopped
  ports: ["8000:8000"]
  environment:
    POSTGRES_DB: "live_core_test"
  env_file: .env.docker
  depends_on: []
  networks:
    - live-network
```

**修改后**：
```yaml
live_core_service:
  build: ./backend/live_core_service
  restart: unless-stopped
  ports: ["8000:8000"]
  environment:
    POSTGRES_DB: "live_core_test"
    ROOM_MEDIA_ROOT_PATH: "/app/media"  # 新增：使用绝对路径
  env_file: .env.docker
  volumes:
    - /var/www/html/live-core-media:/app/media  # 新增：挂载媒体文件目录
  depends_on: []
  networks:
    - live-network
```

### 2. nginx 服务修改

**当前配置**（第 86-106 行）：
```yaml
nginx:
  image: nginx:alpine
  restart: unless-stopped
  ports: ["80:80","443:443"]
  volumes:
    # 挂载远程前端文件到容器
    - /var/www/html/user-service:/var/www/html/user-service:ro
    - /var/www/html/media-download:/var/www/html/media-download:ro
    - /var/www/html/live-center:/var/www/html/live-center:ro
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
    - ./data/srs:/var/www/srs:ro
    # SSL 证书目录（自定义位置）
    - /var/www/mp.dayilive.com:/var/www/mp.dayilive.com:ro
    # Certbot webroot 验证目录（用于 Let's Encrypt 续期）
    - /var/www/certbot:/var/www/certbot:ro
  depends_on: [srs]
  networks:
    - live-network
```

**修改后**：
```yaml
nginx:
  image: nginx:alpine
  restart: unless-stopped
  ports: ["80:80","443:443"]
  volumes:
    # 挂载远程前端文件到容器
    - /var/www/html/user-service:/var/www/html/user-service:ro
    - /var/www/html/media-download:/var/www/html/media-download:ro
    - /var/www/html/live-center:/var/www/html/live-center:ro
    - /var/www/html/live-core-media:/var/www/html/live-core-media:ro  # 新增：挂载媒体文件目录
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
    - ./data/srs:/var/www/srs:ro
    # SSL 证书目录（自定义位置）
    - /var/www/mp.dayilive.com:/var/www/mp.dayilive.com:ro
    # Certbot webroot 验证目录（用于 Let's Encrypt 续期）
    - /var/www/certbot:/var/www/certbot:ro
  depends_on: [srs]
  networks:
    - live-network
```

## 关键点说明

1. **路径一致性**：
   - `live_core_service` 写入路径：`/app/media`（容器内）
   - `live_core_service` volume：`/var/www/html/live-core-media`（宿主机）→ `/app/media`（容器内）
   - `nginx` volume：`/var/www/html/live-core-media`（宿主机）→ `/var/www/html/live-core-media`（容器内）
   - Nginx location alias：`/var/www/html/live-core-media/`

2. **环境变量优先级**：
   - `compose-app.yml` 中的 `environment` 配置会覆盖 `.env.docker` 中的配置
   - 即使 `.env.docker` 中有 `ROOM_MEDIA_ROOT_PATH=./media`，也会被覆盖为 `/app/media`

3. **目录创建**：
   ```bash
   sudo mkdir -p /var/www/html/live-core-media/rooms
   sudo mkdir -p /var/www/html/live-core-media/topics
   sudo chmod -R 755 /var/www/html/live-core-media
   sudo chown -R www-data:www-data /var/www/html/live-core-media
   ```

4. **验证**：
   ```bash
   # 重启服务
   docker-compose -f compose-app.yml down
   docker-compose -f compose-app.yml up -d
   
   # 检查 volume 挂载
   docker inspect <live_core_service_container_id> | grep -A 10 Mounts
   docker inspect <nginx_container_id> | grep -A 10 Mounts
   ```

