/api/v1/auth/captcha
-----

# **LiveCore Service - 用户核心模块设计文档 (V5.0 - 安全配置整合版)**

  * **版本**: 5.1 (安全配置整合版)
  * **状态**: 设计定稿
  * **设计日期**: 2025-09-09
  * **最后更新**: 2025-12-23（整合配置与安全优化方案）


## 1\. 概述

### 1.1. 文档目的

本文档旨在详细定义 **用户核心模块** 的数据库设计、API 接口规范及相关开发约定。它将作为用户模块开发、测试和后续维护的统一依据，为整个 LiveCore 项目提供稳定、安全的用户、认证与会员管理基石。

### 1.2. 模块职责

用户核心模块负责处理以下核心业务：

  * **用户账户管理**：支持用户通过本地密码或社交媒体进行注册和登录，并通过统一身份认证服务 (Authing) 集成多种社会化身份源（如微信、Apple 等）进行登录和账户绑定。
  * **身份认证**：提供基于 Token 的认证机制，管理用户会话。
  * **个人资料管理**：允许用户查看和修改自己的公开信息。
  * **会员体系**：管理可售卖的会员产品，并记录用户的订阅历史与当前状态。

## 2\. 技术栈

| 分类               | 技术选型            | 用途说明                                                                                                                                                                                                                        |
|:-----------------|:----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **服务端框架**        | FastAPI         | 构建高性能、异步的 RESTful API。                                                                                                                                                                                                      |
| **ORM**          | SQLAlchemy (异步) | 与 PostgreSQL 数据库进行交互，管理数据模型。                                                                                                                                                                                                |
| **数据模型**         | Pydantic        | 定义 API 的数据结构、请求体验证和响应序列化。                                                                                                                                                                                                   |
| **数据库**          | PostgreSQL      | 持久化存储直播房间、场次、统计等核心数据。                                                                                                                                                                                                       |
| **媒体服务器**        | SRS             | 接收 RTMP 推流，生成 HLS 流，并通过 HTTP 回调通知后端。                                                                                                                                                                                        |
| **Web 服务器**      | Nginx           | 作为反向代理、SSL 终止、负载均衡和静态资源服务。                                                                                                                                                                                                  |
| **前端播放器**        | Video.js        | 在网页端嵌入，用于播放 SRS 生成的 HLS 直播流。                                                                                                                                                                                                |
| **后台任务队列**       | celery          | 执行耗时的后台异步任务，以避免主应用（FastAPI）在处理长时间操作时被阻塞。主要用于直播结束后，在 on_unpublish 回调触发下，处理视频转码、生成封面、数据归档等任务。通过独立的 Worker 进程，实现任务处理的解耦与水平扩展。                                                                                                  |
| **消息中间件 / 缓存**   | Redis           | 主要职责：作为 Celery 的消息中间件（Broker），负责高效、可靠地存储和分发从主应用发布的后台任务消息。                                                                                                                                                                   |
| **协程/并发库**   |gevent          | 作为 Celery 的执行池（Execution Pool），使其 Worker 能够原生、高并发地执行 async def 异步任务。这统一了整个项目的异步技术模型，并提供了卓越的 I/O 并发性能。                                                                                                                       |
|**身份认证服务** 	|authing-sdk-py|	用于在后端安全地验证由 Authing 颁发的 id_token，并解析出第三方用户的身份信息。|


## **3. 安全规范 (Security Specification)**

本章节定义了用户核心模块在开发过程中必须遵守的核心安全准则。所有代码实现都必须符合以下要求。

### **3.1. 输入验证与防注入**

  * **SQL 注入防护**:

      * **指令**: 所有数据库的读写操作**必须**通过 `SQLAlchemy ORM` 进行。
      * **要求**: 严禁在代码中使用任何形式的手动 SQL 字符串拼接。所有查询条件必须通过 ORM 的参数化查询机制传递，由 SQLAlchemy 自动处理SQL转义，从根源上杜绝SQL注入风险。

  * **跨站脚本攻击 (XSS) 防护**:

      * **指令 (后端)**: 所有接收自用户的输入（尤其`nickname`, `bio`等文本字段）在存入数据库前，**必须**通过 `Pydantic` 模型进行严格的类型和格式验证。
      * **指令 (前端)**: 所有从API获取并展示在页面上的用户生成内容，**必须**使用前端框架（如Vue, React）的默认机制进行HTML转义，防止恶意脚本被执行。

### **3.2. 认证与授权 (Authentication & Authorization)**

  * **指令**: 所有需要用户登录才能访问的接口，**必须**通过 FastAPI 的 `Depends` 机制集成JWT认证中间件，对 `Authorization` Header 中的 `Bearer Token` 进行验证。
  * **要求**: `Access Token` 的有效期应设置为较短时间（如 **15分钟**），`Refresh Token` 的有效期可设置为较长时间（如 **7天**）。
              所有后台管理API**必须**在认证通过后，额外检查用户的 `role` 是否为 `ADMIN` 或 `SUPERADMIN`。具体的角色权限划分，请参见 **[章节 4. 角色与权限设计]

### **3.3. 密码安全**

  * **指令**: 用户密码在存储到 `users.password_hash` 字段前，**必须**使用 `bcrypt` 或 `Argon2` 等业界公认的强哈希算法进行加盐哈希。
  * **要求**: 严禁以任何形式在数据库或日志中存储明文密码。

### **3.4. 速率限制 (Rate Limiting)**

  * **指令**: **必须**为以下无需认证的、计算或资源消耗较大的公开接口配置速率限制。
  * **要求**:
      * `POST /api/v1/auth/login` (用户登录)
      * `POST /api/v1/users/register` (用户注册)
      * `POST /api/v1/auth/verification-codes` (发送OTP)
      * `POST /api/v1/auth/password-reset-request` (请求密码重置)
      * `GET /api/v1/auth/captcha` (获取图形验证码)
      * `POST /api/v1/auth/sso-login (SSO 及第三方登录回调)` （**新增api接口**）
      * **实现**: 采用基于 IP 地址的限制策略，推荐使用 `fastapi-limiter` 库结合 Redis 实现。初始可设置为 **每分钟10次**。

### **3.5. 防重放攻击 (Replay Attack Prevention)**

  * **指令**: 所有一次性的验证码或令牌**必须**在首次使用后立即失效。
  * **要求**:
      * **图形验证码**: 在 `login` 和 `register` 等接口的实现流程中，校验 `captcha_id` 成功后，**必须**立即从 Redis 中删除对应的键。
      * **OTP验证码**: 在 `register` 等接口的实现流程中，校验 `verification_code` 成功后，**必须**立即从 Redis 中删除对应的键。
      * **密码重置令牌**: 在 `POST /api/v1/auth/password-reset` 接口中，校验 `reset_token` 成功后，**必须**立即从 Redis 中删除对应的键。

### **3.6. 配置管理与敏感信息保护**

  * **指令**: 所有敏感信息（数据库密码、JWT密钥、Authing密钥等）**严禁**硬编码在代码中，**必须**通过环境变量进行配置。
  * **要求**:
      * **统一配置管理**: 创建 `app/core/config.py` 文件统一管理所有配置项，从环境变量读取敏感信息。
      * **移除硬编码默认值**: 所有敏感配置项（如 `POSTGRES_PASSWORD`、`JWT_SECRET_KEY`、`VITE_CLIENT_ID`、`USER_POOL_SECRET`）**不得**在代码中提供默认值，必须强制从环境变量读取。
      * **配置验证机制**: 应用启动时**必须**验证必需的环境变量是否存在，并根据环境（开发/生产）采用不同的验证策略：
          * **生产环境**: 强制验证，缺少必需配置时阻止应用启动。
          * **开发环境**: 友好警告，提示开发者配置缺失，但不阻止启动。
      * **JWT密钥强度验证**: `JWT_SECRET_KEY` **必须**至少32个字符，生产环境启动时进行长度验证。
      * **环境变量模板**: 项目**必须**提供 `.env.example` 文件作为配置模板，包含所有必需和可选的配置项说明。
      * **`.gitignore` 配置**: 确保 `.env` 文件及其变体（`.env.local`、`.env.production` 等）已添加到 `.gitignore`，防止敏感信息泄露到版本控制系统。

  * **配置管理模块示例** (`app/core/config.py`):
      ```python
      """
      应用配置管理模块
      负责从环境变量读取配置并验证必需项
      """
      import os
      import warnings
      from typing import List

      class Settings:
          """应用配置类"""
          
          # 环境标识
          ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
          
          # 数据库配置
          POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
          POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
          POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")  # 无默认值
          POSTGRES_DB: str = os.getenv("POSTGRES_DB", "users_service_test")
          POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
          
          # JWT配置
          JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")  # 无默认值
          JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
          
          # Authing配置（可选）
          VITE_CLIENT_ID: str = os.getenv("VITE_CLIENT_ID", "")
          USER_POOL_SECRET: str = os.getenv("USER_POOL_SECRET", "")
          APP_HOST: str = os.getenv("APP_HOST", "")
          REDIRECT_URL: str = os.getenv("REDIRECT_URL", "")
          ISSUER: str = os.getenv("ISSUER", "")
          
          # CORS配置
          _CORS_ORIGINS_STR: str = os.getenv("CORS_ORIGINS", "*")
          
          @property
          def BACKEND_CORS_ORIGINS(self) -> List[str]:
              """CORS允许的源列表"""
              return [
                  origin.strip() 
                  for origin in self._CORS_ORIGINS_STR.split(",") 
                  if origin.strip()
              ]
          
          # Redis配置
          REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
          REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
          REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
          REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
          
          # 调试模式
          DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
          
          def __init__(self):
              """初始化配置并验证"""
              if self.ENVIRONMENT == "production":
                  self._validate_production_config()
              else:
                  self._validate_development_config()
          
          def _validate_production_config(self):
              """生产环境严格验证"""
              errors = []
              
              if not self.POSTGRES_PASSWORD:
                  errors.append("❌ POSTGRES_PASSWORD 环境变量未设置")
              if not self.JWT_SECRET_KEY:
                  errors.append("❌ JWT_SECRET_KEY 环境变量未设置")
              elif len(self.JWT_SECRET_KEY) < 32:
                  errors.append(f"❌ JWT_SECRET_KEY 长度不足32个字符（当前：{len(self.JWT_SECRET_KEY)}）")
              if "*" in self.BACKEND_CORS_ORIGINS:
                  errors.append("❌ 生产环境CORS不允许使用 '*'，必须指定具体域名")
              if self.DEBUG:
                  errors.append("❌ 生产环境必须关闭DEBUG模式（设置 DEBUG=false）")
              
              if errors:
                  raise ValueError(
                      "\n\n" + "="*60 + "\n" +
                      "生产环境配置验证失败：\n" + 
                      "\n".join(errors) +
                      "\n" + "="*60 + "\n"
                  )
          
          def _validate_development_config(self):
              """开发环境基础验证（使用警告而非错误）"""
              warnings_list = []
              
              if not self.POSTGRES_PASSWORD:
                  warnings_list.append("⚠️  POSTGRES_PASSWORD 未设置，数据库连接可能失败")
              if not self.JWT_SECRET_KEY:
                  warnings_list.append("⚠️  JWT_SECRET_KEY 未设置，JWT认证将无法工作")
              elif len(self.JWT_SECRET_KEY) < 32:
                  warnings_list.append(f"⚠️  JWT_SECRET_KEY 长度不足32个字符（当前：{len(self.JWT_SECRET_KEY)}）")
              
              if warnings_list:
                  warning_message = (
                      "\n" + "="*60 + 
                      "\n⚠️  开发环境配置警告：\n" + 
                      "\n".join(warnings_list) + 
                      "\n" + "="*60
                  )
                  warnings.warn(warning_message, UserWarning)

      # 创建全局配置实例
      settings = Settings()
      ```

  * **环境变量部署安全**:
      * **生产环境**: **必须**使用密钥管理服务（如 AWS Secrets Manager、Azure Key Vault、HashiCorp Vault）或容器编排平台的 Secrets 机制（如 Kubernetes Secrets、Docker Secrets）管理敏感信息，严禁将 `.env` 文件直接部署到生产服务器。
      * **密钥轮换**: 建议每90天轮换一次敏感密钥，并建立密钥轮换流程。
      * **访问控制**: 遵循最小权限原则，只给必要的用户/服务访问环境变量的权限，并配置访问审计日志。
      * **分离环境**: 开发、测试、生产环境**必须**使用不同的密钥，严禁共享。

