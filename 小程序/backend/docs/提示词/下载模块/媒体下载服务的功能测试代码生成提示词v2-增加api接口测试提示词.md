#### **1. 角色定义 (Role Definition)**

You are a Senior Python Backend Engineer specializing in automated testing. You are an expert in using `pytest` with `pytest-asyncio` and mocking frameworks like `pytest-mock`. Your task is to write a robust **unit test suite** for the provided `SubscriptionsService` class.

#### **2. 任务目标 (Task Objective)**

你的目标是**末尾追加**新的测试函数到 `tests/test_managepent_api.py`.

#### **3. 核心上下文信息 (Core Context Information)**


#### **4. 新增API接口详细说明**

### **【补充】媒体下载服务 API 接口设计**

#### **5.4.4 查询已下载视频详情**

  * **接口**: `GET /api/v1/download/videos/{video_id}`

  * **描述**: 根据 `video_id` 获取单个已成功下载视频的详细信息。这是向其他业务系统（如媒资管理、内容分发）提供最终下载成果的核心接口。

  * **认证**: 建议需要认证 (例如，内部服务间认证)。

  * **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `video_id` | `UUID` | 视频的唯一标识ID |

  * **成功响应 (`200 OK`)**:

    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "video_id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "liveroom_id": "room123",
        "liveroom_title": "医学讲座直播",
        "video_type": "hls",
        "storage_path": "/media/video_a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
        "file_size": 1073741824,
        "duration": 3600,
        "resolution": "1920x1080",
        "format": "hls",
        "cover_path": "/media/video_a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4/images/cover.jpg",
        "status": "completed",
        "download_end_time": "2025-06-14T10:15:00Z",
        "created_at": "2025-06-14T10:15:00Z"
      },
      "timestamp": "2025-06-14T10:18:00Z"
    }
    ```

  * **失败响应示例 (`404 Not Found`)**:

    ```json
    {
      "code": 404,
      "message": "资源不存在",
      "data": {
        "resource": "DownloadedVideo",
        "id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4"
      },
      "timestamp": "2025-06-14T10:19:00Z"
    }
    ```

  * **实现流程描述**:

    1.  从路径参数中获取 `video_id`。
    2.  在 `downloaded_videos` 表中，使用 `video_id` 作为查询条件进行精确查找。
    3.  如果未找到记录，返回 `404 Not Found` 错误。
    4.  如果找到记录，将其序列化并包装在 `success_response` 中返回。

-----


### 5.4.5. (补充) 全局失败记录管理接口

#### 1 查询所有失败记录（分页）

  * **接口**: `GET /api/v1/download/failures`
  * **描述**: (管理员) 从全局视角分页、筛选查询系统中的所有失败下载记录，用于系统监控和故障排查。
  * **认证**: 需要认证 (例如，内部服务或管理员权限)。
  * **请求参数 (Query)**:
      * `page` (int, 可选, 默认1): 页码。
      * `size` (int, 可选, 默认10): 每页数量。
      * `sort` (string, 可选): 排序字段，如 `created_at:desc`。
      * `status` (string, 可选): 按失败记录状态筛选 (`pending`, `retrying`, `abandoned`)。
      * `failure_type` (string, 可选): 按失败类型筛选 (`network_error`, `timeout` 等)。
  * **成功响应 (`200 OK`)**:
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 50,
        "page": 1,
        "size": 10,
        "items": [
          {
            "failure_id": "uuid-of-failure-1",
            "task_id": "uuid-of-parent-task-A",
            "resource_url": "https://lancet.im/ts/seg_0042.ts",
            "failure_type": "timeout",
            "status": "pending",
            "retry_count": 1,
            "error_message": "Connection timed out after 30 seconds",
            "created_at": "2025-06-14T10:05:00Z"
          }
        ]
      },
      "timestamp": "2025-06-14T11:00:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员的权限。
    2.  构建基础的 `select(download_failures)` 查询。
    3.  根据传入的 `status` 和 `failure_type` 等Query参数动态添加 `WHERE` 筛选条件。
    4.  执行 `count` 查询获取筛选后的总数。
    5.  应用排序和分页到查询上。
    6.  执行最终查询获取当页的 `items`。
    7.  构建并返回符合分页规范的成功响应。

#### 2 查询单个失败记录详情

  * **接口**: `GET /api/v1/download/failures/{failure_id}`
  * **描述**: (管理员) 根据 `failure_id` 获取单个失败下载记录的详细信息。
  * **认证**: 需要认证 (例如, 内部服务或管理员权限)。
  * **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `failure_id` | `UUID` | 失败记录的唯一标识ID |

  * **成功响应 (`200 OK`)**:
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "failure_id": "uuid-of-failure-1",
        "task_id": "uuid-of-parent-task-A",
        "resource_url": "https://lancet.im/ts/seg_0042.ts",
        "standard_name": "seg_0042_...",
        "expected_path": "/media/downloads/task_A/ts/seg_0042_....ts",
        "resource_type": "ts",
        "failure_type": "timeout",
        "error_message": "Connection timed out after 30 seconds",
        "retry_count": 1,
        "next_retry_time": "2025-06-14T10:30:00Z",
        "status": "pending",
        "created_at": "2025-06-14T10:05:00Z",
        "updated_at": "2025-06-14T10:05:00Z"
      },
      "timestamp": "2025-06-14T11:05:00Z"
    }
    ```
  * **失败响应示例 (`404 Not Found`)**:
    ```json
    {
      "code": 404,
      "message": "资源不存在",
      "data": {
        "resource": "DownloadFailure",
        "id": "{failure_id}"
      },
      "timestamp": "2025-06-14T11:06:00Z"
    }
    ```
  * **实现流程描述**:
    1.  校验操作员权限。
    2.  从路径参数中获取 `failure_id`。
    3.  在 `download_failures` 表中，使用 `id` 作为查询条件进行精确查找。
    4.  如果未找到记录，返回 `404 Not Found` 错误。
    5.  如果找到记录，将其序列化并包装在 `success_response` 中返回。

