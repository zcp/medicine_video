

### **最终版：高效 AI 测试代码生成提示词 (针对重构后的 Auth 模块)**

#### **1. 角色定义 (Role Definition)**

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` and mocking frameworks like `pytest-mock`. Your task is to write a robust **unit test suite** for the provided `AdminUserService` class.

#### **2. 任务目标 (Task Objective)**

Your goal is to generate the complete code for **one new test file**: `tests/test_admin_user_service.py`.

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. Testing Strategy**
* **For `Service` layer (`test_admin_user_service.py`)**: Test thoroughly using **mocking**. All external dependencies (like `crud_user` functions and the `redis_client`) **must be mocked** to test the `AdminUserService` logic in complete isolation.

**3.2. Project Structure & Code Context**
*You must generate tests based on the logic within the following application code.*
* **被测试代码 (Code to be Tested)**:
    * `@app/services/admin_user_service.py` 
* **依赖的上下文 (Dependencies & Context)**:
    * `@tests/conftest.py` (**作为测试环境和 Fixture 的来源，不可修改**)
    * `@app/models/users.py`
    * `@app/schemas/users.py`
    * `@app/crud/crud_users.py`
    * `@app/core/responses.py`


**3.3. Project Structure**

```
users/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── admin/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       # <-- 已存在 (代码如下)
│   │       └── endpoints/
│   │           └── auth.py       # <-- 已存在 (代码如下)
│   │           └── users.py       # <-- 已存在 (代码如下)
│   ├── crud/
│   │   └── crud_users.py         # <-- 已存在 (代码如下)
│   │   └── crud_user_membership.py         # <-- 已存在 (代码如下)
│   │   └── crud_membership_product.py         # <-- 已存在 (代码如下)
│   ├── models/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── users.py    # <-- 已存在 (代码如下)
│   ├── services/
│   │   └── admin_user_service.py    # <-- 已存在 (代码如下)
│   └── database.py         # <-- 已存在
|___└── tests/
        ├── conftest.py               # <-- has been generated (for test setup)
        ├── test_admin_users_service.py     # <-- To be generated
```


**3.5. 参考代码示例 (Reference Code Samples）**

*The following code is from another module in this project and has been successfully tested. You must use it as a primary reference for coding style, fixture usage, and testing patterns. The newly generated code should be consistent with these examples.*

#### **被测试函数的源代码**
* `@app/services/admin_user_service.py` 

```
"""
管理员用户服务层 - AdminUserService
封装所有管理员用户管理相关的业务逻辑，包括用户查询、更新等管理功能
"""
import logging
import uuid
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_user
from app.schemas.users import (
    UserResponse, UserUpdate, UserFilterParams
)
from app.models.users import User, UserRole, EntityStatus

logger = logging.getLogger(__name__)


# ============================================================================
# 业务异常定义
# ============================================================================

class AdminUserServiceException(Exception):
    """管理员用户服务基础异常"""
    pass


class TargetUserNotFoundError(AdminUserServiceException):
    """目标用户不存在异常"""
    def __init__(self, user_uuid: str, message: str = "用户不存在"):
        self.user_uuid = user_uuid
        super().__init__(f"{message}: {user_uuid}")


