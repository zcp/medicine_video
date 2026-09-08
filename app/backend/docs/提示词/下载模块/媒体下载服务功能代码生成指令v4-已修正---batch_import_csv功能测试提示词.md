# 媒体下载服务 - CSV批量导入功能测试代码生成提示词

## 一、角色定义 (Role Definition)

你是一名资深的 Python 测试工程师，精通使用 `pytest` 进行自动化测试。你擅长编写覆盖全面、健壮可靠的单元测试和集成测试，特别是针对同步服务层方法和 FastAPI 异步接口的测试。

**重要说明**：
1. **服务层测试**：`download_service.py` 中的所有方法都是**同步方法**，因此服务层测试必须使用**同步测试函数**（`def test_...`），使用同步数据库会话（`sync_db_session`）。
2. **API接口测试**：API 接口是异步的，必须使用**异步测试函数**（`async def test_...`）和 `@pytest.mark.asyncio` 装饰器。
3. **辅助函数**：所有辅助函数（如 `generate_csv_content`）应直接定义在测试文件中，**不要修改 `conftest.py`**。

## 二、任务目标 (Task Objective)

你的目标是为**CSV批量导入下载任务功能**编写完整的测试代码，包括：
1. **服务层方法测试** (`batch_import_tasks_from_csv`)
2. **API接口测试** (`POST /api/v1/download/tasks/batch-import`)

测试代码必须：
- 覆盖所有成功和失败场景
- 验证错误隔离机制（单行失败不中断）
- 测试去重、自动启动等可选功能
- 验证批量提交性能
- 包含边界条件和异常场景测试

## 三、核心上下文信息 (Core Context Information)

### 3.1 被测功能概述

**服务层方法签名**:
```python
def batch_import_tasks_from_csv(
    self,
    file_content: bytes,
    user_id: uuid.UUID,
    skip_duplicates: bool = False,
    auto_start: bool = False
) -> Dict:
```

**API端点签名**:
```python
@router.post("/tasks/batch-import", response_model=ResponseModel[BatchImportResult])
async def batch_import_tasks(
    file: UploadFile = File(...),
    skip_duplicates: bool = Form(False),
    auto_start: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
```

### 3.2 核心功能特性

#### 3.2.1 CSV格式要求
- **编码**: UTF-8
- **分隔符**: 逗号
- **必需列**: `liveroom_id`, `resource_url`, `resource_type`
- **可选列**: `liveroom_title`, `liveroom_url`
- **最大行数**: 1000行（不含表头）
- **最大文件大小**: 10MB

#### 3.2.2 关键特性
1. **错误隔离**: 单行失败不影响其他行
2. **去重功能**: 通过`skip_duplicates`参数控制
3. **自动启动**: 通过`auto_start`参数控制
4. **批量提交**: 每100行提交一次事务
5. **详细统计**: 返回成功/失败/跳过的详细信息

### 3.3 响应状态码（统一响应模式）

**重要**：根据统一响应规范，所有API接口都返回 **HTTP 200**，业务状态码在响应体的 `code` 字段中。

| HTTP状态码 | 响应体code字段 | 场景 |
|:---|:---|:---|
| 200 | 201 | 全部成功 |
| 200 | 207 | 部分成功 |
| 200 | 400 | 文件格式错误、全部失败 |
| 200 | 413 | 文件过大 |
| 200 | 500 | 数据库错误 |

**测试断言示例**：
```python
assert response.status_code == 200  # HTTP状态码固定为200
response_data = response.json()
assert response_data["code"] == 201  # 业务状态码在body的code字段
```

### 3.4 数据库表结构

**download_tasks**:
- `id` (UUID): 主键
- `user_id` (UUID): 用户ID
- `liveroom_id` (String): 直播间ID
- `resource_url` (String): 资源URL
- `resource_type` (String): 资源类型（hls/mp4/image）
- `status` (String): 任务状态
- `created_at` (DateTime): 创建时间

## 四、测试用例详细规范

### 4.1 服务层方法测试 (`test_download_service_batch_import.py`)

#### 4.1.1 成功场景测试

##### **Test Case 1: 全部成功导入**
```python
def test_batch_import_all_success(self, sync_db_session):
    """测试所有行都成功导入"""
```

**测试目标**: 验证正常CSV文件的批量导入功能

