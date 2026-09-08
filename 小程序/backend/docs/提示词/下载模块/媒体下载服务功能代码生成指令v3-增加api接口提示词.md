
### **审查分析与修改方案**

1.  **任务目标**: 我将更新“任务目标”部分，清晰地指出本次任务是在现有基础上**追加**三个API接口到已有的 `service` 和 `endpoint` 文件中。
2.  **具体代码生成指令**: 我将为您**全新撰写**针对这三个新增API接口的、详尽的“具体代码生成指令”，并确保它们：
      * **深度细节**: 包含了您要求的所有细节，如数据库状态验证、业务错误码处理等。
      * **接口覆盖**: **完整覆盖** `GET /videos/{video_id}`、`GET /failures` 和 `GET /failures/{failure_id}` 这三个接口。
      * **架构一致性**: 明确指示将所有数据库查询逻辑都封装在 `DownloadService` 内部，`Endpoint` 层只做调用。
      * **规范应用**: 严格遵循您提供的所有规范，特别是 `success_response`/`error_response` 的调用和“主动变量提取”模式。
3.  **代码修改风险**: 所有指令都将以“**在文件末尾追加**”的形式给出，并明确声明**禁止修改**已有代码，确保之前批次的成果安全无虞。

-----

### **最终版：高效 AI 代码生成提示词 (媒体下载服务 - 扩展)**


#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy和Celery，并擅长根据详细的设计文档和代码上下文，编写出职责清晰、分层明确、健壮可靠的微服务代码。

#### **2. 任务目标 (Task Objective) - 【已更新】**

你的任务是**扩展**现有的**媒体下载服务**，通过**在已有文件中追加内容**的方式，增加三个用于查询已下载资源和失败记录的管理API。**你必须在不修改任何已有代码的前提下完成此任务。**

你的任务是：

1.  **【追加内容】** **更新** `app/services/download_service.py` 文件，在 `DownloadService` 类中**追加**新的业务逻辑方法。
2.  **【追加内容】** **更新** `app/api/v1/endpoints/download.py` 文件，在文件末尾**追加**新的API端点。
2.  **【追加内容】** **更新** `app/core/exceptions.py` 文件，在文件末尾**追加**新的异常类。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 项目结构 (扩展后)**
你将要在以下两个已有文件中追加代码：

```
project/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── download.py  # <-- 目标文件 2 (追加内容)
│   ├── core/
│   │   └── exceptions.py  # <-- 目标文件 1 (追加内容)
│   ├── services/
│   │   └── download_service.py  # <-- 目标文件 1 (追加内容)
...
```

