# 媒体下载服务 - CSV批量导入功能增量开发提示词

## 一、角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy、Pydantic和CSV文件处理，并擅长根据详细的设计文档和代码上下文，编写出职责清晰、分层明确、健壮可靠的微服务代码。你熟悉批量数据处理、错误隔离、事务管理等高级技术。

## 二、任务目标 (Task Objective)

你的任务是**扩展**现有的**媒体下载服务**，通过**在已有文件中追加内容**的方式，增加CSV批量导入下载任务的功能。**你必须在不修改任何已有代码的前提下完成此任务。**

具体要求：
1. **【追加内容】** 更新 `app/services/download_service.py` 文件，在 `DownloadService` 类中**追加**`batch_import_tasks_from_csv`方法
2. **【追加内容】** 更新 `app/api/v1/endpoints/download.py` 文件，在文件末尾**追加**批量导入API端点
3. **【追加内容】** 更新 `app/schemas/download.py` 文件，在文件末尾**追加**批量导入相关的Pydantic Schema

## 三、核心上下文信息 (Core Context Information)

### 3.1 项目结构

```
backend/media_download_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── download.py  # <-- 追加API端点
│   ├── schemas/
│   │   └── download.py  # <-- 追加Schema定义
│   ├── services/
│   │   └── download_service.py  # <-- 追加服务层方法
│   ├── models/
│   │   └── download.py  # <-- 已存在，无需修改
│   └── core/
│       ├── response.py  # <-- 已存在（create_response, create_error_response）
│       └── exceptions.py  # <-- 已存在（TaskNotFoundError, DatabaseError等）
```

### 3.2 已存在的核心依赖

本功能依赖以下已存在的模块和组件：

1. **数据库模型** (`app/models/download.py`):
   - `DownloadTask`: 下载任务模型
   - 字段包括: `id`, `user_id`, `video_id`, `liveroom_id`, `liveroom_title`, `liveroom_url`, `resource_url`, `resource_type`, `status`, `progress`, `retry_count`, `created_at`, `updated_at`, `completed_at`

2. **Schema定义** (`app/schemas/download.py`):
   - `DownloadTaskCreate`: 任务创建Schema（已存在）
   - `TaskStatus`: 任务状态枚举

3. **核心响应** (`app/core/response.py`):
   - `create_response(code, message, data)`: 统一成功响应
   - `create_error_response(code, message, data=None)`: 统一错误响应

4. **核心异常** (`app/core/exceptions.py`):
   - `TaskNotFoundError`: 任务不存在异常
   - `DatabaseError`: 数据库错误异常
   - `DownloadServiceError`: 服务错误基类

5. **服务层方法** (`app/services/download_service.py`):
   - `create_download_task(task_data, user_id)`: 创建单个任务（已存在）
   - `start_download_task(task_id, user_id)`: 启动任务（已存在）

### 3.3 数据库字段定义

**download_tasks表关键字段**:
- `user_id` (UUID): 用户ID，用于数据隔离和权限验证
- `resource_url` (String): 资源URL，用于去重检查
- `liveroom_id` (String): 直播间ID，长度10-20字符
- `resource_type` (String): 资源类型（hls/mp4/image）
- `status` (String): 任务状态（pending/processing/completed/failed/partial_completed）

## 四、功能需求详细说明

### 4.1 CSV文件格式规范

#### 4.1.1 文件基本要求
- **文件编码**: UTF-8
- **分隔符**: 逗号(`,`)
- **表头行**: 必须包含（第一行）
- **最大行数**: 10000行（不含表头）
- **最大文件大小**: 20MB
- **文件扩展名**: 必须是`.csv`

#### 4.1.2 CSV列定义

**必需列**:
| 列名 | 类型 | 验证规则 | 描述 |
|:---|:---|:---|:---|
| `liveroom_id` | String | 长度10-20字符 | 直播间ID |
| `resource_url` | String | 有效URL | 资源下载URL |
| `resource_type` | String | 枚举值: hls/mp4/image | 资源类型 |

**可选列**:
| 列名 | 类型 | 验证规则 | 描述 |
|:---|:---|:---|:---|
| `liveroom_title` | String | 最大255字符 | 直播间标题 |
| `liveroom_url` | String | 有效URL | 直播间URL |

#### 4.1.3 CSV示例