**准备 (Arrange)**:
1. 创建测试用户（`user_id = uuid.uuid4()`）
2. 准备包含10行有效数据的CSV内容（使用 `generate_csv_content` 辅助函数）：
   ```csv
   liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
   1234567890,直播间1,https://example.com/room1,https://example.com/video1.m3u8,hls
   1234567891,直播间2,https://example.com/room2,https://example.com/video2.mp4,mp4
   ...
   ```
3. 将CSV内容编码为UTF-8字节

**执行 (Act)**:
```python
service = DownloadService(sync_db_session)
result = service.batch_import_tasks_from_csv(
    file_content=csv_bytes,
    user_id=test_user_id,
    skip_duplicates=False,
    auto_start=False
)
```

**注意**：
- 使用 `sync_db_session` fixture（同步数据库会话）
- **不使用** `async`/`await` 语法
- **不使用** `@pytest.mark.asyncio` 装饰器

**断言 (Assert)**:
1. **结果统计验证**:
   ```python
   assert result["total"] == 10
   assert result["success"] == 10
   assert result["failed"] == 0
   assert result["skipped"] == 0
   assert len(result["created_task_ids"]) == 10
   assert len(result["failed_rows"]) == 0
   assert result["processing_time"] > 0
   ```

2. **数据库状态验证**:
   ```python
   tasks = sync_db_session.query(DownloadTask).filter(
       DownloadTask.user_id == test_user_id
   ).all()
   assert len(tasks) == 10
   for task in tasks:
       assert task.status == TaskStatus.PENDING
       assert task.resource_type in ["hls", "mp4", "image"]
   ```

##### **Test Case 2: 部分成功导入（错误隔离验证）**
```python
def test_batch_import_partial_success_error_isolation(self, sync_db_session):
    """测试错误隔离机制：部分行失败不影响其他行"""
```

**测试目标**: 验证单行错误不中断整体流程

**准备**:
1. 准备包含10行数据的CSV，其中：
   - 第3行：`liveroom_id`长度不足（如 "123"）
   - 第5行：`resource_type`无效（如 "invalid"）
   - 第8行：缺少必填字段`resource_url`
   - 其余7行正常

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
1. **结果统计**:
   ```python
   assert result["total"] == 10
   assert result["success"] == 7
   assert result["failed"] == 3
   assert len(result["failed_rows"]) == 3
   ```

2. **失败行详细信息**:
   ```python
   # 验证第3行错误
   failed_row_3 = next(r for r in result["failed_rows"] if r["row"] == 3)
   assert "liveroom_id长度必须在10-20之间" in failed_row_3["error"]
   
   # 验证第5行错误
   failed_row_5 = next(r for r in result["failed_rows"] if r["row"] == 5)
   assert "无效的resource_type" in failed_row_5["error"]
   
   # 验证第8行错误
   failed_row_8 = next(r for r in result["failed_rows"] if r["row"] == 8)
   assert "缺少必填字段" in failed_row_8["error"]
   ```

3. **数据库状态**:
   ```python
   tasks = sync_db_session.query(DownloadTask).filter(
       DownloadTask.user_id == test_user_id
   ).all()
   assert len(tasks) == 7  # 只有成功的7条
   ```

##### **Test Case 3: 去重功能测试（skip_duplicates=True）- 组合去重**
```python
def test_batch_import_with_skip_duplicates_enabled(self, sync_db_session):
    """测试去重功能：重复的任务组合（resource_url + liveroom_id + liveroom_title）被跳过"""
```

**测试目标**: 验证基于组合键（`resource_url + liveroom_id + liveroom_title`）的去重逻辑

**准备**:
1. 在数据库中预先创建2个任务：
   - 任务1: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567890"`, `liveroom_title="直播间A"`
   - 任务2: `resource_url="https://example.com/video2.mp4"`, `liveroom_id="1234567891"`, `liveroom_title="直播间B"`
2. 准备CSV文件，包含5行数据：
   - 第1行（重复）: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567890"`, `liveroom_title="直播间A"` - **完全匹配任务1**
   - 第2行（新任务）: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567892"`, `liveroom_title="直播间C"` - **相同URL但不同直播间**
   - 第3行（新任务）: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567890"`, `liveroom_title="直播间D"` - **相同URL和ID但不同标题**
   - 第4行（重复）: `resource_url="https://example.com/video2.mp4"`, `liveroom_id="1234567891"`, `liveroom_title="直播间B"` - **完全匹配任务2**
   - 第5行（新任务）: `resource_url="https://example.com/video3.mp4"`, `liveroom_id="1234567893"`, `liveroom_title="直播间E"`