### **3.7. CORS配置安全**

  * **指令**: CORS（跨域资源共享）配置**严禁**硬编码在代码中，**必须**通过环境变量进行配置。
  * **要求**:
      * **环境变量配置**: CORS允许的源列表**必须**从 `CORS_ORIGINS` 环境变量读取，支持逗号分隔的多个域名。
      * **生产环境限制**: 生产环境**严禁**使用通配符 `*`，**必须**指定具体的允许域名列表。
      * **配置验证**: 应用启动时根据环境进行CORS配置验证：
          * **生产环境**: 检测到 `*` 时阻止启动。
          * **开发环境**: 检测到 `*` 时发出警告。
      * **配置示例**:
          * **开发环境** (`.env`): `CORS_ORIGINS=http://localhost:5174,http://127.0.0.1:5174,https://mp.dayilive.com`
          * **生产环境** (`.env.production`): `CORS_ORIGINS=https://mp.dayilive.com,https://www.mp.dayilive.com,https://admin.mp.dayilive.com`

  * **实现方式** (`app/main.py`):
      ```python
      from app.core.config import settings
      
      app.add_middleware(
          CORSMiddleware,
          allow_origins=settings.BACKEND_CORS_ORIGINS,  # 从配置读取
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
          expose_headers=["*"],
      )
      ```

### **3.8. 日志与错误消息脱敏**

  * **指令**: 所有日志输出和错误消息**必须**对敏感信息进行脱敏处理，防止密码、密钥等敏感信息泄露。
  * **要求**:
      * **日志脱敏**: 实现统一的日志脱敏工具（`app/core/logging_utils.py`），自动脱敏以下敏感信息：
          * 数据库连接URL中的密码（如 `postgresql://user:password@host/db`）
          * JWT密钥（如 `JWT_SECRET_KEY=xxx`）
          * Authing密钥（如 `VITE_CLIENT_ID=xxx`、`USER_POOL_SECRET=xxx`）
          * 通用密码字段（如 `password=xxx`、`POSTGRES_PASSWORD=xxx`）
          * Redis密码（如 `REDIS_PASSWORD=xxx`）
      * **错误消息脱敏**: 异常处理中**必须**遵循以下原则：
          * ✅ **业务逻辑错误**（如参数验证失败）可以返回具体错误信息。
          * ❌ **系统错误**（如数据库连接失败）不暴露内部细节，只返回通用错误消息。
          * ✅ 日志中只记录异常类型，不记录完整堆栈（如果可能包含敏感信息）。
          * ✅ 使用统一的错误响应格式（遵循 `6.1. 通用响应结构`）。
      * **日志脱敏工具示例** (`app/core/logging_utils.py`):
          ```python
          import re
          import logging

          def sanitize_log_message(message: str) -> str:
              """对日志消息进行脱敏处理"""
              # 移除数据库连接URL中的密码
              message = re.sub(
                  r'postgresql[+a-z]*://[^:]+:([^@]+)@',
                  r'postgresql://***:***@',
                  message,
                  flags=re.IGNORECASE
              )
              
              # 移除JWT密钥
              message = re.sub(
                  r'JWT_SECRET_KEY["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
                  r'JWT_SECRET_KEY="***"',
                  message,
                  flags=re.IGNORECASE
              )
              
              # 移除Authing密钥
              message = re.sub(
                  r'(VITE_CLIENT_ID|USER_POOL_SECRET)["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
                  r'\1="***"',
                  message,
                  flags=re.IGNORECASE
              )
              
              # 移除密码字段
              message = re.sub(
                  r'(password|passwd|pwd|POSTGRES_PASSWORD)["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
                  r'\1="***"',
                  message,
                  flags=re.IGNORECASE
              )
              
              return message

          class SanitizedFormatter(logging.Formatter):
              """脱敏日志格式化器"""
              def format(self, record):
                  record.msg = sanitize_log_message(str(record.msg))
                  return super().format(record)
          ```

      * **应用脱敏** (`app/main.py`):
          ```python
          from app.core.logging_utils import setup_sanitized_logging
          
          # 在应用启动时启用日志脱敏
          setup_sanitized_logging()
          ```

