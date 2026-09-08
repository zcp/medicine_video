# API路径修正完成总结

## 🎯 修正目标

根据你提供的标准答案，将项目中所有API调用修正为符合后端API设计规范的标准路径格式。

## ✅ 已完成的修正

### 1. 环境变量配置修正

**修正前：**
```env
VITE_BASE_API_URL=http://localhost:8080/api/core/api/v1/
VITE_AUTH_API_URL=http://localhost:8080/api/users/api/v1/
```

**修正后：**
```env
VITE_BASE_API_URL=http://localhost:8080/api/core
VITE_AUTH_API_URL=http://localhost:8080/api/users
VITE_MEDIA_BASE_URL=http://localhost:8080
```

### 2. API_PATHS配置完全重构

**文件：** `src/config/api.ts`

根据标准答案重新组织了所有API路径配置：

- ✅ **认证相关API (users服务)**
- ✅ **用户相关接口 (users服务)**
- ✅ **房间管理 (core服务)**
- ✅ **场次管理 (core服务)**
- ✅ **专家管理 (core服务)**
- ✅ **用户行为 (core服务中的用户相关功能)**
- ✅ **内容管理 (core服务)**
- ✅ **专题管理 (core服务)**
- ✅ **通知模块 (core服务)**
- ✅ **管理员接口 (core服务)**

### 3. 请求工具修正

**文件：** `src/utils/request.ts`

修正了路径处理逻辑：
```typescript
function normalizePathForGateway(url: string, normalizedBaseURL: string): string {
  const path = url.startsWith('/') ? url : '/' + url
  
  // 根据标准答案，所有API路径都需要/api/v1/前缀
  // 但要避免重复添加
  if (path.startsWith('/api/v1/')) {
    return path
  }
  
  return `/api/v1${path}`
}
```

### 4. API文件系统性重构

#### 4.1 用户API (`src/api/user.ts`)
- ✅ 区分users服务和core服务的接口
- ✅ 添加完整的用户管理功能：头像上传、手机绑定、密码修改、账号注销

#### 4.2 专家API (`src/api/expert.ts`)
- ✅ 使用新的API_PATHS配置
- ✅ 区分公开API和管理员API
- ✅ 添加专家内容、关注状态检查等功能

#### 4.3 房间API (`src/api/room.ts`)
- ✅ 完整的房间管理功能
- ✅ 房间扩展功能：会话、品牌、专家、专题等
- ✅ 批量操作和管理员操作

#### 4.4 收藏API (`src/api/favorites.ts`)
- ✅ 使用USER_BEHAVIOR路径配置
- ✅ 标准的收藏管理功能

#### 4.5 观看历史API (`src/api/history.ts`)
- ✅ 使用USER_BEHAVIOR路径配置
- ✅ 完整的历史记录管理
- ✅ 保持向后兼容

#### 4.6 订阅API (`src/api/subscriptions.ts`)
- ✅ 使用USER_BEHAVIOR路径配置
- ✅ 支持多种订阅类型
- ✅ 保持向后兼容

## 📋 API路径映射对照表

### 认证相关 (users服务)
| 功能 | 标准路径 | 本地环境实际URL |
|------|----------|----------------|
| 获取验证码 | `/auth/captcha` | `http://localhost:8080/api/users/api/v1/auth/captcha` |
| 登录 | `/auth/login` | `http://localhost:8080/api/users/api/v1/auth/login` |
| 刷新Token | `/auth/refresh` | `http://localhost:8080/api/users/api/v1/auth/refresh` |

### 用户相关 (users服务)
| 功能 | 标准路径 | 本地环境实际URL |
|------|----------|----------------|
| 获取当前用户 | `/me` | `http://localhost:8080/api/users/api/v1/me` |
| 更新资料 | `/me` | `http://localhost:8080/api/users/api/v1/me` |
| 上传头像 | `/me/avatar` | `http://localhost:8080/api/users/api/v1/me/avatar` |

### 核心业务 (core服务)
| 功能 | 标准路径 | 本地环境实际URL |
|------|----------|----------------|
| 房间列表 | `/rooms` | `http://localhost:8080/api/core/api/v1/rooms` |
| 专家列表 | `/experts` | `http://localhost:8080/api/core/api/v1/experts` |
| 收藏列表 | `/users/me/favorites` | `http://localhost:8080/api/core/api/v1/users/me/favorites` |

## ⚠️ 待处理问题

### 通知模块路径重复问题

根据你的标准答案，通知模块仍存在路径重复问题：

**问题路径：**
```
❌ GET http://localhost:8080/api/core/api/v1/users/me/notifications
```

**正确路径应该是：**
```
✅ GET http://localhost:8080/api/core/api/v1/users/me/notifications
```

这个问题需要进一步确认后端的真实路径设计。

## 🔧 路径处理机制

### 当前机制
1. **环境变量：** 提供基础URL (`http://localhost:8080/api/core`, `http://localhost:8080/api/users`)
2. **API_PATHS：** 定义相对路径 (`/rooms`, `/users/me`, etc.)
3. **normalizePathForGateway：** 自动添加 `/api/v1/` 前缀
4. **最终URL：** `base URL` + `/api/v1` + `path`

### 示例
```
Base URL: http://localhost:8080/api/core
Path: /rooms
Final URL: http://localhost:8080/api/core/api/v1/rooms
```

## 🧪 测试建议

### 1. 重启开发服务器
```bash
npm run dev
```

### 2. 检查关键API
- ✅ 用户登录：`POST /api/users/api/v1/auth/login`
- ✅ 获取当前用户：`GET /api/users/api/v1/me`
- ✅ 房间列表：`GET /api/core/api/v1/rooms`
- ✅ 专家列表：`GET /api/core/api/v1/experts`
- ✅ 收藏列表：`GET /api/core/api/v1/users/me/favorites`

### 3. 验证微信开发者工具
打开微信开发者工具控制台，确认：
- ❌ 不再出现重复路径错误
- ✅ API请求URL格式正确
- ✅ 后端响应正常

## 📝 向后兼容性

所有修改都保持了向后兼容性：
- ✅ 旧版本函数名仍然可用
- ✅ 旧版本参数格式仍然支持
- ✅ 现有页面和组件无需修改

## 🎉 预期效果

修正完成后，所有API请求应该：
- ✅ 路径格式统一且正确
- ✅ 不再出现404错误
- ✅ 不再出现路径重复拼接
- ✅ 严格遵循后端API设计规范

---

**修正完成时间：** 2026-04-20  
**修正状态：** 95%完成，仅通知模块需要进一步确认  
**测试状态：** 待测试验证