**执行**:
```python
result = service.batch_import_tasks_from_csv(
    file_content=csv_bytes,
    user_id=test_user_id,
    skip_duplicates=True,  # 启用去重
    auto_start=False
)
```

**断言**:
1. **结果统计**:
   ```python
   assert result["total"] == 5
   assert result["success"] == 3  # 第2、3、5行是新任务
   assert result["skipped"] == 2  # 第1、4行被跳过
   assert len(result["skipped_rows"]) == 2
   ```

2. **跳过行详细信息**:
   ```python
   for skipped in result["skipped_rows"]:
       assert "任务组合已存在" in skipped["reason"]
       assert "row" in skipped
       assert "liveroom_id" in skipped
       assert "liveroom_title" in skipped
       assert "resource_url" in skipped
   ```

3. **数据库状态验证**:
   ```python
   # 数据库应有5个任务（2个预先创建 + 3个新导入）
   tasks = sync_db_session.query(DownloadTask).filter(
       DownloadTask.user_id == test_user_id
   ).all()
   assert len(tasks) == 5
   ```

##### **Test Case 4: 去重功能测试（skip_duplicates=False）**
```python
def test_batch_import_with_skip_duplicates_disabled(self, sync_db_session):
    """测试不启用去重：允许创建重复resource_url的任务"""
```

**准备**: 同Test Case 3

**执行**:
```python
result = service.batch_import_tasks_from_csv(
    file_content=csv_bytes,
    user_id=test_user_id,
    skip_duplicates=False,  # 不启用去重
    auto_start=False
)
```

**断言**:
```python
# 根据实际测试，数据库没有对resource_url设置唯一约束
# 因此允许创建重复URL的任务
assert result["success"] == 2  # 两条都成功（包括重复的URL）
assert result["skipped"] == 0  # 不跳过
assert result["failed"] == 0

# 验证数据库中确实有3个任务（1个预先创建 + 2个导入）
tasks = sync_db_session.query(DownloadTask).filter(
    DownloadTask.user_id == test_user_id
).all()
assert len(tasks) == 3
```

##### **Test Case 5: 去重功能测试（liveroom_title为空的情况）**
```python
def test_batch_import_with_skip_duplicates_null_title(self, sync_db_session):
    """测试去重功能：liveroom_title为空时的去重逻辑"""
```

**测试目标**: 验证当 `liveroom_title` 为 `None` 时的去重逻辑（空值匹配）

**准备**:
1. 在数据库中预先创建2个任务：
   - 任务1: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567890"`, `liveroom_title=None`
   - 任务2: `resource_url="https://example.com/video2.mp4"`, `liveroom_id="1234567891"`, `liveroom_title="直播间B"`
2. 准备CSV文件，包含4行数据：
   - 第1行（重复）: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567890"`, `liveroom_title=""` (空字符串，将被转为None) - **应匹配任务1**
   - 第2行（新任务）: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567890"`, `liveroom_title="直播间C"` - **相同URL和ID但有标题**
   - 第3行（新任务）: `resource_url="https://example.com/video1.m3u8"`, `liveroom_id="1234567892"`, `liveroom_title=""` - **相同URL但不同ID**
   - 第4行（重复）: `resource_url="https://example.com/video2.mp4"`, `liveroom_id="1234567891"`, `liveroom_title="直播间B"` - **完全匹配任务2**

**执行**:
```python
result = service.batch_import_tasks_from_csv(
    file_content=csv_bytes,
    user_id=test_user_id,
    skip_duplicates=True,
    auto_start=False
)
```

**断言**:
1. **结果统计**:
   ```python
   assert result["total"] == 4
   assert result["success"] == 2  # 第2、3行是新任务
   assert result["skipped"] == 2  # 第1、4行被跳过
   assert len(result["skipped_rows"]) == 2
   ```

2. **验证空值匹配逻辑**:
   ```python
   # 验证第1行被正确识别为重复（空值匹配空值）
   skipped_row_1 = next(r for r in result["skipped_rows"] if r["row"] == 2)
   assert skipped_row_1["liveroom_title"] is None or skipped_row_1["liveroom_title"] == ""
   assert "任务组合已存在" in skipped_row_1["reason"]
   ```

3. **数据库状态验证**:
   ```python
   # 数据库应有4个任务（2个预先创建 + 2个新导入）
   tasks = sync_db_session.query(DownloadTask).filter(
       DownloadTask.user_id == test_user_id
   ).all()
   assert len(tasks) == 4
   
   # 验证有2个任务的liveroom_title为None
   null_title_tasks = [t for t in tasks if t.liveroom_title is None]
   assert len(null_title_tasks) == 2
   ```