### **3.9. 密钥生成与管理最佳实践**

  * **密钥生成**:
      * **JWT密钥**: 使用 `openssl rand -hex 32` 或 `python -c "import secrets; print(secrets.token_urlsafe(32))"` 生成至少32字符的随机密钥。
      * **数据库密码**: 使用 `openssl rand -base64 24` 生成至少16字符的强密码（包含大小写字母、数字、特殊字符）。
  * **密钥管理**:
      * **定期轮换**: 建议每90天轮换一次敏感密钥。
      * **轮换流程**: 生成新密钥 → 更新环境变量 → 重启应用 → 验证功能正常 → 删除旧密钥。
      * **访问审计**: 记录所有对环境变量的访问和修改操作。
  * **环境变量模板文件**:
      * 项目**必须**提供 `.env.example` 文件作为配置模板，包含所有必需和可选的配置项说明。
      * `.env.example` 文件**严禁**包含任何真实值，只能包含占位符和说明注释。
      * 模板文件应包含以下配置项：
          * 环境标识（`ENVIRONMENT`）
          * 数据库配置（`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_SERVER`、`POSTGRES_PORT`、`POSTGRES_DB`）
          * JWT配置（`JWT_SECRET_KEY`、`JWT_ALGORITHM`）
          * Authing SSO配置（`VITE_CLIENT_ID`、`USER_POOL_SECRET`、`APP_HOST`、`REDIRECT_URL`、`ISSUER`）
          * CORS配置（`CORS_ORIGINS`）
          * Redis配置（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`、`REDIS_DB` 或 `REDIS_URL`）
          * 调试模式（`DEBUG`）
  * **安全检查清单**:
      * [ ] 所有敏感信息都从环境变量读取
      * [ ] `.env` 文件已添加到 `.gitignore`
      * [ ] `.env.example` 文件已创建（不含真实值）
      * [ ] 生产环境使用密钥管理服务
      * [ ] 设置了密钥轮换计划
      * [ ] 配置了访问审计日志
      * [ ] 不同环境使用不同的密钥
      * [ ] 代码中无硬编码的敏感信息
      * [ ] 日志脱敏功能已实现并应用
      * [ ] 错误消息不暴露敏感信息
      * [ ] JWT密钥长度至少32字符
      * [ ] 生产环境CORS配置为具体域名（非 `*`）


## 4\. 角色与权限设计

*(本章节内容有机整合自《权限设计文档》)*

本章节详细定义了平台的角色体系、各角色的职责以及对应的权限边界，是对 **[3.2. 认证与授权](https://www.google.com/search?q=%2332-%E8%AE%A4%E8%AF%81%E4%B8%8E%E6%8E%88%E6%9D%83-authentication--authorization)** 规范的全面具体化。

### 4.1. 版本规划说明

本文档定义了平台的**完整权限模型**，但将分阶段实施。

  * **第一阶段 (MVP):** 核心实现 `REGULAR`, `ADMIN`, `SUPERADMIN` 三个角色的权限。直播间管理采用**单一所有者模型**，即只有创建者可以管理自己的直播间。`MODERATOR` 角色在数据库中创建，但暂不启用其特殊管理权限。
  * **第二阶段 (平台成长期):** 将正式启用 `MODERATOR` 角色，并上线“房管”相关的协作管理功能。

### 4.2. 核心角色职责定义

  * **REGULAR (普通用户)**
      * 核心是**消费者**和**潜在的内容创作者**。他们可以使用平台的所有基础功能，包括观看、评论、购买会员，以及创建和管理**自己的**直播。这是SaaS平台的基础。
  * **MODERATOR (房管)**
      * **(保留角色)** 在平台的第一阶段，此角色**被保留但暂不启用特殊权限**，其权限等同于`REGULAR`普通用户。
      * 设计的初衷是作为**特定直播间的秩序维护者**（即“房管”）。未来版本中，当主播（所有者）需要邀请他人协作管理评论区时，将正式启用此角色并为其分配相应的管理权限。
  * **ADMIN (平台管理员)**
      * 核心是**平台的日常运营者**。他们负责管理平台上的所有用户和内容，处理日常的封禁、推荐、客服支持（如手动开通会员）等工作。**他们是业务的执行者**。
  * **SUPERADMIN (超级管理员)**
      * 核心是**系统的所有者和最高管理者**。除了拥有Admin的所有权限外，他们还独享对系统本身进行修改的最高权限，例如：修改他人角色、查看安全审计日志、调整系统配置等。**他们是规则的制定者和监督者**。

### 4.3. 角色权限矩阵

  * ✅: 代表拥有该权限。
  * \-: 代表无该权限。
  * **继承性**: 高等级角色默认继承所有低等级角色的权限。
  * **范围限制**: `MODERATOR` 的权限范围未来将仅限于被授权管理的特定直播间。

| 模块 | 权限描述 | REGULAR | MODERATOR | ADMIN | SUPERADMIN | 关联API参考                                            |
| :--- | :--- | :---: | :---: | :---: | :---: |:---------------------------------------------------|
| **通用账户** | 注册、登录、登出、刷新Token | ✅ | ✅ | ✅ | ✅ | `/auth/*`                                          |
| | 管理自己的个人资料 (查询/修改) | ✅ | ✅ | ✅ | ✅ | `GET/PATCH /users/me`                              |
| | 修改自己的密码 | ✅ | ✅ | ✅ | ✅ | `POST /users/me/password`                          |
| | 绑定/更换自己的手机号 | ✅ | ✅ | ✅ | ✅ | `POST /users/me/phone`                             |
| | 注销自己的账户 | ✅ | ✅ | ✅ | ✅ | `DELETE /users/me`                                 |
| **会员中心** | 查看可购买的会员产品 | ✅ | ✅ | ✅ | ✅ | `GET /membership-products`                         |
| | 查看/管理自己的会员订阅 | ✅ | ✅ | ✅ | ✅ | `GET/PATCH /users/me/memberships/*`                |
| | 购买/开通会员 | ✅ | ✅ | ✅ | ✅ | `POST /users/me/memberships`                       |
| **直播核心功能** | 观看任意直播 | ✅ | ✅ | ✅ | ✅ | (前端功能)                                             |
| | 在直播间发送弹幕/评论 | ✅ | ✅ | ✅ | ✅ | (WebSocket/API)                                    |
| | **创建/编辑自己的直播间** | ✅ | ✅ | ✅ | ✅ | (需新增 `/streams` 相关API)                             |
| | **开始/结束自己的直播** | ✅ | ✅ | ✅ | ✅ | (推流与回调逻辑)                                          |
| | **查看自己直播间的数据** | ✅ | ✅ | ✅ | ✅ | (需新增 `/streams/me/analytics` API)                  |
| **直播间管理\<br\>(第二阶段功能)** | 删除指定直播间的评论 | - | - | ✅ | ✅ | (需新增 `/streams/{id}/comments/{cid}` API)           |
| **(第二阶段功能)** | 禁言/踢出指定直播间的用户 | - | - | ✅ | ✅ | (需新增 `/streams/{id}/users/{uid}/mute` API)         |
| **后台 - 用户管理** | 查看所有用户列表 | - | - | ✅ | ✅ | `GET /admin/users`                                 |
| | 更新任意用户的资料 (如昵称/状态) | - | - | ✅ | ✅ | `PATCH /admin/users/{uuid}`                        |
| | **更新任意用户的角色** | - | - | - | ✅ | `PATCH /admin/users/{uuid}`                        |
| **后台 - 内容管理\<br\>(需新增模块)** | 查看平台所有直播间列表 | - | - | ✅ | ✅ | (需新增 `GET /admin/streams` API)                     |
| | 强制关停任意直播间 | - | - | ✅ | ✅ | (需新增 `POST /admin/streams/{id}/stop` API)          |
| | 推荐/置顶任意直播间 | - | - | ✅ | ✅ | (需新增 `POST /admin/streams/{id}/recommend` API)     |
| **后台 - 会员产品管理** | 查看所有会员产品 | - | - | ✅ | ✅ | `GET /admin/membership-products`                   |
| | 创建/更新会员产品 | - | - | ✅ | ✅ | `POST/PATCH /admin/membership-products/*`          |
| | 删除会员产品 | - | - | ✅ | ✅ | `DELETE /admin/membership-products/{product_code}` |
| **后台 - 会员订阅管理** | 查看任意用户的订阅记录 | - | - | ✅ | ✅ | `GET /admin/users/{uuid}/memberships`              |
| | 手动为用户创建订阅 | - | - | ✅ | ✅ | `POST /admin/users/{uuid}/memberships`             |
| | 手动更新指定订阅 | - | - | ✅ | ✅ | `PATCH /admin/subscriptions/{subscription_uuid}`   |
| **后台 - 系统管理\<br\>(需新增模块)** | **查看系统审计日志** | - | - | - | ✅ | (需新增 `GET /admin/audit-logs` API)                  |
| | **管理系统核心配置** | - | - | - | ✅ | (需新增 `/admin/system/config` API)                   |



## 5\. 数据库设计 (最终版)

本模块的数据库设计遵循“对内BIGINT，对外UUID”的原则，并采用原生`ENUM`类型保证数据完整性。

```sql
-- 用户角色
CREATE TYPE user_role AS ENUM (
    'REGULAR', 
    'MODERATOR', 
    'ADMIN', 
    'SUPERADMIN'
);

-- 通用实体状态 (用于用户账户、内容等)
CREATE TYPE entity_status AS ENUM (
    'NORMAL', 
    'BANNED', 
    'DELETED', 
    'PENDING_REVIEW', 
    'REJECTED'
);

-- 会员产品状态
CREATE TYPE membership_product_status AS ENUM (
    'DRAFT', 
    'PENDING', 
    'ACTIVE', 
    'INACTIVE', 
    'ARCHIVED'
);

-- 用户会员订阅状态
CREATE TYPE membership_status AS ENUM (
    'PENDING_PAYMENT', 
    'ACTIVE', 
    'PAST_DUE', 
    'EXPIRED', 
    'UPGRADED', 
    'REFUNDED'
);
```

### 5.2. 核心表结构 (DDL)

```sql
-- 公用函数：用于自动更新 updated_at 时间戳
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- users 表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255),
    nickname VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(512),
    bio TEXT,
    role user_role NOT NULL DEFAULT 'REGULAR',
    status entity_status NOT NULL DEFAULT 'NORMAL',
    is_email_verified BOOLEAN NOT NULL DEFAULT false,
    is_phone_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ NULL,
    last_login_ip INET,
    social_provider VARCHAR(20),
    social_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_login_method_check
        CHECK (password_hash IS NOT NULL OR (social_provider IS NOT NULL AND social_id IS NOT NULL))
);
CREATE UNIQUE INDEX idx_users_social_login ON users (social_provider, social_id);
COMMENT ON TABLE users IS '用户核心表';
COMMENT ON COLUMN users.id IS '【内部ID】主键，仅用于数据库内部关联';
COMMENT ON COLUMN users.public_id IS '【公开ID】对外暴露的唯一标识符，用于API等';
COMMENT ON COLUMN users.role IS '用户角色: REGULAR, MODERATOR, ADMIN, SUPERADMIN';
COMMENT ON COLUMN users.status IS '用户状态: NORMAL, BANNED, DELETED, PENDING_REVIEW, REJECTED';
COMMENT ON COLUMN users.social_provider IS '身份提供商。本地密码用户为NULL；通过 Authing 登录的用户，统一记为 ''authing''。';
COMMENT ON COLUMN users.social_id IS '由身份提供商提供的用户唯一ID。当 provider 为 ''authing'' 时，此处存储 Authing id_token 中的 sub 字段。';
    
CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- membership_products 表
CREATE TABLE membership_products (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    level SMALLINT NOT NULL DEFAULT 1,
    duration_unit VARCHAR(10) NOT NULL,
    duration_value INT NOT NULL,
    status membership_product_status NOT NULL DEFAULT 'DRAFT',
    payment_gateway_price_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
               
COMMENT ON TABLE membership_products IS '可供售卖的会员产品目录表';
COMMENT ON COLUMN membership_products.code IS '产品唯一编码 (e.g., VIDEO_YEARLY), 也是外键';

        
CREATE TRIGGER set_timestamp_membership_products BEFORE UPDATE ON membership_products FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- user_memberships 表
CREATE TABLE user_memberships (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    transaction_id VARCHAR(255) UNIQUE,
    product_code VARCHAR(50) NOT NULL,
    level SMALLINT NOT NULL DEFAULT 1,
    status membership_status NOT NULL DEFAULT 'PENDING_PAYMENT',
    is_auto_renew BOOLEAN NOT NULL DEFAULT false,
    admin_notes TEXT,
    start_date TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_memberships_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_memberships_product_code FOREIGN KEY (product_code) REFERENCES membership_products(code) ON DELETE RESTRICT
);
CREATE INDEX idx_user_memberships_user_id ON user_memberships(user_id);
CREATE INDEX idx_user_memberships_expires_at ON user_memberships(expires_at);
CREATE UNIQUE INDEX idx_user_memberships_one_active_per_product ON user_memberships (user_id, product_code) WHERE (status IN ('ACTIVE', 'PAST_DUE'));
COMMENT ON TABLE user_memberships IS '用户会员状态与历史表';
COMMENT ON COLUMN user_memberships.level IS '购买时产品的等级快照，用于历史数据不变性';
COMMENT ON COLUMN user_memberships.admin_notes IS '管理员手动操作备注，用于审计';
COMMENT ON COLUMN user_memberships.public_id IS '【公开ID】对外暴露的唯一标识符，用于API等';
        
CREATE TRIGGER set_timestamp_user_memberships BEFORE UPDATE ON user_memberships FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
```


## 6\. 通用 API 规范

### 6.1. 通用响应结构

所有公开 API 接口的响应都将遵循以下统一结构，以确保前端和客户端能够进行标准化处理。

| 字段名      | 类型     | 说明                                     |
| :---------- | :------- | :--------------------------------------- |
| `code`      | `int`    | 业务状态码（200 表示成功，非 200 表示各类错误） |
| `message`   | `string` | 对本次请求结果的简要说明，如 "success" 或 "参数错误"。 |
| `data`      | `object` | 实际返回的核心数据内容。成功时为业务数据对象，失败时可为 `null` 或包含详细错误信息的对象。 |
| `timestamp` | `string` | 服务器生成响应的时间戳，采用 ISO 8601 格式。 |

### 6.2. 状态码约定

#### 6.2.1. HTTP 状态码

| HTTP 状态码 | 说明             |
| :---------- | :--------------- |
| `200`       | 请求成功         |
| `400`       | 客户端请求错误   |
| `401`       | 未授权           |
| `403`       | 禁止访问         |
| `404`       | 资源或路径不存在 |
| `500`       | 服务器内部错误   |

#### 6.2.2. 业务状态码 (`code` 字段)

| 业务状态码 | 含义             |
| :--------- | :--------------- |
| `200`      | 成功             |
| `1xxx`     | 系统级错误       |
| `2xxx`     | 业务逻辑错误     |
| `3xxx`     | 权限或认证错误   |
| `4xxx`     | 参数校验错误     |

### 6.3. 分页格式约定

#### 6.3.1. 分页请求参数

| 参数名 | 类型     | 描述                                     |
| :----- | :------- | :--------------------------------------- |
| `page` | `int`    | 请求的页码，从 1 开始，默认为 1。        |
| `size` | `int`    | 每页返回的数据条数，默认为 10，最大为 100。 |
| `sort` | `string` | 排序字段及顺序，格式为 `field:direction`，例如 `created_at:desc`。 |

#### 6.3.2. 分页响应格式

分页查询成功时，`data` 字段将采用以下结构。

```json
{
  "total": 100,
  "page": 1,
  "size": 10,
  "items": [
    { "...": "..." }
  ]
}
```

## 7\. API 接口规范

**说明**: 本文档所有接口均遵循已定义的**通用响应结构**、**状态码约定**和**分页格式**。

## 7.1\. 资源: 认证与验证码 (Authentication & Verification)

### 7.1.1. 获取图形验证码 (CAPTCHA)

  * **Endpoint**: `GET /api/v1/auth/captcha`
  * **功能描述**: 生成一个唯一的、有时效性的图形验证码挑战，用于人机识别，防止机器人攻击。
  * **认证**: 公开访问，无需认证。
  * **请求参数**: 无。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "captcha_id": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
      },
      "timestamp": "2025-07-23T11:00:00Z"
    }
    ```
  * **失败响应示例** (`500 Internal Server Error` - 缓存服务异常):
    ```json
    {
      "code": 1001,
      "message": "系统内部错误",
      "data": {
        "error": "无法连接到缓存服务"
      },
      "timestamp": "2025-07-23T11:00:05Z"
    }
    ```
  * **实现流程描述**:
    1.  **生成唯一ID**: 使用 `uuid.uuid4()` 生成 `captcha_id`。
    2.  **生成随机答案**: 生成一个4-6位的随机字母数字组合。
    3.  **存入缓存**: 将 `captcha_id` 作为键，答案（转为小写）作为值，存入 Redis，并设置3分钟过期时间。
    4.  **生成图片**: 使用图像处理库（如 Pillow）将答案绘制成带有干扰的图片。
    5.  **编码与返回**: 将图片进行 Base64 编码，并与 `captcha_id` 一并返回。

### 7.1.2. 发送OTP验证码 (邮件/短信)

  * **Endpoint**: `POST /api/v1/auth/verification-codes`
  * **功能描述**: 根据业务场景，向用户的邮箱或手机发送一个有时效性的OTP验证码。此接口是一个多用途服务，通过 `channel` 和 `scenario` 的组合来适配不同业务。
  * **认证**: 公开访问，无需认证。

  * **请求体** (`application/json`):
      * **`channel`** (string, required): 发送渠道。必须为 `EMAIL` 或 `SMS`。
      * **`recipient`** (string, required): 接收者。根据 `channel` 的值，应为合法的邮箱地址或手机号码。
      * **`scenario`** (string, required): 业务场景。支持 `REGISTER`, `PASSWORD_RESET`, `BIND_PHONE` 等。
      * **`captcha_id`** (string, required): 图形验证码的唯一ID。
      * **`captcha_solution`** (string, required): 用户输入的图形验证码答案。

  * **请求体示例 1 (用于邮箱注册)**:
    ```json
    {
      "channel": "EMAIL",
      "recipient": "newuser@example.com",
      "scenario": "REGISTER",
      "captcha_id": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "captcha_solution": "aB5DeF"
    }
    ```

  * **请求体示例 2 (用于绑定手机号)**:
    ```json
    {
      "channel": "SMS",
      "recipient": "13900139000",
      "scenario": "BIND_PHONE",
      "captcha_id": "e1f2a3b4-c5d6-7a8b-9c1d-e5f6a1b2c3d4",
      "captcha_solution": "xY7zPq"
    }
    ```

  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "message": "验证码已发送，请注意查收。",
        "recipient_masked": "n******r@example.com", // 或 139****9000
        "cooldown_seconds": 60
      },
      "timestamp": "2025-07-23T10:30:00Z"
    }
    ```
  * **失败响应示例** (`429 Too Many Requests` - 请求过于频繁):
    ```json
    {
      "code": 4029,
      "message": "请求过于频繁",
      "data": {
        "error": "请在 60 秒后重试"
      },
      "timestamp": "2025-07-23T10:33:00Z"
    }
    ```
  * **实现流程描述**:
    1.  **图形验证码校验**: 首先校验 `captcha_id` 和 `captcha_solution` 的正确性。
    2.  **参数组合校验**: 检查 `channel` 和 `scenario` 的组合是否逻辑上有效。例如：
        * `scenario` 为 `BIND_PHONE` 时, `channel` 必须为 `SMS`。若不匹配，则返回参数错误。
    3.  **频率限制**: 检查 `recipient` 或 IP 的请求频率，防止滥用。
    4.  **业务前置检查**: 根据 `scenario` 执行差异化的前置检查：
        * **`REGISTER`**: 检查 `recipient` (邮箱或手机) 在 `users` 表中**不存在**或未验证。
        * **`PASSWORD_RESET`**: 检查 `recipient` 在 `users` 表中**必须存在**且已验证。
        * **`BIND_PHONE`**: 检查 `recipient` (手机号) 在 `users` 表中**不存在**于任何其他已验证的用户记录中，以防号码被恶意绑定。
    5.  **生成与存储**: 生成6位数字OTP，以 `(scenario, recipient)` 为键存入 Redis，设置5分钟过期。
    6.  **异步发送**: 根据 `channel` 的值，将发送**邮件**或**短信**的任务推送到后台任务队列（如 Celery）。
    7.  **立即返回**: 立即向客户端返回成功响应。

### 7.1.3. 用户登录

  * **Endpoint**: `POST /api/v1/auth/login`
  * **功能描述**: 通过用户名/密码进行身份验证，成功后返回 Access Token 和 Refresh Token。此接口受图形验证码保护。
  * **认证**: 公开访问，无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "username": "testuser","username": "testuser_or_email@example.com_or_13800138000",      "password": "password123",
      "captcha_id": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "captcha_solution": "xY7zPq"
    }
    ```
     * **`username`** 字段现在支持 **用户名、邮箱或手机号** 三种格式。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "a1b2c3d4e5f6...",
        "token_type": "bearer"
      },
      "timestamp": "2025-07-22T19:50:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - 密码错误):
    ```json
    {
      "code": 3001,
      "message": "用户名或密码错误",
      "data": null,
      "timestamp": "2025-07-22T19:51:00Z"
    }
    ```
  * **实现流程描述**:
    1.  **图形验证码校验**: 首先校验 `captcha_id` 和 `captcha_solution` 的正确性。
    2.  **用户查询**: 根据 `username` 字段的格式，动态判断其为用户名、邮箱还是手机号。在 `users` 表中查询 `username`, `email`, `phone_number` 三个字段中与之匹配的记录。
    3.  状态与密码校验：检查用户 `status` 是否为 `NORMAL`，并验证 `password_hash`。
    3.  **状态与密码校验**: 检查用户 `status` 是否为 `NORMAL`，并验证 `password_hash`。
    4.  **Token 生成**: 生成 JWT 格式的 `access_token` 和 `refresh_token`。
         成功验证用户身份后，系统**必须**为用户生成两种类型的Token：`access_token` 和 `refresh_token`，它们的Payload结构不同。
         **a) Access Token Payload 结构**
         `access_token` 用于访问受保护的API接口，其生命周期较短（如15分钟），并且**必须包含用户的角色信息**以支持无状态权限校验。
             * **`user_id` (Subject)**: `string`, **必需**. 用户的唯一标识符，应使用 `user.public_id`。这是JWT的标准字段。
             * **`user_role`**: `string`, **必需**. 用户的角色，例如 `'REGULAR'` 或 `'ADMIN'`。此字段是权限系统的核心。
             * **`type`**: `string`, **必需**. 固定为 `'access'`。
             * **`exp` (Expiration Time)**: `int`, **必需**. 令牌的过期时间戳。
             * **`iat` (Issued At)**: `int`, **必需**. 令牌的签发时间戳。
             * **`jti` (JWT ID)**: `string`, **必需**. 令牌的唯一ID，可用于Token黑名单机制。
        
         **`access_token` Payload 示例:**
        
         ```json
         {
           "sub": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
           "role": "ADMIN",
           "type": "access",
           "exp": 1757364000,
           "iat": 1757363100,
           "jti": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6"
         }
         ```
        
         **b) Refresh Token Payload 结构**
        
         `refresh_token` 仅用于获取新的 `access_token`，其生命周期较长（如7天）。为安全起见，它**不应包含**除用户标识外的其他敏感信息（如角色）。
        
           * **`sub` (Subject)**: `string`, **必需**. 用户的唯一标识符，应使用 `user.public_id`。
             * **`type`**: `string`, **必需**. 固定为 `'refresh'`。
             * **`exp` (Expiration Time)**: `int`, **必需**.
             * **`iat` (Issued At)**: `int`, **必需**.
             * **`jti` (JWT ID)**: `string`, **必需**.
        
         **`refresh_token` Payload 示例:**
        
         ```json
         {
           "sub": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
           "type": "refresh",
           "exp": 1757967900,
           "iat": 1757363100,
           "jti": "g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6"
         }
         ```
    5.  **信息更新**: 更新用户的 `last_login_at` 和 `last_login_ip` 字段。
    6.  **提交与返回**: 提交数据库事务，并返回 Token 信息。

### 7.1.4. 刷新令牌

  * **Endpoint**: `POST /api/v1/auth/refresh`
  * **功能描述**: 使用有效的 `refresh_token` 获取一个新的 `access_token`。
  * **认证**: 公开访问，无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "refresh_token": "a1b2c3d4e5f6..."
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9_new...",
        "token_type": "bearer"
      },
      "timestamp": "2025-07-22T21:00:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Refresh Token无效或过期):
    ```json
    {
      "code": 3003,
      "message": "凭证无效或已过期",
      "data": {
        "error": "Invalid or expired refresh token"
      },
      "timestamp": "2025-07-22T21:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  验证 `refresh_token` 的有效性（是否存在、未过期、未在黑名单中）。
    2.  若有效，为该 Token 关联的用户生成一个新的 `access_token`。
    3.  返回新的 `access_token`。

### 7.1.5. 用户登出

  * **Endpoint**: `POST /api/v1/auth/logout`
  * **功能描述**: 用户主动登出，使其持有的 Token 失效。
  * **认证**: 需要提供有效的 `Access Token`，已认证用户 (`REGULAR` 或更高)
  * **请求参数**: 无请求体，Token 通过 `Authorization` Header 传递。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": null,
      "timestamp": "2025-07-22T21:05:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token格式错误或已过期):
    ```json
    {
      "code": 3004,
      "message": "认证凭证格式无效",
      "data": null,
      "timestamp": "2025-07-22T21:06:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `access_token` 获取其唯一标识（`jti`）。
    2.  将该 `access_token` 和关联的 `refresh_token` 标识加入到 Redis 黑名单中，并设置适当的过期时间。
    3.  返回成功响应。
好的，收到您的指示。我将严格按照最详尽的标准，为您完善“资源: 用户 (Users) - 公开接口”这一章节，确保每个接口都包含完整的**请求说明**、**成功响应体**、**失败响应体**和**执行流程**。

#### **(新增) 7.1.6. 修改密码 (用户已登录)**

  * **Endpoint**: `POST /api/v1/users/me/password`
  * **功能描述**: 当前已登录的用户修改自己的密码。为保证安全，此操作需要用户提供其**当前密码**。
  * **认证**: 需要提供有效的 `Access Token`。已认证用户 (`REGULAR` 或更高)
  * **请求体** (`application/json`):
    * **`current_password`**: (string, required) 用户的当前密码。
    * **`new_password`**: (string, required) **新密码必须符合以下所有规则**：
        * 最小长度为8位。
        * 必须包含至少一个大写字母 (A-Z)。
        * 必须包含至少一个小写字母 (a-z)。
        * 必须包含至少一个数字 (0-9)。
        * 必须包含至少一个特殊字符 (例如: `!@#$%^&*()`)。
    ```json
    {
      "current_password": "old_password123",
      "new_password": "a_very_strong_new_password"
    }
    ```
      * *前端提示：建议增加一个“确认新密码”的输入框，并在前端校验两次输入的新密码是否一致，后端只需接收一次 `new_password` 即可。*
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "密码修改成功",
      "data": null,
      "timestamp": "2025-07-23T23:00:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 当前密码错误):
    ```json
    {
      "code": 4004,
      "message": "参数校验失败",
      "data": {
        "error": "当前密码不正确"
      },
      "timestamp": "2025-07-23T23:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从 `Access Token` 中解析出用户ID。
    2.  根据用户ID查询 `users` 表，获取 `password_hash`。
    3.  验证请求体中的 `current_password` 与存储的 `password_hash` 是否匹配。若不匹配，返回 400 错误。
    4.  **验证 `new_password` 是否符合上述定义的密码强度策略。** 若不符合，返回参数错误。
    5.  对 `new_password` 进行加盐哈希，生成新的 `password_hash`。
    6.  更新数据库中该用户的 `password_hash` 字段。
    7.  **安全增强**: 使该用户的所有旧 Token 和 Refresh Token 失效，强制其在其他设备上重新登录。
    8.  提交事务，并返回成功响应。

#### **(新增) 7.1.7. 忘记密码/重置密码流程 (用户未登录)**

此流程分为两步：请求重置 和 执行重置。

##### **步骤一: 请求密码重置**

  * **Endpoint**: `POST /api/v1/auth/password-reset-request`
  * **功能描述**: 用户提供注册邮箱，系统向该邮箱发送一个包含有时效性重置令牌的链接。此接口受图形验证码保护。
  * **认证**: 公开访问 ，无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "email": "user@example.com",
      "captcha_id": "e1f2a3b4-...",
      "captcha_solution": "kL9mN2"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "message": "如果该邮箱已注册，一封密码重置邮件已发送至您的邮箱。"
      },
      "timestamp": "2025-07-23T23:10:00Z"
    }
    ```
      * *注意：为防止泄露用户信息，无论邮箱是否存在，都应返回模糊的成功提示。*
  * **失败响应示例**: (`400 Bad Request` - 图形验证码错误)
  * **实现流程描述**:
    1.  校验图形验证码。
    2.  校验 `email` 格式。
    3.  查询 `users` 表确认该 `email` 是否存在。**如果不存在，直接返回成功响应，不执行后续操作**。
    4.  如果存在，生成一个唯一的、有时效性（如15分钟）的 `reset_token`。
    5.  将 `(reset_token, user_id)` 存入 Redis 并设置过期时间。
    6.  异步发送一封包含密码重置链接（如 `https://yoursite.com/reset-password?token=...`）的邮件给用户。
    7.  返回成功响应。

##### **步骤二: 执行密码重置**

  * **Endpoint**: `POST /api/v1/auth/password-reset`
  * **功能描述**: 用户通过重置令牌设置新密码。
  * **认证**: 公开访问，无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "reset_token": "unique_reset_token_from_email",
      "new_password": "a_very_strong_new_password"
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "密码重置成功",
      "data": null,
      "timestamp": "2025-07-23T23:20:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 令牌无效或过期):
    ```json
    {
      "code": 4005,
      "message": "无效的令牌",
      "data": {
        "error": "密码重置链接无效或已过期"
      },
      "timestamp": "2025-07-23T23:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从请求体获取 `reset_token` 和 `new_password`。
    2.  在 Redis 中查询 `reset_token` 是否存在。若不存在，返回 400 错误。
    3.  从 Redis 中获取关联的 `user_id`，并立即删除该键。
    4.  验证 `new_password` 的强度。
    5.  对 `new_password` 进行加盐哈希。
    6.  更新对应 `user_id` 的 `password_hash` 字段。
    7.  提交事务，返回成功响应。
    

#### **7.1.8 SSO & 第三方登录 (Authing)**

  * **Endpoint**: `POST /api/v1/auth/sso-login`
  * **功能描述**: 处理所有通过 Authing 完成的 SSO 及第三方身份源（如微信、Apple）的登录请求。后端验证 Authing 颁发的 `id_token`，并为用户完成**账户绑定或创建**，最终返回**系统自身的业务 Token**。
  * **认证**: 公开访问 ，无需认证。
  * **请求体** (`application/json`):
    ```json
    {
      "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
  * **成功响应** (`200 OK`): **(注意：响应结构与您现有的 `/login` 接口完全一致，以确保前端可以统一处理)**
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "a1b2c3d4e5f6...",
        "token_type": "bearer"
      },
      "timestamp": "2025-08-15T20:00:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token 验证失败):
    ```json
    {
      "code": 3005,
      "message": "第三方认证凭证无效",
      "data": {
        "error": "Invalid or expired id_token"
      },
      "timestamp": "2025-08-15T20:01:00Z"
    }
    ```
  * **实现流程描述 (核心逻辑)**:
    1.  **接收 Token**: 从请求体中获取 `id_token`。
    2.  **安全验证**: 调用 `AuthingService.verify_id_token` 方法，使用 Authing SDK 对 `id_token` 进行严格验证（签名、过期时间、audience、issuer）。**验证失败，立即返回 401 错误**。
    3.  **解析身份**: 验证成功后，从返回的 `payload` 中提取关键信息，主要是 `sub` (作为 `social_id`) 和 `email` (用于绑定)。
    4.  **查找或创建本地用户 (`find_or_create_user` 逻辑)**:
        a.  **第一步 (精确查找)**: `SELECT * FROM users WHERE social_provider = 'authing' AND social_id = :sub`。如果找到用户，进入步骤 5。
        b.  **第二步 (邮件绑定)**: 如果上一步未找到，且 `payload` 中包含 `email`，则 `SELECT * FROM users WHERE email = :email`。如果找到用户，说明该用户是老用户（通过密码注册），现在首次使用第三方登录。此时，应将 `social_provider = 'authing'` 和 `social_id = :sub` 更新到该用户记录中，完成**账户自动绑定**。然后进入步骤 5。
        c.  **第三步 (创建新用户)**: 如果以上两步均未找到用户，则在 `users` 表中创建一个新用户。`password_hash` 为 `NULL`，`social_provider` 设为 `'authing'`，`social_id` 设为 `sub`。`email`, `nickname`, `avatar_url` 等字段可从 `payload` 中获取。`is_email_verified` 根据 `payload` 中的 `email_verified` 字段设置。
    5.  **状态检查**: 检查找到或创建的本地用户的 `status` 是否为 `'NORMAL'`。如果被封禁 (`'BANNED'`)，则返回 403 Forbidden 错误。
    6.  **颁发业务 Token**: 为该本地用户生成系统自身的 `access_token` 和 `refresh_token`（**此步骤与 `/login` 接口完全一致**）。
      成功验证用户身份后，系统**必须**为用户生成两种类型的Token：`access_token` 和 `refresh_token`，它们的Payload结构不同。
      **a) Access Token Payload 结构**
      `access_token` 用于访问受保护的API接口，其生命周期较短（如15分钟），并且**必须包含用户的角色信息**以支持无状态权限校验。
          * **`user_id` (Subject)**: `string`, **必需**. 用户的唯一标识符，应使用 `user.public_id`。这是JWT的标准字段。
          * **`user_role`**: `string`, **必需**. 用户的角色，例如 `'REGULAR'` 或 `'ADMIN'`。此字段是权限系统的核心。
          * **`type`**: `string`, **必需**. 固定为 `'access'`。
          * **`exp` (Expiration Time)**: `int`, **必需**. 令牌的过期时间戳。
          * **`iat` (Issued At)**: `int`, **必需**. 令牌的签发时间戳。
          * **`jti` (JWT ID)**: `string`, **必需**. 令牌的唯一ID，可用于Token黑名单机制。
        
      **`access_token` Payload 示例:**
        
      ```json
      {
        "sub": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "role": "ADMIN",
        "type": "access",
        "exp": 1757364000,
        "iat": 1757363100,
        "jti": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6"
      }
      ```
        
      **b) Refresh Token Payload 结构**
        
      `refresh_token` 仅用于获取新的 `access_token`，其生命周期较长（如7天）。为安全起见，它**不应包含**除用户标识外的其他敏感信息（如角色）。
        
        * **`sub` (Subject)**: `string`, **必需**. 用户的唯一标识符，应使用 `user.public_id`。
          * **`type`**: `string`, **必需**. 固定为 `'refresh'`。
          * **`exp` (Expiration Time)**: `int`, **必需**.
          * **`iat` (Issued At)**: `int`, **必需**.
          * **`jti` (JWT ID)**: `string`, **必需**.
        
      **`refresh_token` Payload 示例:**
        
      ```json
      {
        "sub": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "type": "refresh",
        "exp": 1757967900,
        "iat": 1757363100,
        "jti": "g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6"
      }
      ```
    8. **更新登录信息**: 更新用户的 `last_login_at` 和 `last_login_ip` 字段。
    8.  **返回 Token**: 提交数据库事务，并返回与 `/login` 接口结构相同的成功响应。

-----


## 7.2\. 资源: 用户 (Users) - 公开接口

好的，完全理解您的需求。为了实现快速迭代和分阶段开发，我们将用户注册流程进行简化，**在第一阶段，仅使用图形验证码（CAPTCHA）进行基础的人机校验**，而将通过邮箱或手机发送OTP验证码的流程作为第二阶段的功能。

这是一个非常合理和敏捷的开发策略。下面是为您**简化并重新设计**的用户注册接口规范。

-----

#### 7.2.1. 用户注册 (第一阶段简化版)

  * **Endpoint**: `POST /api/v1/users/register`
  * **功能描述**: 创建一个新的用户账户。**在第一阶段，此接口仅使用图形验证码进行人机识别。**
  * **认证**: 公开访问，无需认证。
  * **请求体** (`application/json`):
    * **`username`**: (string, required)
    * **`email`**: (string, required)
    * **`password`**: (string, required) **密码必须符合以下所有规则**：
        * 最小长度为8位。
        * 必须包含至少一个大写字母 (A-Z)。
        * 必须包含至少一个小写字母 (a-z)。
        * 必须包含至少一个数字 (0-9)。
        * 必须包含至少一个特殊字符 (例如: `!@#$%^&*()`)。
    * **`nickname`**: (string, required)
    * **`captcha_id`**: (string, required)
    * **`captcha_solution`**: (string, required)
    ```json
    {
      "username": "newuser",
      "email": "newuser@example.com",
      "password": "StrongP@ssw0rd!",
      "nickname": "新手上路",
      "captcha_id": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
      "captcha_solution": "aB5DeF"
    }
    ```
      * **`verification_code`** 字段在此阶段**已被移除**。
      * 新增 **`captcha_id`** 和 **`captcha_solution`** 字段，用于图形验证码校验。

  * **成功响应** (`200 OK`):

    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "username": "newuser",
        "nickname": "新手上路"
      },
      "timestamp": "2025-07-22T20:00:00Z"
    }
    ```

  * **失败响应示例** (`400 Bad Request` - 图形验证码错误):

    ```json
    {
      "code": 4003,
      "message": "参数校验失败",
      "data": {
        "error": "图形验证码错误或已过期"
      },
      "timestamp": "2025-07-23T12:00:00Z"
    }
    ```

  * **实现流程描述**:

    1.  **图形验证码校验**: 首先从 Redis 中获取与 `captcha_id` 对应的正确答案，与用户提交的 `captcha_solution` 进行比对。若不匹配或键不存在，返回 400 错误。成功后立即删除该键。
    2.  **参数校验**: 验证 `username`, `email`, `password`, `nickname` 等字段的格式和长度。**同时，必须在后端严格校验 `password` 字段是否符合上述定义的密码强度策略。**
    3.  **唯一性检查**: 检查 `username` 和 `email` 是否已被占用。若占用，返回 409 Conflict 错误。
    4.  **密码处理**: 对 `password` 进行加盐哈希，生成 `password_hash`。
    5.  **创建记录**: 创建 `users` 表的新记录。**注意：在第一阶段，`is_email_verified` 和 `is_phone_verified` 字段应保持其默认值 `false`**，因为邮箱和手机尚未经过OTP验证。
    6.  **提交与返回**: 提交数据库事务，并返回新用户的公开信息。

-----

### **第二阶段开发展望**

当您准备开发第二阶段时，此接口将演变为：

1.  **前端流程**：用户输入邮箱/手机号后，先调用 `POST /api/v1/auth/verification-codes` 接口获取OTP验证码。
2.  **API变更**：
      * `POST /api/v1/users/register` 的请求体中将**重新引入** `verification_code` 字段。
      * 图形验证码（`captcha_id` 和 `captcha_solution`）可以保留，作为发送OTP验证码的前置校验，也可以根据产品策略移除。
3.  **实现流程变更**：
      * 在“参数校验”之后，增加一步“OTP验证码校验”逻辑。
      * 在“创建记录”的第5步中，如果OTP验证通过，则将相应的 `is_email_verified` 或 `is_phone_verified` 字段直接设置为 `true`。


#### 2.2. 获取当前用户信息

  * **Endpoint**: `GET /api/v1/users/me`
  * **功能描述**: 获取当前已登录用户的详细个人资料。
  * **认证**: 需要提供有效的 `Access Token`。已认证用户 (`REGULAR` 或更高)
  * **请求参数**: 无。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "username": "testuser",
        "email": "testuser@example.com",
        "phone_number": "138****8000", // 新增字段
        "nickname": "测试用户",
        "avatar_url": null,
        "bio": null,
        "role": "REGULAR",
        "status": "NORMAL",
        "is_email_verified": true,
        "is_phone_verified": true // 新增字段
      },
      "timestamp": "2025-07-22T20:05:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token无效):
    ```json
    {
      "code": 3004,
      "message": "认证凭证无效",
      "data": {
        "error": "Token has expired or is invalid"
      },
      "timestamp": "2025-07-22T20:06:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从 `Authorization` Header 中解析 `Access Token` 并验证其有效性。
    2.  从 Token 的载荷 (payload) 中解析出用户的内部ID (`id`)。
    3.  根据 `id` 查询 `users` 表获取完整的用户记录。
    4.  若用户不存在或状态异常（如 `BANNED`），返回 401 或 403 错误。
    5.  将查询结果序列化为 Pydantic 模型（过滤掉 `password_hash` 等敏感字段），并返回。

#### 2.3. 更新当前用户信息

  * **Endpoint**: `PATCH /api/v1/users/me`
  * **功能描述**: 更新当前用户的公开个人资料，如昵称、简介、头像。
  * **认证**: 需要提供有效的 `Access Token`。已认证用户 (`REGULAR` 或更高)
  * **请求体** (`application/json`):
    ```json
    {
      "nickname": "资深测试用户",
      "bio": "更新后的个人简介。"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的完整用户对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "a1b2c3d4-...", "username": "testuser", "email": "testuser@example.com",
        "nickname": "资深测试用户", "avatar_url": null, "bio": "更新后的个人简介。",
        "role": "REGULAR", "status": "NORMAL", "is_email_verified": true
      },
      "timestamp": "2025-07-22T20:08:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 昵称过长):
    ```json
    {
      "code": 4001,
      "message": "参数校验失败",
      "data": {
        "field": "nickname",
        "error": "昵称长度不能超过50个字符"
      },
      "timestamp": "2025-07-23T12:05:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取用户ID。
    2.  根据ID查询 `users` 表获取用户对象。
    3.  创建一个仅包含允许用户修改字段 (`nickname`, `avatar_url`, `bio`) 的 Pydantic 模型来解析请求体，以防权限提升攻击。
    4.  遍历 Pydantic 模型中已设置的字段，更新用户对象的相应属性。
    5.  提交数据库事务。
    6.  返回更新后的完整用户信息。

#### 2.4. 用户注销账户

  * **Endpoint**: `DELETE /api/v1/users/me`
  * **功能描述**: 用户软删除自己的账户。
  * **认证**: 需要提供有效的 `Access Token`。已认证用户 (`REGULAR` 或更高)
  * **请求参数**: 无。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": null,
      "timestamp": "2025-07-22T21:10:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 账户有未完成的业务):
    ```json
    {
      "code": 2002,
      "message": "业务逻辑错误",
      "data": {
        "error": "账户下存在有效会员，请先处理"
      },
      "timestamp": "2025-07-23T12:10:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取用户ID。
    2.  （可选）执行安全校验，如要求用户再输入一次密码进行确认。
    3.  （可选）执行业务检查，如确认用户没有正在进行的订阅或交易。若有，返回 403 错误。
    4.  将该用户的 `status` 字段更新为 `'DELETED'` (或 `'DEACTIVATED'`)。
    5.  将该用户的所有 Token 加入黑名单，强制其下线。
    6.  提交数据库事务，返回成功响应。

#### 2.5. 绑定手机号

  * **Endpoint**: `POST /api/v1/users/me/phone`
          * **功能描述**: 当前已登录用户绑定或更换手机号。此操作必须通过 OTP 验证码进行二次确认。
          * **认证**: 需要提供有效的 `Access Token`。已认证用户 (`REGULAR` 或更高)
          * **请求体** (`application/json`):
            ```json
            {
              "phone_number": "13900139000",
              "verification_code": "123456"
            }
            ```
          * **成功响应** (`200 OK`):
            ```json
            {
              "code": 200,
              "message": "手机号绑定成功",
              "data": {
                "phone_number": "139****9000",
                "is_phone_verified": true
              },
              "timestamp": "2025-08-15T22:00:00Z"
            }
            ```
          * **失败响应示例** (`400 Bad Request` - 验证码错误):
            ```json
            {
              "code": 4006,
              "message": "参数校验失败",
              "data": {
                "error": "验证码错误或已过期"
              },
              "timestamp": "2025-08-15T22:01:00Z"
            }
            ```
          * **实现流程描述**:
            1.  从 `Access Token` 中解析出用户ID。
            2.  从 Redis 中校验 `verification_code` 是否与 `phone_number` 及 `BIND_PHONE` 场景匹配。若不匹配，返回 400 错误。成功后立即删除该键。
            3.  再次检查 `phone_number` 是否已被其他用户绑定并验证，防止在发送验证码到完成绑定的时间窗口内被他人抢占。
            4.  更新当前用户的 `phone_number` 和 `is_phone_verified` 字段（设为 `true`）。
            5.  提交数据库事务，并返回成功响应。
            

-----

## 3\. 资源: 会员 (Memberships) - 公开接口

#### 3.1. 获取可购买的会员产品列表

  * **Endpoint**: `GET /api/v1/membership-products`
  * **功能描述**: 公开接口，获取所有状态为 `ACTIVE` 的、可供用户购买的会员产品列表，通常用于价格或购买页面。
  * **认证**:  公开访问 ，无需认证
  * **请求参数 (Query)**:
      * `sort` (string, 可选): 排序字段及顺序，默认 `sort_order:asc`。例如 `price:desc`。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "items": [
          {
            "code": "VIDEO_YEARLY",
            "name": "年度影视会员",
            "description": "畅享所有视频内容，为期一年。",
            "price": "199.99",
            "level": 1,
            "duration_unit": "year",
            "duration_value": 1
          },
          {
            "code": "LIVE_FAN_MONTHLY",
            "name": "粉丝月度包",
            "description": "直播间专属粉丝徽章和彩色弹幕。",
            "price": "29.99",
            "level": 3,
            "duration_unit": "month",
            "duration_value": 1
          }
        ]
      },
      "timestamp": "2025-07-22T20:10:00Z"
    }
    ```
  * **失败响应示例** (`500 Internal Server Error` - 数据库异常):
    ```json
    {
      "code": 1002,
      "message": "数据库查询错误",
      "data": {
        "error": "An unexpected database error occurred"
      },
      "timestamp": "2025-07-22T20:11:00Z"
    }
    ```
  * **实现流程描述**:
    1.  构建 `select(membership_products)` 查询。
    2.  添加 `WHERE status = 'ACTIVE'` 的筛选条件。
    3.  根据 `sort` Query 参数（若提供）或默认的 `sort_order` 字段对结果进行排序。
    4.  执行查询，将结果序列化为对象列表并返回。

#### 3.2. 获取当前用户的会员订阅列表

  * **Endpoint**: `GET /api/v1/users/me/memberships`
  * **功能描述**: 获取当前登录用户的所有会员订阅记录（包括历史记录和当前生效的）。
  * **认证**: 需要提供有效的 `Access Token`。已认证用户 (`REGULAR` 或更高)
  * **请求参数**: 支持通用分页参数 (`page`, `size`, `sort`)。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 2,
        "page": 1,
        "size": 10,
        "items": [
          {
            "uuid": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "VIDEO_YEARLY",
            "level": 1,
            "status": "ACTIVE",
            "is_auto_renew": true,
            "start_date": "2025-01-15T10:00:00Z",
            "expires_at": "2026-01-15T10:00:00Z",
            "created_at": "2025-01-15T09:59:00Z"
          },
          {
            "uuid": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "LIVE_FAN_MONTHLY",
            "level": 3,
            "status": "EXPIRED",
            "is_auto_renew": false,
            "start_date": "2024-12-10T14:00:00Z",
            "expires_at": "2025-01-10T14:00:00Z",
            "created_at": "2024-12-10T13:59:00Z"
          }
        ]
      },
      "timestamp": "2025-07-22T20:15:00Z"
    }
    ```
  * **失败响应示例** (`401 Unauthorized` - Token无效):
    ```json
    {
      "code": 3004,
      "message": "认证凭证无效",
      "data": {
        "error": "Token has expired or is invalid"
      },
      "timestamp": "2025-07-22T20:16:00Z"
    }
    ```
  * **实现流程描述**:
    1.  从 `Access Token` 中解析出用户 `user_id`。
    2.  构建 `select(user_memberships)` 查询，并添加 `WHERE user_id = :user_id` 条件。
    3.  应用分页和排序（默认按 `created_at` 降序）。
    4.  执行查询，将结果序列化后返回。

#### 3.3. 用户购买/创建新订阅

  * **Endpoint**: `POST /api/v1/users/me/memberships`
  * **功能描述**: 用户为自己创建一个新的订阅。这是整个会员体系的核心交易接口。
  * **认证**: 需要提供有效的 `Access Token`。 已认证用户 (`REGULAR` 或更高)
  * **请求体** (`application/json`):
    ```json
    {
      "product_code": "VIDEO_YEARLY",
      "payment_token": "tok_visa_1234..."
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "e1f2a3b4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "product_code": "VIDEO_YEARLY",
        "level": 1,
        "status": "ACTIVE",
        "is_auto_renew": true,
        "start_date": "2025-07-23T14:30:00Z",
        "expires_at": "2026-07-23T14:30:00Z",
        "created_at": "2025-07-23T14:30:00Z"
      },
      "timestamp": "2025-07-23T14:30:00Z"
    }
    ```
  * **失败响应示例** (`409 Conflict` - 用户已有同类有效订阅):
    ```json
    {
      "code": 2005,
      "message": "业务逻辑错误",
      "data": {
        "error": "您已拥有一个正在生效的同类会员"
      },
      "timestamp": "2025-07-23T14:31:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取 `user_id`。
    2.  根据 `product_code` 从 `membership_products` 表查询产品信息（价格、时长、`level`等），并检查其 `status` 是否为 `ACTIVE`。若产品不存在或未上架，返回 404 Not Found。
    3.  **检查冲突**: 查询 `user_memberships` 表，检查该用户是否已存在 `product_code` 相同且 `status` 为 `'ACTIVE'` 或 `'PAST_DUE'` 的记录。若是，则返回 409 Conflict（利用数据库的部分唯一索引 `idx_user_memberships_one_active_per_product`）。
    4.  调用支付网关服务，使用 `payment_token` 和查询到的价格完成扣款。若失败，返回 402 Payment Required。
    5.  支付成功后，获取 `transaction_id`，并根据产品时长计算 `start_date` (NOW) 和 `expires_at`。
    6.  在 `user_memberships` 表中创建一条新记录，`status` 为 `'ACTIVE'`，`is_auto_renew` 默认为 `true`。
    7.  提交事务，并返回新创建的订阅详情。

#### 3.4. 用户更新自己的订阅

  * **Endpoint**: `PATCH /api/v1/users/me/memberships/{subscription_uuid}`
  * **功能描述**: 更新用户自己的一条订阅记录，主要用于开关“自动续费”。
  * **认证**: 需要提供有效的 `Access Token`。 已认证用户 (`REGULAR` 或更高)
  * **请求体** (`application/json`):
    ```json
    {
      "is_auto_renew": false
    }
    ```
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "product_code": "VIDEO_YEARLY",
        "status": "ACTIVE",
        "is_auto_renew": false,
        "expires_at": "2026-01-15T10:00:00Z"
      },
      "timestamp": "2025-07-23T15:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 试图修改不属于自己的订阅):
    ```json
    {
      "code": 3002,
      "message": "权限不足",
      "data": {
        "error": "您无权修改此订阅"
      },
      "timestamp": "2025-07-23T15:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  解析 `Access Token` 获取 `user_id`。
    2.  根据路径参数 `subscription_uuid` 查询 `user_memberships` 表获取订阅记录。若未找到，返回 404 Not Found。
    3.  **权限校验**: 验证该订阅记录的 `user_id` 是否与当前登录用户匹配。若不匹配，返回 403 Forbidden。
    4.  **业务逻辑检查**: 检查该订阅的 `status` 是否允许被修改（例如，已 `EXPIRED` 的订阅可能不允许再修改续费状态）。
    5.  更新记录的 `is_auto_renew` 字段值。
    6.  提交数据库事务，返回更新后的订阅记录。


## 4\. 后台管理 API (Admin-Only)

**说明**: 本章节所有 API 均需要 `ADMIN` 或 `SUPERADMIN` 角色权限。

### 4.1. 资源: 用户管理 (Admin)

#### 4.1.1. 分页获取用户列表

  * **Endpoint**: `GET /api/v1/admin/users`
  * **功能描述**: (管理员) 分页、排序、筛选获取系统中的所有用户列表。
  * **认证**: 需要 `ADMIN` 或或 `SUPERADMIN`
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
      * `username` (string, 可选): 按用户名模糊搜索。
      * `email` (string, 可选): 按邮箱精确搜索。
      * `role` (string, 可选): 按角色筛选 (`REGULAR`, `MODERATOR` 等)。
      * `status` (string, 可选): 按状态筛选 (`NORMAL`, `BANNED` 等)。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "total": 120, "page": 1, "size": 10,
        "items": [
          {
            "uuid": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "username": "testuser1",
            "nickname": "用户一", 
            "email": "user1@example.com",
            "role": "REGULAR",
            "status": "NORMAL",
            "created_at": "2025-07-20T10:00:00Z"
          }
        ]
      },
      "timestamp": "2025-07-22T21:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 权限不足):
    ```json
    {
      "code": 3002,
      "message": "权限不足",
      "data": {
        "error": "您没有权限执行此操作"
      },
      "timestamp": "2025-07-23T16:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的 `ADMIN` 或 `SUPERADMIN`
    2.  构建基础的 `select(users)` 查询。
    3.  根据传入的 Query 参数动态添加 `WHERE` 筛选条件（例如 `ilike` 用于模糊搜索）。
    4.  执行 `count` 查询获取筛选后的总数。
    5.  应用排序和分页（`order_by`, `offset`, `limit`）到查询上。
    6.  执行最终查询获取当页的 `items`。
    7.  构建并返回符合分页规范的成功响应。

#### 4.1.2. 更新指定用户信息

  * **Endpoint**: `PATCH /api/v1/admin/users/{user_uuid}`
  * **功能描述**: (管理员) 更新指定用户的核心信息，如角色、状态。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求体** (`application/json`):
    ```json
    {
      "role": "MODERATOR",
      "status": "BANNED",
      "nickname": "违规用户-已被处理"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的完整用户对象)
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "uuid": "a1b2c3d4-...", "username": "testuser", "email": "testuser@example.com",
        "nickname": "违规用户-已被处理", "role": "MODERATOR", "status": "BANNED", ...
      },
      "timestamp": "2025-07-23T16:10:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 用户不存在):
    ```json
    {
      "code": 2004, "message": "资源不存在",
      "data": {
        "resource": "User",
        "id": "{user_uuid}"
      },
      "timestamp": "2025-07-23T16:11:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `user_uuid` 查询目标用户对象。若未找到，返回 404。
    3.  执行权限检查（例如 `ADMIN` 不能修改 `SUPERADMIN`）。若不通过，返回 403 Forbidden。
    4.  创建一个包含管理员可修改字段的 Pydantic 模型来验证和解析请求体。
    5.  更新用户对象的属性并提交数据库事务。
    6.  返回更新后的完整用户数据。

### 4.2. 资源: 会员产品管理 (Admin)

#### 4.2.1. 创建会员产品

  * **Endpoint**: `POST /api/v1/admin/membership-products`
  * **功能描述**: (管理员) 创建一个新的会员产品。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求体** (`application/json`):
    ```json
    {
        "code": "LIVE_SUPER_FAN_MONTHLY",
        "name": "超级粉丝月度包",
        "description": "直播间专属粉丝徽章和彩色弹幕。",
        "price": "29.99",
        "level": 3,
        "duration_unit": "month",
        "duration_value": 1,
        "status": "DRAFT",
        "sort_order": 10
    }
    ```
  * **成功响应** (`200 OK`): (返回新创建的完整产品对象)
    ```json
    {
      "code": 200, "message": "success",
      "data": {
        "code": "LIVE_SUPER_FAN_MONTHLY",
        "name": "超级粉丝月度包",
        "price": "29.99",
        "status": "DRAFT",
        ...
      },
      "timestamp": "2025-07-23T16:20:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - code已存在):
    ```json
    {
        "code": 4001, "message": "参数校验失败",
        "data": {"field": "code", "error": "产品编码已存在"},
        "timestamp": "2025-07-23T16:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  验证请求体数据，特别是 `code` 字段是否已在数据库中存在。
    3.  创建 `membership_products` 的新记录并存入数据库。
    4.  返回新创建的产品对象。
好的，遵从您的指示。我将严格按照最详尽的标准，为您完善“后台管理 API (Admin-Only)”中关于**会员产品管理**的这一章节，确保每个接口都包含完整的**请求说明**、**成功响应体**、**失败响应体**和**执行流程**。

-----

### 4.2. 资源: 会员产品管理 (Admin)

#### 4.2.1. 分页获取会员产品列表

  * **Endpoint**: `GET /api/v1/admin/membership-products`
  * **功能描述**: (管理员) 分页获取所有会员产品，包括`DRAFT`, `INACTIVE`等非上线状态，用于后台管理列表。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
      * `status` (string, 可选): 按产品状态筛选 (`DRAFT`, `ACTIVE` 等)。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 5,
        "page": 1,
        "size": 10,
        "items": [
          {
            "code": "VIDEO_YEARLY",
            "name": "年度影视会员",
            "price": "199.99",
            "level": 1,
            "status": "ACTIVE",
            "created_at": "2025-07-20T10:00:00Z"
          },
          {
            "code": "LIVE_FAN_MONTHLY",
            "name": "粉丝月度包",
            "price": "29.99",
            "level": 3,
            "status": "DRAFT",
            "created_at": "2025-07-21T11:00:00Z"
          }
        ]
      },
      "timestamp": "2025-07-22T21:00:00Z"
    }
    ```
  * **失败响应示例** (`403 Forbidden` - 权限不足):
    ```json
    {
      "code": 3002,
      "message": "权限不足",
      "data": {
        "error": "您没有权限访问此资源"
      },
      "timestamp": "2025-07-23T16:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的 `ADMIN` 或 `SUPERADMIN`
    2.  构建基础的 `select(membership_products)` 查询。
    3.  根据传入的 `status` 等 Query 参数动态添加 `WHERE` 筛选条件。
    4.  执行 `count` 查询获取筛选后的总数。
    5.  应用排序和分页（`order_by`, `offset`, `limit`）到查询上。
    6.  执行最终查询获取当页的 `items`。
    7.  构建并返回符合分页规范的成功响应。

#### 4.2.2. 获取单个会员产品详情

  * **Endpoint**: `GET /api/v1/admin/membership-products/{product_code}`
  * **功能描述**: (管理员) 获取单个会员产品的全部信息，用于编辑页面。
  * **认证**: 需要 `ADMIN`或 `SUPERADMIN`
  * **请求参数 (Path)**:
      * `product_code` (string, required): 产品的唯一编码。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "code": "VIDEO_YEARLY",
        "name": "年度影视会员",
        "description": "畅享所有视频内容，为期一年。",
        "sort_order": 1,
        "price": "199.99",
        "level": 1,
        "duration_unit": "year",
        "duration_value": 1,
        "status": "ACTIVE",
        "payment_gateway_price_id": "price_1Lq3gR...",
        "created_at": "2025-07-20T10:00:00Z",
        "updated_at": "2025-07-21T14:00:00Z"
      },
      "timestamp": "2025-07-23T18:00:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 产品不存在):
    ```json
    {
      "code": 2004,
      "message": "资源不存在",
      "data": {
        "resource": "MembershipProduct",
        "id": "INVALID_CODE"
      },
      "timestamp": "2025-07-23T18:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据路径参数 `product_code` 查询 `membership_products` 表。
    3.  若查询结果为空，返回 404 Not Found。
    4.  如果找到，序列化完整的产品对象并返回。

#### 4.2.3. 更新会员产品信息

  * **Endpoint**: `PATCH /api/v1/admin/membership-products/{product_code}`
  * **功能描述**: (管理员) 更新一个已存在的会员产品，常用于修改价格、描述或上下架（修改`status`）。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求体** (`application/json`): (所有字段均为可选)
    ```json
    {
      "price": "25.99",
      "status": "ACTIVE",
      "description": "限时优惠活动！"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的完整产品对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "code": "LIVE_FAN_MONTHLY",
        "name": "粉丝月度包",
        "price": "25.99",
        "status": "ACTIVE",
        "description": "限时优惠活动！",
        ...
      },
      "timestamp": "2025-07-23T18:30:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 产品不存在): (参考 4.2.2)
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `product_code` 查询目标产品对象。若未找到，返回 404。
    3.  创建一个包含所有可修改字段的 Pydantic 模型来验证和解析请求体。
    4.  遍历请求体中的字段，更新产品对象的相应属性。
    5.  提交数据库事务。
    6.  返回更新后的完整产品数据。

#### 4.2.4. 删除会员产品

  * **Endpoint**: `DELETE /api/v1/admin/membership-products/{product_code}`
  * **功能描述**: (管理员) 删除一个会员产品。**注意：只有在没有任何用户订阅记录引用的情况下才能成功。**
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求参数 (Path)**:
      * `product_code` (string, required): 待删除产品的唯一编码。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": null,
      "timestamp": "2025-07-23T18:45:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 产品仍被引用):
    ```json
    {
      "code": 2006,
      "message": "业务逻辑错误",
      "data": {
        "error": "无法删除仍被用户订阅引用的产品，请先将其归档(ARCHIVED)"
      },
      "timestamp": "2025-07-22T22:40:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `product_code` 查询目标产品对象。若未找到，返回 404。
    3.  尝试从数据库中删除该记录。
    4.  由于 `user_memberships` 表的外键设置了 `ON DELETE RESTRICT`，如果该产品已被任何用户订阅，数据库将直接抛出引用完整性错误。
    5.  捕获该数据库错误，并将其转换为业务错误码 `2006` 返回给客户端。
    6.  若删除成功（即无任何引用），返回成功的响应。
    7.  **最佳实践**: 业务上应引导管理员先将产品 `status` 置为 `ARCHIVED`，而非直接物理删除。

好的，遵从您的指示。我将严格按照最详尽的标准，为您完善“后台管理 API (Admin-Only)”中关于**用户订阅管理**的这一章节，确保每个接口都包含完整的**请求说明**、**成功响应体**、**失败响应体**和**执行流程**。

-----

### 4.3. 资源: 用户订阅管理 (Admin)

#### 4.3.1. 获取指定用户的订阅列表

  * **Endpoint**: `GET /api/v1/admin/users/{user_uuid}/memberships`
  * **功能描述**: (管理员/客服) 获取指定用户的所有订阅历史记录，用于后台查询和展示。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求参数 (Path)**:
      * `user_uuid` (UUID, required): 目标用户的公开ID。
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
  * **成功响应** (`200 OK`):
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 2,
        "page": 1,
        "size": 10,
        "items": [
          {
            "uuid": "d1e2f3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "VIDEO_YEARLY",
            "level": 1,
            "status": "ACTIVE",
            "is_auto_renew": true,
            "start_date": "2025-01-15T10:00:00Z",
            "expires_at": "2026-01-15T10:00:00Z",
            "created_at": "2025-01-15T09:59:00Z"
          },
          {
            "uuid": "c1b2d3a4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
            "product_code": "LIVE_FAN_MONTHLY",
            "level": 3,
            "status": "EXPIRED",
            "is_auto_renew": false,
            "start_date": "2024-12-10T14:00:00Z",
            "expires_at": "2025-01-10T14:00:00Z",
            "created_at": "2024-12-10T13:59:00Z"
          }
        ]
      },
      "timestamp": "2025-07-23T19:00:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 用户不存在):
    ```json
    {
      "code": 2004,
      "message": "资源不存在",
      "data": {
        "resource": "User",
        "id": "{user_uuid}"
      },
      "timestamp": "2025-07-23T19:01:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的 `ADMIN` 或 `SUPERADMIN`
    2.  根据路径参数 `user_uuid` 查询 `users` 表获取用户的内部 `id`。若用户不存在，返回 404 Not Found。
    3.  使用获取到的 `user_id`，查询 `user_memberships` 表获取该用户的所有记录。
    4.  应用分页和排序逻辑。
    5.  构建并返回符合分页规范的成功响应。

#### 4.3.2. 手动为用户创建订阅

  * **Endpoint**: `POST /api/v1/admin/users/{user_uuid}/memberships`
  * **功能描述**: (管理员/客服) 手动为用户赠送或补偿一个会员订阅，例如作为活动奖励或客服解决方案。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求体** (`application/json`):
    ```json
    {
        "product_code": "VIDEO_YEARLY",
        "transaction_id": "manual_gift_by_admin_xyz_001",
        "start_date": "2025-07-23T00:00:00Z",
        "expires_at": "2026-07-23T00:00:00Z",
        "notes": "用户参与“夏日活动”奖励"
    }
    ```
      * `notes` (string, 可选): 操作备注，建议存入数据库（需新增 `admin_notes` 字段）用于审计。
  * **成功响应** (`200 OK`): (返回新创建的 `user_memberships` 对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "f1g2h3i4-j5k6-7l8m-9n0o-p1q2r3s4t5u6",
        "user_id": 123,
        "product_code": "VIDEO_YEARLY",
        "level": 1,
        "status": "ACTIVE",
        "is_auto_renew": false, -- 手动创建的订阅默认不自动续费
        "start_date": "2025-07-23T00:00:00Z",
        "expires_at": "2026-07-23T00:00:00Z"
      },
      "timestamp": "2025-07-23T19:10:00Z"
    }
    ```
  * **失败响应示例** (`400 Bad Request` - 产品不存在):
    ```json
    {
        "code": 4001,
        "message": "参数校验失败",
        "data": {
            "field": "product_code",
            "error": "指定的产品编码不存在"
        },
        "timestamp": "2025-07-23T19:11:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据 `user_uuid` 找到 `user_id`。若用户不存在，返回 404。
    3.  根据请求体中的 `product_code` 查询 `membership_products` 表，获取 `level` 等信息。若产品不存在，返回 400 Bad Request。
    4.  检查该用户是否已存在与 `product_code` 相同且状态为 `ACTIVE` 或 `PAST_DUE` 的订阅。若存在，返回 409 Conflict。
    5.  在 `user_memberships` 表中插入一条新记录，`status` 设为 `ACTIVE`，`is_auto_renew` 设为 `false`。
    6.  提交事务，并返回新创建的订阅记录。

#### 4.3.3. 手动更新指定订阅

  * **Endpoint**: `PATCH /api/v1/admin/subscriptions/{subscription_uuid}`
  * **功能描述**: (管理员/客服) 手动更新一个订阅的状态或有效期，例如执行退款、延长会员时间等。
  * **认证**: 需要 `ADMIN` 或 `SUPERADMIN`
  * **请求体** (`application/json`): (所有字段均为可选)
    ```json
    {
      "status": "REFUNDED",
      "expires_at": "2025-08-01T00:00:00Z",
      "is_auto_renew": false,
      "notes": "用户申请退款，客服 Alice 手动处理"
    }
    ```
  * **成功响应** (`200 OK`): (返回更新后的 `user_memberships` 对象)
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "uuid": "{subscription_uuid}",
        "status": "REFUNDED",
        "is_auto_renew": false,
        "expires_at": "2025-08-01T00:00:00Z",
        ...
      },
      "timestamp": "2025-07-23T19:20:00Z"
    }
    ```
  * **失败响应示例** (`404 Not Found` - 订阅不存在):
    ```json
    {
      "code": 2004,
      "message": "资源不存在",
      "data": {
        "resource": "Subscription",
        "id": "{subscription_uuid}"
      },
      "timestamp": "2025-07-23T19:21:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  根据路径参数 `subscription_uuid` 查询 `user_memberships` 表获取订阅记录。若未找到，返回 404 Not Found。
    3.  创建一个包含所有管理员可修改字段的 Pydantic 模型，验证并解析请求体。
    4.  遍历请求体中的字段，更新订阅记录对象的相应属性。
    5.  提交数据库事务。
    6.  返回更新后的订阅记录对象。


## 7\. API 接口总览列表

| 模块 | 角色  | 主要功能          | HTTP 方法  | API 端点                                                                  |
| :--- |:----|:--------------|:---------|:------------------------------------------------------------------------|
| **认证与验证码** | 公开  | 获取图形验证码       | `GET`    | `/api/v1/auth/captcha`                                                  |
| | 公开  | 发送OTP验证码      | `POST`   | `/api/v1/auth/verification-codes`                                       |
| | 公开  | 用户登录          | `POST`   | `/api/v1/auth/login`                                                    |
| | 用户  | 刷新令牌          | `POST`   | `/api/v1/auth/refresh`                                                  |
| | 用户  | 用户登出          | `POST`   | `/api/v1/auth/logout`                                                   
|| 公开	 | SSO & 第三方登录	  | `POST`   | 	`/api/v1/auth/sso-login`                                               
| **用户** | 公开  | 用户注册          | `POST`   | `/api/v1/users/register`                                                |
| | 用户  | 获取当前用户信息      | `GET`    | `/api/v1/users/me`                                                      |
| | 用户  | 更新当前用户信息      | `PATCH`  | `/api/v1/users/me`                                                      |
| | 用户  | 用户注销账户        | `DELETE` | `/api/v1/users/me`                                                      |
| | 用户  | 请求密码重置        | `POST `  | `/api/v1/auth/password-reset-request`                                   |
| | 用户  | 修改密码 (用户已登录)  | `POST `  | `/api/v1/users/me/password`                                             |
| | 用户  | 执行密码重置        | `POST `  | `/api/v1/auth/password-reset`                                           
| | 用户  | 绑定手机号         | `POST`   | `/api/v1/users/me/phone`                                                ||
| **会员** | 公开  | 获取可购买产品列表     | `GET`    | `/api/v1/membership-products`                                           |
| | 用户  | 获取自己的订阅列表     | `GET`    | `/api/v1/users/me/memberships`                                          |
| | 用户  | 购买/创建新订阅      | `POST`   | `/api/v1/users/me/memberships`                                          |
| | 用户  | 更新自己的订阅（开关续费） | `PATCH`  | `/api/v1/users/me/memberships/{subscription_uuid}`                      |
| **管理-用户** | 管理员 | 分页获取用户列表      | `GET`    | `/api/v1/admin/users`                                                   |
| | 管理员 | 更新指定用户信息      | `PATCH`  | `/api/v1/admin/users/{user_uuid}`                                       |
| **管理-产品** | 管理员 | 创建会员产品        | `POST`   | `/api/v1/admin/membership-products`                                     |
| | 管理员 | 分页获取所有产品      | `GET`    | `/api/v1/admin/membership-products`                                     |
| | 管理员 | 获取单个产品详情      | `GET`    | `/api/v1/admin/membership-products/{product_code}`                      |
| | 管理员 | 更新会员产品        | `PATCH`  | `/api/v1/admin/membership-products/{product_code}`                      |
| | 管理员 | 删除会员产品        | `DELETE` | `/api/v1/admin/membership-products/{product_code}`                      |
| **管理-订阅** | 管理员 | 获取指定用户的订阅列表   | `GET`    | `/api/v1/admin/users/{user_uuid}/memberships`                           |
| | 管理员 | 手动为用户创建订阅     | `POST`   | `/api/v1/admin/users/{user_uuid}/memberships`                           |
| | 管理员 | 手动更新指定订阅      | `PATCH`  | `/api/v1/admin/subscriptions/{subscription_uuid}`                       |


## 8\. 开发规范

### 8.1. 代码规范

  * **开发语言**: 使用 Python 3.8 或更高版本。
  * **代码风格**: 严格遵循 PEP 8 规范。
  * **格式化**: 使用 4 个空格作为缩进，文件使用 UTF-8 编码。

### 8.2. 命名规范

  * **类名**: 大驼峰命名法 (PascalCase)，例如 `UserMembership`。
  * **函数/方法**: 下划线命名法 (snake\_case)，例如 `get_user_by_uuid`。
  * **变量**: 下划线命名法 (snake\_case)，例如 `access_token`。
  * **常量**: 全大写下划线命名法 (UPPER\_SNAKE\_CASE)，例如 `TOKEN_EXPIRE_MINUTES`。

## 9\. 日志与异常处理规范

#### **9.1 日志规范**

##### **9.1.1 日志级别**
* `ERROR`: 关键系统错误、导致业务失败的异常。必须立即关注。
* `WARNING`: 潜在的问题或警告信息，不影响当前流程但需关注。
* `INFO`: 记录重要的业务操作节点，如用户登录、创建直播间等。
* `DEBUG`: 用于开发和调试阶段，记录详细的程序运行信息。

##### **9.1.2 日志格式**
每一条日志记录都应包含以下标准字段：
* 时间戳 (ISO 8601 格式)
* 日志级别 (如: INFO)
* 模块名 (如: `routers.rooms`)
* 函数名
* 行号
* 消息内容
* 异常堆栈 (仅在记录异常时包含)

##### **9.1.3 日志内容**
应记录但不限于以下关键信息：
* 系统启动与关闭事件。
* 用户认证操作（登录/登出），需注意脱敏。
* 核心业务操作的入口和结果（如创建/更新/删除房间）。
* 所有捕获到的异常信息。
* 关键性能监控数据（如 API 耗时）。

##### **9.1.4 日志管理与存储**
* **集中管理**: 使用 ELK Stack (Elasticsearch, Logstash, Kibana) 进行日志的统一收集、存储和查询。
* **存储策略**:
    * 日志文件按日期进行分割和归档。
    * 对用户密码、密钥等所有敏感信息**必须**进行脱敏处理（详见 **[3.8. 日志与错误消息脱敏](#38-日志与错误消息脱敏)**）。
* **日志脱敏实现**: 
    * **必须**使用统一的日志脱敏工具（`app/core/logging_utils.py`）对所有日志输出进行脱敏。
    * 在应用启动时（`app/main.py`）**必须**调用 `setup_sanitized_logging()` 启用日志脱敏功能。
    * 脱敏范围包括：数据库连接URL、JWT密钥、Authing密钥、密码字段、Redis密码等所有敏感信息。

#### **9.2 异常处理规范**

##### **9.2.1 异常分类**
* **系统异常**: 系统级错误（如数据库连接失败、中间件故障）。
* **业务异常**: 不符合业务规则的正常操作（如余额不足、库存不够）。
* **参数异常**: 用户输入参数不符合格式或校验规则。
* **权限异常**: 用户无权访问特定资源或执行特定操作。

##### **9.2.2 异常处理原则**
* **统一处理**: 实现统一的异常处理中间件 (Exception Handling Middleware) 来捕获所有未处理的异常，避免程序崩溃。
* **明确类型**: 使用自定义的、继承自 `Exception` 的异常类来区分不同的异常情况。
* **详细日志**: 捕获到任何异常时，都必须记录详细的错误日志，包含完整的异常堆栈。**注意**：日志记录前**必须**经过脱敏处理（详见 **[3.8. 日志与错误消息脱敏](#38-日志与错误消息脱敏)**）。
* **格式统一**: 返回给客户端的错误响应必须遵循 `6.1. 通用响应结构` 的格式：    
比如：
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "resource_id": "room_uuid_123",
    "current_status": "live",
    "reason": "无法删除正在直播的房间"
  },
  "timestamp": "2025-07-08T14:40:00Z"
}

* **错误消息脱敏**: 异常处理中**必须**遵循以下原则（详见 **[3.8. 日志与错误消息脱敏](#38-日志与错误消息脱敏)**）：
    * ✅ **业务逻辑错误**（如参数验证失败）可以返回具体错误信息。
    * ❌ **系统错误**（如数据库连接失败）不暴露内部细节，只返回通用错误消息（如"内部服务器错误"）。
    * ✅ 日志中只记录异常类型（`type(e).__name__`），不记录完整堆栈（如果可能包含敏感信息）。
* **避免吞没**: 严禁捕获异常后不做任何处理（`except: pass`）。
* **优雅降级**: 在可能的情况下，对系统异常进行优雅降级处理，保证核心功能的可用性。

##### **9.2.3 异常处理流程**
1.  在业务代码中**捕获**可预见的异常。
2.  将原始异常**记录**到日志系统（**注意**：记录前必须经过脱敏处理，详见 **[3.8. 日志与错误消息脱敏](#38-日志与错误消息脱敏)**）。
3.  将原始异常**转换**为对应的自定义业务异常类型。
4.  由统一的异常处理中间件捕获所有异常，并**返回**统一格式的错误响应。
5.  在必要时（如文件句柄、数据库连接），使用 `finally` 块**清理**资源。

---

## 10. 参考资源

### 10.1. 安全配置相关资源

* **[12-Factor App: Config](https://12factor.net/config)**: 关于应用配置管理的最佳实践，强调配置与代码分离。
* **[OWASP: Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_cryptographic_key)**: OWASP关于密钥管理的安全指南。
* **[Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)**: Docker Swarm模式的密钥管理机制。
* **[Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)**: Kubernetes平台的密钥管理资源。
* **[HashiCorp Vault](https://www.vaultproject.io/)**: 企业级密钥管理工具。

### 10.2. 密钥管理服务

* **AWS Secrets Manager**: AWS平台的密钥管理服务。
* **Azure Key Vault**: Azure平台的密钥管理服务。
* **GCP Secret Manager**: Google Cloud Platform的密钥管理服务。
* **阿里云密钥管理服务（KMS）**: 阿里云平台的密钥管理服务。

### 10.3. 后续优化建议

* **配置中心**: 考虑使用配置中心（如Nacos、Apollo）统一管理配置。
* **密钥轮换自动化**: 实现自动化的密钥轮换流程。
* **配置热更新**: 对于非敏感配置，支持热更新而不需要重启应用。
* **配置验证工具**: 开发配置验证脚本，在部署前检查配置完整性。
* **监控告警**: 监控环境变量的使用情况，异常时告警。