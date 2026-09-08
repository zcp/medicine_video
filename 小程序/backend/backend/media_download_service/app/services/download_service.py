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
from uuid import uuid4

import m3u8
import requests
from pyasn1.type.univ import Boolean
from pydantic.v1 import UUID4
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
from app.core.exceptions import DownloadServiceError, TaskNotFoundError, InvalidTaskStatusError, DatabaseError, VideoNotFoundError, FailureRecordNotFoundError, CrawlerError, CrawlerConfigError

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

    def create_download_task(self, task_data: DownloadTaskCreate, user_id: uuid.UUID) -> DownloadTask:
        """创建下载任务"""
        # 变量提取（安全异步异常处理）
        user_id_for_logging = str(user_id)
        liveroom_id_for_logging = str(task_data.liveroom_id) if task_data.liveroom_id else "N/A"
        resource_url_for_logging = task_data.resource_url
        
        try:
            logger.info(f"Creating download task: {task_data.model_dump()}")
            task = DownloadTask(
                user_id=user_id,
                #video_id=task_data.video_id,
                #不使用前端生成的uuid，后端自己生成，提高安全性
                video_id= uuid4(),
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
            logger.error(f"Integrity error creating task for user {user_id_for_logging}: {str(e)}")
            self.db.rollback()
            raise DownloadServiceError(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating task for user {user_id_for_logging}: {str(e)}")
            self.db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")

    def get_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadTask]:
        """获取下载任务"""
        # 变量提取（安全异步异常处理）
        task_id_for_logging = str(task_id)
        user_id_for_logging = str(user_id)
        
        try:
            logger.info(f"Getting download task: {task_id}")
            task = self.db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
            if not task:
                logger.info(f"Task {task_id} not found")
                raise TaskNotFoundError(f"Task {task_id} not found")
            # 验证任务是否属于当前用户
            if str(task.user_id) != str(user_id):
                logger.info(f"Task {task_id} not found, {task.user_id}, {user_id}")
                raise TaskNotFoundError(f"Task {task_id} not found")
            return task
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while getting task - "
                f"任务ID: {task_id_for_logging}, "
                f"用户ID: {user_id_for_logging}, "
                f"错误: {str(e)}"
            )
            raise DatabaseError(f"Database error: {str(e)}")

    def list_download_tasks(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        sort: str = "created_at:desc"
    ) -> List[DownloadTask]:
        """获取下载任务列表"""
        try:
            logger.info(f"Listing download tasks: skip={skip}, limit={limit}, status={status}, sort={sort}")

            # 添加用户ID过滤

           # 确保user_id是UUID类型
           # if isinstance(user_id, int):
           #     user_id = str(user_id)  # 转换为字符串
           # elif isinstance(user_id, str):
           #     user_id = uuid.UUID(user_id)  # 转换为UUID

            query = self.db.query(DownloadTask)

            query = query.filter(DownloadTask.user_id == str(user_id))
            if status:
                query = query.filter(DownloadTask.status == status)
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadTask, field)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing tasks: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def count_download_tasks(self, user_id: uuid.UUID, status: Optional[TaskStatus] = None) -> int:
        """获取下载任务总数"""
        try:
            query = self.db.query(func.count(DownloadTask.id))
            # 添加用户ID过滤
            query = query.filter(DownloadTask.user_id == user_id)
            if status:
                query = query.filter(DownloadTask.status == status)
            return query.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting tasks: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def update_download_task(self, task_id: uuid.UUID, task_data: DownloadTaskUpdate, user_id: uuid.UUID) -> Optional[DownloadTask]:
        """更新下载任务"""
        # 变量提取（安全异步异常处理）
        task_id_for_logging = str(task_id)
        user_id_for_logging = str(user_id)
        
        try:
            logger.info(f"Updating download task {task_id}: {task_data.model_dump()}")
            task = self.get_download_task(task_id, user_id=user_id)
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

    def delete_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """删除下载任务"""
        try:
            logger.info(f"Deleting download task: {task_id}")
            task = self.get_download_task(task_id, user_id=user_id)
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

    def create_download_failure(self, task_id: uuid.UUID, failure_data: DownloadFailureCreate, user_id: uuid.UUID) -> DownloadFailure:
        """创建下载失败记录"""
        try:
            logger.info(f"Creating download failure for task {task_id}: {failure_data.model_dump()}")
            # 验证任务是否属于当前用户
            task = self.get_download_task(task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
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
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        sort: str = "created_at:desc"
    ) -> List[DownloadFailure]:
        """获取下载失败记录列表"""
        try:
            logger.info(f"Listing download failures for task {task_id}: skip={skip}, limit={limit}, sort={sort}")
            # 验证任务是否属于当前用户
            task = self.get_download_task(task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            query = self.db.query(DownloadFailure)\
                .filter(DownloadFailure.task_id == task_id)
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadFailure, field)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing failures: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def count_download_failures(self, task_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """获取下载失败记录总数"""
        try:
            # 验证任务是否属于当前用户
            task = self.get_download_task(task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            return self.db.query(func.count(DownloadFailure.id))\
                .filter(DownloadFailure.task_id == task_id)\
                .scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting failures: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def get_download_failure(self, failure_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadFailure]:
        """获取下载失败记录"""
        try:
            logger.info(f"Getting download failure: {failure_id}")
            failure = self.db.query(DownloadFailure).filter(DownloadFailure.id == failure_id).first()
            if not failure:
                raise FailureRecordNotFoundError(f"Failure {failure_id} not found")
            
            # 然后验证任务是否属于当前用户
            task = self.get_download_task(failure.task_id, user_id=user_id)
            # get_download_task 内部已经包含了权限验证逻辑
            
            return failure
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting failure: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def retry_download_failure(self, failure_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadFailure]:
        """重试特定失败记录"""
        try:
            logger.info(f"Retrying download failure: {failure_id}")
            failure = self.get_download_failure(failure_id, user_id=user_id)
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

    def abandon_download_failure(self, failure_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadFailure]:
        """放弃特定失败记录"""
        try:
            logger.info(f"Abandoning download failure: {failure_id}")
            failure = self.get_download_failure(failure_id, user_id=user_id)
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

    def pause_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadTask]:
        """暂停下载任务"""
        try:
            logger.info(f"Pausing download task: {task_id}")
            task = self.get_download_task(task_id, user_id=user_id)
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

    def resume_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadTask]:
        """恢复下载任务"""
        try:
            logger.info(f"Resuming download task: {task_id}")
            task = self.get_download_task(task_id, user_id=user_id)
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


    def create_downloaded_video(self, task_id: uuid.UUID, video_data: DownloadedVideoCreate, user_id: uuid.UUID) -> DownloadedVideo:
        """创建已下载视频记录"""
        try:
            logger.info(f"Creating downloaded video for task {task_id}: {video_data.model_dump()}")
            # 验证任务是否属于当前用户
            task = self.get_download_task(task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
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
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        sort: str = "created_at:desc"
    ) -> List[DownloadedVideo]:
        """获取已下载视频列表"""
        try:
            logger.info(f"Listing downloaded videos for task {task_id}: skip={skip}, limit={limit}, sort={sort}")
            # 验证任务是否属于当前用户
            task = self.get_download_task(task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
            query = self.db.query(DownloadedVideo)\
                .filter(DownloadedVideo.task_id == task_id)
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadedVideo, field)))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing downloaded videos: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def count_downloaded_videos(self, task_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """获取已下载视频总数"""
        try:
            # 验证任务是否属于当前用户
            task = self.get_download_task(task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")
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

    def start_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID, retry_flag: bool = False):
        """
        这是执行下载任务的统一入口和编排器。
        """
        task = self.get_download_task(task_id, user_id=user_id)
        print(f"Task {task_id}, {user_id} not found for execution.")
        if not task:
            logger.error(f"Task {task_id} not found for execution.")
            return
        #如果是第一次下载，则任务状态必须是pending

        if  task.status not in [TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.PARTIAL_COMPLETED] :
            logger.warning(f"yyy,Task {task_id} already in status '{task.status}', skipping execution.")
            return task

        task.status = TaskStatus.PROCESSING
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)

        # ==================== 新增：视频去重检查 ====================
        try:
            # 4. 查询是否存在相同resource_url且已完成或部分完成的视频
            existing_video = self.db.query(DownloadedVideo).filter(
                DownloadedVideo.video_url == task.resource_url,
                DownloadedVideo.status.in_(['completed', 'partial_completed'])
            ).first()

            if existing_video:
                logger.info(
                    f"视频去重命中 - 任务ID: {task_id}, "
                    f"resource_url: {task.resource_url}, "
                    f"已存在视频ID: {existing_video.video_id}, "
                    f"已存在视频状态: {existing_video.status}, "
                    f"存储路径: {existing_video.storage_path}"
                )

                # 4.1 直接标记任务状态（根据已存在视频的状态）
                if existing_video.status == 'completed':
                    task.status = TaskStatus.COMPLETED
                    task.progress = 1.0
                elif existing_video.status == 'partial_completed':
                    task.status = TaskStatus.PARTIAL_COMPLETED
                    # progress保持原有值，因为partial_completed状态下progress已经正确计算

                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()

                # 4.2 创建新的downloaded_video记录（关联到当前任务）
                # 注意：必须创建新记录，因为liveroom信息可能不同
                new_video = DownloadedVideo(
                    video_id=task.video_id,
                    task_id=task.id,
                    liveroom_id=task.liveroom_id,
                    liveroom_title=str(task.liveroom_title),
                    liveroom_url=task.resource_url,
                    video_type=existing_video.video_type,
                    video_url=task.resource_url,
                    storage_path=existing_video.storage_path,  # 复用存储路径
                    file_size=existing_video.file_size,
                    duration=existing_video.duration,
                    resolution=existing_video.resolution,
                    format=existing_video.format,
                    status=existing_video.status  # 复用已存在视频的状态
                )
                self.db.add(new_video)

                self.db.commit()
                self.db.refresh(task)

                logger.info(
                    f"任务 {task_id} 通过视频去重完成 - "
                    f"最终状态: {str(task.status)}, "
                    f"视频状态: {existing_video.status}"
                )
                return task

        except SQLAlchemyError as e:
            # 数据库查询异常，记录日志并继续正常下载流程
            logger.warning(
                f"视频去重检查失败 - 任务ID: {task_id}, "
                f"错误: {str(e)}, "
                f"将继续正常下载流程"
            )
            # 回滚可能的部分更改，确保数据一致性
            self.db.rollback()
            # 重新刷新task对象，恢复到processing状态
            self.db.refresh(task)

        except Exception as e:
            # 其他未预期的异常，记录详细日志并继续正常下载流程
            logger.error(
                f"视频去重检查发生未预期错误 - 任务ID: {task_id}, "
                f"错误类型: {type(e).__name__}, "
                f"错误信息: {str(e)}, "
                f"将继续正常下载流程",
                exc_info=True
            )
            # 回滚可能的部分更改
            self.db.rollback()
            # 重新刷新task对象
            self.db.refresh(task)
        # ==================== 视频去重检查结束 ====================

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
                self._process_download_m3u8_result(task, result, user_id)
            if task.resource_type == 'mp4':
                print("2yyxxx")
                self._process_download_mp4_result(task, result, user_id)
            if task.resource_type == "image":
                print("3zzxxx")
                self._process_download_mp4_result(task, result, user_id)
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
            ), user_id)
            #self.db.commit()
        finally:
            # 无论成功或失败，都提交最后的更改并刷新对象状态
            self.db.commit()
            self.db.refresh(task)

        # --- 关键修正：返回最终状态的task对象 ---
        return task

    def _process_download_m3u8_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """
        # 变量提取（安全异步异常处理）
        task_id_for_logging = str(task.id)
        user_id_for_logging = str(user_id)
        resource_type_for_logging = task.resource_type.value if hasattr(task.resource_type, 'value') else str(task.resource_type)
        
        try:
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
                    ), user_id)


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
                    ), user_id)

            task.status = final_task_stauts
            task.completed_at = datetime.utcnow()
            logger.info(f"Task {task.id} final status updated to: {str(task.status)}")
            
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
            try:
                self.db.refresh(task)
                task.status = TaskStatus.FAILED
                task.last_error = f"处理下载结果时数据库错误: {str(e)}"
                self.db.commit()
            except:
                pass
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
            try:
                self.db.refresh(task)
                task.status = TaskStatus.FAILED
                task.last_error = f"处理失败: {str(e)}"
                self.db.commit()
            except:
                pass
            raise


    def _process_download_mp4_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """
        # 变量提取（安全异步异常处理）
        task_id_for_logging = str(task.id)
        user_id_for_logging = str(user_id)
        resource_type_for_logging = task.resource_type.value if hasattr(task.resource_type, 'value') else str(task.resource_type)
        
        try:
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
                    ), user_id)

            task.status = final_task_status
            task.completed_at = datetime.utcnow()
            logger.info(f"Task {task.id} final status updated to: {task.status}")
            
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

    def _process_download_image_result(self, task: DownloadTask, result: Dict, user_id: uuid.UUID):
        """
        # 1. 如果任务是completed or abandon：跳过下载视频
        # 2. 如果任务是pending，下载对应视频,
        #     如果 failure_ratio == 0, 那么将下载视频记录写入，downloaded_videos, 更新tasks状态为completed
        #     如果failure_ratio != 1, 那么将下手视频进入写入到downloaded_videos, 状态更新为partial_completed, 更新task的状态为partial_completed, 并且将下载失败的ts记入到download_failure
        # 3. 如果failure_ratio =1, , 那么插入下载记录到download_failure,resource_type为m3u8，或mp4或image， 更新task的状态为failed
        """
        # 变量提取（安全异步异常处理）
        task_id_for_logging = str(task.id)
        user_id_for_logging = str(user_id)
        resource_type_for_logging = task.resource_type.value if hasattr(task.resource_type, 'value') else str(task.resource_type)
        
        try:
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
                    ), user_id)

            task.status = final_task_stauts
            task.completed_at = datetime.utcnow()
            logger.info(f"Task {task.id} final status updated to: {str(task.status)}")
            
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
                    for i, ts_url in enumerate(ts_urls[:50]):
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

    def retry_download_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[DownloadTask]:
            """
            Retries all pending failures for a specific download task.
            This is the database-driven version of your retry_failed_downloads function.
            """
            task = self.get_download_task(task_id, user_id=user_id)
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
                self.start_download_task(task.id, user_id)
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

    def get_downloaded_video(self, video_id: uuid.UUID, user_id: uuid.UUID) -> DownloadedVideo:
        """根据video_id获取已下载视频详情"""
        try:
            logger.info(f"Getting downloaded video: {video_id}")
            video = self.db.query(DownloadedVideo).filter(DownloadedVideo.video_id == video_id).first()
            if not video:
                raise VideoNotFoundError(f"Video {video_id} not found")

            # 然后验证任务是否属于当前用户
            task = self.get_download_task(video.task_id, user_id=user_id)
            # get_download_task 内部已经包含了权限验证逻辑

            return video
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting downloaded video: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def list_failures(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        failure_type: Optional[str] = None,
        sort: str = "created_at:desc"
    ) -> Dict:
        """获取全局失败记录列表（分页）"""
        try:
            logger.info(f"Listing failures: skip={skip}, limit={limit}, status={status}, failure_type={failure_type}, sort={sort}")
            
            # 构建基础查询
            query = self.db.query(DownloadFailure)
            # 添加用户ID过滤
            query = query.join(DownloadTask).filter(DownloadTask.user_id == user_id)
            
            # 根据筛选条件动态添加WHERE条件
            if status:
                query = query.filter(DownloadFailure.status == status)
            if failure_type:
                query = query.filter(DownloadFailure.failure_type == failure_type)
            
            # 获取筛选后的总数
            total = query.count()
            
            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadFailure, field)))
            
            # 执行分页查询
            failures = query.offset(skip).limit(limit).all()
            
            # 转换为字典格式
            failure_dicts = []
            for failure in failures:
                failure_dict = {
                    "failure_id": str(failure.id),
                    "task_id": str(failure.task_id),
                    "resource_url": failure.resource_url,
                    "expected_path": failure.expected_path,
                    "standard_name": failure.standard_name,
                    "resource_type": failure.resource_type,
                    "failure_type": failure.failure_type,
                    "error_message": failure.error_message,
                    "status": failure.status,
                    "retry_count": failure.retry_count,
                    "created_at": failure.created_at.isoformat() if failure.created_at else None,
                    "updated_at": failure.updated_at.isoformat() if failure.updated_at else None
                }
                failure_dicts.append(failure_dict)
            
            return {
                "total": total,
                "items": failure_dicts
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing failures: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def get_failure_details(self, failure_id: uuid.UUID, user_id: uuid.UUID) -> DownloadFailure:
        """根据failure_id获取失败记录详情"""
        try:
            logger.info(f"Getting failure details: {failure_id}")
            failure = self.db.query(DownloadFailure).filter(DownloadFailure.id == failure_id).first()
            if not failure:
                raise FailureRecordNotFoundError(f"Failure {failure_id} not found")
            # 验证任务是否属于当前用户
            task = self.get_download_task(failure.task_id, user_id=user_id)
            if not task:
                raise TaskNotFoundError(f"Task {failure.task_id} not found")
            return failure
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting failure details: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    def list_videos(
            self,
            user_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100,
            resource_type: Optional[str] = None,
            sort: str = "created_at:desc"
    ) -> Dict:
        """获取全局已下载视频列表（分页）"""
        try:
            logger.info(
                f"Listing global videos: skip={skip}, limit={limit}, resource_type={resource_type}, sort={sort}")

            # 构建基础查询
            print("zzzz1")
            query = self.db.query(DownloadedVideo)
            # 添加用户ID过滤
            print("zzzz2")
            query = query.join(DownloadTask).filter(DownloadTask.user_id == user_id)
            print("zzzz3")
            # 根据筛选条件动态添加WHERE条件
            if resource_type:
                query = query.filter(DownloadedVideo.resource_type == resource_type)
            print("zzzz4")
            # 获取筛选后的总数
            total = query.count()

            # 应用排序
            for field, direction in self._parse_sort(sort):
                query = query.order_by(direction(getattr(DownloadedVideo, field)))
            print("zzzz5")
            # 执行分页查询
            videos = query.offset(skip).limit(limit).all()
            print("zzzz6")
            # 转换为字典格式
            video_dicts = []
            for video in videos:
                print("zzzz7")
                video_dict = {
                    "id": str(video.id),
                    "video_id": str(video.video_id),
                    "liveroom_id": video.liveroom_id,
                    "resource_type": video.video_type,
                    "file_size": video.file_size,
                    "duration": video.duration,
                    "resolution": video.resolution,
                    "format": video.format,
                    "storage_path": video.storage_path,
                    "status": video.status,
                    "created_at": video.created_at.isoformat() if video.created_at else None,
                    "updated_at": video.updated_at.isoformat() if video.updated_at else None
                }
                video_dicts.append(video_dict)
            print("zzzz7")
            return {
                "total": total,
                "items": video_dicts
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing global videos: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")

    # ==================== CSV批量导入方法 ====================
    
    def batch_import_tasks_from_csv(
        self,
        file_content: bytes,
        user_id: uuid.UUID,
        skip_duplicates: bool = True,
        auto_start: bool = False
    ) -> Dict:
        """
        从CSV文件批量导入下载任务
        
        Args:
            file_content: CSV文件的二进制内容
            user_id: 当前用户ID
            skip_duplicates: 是否跳过重复的resource_url（默认False）
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
        from pydantic import ValidationError
        
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
            # 1. 解码文件内容（UTF-8-sig编码，支持BOM）
            # ⚠️ 重要：CSV转换时使用utf-8-sig，这里也要用utf-8-sig解码
            try:
                content = file_content.decode('utf-8-sig')
            except UnicodeDecodeError:
                # 如果utf-8-sig失败，尝试utf-8（向后兼容）
                logger.warning("使用utf-8-sig解码失败，尝试utf-8")
                content = file_content.decode('utf-8')
            
            # 2. 使用csv.DictReader解析CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            
            # 3. 验证表头必需列
            # ⚠️ 添加调试信息：记录实际读取到的表头
            actual_fieldnames = csv_reader.fieldnames
            logger.info(
                f"批量导入CSV - 读取到的表头: {actual_fieldnames}, "
                f"表头数量: {len(actual_fieldnames) if actual_fieldnames else 0}"
            )
            
            # 如果表头为空，记录文件内容的前几行用于调试
            if not actual_fieldnames:
                content_preview = content[:500] if len(content) > 500 else content
                logger.error(
                    f"批量导入CSV - 表头为空！文件内容预览（前500字符）:\n{content_preview}"
                )
                raise ValueError("CSV文件没有表头或表头格式错误")
            
            required_columns = {'liveroom_id', 'resource_url', 'resource_type'}
            if not required_columns.issubset(set(actual_fieldnames)):
                missing = required_columns - set(actual_fieldnames)
                logger.error(
                    f"批量导入CSV - 表头验证失败！"
                    f"必需列: {required_columns}, "
                    f"实际列: {set(actual_fieldnames)}, "
                    f"缺少列: {missing}"
                )
                raise ValueError(
                    f"CSV文件格式错误: 缺少必需列 {', '.join(missing)}。"
                    f"实际表头: {list(actual_fieldnames)}"
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
                    # 4.2.1 对resource_url进行标准化（用于除重判断，不修改入库原值）
                    try:
                        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
                        parsed = urlparse(resource_url.strip())
                        scheme = (parsed.scheme or '').lower()
                        netloc = (parsed.netloc or '').lower()
                        # 统一去除路径尾部斜杠
                        path = (parsed.path or '').rstrip('/')
                        # 查询参数排序，保持键值
                        query_pairs = parse_qsl(parsed.query or '', keep_blank_values=True)
                        query = urlencode(sorted(query_pairs))
                        resource_url_normalized = urlunparse((scheme, netloc, path, '', query, ''))
                    except Exception:
                        # 标准化失败时，回退为原始值
                        resource_url_normalized = resource_url
                    
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
                    if not (5 <= len(liveroom_id) <= 20):
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
                        # 仅使用 (user_id, resource_url, liveroom_id) 进行去重（resource_url使用标准化值）
                        existing_task = self.db.query(DownloadTask).filter(
                            #DownloadTask.user_id == user_id,
                            DownloadTask.resource_url == resource_url_normalized,
                            DownloadTask.liveroom_id == liveroom_id
                        ).first()
                        
                        if existing_task:
                            skipped += 1
                            skipped_rows.append({
                                "row": row_number,
                                "liveroom_id": liveroom_id,
                                "liveroom_title": liveroom_title,
                                "resource_url": resource_url,
                                "reason": "任务已存在（相同的user_id + resource_url + liveroom_id）"
                            })
                            continue
                    
                    # 4.7 构造任务数据
                    task_data = DownloadTaskCreate(
                        liveroom_id=liveroom_id,
                        liveroom_title=liveroom_title,
                        liveroom_url=liveroom_url,
                        resource_url=resource_url_normalized,
                        resource_type=resource_type,
                        video_id=uuid.uuid4()
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
    
    def crawl_and_import_tasks(
        self,
        crawler_type: str,
        user_id: uuid.UUID,
        skip_duplicates: bool = True,
        auto_start: bool = False,
        token: Optional[str] = None,  # 新增：可选参数
        cookie: Optional[str] = None,  # 新增：可选参数
        **crawl_kwargs
    ) -> Dict:
        """
        执行爬取并批量导入下载任务
        
        完整流程: 爬取 → 生成CSV → 读取CSV → 批量导入 → 清理临时文件
        
        Args:
            crawler_type: 爬虫类型（vzan等）
            user_id: 当前用户ID
            skip_duplicates: 是否跳过重复任务组合（resource_url + liveroom_id + liveroom_title，默认True）
            auto_start: 导入后是否自动启动任务（默认False）
            **crawl_kwargs: 传递给爬虫的额外参数，如:
                - page_size: 每页数据量（默认10）
                - max_pages: 最大爬取页数（默认全部）
        
        Returns:
            Dict: {
                "crawl_status": "success" | "failed",
                "crawl_rows": int,
                "crawl_file": str,
                "incremental_file": str,
                "failed_file": str,
                "import_result": Dict,  # 来自 batch_import_tasks_from_csv
                "error_message": str
            }
        
        Raises:
            CrawlerConfigError: 爬虫配置无效
            ValueError: 参数错误
        """
        import os
        import time
        
        # 【第一步：变量提取】（安全异步异常处理）
        user_id_for_logging = str(user_id)
        crawler_type_for_logging = str(crawler_type)
        
        # 【第二步：初始化返回结果】
        result = {
            "crawl_status": "failed",
            "crawl_rows": 0,
            "crawl_file": None,
            "incremental_file": None,
            "failed_file": None,
            "import_result": None,
            "error_message": None
        }
        csv_path = None  # 用于finally块清理
        incremental_file = None
        failed_file = None
        start_time = time.time()
        crawler = None  # 用于finally块清理浏览器资源
        try:
            # 【第三步：参数验证】
            if not crawler_type:
                raise ValueError("crawler_type不能为空")
            
            logger.info(
                f"开始爬取并导入 - 用户ID: {user_id_for_logging}, "
                f"爬虫类型: {crawler_type_for_logging}"
            )
            
            # 【第四步：准备爬虫配置】
            from app.core.config import settings

            # 新增：优先使用前端传递的参数，否则从config读取
            final_token = token if token else settings.VZAN_TOKEN
            final_cookie = cookie if cookie else settings.VZAN_COOKIE

            # 新增：对最终使用的token和cookie进行格式验证
            if final_token:
                final_token = final_token.strip()
                if not final_token or len(final_token) < 10 or len(final_token) > 500:
                    raise CrawlerConfigError("token格式无效")
            if final_cookie:
                final_cookie = final_cookie.strip()
                if not final_cookie or len(final_cookie) < 10 or len(final_cookie) > 2000:
                    raise CrawlerConfigError("cookie格式无效")

            crawler_config = {
                'timeout': settings.CRAWLER_TIMEOUT,
                'temp_dir': settings.CRAWLER_TEMP_DIR,
                'batch_size': settings.CRAWLER_BATCH_SIZE,
                'username': settings.VZAN_USERNAME,
                'password': settings.VZAN_PASSWORD,
                'token': final_token,  # 使用最终确定的token
                'cookie': final_cookie  # 使用最终确定的cookie
            }
            
            # 【第五步：创建爬虫实例】
            from app.crawlers import CrawlerFactory
            
            crawler = CrawlerFactory.create(crawler_type, crawler_config)
            
            if not crawler.validate_config():
                raise CrawlerConfigError("爬虫配置验证失败")
            
            # 【第六步：执行爬取】
            crawl_result = crawler.crawl(crawler_config, **crawl_kwargs)
            
            csv_path = crawl_result['csv_file']
            crawl_rows = crawl_result['total_rows']
            incremental_file = crawl_result['incremental_file']
            incremental_rows = crawl_result['incremental_rows']
            failed_file = crawl_result['failed_file']
            
            # 更新结果
            result['crawl_status'] = 'success'
            result['crawl_rows'] = crawl_rows
            result['crawl_file'] = csv_path
            result['incremental_file'] = incremental_file
            result['failed_file'] = failed_file
            
            logger.info(
                f"爬取成功 - 用户ID: {user_id_for_logging}, "
                f"总行数: {crawl_rows}, 增量行数: {incremental_rows}"
            )
            
            # 【第七步：选择导入文件】（重要：仅使用增量文件）
            csv_to_import = None
            force_skip_duplicates = skip_duplicates  # 保存原始去重设置
            
            # ⚠️ 修复：仅当增量文件存在且非空时才导入，不回退到主文件
            # 增量文件不存在或为空，说明没有新增数据，不需要导入
            if incremental_file and os.path.exists(incremental_file) and incremental_rows > 0:
                # 增量文件存在且非空，使用增量文件导入
                csv_to_import = incremental_file
                logger.info(f"使用增量文件导入 - 文件: {incremental_file}, 行数: {incremental_rows}")
            else:
                # 增量文件不存在或为空，说明没有新增数据，不需要导入
                logger.info(
                    f"无新增数据需要导入 - 用户ID: {user_id_for_logging}, "
                    f"增量文件: {incremental_file}, 增量行数: {incremental_rows}"
                )
                # 创建空的导入结果，表示没有数据需要导入（这是正常情况，不是错误）
                import_result = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "skipped": 0,
                    "created_task_ids": [],
                    "failed_rows": [],
                    "skipped_rows": [],
                    "processing_time": round(time.time() - start_time, 2)
                }
                result['import_result'] = import_result
                logger.info(
                    f"爬取完成，无新增数据导入 - 用户ID: {user_id_for_logging}, "
                    f"耗时: {round(time.time() - start_time, 2)}秒"
                )
                return result
            
            # 【第八步：读取CSV文件】
            # ⚠️ 添加文件存在性验证和调试信息
            if not csv_to_import or not os.path.exists(csv_to_import):
                raise FileNotFoundError(
                    f"CSV文件不存在: {csv_to_import}。"
                    f"请检查爬虫是否正确生成了文件。"
                )
            
            file_size = os.path.getsize(csv_to_import)
            logger.info(
                f"准备读取CSV文件 - 路径: {csv_to_import}, "
                f"文件大小: {file_size} 字节, "
                f"文件存在: {os.path.exists(csv_to_import)}"
            )
            
            # ⚠️ 重要：使用utf-8-sig编码读取，与CSV转换时的编码保持一致
            # CSV转换时使用utf-8-sig（带BOM），读取时也要用utf-8-sig
            try:
                with open(csv_to_import, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                logger.error(f"读取CSV文件失败: {str(e)}")
                raise
            
            logger.info(f"成功读取CSV文件 - 大小: {len(file_content)} 字节")
            
            # ⚠️ 调试：打印文件内容的前200字符（用于调试）
            try:
                content_preview = file_content.decode('utf-8-sig')[:200]
                logger.debug(f"CSV文件内容预览（前200字符）:\n{content_preview}")
            except:
                pass
            
            # 【第九步：调用批量导入】
            import_result = self.batch_import_tasks_from_csv(
                file_content=file_content,
                user_id=user_id,
                skip_duplicates=force_skip_duplicates,  # 注意：使用force_skip_duplicates
                auto_start=auto_start
            )
            
            result['import_result'] = import_result
            
            logger.info(
                f"爬取并导入完成 - 用户ID: {user_id_for_logging}, "
                f"导入成功: {import_result['success']}/{import_result['total']}, "
                f"耗时: {round(time.time() - start_time, 2)}秒"
            )
            
            return result
        
        except CrawlerConfigError as e:
            logger.error(
                f"爬虫配置错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}",
                exc_info=True
            )
            result['crawl_status'] = 'failed'  # 显式设置为failed（一致性）
            result['error_message'] = str(e)
            return result  # 不抛出，返回结果
        
        except CrawlerError as e:
            logger.error(
                f"爬取失败 - 用户ID: {user_id_for_logging}, 错误: {str(e)}",
                exc_info=True
            )
            result['crawl_status'] = 'failed'  # 显式设置为failed（一致性）
            result['error_message'] = str(e)
            return result  # 不抛出，返回结果
        
        except ValueError as e:
            logger.error(
                f"参数错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}"
            )
            raise  # 参数错误需要抛出
        
        except Exception as e:
            logger.error(
                f"爬取并导入失败 - 用户ID: {user_id_for_logging}, "
                f"错误类型: {type(e).__name__}, 错误: {str(e)}",
                exc_info=True
            )
            result['crawl_status'] = 'failed'  # 必须设置为failed（可能在第2300行后发生异常）
            result['error_message'] = str(e)
            return result
        
        finally:
            # ⚠️ 【重要】：关闭爬虫浏览器资源
            if crawler:
                try:
                    crawler.close()
                    logger.info("已关闭爬虫浏览器资源")
                except Exception as e:
                    logger.warning(f"关闭爬虫资源失败: {str(e)}")

            # 【第十步：清理临时文件】
            from app.core.config import settings
            
            if settings.CRAWL_IMPORT_DELETE_TEMP_FILE:
                # ⚠️ 重要：只在导入成功时删除增量文件，失败时保留用于调试
                # 检查导入是否成功
                import_success = (
                    result.get('import_result') and 
                    result['import_result'].get('success', 0) > 0
                )
                
                files_to_delete = []
                
                # 只在导入成功时删除增量文件
                if import_success and incremental_file:
                    files_to_delete.append(incremental_file)
                    logger.info(f"导入成功，将删除增量文件: {incremental_file}")
                elif incremental_file:
                    logger.info(
                        f"导入失败或未导入，保留增量文件用于调试: {incremental_file}"
                    )
                
                # 删除失败文件（可选）
                if failed_file:
                    files_to_delete.append(failed_file)
                
                # ❌ 不删除主文件：csv_path (需要保留作为下次增量爬取的基准)
                
                for file_path in files_to_delete:
                    try:
                        if file_path and os.path.exists(file_path):
                            os.remove(file_path)
                            logger.info(f"已删除临时文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {file_path}, 错误: {str(e)}")
                
                # 记录主文件保留
                if csv_path and os.path.exists(csv_path):
                    logger.info(f"保留主文件用于下次增量爬取: {csv_path}")