##### **Test Case 6: 自动启动功能测试**
```python
def test_batch_import_with_auto_start_enabled(self, sync_db_session):
    """测试自动启动功能：导入后自动调用start_download_task"""
```

**准备**:
1. Mock `start_download_task`方法以验证调用
2. 准备包含3行有效数据的CSV

**执行**:
```python
from unittest.mock import patch

service = DownloadService(sync_db_session)

# Mock start_download_task方法
with patch.object(service, 'start_download_task') as mock_start:
    result = service.batch_import_tasks_from_csv(
        file_content=csv_bytes,
        user_id=test_user_id,
        skip_duplicates=False,
        auto_start=True  # 启用自动启动
    )
```

**断言**:
```python
    assert result["success"] == 3
    # 验证start_download_task被调用了3次
    assert mock_start.call_count == 3
```

##### **Test Case 7: 批量提交性能测试**
```python
def test_batch_import_commit_performance(self, sync_db_session):
    """测试批量提交：每100行提交一次"""
```

**准备**: 准备包含250行有效数据的CSV

**执行**:
```python
from unittest.mock import patch

service = DownloadService(sync_db_session)

# Spy on commit
with patch.object(sync_db_session, 'commit', wraps=sync_db_session.commit) as mock_commit:
    result = service.batch_import_tasks_from_csv(
        file_content=csv_bytes,
        user_id=test_user_id,
        skip_duplicates=False,
        auto_start=False
    )
```

**断言**:
```python
    assert result["success"] == 250
    # 验证commit被调用至少3次：100行、200行、最终提交
    assert mock_commit.call_count >= 3
```

#### 4.1.2 失败场景测试

##### **Test Case 8: CSV缺少必需列**
```python
def test_batch_import_missing_required_columns(self, sync_db_session):
    """测试CSV缺少必需列（resource_url）"""
```

**准备**: CSV只包含`liveroom_id,resource_type`（缺少`resource_url`）

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
```python
service = DownloadService(sync_db_session)

with pytest.raises(ValueError) as exc_info:
    service.batch_import_tasks_from_csv(
        file_content=csv_content,
        user_id=test_user_id
    )
assert "缺少必需列" in str(exc_info.value)
assert "resource_url" in str(exc_info.value)
```

##### **Test Case 9: CSV超过最大行数**
```python
def test_batch_import_exceeds_max_rows(self, sync_db_session):
    """测试CSV超过1000行限制"""
```

**准备**: 生成包含1001行数据的CSV

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
```python
with pytest.raises(ValueError) as exc_info:
    service.batch_import_tasks_from_csv(...)
assert "超过最大行数限制" in str(exc_info.value)
```

##### **Test Case 10: 文件编码错误**
```python
def test_batch_import_invalid_encoding(self, sync_db_session):
    """测试非UTF-8编码文件"""
```

**准备**: 使用GBK编码的CSV文件

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
```python
with pytest.raises(ValueError) as exc_info:
    service.batch_import_tasks_from_csv(...)
assert "文件编码错误" in str(exc_info.value)
```

##### **Test Case 11: CSV格式错误**
```python
def test_batch_import_malformed_csv(self, sync_db_session):
    """测试格式错误的CSV（如引号未闭合跨多行）"""
```

**准备**: 包含格式错误的CSV内容（如 `liveroom_id,"title without closing quote`）

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
```python
with pytest.raises(ValueError) as exc_info:
    service.batch_import_tasks_from_csv(...)
assert "CSV文件格式错误" in str(exc_info.value)
```

##### **Test Case 12: 数据库操作失败**
```python
def test_batch_import_database_error(self, sync_db_session):
    """测试数据库操作失败时的回滚"""
```

**准备**:
1. Mock数据库commit方法抛出异常
2. 准备有效的CSV文件

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
```python
with pytest.raises(DatabaseError):
    service.batch_import_tasks_from_csv(...)
# 验证rollback被调用
```

##### **Test Case 13: 全部失败**
```python
def test_batch_import_all_rows_failed(self, sync_db_session):
    """测试所有行都失败的情况"""
```

**准备**: CSV中所有行的`liveroom_id`都不符合长度要求

**执行**: 调用`batch_import_tasks_from_csv`

**断言**:
```python
assert result["total"] == 10
assert result["success"] == 0
assert result["failed"] == 10
```