-----



### **6. 具体代码生成指令 (Specific Code Generation Instructions)**
##### **6.1. 第一部分: `app/core/exceptions.py` (服务层 - 追加内容)**
  * **指令**:  在 app/core/exceptions.py **内部末尾追加**下面的异常类定义

class VideoNotFoundError(DownloadServiceError):
    """已下载视频记录未找到异常"""
    pass

class FailureRecordNotFoundError(DownloadServiceError):
    """失败记录未找到异常"""
    pass

##### **6.2. 第一部分: `app/services/download_service.py` (服务层 - 追加内容)**

  * **指令**: 在 `app/services/download_service.py` 文件中的 `DownloadService` 类**内部末尾追加**以下新的业务逻辑方法。
  * **架构要求**: **所有数据库操作（增、删、改、查）必须在此文件中，使用 SQLAlchemy Core 或 ORM 语法直接实现。**
  * **需新增的函数**:
    1.  **`get_downloaded_video(self, video_id: uuid.UUID) -> models.DownloadedVideo`**:
          * **业务逻辑流程**:
            1.  在 `downloaded_videos` 表中，使用 `video_id` 作为查询条件进行精确查找。
            2.  如果未找到记录，`raise VideoNotFoundError()` (需要您在Service中定义此异常)。
            3.  如果找到，返回查询到的 `models.DownloadedVideo` 对象。
    2.  **`list_failures(self, filters: ..., page: int, size: int) -> dict`**:
          * **业务逻辑流程**:
            1.  计算分页参数 `skip`。
            2.  根据 `filters` 动态构建 `WHERE` 查询条件。
            3.  执行 `count` 查询获取筛选后的总数。
            4.  执行查询获取当页的失败记录列表。
            5.  将结果序列化并组装成分页格式的字典返回。
    3.  **`get_failure_details(self, failure_id: uuid.UUID) -> models.DownloadFailure`**:
          * **业务逻辑流程**:
            1.  在 `download_failures` 表中，使用主键 `id` (`failure_id`) 作为查询条件进行精确查找。
            2.  如果未找到记录，`raise FailureRecordNotFoundError()` (需要您在Service中定义此异常)。
            3.  返回查询到的 `models.DownloadFailure` 对象。

