# download_service.py 代码更新详细指令

**文档版本**: v1.0  
**创建时间**: 2025-11-04  
**更新目标**: 补充异常处理、日志、变量提取，提升代码健壮性

---

## 📋 更新原则（必须遵守）

### 核心原则
1. ✅ **最小化修改**: 只添加异常处理、日志、变量提取
2. ❌ **不改业务逻辑**: 保持所有业务流程完全不变
3. ❌ **不改方法签名**: 保持所有方法签名完全不变
4. ❌ **不改数据库操作**: 保持所有SQL查询和修改逻辑不变
5. ❌ **不改返回值**: 保持所有return语句的内容不变
6. ❌ **不删除现有代码**: 只能添加，不能删除或重构

### 修改范围
- ✅ 可以添加变量提取语句
- ✅ 可以添加try-except包裹
- ✅ 可以添加logger语句
- ✅ 可以添加rollback调用
- ✅ 可以修改except块中的日志，使用提取的变量

---

## 🎯 P0优先级更新（必须执行）

### 修改1: _process_download_m3u8_result

**文件**: `backend/media_download_service/app/services/download_service.py`  
**行号**: 636-787  
**修改类型**: 添加外层异常保护

#### 当前代码结构
```python
def _process_download_m3u8_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
    """文档字符串"""
    failure_ratio = 1
    # ... 大量业务逻辑 ...
    task.status = final_task_stauts
    task.completed_at = datetime.utcnow()
    logger.info(f"Task {task.id} final status updated to: {task.status.value}")
```

#### 修改后代码结构
```python
def _process_download_m3u8_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
    """文档字符串"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task.id)
    user_id_for_logging = str(user_id)
    resource_type_for_logging = task.resource_type.value if hasattr(task.resource_type, 'value') else str(task.resource_type)
    # ==================== 新增结束 ====================
    
    try:
        # ==================== 保持以下所有代码完全不变 ====================
        failure_ratio = 1
        print("xxxxxx")

        if result.get("success") == True:
            failure_ratio = 0
        else:
            failed_segments = result.get("failed_segments")
            if failed_segments > 0:
                print("xxxx, failed_segments, total_segments",failed_segments, result.get("total_segments"))
                failure_ratio = failed_segments / result.get("total_segments", 1)
            else:
                failure_ratio = 1  #failed_segments ==0意味着m3u8下载出错。

        final_task_stauts = TaskStatus.PENDING
        # 3. 更新主任务的最终状态
        if failure_ratio == 0:
            final_task_stauts = TaskStatus.COMPLETED
            task.progress = 1.0
        elif failure_ratio > self.hls_failure_tolerance:
            final_task_stauts = TaskStatus.FAILED
            task.progress = 0.0
            task.last_error = f"{result.get('failed_segments')} segments failed to download."
        else:
            final_task_stauts = TaskStatus.PARTIAL_COMPLETED
            task.progress = 1 - failure_ratio

        # ... 所有现有的if/else块和try-except块保持不变 ...
        # ... 包括创建DownloadedVideo的代码 ...
        # ... 包括创建DownloadFailure的代码 ...
        
        task.status = final_task_stauts
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} final status updated to: {task.status.value}")
        # ==================== 现有代码完全不变部分结束 ====================
        
    # ==================== 新增：异常处理 ====================
    except SQLAlchemyError as e:
        logger.error(
            f"处理HLS下载结果时数据库错误 - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}, "
            f"资源类型: {resource_type_for_logging}, "
            f"错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        # 尝试更新任务状态为失败（可能已经在失效的session中）
        try:
            self.db.refresh(task)
            task.status = TaskStatus.FAILED
            task.last_error = f"处理下载结果时数据库错误: {str(e)}"
            self.db.commit()
        except:
            pass  # 如果无法更新也不抛出异常
        raise DatabaseError(f"处理HLS下载结果时数据库错误: {str(e)}")
        
    except Exception as e:
        logger.error(
            f"处理HLS下载结果时发生未知错误 - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}, "
            f"资源类型: {resource_type_for_logging}, "
            f"错误类型: {type(e).__name__}, "
            f"错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        # 尝试更新任务状态为失败
        try:
            self.db.refresh(task)
            task.status = TaskStatus.FAILED
            task.last_error = f"处理失败: {str(e)}"
            self.db.commit()
        except:
            pass
        raise
    # ==================== 新增结束 ====================
```