#### 4.1.3 边界条件测试

##### **Test Case 14: 空CSV文件（只有表头）**
```python
def test_batch_import_empty_csv_with_header_only(self, sync_db_session):
    """测试只有表头没有数据行的CSV"""
```

**断言**:
```python
assert result["total"] == 0
assert result["success"] == 0
```

##### **Test Case 15: 单行CSV**
```python
def test_batch_import_single_row(self, sync_db_session):
    """测试只有1行数据的CSV"""
```

##### **Test Case 16: 正好100行（批量提交边界）**
```python
def test_batch_import_exactly_100_rows(self, sync_db_session):
    """测试正好100行数据（批量提交边界）"""
```

**断言**: 验证commit被调用至少2次（100行时+最终提交）

##### **Test Case 17: liveroom_id边界值测试**
```python
def test_batch_import_liveroom_id_boundary(self, sync_db_session):
    """测试liveroom_id长度边界（10和20字符）"""
```

**准备**:
- 第1行：`liveroom_id`正好10个字符
- 第2行：`liveroom_id`正好20个字符
- 第3行：`liveroom_id`9个字符（应失败）
- 第4行：`liveroom_id`21个字符（应失败）

**断言**:
```python
assert result["success"] == 2
assert result["failed"] == 2
```

### 4.2 API接口测试 (`test_download_api_batch_import.py`)

#### 4.2.1 成功场景测试

##### **Test Case 18: API全部成功（201状态码）**
```python
@pytest.mark.asyncio
async def test_api_batch_import_all_success(self, async_client, db_session):
    """测试API批量导入全部成功，返回201"""
```

**准备**:
1. 创建测试CSV文件（使用`io.BytesIO`）
2. 包含10行有效数据

**执行**:
```python
async for client in async_client:
    files = {"file": ("test.csv", csv_file, "text/csv")}
    data = {
        "skip_duplicates": "false",
        "auto_start": "false"
    }
    response = await client.post(
        "/api/v1/download/tasks/batch-import",
        files=files,
        data=data
    )
```

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 201
assert response_data["message"] == "批量导入任务成功"
assert response_data["data"]["total"] == 10
assert response_data["data"]["success"] == 10
assert response_data["data"]["failed"] == 0
```

##### **Test Case 19: API部分成功（207状态码）**
```python
@pytest.mark.asyncio
async def test_api_batch_import_partial_success(self, async_client, db_session):
    """测试API批量导入部分成功，返回207"""
```

**准备**: CSV包含10行，其中3行数据无效

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 207
assert response_data["message"] == "批量导入部分成功"
assert response_data["data"]["success"] == 7
assert response_data["data"]["failed"] == 3
assert len(response_data["data"]["failed_rows"]) == 3
```

##### **Test Case 20: API去重功能测试**
```python
@pytest.mark.asyncio
async def test_api_batch_import_with_duplicates_skip(self, async_client, db_session):
    """测试API去重功能：skip_duplicates=true"""
```

**准备**:
1. 预先在数据库中创建2个任务
2. CSV包含5行，其中2行与已存在任务的`resource_url`重复

**执行**:
```python
data = {"skip_duplicates": "true", "auto_start": "false"}
response = await client.post(..., files=files, data=data)
```

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 207  # 部分成功（有跳过）
assert response_data["data"]["success"] == 3
assert response_data["data"]["skipped"] == 2
assert len(response_data["data"]["skipped_rows"]) == 2
```

#### 4.2.2 失败场景测试

##### **Test Case 21: 文件类型错误（非CSV）**
```python
@pytest.mark.asyncio
async def test_api_batch_import_invalid_file_type(self, async_client):
    """测试上传非CSV文件"""
```

**准备**: 上传`.txt`文件

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 400
assert "文件类型错误" in response_data["message"]
```

##### **Test Case 22: 文件过大（超过10MB）**
```python
@pytest.mark.asyncio
async def test_api_batch_import_file_too_large(self, async_client):
    """测试文件大小超过10MB限制"""
```

**准备**: 生成11MB的CSV文件

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 413
assert "文件大小超过限制" in response_data["message"]
assert "file_size" in response_data["data"]
assert "max_size" in response_data["data"]
```

##### **Test Case 23: 空文件**
```python
@pytest.mark.asyncio
async def test_api_batch_import_empty_file(self, async_client):
    """测试上传空文件"""
```

**准备**: 上传0字节的CSV文件

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 400
assert "文件不能为空" in response_data["message"]
```

