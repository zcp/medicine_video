# 媒体下载服务 - CSV批量导入API接口说明

## 1.8 批量导入下载任务（CSV）

* **接口**: `POST /api/v1/download/tasks/batch-import`
* **描述**: 通过上传CSV文件批量创建下载任务
* **认证**: 需要用户认证
* **Content-Type**: `multipart/form-data`

### 请求参数

#### Form Data

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `file` | `File` | 是 | CSV文件，最大10MB |
| `skip_duplicates` | `Boolean` | 否 | 是否跳过重复的resource_url（默认false，重复时报错） |
| `auto_start` | `Boolean` | 否 | 导入后是否自动启动任务（默认false） |

#### CSV文件格式要求

**文件编码**: UTF-8  
**分隔符**: 逗号(`,`)  
**表头行**: 必须包含（第一行）

**必需列**:
- `liveroom_id`: 直播间ID，长度10-20字符
- `resource_url`: 资源下载URL
- `resource_type`: 资源类型（hls/mp4/image）

**可选列**:
- `liveroom_title`: 直播间标题，最大255字符
- `liveroom_url`: 直播间URL

**CSV示例**:
```csv
liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
8723901837,精彩直播间1,https://example.com/room/8723901837,https://example.com/video1.m3u8,hls
8723901838,精彩直播间2,https://example.com/room/8723901838,https://example.com/video2.mp4,mp4
8723901839,精彩直播间3,https://example.com/room/8723901839,https://example.com/cover.jpg,image
```