#### 关键注意事项
1. ⚠️ **不要删除方法内部现有的任何try-except块**（行685-710，714-739等）
2. ⚠️ **不要修改任何print语句**（虽然它们不规范，但保留原样）
3. ⚠️ **保持所有注释不变**
4. ⚠️ **只在方法的最外层添加try-except包裹**

---

### 修改2: _process_download_mp4_result

**文件**: `backend/media_download_service/app/services/download_service.py`  
**行号**: 789-881  
**修改类型**: 添加外层异常保护

#### 修改后代码结构
```python
def _process_download_mp4_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
    """Process the download result for MP4 tasks"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task.id)
    user_id_for_logging = str(user_id)
    resource_type_for_logging = task.resource_type.value if hasattr(task.resource_type, 'value') else str(task.resource_type)
    # ==================== 新增结束 ====================
    
    try:
        # ==================== 保持以下所有代码完全不变 ====================
        if result.get("success"):
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            # ... 所有现有代码保持不变 ...
        else:
            task.status = TaskStatus.FAILED
            task.progress = 0.0
            # ... 所有现有代码保持不变 ...
        
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} MP4 download completed with status: {task.status.value}")
        # ==================== 现有代码完全不变部分结束 ====================
        
    # ==================== 新增：异常处理 ====================
    except SQLAlchemyError as e:
        logger.error(
            f"处理MP4下载结果时数据库错误 - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}, "
            f"资源类型: {resource_type_for_logging}, "
            f"错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        try:
            self.db.refresh(task)
            task.status = TaskStatus.FAILED
            task.last_error = f"处理下载结果时数据库错误: {str(e)}"
            self.db.commit()
        except:
            pass
        raise DatabaseError(f"处理MP4下载结果时数据库错误: {str(e)}")
        
    except Exception as e:
        logger.error(
            f"处理MP4下载结果时发生未知错误 - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}, "
            f"资源类型: {resource_type_for_logging}, "
            f"错误类型: {type(e).__name__}, "
            f"错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        try:
            self.db.refresh(task)
            task.status = TaskStatus.FAILED
            task.last_error = f"处理失败: {str(e)}"
            self.db.commit()
        except:
            pass
        raise
    # ==================== 新增结束 ====================
```

---

### 修改3: _process_download_image_result

**文件**: `backend/media_download_service/app/services/download_service.py`  
**行号**: 883-974  
**修改类型**: 添加外层异常保护

#### 修改后代码结构
```python
def _process_download_image_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
    """Process the download result for image tasks"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task.id)
    user_id_for_logging = str(user_id)
    resource_type_for_logging = task.resource_type.value if hasattr(task.resource_type, 'value') else str(task.resource_type)
    # ==================== 新增结束 ====================
    
    try:
        # ==================== 保持以下所有代码完全不变 ====================
        if result.get("success"):
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            # ... 所有现有代码保持不变 ...
        else:
            task.status = TaskStatus.FAILED
            task.progress = 0.0
            # ... 所有现有代码保持不变 ...
        
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} image download completed with status: {task.status.value}")
        # ==================== 现有代码完全不变部分结束 ====================
        
    # ==================== 新增：异常处理 ====================
    except SQLAlchemyError as e:
        logger.error(
            f"处理图片下载结果时数据库错误 - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}, "
            f"资源类型: {resource_type_for_logging}, "
            f"错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        try:
            self.db.refresh(task)
            task.status = TaskStatus.FAILED
            task.last_error = f"处理下载结果时数据库错误: {str(e)}"
            self.db.commit()
        except:
            pass
        raise DatabaseError(f"处理图片下载结果时数据库错误: {str(e)}")
        
    except Exception as e:
        logger.error(
            f"处理图片下载结果时发生未知错误 - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}, "
            f"资源类型: {resource_type_for_logging}, "
            f"错误类型: {type(e).__name__}, "
            f"错误: {str(e)}",
            exc_info=True
        )
        self.db.rollback()
        try:
            self.db.refresh(task)
            task.status = TaskStatus.FAILED
            task.last_error = f"处理失败: {str(e)}"
            self.db.commit()
        except:
            pass
        raise
    # ==================== 新增结束 ====================
```

