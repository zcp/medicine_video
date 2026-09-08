# 专题功能banner上传功能 - 增量测试代码生成提示词

## 1. 角色定义 (Role Definition)

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` for asynchronous code, `unittest.mock` for mocking, and FastAPI's `AsyncClient` for integration testing. Your task is to write **incremental tests** for the newly added **Topic Banner Upload Feature**.

## 2. 任务目标 (Task Objective)

Your goal is to **ADD NEW TESTS** to existing test files for the banner upload functionality:

**⚠️ 核心原则：增量测试与最小修改**

1. **DO NOT MODIFY** existing test files except to **ADD** new test functions
2. **DO NOT MODIFY** `conftest.py` or any test configuration
3. **DO NOT CHANGE** existing test functions or fixtures
4. **ONLY ADD** new test functions for banner upload functionality
5. Follow the exact same patterns and conventions as existing tests

### 2.1. 测试文件修改清单

**需要添加测试的文件：**

1. **`tests/unit/test_service_topic.py`**
   - ✅ 添加 1 个新的测试类：`TestTopicBannerManagement`
   - ✅ 添加 6 个新的测试函数（成功、失败、权限场景）
   - ❌ 不修改现有的测试类和函数

2. **`tests/integration/test_api_topic.py`**
   - ✅ 添加 1 个新的测试类：`TestTopicBannerAPI`
   - ✅ 添加 5 个新的测试函数（成功、失败、权限场景）
   - ❌ 不修改现有的测试类、函数和fixtures

**不需要修改的文件：**
- ❌ `tests/conftest.py` - 保持完全不变
- ❌ 现有的任何测试文件中的现有测试函数

## 3. 核心上下文信息 (Core Context Information)

### 3.1. 新增功能概览

本次新增的banner上传功能包括以下几层：

#### **CRUD层 (`app/crud/topic.py`)**
- **新增方法**: `update_banner_url(db, topic_id, banner_url) -> Optional[Topic]`
  - 功能：更新专题的banner_url字段
  - 参数：数据库会话、专题ID、新的banner URL
  - 返回：更新后的Topic对象或None

#### **Service层 (`app/services/topic_service.py`)**
- **新增方法**: `upload_topic_banner(self, topic_id, file, user_id) -> Topic`
  - 功能：上传专题横幅图片
  - 业务逻辑：
    1. 验证专题存在性
    2. 验证用户权限（只有创建者可上传）
    3. 删除旧横幅文件（如果存在）
    4. 保存新文件
    5. 更新数据库banner_url
  - 异常：`TopicNotFoundException`, `TopicPermissionDeniedException`

#### **FileHandler (`app/core/file_handler.py`)**
- **新增方法1**: `generate_banner_path(topic_id, extension) -> Tuple[str, str]`
  - 功能：生成横幅存储路径
  - 返回：(文件系统路径, URL路径)

- **新增方法2**: `save_banner_file(file, topic_id) -> str`
  - 功能：保存横幅文件
  - 验证：文件类型（PNG, JPG）、大小（10MB以内）
  - 返回：URL路径

- **新增方法3**: `delete_old_banner(banner_url) -> None`
  - 功能：删除旧横幅文件
  - 静默失败（只记录警告）

#### **API端点层 (`app/api/v1/endpoints/topic.py`)**
- **新增端点**: `POST /api/v1/topics/{topic_id}/banner`
  - 认证：需要（get_current_user）
  - 请求：`multipart/form-data`，包含 `file` 字段
  - 成功响应：200，包含 `topic_id` 和 `banner_url`
  - 错误响应：
    - 404: 专题不存在 (code: 2001)
    - 403: 权限不足 (code: 2003)
    - 400: 文件格式或大小错误 (code: 4002)
    - 500: 服务器错误 (code: 1002)

### 3.2. 测试数据规范

#### **文件上传测试数据**

```python
from io import BytesIO
from PIL import Image

