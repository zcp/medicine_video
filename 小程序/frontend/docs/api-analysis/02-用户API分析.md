# 用户API完整分析

## 📋 概述

用户API负责用户信息管理、个人资料更新、密码修改等功能，通过 Users Service 提供服务。

## 📁 相关文件

- **独立文件**: `src/api/user.ts`
- **配置文件**: `src/config/api.ts` (API_PATHS.USER)
- **Store**: `src/store/user.ts`

## 🌐 服务信息

- **服务**: Users Service
- **Base URL**: `http://localhost:8080/api/users`
- **路由规则**: 路径以 `/me` 或 `/me/` 开头时自动路由至 Users Service

## 🔗 API接口详细分析

### 用户基本信息管理 (Users Service)

#### 1. 获取当前用户信息
- **函数名**: `getCurrentUser`
- **HTTP方法**: GET
- **相对路径**: `/me`
- **完整URL**: `http://localhost:8080/api/users/me`
- **参数**: 无
- **配置**: `{ showError: false }`
- **用途**: 获取当前登录用户的详细信息

#### 2. 更新用户资料
- **函数名**: `updateProfile`
- **HTTP方法**: PATCH
- **相对路径**: `/me`
- **完整URL**: `http://localhost:8080/api/users/me`
- **参数**: `data: UpdateProfileRequest`
- **配置**: `{ loading: true, loadingText: '保存中...' }`
- **用途**: 更新用户个人资料

#### 3. 上传用户头像
- **函数名**: `uploadAvatar`
- **HTTP方法**: POST
- **相对路径**: `/me/avatar`
- **完整URL**: `http://localhost:8080/api/users/me/avatar`
- **参数**: `file: File`（FormData格式，字段名 `avatar`）
- **配置**: `{ loading: true, loadingText: '上传中...' }`
- **用途**: 上传用户头像

#### 4. 绑定手机号
- **函数名**: `bindPhone`
- **HTTP方法**: POST
- **相对路径**: `/me/phone`
- **完整URL**: `http://localhost:8080/api/users/me/phone`
- **参数**: `data: { phone: string; code: string }`
- **配置**: `{ loading: true, loadingText: '绑定中...' }`
- **用途**: 绑定手机号码

#### 5. 修改密码
- **函数名**: `changePassword`
- **HTTP方法**: POST
- **相对路径**: `/me/password`
- **完整URL**: `http://localhost:8080/api/users/me/password`
- **参数**: `data: { oldPassword: string; newPassword: string }`
- **配置**: `{ loading: true, loadingText: '修改中...' }`
- **用途**: 修改用户密码

#### 6. 注销账户
- **函数名**: `deleteAccount`
- **HTTP方法**: DELETE
- **相对路径**: `/me`
- **完整URL**: `http://localhost:8080/api/users/me`
- **参数**: 无
- **配置**: `{ loading: true, loadingText: '注销中...' }`
- **用途**: 注销用户账户

---

## 🔧 路径路由说明

`shouldUseUsersGateway` 函数判断以下路径路由至 Users Service：

| 路径前缀 | 示例 | 路由目标 |
|---------|------|---------|
| `/auth` | `/auth/login` | Users Service |
| `/me` | `/me` | Users Service |
| `/me/` | `/me/avatar` | Users Service |
| `/register` | `/register` | Users Service |
| `/admin/users` | `/admin/users/...` | Users Service |
| 其他 | `/rooms/...`, `/sessions/...` | Core Service |

所有6个用户API函数均使用 `/me` 或 `/me/...` 前缀，均正确路由至 Users Service，**不存在路径重复拼接问题**。

---

## 📊 使用位置分析

### Store中的使用
- **文件**: `src/store/user.ts`
- **使用的API**:
  - `getCurrentUser` → `fetchCurrentUser()`
  - `updateProfile` → `updateUserProfile(data)`

### 页面中的使用
- **文件**: `src/pages/profile/ProfileEdit.vue`
  - `getCurrentUser` - 加载当前用户信息
  - `updateProfile` - 保存修改
- **文件**: `src/pages/auth/` 相关认证页面
  - `bindPhone` - 绑定手机号
  - `changePassword` - 修改密码

---

## 🗺️ 路径映射表

| 函数名 | 方法 | 相对路径 | 完整URL |
|-------|------|---------|---------|
| `getCurrentUser` | GET | `/me` | `http://localhost:8080/api/users/me` |
| `updateProfile` | PATCH | `/me` | `http://localhost:8080/api/users/me` |
| `uploadAvatar` | POST | `/me/avatar` | `http://localhost:8080/api/users/me/avatar` |
| `bindPhone` | POST | `/me/phone` | `http://localhost:8080/api/users/me/phone` |
| `changePassword` | POST | `/me/password` | `http://localhost:8080/api/users/me/password` |
| `deleteAccount` | DELETE | `/me` | `http://localhost:8080/api/users/me` |

---

**分析完成时间**: 2026-04-22
**API数量**: 6个（均在 Users Service）
**使用位置**: `src/store/user.ts`, `src/pages/profile/`, `src/pages/auth/`