---

## 🎯 P1优先级更新（强烈建议）

### 修改模式：添加变量提取

以下12个方法需要添加变量提取，修改模式相同：

#### 通用修改步骤
1. 在方法开始处（文档字符串后）添加变量提取
2. 在所有except块中，将`current_user.id`等替换为提取的局部变量

---

### 修改4: create_download_task

**行号**: 93-121

**添加内容**（在第95行后添加）:
```python
def create_download_task(self, task_data: DownloadTaskCreate, user_id: uuid.UUID) -> DownloadTask:
    """创建下载任务"""
    # ==================== 新增：变量提取 ====================
    user_id_for_logging = str(user_id)
    liveroom_id_for_logging = str(task_data.liveroom_id) if task_data.liveroom_id else "N/A"
    resource_url_for_logging = task_data.resource_url
    # ==================== 新增结束 ====================
    
    try:
        logger.info(f"Creating download task: {task_data.model_dump()}")
        # ... 保持所有现有代码不变 ...
```

**修改except块**（行111-113）:
```python
# 原代码
except IntegrityError as e:
    logger.error(f"Integrity error creating task for user {user_id}: {str(e)}")
    self.db.rollback()
    raise DownloadServiceError(f"Database integrity error: {str(e)}")

# 修改为
except IntegrityError as e:
    logger.error(f"Integrity error creating task for user {user_id_for_logging}: {str(e)}")  # ✏️ 修改此行
    self.db.rollback()
    raise DownloadServiceError(f"Database integrity error: {str(e)}")
```

**修改except块**（行115-117）:
```python
# 原代码
except SQLAlchemyError as e:
    logger.error(f"Database error creating task for user {user_id}: {str(e)}")
    self.db.rollback()
    raise DatabaseError(f"Database error: {str(e)}")

# 修改为
except SQLAlchemyError as e:
    logger.error(f"Database error creating task for user {user_id_for_logging}: {str(e)}")  # ✏️ 修改此行
    self.db.rollback()
    raise DatabaseError(f"Database error: {str(e)}")
```

---

### 修改5: get_download_task

**行号**: 123-138

**添加内容**（在第125行后添加）:
```python
def get_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadTask]:
    """获取下载任务详情"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task_id)
    user_id_for_logging = str(user_id)
    # ==================== 新增结束 ====================
    
    try:
        logger.info(f"Getting download task {task_id} for user {user_id}")
        # ... 保持所有现有代码不变 ...
```

**修改except块**（行136）:
```python
# 原代码
except SQLAlchemyError as e:
    logger.error(f"Database error while getting task: {str(e)}")
    raise DatabaseError(f"Database error: {str(e)}")

# 修改为（虽然此except块已经是安全的，但为了一致性可以添加更详细的日志）
except SQLAlchemyError as e:
    logger.error(
        f"Database error while getting task - "
        f"任务ID: {task_id_for_logging}, "
        f"用户ID: {user_id_for_logging}, "
        f"错误: {str(e)}"
    )
    raise DatabaseError(f"Database error: {str(e)}")
```

---

### 修改6: update_download_task

**行号**: 188-206

**添加内容**（在第190行后添加）:
```python
def update_download_task(self, task_id: uuid.UUID, task_data: DownloadTaskUpdate, user_id: uuid.UUID) -> Optional[DownloadTask]:
    """更新下载任务"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task_id)
    user_id_for_logging = str(user_id)
    # ==================== 新增结束 ====================
    
    try:
        logger.info(f"Updating download task {task_id} for user {user_id}")
        # ... 保持所有现有代码不变 ...
```

**修改except块**（行204）:
```python
# 原代码
except SQLAlchemyError as e:
    logger.error(f"Database error while updating task: {str(e)}")
    self.db.rollback()
    raise DatabaseError(f"Database error: {str(e)}")

# 修改为
except SQLAlchemyError as e:
    logger.error(
        f"Database error while updating task - "
        f"任务ID: {task_id_for_logging}, "
        f"用户ID: {user_id_for_logging}, "
        f"错误: {str(e)}"
    )
    self.db.rollback()
    raise DatabaseError(f"Database error: {str(e)}")
```