def create_test_image(width=100, height=100, format='PNG') -> BytesIO:
    """创建测试图片"""
    image = Image.new('RGB', (width, height), color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer

def create_oversized_image() -> BytesIO:
    """创建超过10MB的测试图片"""
    # 创建足够大的图片（例如5000x5000）
    image = Image.new('RGB', (5000, 5000), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='PNG', quality=100)
    buffer.seek(0)
    return buffer
```

#### **存储路径格式**

- 格式：`/media/topics/{topic_id}/banner_{timestamp}.{ext}`
- 示例：`/media/topics/a1b2c3d4-e5f6-7890-abcd-ef1234567890/banner_1729500605.jpg`

## 4. Service层测试规范 (tests/unit/test_service_topic.py)

### 4.1. 测试组织结构

**在文件末尾添加新的测试类：**

```python
# ==================== 新增：专题横幅管理测试 ====================

class TestTopicBannerManagement:
    """专题横幅上传功能测试（新增）"""
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_success(self, mocker):
        """测试成功上传横幅"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_topic_not_found(self, mocker):
        """测试专题不存在"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_permission_denied(self, mocker):
        """测试权限不足"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_deletes_old_file(self, mocker):
        """测试删除旧横幅文件"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_file_validation_fails(self, mocker):
        """测试文件验证失败"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_update_url_fails(self, mocker):
        """测试数据库更新失败"""
        pass
```

### 4.2. Mock策略（Service层）

**⚠️ 关键：正确的Mock路径**

Service层导入方式：
```python
from app.crud import topic as crud_topic
from app.core.file_handler import FileHandler
```

Service层调用：
```python
topic = await crud_topic.get(self.db, topic_id)  # 使用 crud_topic
banner_url = await FileHandler.save_banner_file(file=file, topic_id=topic_id)
```

**测试中的Mock路径：**
```python
# ✅ 正确：Mock CRUD原始路径
mocker.patch("app.crud.topic.get", return_value=mock_topic, new_callable=AsyncMock)
mocker.patch("app.crud.topic.update_banner_url", return_value=updated_topic, new_callable=AsyncMock)

# ✅ 正确：Mock FileHandler类方法
mocker.patch("app.core.file_handler.FileHandler.save_banner_file", return_value="/media/topics/xxx/banner_123.jpg", new_callable=AsyncMock)
mocker.patch("app.core.file_handler.FileHandler.delete_old_banner")

# ❌ 错误：使用别名路径
# mocker.patch("app.crud_topic.get")  # 错误！
```

### 4.3. Service层测试用例详细规格

#### **Test 1: `test_upload_topic_banner_success`**

```python
@pytest.mark.asyncio
async def test_upload_topic_banner_success(self, mocker):
    """
    测试成功上传专题横幅
    
    验证点:
    1. 调用 crud_topic.get() 验证专题存在
    2. 验证用户权限通过
    3. 调用 FileHandler.save_banner_file() 保存文件
    4. 调用 crud_topic.update_banner_url() 更新数据库
    5. 返回更新后的Topic对象
    """
    # Arrange
    from app.services.topic_service import TopicService
    from app.models.topic import Topic, TopicStatus
    from fastapi import UploadFile
    import uuid
    
    mock_db = mocker.Mock()
    user_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    
    # 创建Mock专题对象
    mock_topic = Topic(
        id=topic_id,
        user_id=user_id,  # ✅ 相同的用户ID，权限检查通过
        title="Test Topic",
        description="Test Description",
        banner_url=None,  # 初始没有横幅
        status=TopicStatus.DRAFT
    )
    
    # 创建Mock文件
    mock_file = mocker.Mock(spec=UploadFile)
    mock_file.filename = "test_banner.png"
    
    # 更新后的专题对象
    updated_topic = Topic(
        id=topic_id,
        user_id=user_id,
        title="Test Topic",
        description="Test Description",
        banner_url="/media/topics/xxx/banner_123.png",  # ✅ 已更新
        status=TopicStatus.DRAFT
    )
    
    # Mock CRUD函数
    mock_get = mocker.patch(
        "app.crud.topic.get",
        new_callable=AsyncMock,
        return_value=mock_topic
    )
    
    mock_update_banner_url = mocker.patch(
        "app.crud.topic.update_banner_url",
        new_callable=AsyncMock,
        return_value=updated_topic
    )
    
    # Mock FileHandler方法
    mock_save_banner = mocker.patch(
        "app.core.file_handler.FileHandler.save_banner_file",
        new_callable=AsyncMock,
        return_value="/media/topics/xxx/banner_123.png"
    )
    
    # Act
    service = TopicService(mock_db)
    result = await service.upload_topic_banner(
        topic_id=topic_id,
        file=mock_file,
        user_id=user_id
    )
    
    # Assert
    mock_get.assert_called_once_with(mock_db, topic_id)
    mock_save_banner.assert_called_once_with(file=mock_file, topic_id=topic_id)
    mock_update_banner_url.assert_called_once_with(
        db=mock_db,
        topic_id=topic_id,
        banner_url="/media/topics/xxx/banner_123.png"
    )
    assert result == updated_topic
    assert result.banner_url == "/media/topics/xxx/banner_123.png"
```

#### **Test 2: `test_upload_topic_banner_topic_not_found`**
- **Mock**: `crud_topic.get()` 返回 `None`
- **验证**: 抛出 `TopicNotFoundException`
- **验证**: FileHandler方法未被调用

#### **Test 3: `test_upload_topic_banner_permission_denied`**
- **Mock**: `crud_topic.get()` 返回专题（不同的user_id）
- **验证**: 抛出 `TopicPermissionDeniedException`
- **验证**: FileHandler方法未被调用

#### **Test 4: `test_upload_topic_banner_deletes_old_file`**
- **Mock**: 专题已有旧的banner_url
- **Mock**: `FileHandler.delete_old_banner()` 被调用
- **验证**: 删除旧文件的方法被正确调用
- **验证**: 保存新文件的方法被调用

#### **Test 5: `test_upload_topic_banner_file_validation_fails`**
- **Mock**: `FileHandler.save_banner_file()` 抛出 `HTTPException(400)`
- **验证**: 异常被正确传播
- **验证**: 数据库更新方法未被调用

#### **Test 6: `test_upload_topic_banner_update_url_fails`**
- **Mock**: `crud_topic.update_banner_url()` 返回 `None`
- **验证**: 抛出 `Exception("更新横幅URL失败")`

### 4.4. Service层测试模板

```python
@pytest.mark.asyncio
async def test_upload_topic_banner_scenario(self, mocker):
    """
    测试描述
    
    验证点:
    1. 验证点1
    2. 验证点2
    """
    # Arrange
    from app.services.topic_service import TopicService
    from app.models.topic import Topic
    from fastapi import UploadFile
    import uuid
    
    mock_db = mocker.Mock()
    mock_file = mocker.Mock(spec=UploadFile)
    
    # Mock CRUD和FileHandler方法（使用正确的路径）
    mocker.patch("app.crud.topic.get", ...)
    mocker.patch("app.core.file_handler.FileHandler.save_banner_file", ...)
    
    # Act
    service = TopicService(mock_db)
    # 执行测试或验证异常
    
    # Assert
    # 验证Mock被正确调用
```

## 5. API端点测试规范 (tests/integration/test_api_topic.py)

### 5.1. 测试组织结构

**在文件末尾添加新的测试类：**

```python
# ==================== 新增：专题横幅上传API测试 ====================

class TestTopicBannerAPI:
    """专题横幅上传API测试（新增）"""
    
    @pytest.mark.asyncio
    async def test_upload_banner_success(self, topic_client):
        """测试成功上传横幅"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_banner_topic_not_found(self, topic_client):
        """测试专题不存在"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_banner_permission_denied(self, topic_client):
        """测试权限不足"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_banner_invalid_file_type(self, topic_client):
        """测试无效文件类型"""
        pass
    
    @pytest.mark.asyncio
    async def test_upload_banner_oversized_file(self, topic_client):
        """测试文件过大"""
        pass
```

### 5.2. API测试关键点

**⚠️ 重要：使用现有的 `topic_client` fixture**

```python
@pytest.mark.asyncio
async def test_upload_banner_success(self, topic_client):  # ✅ 使用现有fixture
    """测试成功上传横幅"""
    async for client, app, db in topic_client:  # ✅ 解包三个对象
        from app.core.deps import get_current_user
        from io import BytesIO
        from PIL import Image
        
        # Step 1: Mock认证
        user_id = uuid.uuid4()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": str(user_id),
            "username": "testuser"
        }
        
        try:
            # Step 2: 创建测试专题
            topic = await create_test_topic(db, user_id)
            
            # Step 3: 创建测试图片
            image = Image.new('RGB', (100, 100), color='red')
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Step 4: 上传横幅（使用 multipart/form-data）
            files = {"file": ("test_banner.png", buffer, "image/png")}
            response = await client.post(
                f"/api/v1/topics/{topic.id}/banner",
                files=files
            )
            
            # Step 5: 断言HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "success"
            assert "data" in data
            
            # Step 6: 断言响应数据
            banner_data = data["data"]
            assert banner_data["topic_id"] == str(topic.id)
            assert banner_data["banner_url"] is not None
            assert banner_data["banner_url"].startswith("/media/topics/")
            
            # Step 7: 断言数据库状态
            from sqlalchemy import select
            from app.models.topic import Topic
            
            stmt = select(Topic).where(Topic.id == topic.id)
            result = await db.execute(stmt)
            updated_topic = result.scalar_one_or_none()
            
            assert updated_topic is not None
            assert updated_topic.banner_url is not None
            assert updated_topic.banner_url == banner_data["banner_url"]
            
        finally:
            # ✅ 清理依赖覆盖
            app.dependency_overrides.clear()
