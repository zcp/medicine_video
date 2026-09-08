# Nginx 配置修改精确示例

## 基于你的实际 nginx.conf 的修改

### 修改位置

在你的 `nginx/nginx.conf` 文件中，**第 185-188 行之间**插入以下配置：

### 当前配置（第 185-203 行）

```nginx
        # ========================================================================
        # API 代理服务
        # ========================================================================
        # 图片代理（必须放在 /api/core/ 之前，避免被其他 location 匹配）
        location /api/image {
            proxy_pass https://a2.vzan.com;
            proxy_set_header Host a2.vzan.com;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Referer https://a2.vzan.com/;
            proxy_set_header User-Agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
            
            # 重写路径（移除 /api/image 前缀）
            rewrite ^/api/image(.*)$ $1 break;
        }

        # 直播核心服务 API
        location /api/core/ {
            proxy_pass http://core_api/api/v1/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
```

### 修改后的配置

```nginx
        # ========================================================================
        # 直播核心服务媒体文件（必须放在所有 /api/ 路径之前）
        # ========================================================================
        location /media/ {
            alias /var/www/html/live-core-media/;
            expires 7d;
            add_header Cache-Control "public";
            access_log off;
            
            types {
                image/jpeg jpg jpeg;
                image/png png;
                image/gif gif;
            }
            
            try_files $uri =404;
        }

        # ========================================================================
        # API 代理服务
        # ========================================================================
        # 图片代理（必须放在 /api/core/ 之前，避免被其他 location 匹配）
        location /api/image {
            proxy_pass https://a2.vzan.com;
            proxy_set_header Host a2.vzan.com;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Referer https://a2.vzan.com/;
            proxy_set_header User-Agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
            
            # 重写路径（移除 /api/image 前缀）
            rewrite ^/api/image(.*)$ $1 break;
        }

        # 直播核心服务 API
        location /api/core/ {
            proxy_pass http://core_api/api/v1/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
```

## 关键点说明

1. **插入位置**：在第 185 行 `# ========================================================================` 之后，第 188 行 `# API 代理服务` 之前
2. **为什么放在这里**：
   - `/media/` 是普通前缀匹配，需要放在可能冲突的 location 之前
   - 虽然 `/media/` 和 `/api/` 前缀不同，但放在所有 API 代理之前更安全
   - 静态文件服务通常优先于代理服务
3. **alias 路径**：`/var/www/html/live-core-media/` 必须与 docker-compose 中的 volume 挂载路径一致
4. **末尾斜杠**：`alias` 指令的路径末尾必须有斜杠 `/`

## 验证配置

修改后，执行以下命令验证：

```bash
# 检查 Nginx 配置语法
docker exec -it <nginx_container_id> nginx -t

# 如果语法正确，重新加载配置
docker exec -it <nginx_container_id> nginx -s reload
```

## 关于 HTTP 80 端口

根据你的配置，HTTP 80 端口只用于用户服务前端，不涉及直播核心服务的媒体文件。因此：

- ✅ **不需要**在 80 端口配置 `/media/` location
- ✅ 所有媒体文件访问都通过 HTTPS 443 端口
- ✅ 如果未来需要在 80 端口也支持，可以添加相同的配置