##### **Test Case 24: CSV缺少必需列**
```python
@pytest.mark.asyncio
async def test_api_batch_import_missing_columns(self, async_client):
    """测试CSV缺少必需列"""
```

**准备**: CSV只包含部分必需列

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 400
assert "缺少必需列" in response_data["message"]
```

##### **Test Case 25: 全部失败（400状态码）**
```python
@pytest.mark.asyncio
async def test_api_batch_import_all_failed(self, async_client):
    """测试所有行都失败，返回400"""
```

**准备**: CSV中所有行数据都无效

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 400
assert "批量导入失败，所有行都处理失败" in response_data["message"]
assert response_data["data"]["success"] == 0
```

##### **Test Case 26: 文件编码错误**
```python
@pytest.mark.asyncio
async def test_api_batch_import_encoding_error(self, async_client):
    """测试非UTF-8编码文件```

**准备**: 使用GBK编码的CSV文件，并包含中文以确保编码差异

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 400
assert "文件编码错误" in response_data["message"]
```

#### 4.2.3 边界条件和安全测试

##### **Test Case 27: 超长文件名**
```python
@pytest.mark.asyncio
async def test_api_batch_import_extremely_long_filename(self, async_client):
    """测试超长文件名（1000个字符）"""
```

##### **Test Case 28: 文件名包含特殊字符**
```python
@pytest.mark.asyncio
async def test_api_batch_import_special_chars_in_filename(self, async_client):
    """测试文件名包含特殊字符（如 <script>）"""
```

##### **Test Case 29: CSV包含SQL注入尝试**
```python
@pytest.mark.asyncio
async def test_api_batch_import_sql_injection_attempt(self, async_client, db_session):
    """测试CSV数据包含SQL注入代码"""
```

**准备**: CSV行数据包含`'; DROP TABLE--`等SQL注入代码

**断言**: 数据被安全处理，不会导致数据库损坏

##### **Test Case 30: 并发上传测试**
```python
@pytest.mark.asyncio
async def test_api_batch_import_concurrent_uploads(self, async_client, db_session):
    """测试并发上传多个CSV文件"""
```

**执行**: 使用`asyncio.gather`同时发起5个上传请求

**断言**: 所有请求都正确处理，数据库状态一致

#### 4.2.4 性能测试

##### **Test Case 31: 响应时间测试**
```python
@pytest.mark.asyncio
async def test_api_batch_import_response_time(self, async_client):
    """测试API响应时间（100行数据）"""
```

**准备**: 100行有效数据的CSV

**断言**:
```python
import time
start = time.time()
response = await client.post(...)
duration = time.time() - start

# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] in [201, 207]
assert duration < 5.0  # 100行应在5秒内完成
```

##### **Test Case 32: 大文件处理性能**
```python
@pytest.mark.asyncio
async def test_api_batch_import_large_file_performance(self, async_client, db_session):
    """测试大文件处理性能（1000行）```

**准备**: 1000行有效数据的CSV（接近最大行数）

**断言**:
```python
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] == 201
assert response_data["data"]["processing_time"] < 30.0  # 1000行应在30秒内完成
```

## 五、测试数据生成工具函数

**重要说明**：所有辅助函数都应直接定义在测试文件内，**不要修改 `conftest.py`**。

### 5.1 CSV生成辅助函数

**文件位置**：直接定义在 `test_download_service_batch_import.py` 和 `test_download_api_batch_import.py` 文件的开头部分。