##### **6.3. 第二部分: `app/api/v1/endpoints/download.py` (表现层/端点层 - 追加内容)**

  * **指令**: 在 `app/api/v1/endpoints/download.py` 文件**末尾追加**以下新的API端点。

  * **通用要求**:

      * 严格遵循您提供的所有通用规范（认证、安全编码、响应格式等）。

  * **需新增的端点 (在 `download.py` 的 `router` 对象下)**:

    1.  **`GET /videos/{video_id}` (查询已下载视频详情)**

          * **实现流程**:
            1.  依赖注入 `admin_user` 和 `db`。
            2.  **主动提取**: `admin_user_id_for_logging = admin_user.id`。
            3.  在 `try...except` 块中：
                  * a. 实例化 `info_service = DownloadService(db)`。
                  * b. 调用 `video = await info_service.get_downloaded_video(video_id=video_id)`。
                  * c. 序列化 `video` 对象并调用 `success_response` 返回。
            4.  **异常处理**:
                  * a. `except VideoNotFoundError as e`: 返回 `JSONResponse(status_code=404, content=error_response(code=2004, message=str(e)))`。
                  * b.  except Exception as e: 【已修正】 记录日志，并返回 JSONResponse(status_code=500, content=error_response(code=1002, message='服务器内部错误'))。

    2.  **`GET /failures` (查询所有失败记录)**

          * **实现流程**:
            1.  依赖注入 `admin_user` 和 `db`。接收分页和筛选参数。
            2.  在 `try...except` 块中：
                  * a. 实例化 `info_service = DownloadService(db)`。
                  * b. 将`Query`参数聚合到一个筛选Schema实例中。
                  * c. 调用 `paginated_result = await info_service.list_failures(...)`。
                  * d. 调用 `success_response` 返回 `paginated_result`。
            3.  **异常处理**: except Exception as e: 【已修正】 记录日志，并返回 JSONResponse(status_code=500, content=error_response(code=1002, message='服务器内部错误'))。

    3.  **`GET /failures/{failure_id}` (查询单个失败记录详情)**

          * **实现流程**:
            1.  依赖注入 `admin_user` 和 `db`。
            2.  在 `try...except` 块中：
                  * a. 实例化 `info_service = DownloadService(db)`。
                  * b. 调用 `failure = await info_service.get_failure_details(failure_id=failure_id)`。
                  * c. 序列化 `failure` 对象并调用 `success_response` 返回。
            3.  **异常处理**:
                  * a. `except FailureRecordNotFoundError as e`: 返回 `404` 错误。
                  * b. except Exception as e: 【已修正】 记录日志，并返回 JSONResponse(status_code=500, content=error_response(code=1002, message='服务器内部错误'))。

###### **B. 单个任务端点: `/api/v1/download/tasks/{task_id}`**

* **`test_get_task_details_success`**:
    * **准备**: 创建一个任务。
    * **操作**: 使用其ID调用GET `/api/v1/download/tasks/{task_id}` 请求。
    * **断言**: 状态码`200 OK`，返回数据正确。
* **`test_get_task_details_not_found`**:
    * **操作**: 使用不存在的ID调用GET `/api/v1/download/tasks/{task_id}` 请求。
    * **断言**: 状态码`404 Not Found`。
* **`test_delete_pending_task_success`**:
    * **准备**: 创建一个`PENDING`状态的任务。
    * **操作**: 调用DELETE `/api/v1/download/tasks/{task_id}` 请求。
    * **断言**: 状态码`200 OK`，数据库中该任务状态变为`CANCELLED`或被删除。
* **`test_delete_non_deletable_task_fails`**:
    * **准备**: 创建一个`COMPLETED`或`PROCESSING`状态的任务。
    * **操作**: 调用DELETE `/api/v1/download/tasks/{task_id}` 请求。
    * **断言**: 状态码`400 Bad Request`或`409 Conflict`。

###### **C. 失败记录管理端点**

* **`GET /api/v1/download/tasks/{task_id}/failures`**:
    * **`test_get_failures_for_task_success`**:
        * **准备**: 创建一个任务并关联3条失败记录。
        * **操作**: 调用GET `/api/v1/download/tasks/{task_id}/failures` 接口。
        * **断言**: 状态码`200 OK`，返回的列表长度为3。
* **`POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon`**:
    * **`test_abandon_specific_failure_success`**:
        * **准备**: 创建任务和一条`pending`状态的失败记录。
        * **操作**: 调用POST `/api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon` 接口。
        * **断言**: 状态码`200 OK`，数据库中该失败记录的`status`变为`abandoned`。
    * **`test_abandon_failure_with_invalid_ids_fails`**:
        * **操作**: 使用不存在的`failure_id`或与`task_id`不匹配的`failure_id`调用POST `/api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon` 接口。
        * **断言**: 状态码为`404 Not Found`或`400 Bad Request`。

