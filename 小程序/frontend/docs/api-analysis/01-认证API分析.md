# 认证API完整分析

## 📋 概述

认证API负责用户登录、注册、Token刷新、密码重置等功能，均通过 Users Service 提供服务。

## 📁 相关文件

- **独立文件**: `src/api/auth.ts`
- **配置文件**: `src/config/api.ts` (API_PATHS.AUTH / API_PATHS.USER)
- **Store**: `src/store/auth.ts`

## 🌐 服务信息

- **服务**: Users Service
- **Base URL**: `https://mp.dayilive.com/api/users`
- **路由规则**: 路径以 `/auth` 开头，均自动路由至 Users Service

---

## 🔗 API接口详细分析

### 认证核心接口

#### 1. 获取验证码
- **HTTP方法**: GET
- **相对路径**: `/auth/captcha`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/captcha` ✓

#### 2. 发送验证码
- **HTTP方法**: POST
- **相对路径**: `/auth/verification-codes`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/verification-codes` ✓

#### 3. 用户登录
- **HTTP方法**: POST
- **相对路径**: `/auth/login`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/login` ✓

#### 4. 用户登出
- **HTTP方法**: POST
- **相对路径**: `/auth/logout`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/logout` ✓

#### 5. 刷新 Token
- **HTTP方法**: POST
- **相对路径**: `/auth/refresh`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/refresh` ✓

#### 6. 请求密码重置
- **HTTP方法**: POST
- **相对路径**: `/auth/password-reset-request`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/password-reset-request` ✓

#### 7. 执行密码重置
- **HTTP方法**: POST
- **相对路径**: `/auth/password-reset`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/password-reset` ✓

#### 8. SSO 登录
- **HTTP方法**: POST
- **相对路径**: `/auth/sso-login`
- **完整URL**: `https://mp.dayilive.com/api/users/auth/sso-login` ✓

### 用户注册接口

#### 9. 用户注册
- **HTTP方法**: POST
- **相对路径**: `/register`
- **完整URL**: `https://mp.dayilive.com/api/users/register` ✓
- **路由规则**: `/register` 路径匹配 `shouldUseUsersGateway`

---

## 🗺️ 路径映射表

| 功能 | 方法 | 相对路径 | 完整URL |
|------|------|---------|---------|
| 获取验证码 | GET | `/auth/captcha` | `https://mp.dayilive.com/api/users/auth/captcha` |
| 发送验证码 | POST | `/auth/verification-codes` | `https://mp.dayilive.com/api/users/auth/verification-codes` |
| 用户登录 | POST | `/auth/login` | `https://mp.dayilive.com/api/users/auth/login` |
| 用户登出 | POST | `/auth/logout` | `https://mp.dayilive.com/api/users/auth/logout` |
| 刷新Token | POST | `/auth/refresh` | `https://mp.dayilive.com/api/users/auth/refresh` |
| 请求密码重置 | POST | `/auth/password-reset-request` | `https://mp.dayilive.com/api/users/auth/password-reset-request` |
| 执行密码重置 | POST | `/auth/password-reset` | `https://mp.dayilive.com/api/users/auth/password-reset` |
| SSO登录 | POST | `/auth/sso-login` | `https://mp.dayilive.com/api/users/auth/sso-login` |
| 用户注册 | POST | `/register` | `https://mp.dayilive.com/api/users/register` |

---

**分析完成时间**: 2026-04-22
**API数量**: 9个（全部 Users Service）