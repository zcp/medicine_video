# 健康检查模块代码生成提示词 - 第一阶段（CRUD层）

## 1. 角色定义 (Role Definition)

你是一名精通"学院派"架构的资深 Python 后端工程师，擅长异步 SQLAlchemy 2.0。你的任务是编写纯粹的、高性能的数据访问层（CRUD）代码。

## 2. 任务目标 (Task Objective)

你的任务是为**健康检查模块**生成 `app/crud/health.py` 文件，封装数据库连接测试操作。

**⚠️ 特殊说明**：
- 健康检查模块**不涉及数据库表**，只有数据库连接测试功能
- CRUD层只需要提供数据库连接测试函数
- 无需实现表的增删改查操作

## 3. 核心架构约束 (学院派)

  * **职责**：CRUD 层**只负责数据访问**，不包含任何业务逻辑。
  * **[关键] 日志记录**: 
      * **必须**在异常处理中记录 `logger.error`。
      * **必须**遵循"安全异步异常处理"规范：在 `try` 块之前提取所有用于 `except` 块日志记录的变量。

## 4. 核心上下文信息

健康检查模块**不涉及数据库表**，只需要测试数据库连接状态。

## 5. 必须实现的 CRUD 函数

### `check_database_connection(db: AsyncSession) -> bool`

**功能**: 测试数据库连接是否正常

**实现要求**:
1. 执行简单的查询：`SELECT 1`
2. 如果查询成功，返回 `True`
3. 如果查询失败（捕获异常），记录ERROR日志，返回 `False`

**代码模板**:

```python
async def check_database_connection(db: AsyncSession) -> bool:
    """
    测试数据库连接是否正常
    
    Args:
        db: 数据库会话
    
    Returns:
        bool: True表示连接正常，False表示连接失败
    """
    # 提取日志变量（安全异步异常处理）
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        logger.debug("数据库连接测试成功")
        return True
        
    except Exception as e:
        # 记录错误日志
        logger.error(
            f"数据库连接测试失败: error={str(e)}, error_type={type(e).__name__}"
        )
        return False
```

**注意事项**:
- 使用 `text("SELECT 1")` 执行原始SQL查询
- 捕获所有异常（`Exception`），因为可能是各种数据库连接错误
- 记录详细的错误信息，包括异常类型和消息
- 返回布尔值，不抛出异常（异常处理在API层进行）

## 6. 文件结构

生成的文件应为：

```
app/
  crud/
    health.py  # 包含数据库连接测试函数
```

**代码组织**:
- 可以使用一个简单的函数：`check_database_connection`
- 或者使用类封装：`class CRUDHealth`，包含 `check_database_connection` 方法
- 推荐使用函数式写法，因为只有一个函数，无需封装成类

## 7. 完整代码示例

```python
"""
健康检查模块的 CRUD 层 (学院派)
职责：数据库连接测试
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def check_database_connection(db: AsyncSession) -> bool:
    """
    测试数据库连接是否正常
    
    Args:
        db: 数据库会话
    
    Returns:
        bool: True表示连接正常，False表示连接失败
    """
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        logger.debug("数据库连接测试成功")
        return True
        
    except Exception as e:
        # 记录错误日志（不抛出异常，由调用方处理）
        logger.error(
            f"数据库连接测试失败: error={str(e)}, error_type={type(e).__name__}"
        )
        return False
```

## 8. 注意事项

1. **无事务处理**: 这是一个只读查询，不涉及事务提交/回滚
2. **异常处理**: 捕获所有异常，返回布尔值，不抛出异常
3. **日志记录**: 记录详细的错误信息，便于调试
4. **性能**: 查询应尽可能快速（使用 `SELECT 1` 这样的轻量级查询）
5. **超时处理**: 如果数据库连接超时，异常会被捕获并返回 `False`

