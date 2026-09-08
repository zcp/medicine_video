# Nginx 403 Permission Denied 错误修复方案

## 问题分析

nginx 日志显示：
```
open() "/var/www/html/user-service/assets/uni.bcc53402.css" failed (13: Permission denied)
```

**错误代码 13 = Permission denied**，说明 nginx 进程无法读取文件。

## 原因

1. **文件权限问题**：文件所有者不是 nginx 用户，或者没有读取权限
2. **目录权限问题**：目录没有执行权限，nginx 无法进入目录
3. **SELinux 限制**（如果启用了 SELinux）

## 快速修复步骤

### 方法1：修复文件权限（推荐）

在服务器上执行以下命令：

```bash
# 1. 检查当前权限
ls -la /var/www/html/user-service/assets/

# 2. 修改文件权限（确保 nginx 可以读取）
# 给文件添加读取权限
chmod -R 644 /var/www/html/user-service/assets/*

# 3. 修改目录权限（确保 nginx 可以进入目录）
# 目录需要执行权限（x）
find /var/www/html/user-service/assets -type d -exec chmod 755 {} \;
find /var/www/html/user-service/assets -type f -exec chmod 644 {} \;

# 4. 如果还是不行，检查整个 user-service 目录
chmod -R 755 /var/www/html/user-service
```

### 方法2：修改文件所有者（如果方法1不行）

```bash
# 检查 nginx 容器内的用户（通常是 nginx 或 www-data）
docker-compose exec nginx id

# 修改文件所有者（假设 nginx 容器内用户是 nginx，UID 可能是 101）
# 方法A：使用 nginx 用户名（如果主机上有同名用户）
chown -R nginx:nginx /var/www/html/user-service

# 方法B：使用 UID（更可靠）
# 先查看 nginx 容器的 UID
docker-compose exec nginx id
# 假设输出是 uid=101(nginx) gid=101(nginx)
chown -R 101:101 /var/www/html/user-service

# 或者使用 www-data（如果 nginx 容器使用 www-data）
chown -R www-data:www-data /var/www/html/user-service
```

### 方法3：检查 SELinux（如果启用了）

```bash
# 检查 SELinux 状态
getenforce

# 如果输出是 Enforcing，需要设置 SELinux 上下文
# 临时禁用 SELinux（不推荐，仅用于测试）
setenforce 0

# 或者设置正确的 SELinux 上下文
chcon -R -t httpd_sys_content_t /var/www/html/user-service
```

## 完整的修复命令（一键执行）

```bash
# 在服务器上执行
cd /var/www/html/user-service

# 1. 修复目录权限（目录需要执行权限）
find . -type d -exec chmod 755 {} \;

# 2. 修复文件权限（文件需要读取权限）
find . -type f -exec chmod 644 {} \;

# 3. 检查 nginx 容器内的用户
NGINX_UID=$(docker-compose exec -T nginx id -u)
NGINX_GID=$(docker-compose exec -T nginx id -g)

# 4. 修改文件所有者（使用 nginx 容器的 UID/GID）
chown -R ${NGINX_UID}:${NGINX_GID} /var/www/html/user-service

# 5. 验证权限
ls -la /var/www/html/user-service/assets/ | head -5
```

## 验证修复

1. **检查文件权限**
   ```bash
   ls -la /var/www/html/user-service/assets/uni.bcc53402.css
   # 应该显示类似：-rw-r--r-- 1 nginx nginx ...
   ```

2. **测试 nginx 是否可以读取**
   ```bash
   # 在 nginx 容器内测试
   docker-compose exec nginx cat /var/www/html/user-service/assets/uni.bcc53402.css | head -5
   ```

3. **刷新浏览器**
   - 清除缓存（Ctrl+Shift+R）
   - 检查 Network 标签，CSS/JS 文件应该返回 200 而不是 403

## 预防措施

### 1. 部署脚本中添加权限设置

在部署脚本中添加：
```bash
#!/bin/bash
# 部署脚本

# 复制文件
cp -r dist/* /var/www/html/user-service/

# 设置权限
find /var/www/html/user-service -type d -exec chmod 755 {} \;
find /var/www/html/user-service -type f -exec chmod 644 {} \;

# 设置所有者（根据实际情况调整）
NGINX_UID=101  # nginx 用户的 UID
NGINX_GID=101  # nginx 组的 GID
chown -R ${NGINX_UID}:${NGINX_GID} /var/www/html/user-service
```

### 2. 使用 umask 确保默认权限

```bash
# 在部署前设置 umask
umask 022  # 文件：644，目录：755
cp -r dist/* /var/www/html/user-service/
```

## 常见问题

### Q1: 为什么会出现权限问题？

**A**: 通常是因为：
- 文件是在主机上直接创建的，所有者是 root 或其他用户
- nginx 容器内的 nginx 用户（通常是 UID 101）无法读取这些文件

### Q2: 如何查看 nginx 容器的用户？

**A**: 
```bash
docker-compose exec nginx id
# 输出示例：uid=101(nginx) gid=101(nginx) groups=101(nginx)
```

### Q3: 修改权限后还是 403？

**A**: 检查：
1. 目录的父目录是否有执行权限（nginx 需要能够进入目录）
2. SELinux 是否启用并限制了访问
3. nginx 配置中的 `root` 或 `alias` 路径是否正确

## 总结

**核心问题**：nginx 进程无法读取 `/var/www/html/user-service/assets/` 下的文件

**解决方案**：
1. 给文件添加读取权限：`chmod 644`
2. 给目录添加执行权限：`chmod 755`
3. 修改文件所有者：`chown -R nginx:nginx`（或使用 UID/GID）

**快速修复**：
```bash
find /var/www/html/user-service -type d -exec chmod 755 {} \;
find /var/www/html/user-service -type f -exec chmod 644 {} \;
chown -R 101:101 /var/www/html/user-service  # 根据实际 UID/GID 调整
```