#### **5. 断言模板与最佳实践**

##### **A. 标准断言结构**

每个测试函数都应该遵循 **AAA模式** (Arrange-Act-Assert):

```python
def test_example(client, db_session):
    # Arrange (准备)
    task = create_test_task(db_session)
    
    # Act (操作)
    response = client.post(f"/api/v1/download/tasks/{task.id}/start")
    
    # Assert (断言)
    # 1. API响应断言
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "completed"
    
    # 2. 数据库状态断言
    updated_task = db_session.query(DownloadTask).filter_by(id=task.id).first()
    assert updated_task.status == TaskStatus.COMPLETED
    
    # 3. 关联数据断言
    video_record = db_session.query(DownloadedVideo).filter_by(task_id=task.id).first()
    assert video_record is not None
```

##### **B. 常见断言类型**

###### **成功场景断言模板**
```python
# API响应断言
assert response.status_code == 200  # 或 201 Created
assert response.json()["status"] == "completed"
assert "task_id" in response.json()

# 数据库状态断言
task = db_session.query(DownloadTask).filter_by(id=task_id).first()
assert task.status == TaskStatus.COMPLETED
assert task.retry_count == expected_retry_count

# 关联记录断言
failures = db_session.query(DownloadFailure).filter_by(task_id=task_id).all()
assert len(failures) == 0  # 成功时应该没有失败记录

video_record = db_session.query(DownloadedVideo).filter_by(task_id=task_id).first()
assert video_record is not None
assert video_record.status == "completed"
```

###### **失败场景断言模板**
```python
# API响应断言
assert response.status_code == 400  # 或 404, 422, 409
error_data = response.json()
assert "detail" in error_data
assert "任务不存在" in error_data["detail"]  # 或相应的错误信息

# 数据库状态断言
task = db_session.query(DownloadTask).filter_by(id=task_id).first()
assert task.status == TaskStatus.FAILED  # 或相应状态
assert task.retry_count == expected_retry_count

# 失败记录断言
failures = db_session.query(DownloadFailure).filter_by(task_id=task_id).all()
assert len(failures) == expected_failure_count
for failure in failures:
    assert failure.resource_type in ["mp4", "m3u8", "ts"]
    assert failure.status == "pending"  # 或 "abandoned"
```

###### **异常处理断言模板**
```python
# 404 Not Found
assert response.status_code == 404
assert "任务不存在" in response.json()["detail"]

# 422 Unprocessable Entity
assert response.status_code == 422
assert "无效的UUID格式" in response.json()["detail"]

# 409 Conflict
assert response.status_code == 409
assert "视频已下载" in response.json()["detail"]

# 400 Bad Request
assert response.status_code == 400
assert "任务已完成" in response.json()["detail"]
```

##### **C. 数据库查询断言技巧**

```python
# 验证记录存在
record = db_session.query(Model).filter_by(id=record_id).first()
assert record is not None

# 验证记录不存在
record = db_session.query(Model).filter_by(id=record_id).first()
assert record is None

# 验证记录数量
count = db_session.query(Model).filter_by(task_id=task_id).count()
assert count == expected_count

# 验证字段值
task = db_session.query(DownloadTask).filter_by(id=task_id).first()
assert task.status == TaskStatus.COMPLETED
assert task.retry_count == 0
assert task.updated_at > task.created_at

# 验证关联关系
failures = db_session.query(DownloadFailure).filter_by(task_id=task_id).all()
for failure in failures:
    assert failure.task_id == task_id
    assert failure.resource_type in ["mp4", "m3u8", "ts"]
```

##### **D. 并发和异常测试断言**

