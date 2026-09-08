# 健康检查模块代码生成提示词 - 第二阶段（Service层和API层）

## 1. 角色定义 (Role Definition)

你是一名精通"学院派"架构（Clean Architecture）的资深 Python 后端架构师。你擅长将业务需求（来自设计文档）解耦，并严格执行分层架构。

## 2. 任务目标 (Task Objective)

你的任务是为**健康检查模块**生成第二阶段的代码，包括：

1. **业务逻辑层 (Service Layer)** (创建 `app/services/health_service.py`)
2. **API端点层 (Endpoint Layer)** (创建 `app/api/v1/endpoints/health.py`)

**⚠️ 特殊说明**：
- 健康检查模块有3个API端点，但只有1个需要Service层（就绪检查）
- 基础健康检查和配置检查直接在API层实现，无需Service层

## 3. 核心架构约束 (学院派关键规则)

你**必须**严格执行"学院派"架构分层：

  * **`Service` 层 (本提示词生成)**:
      * **负责**：业务逻辑编排（如数据库连接测试的调用）。
      * **严禁**：处理事务（`db.commit/rollback`）。
      * **严禁**：抛出 `HTTPException` 或返回 `JSONResponse`。
      * **注意**：健康检查模块的Service层非常简单，主要是调用CRUD层的数据库连接测试函数。

  * **`Endpoint` (API) 层 (本提示词生成)**:
      * **负责**：参数绑定、`Depends` 注入、调用 Service（如果需要）。
      * **[关键] 路由定义**：**必须**在 `endpoints/health.py` 中定义 `APIRouter(tags=["健康检查"])` (不含 `prefix`)。`prefix` **必须**在顶层 `api/v1/api.py` 文件的 `api_router.include_router(...)` 中统一指定。
      * **[关键] 响应格式**：所有成功响应**必须**调用 `success_response(data=...)` 函数。
      * **[关键] HTTP状态码**：就绪检查失败时应返回 `503 Service Unavailable`。

## 4. 核心上下文信息 (Dependencies)

  * `app/crud/health.py`：已存在 `check_database_connection(db)` 函数。
  * `app/core/responses.py`：已存在 `success_response(data)` 和 `error_response(code, message, data)`。
  * `app/core/config.py`：已存在 `settings` 对象，包含所有配置信息。
  * `app/core/deps.py`：已存在 `get_db` 依赖，用于获取数据库会话。

## 5. API接口详细说明

### 5.1 GET /api/v1/health - 基础健康检查

**描述**: 基础健康检查端点，返回服务状态和版本信息

**认证**: 无需认证，公开访问

**请求参数**: 无

**成功响应** (`200 OK`):
```json
{
  "status": "healthy",
  "service": "live-core-service",
  "version": "2.1.0",
  "timestamp": "2026-01-06T10:00:00Z"
}
```

**实现要求**:
- **直接在API层实现**，无需Service层
- 硬编码返回服务状态信息
- 版本号从配置读取或硬编码
- 始终返回200状态码

### 5.2 GET /api/v1/health/ready - 就绪检查

**描述**: 就绪检查端点，包含数据库连接测试

**认证**: 无需认证，公开访问

**请求参数**: 无

**成功响应** (`200 OK`):
```json
{
  "status": "ready",
  "service": "live-core-service",
  "database": "connected",
  "timestamp": "2026-01-06T10:00:00Z"
}
```

**失败响应** (`503 Service Unavailable`):
```json
{
  "status": "not_ready",
  "service": "live-core-service",
  "database": "disconnected",
  "error": "连接数据库失败",
  "timestamp": "2026-01-06T10:00:00Z"
}
```

**实现要求**:
- **需要Service层**：调用 `crud.health.check_database_connection(db)`
- 根据数据库连接测试结果返回不同状态码：
  - 连接成功：返回200，`status: "ready"`, `database: "connected"`
  - 连接失败：返回503，`status: "not_ready"`, `database: "disconnected"`, `error: "连接数据库失败"`

### 5.3 GET /api/v1/health/config - 配置检查

**描述**: 配置检查端点，返回非敏感的配置信息

**认证**: 无需认证，公开访问

**请求参数**: 无

