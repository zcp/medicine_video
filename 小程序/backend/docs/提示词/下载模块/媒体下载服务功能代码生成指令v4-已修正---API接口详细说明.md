# 媒体下载服务API接口详细说明

## 〇、核心编码规范（必读）

### 0.1. 安全异步异常处理规范
**🛡️ 在异常处理中访问ORM对象的安全规则**：

- **规则**：在任何 `try...except` 块中，如果需要在 `except` 块中使用来自数据库ORM对象（如 `current_user`、`task`）的属性进行日志记录或错误处理，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。

- **禁止**：严禁在捕获了数据库相关异常（如 `IntegrityError`、`SQLAlchemyError`）的 `except` 块中直接访问可能已与失效会话关联的ORM对象的属性。

- **实现流程**：
  ```python
  # ✅ 正确做法：在 try 块之前提取
  user_id_for_logging = current_user["user_id"]
  task_id_for_logging = str(task_id)
  
  try:
      # 数据库操作
      task = service.get_download_task(task_id, user_id_for_logging)
      # ...
  except SQLAlchemyError as e:
      # ✅ 使用之前提取的局部变量
      logger.error(f"操作失败 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}")
      db.rollback()
      # ❌ 不要在这里访问 task.id 或 current_user.id
  ```

### 0.2. 响应处理规范

#### 0.2.1. 成功响应
**✅ 所有成功返回必须调用 `create_response()` 函数**：
```python
return create_response(
    code=200,  # 或 201 for POST
    message="操作成功",
    data=result_dict
)
```

#### 0.2.2. 错误响应
**❌ 所有错误必须返回 `JSONResponse`，其 `content` 由 `create_error_response()` 构建**：
```python
from fastapi.responses import JSONResponse

return JSONResponse(
    status_code=400,
    content=create_error_response(
        code=1001,
        message="参数错误"
    )
)
```

### 0.3. 环境变量驱动配置
- 所有外部服务（Redis、数据库、第三方API）的连接信息**必须**通过环境变量读取
- 使用 `from app.core.config import settings` 读取配置
- 禁止硬编码任何连接信息

### 0.4. RESTful 设计规范
- 使用合适的 HTTP 方法（GET、POST、PUT、DELETE）
- URL 路径使用名词复数形式（`/tasks` 而非 `/task`）
- 使用嵌套路径表示资源关系（`/tasks/{task_id}/failures`）
- URL 中不包含动词，动作通过 HTTP 方法表达
- 返回统一结构的 JSON 响应

### 0.5. API端点实现通用流程
**所有API端点必须遵循以下流程**：

1. **【必须】在 `try` 块之前提取用于日志的变量**
2. **【必须】将整个业务逻辑包裹在 `try...except` 块中**
3. **【必须】使用 `create_response()` 返回成功结果**
4. **【必须】使用 `JSONResponse + create_error_response()` 返回错误**
5. **【必须】在异常处理中使用之前提取的局部变量进行日志记录**

---

## 一、任务管理接口

### 1.1 创建下载任务

* **接口**: `POST /api/v1/download/tasks`
* **描述**: 创建一个新的媒体下载任务(HLS/MP4/图片)
* **认证**: 需要用户认证

* **请求参数 (Body)**:

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `video_id` | `UUID` | 否 | 视频ID(前端可选提供,后端会重新生成) |
| `liveroom_id` | `String(20)` | 是 | 直播间ID,长度10-20字符 |
| `liveroom_title` | `String(255)` | 否 | 直播间标题 |
| `liveroom_url` | `HttpUrl` | 否 | 直播间URL |
| `resource_url` | `HttpUrl` | 是 | 资源下载URL(m3u8/mp4/image) |
| `resource_type` | `String` | 是 | 资源类型: `hls`, `mp4`, `image` |

* **成功响应 (`201 Created`)**:

```json
{
  "code": 201,
  "message": "创建下载任务成功",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-uuid",
    "video_id": "8723901837-f22d-41d4-a716-446655440001",
    "liveroom_id": "8723901837",
    "liveroom_title": "精彩直播间",
    "liveroom_url": "https://example.com/room/8723901837",
    "resource_url": "https://example.com/video.m3u8",
    "resource_type": "hls",
    "status": "pending",
    "progress": 0.0,
    "retry_count": 0,
    "last_error": null,
    "created_at": "2025-06-14T10:00:00Z",
    "updated_at": "2025-06-14T10:00:00Z",
    "completed_at": null
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

* **失败响应示例 (`400 Bad Request`)**:

```json
{
  "code": 400,
  "message": "参数错误: liveroom_id长度必须在10-20之间",
  "data": null,
  "timestamp": "2025-06-14T10:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     resource_url_for_logging = str(task_data.resource_url)
     liveroom_id_for_logging = task_data.liveroom_id
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 从请求体中获取`DownloadTaskCreate` Schema数据
     - 实例化 `DownloadService(db)`
     - 调用 `service.create_download_task(task_data, user_id=user_id_for_logging)`
     - 在数据库 `download_tasks` 表中创建新记录:
       * 自动生成任务`id` (UUID)
       * 后端重新生成`video_id` (不使用前端传入值,提高安全性)
       * 设置默认`status="pending"`
       * 设置默认`progress=0.0`
       * 设置默认`retry_count=0`
       * 自动设置`created_at`和`updated_at`为当前UTC时间
     - 将ORM对象手动转换为字典,处理UUID和datetime字段的序列化
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=201,
           message="创建下载任务成功",
           data=task_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数验证错误 - 用户ID: {user_id_for_logging}, 直播间ID: {liveroom_id_for_logging}, 错误: {str(e)}")`
       * **【核心规范0.2.2】返回JSONResponse**: `status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except IntegrityError**:
       * 记录日志: `logger.error(f"数据完整性错误 - 用户ID: {user_id_for_logging}, 资源URL: {resource_url_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=400, content=create_error_response(code=1003, message="任务已存在或数据冲突")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"数据库错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 1.2 获取下载任务列表

* **接口**: `GET /api/v1/download/tasks`
* **描述**: 分页查询当前用户的下载任务列表,支持按状态筛选和排序
* **认证**: 需要用户认证

* **请求参数 (Query)**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `Integer` | 否 | `1` | 页码,从1开始 |
| `size` | `Integer` | 否 | `10` | 每页记录数,范围1-100 |
| `status` | `TaskStatus` | 否 | `null` | 任务状态筛选: `pending`, `processing`, `completed`, `partial_completed`, `failed`, `cancelled` |
| `sort` | `String` | 否 | `created_at:desc` | 排序规则,格式: `field:direction`,如`created_at:desc,id:asc` |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取下载任务列表成功",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "pages": 3,
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "user-uuid",
        "video_id": "8723901837-f22d-41d4-a716-446655440001",
        "liveroom_id": "8723901837",
        "liveroom_title": "精彩直播间",
        "liveroom_url": "https://example.com/room/8723901837",
        "resource_url": "https://example.com/video.m3u8",
        "resource_type": "hls",
        "status": "completed",
        "progress": 1.0,
        "retry_count": 0,
        "last_error": null,
        "created_at": "2025-06-14T10:00:00Z",
        "updated_at": "2025-06-14T10:30:00Z",
        "completed_at": "2025-06-14T10:30:00Z"
      }
    ]
  },
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **失败响应示例 (`400 Bad Request`)**:

