# API路径问题诊断与解决方案

## 🔍 问题现状

从微信开发者工具控制台可以看到，所有API请求都出现了**路径重复拼接**问题：

```
❌ GET http://localhost:8080/api/users/api/v1/users/me 404 (Not Found)
❌ GET http://localhost:8080/api/users/api/v1/users/me/favorites 404 (Not Found)
❌ GET http://localhost:8080/api/users/api/v1/users/me/followed-experts 404 (Not Found)
❌ GET http://localhost:8080/api/users/api/v1/users/me/watch-history 404 (Not Found)
❌ GET http://localhost:8080/api/users/api/v1/users/me/subscriptions 404 (Not Found)
```

**正确的URL应该是：**
```
✅ GET http://localhost:8080/api/users/api/v1/users/me
✅ GET http://localhost:8080/api/users/api/v1/users/me/favorites
```

## 🎯 根本原因分析

### 1. 环境变量配置
当前 `.env.development` 配置：
```env
VITE_BASE_API_URL=http://localhost:8080/api/core/
VITE_AUTH_API_URL=http://localhost:8080/api/users/
```

### 2. 路径拼接逻辑问题
在 `src/utils/request.ts` 中的 `normalizePathForGateway` 函数强制添加了 `/api/v1/` 前缀：

```typescript
// 当前错误的逻辑
function normalizePathForGateway(url: string, normalizedBaseURL: string): string {
  const path = url.startsWith('/') ? url : '/' + url
  
  if (normalizedBaseURL.includes('/api/core') || normalizedBaseURL.includes('/api/users')) {
    return path.startsWith('/api/v1/') ? path : `/api/v1${path}`  // ❌ 这里导致重复
  }
  
  return path
}
```

### 3. 拼接过程分析
1. Base URL: `http://localhost:8080/api/users/`
2. API路径: `/users/me`
3. 经过 `normalizePathForGateway` 处理后: `/api/v1/users/me`
4. 最终URL: `http://localhost:8080/api/users/` + `/api/v1/users/me` = `http://localhost:8080/api/users/api/v1/users/me` ❌

## 🔧 解决方案

### 方案一：修改环境变量（推荐）

**步骤1：修改 `.env.development`**
```env
# 修改前
VITE_BASE_API_URL=http://localhost:8080/api/core/
VITE_AUTH_API_URL=http://localhost:8080/api/users/

# 修改后
VITE_BASE_API_URL=http://localhost:8080/api/core/api/v1/
VITE_AUTH_API_URL=http://localhost:8080/api/users/api/v1/
```

**步骤2：简化路径处理逻辑**
修改 `src/utils/request.ts` 中的 `normalizePathForGateway` 函数：

```typescript
function normalizePathForGateway(url: string, normalizedBaseURL: string): string {
  const path = url.startsWith('/') ? url : '/' + url
  // 直接返回路径，不再添加 /api/v1/ 前缀
  return path
}
```

### 方案二：修改路径处理逻辑（备选）

保持环境变量不变，修改路径处理逻辑：

```typescript
function normalizePathForGateway(url: string, normalizedBaseURL: string): string {
  const path = url.startsWith('/') ? url : '/' + url
  
  // 检查base URL是否已经包含 /api/v1/
  if (normalizedBaseURL.includes('/api/v1/')) {
    // 如果base URL已经包含 /api/v1/，直接返回路径
    return path
  } else if (normalizedBaseURL.includes('/api/core') || normalizedBaseURL.includes('/api/users')) {
    // 如果base URL只包含服务路径，添加 /api/v1/ 前缀
    return path.startsWith('/api/v1/') ? path : `/api/v1${path}`
  }
  
  return path
}
```

## 📋 实施步骤

### 第一步：备份当前配置
```bash
# 备份环境变量文件
cp .env.development .env.development.backup
```

### 第二步：实施方案一（推荐）

