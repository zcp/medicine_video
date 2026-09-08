# Endpoints 和 Service 层调用一致性规范指南

## 1. 方法命名规范
- 确保 endpoints 和 service 层的方法命名保持一致：
- 无须通过 AI 或人手做“名义猜测”
- 正确示例
```
endpoints: create_download_task -> service: create_download_task
endpoints: get_download_task -> service: get_download_task
endpoints: update_download_task -> service: update_download_task
endpoints: cancel_download_task -> service: cancel_download_task
endpoints: retry_download_task -> service: retry_download_task
```
- 错误示例
```
endpoints: create_tasks -> service:  未定义
```

## 2. 方法调用存在性检查

- 除命名一致外，必须确保 endpoints 中调用的 service 方法在 `download_service.py` 中显式定义。
- 建议使用静态检查工具或脚本比对：

- 提取 endpoints 中所有 service 方法调用
- 校验其在 service 文件中是否有对应方法定义
- 
## 3. 参数类型匹配

- 确保 endpoints 和 service 层的参数类型正确匹配：
- 正确示例
task_id: endpoints 接收 str -> service 接收 uuid.UUID
status: endpoints 接收 str -> service 接收 TaskStatus
segment_ids: endpoints 接收 List[str] -> service 接收 List[uuid.UUID]

## 4. 同步/异步一致性

确保 endpoints 和 service 层的同步/异步特性一致：

### 同步方法示例---service 层

```python
def create_download_task(self, task_data: DownloadTaskCreate) -> DownloadTaskData:
    pass
```

### 同步方法示例---endpoints 层
```python
@router.post("/tasks", response_model=DownloadTaskResponse)
def create_download_task(task_data: DownloadTaskCreate, db: Session = Depends(get_db)):
    pass

# 异步方法示例
# service 层
async def process_download_task(self, task_id: uuid.UUID):
    pass

# endpoints 层
@router.post("/tasks/{task_id}/process")
async def process_download_task(task_id: str, db: Session = Depends(get_db)):
    pass
```

## 5.错误处理一致性
确保 endpoints 和 service 层的错误处理方式一致：

### service 层

```python
def create_download_task(self, task_data: DownloadTaskCreate) -> DownloadTaskData:
    try:
        # 业务逻辑
        pass
    except ValueError as e:
        raise ValueError(f"Invalid task data: {str(e)}")
    except SQLAlchemyError as e:
        raise DownloadServiceError(f"Database error: {str(e)}")
```

### endpoints 层
```python
@router.post("/tasks", response_model=DownloadTaskResponse)
def create_download_task(task_data: DownloadTaskCreate, db: Session = Depends(get_db)):
    try:
        service = DownloadService(db)
        task_data = service.create_download_task(task_data)
        return DownloadTaskResponse(
            code=200,
            message="创建下载任务成功",
            data=task_data,
            timestamp=datetime.now()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": str(e),
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
    except DownloadServiceError as e:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": str(e),
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
```

## 6. 返回值类型匹配

确保 endpoints 和 service 层的返回值类型正确匹配：

### service 层返回值
```python
DownloadTaskData
List[DownloadTaskData]
Dict[str, Any]
```

### endpoints 层返回值
```python
DownloadTaskResponse
PaginatedResponse
BaseResponse
```

## 7. 完整示例
以下是一个完整的重试任务示例：
### service 层
```python
def retry_download_task(
    self,
    task_id: uuid.UUID,
    segment_ids: Optional[List[uuid.UUID]] = None,
    resource_type: Optional[ResourceType] = None
) -> DownloadTaskData:
    try:
        # 业务逻辑
        pass
    except ValueError as e:
        raise ValueError(f"Invalid task data: {str(e)}")
    except SQLAlchemyError as e:
        raise DownloadServiceError(f"Database error: {str(e)}")
```

### endpoints 层
```python
@router.post("/tasks/{task_id}/retry", response_model=DownloadTaskResponse)
def retry_download_task(
    task_id: str,
    segment_ids: Optional[List[str]] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        service = DownloadService(db)
        task_data = service.retry_download_task(
            uuid.UUID(task_id),
            [uuid.UUID(sid) for sid in segment_ids] if segment_ids else None,
            ResourceType(resource_type) if resource_type else None
        )
        return DownloadTaskResponse(
            code=200,
            message="重试下载任务成功",
            data=task_data,
            timestamp=datetime.now()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": str(e),
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
    except DownloadServiceError as e:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": str(e),
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
```

## 8. 调试检查清单
- 当遇到调用问题时，请检查以下项：
- 方法名是否完全一致
- 参数类型是否正确转换
- 是否使用了正确的错误处理
- 返回值是否正确包装
- 日志记录是否完整
- 响应格式是否统一
- 
## 9. 附录：排查建议与最佳实践

### 常见问题排查

- 方法名不匹配：检查拼写、大小写、名称对齐
- 参数类型错误：检查类型转换、枚举值、UUID 使用
- 同步/异步问题：检查 async/await、方法定义一致性
- 错误处理遗漏：检查异常捕获、状态码一致性
- 返回值不一致：检查返回类型与响应模型匹配

### 代码生成与维护最佳实践

- 保持命名一致性
- 使用类型注解和响应模型
- 统一错误处理格式
- 添加日志记录和注释
- 编写单元测试，定期审查
- 遵循 RESTful 设计原则