```csv
liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
8723901837,精彩直播间1,https://example.com/room/8723901837,https://example.com/video1.m3u8,hls
8723901838,精彩直播间2,https://example.com/room/8723901838,https://example.com/video2.mp4,mp4
8723901839,精彩直播间3,https://example.com/room/8723901839,https://example.com/cover.jpg,image
```

### 4.2 核心功能特性

#### 4.2.1 错误隔离机制（关键特性）

**【重要】单行失败不中断整体流程**：
- 每行数据的处理都在独立的try-except块中
- 捕获异常后记录到`failed_rows`，然后使用`continue`继续处理下一行
- 确保一行数据错误不影响其他行的导入

#### 4.2.2 去重检查（可选功能）

- 通过`skip_duplicates`参数控制
- **去重依据**: `user_id` + `resource_url` + `liveroom_id` + `liveroom_title`
  * **理由**: 同一视频链接可能被不同直播间使用，需要从任务维度（而非视频维度）进行去重
  * **实现**: 查询条件为 `(user_id == user_id) AND (resource_url == resource_url) AND (liveroom_id == liveroom_id) AND (liveroom_title == liveroom_title OR (liveroom_title IS NULL AND row_title IS NULL))`
- 如果重复且`skip_duplicates=true`：跳过该行，记录到`skipped_rows`
- 如果重复且`skip_duplicates=false`：作为失败行处理，记录到`failed_rows`

#### 4.2.3 自动启动（可选功能）

- 通过`auto_start`参数控制
- 如果`auto_start=true`：导入成功后自动调用`start_download_task()`
- 启动失败不影响导入结果，仅记录警告日志

#### 4.2.4 批量事务提交（性能优化）

- 每处理100行提交一次事务（`if success % 100 == 0: db.commit()`）
- 所有行处理完毕后执行最终提交（`db.commit()`）
- 发生严重异常时执行回滚（`db.rollback()`）

#### 4.2.5 详细结果统计

返回结果包含：
- `total`: 总行数（不含表头）
- `success`: 成功导入的任务数
- `failed`: 失败的行数
- `skipped`: 跳过的行数（去重）
- `created_task_ids`: 成功创建的任务ID列表（最多前100个）
- `failed_rows`: 失败行的详细信息（行号、数据、错误原因）
- `skipped_rows`: 跳过行的详细信息（行号、数据、跳过原因）
- `processing_time`: 处理耗时（秒）

## 五、API接口详细说明

### 5.1 批量导入下载任务（CSV）

* **接口**: `POST /api/v1/download/tasks/batch-import`
* **描述**: 通过上传CSV文件批量创建下载任务
* **认证**: 需要用户认证（JWT Token）
* **Content-Type**: `multipart/form-data`

#### 5.1.1 请求参数

**Form Data参数**:

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|:---|:---|:---|:---|:---|
| `file` | `File` | 是 | - | CSV文件，最大10MB |
| `skip_duplicates` | `Boolean` | 否 | `false` | 是否跳过重复的任务组合（resource_url + liveroom_id + liveroom_title） |
| `auto_start` | `Boolean` | 否 | `false` | 导入后是否自动启动任务 |

#### 5.1.2 成功响应

**全部成功 (`201 Created`)**:

```json
{
  "code": 201,
  "message": "批量导入任务成功",
  "data": {
    "total": 100,
    "success": 100,
    "failed": 0,
    "skipped": 0,
    "created_task_ids": [
      "550e8400-e29b-41d4-a716-446655440001",
      "550e8400-e29b-41d4-a716-446655440002"
    ],
    "failed_rows": [],
    "skipped_rows": [],
    "processing_time": 2.5
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

**部分成功 (`207 Multi-Status`)**:

```json
{
  "code": 207,
  "message": "批量导入部分成功",
  "data": {
    "total": 100,
    "success": 80,
    "failed": 15,
    "skipped": 5,
    "created_task_ids": ["..."],
    "failed_rows": [
      {
        "row": 15,
        "liveroom_id": "invalid",
        "resource_url": "https://example.com/video.m3u8",
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
    "processing_time": 5.2
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

#### 5.1.3 失败响应

**文件格式错误 (`400 Bad Request`)**:

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

**全部失败 (`400 Bad Request`)**:

```json
{
  "code": 400,
  "message": "批量导入失败，所有行都处理失败",
  "data": {
    "total": 10,
    "success": 0,
    "failed": 10,
    "failed_rows": [...]
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

**文件过大 (`413 Payload Too Large`)**:

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

## 六、具体代码生成指令

### 6.1 Schema定义 (`app/schemas/download.py` - 追加内容)

**指令**: 在 `app/schemas/download.py` 文件**末尾追加**以下Schema定义。

```python
# ==================== CSV批量导入相关Schema ====================

from typing import List, Optional
from pydantic import BaseModel, Field


class BatchImportResult(BaseModel):
    """批量导入结果Schema"""
    total: int = Field(..., description="总行数（不含表头）")
    success: int = Field(..., description="成功导入的任务数")
    failed: int = Field(..., description="失败的行数")
    skipped: int = Field(..., description="跳过的行数（去重）")
    created_task_ids: List[str] = Field(default_factory=list, description="成功创建的任务ID列表（最多前100个）")
    failed_rows: List[dict] = Field(default_factory=list, description="失败行的详细信息")
    skipped_rows: List[dict] = Field(default_factory=list, description="跳过行的详细信息")
    processing_time: float = Field(..., description="处理耗时（秒）")
```

### 6.2 服务层方法 (`app/services/download_service.py` - 追加内容)

**指令**: 在 `app/services/download_service.py` 文件中的 `DownloadService` 类**内部末尾追加**以下方法。

**架构要求**: 
- 所有数据库操作必须在此文件中完成
- 使用SQLAlchemy ORM语法
- 严格遵循服务层职责：不返回HTTP响应对象

**方法签名**:
```python
def batch_import_tasks_from_csv(
    self,
    file_content: bytes,
    user_id: uuid.UUID,
    skip_duplicates: bool = False,
    auto_start: bool = False
) -> Dict:
```

**完整实现流程**:

```python
def batch_import_tasks_from_csv(
    self,
    file_content: bytes,
    user_id: uuid.UUID,
    skip_duplicates: bool = False,
    auto_start: bool = False
) -> Dict:
    """
    从CSV文件批量导入下载任务
    
    Args:
        file_content: CSV文件的二进制内容
        user_id: 当前用户ID
        skip_duplicates: 是否跳过重复的任务组合（默认False，去重依据为resource_url + liveroom_id + liveroom_title）
        auto_start: 导入后是否自动启动任务（默认False）
    
    Returns:
        Dict: 导入结果统计，包含total, success, failed, skipped等字段
    
    Raises:
        ValueError: CSV格式错误、缺少必需列、超过最大行数等
        UnicodeDecodeError: 文件编码错误
        csv.Error: CSV解析错误
        SQLAlchemyError: 数据库操作失败
    """
    import csv
    import io
    import time
    from datetime import datetime
    
    # 初始化统计变量
    total = 0
    success = 0
    failed = 0
    skipped = 0
    created_task_ids = []
    failed_rows = []
    skipped_rows = []
    start_time = time.time()
    
    try:
        # 1. 解码文件内容（UTF-8编码）
        content = file_content.decode('utf-8')
        
        # 2. 使用csv.DictReader解析CSV
        csv_reader = csv.DictReader(io.StringIO(content))
        
        # 3. 验证表头必需列
        required_columns = {'liveroom_id', 'resource_url', 'resource_type'}
        if not required_columns.issubset(csv_reader.fieldnames or []):
            missing = required_columns - (set(csv_reader.fieldnames) if csv_reader.fieldnames else set())
            raise ValueError(
                f"CSV文件格式错误: 缺少必需列 {', '.join(missing)}"
            )
        
        # 4. 逐行处理（关键：单行错误不中断）
        for row_number, row in enumerate(csv_reader, start=2):  # 从第2行开始（第1行是表头）
            total += 1
            
            # 4.1 检查行数限制
            if total > 1000:
                raise ValueError("CSV文件超过最大行数限制（1000行）")
            
            try:
                # 4.2 提取并清理数据
                liveroom_id = row.get('liveroom_id', '').strip()
                resource_url = row.get('resource_url', '').strip()
                resource_type = row.get('resource_type', '').strip()
                liveroom_title = row.get('liveroom_title', '').strip() or None
                liveroom_url = row.get('liveroom_url', '').strip() or None
                
                # 4.3 验证必填字段
                if not liveroom_id or not resource_url or not resource_type:
                    failed += 1
                    failed_rows.append({
                        "row": row_number,
                        "liveroom_id": liveroom_id,
                        "resource_url": resource_url,
                        "error": "缺少必填字段"
                    })
                    continue
                
                # 4.4 验证字段长度
                if not (10 <= len(liveroom_id) <= 20):
                    failed += 1
                    failed_rows.append({
                        "row": row_number,
                        "liveroom_id": liveroom_id,
                        "resource_url": resource_url,
                        "error": "liveroom_id长度必须在10-20之间"
                    })
                    continue
                
                # 4.5 验证资源类型
                if resource_type not in ['hls', 'mp4', 'image']:
                    failed += 1
                    failed_rows.append({
                        "row": row_number,
                        "liveroom_id": liveroom_id,
                        "resource_url": resource_url,
                        "error": f"无效的resource_type: {resource_type}，必须是hls/mp4/image之一"
                    })
                    continue
                
                # 4.6 去重检查（如果启用）
                if skip_duplicates:
                    # 使用(resource_url + liveroom_id + liveroom_title)组合去重
                    query_filter = [
                        DownloadTask.user_id == user_id,
                        DownloadTask.resource_url == resource_url,
                        DownloadTask.liveroom_id == liveroom_id
                    ]
                    # 处理liveroom_title可能为空的情况
                    if liveroom_title:
                        query_filter.append(DownloadTask.liveroom_title == liveroom_title)
                    else:
                        query_filter.append(DownloadTask.liveroom_title.is_(None))
                    
                    existing_task = self.db.query(DownloadTask).filter(*query_filter).first()
                    
                    if existing_task:
                        skipped += 1
                        skipped_rows.append({
                            "row": row_number,
                            "liveroom_id": liveroom_id,
                            "liveroom_title": liveroom_title,
                            "resource_url": resource_url,
                            "reason": "任务组合已存在（相同的resource_url + liveroom_id + liveroom_title）"
                        })
                        continue
                
                # 4.7 构造任务数据
                task_data = DownloadTaskCreate(
                    liveroom_id=liveroom_id,
                    liveroom_title=liveroom_title,
                    liveroom_url=liveroom_url,
                    resource_url=resource_url,
                    resource_type=resource_type
                )
                
                # 4.8 创建任务
                task = self.create_download_task(task_data, user_id)
                
                # 4.9 记录成功
                success += 1
                if len(created_task_ids) < 100:  # 最多保存前100个ID
                    created_task_ids.append(str(task.id))
                
                # 4.10 批量提交（每100行）
                if success % 100 == 0:
                    self.db.commit()
                    logger.info(f"批量导入进度 - 用户ID: {user_id}, 已成功: {success}/{total}")
                
                # 4.11 自动启动（如果启用）
                if auto_start:
                    try:
                        self.start_download_task(task.id, user_id)
                        logger.info(f"自动启动任务成功 - 任务ID: {task.id}")
                    except Exception as e:
                        # 启动失败不影响导入，仅记录警告
                        logger.warning(
                            f"自动启动任务失败 - 任务ID: {task.id}, 错误: {str(e)}"
                        )
            
            except ValidationError as e:
                # Pydantic验证错误
                failed += 1
                failed_rows.append({
                    "row": row_number,
                    "liveroom_id": row.get('liveroom_id', ''),
                    "resource_url": row.get('resource_url', ''),
                    "error": f"数据验证失败: {str(e)}"
                })
                continue
            
            except Exception as e:
                # 其他单行处理错误
                failed += 1
                failed_rows.append({
                    "row": row_number,
                    "liveroom_id": row.get('liveroom_id', ''),
                    "resource_url": row.get('resource_url', ''),
                    "error": str(e)
                })
                logger.error(
                    f"处理CSV行失败 - 行号: {row_number}, 错误: {str(e)}",
                    exc_info=True
                )
                continue
        
        # 5. 最终提交事务
        self.db.commit()
        
        # 6. 计算处理时间
        processing_time = round(time.time() - start_time, 2)
        
        # 7. 记录完成日志
        logger.info(
            f"批量导入完成 - 用户ID: {user_id}, "
            f"总数: {total}, 成功: {success}, 失败: {failed}, 跳过: {skipped}, "
            f"耗时: {processing_time}秒"
        )
        
        # 8. 返回结果字典
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "created_task_ids": created_task_ids,
            "failed_rows": failed_rows,
            "skipped_rows": skipped_rows,
            "processing_time": processing_time
        }
    
    except UnicodeDecodeError:
        logger.error(f"文件编码错误 - 用户ID: {user_id}")
        raise ValueError("文件编码错误，请使用UTF-8编码")
    
    except csv.Error as e:
        logger.error(f"CSV格式错误 - 用户ID: {user_id}, 错误: {str(e)}")
        raise ValueError(f"CSV文件格式错误: {str(e)}")
    
    except SQLAlchemyError as e:
        logger.error(
            f"批量导入数据库错误 - 用户ID: {user_id}, 错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        raise DatabaseError(f"数据库操作失败: {str(e)}")
    
    except Exception as e:
        logger.error(
            f"批量导入未知错误 - 用户ID: {user_id}, "
            f"错误类型: {type(e).__name__}, 错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        raise
```

### 6.3 API端点层 (`app/api/v1/endpoints/download.py` - 追加内容)

**指令**: 在 `app/api/v1/endpoints/download.py` 文件**末尾追加**以下API端点。

**完整实现流程**:

```python
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse


@router.post("/tasks/batch-import", response_model=ResponseModel[BatchImportResult])
async def batch_import_tasks(
    file: UploadFile = File(..., description="CSV文件，最大10MB"),
    skip_duplicates: bool = Form(False, description="是否跳过重复的任务组合（resource_url + liveroom_id + liveroom_title）"),
    auto_start: bool = Form(False, description="导入后是否自动启动任务"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量导入下载任务（CSV文件）
    
    CSV文件格式要求：
    - 文件编码：UTF-8
    - 分隔符：逗号
    - 表头必需列：liveroom_id, resource_url, resource_type
    - 最大行数：1000行（不含表头）
    - 最大文件大小：10MB
    """
    # ==================== 【核心规范0.1】变量提取（安全异步异常处理） ====================
    user_id_for_logging = current_user["user_id"]
    file_name_for_logging = file.filename if file and file.filename else "unknown"
    skip_duplicates_for_logging = skip_duplicates
    auto_start_for_logging = auto_start
    
    try:
        # ==================== 文件验证 ====================
        # 1. 验证文件扩展名
        if not file.filename or not file.filename.lower().endswith('.csv'):
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=1001,
                    message="文件类型错误，必须是CSV文件"
                )
            )
        
        # 2. 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 3. 验证文件大小（10MB = 10485760 bytes）
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            return JSONResponse(
                status_code=413,
                content=create_error_response(
                    code=413,
                    message="文件大小超过限制，最大允许10MB",
                    data={
                        "file_size": file_size,
                        "max_size": max_size
                    }
                )
            )
        
        # 4. 验证文件不为空
        if file_size == 0:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=1001,
                    message="文件不能为空"
                )
            )
        
        # ==================== 业务处理 ====================
        # 5. 调用服务层方法
        service = DownloadService(db)
        result = service.batch_import_tasks_from_csv(
            file_content=file_content,
            user_id=user_id_for_logging,
            skip_duplicates=skip_duplicates,
            auto_start=auto_start
        )
        
        # 6. 记录日志
        logger.info(
            f"批量导入完成 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, "
            f"总数: {result['total']}, 成功: {result['success']}, "
            f"失败: {result['failed']}, 跳过: {result['skipped']}"
        )
        
        # ==================== 【核心规范0.2】统一响应处理 ====================
        # 7. 根据结果返回不同的响应
        
        # 7.1 全部失败（成功数为0）
        if result['success'] == 0:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=1001,
                    message="批量导入失败，所有行都处理失败",
                    data=result
                )
            )
        
        # 7.2 部分成功（有失败行）
        if result['failed'] > 0:
            return JSONResponse(
                status_code=207,
                content=create_response(
                    code=207,
                    message="批量导入部分成功",
                    data=result
                )
            )
        
        # 7.3 全部成功
        return create_response(
            code=201,
            message="批量导入任务成功",
            data=result
        )
    
    # ==================== 【核心规范0.3】异常处理（使用提取的变量记录日志） ====================
    except ValueError as e:
        # 文件验证错误、CSV格式错误
        logger.warning(
            f"文件验证错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, 错误: {str(e)}"
        )
        return JSONResponse(
            status_code=400,
            content=create_error_response(code=1001, message=str(e))
        )
    
    except UnicodeDecodeError as e:
        # 文件编码错误
        logger.warning(
            f"文件编码错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}"
        )
        return JSONResponse(
            status_code=400,
            content=create_error_response(
                code=1001,
                message="文件编码错误，请使用UTF-8编码"
            )
        )
    
    except csv.Error as e:
        # CSV解析错误
        logger.warning(
            f"CSV格式错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, 错误: {str(e)}"
        )
        return JSONResponse(
            status_code=400,
            content=create_error_response(
                code=1001,
                message="CSV文件格式错误"
            )
        )
    
    except SQLAlchemyError as e:
        # 数据库操作错误
        logger.error(
            f"批量导入数据库错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, 错误: {str(e)}",
            exc_info=True
        )
        # 注意：服务层已执行rollback
        return JSONResponse(
            status_code=500,
            content=create_error_response(code=1002, message="数据库操作失败")
        )
    
    except Exception as e:
        # 未知错误
        logger.error(
            f"批量导入未知错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, "
            f"错误类型: {type(e).__name__}, 错误: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content=create_error_response(code=1000, message="服务器内部错误")
        )
```

## 七、编码规范与约束

### 7.1 核心编码原则（必须遵守）

#### 7.1.1 安全异步异常处理
- **【规则】**: 在进入`try`块之前，提取所有需要在`except`块中使用的ORM对象属性
- **【原因】**: 避免在捕获`SQLAlchemyError`后访问失效的ORM对象
- **【实现】**: 使用局部变量保存，如`user_id_for_logging = current_user["user_id"]`

#### 7.1.2 统一响应处理
- **【成功响应】**: 必须使用`create_response(code, message, data)`
- **【错误响应】**: 必须使用`JSONResponse(status_code=xxx, content=create_error_response(code, message, data))`
- **【禁止】**: 服务层不得返回HTTP响应对象

#### 7.1.3 事务管理
- **【提交时机】**: 
  - 批量操作：每100行提交一次（`if success % 100 == 0: db.commit()`）
  - 最终提交：所有行处理完毕后（`db.commit()`）
- **【回滚时机】**: 捕获`SQLAlchemyError`或严重异常时（`db.rollback()`）

#### 7.1.4 错误隔离
- **【关键】**: 单行数据处理错误不影响其他行
- **【实现】**: 每行处理在独立try-except中，捕获后`continue`

#### 7.1.5 日志记录
- **【Info级别】**: 记录开始、进度、完成信息
- **【Warning级别】**: 记录业务验证失败、自动启动失败
- **【Error级别】**: 记录数据库错误、未知错误，必须包含`exc_info=True`

### 7.2 数据验证规范

#### 7.2.1 必填字段验证
```python
if not liveroom_id or not resource_url or not resource_type:
    # 记录到failed_rows，continue
```

#### 7.2.2 字段长度验证
```python
if not (10 <= len(liveroom_id) <= 20):
    # 记录到failed_rows，continue
```

#### 7.2.3 枚举值验证
```python
if resource_type not in ['hls', 'mp4', 'image']:
    # 记录到failed_rows，continue
```

#### 7.2.4 去重验证
```python
if skip_duplicates:
    existing_task = db.query(DownloadTask).filter(
        DownloadTask.user_id == user_id,
        DownloadTask.resource_url == resource_url
    ).first()
    if existing_task:
        # 记录到skipped_rows，continue
```

### 7.3 性能优化规范

#### 7.3.1 批量提交
- 每100行提交一次事务
- 避免每行都commit，减少数据库IO

#### 7.3.2 ID列表限制
- `created_task_ids`最多保存前100个
- 避免内存占用过大

#### 7.3.3 CSV行数限制
- 最多1000行（不含表头）
- 超过限制立即抛出异常

## 八、测试验证要点

### 8.1 正常场景测试
- [ ] 导入100行有效数据，全部成功
- [ ] 验证`created_task_ids`包含所有任务ID
- [ ] 验证返回`201 Created`状态码

### 8.2 异常场景测试
- [ ] CSV缺少必需列（resource_url），返回400错误
- [ ] CSV超过1000行，返回400错误
- [ ] 文件大小超过10MB，返回413错误
- [ ] 文件编码非UTF-8，返回400错误

### 8.3 业务场景测试
- [ ] `skip_duplicates=true`时，重复resource_url被跳过
- [ ] `skip_duplicates=false`时，重复resource_url作为失败处理
- [ ] 部分行数据无效，返回207状态码
- [ ] 全部行数据无效，返回400状态码

### 8.4 错误隔离测试
- [ ] 第5行数据错误，不影响第6行导入
- [ ] 失败行详细信息记录在`failed_rows`中
- [ ] 最终`success + failed + skipped == total`

### 8.5 自动启动测试
- [ ] `auto_start=true`时，成功任务自动启动
- [ ] 启动失败不影响导入结果

## 九、最终交付清单

### 9.1 文件修改清单
1. **`app/schemas/download.py`** (追加)
   - 新增`BatchImportResult` Schema

2. **`app/services/download_service.py`** (追加)
   - 新增`batch_import_tasks_from_csv`方法

3. **`app/api/v1/endpoints/download.py`** (追加)
   - 新增`POST /tasks/batch-import`端点

### 9.2 依赖导入清单
在相应文件顶部确保导入以下模块：
- `import csv`
- `import io`
- `import time`
- `from fastapi import UploadFile, File, Form`
- `from pydantic import ValidationError`

### 9.3 验证清单
- [ ] 代码符合所有编码规范
- [ ] 使用统一响应格式（`create_response`/`create_error_response`）
- [ ] 所有异常处理使用提取的局部变量记录日志
- [ ] 单行错误不中断整体流程
- [ ] 批量提交事务（每100行）
- [ ] 服务层不返回HTTP响应对象
- [ ] 详细的错误信息记录

## 十、注意事项与最佳实践

### 10.1 关键注意事项

1. **【禁止修改已有代码】**: 所有代码都是**追加**到文件末尾，不修改任何现有功能
2. **【错误隔离机制】**: 这是本功能的核心特性，必须确保单行失败不影响其他行
3. **【事务管理】**: 批量提交和回滚机制至关重要，避免内存占用过大和数据不一致
4. **【安全异步异常处理】**: 在`except`块中只使用提前提取的局部变量，不访问ORM对象
5. **【详细错误记录】**: 每个失败行都需要记录行号、数据和错误原因，便于用户排查

### 10.2 最佳实践建议

1. **文件验证优先**: 在解析CSV之前先验证文件类型、大小、编码
2. **渐进式commit**: 批量操作使用渐进式提交，避免事务过大
3. **防御式编程**: 对所有外部输入进行严格验证和清理
4. **详细日志**: 关键步骤都记录日志，便于问题排查
5. **优雅降级**: 自动启动失败不影响导入，仅记录警告

### 10.3 性能考虑

1. **内存控制**: `created_task_ids`限制100个，避免大量ID占用内存
2. **数据库连接**: 使用批量提交减少数据库连接次数
3. **CSV解析**: 使用迭代器方式解析，不一次性加载所有行到内存

---

## 附录：完整代码示例概览

### A.1 服务层方法签名
```python
def batch_import_tasks_from_csv(
    self,
    file_content: bytes,
    user_id: uuid.UUID,
    skip_duplicates: bool = False,
    auto_start: bool = False
) -> Dict:
```

### A.2 API端点签名
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

### A.3 核心流程伪代码
```
1. 提取变量（user_id_for_logging, file_name_for_logging）
2. try:
   2.1 验证文件（扩展名、大小、非空）
   2.2 读取并解码文件内容（UTF-8）
   2.3 解析CSV（csv.DictReader）
   2.4 验证表头必需列
   2.5 逐行处理：
       for row in csv_reader:
           try:
               - 提取并清理数据
               - 验证必填字段
               - 验证字段长度和格式
               - 去重检查（如果启用）
               - 创建任务
               - 记录成功
               - 批量提交（每100行）
               - 自动启动（如果启用）
           except 单行异常:
               - 记录到failed_rows
               - continue
   2.6 最终提交
   2.7 返回结果字典
3. except 各种异常:
   - 使用提取的变量记录日志
   - 返回统一错误响应
```

---

**文档版本**: v1.0  
**创建日期**: 2025-01-XX  
**最后更新**: 2025-01-XX  
**文档状态**: 已完成，待实施