### 成功响应 (`201 Created`)

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
      },
      {
        "row": 25,
        "liveroom_id": "8723901840",
        "resource_url": "invalid-url",
        "error": "resource_url格式错误，必须是有效的URL"
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

### 失败响应示例

#### 1. 文件格式错误 (`400 Bad Request`)

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

#### 2. 文件过大 (`413 Payload Too Large`)

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

#### 3. 文件类型错误 (`400 Bad Request`)

```json
{
  "code": 400,
  "message": "文件类型错误，只允许上传CSV文件",
  "data": {
    "uploaded_type": "application/vnd.ms-excel",
    "allowed_types": ["text/csv", "application/csv"]
  },
  "timestamp": "2025-06-14T10:00:00Z"
}
```

#### 4. CSV内容为空 (`400 Bad Request`)

```json
{
  "code": 400,
  "message": "CSV文件为空或只包含表头",
  "data": null,
  "timestamp": "2025-06-14T10:00:00Z"
}
```

#### 5. 批量导入部分失败 (`207 Multi-Status`)

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

### 实现流程描述

1. **接收文件和参数**:
   - 校验用户认证信息(`get_current_user`)
   - 从form-data中获取文件对象和参数(`skip_duplicates`, `auto_start`)

2. **文件验证**:
   - 检查文件是否存在
   - 检查文件大小（≤10MB）
   - 检查文件类型（text/csv 或 application/csv）
   - 检查文件扩展名（.csv）

3. **解析CSV文件**:
   - 使用UTF-8编码读取文件
   - 检查表头行是否包含必需列：`liveroom_id`, `resource_url`, `resource_type`
   - 如果缺少必需列，返回400错误，说明缺少哪些列
   - 检查CSV是否为空（除表头外无数据行）

4. **逐行处理**:
   ```python
   total = 0
   success = 0
   failed = 0
   skipped = 0
   created_task_ids = []
   failed_rows = []
   skipped_rows = []
   
   for row_num, row in enumerate(csv_reader, start=2):  # 从第2行开始（第1行是表头）
       total += 1
       
       try:
           # 4.1 数据验证
           liveroom_id = row.get('liveroom_id', '').strip()
           resource_url = row.get('resource_url', '').strip()
           resource_type = row.get('resource_type', '').strip()
           
           # 验证必填字段
           if not liveroom_id or not resource_url or not resource_type:
               failed += 1
               failed_rows.append({
                   "row": row_num,
                   "liveroom_id": liveroom_id,
                   "resource_url": resource_url,
                   "error": "缺少必填字段"
               })
               continue
           
           # 4.2 去重检查（如果开启）
           if skip_duplicates:
               existing = self.db.query(DownloadTask).filter(
                   DownloadTask.user_id == user_id,
                   DownloadTask.resource_url == resource_url
               ).first()
               
               if existing:
                   skipped += 1
                   skipped_rows.append({
                       "row": row_num,
                       "liveroom_id": liveroom_id,
                       "resource_url": resource_url,
                       "reason": "resource_url已存在"
                   })
                   continue
           
           # 4.3 构造任务数据
           task_data = DownloadTaskCreate(
               liveroom_id=liveroom_id,
               liveroom_title=row.get('liveroom_title', '').strip() or None,
               liveroom_url=row.get('liveroom_url', '').strip() or None,
               resource_url=resource_url,
               resource_type=resource_type
           )
           
           # 4.4 创建任务
           task = service.create_download_task(task_data, user_id)
           created_task_ids.append(str(task.id))
           success += 1
           
           # 4.5 自动启动（如果开启）
           if auto_start:
               try:
                   service.start_download_task(task.id, user_id)
               except Exception as e:
                   logger.warning(f"自动启动任务失败: {task.id}, 错误: {str(e)}")
           
       except ValidationError as e:
           # Schema验证错误
           failed += 1
           failed_rows.append({
               "row": row_num,
               "liveroom_id": liveroom_id,
               "resource_url": resource_url,
               "error": str(e.errors()[0]['msg'])
           })
           logger.error(f"第{row_num}行验证失败: {str(e)}")
           
       except Exception as e:
           # 其他错误
           failed += 1
           failed_rows.append({
               "row": row_num,
               "liveroom_id": liveroom_id,
               "resource_url": resource_url,
               "error": str(e)
           })
           logger.error(f"第{row_num}行处理失败: {str(e)}")
   ```

5. **构造响应**:
   - 如果`total == 0`（CSV为空），返回400错误
   - 如果`success == 0`（全部失败），返回400错误
   - 如果`success == total`（全部成功），返回201状态码
   - 如果`0 < success < total`（部分成功），返回207状态码（Multi-Status）
   - 响应数据包含：
     * `total`: 总行数
     * `success`: 成功创建的任务数
     * `failed`: 失败的行数
     * `skipped`: 跳过的行数（仅当`skip_duplicates=true`时）
     * `created_task_ids`: 成功创建的任务ID列表（最多返回前100个）
     * `failed_rows`: 失败的行详情（包含行号、数据和错误信息）
     * `skipped_rows`: 跳过的行详情
     * `processing_time`: 处理耗时（秒）

6. **日志记录**:
   - 记录批量导入开始: `logger.info(f"开始批量导入任务 - 用户ID: {user_id}, 文件名: {filename}")`
   - 记录批量导入结果: `logger.info(f"批量导入完成 - 总数: {total}, 成功: {success}, 失败: {failed}, 跳过: {skipped}, 耗时: {processing_time}s")`
   - 对每个失败行记录警告日志
   - 对异常情况记录错误日志

7. **异常处理**:
   - `UnicodeDecodeError`: 返回400错误，提示"文件编码错误，请使用UTF-8编码"
   - `csv.Error`: 返回400错误，提示"CSV文件格式错误"
   - `RequestEntityTooLarge`: 返回413错误，提示"文件大小超过限制"
   - `ValueError`: 返回400错误，提示具体的验证错误
   - `SQLAlchemyError`: 记录日志，回滚事务，返回500错误
   - 其他异常: 记录完整堆栈，返回500错误

### 性能优化建议

1. **批量提交**:
   - 每处理100行提交一次事务（`db.commit()`）
   - 避免单行提交导致的性能问题

2. **限制并发**:
   - 如果开启`auto_start`，限制同时启动的任务数（如最多10个）
   - 使用任务队列异步启动

3. **行数限制**:
   - 建议单次导入最多1000行
   - 超过限制返回400错误，提示"CSV行数超过限制（最多1000行）"

### Pydantic Schema定义

```python
class BatchImportRequest(BaseModel):
    """批量导入请求模型"""
    skip_duplicates: bool = Field(False, description="是否跳过重复的resource_url")
    auto_start: bool = Field(False, description="导入后是否自动启动任务")

class BatchImportFailedRow(BaseModel):
    """导入失败行信息"""
    row: int = Field(..., description="行号（从2开始，第1行是表头）")
    liveroom_id: str = Field(..., description="直播间ID")
    resource_url: str = Field(..., description="资源URL")
    error: str = Field(..., description="错误信息")

class BatchImportSkippedRow(BaseModel):
    """导入跳过行信息"""
    row: int = Field(..., description="行号")
    liveroom_id: str = Field(..., description="直播间ID")
    resource_url: str = Field(..., description="资源URL")
    reason: str = Field(..., description="跳过原因")

class BatchImportResponse(BaseModel):
    """批量导入响应模型"""
    total: int = Field(..., description="总行数")
    success: int = Field(..., description="成功创建的任务数")
    failed: int = Field(..., description="失败的行数")
    skipped: int = Field(..., description="跳过的行数")
    created_task_ids: List[str] = Field(..., description="成功创建的任务ID列表（最多100个）")
    failed_rows: List[BatchImportFailedRow] = Field(..., description="失败的行详情")
    skipped_rows: List[BatchImportSkippedRow] = Field(..., description="跳过的行详情")
    processing_time: float = Field(..., description="处理耗时（秒）")
```

### 服务层方法签名

```python
class DownloadService:
    def batch_import_tasks_from_csv(
        self,
        file_content: bytes,
        user_id: uuid.UUID,
        skip_duplicates: bool = False,
        auto_start: bool = False
    ) -> Dict:
        """
        从CSV文件批量导入下载任务
        
        :param file_content: CSV文件内容（字节）
        :param user_id: 用户ID
        :param skip_duplicates: 是否跳过重复的resource_url
        :param auto_start: 导入后是否自动启动任务
        :return: 导入结果字典
        """
        pass
```

### API端点实现示例

```python
@router.post("/tasks/batch-import", status_code=status.HTTP_201_CREATED)
async def batch_import_tasks(
    file: UploadFile = File(...),
    skip_duplicates: bool = Form(False),
    auto_start: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """批量导入下载任务"""
    
    start_time = time.time()
    
    try:
        # 1. 验证文件
        if not file.filename.endswith('.csv'):
            return create_error_response(
                "文件类型错误，只允许上传CSV文件",
                code=400
            )
        
        # 2. 检查文件大小
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            return create_error_response(
                "文件大小超过限制，最大允许10MB",
                code=413
            )
        
        # 3. 调用服务层方法
        service = DownloadService(db)
        result = service.batch_import_tasks_from_csv(
            file_content=file_content,
            user_id=uuid.UUID(current_user["user_id"]),
            skip_duplicates=skip_duplicates,
            auto_start=auto_start
        )
        
        # 4. 添加处理时间
        result["processing_time"] = round(time.time() - start_time, 2)
        
        # 5. 根据结果返回不同状态码
        if result["success"] == 0:
            return create_error_response(
                "批量导入失败，所有行都处理失败",
                code=400,
                data=result
            )
        elif result["failed"] > 0:
            return create_response(
                code=207,
                message="批量导入部分成功",
                data=result
            )
        else:
            return create_response(
                code=201,
                message="批量导入任务成功",
                data=result
            )
    
    except UnicodeDecodeError:
        logger.error("CSV文件编码错误")
        return create_error_response(
            "文件编码错误，请使用UTF-8编码",
            code=400
        )
    except Exception as e:
        logger.error(f"批量导入失败: {str(e)}", exc_info=True)
        return create_error_response(
            f"批量导入失败: {str(e)}",
            code=500
        )
```

### 安全注意事项

1. **文件验证**:
   - 检查文件扩展名和MIME类型
   - 限制文件大小（建议≤10MB）
   - 限制CSV行数（建议≤1000行）

2. **权限验证**:
   - 所有导入的任务都关联到当前用户
   - 不允许在CSV中指定`user_id`

3. **SQL注入防护**:
   - 使用参数化查询
   - 使用ORM操作数据库

4. **资源限制**:
   - 限制同时处理的CSV文件数
   - 使用异步处理避免阻塞

5. **错误隔离**:
   - 单行失败不影响其他行
   - 使用事务保证数据一致性

---

**文档版本**: v1.0  
**最后更新**: 2025-06-14  
**适用范围**: 媒体下载服务 v4+