```json
{
  "code": 400,
  "message": "参数错误: page必须大于0",
  "data": null,
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     page_for_logging = page
     status_for_logging = status.value if status else "all"
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 从Query参数中获取分页参数(`PageParams`)和筛选参数(`status`)
     - 实例化 `DownloadService(db)`
     - 调用 `service.list_download_tasks(user_id_for_logging, skip=(page-1)*size, limit=size, status, sort)`:
       * 在`download_tasks`表中查询当前用户的任务
       * 应用状态筛选(如果提供)
       * 应用排序规则(解析`sort`字符串)
       * 应用分页(offset和limit)
     - 调用 `service.count_download_tasks(user_id_for_logging, status)` 获取符合条件的总记录数
     - 将查询结果(ORM对象列表)手动转换为字典列表,处理UUID和datetime序列化
     - 构造`PageResponse`对象,包含`total`, `items`, `page`, `size`, `pages`字段
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取下载任务列表成功",
           data=page_data.model_dump()
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 页码: {page_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"数据库查询错误 - 用户ID: {user_id_for_logging}, 状态筛选: {status_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 1.3 获取下载任务详情

* **接口**: `GET /api/v1/download/tasks/{task_id}`
* **描述**: 根据任务ID获取单个下载任务的详细信息
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取下载任务详情成功",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "video_id": "8723901837-f22d-41d4-a716-446655440001",
    "liveroom_id": "8723901837",
    "liveroom_title": "精彩直播间",
    "liveroom_url": "https://example.com/room/8723901837",
    "resource_url": "https://example.com/video.m3u8",
    "resource_type": "hls",
    "status": "processing",
    "progress": 0.65,
    "retry_count": 1,
    "last_error": null,
    "created_at": "2025-06-14T10:00:00Z",
    "updated_at": "2025-06-14T10:15:00Z",
    "completed_at": null
  },
  "timestamp": "2025-06-14T10:20:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:20:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.get_download_task(task_id, user_id_for_logging)`:
       * 在 `download_tasks` 表中,使用 `id=task_id` 进行查询
       * 验证任务是否属于当前用户(比对`user_id`)
       * 如果不存在或不属于当前用户,抛出`TaskNotFoundError`
     - 将ORM对象手动转换为字典,处理UUID和datetime序列化
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取下载任务详情成功",
           data=task_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"数据库查询错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 1.4 更新下载任务

* **接口**: `PUT /api/v1/download/tasks/{task_id}`
* **描述**: 更新指定下载任务的可修改字段
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **请求参数 (Body)**:

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `status` | `TaskStatus` | 否 | 任务状态 |
| `max_retries` | `Integer` | 否 | 最大重试次数,范围1-10 |
| `priority` | `Integer` | 否 | 下载优先级,范围0-100 |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "更新下载任务成功",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "updated_at": "2025-06-14T10:25:00Z"
  },
  "timestamp": "2025-06-14T10:25:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:25:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     update_fields_for_logging = str(task_data.model_dump(exclude_unset=True).keys())
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.update_download_task(task_id, task_data, user_id_for_logging)`:
       * 首先调用`get_download_task`验证任务存在且属于当前用户
       * 遍历`task_data.model_dump(exclude_unset=True)`,仅更新提供的字段
       * 自动更新`updated_at`字段为当前UTC时间
       * 提交事务并刷新对象
     - 将更新后的任务转换为字典
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="更新下载任务成功",
           data=task_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 更新字段: {update_fields_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"数据库更新错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库更新失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 1.5 删除下载任务

* **接口**: `DELETE /api/v1/download/tasks/{task_id}`
* **描述**: 删除指定的下载任务(仅允许删除非completed状态的任务)
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "删除下载任务成功",
  "data": null,
  "timestamp": "2025-06-14T10:30:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:30:00Z"
}
```

* **失败响应示例 (`400 Bad Request`)**:

```json
{
  "code": 400,
  "message": "不能删除已完成任务",
  "data": null,
  "timestamp": "2025-06-14T10:30:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.get_download_task(task_id, user_id_for_logging)` 验证任务存在且属于当前用户
     - 检查任务状态:
       * 如果`task.status == TaskStatus.COMPLETED`,抛出`ValueError("不能删除已完成任务")`
     - 调用 `service.delete_download_task(task_id, user_id_for_logging)`:
       * 从`download_tasks`表中删除记录
       * 由于设置了级联删除,相关的`download_failures`和`downloaded_videos`记录也会被删除
       * 提交事务
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="删除下载任务成功",
           data=None
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except ValueError** (如"不能删除已完成任务"):
       * 记录日志: `logger.warning(f"业务规则错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"数据库删除错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库删除失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 1.6 启动下载任务

* **接口**: `POST /api/v1/download/tasks/{task_id}/start`
* **描述**: 明确地开始一个pending状态的任务,将其交给后台工作队列执行
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "下载任务成功",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "video_id": "8723901837-f22d-41d4-a716-446655440001",
    "liveroom_id": "8723901837",
    "liveroom_title": "精彩直播间",
    "liveroom_url": "https://example.com/room/8723901837",
    "resource_url": "https://example.com/video.m3u8",
    "resource_type": "hls",
    "status": "processing",
    "progress": 0.0,
    "retry_count": 0,
    "last_error": null,
    "created_at": "2025-06-14T10:00:00Z",
    "updated_at": "2025-06-14T10:35:00Z",
    "completed_at": null
  },
  "timestamp": "2025-06-14T10:35:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:35:00Z"
}
```

* **实现流程描述**:
  1. 校验用户认证信息(`get_current_user`)。
  2. 从路径参数中获取 `task_id`。
  3. 实例化 `DownloadService(db)`。
  4. 调用 `service.start_download_task(task_id, user_id)`:
     - 验证任务存在且属于当前用户
     - 检查任务状态必须是`pending`, `failed`, 或 `partial_completed`之一
     - **【关键】更新任务状态为`processing`（必须包含异常保护）**:
       * 包裹在try-except块中
       * 设置`task.status = TaskStatus.PROCESSING`
       * 设置`task.updated_at = datetime.utcnow()`
       * 执行`self.db.commit()`
       * 执行`self.db.refresh(task)`
       * 如果捕获`SQLAlchemyError`: 记录错误日志"更新任务状态为PROCESSING失败 - 任务ID: {task_id}, 错误: {str(e)}"，执行`self.db.rollback()`，抛出`DatabaseError("无法启动任务: {str(e)}")`
     - **【新增】视频去重检查**（包含异常处理）:
       * **try块**: 
         - 查询`downloaded_videos`表中是否存在`video_url == task.resource_url`且`status IN ('completed', 'partial_completed')`的记录
         - 如果找到已完成或部分完成的视频:
           * 记录日志: "视频去重命中 - 任务ID: {task_id}, resource_url: {resource_url}, 已存在视频ID: {existing_video_id}, 已存在视频状态: {existing_video.status}"
           * 根据已存在视频的状态设置任务状态:
             - 如果existing_video.status='completed': 任务标记为`completed`,设置`progress=1.0`
             - 如果existing_video.status='partial_completed': 任务标记为`partial_completed`,progress保持原有值
           * 设置`completed_at=当前时间`
           * 创建新的`downloaded_video`记录,关联到当前任务(`task_id=task.id`),但复用已存在视频的`storage_path`、`file_size`、`status`等字段
           * **关键字段处理**: `liveroom_title`使用`str(task.liveroom_title)`转换,`liveroom_url`使用`task.resource_url`,`status`使用`existing_video.status`
           * 提交事务并返回任务(跳过后续下载流程)
           * 记录完成日志: "任务 {task_id} 通过视频去重完成 - 最终状态: {task.status}, 视频状态: {existing_video.status}"
       * **except SQLAlchemyError**: 
         - 记录警告日志: "视频去重检查失败 - 任务ID: {task_id}, 错误: {error}, 将继续正常下载流程"
         - 执行`db.rollback()`回滚可能的部分更改
         - 执行`db.refresh(task)`重新刷新任务对象
         - 继续正常下载流程(不抛出异常)
       * **except Exception**: 
         - 记录错误日志(包含完整堆栈): "视频去重检查发生未预期错误 - 任务ID: {task_id}, 错误类型: {type}, 错误信息: {error}, 将继续正常下载流程"
         - 执行`db.rollback()`
         - 执行`db.refresh(task)`
         - 继续正常下载流程(不抛出异常)
       * 如果未找到或找到的视频状态是`failed`,继续正常下载流程
     - **【关键】下载执行（必须包含异常保护）**:
       * 整个下载执行包裹在try-except-finally块中
       * 根据`resource_type`调用相应的下载方法:
         - `hls`: 调用`download_m3u8()`下载m3u8索引和所有ts分片
         - `mp4`: 调用`download_mp4_image()`下载MP4文件
         - `image`: 调用`download_mp4_image()`下载图片文件
       * 调用结果处理方法（必须有外层异常保护）:
         - `_process_download_m3u8_result()` - 根据失败分片比例决定最终状态，需要有自己的try-except和rollback
         - `_process_download_mp4_result()` - 根据下载成功与否决定状态，需要有自己的try-except和rollback
         - `_process_download_image_result()` - 根据下载成功与否决定状态，需要有自己的try-except和rollback
       * **except块**（捕获所有下载和处理异常）:
         - 记录错误日志: "Task {task_id} execution failed critically: {e}"，包含完整堆栈(`exc_info=True`)
         - 执行`self.db.rollback()`回滚可能的部分更改，清理session
         - 执行`self.db.refresh(task)`重新获取task对象，确保状态正确
         - 设置`task.status = TaskStatus.FAILED`
         - 设置`task.last_error = str(e)`
         - 设置`task.updated_at = datetime.utcnow()`
         - 尝试创建失败记录（嵌套try-except块）:
           * 调用`self.create_download_failure()`
           * 如果创建失败记录也失败，记录错误日志"创建失败记录时发生错误 - 任务ID: {task_id}, 错误: {str(failure_error)}"，包含堆栈，但不中断流程
       * **finally块**:
         - 无论成功或失败，都执行`self.db.commit()`提交最后的更改
         - 执行`self.db.refresh(task)`刷新对象状态
  5. 将返回的任务对象转换为字典。
  6. 使用`create_response(code=200, message="下载任务成功", data=task_dict)`返回。
  7. **异常处理**: 
     - `TaskNotFoundError`: 返回404错误
     - 下载过程异常: 由上述except块处理，记录日志、rollback、更新任务状态为`failed`、创建失败记录
  8. **性能优化建议**: 为`downloaded_videos`表的`(video_url, status)`创建组合索引以提高去重查询性能