1. **修改环境变量**
   ```env
   VITE_BASE_API_URL=http://localhost:8080/api/core/api/v1/
   VITE_AUTH_API_URL=http://localhost:8080/api/users/api/v1/
   ```

2. **修改 `src/utils/request.ts`**
   ```typescript
   function normalizePathForGateway(url: string, normalizedBaseURL: string): string {
     const path = url.startsWith('/') ? url : '/' + path
     return path
   }
   ```

### 第三步：测试验证

1. **重启开发服务器**
   ```bash
   npm run dev
   ```

2. **检查API请求URL**
   打开微信开发者工具控制台，验证API请求URL格式：
   ```
   ✅ GET http://localhost:8080/api/users/api/v1/users/me
   ✅ GET http://localhost:8080/api/core/api/v1/experts
   ```

3. **验证后端连接**
   确保后端服务运行在正确端口：
   - 核心服务：`http://localhost:8080/api/core/api/v1/`
   - 用户服务：`http://localhost:8080/api/users/api/v1/`

## 🔍 问题排查清单

### 1. 环境变量检查
- [ ] `.env.development` 文件存在
- [ ] `VITE_BASE_API_URL` 和 `VITE_AUTH_API_URL` 配置正确
- [ ] 环境变量以 `/` 结尾

### 2. 路径处理检查
- [ ] `normalizePathForGateway` 函数逻辑正确
- [ ] `shouldUseUsersGateway` 函数判断正确
- [ ] `fixDuplicatePath` 函数处理重复路径

### 3. API配置检查
- [ ] `src/config/api.ts` 中路径定义正确
- [ ] 所有API文件使用 `API_PATHS` 配置
- [ ] 路径不包含 `/api/v1/` 前缀

### 4. 后端服务检查
- [ ] 后端服务正常运行
- [ ] Nginx代理配置正确
- [ ] 端口映射正确

## 🧪 测试用例

### 测试1：用户相关API
```javascript
// 测试getCurrentUser
const response = await request.get('/users/me')
// 期望URL: http://localhost:8080/api/users/api/v1/users/me
```

### 测试2：专家相关API
```javascript
// 测试getExpertList
const response = await request.get('/experts')
// 期望URL: http://localhost:8080/api/core/api/v1/experts
```

### 测试3：收藏相关API
```javascript
// 测试getFavoriteList
const response = await request.get('/users/me/favorites')
// 期望URL: http://localhost:8080/api/users/api/v1/users/me/favorites
```

## 🚨 常见错误及解决

### 错误1：路径重复拼接
**现象：** `http://localhost:8080/api/users/api/v1/users/me`
**原因：** 环境变量和路径处理都添加了前缀
**解决：** 选择方案一或方案二

### 错误2：404 Not Found
**现象：** 所有API返回404
**原因：** 后端服务未启动或路径不匹配
**解决：** 检查后端服务和路径配置

### 错误3：CORS错误
**现象：** 跨域请求被阻止
**原因：** 后端CORS配置问题
**解决：** 配置后端允许跨域请求

## 📝 验证清单

完成修改后，请验证以下内容：

- [ ] 微信开发者工具控制台无404错误
- [ ] API请求URL格式正确
- [ ] 用户信息正常加载
- [ ] 专家列表正常显示
- [ ] 收藏功能正常工作
- [ ] 观看历史正常显示
- [ ] 订阅功能正常工作

## 🔄 回滚方案

如果修改后出现问题，可以快速回滚：

```bash
# 恢复环境变量
cp .env.development.backup .env.development

# 恢复request.ts（如果有备份）
git checkout src/utils/request.ts
```

## 📞 技术支持

如果问题仍然存在，请提供以下信息：
1. 微信开发者工具控制台完整错误日志
2. 当前 `.env.development` 配置
3. 后端服务运行状态
4. 修改后的 `request.ts` 文件内容

---

**最后更新：** 2026-04-20
**状态：** 待实施