```

### 5.3. API端点测试用例详细规格

#### **Test 1: `test_upload_banner_success`**
- **前置条件**: 创建专题（user_A）
- **操作**: user_A上传PNG图片
- **验证**:
  1. HTTP状态码 200
  2. 响应结构正确（code, message, data, timestamp）
  3. 业务码 200
  4. 返回 topic_id 和 banner_url
  5. banner_url 格式正确
  6. 数据库中 banner_url 已更新

#### **Test 2: `test_upload_banner_topic_not_found`**
- **操作**: 使用不存在的topic_id上传
- **验证**:
  1. HTTP状态码 404
  2. 业务码 2001
  3. data包含 resource="Topic"

#### **Test 3: `test_upload_banner_permission_denied`**
- **前置条件**: 创建专题（user_A）
- **操作**: user_B尝试上传
- **验证**:
  1. HTTP状态码 403
  2. 业务码 2003
  3. data包含权限错误信息

#### **Test 4: `test_upload_banner_invalid_file_type`**
- **操作**: 上传非图片文件（如.txt）
- **验证**:
  1. HTTP状态码 400
  2. 业务码 4002
  3. data包含文件类型错误信息

#### **Test 5: `test_upload_banner_oversized_file`**
- **操作**: 上传超过10MB的图片
- **验证**:
  1. HTTP状态码 400
  2. 业务码 4002
  3. data包含文件大小错误信息

### 5.4. API测试辅助函数

**在文件末尾添加新的辅助函数：**

```python
# ==================== 辅助函数：文件上传测试 ====================