**成功响应** (`200 OK`):
```json
{
  "status": "configured",
  "service": "live-core-service",
  "config": {
    "environment": "production",
    "debug": false,
    "database": {
      "server": "localhost",
      "port": 5432,
      "database": "live_streaming_saas"
    },
    "cors_origins": ["https://yourdomain.com"],
    "jwt_algorithm": "HS256"
  },
  "timestamp": "2026-01-06T10:00:00Z"
}
```

**实现要求**:
- **直接在API层实现**，无需Service层
- 从 `settings` 对象读取配置
- **脱敏处理**：移除所有敏感信息
  - 移除 `database.password`
  - 移除 `jwt_secret_key`
  - 移除 `api_keys`
  - 移除任何包含 `password`, `secret`, `key`, `token` 的字段
- 只保留安全的配置信息：`environment`, `debug`, `database.server`, `database.port`, `database.database`, `cors_origins`, `jwt_algorithm`

## 6. 具体代码生成指令

### 6.1 第一部分：`app/services/health_service.py`

**职责**：封装健康检查相关的业务逻辑（主要是数据库连接测试的调用）。

#### 代码生成模板

```python
"""
健康检查模块的 Service 层 (学院派)
职责：
- 调用CRUD层进行数据库连接测试
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import health as crud_health
import logging

logger = logging.getLogger(__name__)

class HealthService:
    """健康检查Service"""
    
    def __init__(self):
        pass
    
    async def check_readiness(
        self,
        db: AsyncSession
    ) -> dict:
        """
        检查服务就绪状态（包含数据库连接测试）
        
        Args:
            db: 数据库会话
        
        Returns:
            dict: 包含状态信息的字典
                {
                    "status": "ready" | "not_ready",
                    "database": "connected" | "disconnected",
                    "error": str | None
                }
        """
        # 调用CRUD层测试数据库连接
        is_connected = await crud_health.check_database_connection(db)
        
        if is_connected:
            return {
                "status": "ready",
                "database": "connected",
                "error": None
            }
        else:
            return {
                "status": "not_ready",
                "database": "disconnected",
                "error": "连接数据库失败"
            }
```

### 6.2 第二部分：`app/api/v1/endpoints/health.py`

**职责**：定义健康检查相关的API端点。

#### 代码生成模板

```python
"""
健康检查模块的 API 端点层 (学院派)
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Dict, Any
import logging

from app.core.deps import get_db
from app.core.responses import success_response, error_response
from app.core.config import settings
from app.services.health_service import HealthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["健康检查"])

# Service实例
health_service = HealthService()

def get_current_timestamp() -> str:
    """获取当前UTC时间戳字符串"""
    return datetime.now(timezone.utc).isoformat()

def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    脱敏配置信息，移除敏感字段
    
    Args:
        config: 原始配置字典
    
    Returns:
        dict: 脱敏后的配置字典
    """
    sensitive_keys = [
        "password", "secret", "key", "token", "api_key",
        "jwt_secret_key", "database_password"
    ]
    
    sanitized = {}
    for key, value in config.items():
        # 跳过包含敏感关键词的字段
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            continue
        
        # 如果是字典，递归处理
        if isinstance(value, dict):
            sanitized[key] = sanitize_config(value)
        else:
            sanitized[key] = value
    
    return sanitized

@router.get("/health")
async def health_check():
    """
    基础健康检查端点
    
    返回：
        - 200: 服务正常运行
    """
    try:
        # 直接返回硬编码的状态信息
        data = {
            "status": "healthy",
            "service": "live-core-service",
            "version": getattr(settings, "VERSION", "2.1.0"),
            "timestamp": get_current_timestamp()
        }
        
        logger.debug("基础健康检查请求")
        return success_response(data=data)
        
    except Exception as e:
        logger.error(f"基础健康检查失败: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="服务内部错误",
                data={"reason": str(e)}
            )
        )

@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
):
    """
    就绪检查端点（包含数据库连接测试）
    
    返回：
        - 200: 服务就绪（数据库连接正常）
        - 503: 服务未就绪（数据库连接失败）
    """
    try:
        # 调用Service层检查就绪状态
        readiness_status = await health_service.check_readiness(db)
        
        # 根据状态返回不同的HTTP状态码
        if readiness_status["status"] == "ready":
            data = {
                "status": readiness_status["status"],
                "service": "live-core-service",
                "database": readiness_status["database"],
                "timestamp": get_current_timestamp()
            }
            logger.info("就绪检查：服务就绪")
            return success_response(data=data)
        else:
            data = {
                "status": readiness_status["status"],
                "service": "live-core-service",
                "database": readiness_status["database"],
                "error": readiness_status["error"],
                "timestamp": get_current_timestamp()
            }
            logger.warning(f"就绪检查：服务未就绪 - {readiness_status['error']}")
            return JSONResponse(
                status_code=503,
                content=success_response(data=data)
            )
            
    except Exception as e:
        logger.error(f"就绪检查失败: error={str(e)}")
        data = {
            "status": "not_ready",
            "service": "live-core-service",
            "database": "unknown",
            "error": f"检查失败: {str(e)}",
            "timestamp": get_current_timestamp()
        }
        return JSONResponse(
            status_code=503,
            content=success_response(data=data)
        )

@router.get("/health/config")
async def config_check():
    """
    配置检查端点（返回非敏感配置信息）
    
    返回：
        - 200: 配置正常加载
    """
    try:
        # 从settings对象读取配置
        config_dict = {
            "environment": getattr(settings, "ENVIRONMENT", "unknown"),
            "debug": getattr(settings, "DEBUG", False),
            "database": {
                "server": getattr(settings, "DATABASE_HOST", "unknown"),
                "port": getattr(settings, "DATABASE_PORT", "unknown"),
                "database": getattr(settings, "DATABASE_NAME", "unknown")
            },
            "cors_origins": getattr(settings, "CORS_ORIGINS", []),
            "jwt_algorithm": getattr(settings, "JWT_ALGORITHM", "HS256")
        }
        
        # 脱敏处理
        sanitized_config = sanitize_config(config_dict)
        
        data = {
            "status": "configured",
            "service": "live-core-service",
            "config": sanitized_config,
            "timestamp": get_current_timestamp()
        }
        
        logger.debug("配置检查请求")
        return success_response(data=data)
        
    except Exception as e:
        logger.error(f"配置检查失败: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="配置读取失败",
                data={"reason": str(e)}
            )
        )
```

