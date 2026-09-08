# Nginx 图片代理修复说明

**问题**: 远程部署后图片无法显示（显示"暂无图片"）  
**修复日期**: 2025-12-19

---

## 📋 问题原因

**本地开发环境**：
- Vite 开发服务器配置了 `/api/image` 代理
- 请求 `/api/image/xxx` → Vite 代理 → `https://a2.vzan.com/xxx` ✅

**远程生产环境**：
- 没有 Vite 开发服务器
- nginx 没有配置 `/api/image` 代理
- 请求 `/api/image/xxx` → nginx → 没有匹配的 location → 404 ❌

---

## ✅ 已修复

**文件**: `live-streaming-saas/nginx/nginx.conf`

**修改内容**：在 API 代理服务部分添加了 `/api/image` 代理配置（第 188-199 行）

```nginx
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
```

**关键点**：
- ✅ 位置：放在 `/api/core/` 之前，确保优先匹配
- ✅ 目标：`https://a2.vzan.com`（vzan 图片服务器）
- ✅ 伪造 Referer 和 User-Agent：绕过防盗链
- ✅ 路径重写：移除 `/api/image` 前缀

---

## 🔧 应用修复

### 步骤1：重新加载 nginx 配置

```bash
# 在服务器上执行

# 1. 测试配置语法
docker-compose exec nginx nginx -t

# 2. 如果测试通过，重新加载配置（不中断服务）
docker-compose exec nginx nginx -s reload

# 或者重启 nginx 容器
docker-compose restart nginx
```

### 步骤2：验证修复

1. **检查 nginx 日志**（应该没有 404 错误）：
   ```bash
   docker-compose logs nginx | grep "api/image"
   ```

2. **在浏览器中测试**：
   - 打开开发者工具 → Network 标签
   - 刷新页面
   - 查找 `/api/image/xxx` 请求
   - 应该返回 200 状态码，而不是 404

3. **检查图片显示**：
   - 图片应该正常显示
   - 不应该再显示"暂无图片"

---

## 📝 工作原理

### 请求流程

**修复前**（错误）：
```
浏览器 → /api/image/xxx → nginx → 没有匹配的 location → 404 ❌
```

**修复后**（正确）：
```
浏览器 → /api/image/xxx → nginx → /api/image location → 
proxy_pass https://a2.vzan.com/xxx → 返回图片 ✅
```

### 路径重写

- **请求**: `/api/image/path/to/image.jpg`
- **重写后**: `/path/to/image.jpg`
- **最终请求**: `https://a2.vzan.com/path/to/image.jpg`

---

## 🎯 总结

**问题**：nginx 缺少 `/api/image` 代理配置

**修复**：✅ 已添加 `/api/image` 代理配置

**下一步**：
1. ⚠️ 重新加载 nginx 配置
2. ⚠️ 验证图片是否正常显示

---

**修复完成时间**: 2025-12-19