---

### 修改7-15: 其他高风险方法

按照相同的模式修改以下方法：

| # | 方法名 | 行号 | 需要提取的变量 |
|:---|:---|:---:|:---|
| 7 | `delete_download_task` | 208 | `task_id_for_logging`, `user_id_for_logging` |
| 8 | `create_download_failure` | 225 | `task_id_for_logging`, `user_id_for_logging` |
| 9 | `get_download_failure` | 294 | `failure_id_for_logging`, `user_id_for_logging` |
| 10 | `retry_download_failure` | 311 | `failure_id_for_logging`, `user_id_for_logging` |
| 11 | `abandon_download_failure` | 331 | `failure_id_for_logging`, `user_id_for_logging` |
| 12 | `create_downloaded_video` | 389 | `task_id_for_logging`, `user_id_for_logging` |
| 13 | `get_downloaded_video` | 1665 | `video_id_for_logging`, `user_id_for_logging` |
| 14 | `get_failure_details` | 1744 | `failure_id_for_logging`, `user_id_for_logging` |
| 15 | `retry_download_task` | 1484 | `task_id_for_logging`, `user_id_for_logging` |

**修改步骤**: 对每个方法执行以下操作：
1. 在方法开始处添加变量提取（在try之前）
2. 在所有except块的logger语句中，将ID参数替换为提取的局部变量

---

## 🎯 P2优先级更新（可选）

### 修改16: count_download_tasks

**行号**: 175-186

**添加内容**:
```python
def count_download_tasks(self, user_id: uuid.UUID, status: Optional[TaskStatus] = None) -> int:
    """获取下载任务总数"""
    # ==================== 新增：变量提取 ====================
    user_id_for_logging = str(user_id)
    status_for_logging = status.value if status else "all"
    # ==================== 新增结束 ====================
    
    try:
        # ==================== 新增：日志 ====================
        logger.info(f"Counting download tasks for user {user_id_for_logging}, status={status_for_logging}")
        # ==================== 新增结束 ====================
        
        query = self.db.query(func.count(DownloadTask.id))
        # ... 保持所有现有代码不变 ...
```

**修改except块**（行184）:
```python
# 原代码
except SQLAlchemyError as e:
    logger.error(f"Database error while counting tasks: {str(e)}")
    raise DatabaseError(f"Database error: {str(e)}")

# 修改为
except SQLAlchemyError as e:
    logger.error(
        f"Database error while counting tasks - "
        f"用户ID: {user_id_for_logging}, "
        f"状态过滤: {status_for_logging}, "
        f"错误: {str(e)}"
    )
    raise DatabaseError(f"Database error: {str(e)}")
```

---

### 修改17: count_download_failures

**行号**: 280-292

**添加内容**:
```python
def count_download_failures(self, task_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """获取下载失败记录总数"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task_id)
    user_id_for_logging = str(user_id)
    # ==================== 新增结束 ====================
    
    try:
        # ==================== 新增：日志 ====================
        logger.info(
            f"Counting download failures - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}"
        )
        # ==================== 新增结束 ====================
        
        query = self.db.query(func.count(DownloadFailure.id))
        # ... 保持所有现有代码不变 ...
```

**修改except块**（行290）:
```python
# 原代码
except SQLAlchemyError as e:
    logger.error(f"Database error while counting failures: {str(e)}")
    raise DatabaseError(f"Database error: {str(e)}")

# 修改为
except SQLAlchemyError as e:
    logger.error(
        f"Database error while counting failures - "
        f"任务ID: {task_id_for_logging}, "
        f"用户ID: {user_id_for_logging}, "
        f"错误: {str(e)}"
    )
    raise DatabaseError(f"Database error: {str(e)}")
```

---

### 修改18: count_downloaded_videos

**行号**: 449-470