```python
# 并发测试断言
def test_concurrent_task_creation(client, db_session):
    # 准备多个并发请求
    responses = []
    for i in range(5):
        response = client.post("/api/v1/download/tasks", json=task_data)
        responses.append(response)
    
    # 断言只有一个成功，其他返回409
    success_count = sum(1 for r in responses if r.status_code == 201)
    conflict_count = sum(1 for r in responses if r.status_code == 409)
    assert success_count == 1
    assert conflict_count == 4

# 系统异常测试断言
def test_database_connection_error(client, db_session, monkeypatch):
    # 模拟数据库连接失败
    def mock_query(*args, **kwargs):
        raise Exception("Database connection failed")
    
    monkeypatch.setattr(db_session, "query", mock_query)
    
    response = client.post("/api/v1/download/tasks", json=task_data)
    assert response.status_code == 500
    assert "内部服务器错误" in response.json()["detail"]
```


#### **4. 代码生成具体要求 (Specific Code Generation Instructions)**

##### **4.1. `tests/conftest.py` - 测试设置**
* **指令**: 你的任务**不包括**生成或修改 `conftest.py`。你**必须假设**它已存在并提供以下 fixture：
  * `db_session` - 数据库会话 fixture
  * `async_client` - 异步HTTP客户端 fixture
  * `test_app` - 测试应用实例 fixture

##### **4.2. 测试数据隔离 (Test Data Isolation)**
* **指令**: 所有测试用例在准备数据时，**必须**使用 `uuid` 生成随机且唯一的测试数据。

##### **4.3. `tests/test_download_api_new.py` - 新增API接口测试**

* **文件名**: `tests/test_download_api_new.py`
* **职责**: 对新增的三个下载服务API接口进行完整的功能测试。
* **核心要求**: **必须严格遵循异步测试规范和数据隔离原则**。

#### **4.4. 新增API接口测试用例详细规范**

##### **A. GET /api/v1/download/videos/{video_id} - 查询已下载视频详情**

* **`test_get_downloaded_video_success`**:
        * **准备 (Arrange)**:
    * a. 在 `async for db in db_session:` 块内清空相关表数据。
    * b. 创建测试用的 `DownloadTask` 记录，状态为 `COMPLETED`。
    * c. 创建对应的 `DownloadedVideo` 记录，关联到上述任务，状态为 `completed`。
    * d. 提取创建的 `video.video_id` 用于API调用。
  * **执行 (Act)**: 在 `async for client in async_client:` 块内调用 `GET /api/v1/download/videos/{video_id}`。
        * **断言 (Assert)**:
    * a. 断言 HTTP 状态码为 `200`，业务 `code` 为 `200`。
    * b. 断言响应 `data` 包含正确的 `video_id`, `liveroom_id`, `storage_path` 等字段。
    * c. 断言 `data.status` 为 `"completed"`。
    * d. 验证时间戳字段格式正确（ISO格式）。

* **`test_get_downloaded_video_not_found`**:
  * **准备**: 生成一个随机的 `video_id`（使用 `uuid.uuid4()`），确保数据库中不存在该记录。
  * **执行**: 调用 `GET /api/v1/download/videos/{non_existent_video_id}`。
  * **断言**:
    * a. 断言 HTTP 状态码为 `404`。
    * b. 断言错误信息包含 `"不存在"` 关键字。

* **`test_get_downloaded_video_invalid_uuid_format`**:
  * **执行**: 使用无效的UUID格式（如 `"invalid-uuid"`）调用API。
  * **断言**: 断言 HTTP 状态码为 `422`（参数验证失败）。

##### **B. GET /api/v1/download/failures - 查询所有失败记录（分页）**

* **`test_list_all_failures_success_with_data`**:
        * **准备 (Arrange)**:
    * a. 在数据库中创建3个不同的 `DownloadTask` 记录。
    * b. 为每个任务创建2条 `DownloadFailure` 记录，使用不同的 `status`（如 `pending`, `abandoned`）和 `failure_type`（如 `network_error`, `timeout`）。
    * c. 确保所有测试数据的 `resource_url`, `error_message` 等字段都是随机生成的。
  * **执行 (Act)**: 调用 `GET /api/v1/download/failures?page=1&size=10`。
        * **断言 (Assert)**:
    * a. 断言 HTTP 状态码为 `200`，业务 `code` 为 `200`。
    * b. 断言返回的 `data.total` 等于 6（3个任务 × 2条失败记录）。
    * c. 断言 `data.items` 数组长度为 6。
    * d. 验证每个失败记录包含必要字段：`failure_id`, `task_id`, `resource_url`, `failure_type`, `status`。