```python
from faker import Faker
import random
import io

fake = Faker()

def generate_csv_content(num_rows: int, invalid_rows: list = None) -> bytes:
    """
    生成测试用CSV内容
    
    Args:
        num_rows: 总行数
        invalid_rows: 无效行的配置列表，如 [
            {"row": 3, "type": "short_liveroom_id"},
            {"row": 5, "type": "invalid_resource_type"}
        ]
    
    Returns:
        bytes: UTF-8编码的CSV内容
    """
    output = io.StringIO()
    # 写入表头
    output.write("liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type\n")
    
    invalid_row_dict = {item["row"]: item["type"] for item in (invalid_rows or [])}
    
    for i in range(1, num_rows + 1):
        row_number = i + 1  # 从第2行开始（第1行是表头）
        
        if row_number in invalid_row_dict:
            error_type = invalid_row_dict[row_number]
            if error_type == "short_liveroom_id":
                liveroom_id = "123"  # 长度不足
            elif error_type == "long_liveroom_id":
                liveroom_id = "1" * 25  # 长度超出
            elif error_type == "invalid_resource_type":
                resource_type = "invalid"
            elif error_type == "missing_resource_url":
                # 缺少resource_url
                output.write(f"{fake.random_int(min=1000000000, max=9999999999)},标题,https://example.com,,hls\n")
                continue
            else:
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
        else:
            liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
            resource_type = random.choice(["hls", "mp4", "image"])
        
        liveroom_title = fake.sentence(nb_words=3)
        liveroom_url = fake.url()
        resource_url = fake.url()
        
        if row_number not in invalid_row_dict or error_type not in ["invalid_resource_type"]:
            resource_type = random.choice(["hls", "mp4", "image"])
        
        output.write(f"{liveroom_id},{liveroom_title},{liveroom_url},{resource_url},{resource_type}\n")
    
    return output.getvalue().encode('utf-8')


def generate_csv_file_object(csv_bytes: bytes, filename: str = "test.csv"):
    """
    生成可用于FastAPI UploadFile的文件对象
    
    Args:
        csv_bytes: CSV内容（字节）
        filename: 文件名
    
    Returns:
        io.BytesIO: 文件对象
    """
    file_obj = io.BytesIO(csv_bytes)
    file_obj.name = filename
    return file_obj
```

### 5.2 同步数据库Fixture

**重要说明**：服务层测试需要同步数据库会话。如果`conftest.py`中没有`sync_db_session` fixture，需要在测试文件中添加：

```python
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def sync_db_session():
    """同步数据库会话（用于Service层测试）"""
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
    POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "media_download_test")
    
    SYNC_TEST_DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    sync_engine = create_engine(SYNC_TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=sync_engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
```

## 六、测试代码结构要求

### 6.1 文件组织

```
tests/
├── test_download_service_batch_import.py  # 服务层测试（16个测试用例，同步）
├── test_download_api_batch_import.py      # API接口测试（15个测试用例，异步）
└── conftest.py                             # 测试配置（不需要修改）
```

### 6.2 测试类结构

```python
# test_download_service_batch_import.py
class TestDownloadServiceBatchImport:
    """CSV批量导入服务层测试类"""
    
    def test_batch_import_all_success(self, sync_db_session):
        """测试全部成功导入"""
        # 同步测试方法，不使用 async/await
        pass
    
    # ... 其他测试方法（都是同步的）


# test_download_api_batch_import.py
class TestDownloadApiBatchImport:
    """CSV批量导入API接口测试类"""
    
    @pytest.mark.asyncio
    async def test_api_batch_import_all_success(self, db_session, auth_headers):
        """测试API全部成功"""
        # 异步测试方法，使用 async/await
        pass
    
    # ... 其他测试方法（都是异步的）
```

### 6.3 必需的导入语句

```python
import pytest
import uuid
import asyncio
import time
import io
import csv
from datetime import datetime, timedelta
from faker import Faker
import random

# FastAPI 测试相关
from httpx import AsyncClient

# 应用模型和Schema
from app.models.download import DownloadTask, DownloadedVideo
from app.schemas.download import TaskStatus, DownloadTaskCreate, BatchImportResult
from app.services.download_service import DownloadService
from app.core.exceptions import DatabaseError

fake = Faker()
```

## 七、断言模板

### 7.1 成功场景断言模板

```python
# 1. API响应断言（统一响应模式）
# HTTP状态码固定为200
assert response.status_code == 200
response_data = response.json()
# 业务状态码在body的code字段
assert response_data["code"] in [201, 207]
assert response_data["message"] in ["批量导入任务成功", "批量导入部分成功"]
assert "data" in response_data

# 2. 服务层响应断言
result = service.batch_import_tasks_from_csv(...)
assert result["total"] == expected_total
assert result["success"] == expected_success
assert result["failed"] == expected_failed
assert result["skipped"] == expected_skipped
assert len(result["created_task_ids"]) == expected_success
assert result["processing_time"] > 0

# 3. 数据库状态断言（使用同步会话）
tasks = sync_db_session.query(DownloadTask).filter(
    DownloadTask.user_id == test_user_id
).all()
assert len(tasks) == expected_success
for task in tasks:
    assert task.status == TaskStatus.PENDING
    assert task.resource_type in ["hls", "mp4", "image"]
```

### 7.2 失败场景断言模板