## 7. 关键注意事项

### 7.1 HTTP状态码使用

- **基础健康检查**：始终返回 `200 OK`
- **就绪检查**：
  - 数据库连接成功：返回 `200 OK`
  - 数据库连接失败：返回 `503 Service Unavailable`
- **配置检查**：始终返回 `200 OK`（配置加载失败时返回 `500 Internal Server Error`）

### 7.2 响应格式

- 所有成功响应使用 `success_response(data=...)` 包装
- 所有错误响应使用 `error_response(code, message, data)` 包装
- 响应数据必须包含 `timestamp` 字段（ISO 8601格式，UTC时区）

### 7.3 配置脱敏

- **必须**移除所有敏感字段：`password`, `secret`, `key`, `token` 等
- **可以**保留的配置：`environment`, `debug`, `database.server`, `database.port`, `database.database`, `cors_origins`, `jwt_algorithm`
- 使用递归函数处理嵌套的配置字典

### 7.4 日志记录

- **基础健康检查**：DEBUG级别日志
- **就绪检查**：
  - 成功：INFO级别日志
  - 失败：WARNING级别日志（数据库连接失败）
  - 异常：ERROR级别日志
- **配置检查**：DEBUG级别日志

### 7.5 性能要求

- **基础健康检查**：响应时间 < 1ms（无数据库查询）
- **就绪检查**：响应时间 < 100ms（包含数据库查询）
- **配置检查**：响应时间 < 10ms（配置读取）

## 8. 路由注册

在 `app/api/v1/api.py` 文件中注册路由：

```python
from app.api.v1.endpoints import health

api_router.include_router(
    health.router,
    prefix="/api/v1",
    tags=["健康检查"]
)
```

**注意**：`prefix` 在 `include_router` 中指定，不在 `APIRouter` 定义时指定。

## 9. 文件结构

生成的文件应为：

```
app/
  services/
    health_service.py  # Service层
  api/
    v1/
      endpoints/
        health.py  # API端点层
```

## 10. 测试建议

### 10.1 基础健康检查测试

- 测试返回状态码200
- 测试响应格式正确
- 测试版本号正确

### 10.2 就绪检查测试

- 测试数据库连接正常时返回200
- 测试数据库连接失败时返回503
- 测试响应格式正确

### 10.3 配置检查测试

- 测试返回状态码200
- 测试响应格式正确
- 测试敏感信息已脱敏（验证不包含 `password`, `secret` 等字段）