def create_test_image(width: int = 100, height: int = 100, format: str = 'PNG') -> BytesIO:
    """
    创建测试图片
    
    Args:
        width: 图片宽度
        height: 图片高度
        format: 图片格式（PNG, JPEG）
        
    Returns:
        BytesIO: 图片二进制流
    """
    from PIL import Image
    from io import BytesIO
    
    image = Image.new('RGB', (width, height), color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def create_oversized_image() -> BytesIO:
    """
    创建超过10MB的测试图片
    
    Returns:
        BytesIO: 图片二进制流
    """
    from PIL import Image
    from io import BytesIO
    
    # 创建足够大的图片（例如5000x5000）
    image = Image.new('RGB', (5000, 5000), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='PNG', quality=100)
    buffer.seek(0)
    return buffer


def create_invalid_file() -> BytesIO:
    """
    创建无效的文件（非图片）
    
    Returns:
        BytesIO: 文本文件二进制流
    """
    from io import BytesIO
    
    buffer = BytesIO(b"This is not an image file")
    buffer.seek(0)
    return buffer
```

## 6. 代码质量要求

### 6.1. 导入语句规范

**Service层测试新增导入：**
```python
# 在 tests/unit/test_service_topic.py 顶部已有导入的基础上，确保包含：
from fastapi import UploadFile  # ✅ 用于Mock文件对象
```

**API端点测试新增导入：**
```python
# 在 tests/integration/test_api_topic.py 顶部已有导入的基础上，确保包含：
from io import BytesIO  # ✅ 用于创建测试图片
from PIL import Image  # ✅ 用于生成图片（需要 pip install Pillow）
```

### 6.2. 测试命名规范

```python
# ✅ 正确：清晰描述测试场景
test_upload_topic_banner_success
test_upload_topic_banner_topic_not_found
test_upload_topic_banner_permission_denied
test_upload_banner_invalid_file_type

# ❌ 错误：命名不清晰
test_banner_1
test_upload
test_error
```

### 6.3. 断言消息规范

```python
# ✅ 正确：提供详细的错误消息
assert response.status_code == 200, \
    f"期望HTTP状态码200，实际 {response.status_code}"
assert data["code"] == 200, \
    f"期望业务码200，实际 {data['code']}"
assert banner_url.startswith("/media/topics/"), \
    f"横幅URL格式错误: {banner_url}"
```

### 6.4. 文档字符串规范

```python
@pytest.mark.asyncio
async def test_upload_topic_banner_success(self, mocker):
    """
    测试成功上传专题横幅
    
    验证点:
    1. 调用 crud_topic.get() 验证专题存在
    2. 验证用户权限通过（user_id匹配）
    3. 调用 FileHandler.save_banner_file() 保存文件
    4. 调用 crud_topic.update_banner_url() 更新数据库
    5. 返回更新后的Topic对象，banner_url不为空
    """
```

## 7. 最终交付 (Final Deliverable)

Please generate the **INCREMENTAL CODE** to be **ADDED** to the existing test files:

### 7.1. Service层测试（增量代码）

**文件**: `tests/unit/test_service_topic.py`

**操作**: 在文件末尾**添加**以下内容：

```python
# ==================== 新增：专题横幅管理测试 ====================

class TestTopicBannerManagement:
    """专题横幅上传功能测试（新增）"""
    
    # 在这里生成 6 个测试函数
```

**要求**:
- ✅ 在现有测试类之后添加，不修改现有代码
- ✅ 包含完整的 6 个测试函数
- ✅ 每个测试函数包含详细的文档字符串
- ✅ 使用正确的Mock路径
- ✅ 遵循现有测试的代码风格

### 7.2. API端点测试（增量代码）

**文件**: `tests/integration/test_api_topic.py`

**操作**: 在文件末尾**添加**以下内容：

```python
# ==================== 新增：专题横幅上传API测试 ====================

class TestTopicBannerAPI:
    """专题横幅上传API测试（新增）"""
    
    # 在这里生成 5 个测试函数


# ==================== 新增：辅助函数 - 文件上传测试 ====================

def create_test_image(...):
    """创建测试图片"""
    pass

def create_oversized_image():
    """创建超过10MB的测试图片"""
    pass

def create_invalid_file():
    """创建无效的文件"""
    pass
```

**要求**:
- ✅ 在现有测试类之后添加，不修改现有代码
- ✅ 包含完整的 5 个测试函数
- ✅ 包含 3 个文件上传辅助函数
- ✅ 使用现有的 `topic_client` fixture
- ✅ 所有测试使用 `async for client, app, db in topic_client:` 模式
- ✅ 所有测试使用 try-finally 清理 `dependency_overrides`
- ✅ 遵循现有测试的代码风格

### 7.3. 依赖项检查

**确保已安装必要的依赖：**

```bash
pip install Pillow  # 用于生成测试图片
```

## 8. 快速检查清单

生成增量测试代码后，请确认：

### 8.1. Service层测试
- [ ] 添加了 `TestTopicBannerManagement` 类
- [ ] 包含 6 个测试函数
- [ ] 所有测试使用 `@pytest.mark.asyncio` 装饰器
- [ ] Mock路径使用 `app.crud.topic.*` 和 `app.core.file_handler.FileHandler.*`
- [ ] 测试覆盖：成功、失败、权限、文件验证场景
- [ ] 没有修改现有的测试代码

### 8.2. API端点测试
- [ ] 添加了 `TestTopicBannerAPI` 类
- [ ] 包含 5 个测试函数
- [ ] 添加了 3 个辅助函数（create_test_image, create_oversized_image, create_invalid_file）
- [ ] 所有测试使用 `topic_client` fixture
- [ ] 所有测试使用 `async for client, app, db in topic_client:` 模式
- [ ] 所有测试使用 try-finally 清理 `dependency_overrides`
- [ ] 测试覆盖：成功、404、403、400错误场景
- [ ] 没有修改现有的测试代码和fixtures

### 8.3. 代码规范
- [ ] 所有新增代码使用 4 个空格缩进
- [ ] 每个测试函数之间空 2 行
- [ ] 所有测试包含详细的文档字符串
- [ ] 所有断言包含清晰的错误消息
- [ ] 遵循现有测试的命名和组织风格

### 8.4. 功能覆盖
- [ ] 测试文件上传成功场景
- [ ] 测试专题不存在场景
- [ ] 测试权限不足场景
- [ ] 测试文件类型验证
- [ ] 测试文件大小验证
- [ ] 测试删除旧文件逻辑
- [ ] 测试数据库更新

---

## 9. 重要提醒

### 9.1. 最小修改原则

**✅ 允许的操作：**
- 在测试文件末尾添加新的测试类
- 在测试文件末尾添加新的辅助函数
- 在现有导入语句中添加新的导入（如果需要）

**❌ 禁止的操作：**
- 修改现有的测试类和函数
- 修改 `conftest.py`
- 修改现有的fixture定义
- 删除或重构现有的测试代码
- 修改现有的辅助函数

### 9.2. 测试隔离原则

- ✅ 每个测试必须能独立运行
- ✅ 测试不依赖执行顺序
- ✅ 测试数据使用随机生成（faker, uuid）
- ✅ 每个测试后清理状态（dependency_overrides）

### 9.3. Mock一致性原则

- ✅ Service层测试：Mock CRUD和FileHandler
- ✅ API端点测试：真实调用Service层，使用真实数据库
- ✅ 使用正确的Mock路径（原始模块路径，不是别名）
- ✅ 异步函数使用 `AsyncMock`

---

**现在，请开始生成增量测试代码！记住：只添加新代码，不修改现有代码！**