app/api/v1/services/download.py代码
```
import concurrent
import json
import os
import threading
import time
import traceback
import uuid
import logging
from datetime import datetime
from fileinput import filename
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import m3u8
import requests
from pyasn1.type.univ import Boolean
from pytest_html.extras import video
from rfc3986.abnf_regexp import segments
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import desc, asc, func

from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import (
    DownloadTaskCreate,
    DownloadTaskUpdate,
    DownloadFailureCreate,
    DownloadedVideoCreate,
    TaskStatus,
    FailureStatusEnum
)
from app.core.config import settings
from app.core.exceptions import DownloadServiceError, TaskNotFoundError, InvalidTaskStatusError, DatabaseError

# 配置日志
logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self, db: Session):
        self.db = db
        self.download_dir = Path(settings.DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Add constants from your original script
        self.max_workers = 20
        self.max_retry_count = 3
        self.timeout = 30
        self.maximum_error_ts = 10
        self.hls_failure_tolerance = 0.3 # 5%
        self.chunk_size = 1024 * 1024  # 1MB
        self.thread_status = {}  # 用于监控线程状态
        self.active_threads = set()  # 记录活跃的线程
        self._stop_event = threading.Event()  # 用于控制线程停止的标志位
        # Define a list of common image extensions
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        # 设置请求头
        self.headers = {
            'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

    def _parse_sort(self, sort_str: str) -> List[tuple]:
        """解析排序字符串
        格式: field:direction,field:direction
        例如: created_at:desc,id:asc
        """
        if not sort_str:
            return [("created_at", desc)]
        
        result = []
        for part in sort_str.split(","):
            if ":" not in part:
                continue
            field, direction = part.split(":")
            if direction.lower() == "desc":
                result.append((field, desc))
            else:
                result.append((field, asc))
        return result or [("created_at", desc)]

    def create_download_task(self, task_data: DownloadTaskCreate) -> DownloadTask:
        """创建下载任务"""
        try:
            logger.info(f"Creating download task: {task_data.model_dump()}")
            task = DownloadTask(
                video_id=task_data.video_id,
                liveroom_id=task_data.liveroom_id,
                liveroom_title=task_data.liveroom_title,
                liveroom_url=str(task_data.liveroom_url),
                resource_url=str(task_data.resource_url),
                resource_type=task_data.resource_type,
                status=TaskStatus.PENDING
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Created download task with ID: {task.id}")
            return task
        except IntegrityError as e:
            logger.error(f"Integrity error while creating task: {str(e)}")
            self.db.rollback()
            raise DownloadServiceError(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating task: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def get_download_task(self, task_id: uuid.UUID) -> Optional[DownloadTask]:
        """获取下载任务"""
        try:
            logger.info(f"Getting download task: {task_id}")
            task = self.db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting task: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def list_download_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        sort: str = "created_at:desc"
    ) -> List[DownloadTask]:
        """获取下载任务列表"""
        try:
            logger.info(f"Listing download tasks: skip={skip}, limit={limit}, status={status}, sort={sort}")
            query = self.db.query(DownloadTask)
            if status:
                query = query.filter(DownloadTask.status == status)
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadTask, field)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing tasks: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def count_download_tasks(self, status: Optional[TaskStatus] = None) -> int:
        """获取下载任务总数"""
        try:
            query = self.db.query(func.count(DownloadTask.id))
            if status:
                query = query.filter(DownloadTask.status == status)
            return query.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting tasks: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def update_download_task(self, task_id: uuid.UUID, task_data: DownloadTaskUpdate) -> Optional[DownloadTask]:
        """更新下载任务"""
        try:
            logger.info(f"Updating download task {task_id}: {task_data.model_dump()}")
            task = self.get_download_task(task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            
            for field, value in task_data.model_dump(exclude_unset=True).items():
                setattr(task, field, value)
            
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Updated download task {task_id}")
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating task: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def delete_download_task(self, task_id: uuid.UUID) -> bool:
        """删除下载任务"""
        try:
            logger.info(f"Deleting download task: {task_id}")
            task = self.get_download_task(task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            
            self.db.delete(task)
            self.db.commit()
            logger.info(f"Deleted download task {task_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting task: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def create_download_failure(self, task_id: uuid.UUID, failure_data: DownloadFailureCreate) -> DownloadFailure:
        """创建下载失败记录"""
        try:
            logger.info(f"Creating download failure for task {task_id}: {failure_data.model_dump()}")
            failure = DownloadFailure(
                task_id=failure_data.task_id,  # 已经是 UUID 类型
                resource_url=str(failure_data.resource_url),
                expected_path=failure_data.expected_path,
                standard_name=failure_data.standard_name,
                resource_type=failure_data.resource_type,
                failure_type=failure_data.failure_type,
                error_message=failure_data.error_message,
                retry_count=failure_data.retry_count
            )
            self.db.add(failure)
            self.db.commit()
            self.db.refresh(failure)
            logger.info(f"Created download failure with ID: {failure.id}")
            return failure
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating failure: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def list_download_failures(
        self,
        task_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        sort: str = "created_at:desc"
    ) -> List[DownloadFailure]:
        """获取下载失败记录列表"""
        try:
            logger.info(f"Listing download failures for task {task_id}: skip={skip}, limit={limit}, sort={sort}")
            query = self.db.query(DownloadFailure)\
                .filter(DownloadFailure.task_id == task_id)
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadFailure, field)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing failures: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def count_download_failures(self, task_id: uuid.UUID) -> int:
        """获取下载失败记录总数"""
        try:
            return self.db.query(func.count(DownloadFailure.id))\
                .filter(DownloadFailure.task_id == task_id)\
                .scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting failures: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def get_download_failure(self, failure_id: uuid.UUID) -> Optional[DownloadFailure]:
        """获取下载失败记录"""
        try:
            logger.info(f"Getting download failure: {failure_id}")
            failure = self.db.query(DownloadFailure).filter(DownloadFailure.id == failure_id).first()
            if not failure:
                raise TaskNotFoundError(f"Failure {failure_id} not found")
            return failure
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting failure: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def retry_download_failure(self, failure_id: uuid.UUID) -> Optional[DownloadFailure]:
        """重试特定失败记录"""
        try:
            logger.info(f"Retrying download failure: {failure_id}")
            failure = self.get_download_failure(failure_id)
            if not failure:
                raise TaskNotFoundError(f"Failure {failure_id} not found")
            
            failure.retry_count += 1
            failure.status = "pending"
            failure.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(failure)
            logger.info(f"Retried download failure {failure_id}")
            return failure
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrying failure: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def abandon_download_failure(self, failure_id: uuid.UUID) -> Optional[DownloadFailure]:
        """放弃特定失败记录"""
        try:
            logger.info(f"Abandoning download failure: {failure_id}")
            failure = self.get_download_failure(failure_id)
            if not failure:
                raise TaskNotFoundError(f"Failure {failure_id} not found")
            
            failure.status = FailureStatusEnum.ABANDONED
            failure.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(failure)
            logger.info(f"Abandoned download failure {failure_id}")
            return failure
        except SQLAlchemyError as e:
            logger.error(f"Database error while abandoning failure: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def pause_download_task(self, task_id: uuid.UUID) -> Optional[DownloadTask]:
        """暂停下载任务"""
        try:
            logger.info(f"Pausing download task: {task_id}")
            task = self.get_download_task(task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            
            task.status = TaskStatus.PENDING
            task.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Paused download task {task_id}")
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error while pausing task: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def resume_download_task(self, task_id: uuid.UUID) -> Optional[DownloadTask]:
        """恢复下载任务"""
        try:
            logger.info(f"Resuming download task: {task_id}")
            task = self.get_download_task(task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            
            task.status = TaskStatus.PENDING
            task.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Resumed download task {task_id}")
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error while resuming task: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")


    def create_downloaded_video(self, task_id: uuid.UUID, video_data: DownloadedVideoCreate) -> DownloadedVideo:
        """创建已下载视频记录"""
        try:
            logger.info(f"Creating downloaded video for task {task_id}: {video_data.model_dump()}")
            video = DownloadedVideo(
                video_id=video_data.video_id,
                liveroom_id=video_data.liveroom_id,
                liveroom_title=video_data.liveroom_title,
                liveroom_url=video_data.liveroom_url,
                video_type=video_data.video_type,
                video_url=video_data.video_url,
                storage_path=video_data.storage_path,  # 注意字段名映射
                file_size=video_data.file_size,
                duration=video_data.duration,
                resolution=video_data.resolution,
                format=video_data.format,
                status=video_data.status,
                task_id=task_id
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            logger.info(f"Created downloaded video with ID: {video.id}")
            return video
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating downloaded video: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def list_downloaded_videos(
        self,
        task_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        sort: str = "created_at:desc"
    ) -> List[DownloadedVideo]:
        """获取已下载视频列表"""
        try:
            logger.info(f"Listing downloaded videos for task {task_id}: skip={skip}, limit={limit}, sort={sort}")
            query = self.db.query(DownloadedVideo)\
                .filter(DownloadedVideo.task_id == task_id)
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadedVideo, field)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing downloaded videos: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def count_downloaded_videos(self, task_id: uuid.UUID) -> int:
        """获取已下载视频总数"""
        try:
            return self.db.query(func.count(DownloadedVideo.id))\
                .filter(DownloadedVideo.task_id == task_id)\
                .scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting downloaded videos: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

            # =================================================================

        # == 核心工作流 (Core Workflow) - 由后台任务系统调用
        # =================================================================

        # =================================================================
        # == 核心工作流 (Core Workflow) - 由后台任务系统调用
        # =================================================================

    def start_download_task(self, task_id: uuid.UUID, retry_flag: bool = False):
        """
        这是执行下载任务的统一入口和编排器。
        """
        task = self.get_download_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found for execution.")
            return
        #如果是第一次下载，则任务状态必须是pending

        if  task.status not in [TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.PARTIAL_COMPLETED] :
            logger.warning(f"yyy,Task {task_id} already in status '{task.status}', skipping execution.")
            return task


        task.status = TaskStatus.PROCESSING
        self.db.commit()

        try:
            if task.resource_type == 'hls':
                result = self.download_m3u8(task, self.download_dir)
            elif task.resource_type == 'mp4' or task.resource_type == 'image':
                result = self.download_mp4_image(task, self.download_dir)
                #result = self.download_m3u8(task, self.download_dir)  # Assuming this method will be created similarly
                #return result
            else:
                raise ValueError(f"Unsupported video type: {task.resource_type}")
            print("xxx")
            # --- 根据下载结果，处理数据库记录 ---
            if task.resource_type == 'hls':
                print("1xxx")
                self._process_download_m3u8_result(task, result)
            if task.resource_type == 'mp4':
                print("2yyxxx")
                self._process_download_mp4_result(task, result)
            if task.resource_type == "image":
                print("3zzxxx")
                self._process_download_mp4_result(task, result)
        except Exception as e:
            logger.error(f"Task {task_id} execution failed critically: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.last_error = str(e)
            self.create_download_failure(task.id, DownloadFailureCreate(
                resource_url=task.resource_url,
                expected_path="",
                standard_name="",
                resource_type='m3u8',
                failure_type="execution_error",
                error_message=str(e),
                retry_count=task.retry_count
            ))
            #self.db.commit()
        finally:
            # 无论成功或失败，都提交最后的更改并刷新对象状态
            self.db.commit()
            self.db.refresh(task)

        # --- 关键修正：返回最终状态的task对象 ---
        return task

    def _process_download_m3u8_result(self, task: DownloadTask, result: Dict):
        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """
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


        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """

        # 2. 创建已下载视频记录
        # TODO: Here you would call ffmpeg to get real metadata and update the result['metadata'] dict
        print("xxxxx")
        #if result.get("success") or failure_ratio <= self.hls_failure_tolerance:
        if final_task_stauts == TaskStatus.COMPLETED :
            print("yyyy", self.hls_failure_tolerance)
            try:
                video = DownloadedVideo(
                    video_id=task.video_id,
                    task_id=task.id,
                    liveroom_id=task.liveroom_id,
                    liveroom_title=str(task.liveroom_title),
                    liveroom_url=task.resource_url,  # Note: using resource_url as placeholder, adjust if needed
                    video_type=task.resource_type,
                    video_url=task.resource_url,
                    storage_path=result["storage_path"],
                    format=task.resource_type,
                    file_size=0,
                    duration=0,
                    resolution="1080p",
                    status="completed",
                )

                self.db.add(video)
                #self.db.commit()
                #self.db.refresh(video)
                logger.info(f"Created downloaded video with ID: {video.id}")
                #return video
            except SQLAlchemyError as e:
                logger.error(f"Database error while creating downloaded video: {str(e)}")
                self.db.rollback()
                raise DatabaseError(f"Database error: {str(e)}")

        if final_task_stauts == TaskStatus.PARTIAL_COMPLETED:
            print("yyyy",self.hls_failure_tolerance)
            try:
                video = DownloadedVideo(
                    video_id=task.video_id,
                    task_id=task.id,
                    liveroom_id=task.liveroom_id,
                    liveroom_title=str(task.liveroom_title),
                    liveroom_url=task.resource_url,  # Note: using resource_url as placeholder, adjust if needed
                    video_type=task.resource_type,
                    video_url=task.resource_url,
                    storage_path=result["storage_path"],
                    format=task.resource_type,
                    file_size=0,
                    duration=0,
                    resolution="1080p",
                    status="partial_completed",
                )

                self.db.add(video)
                #self.db.commit()
                #self.db.refresh(video)
                logger.info(f"Created downloaded video with ID: {video.id}")
                #return video
            except SQLAlchemyError as e:
                logger.error(f"Database error while creating downloaded video: {str(e)}")
                self.db.rollback()
                raise DatabaseError(f"Database error: {str(e)}")

            for failed_segment_info in result["failed_ts_segments"]:
                self.create_download_failure(task.id, DownloadFailureCreate(
                    task_id=task.id,
                    resource_url=failed_segment_info["url"],
                    expected_path=failed_segment_info['expected_path'],
                    standard_name=failed_segment_info['standard_name'],
                    resource_type='ts',
                    failure_type='network_error',
                    error_message=failed_segment_info["error"],
                    retry_count=0
                ))


        #m3u8列表下载有问题，
        #if  result.get("success") == False and not result.get("failed_segments"):
        if final_task_stauts == TaskStatus.FAILED:
            print("task_id", task.id)
            # 1. 尝试根据 task_id 和 resource_type 查找现有的失败记录
            existing_failure = self.db.query(DownloadFailure).filter(
                DownloadFailure.task_id == task.id,
                DownloadFailure.resource_type == 'm3u8'  # 对hls任务，主要失败类型是m3u8
            ).first()

            if existing_failure:
                # 2. 如果找到了，就更新它
                logger.info(f"Updating existing failure record for m3u8 task {task.id}")
                existing_failure.retry_count += 1
                existing_failure.error_message = result.get("error")  # 更新为最新的错误信息
                existing_failure.updated_at = datetime.utcnow()
                if existing_failure.retry_count >= self.max_retry_count:
                    existing_failure.status = FailureStatusEnum.ABANDONED
            else:
                self.create_download_failure(task.id, DownloadFailureCreate(
                    task_id=task.id,
                    resource_url=task.resource_url,
                    expected_path=result['storage_path'],
                    standard_name=result['standard_name'],
                    resource_type="m3u8" if task.resource_type == 'hls' else task.resource_type,
                    failure_type='network_error',
                    error_message=result.get("error"),
                    retry_count=0
                ))

        task.status = final_task_stauts
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} final status updated to: {task.status.value}")


    def _process_download_mp4_result(self, task: DownloadTask, result: Dict):
        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """
        failure_ratio = 1
        print("xxxxxxyyyy, result", result)

        if result.get("success") == True:
            failure_ratio = 0
            final_task_status = TaskStatus.COMPLETED
            task.progress = 1.0
        else:
            failure_ratio = 1
            final_task_status = TaskStatus.FAILED
            task.progress = 0.0

        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """

        # 2. 创建已下载视频记录
        # TODO: Here you would call ffmpeg to get real metadata and update the result['metadata'] dict
        print("xxxxx")
        #if result.get("success") or failure_ratio <= self.hls_failure_tolerance:
        if final_task_status == TaskStatus.COMPLETED :
            try:
                video = DownloadedVideo(
                    video_id=task.video_id,
                    task_id=task.id,
                    liveroom_id=task.liveroom_id,
                    liveroom_title=str(task.liveroom_title),
                    liveroom_url=task.resource_url,  # Note: using resource_url as placeholder, adjust if needed
                    video_type=task.resource_type,
                    video_url=task.resource_url,
                    storage_path=result["storage_path"],
                    format=task.resource_type,
                    file_size=0,
                    duration=0,
                    resolution="1080p",
                    status="completed",
                )

                self.db.add(video)
                #self.db.commit()
                #self.db.refresh(video)
                logger.info(f"Created downloaded video with ID: {video.id}")
                #return video
            except SQLAlchemyError as e:
                logger.error(f"Database error while creating downloaded video: {str(e)}")
                self.db.rollback()
                raise DatabaseError(f"Database error: {str(e)}")


        if final_task_status == TaskStatus.FAILED:
            print("task_idxxxxxx", task.id)
            # 1. 尝试根据 task_id 和 resource_type 查找现有的失败记录
            existing_failure = self.db.query(DownloadFailure).filter(
                DownloadFailure.task_id == task.id,
                DownloadFailure.resource_type == 'mp4'  # 对hls任务，主要失败类型是m3u8
            ).first()

            if existing_failure:
                # 2. 如果找到了，就更新它
                logger.info(f"Updating existing failure record for mp4 task {task.id}")
                existing_failure.retry_count += 1
                existing_failure.error_message = result.get("error")  # 更新为最新的错误信息
                existing_failure.updated_at = datetime.utcnow()
                if existing_failure.retry_count >= self.max_retry_count:
                    existing_failure.status = FailureStatusEnum.ABANDONED
                    final_task_status = TaskStatus.FAILED
            else:
                self.create_download_failure(task.id, DownloadFailureCreate(
                    task_id=task.id,
                    resource_url=task.resource_url,
                    expected_path=result['storage_path'],
                    standard_name=result['standard_name'],
                    resource_type="m3u8" if task.resource_type == 'hls' else task.resource_type,
                    failure_type='network_error',
                    error_message=result.get("error"),
                    retry_count=0
                ))

        task.status = final_task_status
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} final status updated to: {task.status}")

    def _process_download_image_result(self, task: DownloadTask, result: Dict):
        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """
        failure_ratio = 1
        print("xxxxxxyyyy, result", result)

        if result.get("success") == True:
            failure_ratio = 0
            final_task_stauts = TaskStatus.COMPLETED
            task.progress = 1.0
        else:
            failure_ratio = 1
            final_task_stauts = TaskStatus.FAILED
            task.progress = 0.0

        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """

        # 2. 创建已下载视频记录
        # TODO: Here you would call ffmpeg to get real metadata and update the result['metadata'] dict
        print("xxxxx")
        #if result.get("success") or failure_ratio <= self.hls_failure_tolerance:
        if final_task_stauts == TaskStatus.COMPLETED :
            try:
                video = DownloadedVideo(
                    video_id=task.video_id,
                    task_id=task.id,
                    liveroom_id=task.liveroom_id,
                    liveroom_title=str(task.liveroom_title),
                    liveroom_url=task.resource_url,  # Note: using resource_url as placeholder, adjust if needed
                    video_type=task.resource_type,
                    video_url=task.resource_url,
                    storage_path=result["storage_path"],
                    format=task.resource_type,
                    file_size=0,
                    duration=0,
                    resolution="1080p",
                    status="completed",
                )

                self.db.add(video)
                #self.db.commit()
                #self.db.refresh(video)
                logger.info(f"Created downloaded video with ID: {video.id}")
                #return video
            except SQLAlchemyError as e:
                logger.error(f"Database error while creating downloaded video: {str(e)}")
                self.db.rollback()
                raise DatabaseError(f"Database error: {str(e)}")


        if final_task_stauts == TaskStatus.FAILED:
            print("task_idxxxxxx", task.id)
            # 1. 尝试根据 task_id 和 resource_type 查找现有的失败记录
            existing_failure = self.db.query(DownloadFailure).filter(
                DownloadFailure.task_id == task.id,
                DownloadFailure.resource_type == 'image'  # 对hls任务，主要失败类型是m3u8
            ).first()

            if existing_failure:
                # 2. 如果找到了，就更新它
                logger.info(f"Updating existing failure record for image task {task.id}")
                existing_failure.retry_count += 1
                existing_failure.error_message = result.get("error")  # 更新为最新的错误信息
                existing_failure.updated_at = datetime.utcnow()
                if existing_failure.retry_count >= self.max_retry_count:
                    existing_failure.status = FailureStatusEnum.ABANDONED
            else:
                self.create_download_failure(task.id, DownloadFailureCreate(
                    task_id=task.id,
                    resource_url=task.resource_url,
                    expected_path=result['storage_path'],
                    standard_name=result['standard_name'],
                    resource_type="m3u8" if task.resource_type == 'hls' else task.resource_type,
                    failure_type='network_error',
                    error_message=result.get("error"),
                    retry_count=0
                ))

        task.status = final_task_stauts
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} final status updated to: {task.status.value}")

    def generate_standard_filename(self, resource_type, video_id, operation_type, extension, segment_index=None):
            """
            生成标准格式的文件名

            Args:
                resource_type (str): 资源类型 (video/cover/snapshot)
                video_id (str): videoID，如果长度超过8位，将只取后8位
                operation_type (str): 操作类型 (upload/transcoded/fetch)
                extension (str): 文件扩展名

            Returns:
                str: 标准格式的文件名，格式为：
                    {resource_type}_{video_id}_{operation_type}_{timestamp}_{extension}

            Note:
                - timestamp: ISO格式时间戳，格式为YYYYMMDDThhmmss，例如：20240328T153000
                - random_hash: 8位随机十六进制数，用于确保文件名唯一性
                - 如果生成的文件名超过255个字符，将自动截断并保留扩展名
            """
            # 处理resource_id，如果长度超过8位，只取后8位
            # if len(video_id) > 8:
            resource_id = str(video_id)

            timestamp = time.strftime("%Y%m%dT%H%M%S")
            # 增加随机数长度到8位，确保唯一性

            # 生成文件名
            if segment_index is not None and resource_type == 'video' and extension == '.ts':
                # ts文件使用新的命名格式
                filename = f"segment_{segment_index:06d}_{resource_id}_{operation_type}_{timestamp}{extension}"
            else:
                # 其他文件使用标准格式
                filename = f"{resource_type}_{resource_id}_{operation_type}_{timestamp}{extension}"

            # 如果文件名总长度超过255个字符（Windows文件系统限制），进行截断
            if len(filename) > 255:
                # 保留扩展名
                ext_len = len(extension)
                # 计算需要保留的其他部分长度
                remaining_len = 255 - ext_len
                # 截断文件名，保留扩展名
                filename = filename[:remaining_len] + extension

            return filename


    def modify_m3u8_for_local_playback(self, m3u8_filename, video_id, ts_dir, ts_urls, ts_mapping=None, create_new_file=True):
            """
            修改m3u8文件以便本地播放，使用ts_mapping.json中的映射关系

            Args:
                m3u8_filename (str): 原始m3u8文件路径
                ts_dir (str): ts文件所在目录
                ts_urls (list): 新下载的ts文件URL列表
                ts_mapping (dict, optional): ts文件名映射关系
                create_new_file (bool): 是否创建新的m3u8文件，默认为True
            """
            try:
                if ts_mapping is None:
                    # 读取ts_mapping.json文件，与m3u8文件在同一目录
                    video_dir = os.path.dirname(m3u8_filename)  # 获取videos目录
                    mapping_file = os.path.join(video_dir, 'ts_mapping.json')
                    if not os.path.exists(mapping_file):
                        logger.error(f"找不到ts_mapping.json文件: {mapping_file}")
                        return False

                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        ts_mapping = json.load(f)

                # 创建一个新下载ts文件的集合，用于快速查找
                new_downloaded_ts = {os.path.basename(url) for url in ts_urls}

                # 读取原始m3u8文件
                with open(m3u8_filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 按行分割
                lines = content.split('\n')
                modified_lines = []
                ts_count = 0  # 用于跟踪ts片段的顺序

                for line in lines:
                    if line.endswith('.ts'):
                        # 从URL中提取文件名
                        original_filename = os.path.basename(line.strip())

                        # 检查这个文件是否在新下载的ts文件中
                        if original_filename in ts_mapping:
                            standard_filename = ts_mapping[original_filename]
                            # 使用标准文件名作为本地路径
                            local_path = f'ts/{standard_filename}'
                            modified_lines.append(local_path)
                            logger.info(f"替换第 {ts_count} 个ts片段: {original_filename} -> {standard_filename}")

                        else:
                            # 如果不在新下载的列表中或找不到映射，保持原始URL
                            modified_lines.append(line)
                            #if original_filename not in new_downloaded_ts:
                            #    self.logger.info(f"第 {ts_count + 1} 个ts片段未重新下载: {original_filename}")
                            #if original_filename not in ts_mapping:
                            #    self.logger.warning(f"第 {ts_count + 1} 个ts片段找不到映射: {original_filename}")

                        ts_count += 1
                    else:
                        modified_lines.append(line)

                # 根据create_new_file参数决定是创建新文件还是覆盖原文件
                if create_new_file:
                    # 创建新的m3u8文件名
                    dir_name = os.path.dirname(m3u8_filename)
                    new_m3u8_filename = os.path.join(dir_name,
                                                     self.generate_standard_filename('video', video_id, 'local', '.m3u8'))
                else:
                    new_m3u8_filename = m3u8_filename

                # 写入修改后的内容到文件
                with open(new_m3u8_filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(modified_lines))

                logger.info(f"已{'创建' if create_new_file else '更新'}本地播放的m3u8文件: {new_m3u8_filename}")
                logger.info(f"共处理 {ts_count} 个ts片段")
                return True

            except Exception as e:
                logger.error(f"修改m3u8文件时出错: {str(e)}")
                return False

    def download_and_verify_ts_segment(self, url, filename, headers, index):
        """
        下载并验证单个ts片段

        Args:
            url (str): ts片段的URL
            filename (str): 保存的文件路径
            headers (dict): 请求头
            index (int): 片段的索引号

        Returns:
           True or False
        """
        try:
            with requests.get(url, headers=headers, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                print("total_sizexxx", total_size)
                # 下载文件
                with open(filename, 'wb') as f:
                    downloaded_size = 0
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                # 验证文件大小
                actual_size = os.path.getsize(filename)

                if actual_size != total_size:
                    raise Exception(f"文件大小不匹配: 预期 {total_size}, 实际 {actual_size}")

                # 验证文件是否为空
                if actual_size == 0:
                    raise Exception("下载的文件大小为0")

                # 验证文件是否可读
                try:
                    with open(filename, 'rb') as f:
                        # 读取文件头部，检查是否是有效的ts文件
                        header = f.read(4)
                        if not header:
                            raise Exception("无法读取文件头部")
                except Exception as e:
                    raise Exception(f"文件验证失败: {str(e)}")

                return True
        except requests.exceptions.RequestException as e:
            logger.error(f"下载 {url} 时发生致命错误: {e.__class__.__name__} - {e}")
            # 打印完整的错误堆栈，这会告诉你最详细的信息
            logger.error(traceback.format_exc())
            return False
        except Exception as e:
            logger.error(f"下载 {url} 时发生致命错误: {e.__class__.__name__} - {e}")
            # 打印完整的错误堆栈，这会告诉你最详细的信息
            logger.error(traceback.format_exc())
            return False

    def download_mp4_image(self, task:DownloadTask, save_dir=None):
        """
        下载单个文件（如MP4或图像），并遵循标准目录和命名约定。
        """
        result = {
            "success": False,
            "error": None,
            "storage_path": None,
            "standard_name": None
        }

        video_id = task.video_id
        url = task.resource_url
        print("xxxaaaaa")
        try:
            # 1. 创建存储目录 (e.g., .../video_123/mp4/)
            save_dir = os.path.join(self.download_dir, f"video_{str(video_id)}")


            subdir_name = ""
            print("1", task.resource_type)
            if task.resource_type == 'mp4':
                subdir_name = 'mp4'
                resource_type = 'video'
            elif task.resource_type == "image":
                subdir_name = 'image'
                resource_type = 'cover'
            else:
                result['error'] = "format is invalid. An valid format is mp4 or image"
                result['success'] = False
                return result
            print("2", task.resource_type)
            # Create the final media directory path
            media_dir = os.path.join(save_dir, subdir_name)
            os.makedirs(media_dir, exist_ok=True)

            logger.info(f"文件将保存在: {media_dir}")

            path = urlparse(url).path
            # Get the file extension (e.g., .mp4)
            _, extension = os.path.splitext(path)
            extension = extension.lower()  # Use lowercase for reliable comparison

            standard_name = self.generate_standard_filename(resource_type, video_id, 'fetch', extension)
            final_path = os.path.join(media_dir, standard_name)

            result['storage_path'] = final_path
            result['standard_name'] = standard_name

            logger.info(f"开始下载 {url} 到 {final_path}")

            with requests.get(url, headers=self.headers, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()

                with open(final_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)

            logger.info(f"文件下载完成: {final_path}")
            result["success"] = True

        except requests.exceptions.RequestException as e:
            error_msg = f"下载文件时发生网络错误: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"处理文件下载时发生未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg

        return result

    def download_m3u8(self, task:DownloadTask, save_dir=None):
            # 初始化结果
            result = {
                "success": True,
                "error": None,
                "failed_ts_segments": [],
                'expected_path': None,
                'standard_name': None,
                "ts_urls": [],
                "download_start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "download_end_time": None,
                "total_segments": 0,
                "successful_segments": 0,
                "failed_segments": 0,
                "storage_path": ""
            }

            try:
                # 使用指定的保存目录或默认目录
                video_id = task.video_id
                save_dir = os.path.join(self.download_dir, f"video_{str(video_id)}")

                # 创建视频保存目录
                video_dir = os.path.join(save_dir, 'hls')
                result['storage_path'] = video_dir
                os.makedirs(video_dir, exist_ok=True)
                logger.info(f"视频文件将保存在: {video_dir}")


                print("video_id", str(video_id))
                url = task.resource_url
                path_string = urlparse(url).path

                # 2. Create a Path object and get its .name attribute
                file_name = Path(path_string).name
                result['standard_name'] = file_name
                m3u8_filename = os.path.join(video_dir, file_name)
                logger.info(f"开始下载m3u8文件: {url}")

                # 模拟VLC的请求头


                # 创建session来保持连接
                session = requests.Session()
                session.max_redirects = 5

                # 尝试下载m3u8文件
                print("urlxxx",url)
                response = session.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                # 保存m3u8文件
                with open(m3u8_filename, 'wb') as f:
                    f.write(response.content)

                logger.info("m3u8文件下载成功")

                # 解析m3u8文件
                with open(m3u8_filename, 'r') as f:
                    m3u8_content = f.read()

                playlist = m3u8.loads(m3u8_content)
                print("xxx")
                # 获取所有ts片段的URL
                ts_urls = []
                ts_mapping = {}
                for i, segment in enumerate(playlist.segments):
                    ts_url = urljoin(url, segment.uri)
                    # ts_filename = os.path.join(ts_dir, f'segment_{i:06d}.ts')
                    original_filename = os.path.basename(ts_url)
                    standard_filename = self.generate_standard_filename('video', video_id, 'fetch', '.ts',
                                                                        segment_index=i)
                    # 保存映射关系
                    ts_mapping[original_filename] = standard_filename
                    #print("ts_url", ts_url)
                    ts_urls.append(ts_url)


                result["ts_urls"] = ts_urls
                result["total_segments"] = len(ts_urls)
                logger.info(f"找到 {len(ts_urls)} 个视频片段")

                # 创建ts文件保存目录
                ts_dir = os.path.join(video_dir, 'ts')
                os.makedirs(ts_dir, exist_ok=True)
                print("4xxx")
                #更新m3u8文件
                self.modify_m3u8_for_local_playback(m3u8_filename, video_id, ts_dir, ts_urls, ts_mapping=ts_mapping)

                # 使用线程池并发下载ts片段
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = []
                    logger.info(f"开始下载 {len(ts_urls)} 个视频片段")

                    # 提交所有下载任务
                    for i, ts_url in enumerate(ts_urls[:7]):
                        # ts_filename = os.path.join(ts_dir, f'segment_{i:06d}.ts')
                        original_filename = os.path.basename(ts_url)
                        standard_filename = ts_mapping[original_filename]
                        ts_filename = os.path.join(ts_dir, standard_filename)
                        future = executor.submit(self.download_and_verify_ts_segment, ts_url, ts_filename, self.headers, i)
                        futures.append((i, ts_url, ts_filename,  future, i))
                    print("5xxxx")
                    # 等待所有下载完成，同时监控线程健康状态
                    while futures:
                        # 检查失败数量是否超过限制
                        if result["failed_segments"] >= self.maximum_error_ts:
                            print("2-1")
                            logger.error(f'失败片段数量超过{self.maximum_error_ts}个，停止当前视频下载')
                            # 取消所有未完成的下载任务
                            for _, _, future, i in futures:
                                future.cancel()
                            # 更新结果
                            futures.clear()
                            result["success"] = False
                            result["error"] = f'失败片段数量超过{self.maximum_error_ts}个，停止当前视频下载'
                            result["download_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                            result['failed_m3u8'] = None
                            # 清空futures列表，退出while循环，继续处理下一个视频

                            return result

                        # 检查线程健康状态
                        current_time = time.time()
                        for thread_id, status in list(self.thread_status.items()):
                            # 检查线程是否超时或僵死
                            if (current_time - status["start_time"] > self.thread_timeout or
                                    current_time - status.get("last_active", status["start_time"]) > 30):
                                logger.warning(f"发现僵死线程 {thread_id}，正在重启")
                                # 找到对应的future
                                for idx, (i, ts_url, future, segment_index) in enumerate(futures):
                                    if future.done():
                                        continue
                                    # 取消旧的future
                                    future.cancel()
                                    # 创建新的下载任务
                                    original_filename = os.path.basename(ts_url)
                                    try:
                                        standard_filename = ts_mapping[original_filename]
                                    except KeyError:
                                        # 如果获取不到映射，使用保存的segment_index重新生成
                                        standard_filename = self.generate_standard_filename('video', video_id,
                                                                                       'fetch',
                                                                                       '.ts',
                                                                                       segment_index=segment_index)
                                    ts_filename = os.path.join(ts_dir, standard_filename)

                                    new_future = executor.submit(
                                        self.download_and_verify_ts_segment,
                                        ts_url,
                                        ts_filename,
                                        self.headers,
                                        i
                                    )
                                    futures[idx] = (i, ts_url, ts_filename, new_future, segment_index)
                                    break

                        # 检查已完成的future
                        for i, ts_url, ts_filename, future, segment_index in futures[:]:
                            try:
                                if future.done():
                                    if not future.result():
                                        logger.error(f"TS片段 {i} 下载失败: {ts_url}")
                                        result["failed_ts_segments"].append({
                                            "url": ts_url,
                                            'expected_path': ts_dir,
                                            "standard_name": os.path.basename(ts_filename),
                                            "segment_index": i,
                                            "error": "TS片段下载失败",
                                            "total_segments": len(ts_urls),
                                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "retry_count": 0
                                        })
                                        result["failed_segments"] += 1
                                    else:
                                        result["successful_segments"] += 1
                                    futures.remove((i, ts_url, ts_filename, future, segment_index))
                            except concurrent.futures.TimeoutError:
                                logger.error(f"TS片段 {i} 下载超时: {ts_url}")
                                result["failed_ts_segments"].append({
                                    "url": ts_url,
                                    'expected_path': ts_dir,
                                    "standard_name": os.path.basename(ts_filename),
                                    "segment_index": i,
                                    "error": "下载超时",
                                    "total_segments": len(ts_urls),
                                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "retry_count": 0
                                })
                                result["failed_segments"] += 1
                                futures.remove((i, ts_url, ts_filename, future, segment_index))
                            except Exception as e:
                                logger.error(f"TS片段 {i} 下载出错: {str(e)}")
                                result["failed_ts_segments"].append({
                                    "url": ts_url,
                                    'expected_path': ts_dir,
                                    "standard_name": os.path.basename(ts_filename),
                                    "segment_index": i,
                                    "error": str(e),
                                    "total_segments": len(ts_urls),
                                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "retry_count": 0
                                })
                                result["failed_segments"] += 1
                                futures.remove((i, ts_url, ts_filename, future, segment_index))

                        time.sleep(1)

                    # 更新下载结束时间
                    result["download_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

                    # 保存ts文件名映射
                    mapping_file = os.path.join(video_dir, 'ts_mapping.json')
                    with open(mapping_file, 'w', encoding='utf-8') as f:
                        json.dump(ts_mapping, f, ensure_ascii=False, indent=2)
                    logger.info(f"已保存ts文件名映射到: {mapping_file}")


                    # 检查是否有失败的片段
                    if result["failed_ts_segments"]:
                        result["success"] = False
                        result["error"] = f"有 {len(result['failed_ts_segments'])} 个TS片段下载失败"
                        logger.error(result["error"])
                        # 记录详细的失败统计
                        logger.error(f"下载统计: 总数={result['total_segments']}, "
                                          f"成功={result['successful_segments']}, "
                                          f"失败={result['failed_segments']}")
                    else:
                        logger.info("所有视频片段下载完成")
                        logger.info(f"下载统计: 总数={result['total_segments']}, "
                                         f"成功={result['successful_segments']}, "
                                         f"失败={result['failed_segments']}")

                    return result

            except requests.exceptions.RequestException as e:
                error_msg = f"下载m3u8文件时出错: {str(e)}"
                logger.error(error_msg)
                result["success"] = False
                result["error"] = error_msg
                result["download_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                return result
            except Exception as e:
                error_msg = f"处理m3u8文件时出错: {str(e)}"
                logger.error(error_msg)
                result["success"] = False
                result["error"] = error_msg
                result["download_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                return result

    def retry_download_task(self, task_id: uuid.UUID) -> Optional[DownloadTask]:
            """
            Retries all pending failures for a specific download task.
            This is the database-driven version of your retry_failed_downloads function.
            """
            task = self.get_download_task(task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for retry.")


            if task.status not in [TaskStatus.FAILED, TaskStatus.PARTIAL_COMPLETED]:
                logger.warning(f"Task {task_id} is in status '{task.status}' and cannot be retried.")
                # Return the task without changes if it's not in a retryable state
                return task

            # 添加重试次数检查
            if task.retry_count >= self.max_retry_count:
                logger.warning(
                    f"Task {task_id} has exceeded max retry count ({task.retry_count}/{self.max_retry_count}).")
                raise ValueError("重试次数已达上限")

            logger.info(f"Initiating retry for task {task_id}...")

            # 1. 从数据库中获取所有需要重试的失败记录
            failures_to_retry = self.db.query(DownloadFailure).filter(
                DownloadFailure.task_id == task_id,
                DownloadFailure.status == 'pending'  # Or 'retrying'
            ).all()

            if not failures_to_retry:
                logger.info(f"No pending failures found for task {task_id}. Checking task status.")
                # If there are no failures, the task should be marked as completed.
                # 检查是否存在任何“已放弃”的失败记录
                abandoned_failures_count = self.db.query(DownloadFailure.id).filter(
                    DownloadFailure.task_id == task_id,
                    DownloadFailure.status == FailureStatusEnum.ABANDONED
                ).count()

                if abandoned_failures_count > 0:
                    # 如果存在被放弃的记录，那么任务状态应为 PARTIAL_COMPLETED，绝不能是 COMPLETED
                    logger.warning(f"Task {task_id} has abandoned failures and cannot be marked as completed.")
                    self.db.commit()
                    self.db.refresh(task)
                    return task
                else:
                    logger.info(f"No pending or abandoned failures found. Marking task {task_id} as COMPLETED.")
                    task.status = TaskStatus.COMPLETED
                    task.last_error = None
                    self.db.commit()
                    self.db.refresh(task)
                    return task

            # --- 2. 关键决策点：检查是否存在 M3U8 级别的失败 ---
            # 一个失败的taskid只可能最多对应一个m3u8,mp4或image，但是可以对应多个ts
            has_m3u8_failure = any(f.resource_type == 'm3u8' for f in failures_to_retry)
            has_mp4_failure = any(f.resource_type == 'mp4' for f in failures_to_retry)
            has_image_failure = any(f.resource_type == 'image' for f in failures_to_retry)
            has_ts_failure = any(f.resource_type == 'ts' for f in failures_to_retry)
            if has_m3u8_failure or has_mp4_failure or has_image_failure:
                logger.info(f"M3U8 failure detected for task {task_id}. Initiating full re-download.")
                # 清理掉所有旧的失败记录，因为我们要从头开始
                #for failure in failures_to_retry:
                #    self.db.delete(failure)
                #self.db.commit()

                task.retry_count += 1
                # 直接调用主执行流程，这会重新下载m3u8和所有ts文件
                self.start_download_task(task.id)
                # 返回刷新后的任务状态
                self.db.refresh(task)

                if task.status == TaskStatus.COMPLETED:
                    for f in failures_to_retry:
                        self.db.delete(failures_to_retry[0])
                    self.db.commit()
                return task

            if has_ts_failure:
                # --- 3. 如果没有M3U8失败，则只重试失败的TS分片 ---
                logger.info(f"Retrying {len(failures_to_retry)} failed segments for task {task_id}.")
                return self._retry_only_failed_segments(task, failures_to_retry)

    def _retry_only_failed_segments(self, task, failures_to_retry):

                # 2. 【关键修正】准备并执行所有下载任务，不因个别失败而中断
                successful_retries = []
                still_failed_failures = []

                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Map each future back to its corresponding DownloadFailure ORM object
                    # --- 1. 健壮的提交阶段 ---
                    future_to_failure = {}
                    logger.info(f"Submitting {len(failures_to_retry)} segments to the thread pool for retry...")
                    for failure in failures_to_retry:
                        try:
                            filename = os.path.join(failure.expected_path, failure.standard_name)
                            # --- 为 executor.submit() 调用本身添加 try...except ---
                            future = executor.submit(
                                self.download_and_verify_ts_segment,
                                failure.resource_url,
                                filename,
                                self.headers,
                                0
                            )
                            future_to_failure[future] = failure
                        except Exception as e:
                            # 如果在提交阶段就发生错误，直接将其视为失败
                            print("xxxxxxx")
                            logger.info(f"Failed to submit task for {failure.resource_url} to executor: {e}")
                            still_failed_failures.append(failure)


                    for future in concurrent.futures.as_completed(future_to_failure):
                        failure_record = future_to_failure[future]
                        try:
                            # Your function returns True on success, False on failure
                            was_successful = future.result()
                            if was_successful:
                                    successful_retries.append(failure_record)
                                    logger.info(f"Successfully retried download for {failure_record.resource_url}")
                            else:
                                still_failed_failures.append(failure_record)
                                logger.warning(f"Retry attempt failed for {failure_record.resource_url}")


                        except Exception as e:
                            logger.error(f"Retry for {failure_record.resource_url} failed with exception: {e}")
                            still_failed_failures.append(failure_record)

                # 2a. 对成功重试的记录，从数据库中删除
                if successful_retries:
                    logger.info(f"Successfully retried and deleting {len(successful_retries)} failure records.")
                    for failure in successful_retries:
                        self.db.delete(failure)

                # 2b. 对仍然失败的记录，更新其重试次数和状态
                if still_failed_failures:
                    logger.warning(f"{len(still_failed_failures)} segments failed to retry.")
                    for failure in still_failed_failures:
                        failure.retry_count += 1
                        if failure.retry_count >= self.max_retry_count:
                            failure.status = FailureStatusEnum.ABANDONED
                        print("failure.standard_name", failure.standard_name)
                        self.db.add(failure)
                print("xxxxx")
                # 2c. 检查是否所有失败都已解决，并更新主任务状态
                task.retry_count += 1
                if not still_failed_failures:  # 如果仍然失败的列表为空
                    print("yyyy")
                    task.status = TaskStatus.COMPLETED
                    task.last_error = None
                    logger.info(f"All failures for task {task.id} resolved. Task marked as COMPLETED.")

                    # --- 关键修正：同步更新 downloaded_videos 表的状态 ---
                    logger.info(f"Updating associated DownloadedVideo record status to 'completed' for task {task.id}")
                    video_record = self.db.query(DownloadedVideo).filter(
                        DownloadedVideo.task_id == task.id).first()
                    if video_record:
                        # Assuming 'completed' is a valid status for DownloadedVideo
                        video_record.status = 'completed'
                        self.db.add(video_record)
                    else:
                        # This case might happen if the initial download failed before creating a video record.
                        # This indicates a need for a full retry, not a partial one.
                        logger.warning(
                            f"Could not find an associated DownloadedVideo record for successfully retried task {task.id}")
                    # --- 修正结束 ---

                else:
                    #task.status = TaskStatus.PARTIAL_COMPLETED
                    print("zzzzz")
                    task.last_error = f"{len(still_failed_failures)} segments still failing after retry."
                    logger.warning(f"Task {task.id} still has {len(still_failed_failures)} unresolved failures.")

                # 3. 一次性提交所有数据库变更
                logger.warning(f"{len(still_failed_failures)} xxxxx segments failed to retry.")
                self.db.commit()
                self.db.refresh(task)

                return task
```
app/api/v1/endpoints/download.py代码
```
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import create_response, create_error_response
from app.core.deps import get_db
from app.services.download_service import DownloadService
from app.schemas.download import (
    DownloadTaskCreate,
    DownloadTaskUpdate,
    DownloadTask,
    DownloadFailureCreate,
    DownloadFailure,
    DownloadedVideoCreate,
    DownloadedVideo,
    TaskStatus
)
from app.schemas.common import ResponseModel, PageParams, PageResponse

router = APIRouter()

@router.post("/tasks", response_model=ResponseModel[DownloadTask])
def create_download_task(
    task_data: DownloadTaskCreate,
    db: Session = Depends(get_db)
):
    """创建下载任务"""
    try:
        service = DownloadService(db)
        task = service.create_download_task(task_data)
        task_dict = {
            "id": str(task.id),
            "video_id": str(task.video_id),
            "liveroom_id": task.liveroom_id,
            "liveroom_title": task.liveroom_title,
            "liveroom_url": task.liveroom_url,
            "resource_url": task.resource_url,
            "resource_type": task.resource_type,
            "status": task.status,
            "progress": task.progress,
            "retry_count": task.retry_count,
            "last_error": task.last_error,
            "created_at": task.created_at.isoformat() if task.created_at else None,  # 转换为 ISO 格式字符串
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,  # 转换为 ISO 格式字符串
            "completed_at": task.completed_at.isoformat() if task.completed_at else None  # 转换为 ISO 格式字符串

        }
        return create_response(
            code=201,
            message="创建下载任务成功",
            data=task_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.get("/tasks", response_model=ResponseModel[PageResponse[DownloadTask]])
def list_download_tasks(
    params: PageParams = Depends(),
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db)
):
    """获取下载任务列表"""
    try:
        service = DownloadService(db)
        tasks = service.list_download_tasks(
            skip=(params.page - 1) * params.size,
            limit=params.size,
            status=status,
            sort=params.sort
        )
        total = service.count_download_tasks(status=status)
        # --- 关键修改：应用相同的“手动转换”模式 ---
        task_dicts = []
        for task in tasks:
            task_dict = {
                "id": str(task.id),
                "video_id": str(task.video_id),
                "liveroom_id": task.liveroom_id,
                "liveroom_title": task.liveroom_title,
                "liveroom_url": task.liveroom_url,
                "resource_url": task.resource_url,
                "resource_type": task.resource_type,
                "status": task.status,
                "progress": task.progress,
                "retry_count": task.retry_count,
                "last_error": task.last_error,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
            task_dicts.append(task_dict)
        # --- 转换结束 ---

        # 现在传递给PageResponse的是一个字典列表，可以被安全地JSON序列化
        page_data = PageResponse(
            total=total,
            items=task_dicts,  # <-- 使用转换后的字典列表
            page=params.page,
            size=params.size,
            pages=(total + params.size - 1) // params.size
        )

        return create_response(
            code=200,
            message="获取下载任务列表成功",
            data=page_data.model_dump() # 确保传递给最终响应的是字典
        )
    except Exception as e:
        return create_error_response(str(e))

@router.get("/tasks/{task_id}", response_model=ResponseModel[DownloadTask])
def get_download_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取下载任务详情"""
    try:
        service = DownloadService(db)
        task = service.get_download_task(task_id)
        if not task:
            return create_error_response("任务不存在", code=404)
        task_dict = {
            "id": str(task.id),
            "video_id": str(task.video_id),
            "liveroom_id": task.liveroom_id,
            "liveroom_title": task.liveroom_title,
            "liveroom_url": task.liveroom_url,
            "resource_url": task.resource_url,
            "resource_type": task.resource_type,
            "status": task.status,
            "progress": task.progress,
            "retry_count": task.retry_count,
            "last_error": task.last_error,
            "created_at": task.created_at.isoformat() if task.created_at else None,  # 转换为 ISO 格式字符串
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,  # 转换为 ISO 格式字符串
            "completed_at": task.completed_at.isoformat() if task.completed_at else None  # 转换为 ISO 格式字符串

        }
        return create_response(
            code=200,
            message="获取下载任务详情成功",
            data=task_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.put("/tasks/{task_id}", response_model=ResponseModel[DownloadTask])
def update_download_task(
    task_id: uuid.UUID,
    task_data: DownloadTaskUpdate,
    db: Session = Depends(get_db)
):
    """更新下载任务"""
    try:
        service = DownloadService(db)
        task = service.update_download_task(task_id, task_data)
        if not task:
            return create_error_response("任务不存在", code=404)
        return create_response(
            code=200,
            message="更新下载任务成功",
            data=task
        )
    except Exception as e:
        return create_error_response(str(e))

@router.delete("/tasks/{task_id}", response_model=ResponseModel)
def delete_download_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除下载任务"""
    try:
        service = DownloadService(db)
        task = service.get_download_task(task_id)
        if not task:
            return create_error_response("任务不存在", code=404)
        # 添加状态检查
        if task.status == TaskStatus.COMPLETED:
            return create_error_response(
                message="不能删除已完成任务",
                code=400
            )

        service.delete_download_task(task_id)
        return create_response(
            code=200,
            message="删除下载任务成功"
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/tasks/{task_id}/start", response_model=ResponseModel[DownloadTask])
def start_download_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """暂停下载任务"""
    try:
        service = DownloadService(db)
        task = service.start_download_task(task_id)
        if not task:
            return create_error_response("任务不存在", code=404)
        task_dict = {
            "id": str(task.id),
            "video_id": str(task.video_id),
            "liveroom_id": task.liveroom_id,
            "liveroom_title": task.liveroom_title,
            "liveroom_url": task.liveroom_url,
            "resource_url": task.resource_url,
            "resource_type": task.resource_type,
            "status": task.status,
            "progress": task.progress,
            "retry_count": task.retry_count,
            "last_error": task.last_error,
            "created_at": task.created_at.isoformat() if task.created_at else None,  # 转换为 ISO 格式字符串
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,  # 转换为 ISO 格式字符串
            "completed_at": task.completed_at.isoformat() if task.completed_at else None  # 转换为 ISO 格式字符串

        }
        return create_response(
            code=200,
            message="下载任务成功",
            data=task_dict
        )
    except Exception as e:
        return create_error_response(str(e))



@router.post("/tasks/{task_id}/retry", response_model=ResponseModel[DownloadTask])
def retry_download_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """重试下载任务"""
    try:
        service = DownloadService(db)
        task = service.retry_download_task(task_id)
        if not task:
            return create_error_response("任务不存在", code=404)

        task_dict = {
            "id": str(task.id),
            "video_id": str(task.video_id),
            "liveroom_id": task.liveroom_id,
            "liveroom_title": task.liveroom_title,
            "liveroom_url": task.liveroom_url,
            "resource_url": task.resource_url,
            "resource_type": task.resource_type,
            "status": task.status,
            "progress": task.progress,
            "retry_count": task.retry_count,
            "last_error": task.last_error,
            "created_at": task.created_at.isoformat() if task.created_at else None,  # 转换为 ISO 格式字符串
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,  # 转换为 ISO 格式字符串
            "completed_at": task.completed_at.isoformat() if task.completed_at else None  # 转换为 ISO 格式字符串

        }

        return create_response(
            code=200,
            message="重试下载任务成功",
            data=task_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/tasks/{task_id}/failures", response_model=ResponseModel[DownloadFailure])
def create_download_failure(
    task_id: uuid.UUID,
    failure_data: DownloadFailureCreate,
    db: Session = Depends(get_db)
):
    """创建下载失败记录"""
    try:
        service = DownloadService(db)
        failure = service.create_download_failure(task_id, failure_data)
        
        # 将 DownloadFailure 对象转换为字典
        failure_dict = {
            "id": str(failure.id),
            "task_id": str(failure.task_id),
            "resource_url": failure.resource_url,
            "expected_path": failure.expected_path,
            "resource_type": failure.resource_type,
            "failure_type": failure.failure_type,
            "error_message": failure.error_message,
            "status": failure.status,
            "retry_count": failure.retry_count,
            "created_at": failure.created_at.isoformat() if failure.created_at else None,
            "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
        }

        return create_response(
            code=201,
            message="创建下载失败记录成功",
            data=failure_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.get("/tasks/{task_id}/failures", response_model=ResponseModel[PageResponse[DownloadFailure]])
def list_download_failures(
    task_id: uuid.UUID,
    params: PageParams = Depends(),
    db: Session = Depends(get_db)
):
    """获取下载失败记录列表"""
    try:
        service = DownloadService(db)
        failures = service.list_download_failures(
            task_id,
            skip=(params.page - 1) * params.size,
            limit=params.size,
            sort=params.sort
        )
        total = service.count_download_failures(task_id)
        
        # 将 DownloadFailure 对象转换为字典
        failure_dicts = []
        for failure in failures:
            failure_dict = {
                "id": str(failure.id),
                "task_id": str(failure.task_id),
                "resource_url": failure.resource_url,
                "expected_path": failure.expected_path,
                "resource_type": failure.resource_type,
                "failure_type": failure.failure_type,
                "error_message": failure.error_message,
                "status": failure.status,
                "retry_count": failure.retry_count,
                "created_at": failure.created_at.isoformat() if failure.created_at else None,
                "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
            }
            failure_dicts.append(failure_dict)
        
        return create_response(
            code=200,
            message="获取下载失败记录列表成功",
            data=PageResponse(
                total=total,
                items=failure_dicts,
                page=params.page,
                size=params.size,
                pages=(total + params.size - 1) // params.size
            )
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/tasks/{task_id}/videos", response_model=ResponseModel[DownloadedVideo])
def create_downloaded_video(
    task_id: uuid.UUID,
    video_data: DownloadedVideoCreate,
    db: Session = Depends(get_db)
):
    """创建已下载视频记录"""
    try:
        service = DownloadService(db)
        video = service.create_downloaded_video(task_id, video_data)
        return create_response(
            code=201,
            message="创建已下载视频记录成功",
            data=video
        )
    except Exception as e:
        return create_error_response(str(e))

@router.get("/tasks/{task_id}/videos", response_model=ResponseModel[PageResponse[DownloadedVideo]])
def list_downloaded_videos(
    task_id: uuid.UUID,
    params: PageParams = Depends(),
    db: Session = Depends(get_db)
):
    """获取已下载视频列表"""
    try:
        service = DownloadService(db)
        videos = service.list_downloaded_videos(
            task_id,
            skip=(params.page - 1) * params.size,
            limit=params.size,
            sort=params.sort
        )
        total = service.count_downloaded_videos(task_id)
        return create_response(
            code=200,
            message="获取已下载视频列表成功",
            data=PageResponse(
                total=total,
                items=videos,
                page=params.page,
                size=params.size,
                pages=(total + params.size - 1) // params.size
            )
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/tasks/{task_id}/failures/{failure_id}/retry", response_model=ResponseModel[DownloadFailure])
def retry_specific_failure(
    task_id: uuid.UUID,
    failure_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """重试特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.retry_download_failure(failure_id)
        if not failure:
            return create_error_response("失败记录不存在", code=404)
        
        # 将 DownloadFailure 对象转换为字典
        failure_dict = {
            "id": str(failure.id),
            "task_id": str(failure.task_id),
            "resource_url": failure.resource_url,
            "expected_path": failure.expected_path,
            "resource_type": failure.resource_type,
            "failure_type": failure.failure_type,
            "error_message": failure.error_message,
            "status": failure.status,
            "retry_count": failure.retry_count,
            "created_at": failure.created_at.isoformat() if failure.created_at else None,
            "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
        }
        
        return create_response(
            code=200,
            message="重试失败记录成功",
            data=failure_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/tasks/{task_id}/failures/{failure_id}/abandon", response_model=ResponseModel[DownloadFailure])
def abandon_specific_failure(
    task_id: uuid.UUID,
    failure_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """放弃特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.abandon_download_failure(failure_id)
        if not failure:
            return create_error_response("失败记录不存在", code=404)
        
        # 将 DownloadFailure 对象转换为字典
        failure_dict = {
            "id": str(failure.id),
            "task_id": str(failure.task_id),
            "resource_url": failure.resource_url,
            "expected_path": failure.expected_path,
            "resource_type": failure.resource_type,
            "failure_type": failure.failure_type,
            "error_message": failure.error_message,
            "status": failure.status,
            "retry_count": failure.retry_count,
            "created_at": failure.created_at.isoformat() if failure.created_at else None,
            "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
        }
        
        return create_response(
            code=200,
            message="放弃失败记录成功",
            data=failure_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/failures/{failure_id}/retry", response_model=ResponseModel[DownloadFailure])
def retry_failure(
    failure_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """重试特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.retry_download_failure(failure_id)
        if not failure:
            return create_error_response("失败记录不存在", code=404)
        
        # 将 DownloadFailure 对象转换为字典
        failure_dict = {
            "id": str(failure.id),
            "task_id": str(failure.task_id),
            "resource_url": failure.resource_url,
            "expected_path": failure.expected_path,
            "resource_type": failure.resource_type,
            "failure_type": failure.failure_type,
            "error_message": failure.error_message,
            "status": failure.status,
            "retry_count": failure.retry_count,
            "created_at": failure.created_at.isoformat() if failure.created_at else None,
            "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
        }
        
        return create_response(
            code=200,
            message="重试失败记录成功",
            data=failure_dict
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/failures/{failure_id}/abandon", response_model=ResponseModel[DownloadFailure])
def abandon_failure(
    failure_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """放弃特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.abandon_download_failure(failure_id)
        if not failure:
            return create_error_response("失败记录不存在", code=404)
        
        # 将 DownloadFailure 对象转换为字典
        failure_dict = {
            "id": str(failure.id),
            "task_id": str(failure.task_id),
            "resource_url": failure.resource_url,
            "expected_path": failure.expected_path,
            "resource_type": failure.resource_type,
            "failure_type": failure.failure_type,
            "error_message": failure.error_message,
            "status": failure.status,
            "retry_count": failure.retry_count,
            "created_at": failure.created_at.isoformat() if failure.created_at else None,
            "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
        }
        
        return create_response(
            code=200,
            message="放弃失败记录成功",
            data=failure_dict
        )
    except Exception as e:
        return create_error_response(str(e)) 
```


**3.2. 已存在的代码上下文**
*你必须依赖以下已存在的模块和文件来编写新代码。*

  * `@app/models/download.py` (包含 `DownloadedVideo` 和 `DownloadFailure` 模型)
  * `@app/schemas/download.py` (包含所有相关的 Pydantic Schemas)
  * `@app/database.py` (提供 `get_async_db` 依赖)
  * `@app/core/responses.py` (提供 `success_response` 和 `error_response` 工具函数)
  * `@app/core/exceptions.py` (提供必要的异常类)
  * `@app/api/v1/deps.py` (假设其中有 `get_current_admin_user` 依赖)

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

#### **7. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我**更新**以下**三个文件**。请只提供**需要追加的新代码部分**。

1.  `app/services/download_service.py` **(仅追加部分)**
2.  `app/api/v1/endpoints/download.py` **(仅追加部分)**
3.  `app/core/exceptions.py` **(仅追加部分)**