### 1.7 重试下载任务

* **接口**: `POST /api/v1/download/tasks/{task_id}/retry`
* **描述**: 重试失败或部分完成的下载任务,智能判断是全量重试还是仅重试失败分片
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "重试下载任务成功",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "video_id": "8723901837-f22d-41d4-a716-446655440001",
    "liveroom_id": "8723901837",
    "liveroom_title": "精彩直播间",
    "liveroom_url": "https://example.com/room/8723901837",
    "resource_url": "https://example.com/video.m3u8",
    "resource_type": "hls",
    "status": "completed",
    "progress": 1.0,
    "retry_count": 1,
    "last_error": null,
    "created_at": "2025-06-14T10:00:00Z",
    "updated_at": "2025-06-14T10:45:00Z",
    "completed_at": "2025-06-14T10:45:00Z"
  },
  "timestamp": "2025-06-14T10:45:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:45:00Z"
}
```

* **失败响应示例 (`400 Bad Request`)**:

```json
{
  "code": 400,
  "message": "重试次数已达上限",
  "data": null,
  "timestamp": "2025-06-14T10:45:00Z"
}
```

* **实现流程描述**:
  1. 校验用户认证信息(`get_current_user`)。
  2. 从路径参数中获取 `task_id`。
  3. 实例化 `DownloadService(db)`。
  4. 调用 `service.retry_download_task(task_id, user_id)` - **整个函数必须包裹在try-except块中**:
     - **try块**:
       * 验证任务存在且属于当前用户(`get_download_task`)
       * 检查任务状态必须是`failed`或`partial_completed`
       * 检查`retry_count`是否超过最大重试次数(3次),超过则抛出`ValueError`
       * 查询`download_failures`表中所有`status='pending'`的失败记录
       * **智能重试策略**:
         - 如果存在m3u8/mp4/image级别的失败: 清空所有失败记录（commit），调用`start_download_task()`全量重新下载
         - 如果仅存在ts分片级别的失败: 调用`_retry_only_failed_segments()`仅重试失败的ts分片
       * 更新`retry_count += 1`
       * 根据重试结果更新任务状态:
         - 全部成功: 状态改为`completed`，删除所有失败记录，更新`downloaded_videos`状态
         - 部分成功: 状态保持`partial_completed`，更新失败记录的`retry_count`
         - 全部失败: 失败记录的`retry_count >= 3`时，将其`status`改为`abandoned`
       * 执行多个commit操作（每个都需要在安全的上下文中）
     - **except ValueError块**（业务逻辑异常，如重试次数超限）:
       * 记录日志
       * 直接重新抛出（不需要rollback，因为没有数据库修改）
     - **except SQLAlchemyError块**（数据库异常）:
       * 记录错误日志: "重试任务时数据库错误 - 任务ID: {task_id}, 错误: {str(e)}"，包含完整堆栈(`exc_info=True`)
       * 执行`self.db.rollback()`
       * 抛出`DatabaseError(f"Database error: {str(e)}")`
     - **except Exception块**（其他未预期异常）:
       * 记录错误日志: "重试任务时发生未预期错误 - 任务ID: {task_id}, 错误类型: {type(e).__name__}, 错误: {str(e)}"，包含完整堆栈
       * 执行`self.db.rollback()`
       * 重新抛出异常
  5. 将返回的任务对象转换为字典。
  6. 使用`create_response(code=200, message="重试下载任务成功", data=task_dict)`返回。
  7. **异常处理**: 
     - `TaskNotFoundError`: 返回404错误
     - `ValueError`(重试次数超限): 返回400错误
     - `DatabaseError`/`SQLAlchemyError`: 记录日志，回滚事务，返回500错误

### 1.8 批量导入下载任务（CSV）

* **接口**: `POST /api/v1/download/tasks/batch-import`
* **描述**: 通过上传CSV文件批量创建下载任务
* **认证**: 需要用户认证
* **Content-Type**: `multipart/form-data`

* **请求参数 (Form Data)**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `file` | `File` | 是 | - | CSV文件，最大10MB |
| `skip_duplicates` | `Boolean` | 否 | `false` | 是否跳过重复的任务组合（基于resource_url + liveroom_id + liveroom_title，默认false，重复时报错） |
| `auto_start` | `Boolean` | 否 | `false` | 导入后是否自动启动任务（默认false） |

* **CSV文件格式要求**:
  - **文件编码**: UTF-8
  - **分隔符**: 逗号(`,`)
  - **表头行**: 必须包含（第一行）
  - **最大行数**: 1000行（不含表头）
  - **最大文件大小**: 10MB

* **必需列**:
  - `liveroom_id`: 直播间ID，长度10-20字符
  - `resource_url`: 资源下载URL
  - `resource_type`: 资源类型（hls/mp4/image）

* **可选列**:
  - `liveroom_title`: 直播间标题，最大255字符
  - `liveroom_url`: 直播间URL

* **CSV示例**:
```csv
liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
8723901837,精彩直播间1,https://example.com/room/8723901837,https://example.com/video1.m3u8,hls
8723901838,精彩直播间2,https://example.com/room/8723901838,https://example.com/video2.mp4,mp4
8723901839,精彩直播间3,https://example.com/room/8723901839,https://example.com/cover.jpg,image
```

* **成功响应 (`201 Created`)**:

```json
{
  "code": 201,
  "message": "批量导入任务成功",
  "data": {
    "total": 100,
    "success": 95,
    "failed": 5,
    "skipped": 3,
    "created_task_ids": [
      "550e8400-e29b-41d4-a716-446655440001",
      "550e8400-e29b-41d4-a716-446655440002"
    ],
    "failed_rows": [
      {
        "row": 10,
        "liveroom_id": "123",
        "resource_url": "https://example.com/invalid.m3u8",
        "error": "liveroom_id长度必须在10-20之间"
      }
    ],
    "skipped_rows": [
      {
        "row": 5,
        "liveroom_id": "8723901837",
        "resource_url": "https://example.com/duplicate.m3u8",
        "reason": "resource_url已存在"
      }
    ],
    "processing_time": 2.5
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

* **失败响应示例 (`207 Multi-Status` - 部分成功)**:

```json
{
  "code": 207,
  "message": "批量导入部分成功",
  "data": {
    "total": 100,
    "success": 80,
    "failed": 20,
    "skipped": 0,
    "created_task_ids": ["..."],
    "failed_rows": [
      {
        "row": 15,
        "liveroom_id": "invalid",
        "resource_url": "https://example.com/video.m3u8",
        "error": "liveroom_id长度必须在10-20之间"
      }
    ],
    "processing_time": 5.2
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

* **失败响应示例 (`400 Bad Request` - 文件格式错误)**:

```json
{
  "code": 400,
  "message": "CSV文件格式错误: 缺少必需列 resource_url",
  "data": {
    "required_columns": ["liveroom_id", "resource_url", "resource_type"],
    "missing_columns": ["resource_url"]
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

* **失败响应示例 (`413 Payload Too Large` - 文件过大)**:

```json
{
  "code": 413,
  "message": "文件大小超过限制，最大允许10MB",
  "data": {
    "file_size": 15728640,
    "max_size": 10485760
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     file_name_for_logging = file.filename if file else "unknown"
     skip_duplicates_for_logging = skip_duplicates
     auto_start_for_logging = auto_start
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块 - 文件验证**:
     - 检查文件扩展名（必须是.csv），否则抛出`ValueError("文件类型错误，必须是CSV文件")`
     - 检查文件大小（≤10MB），超过抛出`ValueError("文件大小超过限制，最大允许10MB")`
     - 检查文件不为空，否则抛出`ValueError("文件不能为空")`
  4. **try块 - 业务处理**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.batch_import_tasks_from_csv(file_content, user_id_for_logging, skip_duplicates, auto_start)`:
     - 使用UTF-8编码解码文件内容
     - 使用`csv.DictReader`解析CSV
     - 验证表头必需列：`liveroom_id`, `resource_url`, `resource_type`
     - 如果缺少必需列，抛出ValueError并返回400错误
     - 检查CSV是否为空（除表头外无数据行），如果为空返回400错误
     - **逐行处理**（关键：单行错误不中断，继续处理下一行）:
       * 统计变量初始化：`total=0`, `success=0`, `failed=0`, `skipped=0`
       * 对每一行（从第2行开始，第1行是表头）:
         - `total += 1`
         - 检查行数是否超过1000行，超过则抛出ValueError
        - 提取并去除首尾空格：`liveroom_id`, `resource_url`, `resource_type`, `liveroom_title`, `liveroom_url`
        - **验证必填字段**：如果任何必填字段为空，记录到`failed_rows`，`failed += 1`，使用`continue`跳过本行继续下一行
        - **去重检查**（如果`skip_duplicates=true`）：
          * 查询`DownloadTask`表中是否存在相同的任务组合（`user_id` + `resource_url` + `liveroom_id` + `liveroom_title`）
          * **理由**: 同一视频链接可能被不同直播间使用，需要从任务维度（而非视频维度）进行去重
          * **实现**: 构建动态查询条件，处理`liveroom_title`可能为空的情况
          * 如果存在，记录到`skipped_rows`，`skipped += 1`，使用`continue`跳过本行
        - **构造任务数据**：使用`DownloadTaskCreate` Schema验证数据
         - **创建任务**：调用`create_download_task(task_data, user_id)`
         - **记录成功**：将任务ID添加到`created_task_ids`，`success += 1`
         - **批量提交**：每处理100行提交一次事务（`if success % 100 == 0: db.commit()`）
         - **自动启动**（如果`auto_start=true`）：
           * 调用`start_download_task(task.id, user_id)`
           * 如果启动失败，记录警告日志但不影响导入（使用try-except捕获）
         - **异常处理**（关键：捕获单行异常，不中断整体流程）:
           * 捕获`ValidationError`：记录到`failed_rows`，`failed += 1`，使用`continue`继续下一行
           * 捕获其他`Exception`：记录到`failed_rows`，`failed += 1`，使用`continue`继续下一行
     - 最终提交事务（`db.commit()`）
     - 记录日志：`logger.info(f"批量导入完成 - 用户ID: {user_id_for_logging}, 总数: {total}, 成功: {success}, 失败: {failed}, 跳过: {skipped}")`
     - 返回结果字典：`total`, `success`, `failed`, `skipped`, `created_task_ids`（最多前100个）, `failed_rows`, `skipped_rows`, `processing_time`
  5. **try块 - 返回响应**:
     - **【核心规范0.2.1】根据结果使用不同的响应**:
       * 如果`success == 0`：
         ```python
         return JSONResponse(
             status_code=400,
             content=create_error_response(code=1001, message="批量导入失败，所有行都处理失败", data=result_dict)
         )
         ```
       * 如果`0 < failed < total`：
         ```python
         return JSONResponse(
             status_code=207,
             content=create_response(code=207, message="批量导入部分成功", data=result_dict)
         )
         ```
       * 如果`failed == 0`：
         ```python
         return create_response(code=201, message="批量导入任务成功", data=result_dict)
         ```
  6. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except UnicodeDecodeError**:
       * 记录日志: `logger.warning(f"文件编码错误 - 用户ID: {user_id_for_logging}, 文件名: {file_name_for_logging}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message="文件编码错误，请使用UTF-8编码")`
     - **except csv.Error**:
       * 记录日志: `logger.warning(f"CSV格式错误 - 用户ID: {user_id_for_logging}, 文件名: {file_name_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message="CSV文件格式错误")`
     - **except ValueError** (文件验证错误):
       * 记录日志: `logger.warning(f"文件验证错误 - 用户ID: {user_id_for_logging}, 文件名: {file_name_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"批量导入数据库错误 - 用户ID: {user_id_for_logging}, 文件名: {file_name_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"批量导入未知错误 - 用户ID: {user_id_for_logging}, 文件名: {file_name_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`
  7. **错误隔离机制**（重要）：
     - **单行失败不影响其他行**：每行数据的处理都在try-except块中，捕获异常后使用`continue`继续处理下一行
     - **详细错误记录**：每个失败行都记录行号、数据和错误信息到`failed_rows`数组
     - **事务保证**：使用批量提交（每100行）和最终提交确保数据一致性
     - **资源释放**：发生严重异常时回滚事务（`db.rollback()`）

## 二、失败记录管理接口

### 2.1 创建下载失败记录

* **接口**: `POST /api/v1/download/tasks/{task_id}/failures`
* **描述**: (系统内部使用)为指定任务创建一条下载失败记录
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 关联的下载任务ID |

* **请求参数 (Body)**:

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `task_id` | `UUID` | 是 | 关联的下载任务ID |
| `resource_url` | `String(Text)` | 是 | 原始资源地址(URL) |
| `expected_path` | `String(Text)` | 是 | 希望保存的路径(用于重试时定位) |
| `standard_name` | `String` | 否 | 标准化文件名 |
| `resource_type` | `String(20)` | 是 | 资源类型: `ts`, `m3u8`, `mp4`, `image` |
| `failure_type` | `String(50)` | 是 | 失败类型: `network_error`, `timeout`, `invalid_content`, `storage_error`, `permission_error` |
| `error_message` | `String(Text)` | 是 | 错误信息 |
| `retry_count` | `Integer` | 是 | 当前重试次数,初始为0 |

* **成功响应 (`201 Created`)**:

```json
{
  "code": 201,
  "message": "创建下载失败记录成功",
  "data": {
    "id": "failure-uuid",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "resource_url": "https://example.com/ts/seg_0042.ts",
    "expected_path": "/media/video_8723901837_f22d/hls/ts/",
    "resource_type": "ts",
    "failure_type": "timeout",
    "error_message": "Connection timed out after 30 seconds",
    "status": "pending",
    "retry_count": 0,
    "created_at": "2025-06-14T10:05:00Z",
    "updated_at": "2025-06-14T10:05:00Z"
  },
  "timestamp": "2025-06-14T10:05:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:05:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     resource_url_for_logging = failure_data.resource_url
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.create_download_failure(task_id, failure_data, user_id_for_logging)`:
       * 首先验证任务存在且属于当前用户
       * 在 `download_failures` 表中创建新记录:
         - 自动生成`id` (UUID)
         - 设置默认`status="pending"`
         - 设置`retry_count`初始值
         - 自动设置`created_at`和`updated_at`为当前UTC时间
       * 提交事务并刷新对象
     - 将ORM对象转换为字典,处理UUID和datetime序列化
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=201,
           message="创建下载失败记录成功",
           data=failure_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"创建失败记录数据库错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.2 获取任务的失败记录列表

* **接口**: `GET /api/v1/download/tasks/{task_id}/failures`
* **描述**: 分页查询指定任务的所有下载失败记录
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **请求参数 (Query)**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `Integer` | 否 | `1` | 页码,从1开始 |
| `size` | `Integer` | 否 | `10` | 每页记录数,范围1-100 |
| `sort` | `String` | 否 | `created_at:desc` | 排序规则,格式: `field:direction` |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取下载失败记录列表成功",
  "data": {
    "total": 5,
    "page": 1,
    "size": 10,
    "pages": 1,
    "items": [
      {
        "id": "failure-uuid-1",
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "resource_url": "https://example.com/ts/seg_0042.ts",
        "expected_path": "/media/video_8723901837_f22d/hls/ts/",
        "resource_type": "ts",
        "failure_type": "timeout",
        "error_message": "Connection timed out after 30 seconds",
        "status": "pending",
        "retry_count": 1,
        "created_at": "2025-06-14T10:05:00Z",
        "updated_at": "2025-06-14T10:10:00Z"
      }
    ]
  },
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     page_for_logging = page
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.list_download_failures(task_id, user_id_for_logging, skip, limit, sort)`:
       * 首先验证任务存在且属于当前用户
       * 在`download_failures`表中查询`task_id`匹配的记录
       * 应用排序规则
       * 应用分页(offset和limit)
     - 调用 `service.count_download_failures(task_id, user_id_for_logging)` 获取总记录数
     - 将查询结果转换为字典列表,处理UUID和datetime序列化
     - 构造`PageResponse`对象
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取下载失败记录列表成功",
           data=page_data.model_dump()
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 页码: {page_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"查询失败记录数据库错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.3 查询所有失败记录(全局分页)

* **接口**: `GET /api/v1/download/failures`
* **描述**: 分页查询当前用户所有任务的失败记录,支持按状态和失败类型筛选
* **认证**: 需要用户认证

* **请求参数 (Query)**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `Integer` | 否 | `1` | 页码,从1开始 |
| `size` | `Integer` | 否 | `10` | 每页记录数,范围1-100 |
| `status` | `String(20)` | 否 | `null` | 失败记录状态筛选: `pending`, `retrying`, `abandoned` |
| `failure_type` | `String(50)` | 否 | `null` | 失败类型筛选: `network_error`, `timeout`, `invalid_content`, `storage_error`, `permission_error` |
| `sort` | `String` | 否 | `created_at:desc` | 排序规则 |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取全局失败记录列表成功",
  "data": {
    "total": 15,
    "page": 1,
    "size": 10,
    "pages": 2,
    "items": [
      {
        "failure_id": "failure-uuid-1",
        "task_id": "task-uuid-1",
        "resource_url": "https://example.com/ts/seg_0042.ts",
        "expected_path": "/media/video_8723901837_f22d/hls/ts/",
        "standard_name": "segment_000042_8723901837_f22d_fetch_20250614T100000.ts",
        "resource_type": "ts",
        "failure_type": "timeout",
        "error_message": "Connection timed out after 30 seconds",
        "status": "pending",
        "retry_count": 1,
        "created_at": "2025-06-14T10:05:00Z",
        "updated_at": "2025-06-14T10:10:00Z"
      }
    ]
  },
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **失败响应示例 (`500 Internal Server Error`)**:

```json
{
  "code": 500,
  "message": "服务器内部错误",
  "data": null,
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     page_for_logging = page
     status_for_logging = status if status else "all"
     failure_type_for_logging = failure_type if failure_type else "all"
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.list_failures(user_id_for_logging, skip, limit, status, failure_type, sort)`:
       * 构建基础查询: `db.query(DownloadFailure).join(DownloadTask)`
       * 添加用户ID过滤: `filter(DownloadTask.user_id == user_id_for_logging)`
       * 如果提供`status`,添加状态筛选
       * 如果提供`failure_type`,添加类型筛选
       * 应用排序和分页
     - 将结果转换为字典列表
     - 构造`PageResponse`对象
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取全局失败记录列表成功",
           data=page_data.model_dump()
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 页码: {page_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"查询全局失败记录数据库错误 - 用户ID: {user_id_for_logging}, 状态: {status_for_logging}, 类型: {failure_type_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.4 查询单个失败记录详情

* **接口**: `GET /api/v1/download/failures/{failure_id}`
* **描述**: 根据`failure_id`获取单个失败下载记录的详细信息
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `failure_id` | `UUID` | 失败记录的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取失败记录详情成功",
  "data": {
    "failure_id": "failure-uuid-1",
    "task_id": "task-uuid-1",
    "resource_url": "https://example.com/ts/seg_0042.ts",
    "expected_path": "/media/video_8723901837_f22d/hls/ts/",
    "standard_name": "segment_000042_8723901837_f22d_fetch_20250614T100000.ts",
    "resource_type": "ts",
    "failure_type": "timeout",
    "error_message": "Connection timed out after 30 seconds",
    "status": "pending",
    "retry_count": 1,
    "created_at": "2025-06-14T10:05:00Z",
    "updated_at": "2025-06-14T10:10:00Z"
  },
  "timestamp": "2025-06-14T11:05:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "失败记录不存在",
  "data": null,
  "timestamp": "2025-06-14T11:06:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     failure_id_for_logging = str(failure_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.get_failure_details(failure_id, user_id_for_logging)`:
       * 在 `download_failures` 表中,使用 `id=failure_id` 进行查询
       * 如果不存在,抛出`FailureRecordNotFoundError`
       * 通过`task_id`验证关联的任务是否属于当前用户
     - 将找到的记录转换为字典,处理UUID和datetime序列化
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取失败记录详情成功",
           data=failure_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except FailureRecordNotFoundError**:
       * 记录日志: `logger.warning(f"失败记录不存在 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="失败记录不存在")`
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在或无权限 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"查询失败记录数据库错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.5 重试特定失败记录(任务级)

* **接口**: `POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry`
* **描述**: 重试指定任务下的特定失败记录
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |
| `failure_id` | `UUID` | 失败记录的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "重试失败记录成功",
  "data": {
    "id": "failure-uuid-1",
    "task_id": "task-uuid-1",
    "resource_url": "https://example.com/ts/seg_0042.ts",
    "expected_path": "/media/video_8723901837_f22d/hls/ts/",
    "resource_type": "ts",
    "failure_type": "timeout",
    "error_message": "Connection timed out after 30 seconds",
    "status": "pending",
    "retry_count": 2,
    "created_at": "2025-06-14T10:05:00Z",
    "updated_at": "2025-06-14T10:50:00Z"
  },
  "timestamp": "2025-06-14T10:50:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "失败记录不存在",
  "data": null,
  "timestamp": "2025-06-14T10:50:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     failure_id_for_logging = str(failure_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.retry_download_failure(failure_id, user_id_for_logging)`:
       * 调用`get_download_failure(failure_id, user_id_for_logging)`获取失败记录
       * 验证失败记录存在且关联的任务属于当前用户
       * 更新失败记录:
         - `retry_count += 1`
         - `status = "pending"`
         - `updated_at = 当前UTC时间`
       * 提交事务并刷新对象
     - 将返回的失败记录转换为字典
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="重试失败记录成功",
           data=failure_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except FailureRecordNotFoundError**:
       * 记录日志: `logger.warning(f"失败记录不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="失败记录不存在")`
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在或无权限 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"重试失败记录数据库错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.6 放弃特定失败记录(任务级)

* **接口**: `POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon`
* **描述**: 放弃指定任务下的特定失败记录,不再重试
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |
| `failure_id` | `UUID` | 失败记录的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "放弃失败记录成功",
  "data": {
    "id": "failure-uuid-1",
    "task_id": "task-uuid-1",
    "resource_url": "https://example.com/ts/seg_0042.ts",
    "expected_path": "/media/video_8723901837_f22d/hls/ts/",
    "resource_type": "ts",
    "failure_type": "timeout",
    "error_message": "Connection timed out after 30 seconds",
    "status": "abandoned",
    "retry_count": 3,
    "created_at": "2025-06-14T10:05:00Z",
    "updated_at": "2025-06-14T10:55:00Z"
  },
  "timestamp": "2025-06-14T10:55:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "失败记录不存在",
  "data": null,
  "timestamp": "2025-06-14T10:55:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     failure_id_for_logging = str(failure_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.abandon_download_failure(failure_id, user_id_for_logging)`:
       * 调用`get_download_failure(failure_id, user_id_for_logging)`获取失败记录
       * 验证失败记录存在且关联的任务属于当前用户
       * 更新失败记录:
         - `status = FailureStatusEnum.ABANDONED`
         - `updated_at = 当前UTC时间`
       * 提交事务并刷新对象
     - 将返回的失败记录转换为字典
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="放弃失败记录成功",
           data=failure_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except FailureRecordNotFoundError**:
       * 记录日志: `logger.warning(f"失败记录不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="失败记录不存在")`
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在或无权限 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"放弃失败记录数据库错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.7 重试失败记录(全局)

* **接口**: `POST /api/v1/download/failures/{failure_id}/retry`
* **描述**: 重试指定的失败记录(不需要指定task_id)
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `failure_id` | `UUID` | 失败记录的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "重试失败记录成功",
  "data": {
    "id": "failure-uuid-1",
    "task_id": "task-uuid-1",
    "resource_url": "https://example.com/ts/seg_0042.ts",
    "expected_path": "/media/video_8723901837_f22d/hls/ts/",
    "resource_type": "ts",
    "failure_type": "timeout",
    "error_message": "Connection timed out after 30 seconds",
    "status": "pending",
    "retry_count": 2,
    "created_at": "2025-06-14T10:05:00Z",
    "updated_at": "2025-06-14T11:00:00Z"
  },
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "失败记录不存在",
  "data": null,
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     failure_id_for_logging = str(failure_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.retry_download_failure(failure_id, user_id_for_logging)`:
       * 调用`get_download_failure(failure_id, user_id_for_logging)`获取失败记录
       * 验证失败记录存在且关联的任务属于当前用户
       * 更新失败记录:
         - `retry_count += 1`
         - `status = "pending"`
         - `updated_at = 当前UTC时间`
       * 提交事务并刷新对象
     - 将返回的失败记录转换为字典
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="重试失败记录成功",
           data=failure_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except FailureRecordNotFoundError**:
       * 记录日志: `logger.warning(f"失败记录不存在 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="失败记录不存在")`
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在或无权限 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"重试失败记录数据库错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 2.8 放弃失败记录(全局)

* **接口**: `POST /api/v1/download/failures/{failure_id}/abandon`
* **描述**: 放弃指定的失败记录,不再重试(不需要指定task_id)
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `failure_id` | `UUID` | 失败记录的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "放弃失败记录成功",
  "data": {
    "id": "failure-uuid-1",
    "task_id": "task-uuid-1",
    "resource_url": "https://example.com/ts/seg_0042.ts",
    "expected_path": "/media/video_8723901837_f22d/hls/ts/",
    "resource_type": "ts",
    "failure_type": "timeout",
    "error_message": "Connection timed out after 30 seconds",
    "status": "abandoned",
    "retry_count": 3,
    "created_at": "2025-06-14T10:05:00Z",
    "updated_at": "2025-06-14T11:05:00Z"
  },
  "timestamp": "2025-06-14T11:05:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "失败记录不存在",
  "data": null,
  "timestamp": "2025-06-14T11:05:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     failure_id_for_logging = str(failure_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.abandon_download_failure(failure_id, user_id_for_logging)`:
       * 调用`get_download_failure(failure_id, user_id_for_logging)`获取失败记录
       * 验证失败记录存在且关联的任务属于当前用户
       * 更新失败记录:
         - `status = FailureStatusEnum.ABANDONED`
         - `updated_at = 当前UTC时间`
       * 提交事务并刷新对象
     - 将返回的失败记录转换为字典
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="放弃失败记录成功",
           data=failure_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except FailureRecordNotFoundError**:
       * 记录日志: `logger.warning(f"失败记录不存在 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="失败记录不存在")`
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在或无权限 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"放弃失败记录数据库错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 失败记录ID: {failure_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

## 三、已下载视频管理接口

### 3.1 创建已下载视频记录

* **接口**: `POST /api/v1/download/tasks/{task_id}/videos`
* **描述**: (系统内部使用)为指定任务创建一条已下载视频记录
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 关联的下载任务ID |

* **请求参数 (Body)**:

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `video_id` | `UUID` | 是 | 视频ID |
| `liveroom_id` | `String(20)` | 是 | 直播间ID |
| `liveroom_title` | `String(255)` | 否 | 直播间标题 |
| `liveroom_url` | `HttpUrl` | 否 | 直播间URL |
| `video_type` | `String(20)` | 是 | 视频类型: `hls`, `mp4` |
| `video_url` | `String(255)` | 是 | 原始视频URL |
| `storage_path` | `String(255)` | 是 | 存储路径,遵循存储目录结构规范 |
| `file_size` | `BigInteger` | 否 | 文件大小(字节) |
| `duration` | `Integer` | 否 | 视频时长(秒) |
| `resolution` | `String(20)` | 否 | 视频分辨率 |
| `format` | `String(20)` | 否 | 视频格式 |
| `status` | `String(20)` | 是 | 状态: `completed`, `partial_completed`, `failed` |

* **成功响应 (`201 Created`)**:

```json
{
  "code": 201,
  "message": "创建已下载视频记录成功",
  "data": {
    "id": "video-record-uuid",
    "video_id": "8723901837-f22d-41d4-a716-446655440001",
    "liveroom_id": "8723901837",
    "liveroom_title": "精彩直播间",
    "liveroom_url": "https://example.com/room/8723901837",
    "video_type": "hls",
    "video_url": "https://example.com/video.m3u8",
    "storage_path": "/media/video_8723901837_f22d/hls/",
    "file_size": 1073741824,
    "duration": 3600,
    "resolution": "1080p",
    "format": "hls",
    "status": "completed",
    "created_at": "2025-06-14T10:30:00Z",
    "updated_at": "2025-06-14T10:30:00Z"
  },
  "timestamp": "2025-06-14T10:30:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T10:30:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     video_url_for_logging = str(video_data.video_url)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.create_downloaded_video(task_id, video_data, user_id_for_logging)`:
       * 首先验证任务存在且属于当前用户
       * 在 `downloaded_videos` 表中创建新记录:
         - 自动生成`id` (UUID)
         - 设置`task_id`关联到下载任务
         - 自动设置`created_at`和`updated_at`为当前UTC时间
       * 提交事务并刷新对象
     - 将ORM对象转换为字典,处理UUID和datetime序列化
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=201,
           message="创建已下载视频记录成功",
           data=video_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"创建视频记录数据库错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 视频URL: {video_url_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 执行`db.rollback()`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库操作失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 3.2 获取任务的已下载视频列表

* **接口**: `GET /api/v1/download/tasks/{task_id}/videos`
* **描述**: 分页查询指定任务的所有已下载视频记录
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `task_id` | `UUID` | 下载任务的唯一标识ID |

* **请求参数 (Query)**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `Integer` | 否 | `1` | 页码,从1开始 |
| `size` | `Integer` | 否 | `10` | 每页记录数,范围1-100 |
| `sort` | `String` | 否 | `created_at:desc` | 排序规则,格式: `field:direction` |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取已下载视频列表成功",
  "data": {
    "total": 1,
    "page": 1,
    "size": 10,
    "pages": 1,
    "items": [
      {
        "id": "video-record-uuid",
        "video_id": "8723901837-f22d-41d4-a716-446655440001",
        "liveroom_id": "8723901837",
        "liveroom_title": "精彩直播间",
        "liveroom_url": "https://example.com/room/8723901837",
        "video_type": "hls",
        "video_url": "https://example.com/video.m3u8",
        "storage_path": "/media/video_8723901837_f22d/hls/",
        "file_size": 1073741824,
        "duration": 3600,
        "resolution": "1080p",
        "format": "hls",
        "status": "completed",
        "created_at": "2025-06-14T10:30:00Z",
        "updated_at": "2025-06-14T10:30:00Z"
      }
    ]
  },
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null,
  "timestamp": "2025-06-14T11:00:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     task_id_for_logging = str(task_id)
     page_for_logging = page
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.list_downloaded_videos(task_id, user_id_for_logging, skip=(page-1)*size, limit=size, sort)`:
       * 首先验证任务存在且属于当前用户
       * 在`downloaded_videos`表中查询`task_id`匹配的记录
       * 应用排序规则
       * 应用分页(offset和limit)
     - 调用 `service.count_downloaded_videos(task_id, user_id_for_logging)` 获取总记录数
     - 将查询结果转换为字典列表,处理UUID和datetime序列化
     - 构造`PageResponse`对象
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取已下载视频列表成功",
           data=page_data.model_dump()
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 页码: {page_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"查询视频列表数据库错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 任务ID: {task_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 3.3 查询已下载视频详情

* **接口**: `GET /api/v1/download/videos/{video_id}`
* **描述**: 根据`video_id`获取已下载视频的详细信息
* **认证**: 需要用户认证

* **请求参数 (Path)**:

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `video_id` | `UUID` | 视频的唯一标识ID |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取已下载视频详情成功",
  "data": {
    "id": "video-record-uuid",
    "video_id": "8723901837-f22d-41d4-a716-446655440001",
    "liveroom_id": "8723901837",
    "liveroom_title": "精彩直播间",
    "liveroom_url": "https://example.com/room/8723901837",
    "video_type": "hls",
    "video_url": "https://example.com/video.m3u8",
    "storage_path": "/media/video_8723901837_f22d/hls/",
    "file_size": 1073741824,
    "duration": 3600,
    "resolution": "1080p",
    "format": "hls",
    "status": "completed",
    "created_at": "2025-06-14T10:30:00Z",
    "updated_at": "2025-06-14T10:30:00Z"
  },
  "timestamp": "2025-06-14T11:10:00Z"
}
```

* **失败响应示例 (`404 Not Found`)**:

```json
{
  "code": 404,
  "message": "视频不存在",
  "data": null,
  "timestamp": "2025-06-14T11:10:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     video_id_for_logging = str(video_id)
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.get_downloaded_video(video_id, user_id_for_logging)`:
       * 在 `downloaded_videos` 表中,使用 `video_id` 进行查询
       * 如果不存在,抛出`VideoNotFoundError`
       * 通过`task_id`验证关联的任务是否属于当前用户
     - 将找到的记录转换为字典,处理UUID和datetime序列化
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取已下载视频详情成功",
           data=video_dict
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except VideoNotFoundError**:
       * 记录日志: `logger.warning(f"视频不存在 - 用户ID: {user_id_for_logging}, 视频ID: {video_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="视频不存在")`
     - **except TaskNotFoundError**:
       * 记录日志: `logger.warning(f"任务不存在或无权限 - 用户ID: {user_id_for_logging}, 视频ID: {video_id_for_logging}")`
       * 返回`status_code=404, content=create_error_response(code=404, message="任务不存在")`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"查询视频详情数据库错误 - 用户ID: {user_id_for_logging}, 视频ID: {video_id_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 视频ID: {video_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

### 3.4 查询所有已下载视频(全局分页)

* **接口**: `GET /api/v1/download/videos`
* **描述**: 分页查询当前用户所有任务的已下载视频,支持按资源类型筛选
* **认证**: 需要用户认证

* **请求参数 (Query)**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `page` | `Integer` | 否 | `1` | 页码,从1开始 |
| `size` | `Integer` | 否 | `10` | 每页记录数,范围1-100 |
| `resource_type` | `String(20)` | 否 | `null` | 按资源类型筛选: `hls`, `mp4` |
| `sort` | `String` | 否 | `created_at:desc` | 排序规则 |

* **成功响应 (`200 OK`)**:

```json
{
  "code": 200,
  "message": "获取全局视频列表成功",
  "data": {
    "total": 20,
    "page": 1,
    "size": 10,
    "pages": 2,
    "items": [
      {
        "id": "video-record-uuid-1",
        "video_id": "8723901837-f22d-41d4-a716-446655440001",
        "liveroom_id": "8723901837",
        "resource_type": "hls",
        "file_size": 1073741824,
        "duration": 3600,
        "resolution": "1080p",
        "format": "hls",
        "storage_path": "/media/video_8723901837_f22d/hls/",
        "status": "completed",
        "created_at": "2025-06-14T10:30:00Z",
        "updated_at": "2025-06-14T10:30:00Z"
      }
    ]
  },
  "timestamp": "2025-06-14T11:15:00Z"
}
```

* **失败响应示例 (`500 Internal Server Error`)**:

```json
{
  "code": 500,
  "message": "服务器内部错误",
  "data": null,
  "timestamp": "2025-06-14T11:15:00Z"
}
```

* **实现流程描述**:
  1. **【核心规范0.1】在 `try` 块之前提取用于日志的变量**:
     ```python
     user_id_for_logging = current_user["user_id"]
     page_for_logging = page
     resource_type_for_logging = resource_type if resource_type else "all"
     ```
  2. 将整个业务逻辑包裹在 `try...except` 块中。
  3. **try块**:
     - 实例化 `DownloadService(db)`
     - 调用 `service.list_videos(user_id_for_logging, skip=(page-1)*size, limit=size, resource_type, sort)`:
       * 构建基础查询: `db.query(DownloadedVideo).join(DownloadTask)`
       * 添加用户ID过滤: `filter(DownloadTask.user_id == user_id_for_logging)`
       * 如果提供`resource_type`,添加类型筛选: `filter(DownloadedVideo.video_type == resource_type)`
       * 获取筛选后的总数: `query.count()`
       * 应用排序和分页
       * 将结果转换为字典列表,字段包括: `id`, `video_id`, `liveroom_id`, `resource_type`, `file_size`, `duration`, `resolution`, `format`, `storage_path`, `status`, `created_at`, `updated_at`
     - 构造`PageResponse`对象
     - **【核心规范0.2.1】使用`create_response()`返回成功结果**:
       ```python
       return create_response(
           code=200,
           message="获取全局视频列表成功",
           data=page_data.model_dump()
       )
       ```
  4. **异常处理（必须使用之前提取的局部变量进行日志记录）**: 
     - **except ValueError**:
       * 记录日志: `logger.warning(f"参数错误 - 用户ID: {user_id_for_logging}, 页码: {page_for_logging}, 错误: {str(e)}")`
       * 返回`status_code=400, content=create_error_response(code=1001, message=str(e))`
     - **except SQLAlchemyError**:
       * 记录日志: `logger.error(f"查询全局视频列表数据库错误 - 用户ID: {user_id_for_logging}, 资源类型: {resource_type_for_logging}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1002, message="数据库查询失败")`
     - **except Exception**:
       * 记录日志: `logger.error(f"未知错误 - 用户ID: {user_id_for_logging}, 错误类型: {type(e).__name__}, 错误: {str(e)}", exc_info=True)`
       * 返回`status_code=500, content=create_error_response(code=1000, message="服务器内部错误")`

## 四、数据库字段说明

### 4.1 download_tasks 表字段

| 字段名 | 类型 | 约束 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | PRIMARY KEY | `uuid4()` | 任务唯一标识ID |
| `user_id` | `UUID` | NOT NULL | - | 用户ID |
| `video_id` | `UUID` | NOT NULL | - | 视频ID,格式:{liveroom_id}_{uuid4后缀} |
| `liveroom_id` | `String(20)` | NOT NULL | - | 直播间ID |
| `liveroom_title` | `String(255)` | NULL | `null` | 直播间标题 |
| `liveroom_url` | `String(255)` | NULL | `null` | 直播间URL |
| `resource_url` | `String(255)` | NOT NULL | - | 资源下载URL |
| `resource_type` | `String(20)` | NOT NULL | - | 资源类型: hls, mp4, image |
| `status` | `String(20)` | NOT NULL | `'pending'` | 任务状态: pending, processing, completed, partial_completed, failed, cancelled |
| `progress` | `Float` | NOT NULL | `0.0` | 下载进度(0-1) |
| `retry_count` | `Integer` | NOT NULL | `0` | 重试次数 |
| `last_error` | `Text` | NULL | `null` | 最后错误信息 |
| `created_at` | `DateTime` | NOT NULL | `utcnow()` | 创建时间(UTC) |
| `updated_at` | `DateTime` | NOT NULL | `utcnow()` | 更新时间(UTC),自动更新 |
| `completed_at` | `DateTime` | NULL | `null` | 完成时间(UTC) |

### 4.2 download_failures 表字段

| 字段名 | 类型 | 约束 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | PRIMARY KEY | `uuid4()` | 失败记录唯一标识ID |
| `task_id` | `UUID` | FOREIGN KEY, NOT NULL | - | 关联的下载任务ID |
| `resource_url` | `Text` | NOT NULL | - | 原始资源地址(URL) |
| `expected_path` | `Text` | NOT NULL | - | 希望保存的路径(用于重试时定位) |
| `standard_name` | `String` | NULL | `null` | 标准化文件名 |
| `resource_type` | `String(20)` | NOT NULL | `'ts'` | 资源类型: ts, m3u8, mp4, image |
| `failure_type` | `String(50)` | NOT NULL | - | 失败类型: network_error, timeout, invalid_content, storage_error, permission_error |
| `error_message` | `Text` | NOT NULL | - | 错误信息 |
| `retry_count` | `Integer` | NOT NULL | `0` | 当前重试次数,范围0-3 |
| `next_retry_time` | `DateTime` | NULL | `null` | 下次重试时间(UTC) |
| `status` | `String(20)` | NOT NULL | `'pending'` | 失败记录状态: pending, retrying, abandoned |
| `created_at` | `DateTime` | NOT NULL | `utcnow()` | 创建时间(UTC) |
| `updated_at` | `DateTime` | NOT NULL | `utcnow()` | 更新时间(UTC),自动更新 |

### 4.3 downloaded_videos 表字段

| 字段名 | 类型 | 约束 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | PRIMARY KEY | `uuid4()` | 视频记录唯一标识ID |
| `video_id` | `UUID` | NOT NULL | - | 视频ID |
| `liveroom_id` | `String(20)` | NOT NULL | - | 直播间ID |
| `liveroom_title` | `String(255)` | NULL | `null` | 直播间标题 |
| `liveroom_url` | `String(255)` | NULL | `null` | 直播间URL |
| `video_type` | `String(20)` | NOT NULL | - | 视频类型: hls, mp4 |
| `video_url` | `String(255)` | NOT NULL | - | 原始视频URL |
| `storage_path` | `String(255)` | NOT NULL | - | 存储路径,遵循存储目录结构规范 |
| `file_size` | `BigInteger` | NULL | `null` | 文件大小(字节) |
| `duration` | `Integer` | NULL | `null` | 视频时长(秒) |
| `resolution` | `String(20)` | NULL | `null` | 视频分辨率 |
| `format` | `String(20)` | NULL | `null` | 视频格式 |
| `cover_url` | `String(255)` | NULL | `null` | 封面图片URL |
| `cover_path` | `String(255)` | NULL | `null` | 封面图片存储路径 |
| `task_id` | `UUID` | FOREIGN KEY, NULL | `null` | 关联的下载任务ID |
| `status` | `String(20)` | NOT NULL | - | 状态: completed, partial_completed, failed |
| `download_start_time` | `DateTime` | NULL | `null` | 开始下载时间(UTC) |
| `download_end_time` | `DateTime` | NULL | `null` | 完成下载时间(UTC) |
| `created_at` | `DateTime` | NOT NULL | `utcnow()` | 创建时间(UTC) |
| `updated_at` | `DateTime` | NOT NULL | `utcnow()` | 更新时间(UTC),自动更新 |

## 五、状态枚举说明

### 5.1 TaskStatus (任务状态)

| 枚举值 | 描述 | 可转换状态 |
| :--- | :--- | :--- |
| `pending` | 等待下载 | → processing, cancelled |
| `processing` | 下载中 | → completed, partial_completed, failed, cancelled |
| `completed` | 完全成功 | - (终态) |
| `partial_completed` | 部分成功(少量分片失败) | → processing, completed, failed |
| `failed` | 失败 | → processing (重试) |
| `cancelled` | 已取消 | - (终态) |

### 5.2 FailureStatus (失败记录状态)

| 枚举值 | 描述 |
| :--- | :--- |
| `pending` | 等待重试 |
| `retrying` | 重试中 |
| `abandoned` | 已放弃(重试次数超限或手动放弃) |

### 5.3 FailureType (失败类型)

| 枚举值 | 描述 | 常见原因 |
| :--- | :--- | :--- |
| `network_error` | 网络错误 | 连接失败、网络中断 |
| `timeout` | 超时错误 | 请求超时(默认30秒) |
| `invalid_content` | 内容无效 | 文件损坏、格式错误 |
| `storage_error` | 存储错误 | 磁盘空间不足、权限不足 |
| `permission_error` | 权限错误 | 无访问权限、文件被锁定 |

## 六、重要业务规则

### 6.1 任务状态转换规则

1. **创建任务**: 状态初始化为`pending`
2. **启动任务**: `pending` → `processing`
3. **下载完成**:
   - 全部成功: `processing` → `completed`
   - 少量失败(失败率≤30%): `processing` → `partial_completed`
   - 大量失败(失败率>30%): `processing` → `failed`
4. **重试任务**:
   - M3U8级别失败: 全量重新下载
   - TS级别失败: 仅重试失败分片
   - 重试成功: `failed/partial_completed` → `completed`
5. **删除任务**: 仅允许删除非`completed`状态的任务

### 6.2 失败记录处理规则

1. **失败记录创建**: 下载失败时自动创建
2. **重试次数限制**: 最多重试3次
3. **自动放弃**: `retry_count >= 3`时,自动将`status`改为`abandoned`
4. **手动放弃**: 用户可主动放弃失败记录
5. **失败容忍度**: HLS下载中,ts分片失败率≤30%视为可接受

### 6.3 并发控制规则

1. **全局并发限制**: 最大100个下载任务同时执行
2. **单任务并发**: 最大20个分片同时下载
3. **重试策略**: 指数退避(1分钟、2分钟、4分钟)
4. **超时设置**: 单个请求超时30秒

### 6.4 权限验证规则

1. **所有接口**: 需要用户认证
2. **任务操作**: 仅允许操作自己的任务
3. **失败记录操作**: 仅允许操作自己任务下的失败记录
4. **视频查询**: 仅允许查询自己下载的视频

---

**文档版本**: v1.0  
**最后更新**: 2025-06-14  
**维护者**: AI Assistant