```python
# 1. API错误响应断言（统一响应模式）
# HTTP状态码固定为200
assert response.status_code == 200
error_data = response.json()
# 业务状态码在body的code字段
assert error_data["code"] in [400, 413, 500]
assert "message" in error_data
assert expected_error_keyword in error_data["message"]

# 2. 服务层异常断言
with pytest.raises(ExpectedException) as exc_info:
    service.batch_import_tasks_from_csv(...)
assert expected_keyword in str(exc_info.value)
```

# 2. 失败行详细信息断言
failed_rows = error_data["data"]["failed_rows"]
assert len(failed_rows) == expected_failed_count
for failed_row in failed_rows:
    assert "row" in failed_row
    assert "liveroom_id" in failed_row
    assert "resource_url" in failed_row
    assert "error" in failed_row

# 3. 异常断言
with pytest.raises(ExpectedException) as exc_info:
    service.batch_import_tasks_from_csv(...)
assert expected_keyword in str(exc_info.value)
```

### 7.3 错误隔离验证断言

```python
# 验证特定行的失败信息
failed_row_3 = next(
    (r for r in result["failed_rows"] if r["row"] == 3),
    None
)
assert failed_row_3 is not None
assert "expected_error_message" in failed_row_3["error"]

# 验证成功的行确实创建了任务
assert result["success"] == expected_success_count
tasks = db.query(DownloadTask).filter(
    DownloadTask.user_id == test_user_id
).all()
assert len(tasks) == expected_success_count
```

## 八、最佳实践与注意事项

### 8.1 测试隔离
- 每个测试用例使用独立的`user_id`
- 测试前后清理数据库相关表
- 使用`Faker`生成随机数据避免冲突

### 8.2 同步/异步测试规范

#### 服务层测试（同步）
- **不使用** `@pytest.mark.asyncio` 装饰器
- 使用 `def test_...` 定义测试方法（同步）
- 使用 `sync_db_session` fixture（同步数据库会话）
- **不使用** `async`/`await` 语法
- 直接调用服务层方法：`service.batch_import_tasks_from_csv(...)`

#### API测试（异步）
- **必须使用** `@pytest.mark.asyncio` 装饰器
- 使用 `async def test_...` 定义测试方法（异步）
- 使用 `AsyncClient` 发送HTTP请求
- 所有测试断言都应验证 `response.status_code == 200` 和 `response.json()["code"]`

### 8.3 Mock使用原则
- Mock外部依赖（如`start_download_task`）
- Spy数据库操作（如`commit`）验证调用次数
- 不Mock被测方法本身

### 8.4 数据库状态验证
- 成功场景必须验证数据库记录创建正确
- 失败场景必须验证数据库未产生脏数据
- 回滚场景必须验证事务正确回滚

### 8.5 性能测试要求
- 100行数据应在5秒内完成
- 1000行数据应在30秒内完成
- 批量提交机制应正常工作（每100行提交一次）

## 九、测试覆盖率目标

### 9.1 代码覆盖率
- **服务层方法**: 覆盖率 ≥ 95%
- **API端点**: 覆盖率 ≥ 90%

### 9.2 场景覆盖率
- ✅ 全部成功
- ✅ 部分成功（错误隔离）
- ✅ 全部失败
- ✅ 去重功能（启用/禁用）
- ✅ 自动启动功能
- ✅ 批量提交性能
- ✅ 文件验证（类型、大小、编码）
- ✅ CSV格式验证
- ✅ 字段验证（长度、枚举值）
- ✅ 边界条件
- ✅ 并发场景
- ✅ 异常处理和回滚

## 十、最终交付清单

### 10.1 文件清单
1. **`tests/test_download_service_batch_import.py`** (12个测试用例)
2. **`tests/test_download_api_batch_import.py`** (15个测试用例)
3. **`tests/conftest.py`** (包含CSV生成辅助函数)

### 10.2 测试用例总数
- **服务层测试**: 17个测试用例（Test Case 1-17）
- **API接口测试**: 15个测试用例（Test Case 18-32）
- **总计**: 32个测试用例

### 10.3 质量要求
- ✅ 所有测试用例必须可独立运行
- ✅ 所有测试用例必须可重复执行
- ✅ 测试数据必须使用Faker随机生成
- ✅ 每个测试函数都有详细的文档字符串
- ✅ 所有断言都有明确的验证目的
- ✅ 错误消息验证不仅检查状态码，还检查具体错误信息

---

**文档版本**: v1.0  
**创建日期**: 2025-01-XX  
**文档状态**: 已完成，待实施