**添加内容**:
```python
def count_downloaded_videos(self, task_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """获取已下载视频总数"""
    # ==================== 新增：变量提取 ====================
    task_id_for_logging = str(task_id)
    user_id_for_logging = str(user_id)
    # ==================== 新增结束 ====================
    
    try:
        # ==================== 新增：日志 ====================
        logger.info(
            f"Counting downloaded videos - "
            f"任务ID: {task_id_for_logging}, "
            f"用户ID: {user_id_for_logging}"
        )
        # ==================== 新增结束 ====================
        
        query = self.db.query(func.count(DownloadedVideo.id))
        # ... 保持所有现有代码不变 ...
```

**修改except块**（行465）:
```python
# 原代码（如果有的话，需要检查）
except SQLAlchemyError as e:
    logger.error(f"Database error while counting videos: {str(e)}")
    raise DatabaseError(f"Database error: {str(e)}")

# 修改为
except SQLAlchemyError as e:
    logger.error(
        f"Database error while counting videos - "
        f"任务ID: {task_id_for_logging}, "
        f"用户ID: {user_id_for_logging}, "
        f"错误: {str(e)}"
    )
    raise DatabaseError(f"Database error: {str(e)}")
```

---

## 📊 更新验证清单（步骤4&5）

### 验证步骤1：逐方法代码检查

对每个修改的方法，检查以下项目：

#### P0方法验证（3个）
- [ ] `_process_download_m3u8_result`
  - [ ] ✅ 变量提取在方法开始处（try之前）
  - [ ] ✅ 提取了`task_id_for_logging`, `user_id_for_logging`, `resource_type_for_logging`
  - [ ] ✅ 整个方法体被try包裹
  - [ ] ✅ 有SQLAlchemyError except块
  - [ ] ✅ 有通用Exception except块
  - [ ] ✅ 每个except块都调用了`self.db.rollback()`
  - [ ] ✅ 每个except块的日志使用了提取的局部变量
  - [ ] ✅ 没有修改任何业务逻辑
  - [ ] ✅ 没有删除内部现有的try-except块
  - [ ] ✅ 没有修改方法签名

- [ ] `_process_download_mp4_result`
  - [ ] （同上检查项）

- [ ] `_process_download_image_result`
  - [ ] （同上检查项）

#### P1方法验证（12个）
- [ ] `create_download_task`
  - [ ] ✅ 变量提取在方法开始处（try之前）
  - [ ] ✅ 提取了`user_id_for_logging`, `liveroom_id_for_logging`
  - [ ] ✅ 所有except块的日志使用了提取的局部变量
  - [ ] ✅ 没有修改业务逻辑
  - [ ] ✅ 没有修改方法签名
  - [ ] ✅ 没有修改try-except结构（只修改了日志内容）

- [ ] `get_download_task`
  - [ ] （同上检查项）

- [ ] `update_download_task`
  - [ ] （同上检查项）

- [ ] `delete_download_task`
  - [ ] （同上检查项）

- [ ] `create_download_failure`
  - [ ] （同上检查项）

- [ ] `get_download_failure`
  - [ ] （同上检查项）

- [ ] `retry_download_failure`
  - [ ] （同上检查项）

- [ ] `abandon_download_failure`
  - [ ] （同上检查项）

- [ ] `create_downloaded_video`
  - [ ] （同上检查项）

- [ ] `get_downloaded_video`
  - [ ] （同上检查项）

- [ ] `get_failure_details`
  - [ ] （同上检查项）

- [ ] `retry_download_task`
  - [ ] （同上检查项）

#### P2方法验证（3个）
- [ ] `count_download_tasks`
  - [ ] ✅ 添加了变量提取
  - [ ] ✅ 添加了开始日志（Info级别）
  - [ ] ✅ 修改了except块的日志
  - [ ] ✅ 没有修改业务逻辑

- [ ] `count_download_failures`
  - [ ] （同上检查项）

- [ ] `count_downloaded_videos`
  - [ ] （同上检查项）

---

### 验证步骤2：文档一致性检查

将更新后的代码与文档对比：

#### 与服务层详细文档对比
**文档**: `媒体下载服务功能代码生成指令v4-已修正---服务层方法详细说明-完整版.md`