* **`test_list_all_failures_with_status_filter`**:
  * **准备**: 创建失败记录，其中2条状态为 `pending`，2条状态为 `abandoned`。
  * **执行**: 调用 `GET /api/v1/download/failures?status=pending`。
  * **断言**:
    * a. 断言返回的记录总数为2。
    * b. 断言所有返回的记录 `status` 都为 `"pending"`。

* **`test_list_all_failures_with_failure_type_filter`**:
  * **准备**: 创建失败记录，其中2条 `failure_type` 为 `network_error`，2条为 `timeout`。
  * **执行**: 调用 `GET /api/v1/download/failures?failure_type=network_error`。
  * **断言**:
    * a. 断言返回的记录总数为2。
    * b. 断言所有返回的记录 `failure_type` 都为 `"network_error"`。

* **`test_list_all_failures_pagination`**:
  * **准备**: 创建15条失败记录。
  * **执行**: 依次调用 `page=1&size=10` 和 `page=2&size=10`。
  * **断言**:
    * a. 第一页返回10条记录，`total=15`，`pages=2`。
    * b. 第二页返回5条记录，`total=15`，`pages=2`。

* **`test_list_all_failures_empty_result`**:
  * **准备**: 确保数据库中没有失败记录。
  * **执行**: 调用 `GET /api/v1/download/failures`。
  * **断言**:
    * a. 断言 HTTP 状态码为 `200`。
    * b. 断言 `data.total` 为 0，`data.items` 为空数组。

##### **C. GET /api/v1/download/failures/{failure_id} - 查询单个失败记录详情**

* **`test_get_failure_details_success`**:
  * **准备 (Arrange)**:
    * a. 创建一个 `DownloadTask` 记录。
    * b. 创建一个关联的 `DownloadFailure` 记录，包含完整的字段信息：
      * `resource_url`: 随机生成的URL
      * `expected_path`: 随机生成的文件路径
      * `standard_name`: 随机生成的文件名
      * `resource_type`: `"ts"`
      * `failure_type`: `"network_error"`
      * `error_message`: 随机生成的错误信息
      * `status`: `"pending"`
      * `retry_count`: `1`
    * c. 提取创建的 `failure.id` 用于API调用。
  * **执行 (Act)**: 调用 `GET /api/v1/download/failures/{failure_id}`。
  * **断言 (Assert)**:
    * a. 断言 HTTP 状态码为 `200`，业务 `code` 为 `200`。
    * b. 断言响应 `data` 包含正确的 `failure_id`, `task_id`, `resource_url` 等所有字段。
    * c. 断言 `data.standard_name`, `expected_path` 字段值与创建时一致。
    * d. 断言 `data.retry_count` 为 1。
    * e. 验证时间戳字段格式正确（ISO格式）。

* **`test_get_failure_details_not_found`**:
  * **准备**: 生成一个随机的 `failure_id`（使用 `uuid.uuid4()`），确保数据库中不存在该记录。
  * **执行**: 调用 `GET /api/v1/download/failures/{non_existent_failure_id}`。
        * **断言**:
    * a. 断言 HTTP 状态码为 `404`。
    * b. 断言错误信息包含 `"不存在"` 关键字。

* **`test_get_failure_details_invalid_uuid_format`**:
  * **执行**: 使用无效的UUID格式（如 `"invalid-uuid"`）调用API。
  * **断言**: 断言 HTTP 状态码为 `422`（参数验证失败）。

##### **D. 边界条件和异常测试**

* **`test_api_endpoints_with_sql_injection_attempts`**:
  * **执行**: 尝试在UUID参数中注入SQL代码（如 `"'; DROP TABLE--"`）。
  * **断言**: 断言API能正确处理并返回 422 或 400 状态码。

* **`test_api_endpoints_with_extremely_long_parameters`**:
  * **执行**: 使用超长字符串作为UUID参数。
  * **断言**: 断言API能正确处理并返回适当的错误状态码。

##### **E. 数据库状态验证要求**

所有成功的测试用例还必须包含以下数据库状态验证：

```python
# 验证数据库记录存在且字段正确
async for db in db_session:
    # 重新查询记录以验证数据库状态
    db_video = db.query(DownloadedVideo).filter(
        DownloadedVideo.video_id == test_video_id
    ).first()
    assert db_video is not None
    assert db_video.status == "completed"
    assert db_video.storage_path == expected_storage_path
```