class PermissionDeniedError(AdminUserServiceException):
    """权限不足异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message)


# ============================================================================
# 管理员用户服务类
# ============================================================================

class AdminUserService:
    """管理员用户服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化管理员用户服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def list_users(self, filters: UserFilterParams, page: int, size: int) -> Dict[str, Any]:
        """
        分页、排序、筛选获取系统中的所有用户列表
        
        Args:
            filters: 筛选条件
            page: 页码
            size: 每页数量
            
        Returns:
            包含分页信息的用户列表字典
        """
        logger.info(f"开始查询用户列表: page={page}, size={size}, filters={filters}")
        
        try:
            # 1. 计算分页参数
            skip = (page - 1) * size
            
            # 2. 数据查询
            # a. 获取筛选后的用户总数
            total = await crud_user.count_with_filtering(self.db, filters=filters)
            
            # b. 获取当页的用户列表
            users = await crud_user.get_multi_with_filtering(
                self.db, skip=skip, limit=size, filters=filters
            )
            
            # 3. 序列化 - 将SQLAlchemy对象列表转换为Pydantic模型
            user_responses = []
            for user in users:
                try:
                    user_response = UserResponse.model_validate(user)
                    user_responses.append(user_response)
                except Exception as e:
                    user_id = getattr(user, 'id', 'unknown')
                    logger.warning(f"序列化用户失败: user_id={user_id}, error={e}")
                    # 跳过失败的用户，继续处理其他用户
                    continue
            
            # 4. 构建分页响应数据
            paginated_result = {
                "total": total,
                "page": page,
                "size": size,
                "items": user_responses
            }
            
            logger.info(f"成功查询用户列表: total={total}, count={len(user_responses)}")
            return paginated_result
            
        except Exception as e:
            logger.error(f"查询用户列表失败: page={page}, size={size}, error={e}")
            raise
    
    async def update_user_by_admin(self, admin_user: User, user_uuid: uuid.UUID, user_update: UserUpdate) -> User:
        """
        管理员更新指定用户的核心信息，如角色、状态
        
        Args:
            admin_user: 管理员用户对象
            user_uuid: 目标用户UUID
            user_update: 用户更新数据
            
        Returns:
            更新后的用户对象
            
        Raises:
            TargetUserNotFoundError: 目标用户不存在
            PermissionDeniedError: 权限不足
        """
        # 🔴 主动变量提取（安全红线）
        admin_user_id_for_logging = admin_user.id
        admin_role_for_logging = admin_user.role
        user_uuid_for_logging = str(user_uuid)
        
        logger.info(f"开始更新用户: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}")
        
        try:
            # 1. 用户查询 - 根据UUID获取目标用户
            user_to_update = await crud_user.get_by_uuid(self.db, public_id=user_uuid)
            if not user_to_update:
                logger.warning(f"目标用户不存在: user_uuid={user_uuid_for_logging}")
                raise TargetUserNotFoundError(user_uuid_for_logging)
            
            # 🔴 提取目标用户安全变量
            target_user_id_for_logging = user_to_update.id
            target_user_role_for_logging = user_to_update.role
            
            # 2. 权限检查 (静态) - ADMIN不能修改SUPERADMIN
            if (admin_user.role == UserRole.ADMIN and 
                user_to_update.role == UserRole.SUPERADMIN):
                logger.warning(f"管理员权限不足: admin_user_id={admin_user_id_for_logging}, target_user_role={target_user_role_for_logging}")
                raise PermissionDeniedError("管理员无权修改超级管理员")
            
            # 3. 权限检查 (动态) - 检查是否要修改角色
            update_data = user_update.model_dump(exclude_unset=True)
            if "role" in update_data:
                new_role = update_data["role"]
                if (admin_user.role == UserRole.ADMIN and 
                    new_role == UserRole.SUPERADMIN):
                    logger.warning(f"管理员无权设置超级管理员角色: admin_user_id={admin_user_id_for_logging}")
                    raise PermissionDeniedError("管理员无权设置超级管理员角色")
            
            # 4. 数据更新 - 更新用户信息
            updated_user = await crud_user.update(
                self.db, db_obj=user_to_update, obj_in=user_update
            )
            
            logger.info(f"成功更新用户: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}")
            return updated_user
            
        except (TargetUserNotFoundError, PermissionDeniedError):
            raise
        except Exception as e:
            logger.error(f"更新用户失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}, error={e}")
            raise 