对每个方法检查：
- [ ] ✅ 变量提取与文档"实现流程"的第1步一致
- [ ] ✅ 异常处理类型与文档"抛出异常"表一致
- [ ] ✅ 日志级别与文档"日志记录"一致
- [ ] ✅ Rollback位置与文档"数据库操作"一致
- [ ] ✅ 数据库字段名与文档一致（如`task.id`, `task.status`）
- [ ] ✅ 返回值类型与文档"返回值"表一致

#### 与主文档对比
**文档**: `媒体下载服务功能代码生成指令v4-已修正.md`

检查项：
- [ ] ✅ 符合"2.1.4 安全异步异常处理"规范
- [ ] ✅ 符合"2.1.5 主动变量提取"规范
- [ ] ✅ 符合"2.1.6 异常处理"规范
- [ ] ✅ 符合"2.1.10 数据库操作规范"（rollback要求）
- [ ] ✅ 所有方法签名与"三、服务层实现"一致

---

### 验证步骤3：代码运行测试

#### 单元测试
```bash
# 运行download_service相关测试
pytest backend/media_download_service/tests/test_download_service.py -v
```

**检查项**：
- [ ] ✅ 所有现有测试通过
- [ ] ✅ 没有新增测试失败
- [ ] ✅ 异常处理逻辑正确（通过测试用例验证）

#### 日志验证
```bash
# 启动服务，触发各个修改的方法
# 检查日志输出
```

**检查项**：
- [ ] ✅ 开始日志正确输出（包含提取的变量）
- [ ] ✅ 异常日志正确输出（使用局部变量，不访问失效对象）
- [ ] ✅ 没有出现`DetachedInstanceError`异常

---

### 验证步骤4：边界情况测试

| 场景 | 测试方法 | 预期结果 |
|:---|:---|:---|
| 数据库连接中断 | 在下载过程中断开数据库 | ✅ 正确rollback，日志正常输出 |
| 并发修改冲突 | 并发更新同一任务 | ✅ IntegrityError被正确捕获 |
| Session失效 | 在长时间操作后访问ORM对象 | ✅ 日志使用局部变量，不崩溃 |
| 下载失败 | HLS下载部分失败 | ✅ _process方法正确处理异常 |

---

## 📈 更新统计

### 代码变更统计
| 优先级 | 方法数 | 新增行数 | 修改行数 | 风险等级 |
|:---|:---:|:---:|:---:|:---:|
| P0 | 3 | ~45 | ~0 | ✅ 低 |
| P1 | 12 | ~24 | ~12 | ✅ 无 |
| P2 | 3 | ~15 | ~3 | ✅ 无 |
| **总计** | **18** | **~84** | **~15** | ✅ **安全** |

### 不修改的方法（16个）
1. `__init__` - 初始化方法
2. `_parse_sort` - 纯工具方法
3. `list_download_tasks` - 已符合规范
4. `list_download_failures` - 已符合规范
5. `list_downloaded_videos` - 已符合规范
6. `pause_download_task` - 已有完整异常处理
7. `resume_download_task` - 已有完整异常处理
8. `start_download_task` - 已有完整异常处理（子方法已修复）
9. `generate_standard_filename` - 纯工具方法
10. `modify_m3u8_for_local_playback` - 已有异常处理
11. `download_and_verify_ts_segment` - 已有异常处理
12. `download_mp4_image` - 已有异常处理
13. `download_m3u8` - 已有异常处理
14. `_retry_only_failed_segments` - 复杂逻辑，不宜改动
15. `list_failures` - 已符合规范
16. `list_videos` - 已符合规范

---

## ✅ 最终确认

### 更新前确认
- [ ] 已备份原始文件
- [ ] 已阅读全部修改指令
- [ ] 已理解"最小化修改"原则
- [ ] 已准备好测试环境

### 更新后确认
- [ ] 所有18个方法都已修改
- [ ] 所有修改都通过了验证清单
- [ ] 单元测试全部通过
- [ ] 代码与两个文档保持一致
- [ ] 没有引入任何新的业务逻辑

---

**预计工作量**: 2-3小时  
**预计风险**: 极低  
**预计收益**: 显著提升代码健壮性

**建议执行顺序**: P0 → P1 → 测试 → P2 → 最终测试

---

**文档结束**