##### **F. 测试用例命名规范**

所有测试函数必须遵循以下命名规范：
* 成功场景：`test_{endpoint_name}_success`
* 失败场景：`test_{endpoint_name}_{failure_condition}`
* 边界条件：`test_{endpoint_name}_{boundary_condition}`

例如：
* `test_get_downloaded_video_success`
* `test_get_downloaded_video_not_found`
* `test_list_all_failures_with_status_filter`

##### **G. 测试数据生成规范**

所有测试用例在创建数据库记录时，必须遵循以下数据生成规范：

```python
import uuid
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# DownloadTask 数据生成
def create_test_download_task(db_session, status=TaskStatus.COMPLETED):
    task_data = {
        "video_id": uuid.uuid4(),
        "liveroom_id": f"room_{fake.random_int(min=1000, max=9999)}",
        "liveroom_title": fake.sentence(nb_words=4),
        "liveroom_url": fake.url(),
        "resource_url": fake.url(),
        "resource_type": random.choice(["hls", "mp4", "image"]),
        "status": status,
        "progress": 1.0 if status == TaskStatus.COMPLETED else 0.0,
        "retry_count": 0,
        "last_error": None,
        "created_at": datetime.utcnow() - timedelta(hours=1),
        "updated_at": datetime.utcnow()
    }
    return DownloadTask(**task_data)

# DownloadedVideo 数据生成
def create_test_downloaded_video(db_session, task_id, video_id):
    video_data = {
        "video_id": video_id,
        "task_id": task_id,
        "liveroom_id": f"room_{fake.random_int(min=1000, max=9999)}",
        "liveroom_title": fake.sentence(nb_words=4),
        "liveroom_url": fake.url(),
        "video_type": "hls",
        "video_url": fake.url(),
        "storage_path": f"/media/video_{video_id}/hls/",
        "file_size": fake.random_int(min=1000000, max=5000000000),
        "duration": fake.random_int(min=300, max=7200),
        "resolution": random.choice(["720p", "1080p", "1440p"]),
        "format": "hls",
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    return DownloadedVideo(**video_data)

# DownloadFailure 数据生成
def create_test_download_failure(db_session, task_id):
    failure_data = {
        "task_id": task_id,
        "resource_url": fake.url(),
        "expected_path": f"/media/downloads/{fake.uuid4()}/ts/",
        "standard_name": f"segment_{fake.random_int(min=1, max=999):06d}_{fake.uuid4().hex[:8]}.ts",
        "resource_type": random.choice(["ts", "m3u8", "mp4", "image"]),
        "failure_type": random.choice(["network_error", "timeout", "file_error"]),
        "error_message": fake.sentence(nb_words=8),
        "status": random.choice(["pending", "abandoned"]),
        "retry_count": fake.random_int(min=0, max=3),
        "created_at": datetime.utcnow() - timedelta(minutes=30),
        "updated_at": datetime.utcnow()
    }
    return DownloadFailure(**failure_data)
```

##### **H. 异步测试函数模板**

所有新增的测试函数必须严格遵循以下模板：

```python
@pytest.mark.asyncio
async def test_function_name(self, async_client, db_session):
    """测试描述"""
    async for client in async_client:
        async for db in db_session:
            # === 准备 (Arrange) ===
            # 1. 清空相关表数据
            db.query(DownloadedVideo).delete()
            db.query(DownloadFailure).delete()
            db.query(DownloadTask).delete()
            db.commit()
            
            # 2. 创建测试数据
            test_task = create_test_download_task(db, status=TaskStatus.COMPLETED)
            db.add(test_task)
            db.commit()
            db.refresh(test_task)
            
            # === 执行 (Act) ===
            response = await client.get(f"/api/v1/download/videos/{test_task.video_id}")
            
            # === 断言 (Assert) ===
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 200
            
            # === 数据库状态验证 ===
            # 重新查询数据库验证状态变化
            updated_task = db.query(DownloadTask).filter_by(id=test_task.id).first()
            assert updated_task is not None
```

##### **I. 错误处理和异常场景测试规范**