```
-----


#### **4. 代码生成具体要求 (Specific Code Generation Instructions) - REVISED FOR USERS & AUTH**
##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**:
    1.  你的任务**不包括**生成或修改 `conftest.py`。
    2.  你**必须假设**一个已存在的 `conftest.py` 文件已经提供了 `db_session` (异步数据库会话) 和 `async_client` (异步HTTP客户端) 这两个 fixtures，并且它们可以正常工作。

---
---
#### **4. 代码生成具体要求 (Specific Code Generation Instructions)**

##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**: 你的任务**不包括**生成或修改 `conftest.py`。你**必须假设**它已存在并提供 `db_session` fixture。

##### **4.2. 测试数据隔离 (Test Data Isolation)**
* **指令**: 所有测试用例在准备数据时，**必须**使用 `uuid` 生成随机且唯一的 `username`, `email` 等字段，以防止测试间冲突。

##### **4.3. `tests/test_admin_user_service.py` - Service层单元测试**

* **文件名**: `tests/test_admin_user_service.py`
* **职责**: 对 `app/services/admin_user_service.py` 中的每个公共方法进行详细的、隔离的单元测试。
* **核心要求**: **必须使用 `mocker` fixture** 来模拟所有外部依赖。

* **需实现的测试用例**:

    1.  **`test_list_users_success`**:
        * **准备 (Arrange)**:
            * a. 创建 `AdminUserService` 实例 `admin_user_service`。
            * b. 创建一个模拟的 `User` 对象列表 `mock_users`。
            * c. Mock `crud_user.count_with_filtering` 使其返回 `len(mock_users)`。
            * d. Mock `crud_user.get_multi_with_filtering` 使其返回 `mock_users`。
        * **执行 (Act)**: 调用 `admin_user_service.list_users()`。
        * **断言 (Assert)**:
            * a. 断言 `crud_user.count_with_filtering` 和 `crud_user.get_multi_with_filtering` 都被以正确的 `filters` 和分页参数调用。
            * b. 断言返回的字典中 `items` 列表的长度与模拟数据一致，且 `total` 字段的值也正确。

    2.  **`test_update_user_by_admin_success`**:
        * **准备**:
            * a. 创建 `admin_user_service` 实例。
            * b. 创建一个 `role` 为 `ADMIN` 的模拟管理员 `mock_admin`。
            * c. 创建一个 `role` 为 `REGULAR` 的模拟目标用户 `mock_target_user`。
            * d. 创建一个 `schemas.UserUpdate` 对象 `user_update`，其中包含新的 `role` (`MODERATOR`) 和 `status` (`BANNED`)。
            * e. Mock `crud_user.get_by_uuid` 使其返回 `mock_target_user`。
            * f. Mock `crud_user.update` 方法。
        * **执行**: 调用 `admin_user_service.update_user_by_admin(admin_user=mock_admin, user_uuid=..., user_update=user_update)`。
        * **断言**:
            * a. 断言 `crud_user.update` **被调用了一次**。
            * b. **验证数据库字段**: 检查传递给 `update` 的 `obj_in` 参数，断言其 `role` 和 `status` 的值与 `user_update` 中的新值一致。

    3.  **`test_update_user_by_admin_fails_if_user_not_found`**:
        * **准备**: Mock `crud_user.get_by_uuid` 使其返回 `None`。
        * **执行与断言**: 使用 `with pytest.raises(TargetUserNotFoundError):` 来包裹对 `admin_user_service.update_user_by_admin()` 的调用。

    4.  **`test_update_user_by_admin_fails_if_admin_updates_superadmin`**:
        * **准备**:
            * a. 创建一个 `role` 为 `ADMIN` 的模拟管理员 `mock_admin`。
            * b. 创建一个 `role` 为 `SUPERADMIN` 的模拟目标用户 `mock_superadmin`。
            * c. Mock `crud_user.get_by_uuid` 使其返回 `mock_superadmin`。
        * **执行与断言**: 使用 `with pytest.raises(PermissionDeniedError):` 来包裹对 `admin_user_service.update_user_by_admin(admin_user=mock_admin, ...)` 的调用。

#### **5. 最终交付 (Final Deliverable)**

Please generate the complete, runnable Python code for the following **one new file**:
1.  `tests/test_admin_user_service.py`