```python
# 404 Not Found 测试模板
@pytest.mark.asyncio
async def test_endpoint_not_found(self, async_client, db_session):
    """测试资源不存在的情况"""
    async for client in async_client:
        async for db in db_session:
            # 使用不存在的UUID
            non_existent_id = uuid.uuid4()
            
            response = await client.get(f"/api/v1/download/videos/{non_existent_id}")
            
            assert response.status_code == 404
            error_data = response.json()
            assert "不存在" in error_data.get("message", "")

# 422 参数验证失败测试模板
@pytest.mark.asyncio
async def test_endpoint_invalid_params(self, async_client):
    """测试参数验证失败的情况"""
    async for client in async_client:
        # 使用无效的UUID格式
        response = await client.get("/api/v1/download/videos/invalid-uuid")
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
```

##### **J. 性能和负载测试要求**

每个API接口还应包含基本的性能测试：

* **`test_api_response_time`**: 验证API响应时间在合理范围内（< 2秒）
* **`test_api_with_large_dataset`**: 测试大数据量情况下的API性能
* **`test_concurrent_api_calls`**: 测试并发调用的正确性

#### **5. 最终交付 (Final Deliverable)**

请根据以上所有规范，生成以下**完整、可运行**的 Python 测试代码文件：

**`tests/test_download_api_new.py`** - 包含新增的三个API接口的完整测试用例

**必须包含的测试用例总数**: 不少于 **15个测试函数**，覆盖：
1. **GET /videos/{video_id}**: 3个测试用例（成功、404、422）
2. **GET /failures**: 5个测试用例（成功带数据、状态筛选、类型筛选、分页、空结果）  
3. **GET /failures/{failure_id}**: 3个测试用例（成功、404、422）
4. **边界条件测试**: 2个测试用例（SQL注入防护、超长参数）
5. **性能测试**: 2个测试用例（响应时间、并发调用）

**代码质量要求**:
* 每个测试函数都有详细的文档字符串
* 严格遵循异步测试规范 (`async for` 模式)
* 完整的数据隔离和清理机制
* 覆盖所有成功和失败场景
* 包含数据库状态验证
* 使用 Faker 生成随机测试数据

##### **K. 必需的导入和依赖**

生成的测试文件必须包含以下导入语句：

```python
import pytest
import uuid
import asyncio
import time
from datetime import datetime, timedelta
from faker import Faker
import random

# FastAPI 测试相关
from httpx import AsyncClient

# 应用模型和枚举
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus, FailureStatusEnum

# 确保导入所有必要的测试fixture
# 注意：这些fixture应该在conftest.py中已经定义
# async_client, db_session, test_app 等
```

##### **L. 测试类结构要求**

测试文件必须使用以下类结构：

```python
class TestDownloadApiNew:
    """新增下载服务API接口测试类"""
    
    # 所有测试方法都在这个类内部
    # 每个测试方法都必须是异步的
    # 每个测试方法都必须有 self 参数
```

##### **M. 重要注意事项**

1. **数据库事务隔离**: 每个测试函数都必须在独立的数据库事务中运行，确保测试之间不会相互影响。

2. **异步上下文管理**: 严格使用 `async for` 来管理异步fixture，不得直接使用fixture参数。

3. **错误信息验证**: 所有错误场景测试都必须验证返回的错误信息内容，不仅仅是状态码。

4. **时间戳验证**: 对于包含时间戳的API响应，必须验证时间戳格式的正确性（ISO 8601格式）。

5. **UUID验证**: 对于包含UUID的API响应，必须验证UUID格式的正确性。

6. **分页参数验证**: 对于分页接口，必须测试边界值（如page=0, size=0等）。

##### **N. 性能基准要求**

```python
# 性能测试示例
@pytest.mark.asyncio
async def test_api_performance_benchmark(self, async_client, db_session):
    """测试API响应时间基准"""
    async for client in async_client:
        async for db in db_session:
            # 准备数据...
            
            start_time = time.time()
            response = await client.get("/api/v1/download/failures")
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 2.0  # API响应时间应小于2秒
```

##### **O. 并发测试要求**

```python
# 并发测试示例
@pytest.mark.asyncio
async def test_concurrent_api_access(self, async_client, db_session):
    """测试并发访问API的安全性"""
    async for client in async_client:
        async for db in db_session:
            # 准备数据...
            
            # 创建多个并发请求
            tasks = []
            for i in range(5):
                task = asyncio.create_task(
                    client.get("/api/v1/download/failures")
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            for response in responses:
                assert response.status_code == 200
```