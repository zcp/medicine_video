import uuid
import logging
import csv
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.response import create_response, create_error_response
from app.core.deps import get_db, get_current_user
from app.services.download_service import DownloadService
from app.core.exceptions import VideoNotFoundError, FailureRecordNotFoundError, CrawlerError, CrawlerConfigError
from app.core.crawl_import_status import (
    check_running_task,
    get_crawl_import_status,
    save_crawl_import_status,
)
from app.schemas.download import (
    DownloadTaskCreate,
    DownloadTaskUpdate,
    DownloadTask,
    DownloadFailureCreate,
    DownloadFailure,
    DownloadedVideoCreate,
    DownloadedVideo,
    TaskStatus,
    BatchImportResult,
    CrawlAndImportRequest,
    CrawlAndImportResponse
)
from app.schemas.common import ResponseModel, PageParams, PageResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/tasks", response_model=ResponseModel[DownloadTask])
def create_download_task(
    task_data: DownloadTaskCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建下载任务"""
    try:
        logger.info(f"开始处理创建下载任务请求: user_id={current_user['user_id']}")
        service = DownloadService(db)
        task = service.create_download_task(task_data, user_id=current_user["user_id"])
        task_dict = {
            "id": str(task.id),
            "user_id": current_user["user_id"],
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取下载任务列表"""
    try:
        logger.info(f"开始处理获取任务列表请求: user_id={current_user['user_id']}")
        service = DownloadService(db)
        tasks = service.list_download_tasks(
            user_id=current_user["user_id"],
            skip=(params.page - 1) * params.size,
            limit=params.size,
            status=status,
            sort=params.sort
        )
        total = service.count_download_tasks(user_id=current_user["user_id"], status=status)
        # --- 关键修改：应用相同的“手动转换”模式 ---
        task_dicts = []
        for task in tasks:
            task_dict = {
                "id": str(task.id),
                "user_id": current_user["user_id"],
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

@router.get("/tasks/crawl-import-status")
def get_crawl_import_status_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询爬取导入任务状态
    
    用于前端轮询查询当前用户最近一次任务状态
    
    **认证**: 需要JWT Token
    """
    # ==================== 【核心规范0.1】变量提取（安全异步异常处理） ====================
    logger.info(f"API /tasks/crawl-import-status: 请求开始")
    print("xxx1")
    user_id_for_logging = current_user["user_id"]
    print("xxx3")
    user_id = uuid.UUID(user_id_for_logging)
    print("xxx3")

    logger.info(f"API /tasks/crawl-import-status: 请求开始 - 用户ID={user_id_for_logging}")
    
    try:
        # ==================== 业务处理 ====================
        status = get_crawl_import_status(db, user_id)
        
        if not status:
            logger.info(f"状态查询 - User: {user_id_for_logging}, Status: not_found")
            return create_error_response(
                message="未找到爬取导入任务状态",
                code=404
            )
        
        logger.info(f"状态查询成功 - User: {user_id_for_logging}, Status: {status.get('status')}")

        # 【添加调试日志位置2】在这里添加
        logger.info(f"[调试] API端点接收到的状态数据: {status}, 类型: {type(status)}")
        if status and 'progress' in status:
            logger.info(f"[调试] progress 类型: {type(status['progress'])}, 内容: {status['progress']}")
        if status and 'updated_at' in status:
            logger.info(f"[调试] updated_at 类型: {type(status['updated_at'])}, 内容: {status['updated_at']}")


        # ==================== 【核心规范0.2】统一响应处理 ====================
        return create_response(
            data=status,
            message="查询成功",
            code=200
        )
    except Exception as e:
        logger.error(f"状态查询失败 - User: {user_id_for_logging}, Error: {str(e)}", exc_info=True)
        return create_error_response(
            message="查询状态时发生错误",
            code=500
        )

@router.get("/tasks/{task_id}", response_model=ResponseModel[DownloadTask])
def get_download_task(
    task_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取下载任务详情"""
    try:
        logger.info(f"开始处理获取任务详情请求: user_id={current_user['user_id']}, task_id={task_id}")
        service = DownloadService(db)
        task = service.get_download_task(task_id, user_id=current_user["user_id"])
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

@router.patch("/tasks/{task_id}", response_model=ResponseModel[DownloadTask])
def update_download_task(
    task_id: uuid.UUID,
    task_data: DownloadTaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新下载任务"""
    try:
        logger.info(f"开始处理更新任务请求: user_id={current_user['user_id']}, task_id={task_id}")
        service = DownloadService(db)
        task = service.update_download_task(task_id, task_data, user_id=current_user["user_id"])
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除下载任务"""
    try:
        logger.info(f"开始处理删除任务请求: user_id={current_user['user_id']}, task_id={task_id}")
        service = DownloadService(db)
        task = service.get_download_task(task_id, user_id=current_user["user_id"])
        if not task:
            return create_error_response("任务不存在", code=404)
        # 添加状态检查
        if task.status == TaskStatus.COMPLETED:
            return create_error_response(
                message="不能删除已完成任务",
                code=400
            )

        service.delete_download_task(task_id, user_id=current_user["user_id"])
        return create_response(
            code=200,
            message="删除下载任务成功"
        )
    except Exception as e:
        return create_error_response(str(e))

@router.post("/tasks/{task_id}/start", response_model=ResponseModel[DownloadTask])
def start_download_task(
    task_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """暂停下载任务"""
    try:
        logger.info(f"开始处理启动任务请求: user_id={current_user['user_id']}, task_id={task_id}")
        service = DownloadService(db)
        task = service.start_download_task(task_id, user_id=current_user["user_id"])
        if not task:
            print("xxxx, 任务不存在")
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重试下载任务"""
    try:
        logger.info(f"开始处理重试任务请求: user_id={current_user['user_id']}, task_id={task_id}")
        service = DownloadService(db)
        task = service.retry_download_task(task_id, user_id=current_user["user_id"])
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建下载失败记录"""
    try:
        service = DownloadService(db)
        failure = service.create_download_failure(task_id, failure_data, user_id=current_user["user_id"])
        
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取下载失败记录列表"""
    try:
        service = DownloadService(db)
        failures = service.list_download_failures(
            task_id,
            user_id=current_user["user_id"],  # 使用正确的 user_id
            skip=(params.page - 1) * params.size,
            limit=params.size,
            sort=params.sort
        )
        total = service.count_download_failures(task_id,user_id=current_user["user_id"])
        
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建已下载视频记录"""
    try:
        service = DownloadService(db)
        video = service.create_downloaded_video(task_id, video_data, user_id=current_user["user_id"])
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取已下载视频列表"""
    try:
        service = DownloadService(db)
        videos = service.list_downloaded_videos(
            task_id,
            user_id=current_user["user_id"],
            skip=(params.page - 1) * params.size,
            limit=params.size,
            sort=params.sort
        )
        total = service.count_downloaded_videos(task_id, user_id=current_user["user_id"])
        # === 新增：将 DownloadedVideo 对象转换为字典 ===
        video_dicts = []
        for video in videos:
            video_dict = {
                "id": str(video.id),
                "video_id": str(video.video_id),
                "liveroom_id": video.liveroom_id,
                "liveroom_title": video.liveroom_title,
                "liveroom_url": video.liveroom_url,
                "video_type": video.video_type,
                "video_url": video.video_url,
                "storage_path": video.storage_path,
                "file_size": video.file_size,
                "duration": video.duration,
                "resolution": video.resolution,
                "format": video.format,
                "status": video.status,
                "created_at": video.created_at.isoformat() if video.created_at else None,
                "updated_at": video.updated_at.isoformat() if video.updated_at else None
            }
            video_dicts.append(video_dict)
        # === 转换结束 ===
        return create_response(
            code=200,
            message="获取已下载视频列表成功",
            data=PageResponse(
                total=total,
                items=video_dicts,  # <-- 修改：使用转换后的字典列表
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重试特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.retry_download_failure(failure_id, user_id=current_user["user_id"])
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """放弃特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.abandon_download_failure(failure_id,user_id=current_user["user_id"])
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重试特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.retry_download_failure(failure_id,user_id=current_user["user_id"])
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """放弃特定失败记录"""
    try:
        service = DownloadService(db)
        failure = service.abandon_download_failure(failure_id, user_id=current_user["user_id"])
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

# === 新增API接口 ===

@router.get("/videos/{video_id}", response_model=ResponseModel[DownloadedVideo])
def get_downloaded_video(
    video_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询已下载视频详情"""
    try:
        service = DownloadService(db)
        video = service.get_downloaded_video(video_id, user_id=current_user["user_id"])
        
        # 将 DownloadedVideo 对象转换为字典
        video_dict = {
            "id": str(video.id),
            "video_id": str(video.video_id),
            "liveroom_id": video.liveroom_id,
            "liveroom_title": video.liveroom_title,
            "liveroom_url": video.liveroom_url,
            "video_type": video.video_type,
            "video_url": video.video_url,
            "storage_path": video.storage_path,
            "file_size": video.file_size,
            "duration": video.duration,
            "resolution": video.resolution,
            "format": video.format,
            "status": video.status,
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "updated_at": video.updated_at.isoformat() if video.updated_at else None
        }
        
        return create_response(
            code=200,
            message="获取已下载视频详情成功",
            data=video_dict
        )
    except VideoNotFoundError as e:
        return create_error_response(str(e), code=404)
    except Exception as e:
        return create_error_response("服务器内部错误", code=500)

@router.get("/failures", response_model=ResponseModel[PageResponse[DownloadFailure]])
def list_all_failures(
    params: PageParams = Depends(),
    status: Optional[str] = Query(None, description="按失败记录状态筛选"),
    failure_type: Optional[str] = Query(None, description="按失败类型筛选"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询所有失败记录（分页）"""
    try:
        service = DownloadService(db)
        result = service.list_failures(
            user_id=current_user["user_id"],
            skip=(params.page - 1) * params.size,
            limit=params.size,
            status=status,
            failure_type=failure_type,
            sort=params.sort
        )
        
        page_data = PageResponse(
            total=result["total"],
            items=result["items"],
            page=params.page,
            size=params.size,
            pages=(result["total"] + params.size - 1) // params.size
        )
        
        return create_response(
            code=200,
            message="获取全局失败记录列表成功",
            data=page_data.model_dump()
        )
    except Exception as e:
        return create_error_response("服务器内部错误", code=500)


@router.get("/videos", response_model=ResponseModel[PageResponse[DownloadedVideo]])
def list_all_videos(
        params: PageParams = Depends(),
        resource_type: Optional[str] = Query(None, description="按资源类型筛选"),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """查询所有已下载视频（分页）"""
    try:
        print("xxxxx1")
        service = DownloadService(db)
        result = service.list_videos(
            user_id=current_user["user_id"],
            skip=(params.page - 1) * params.size,
            limit=params.size,
            resource_type=resource_type,
            sort=params.sort
        )
        print("xxx2")
        page_data = PageResponse(
            total=result["total"],
            items=result["items"],
            page=params.page,
            size=params.size,
            pages=(result["total"] + params.size - 1) // params.size
        )

        return create_response(
            code=200,
            message="获取全局视频列表成功",
            data=page_data.model_dump()
        )
    except Exception as e:
        return create_error_response("服务器内部错误", code=500)

@router.get("/failures/{failure_id}", response_model=ResponseModel[DownloadFailure])
def get_failure_details(
    failure_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询单个失败记录详情"""
    try:
        service = DownloadService(db)
        failure = service.get_failure_details(failure_id, user_id=current_user["user_id"])
        
        # 将 DownloadFailure 对象转换为字典
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
        
        return create_response(
            code=200,
            message="获取失败记录详情成功",
            data=failure_dict
        )
    except FailureRecordNotFoundError as e:
        return create_error_response(str(e), code=404)
    except Exception as e:
        return create_error_response("服务器内部错误", code=500)


# ==================== CSV批量导入API端点 ====================

@router.post("/tasks/batch-import")
def batch_import_tasks(
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
            return create_error_response(
                code=400,
                message="文件类型错误，必须是CSV文件"
            )
        
        # 2. 读取文件内容
        file_content = file.read()
        file_size = len(file_content)
        
        # 3. 验证文件大小（10MB = 10485760 bytes）
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            return create_error_response(
                code=413,
                message="文件大小超过限制，最大允许10MB",
                data={
                    "file_size": file_size,
                    "max_size": max_size
                }
            )
    
        
        # 4. 验证文件不为空
        if file_size == 0:
            return create_error_response(
                code=400,
                message="文件不能为空"
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
        # 7. 根据结果返回不同的响应（HTTP状态码统一为200，业务状态码在body的code字段）
        
        # 7.1 全部失败（成功数为0）
        if result['success'] == 0:
            return create_response(
                code=400,
                message="批量导入失败，所有行都处理失败",
                data=result
            )
        
        # 7.2 部分成功（有失败行或有跳过行）
        if result['failed'] > 0 or result['skipped'] > 0:
            return create_response(
                code=207,
                message="批量导入部分成功",
                data=result
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
        return create_error_response(code=400, message=str(e))
    
    except UnicodeDecodeError as e:
        # 文件编码错误
        logger.warning(
            f"文件编码错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}"
        )
        return create_error_response(
            code=400,
            message="文件编码错误，请使用UTF-8编码"
        )
    
    except csv.Error as e:
        # CSV解析错误
        logger.warning(
            f"CSV格式错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, 错误: {str(e)}"
        )
        return create_error_response(
            code=400,
            message="CSV文件格式错误"
        )
    
    except SQLAlchemyError as e:
        # 数据库操作错误
        logger.error(
            f"批量导入数据库错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, 错误: {str(e)}",
            exc_info=True
        )
        # 注意：服务层已执行rollback
        return create_error_response(code=400, message="数据库操作失败")
    
    except Exception as e:
        # 未知错误
        logger.error(
            f"批量导入未知错误 - 用户ID: {user_id_for_logging}, "
            f"文件名: {file_name_for_logging}, "
            f"错误类型: {type(e).__name__}, 错误: {str(e)}",
            exc_info=True
        )
        return create_error_response(code=500, message="服务器内部错误")


# ==================== 爬取与导入API端点 ====================

@router.post("/tasks/crawl-and-import")
def crawl_and_import_tasks(
    request_data: CrawlAndImportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    爬取并批量导入下载任务
    
    完整流程: 爬取 → 生成CSV → 批量导入任务 → 返回结果
    
    **认证**: 需要JWT Token
    """
    # ==================== 【核心规范0.1】变量提取（安全异步异常处理） ====================
    user_id_for_logging = current_user["user_id"]
    crawler_type_for_logging = request_data.crawler_type
    user_id = uuid.UUID(user_id_for_logging)
    
    logger.info(
        f"API /tasks/crawl-and-import: 请求开始 - "
        f"用户ID={user_id_for_logging}, 爬虫类型={crawler_type_for_logging}"
    )
    
    try:
        # ==================== 并发控制：检查是否已有运行中的任务 ====================
        if check_running_task(db, user_id):
            # 获取当前运行任务的状态信息（用于返回给前端）
            running_status = get_crawl_import_status(db, user_id)
            progress = running_status.get("progress", {}) if running_status else {}
            
            logger.warning(f"并发控制 - User: {user_id_for_logging}, 有正在运行的任务")
            return create_error_response(
                message="您有一个爬取导入任务正在执行中，请等待任务完成后再试",
                code=409,
                data={
                    "status": "running",
                    "start_time": progress.get("start_time") if progress else None,
                    "suggestion": "您可以通过 GET /api/v1/download/tasks/crawl-import-status 接口查询任务状态",
                },
            )
        
        # ==================== 无运行任务：写入 running 状态 ====================
        progress_data = {
            "start_time": datetime.utcnow().isoformat()
        }
        save_crawl_import_status(db, user_id, "running", progress_data)
        logger.info(f"状态记录 - User: {user_id_for_logging}, Status: running")
        
        # ==================== 业务处理 ====================
        service = DownloadService(db)
        
        # 准备爬虫参数
        crawl_kwargs = {}
        if request_data.crawl_options:
            crawl_kwargs = request_data.crawl_options.model_dump(exclude_unset=True)

        # 新增：提取token和cookie（如果前端传递了）
        # 注意：不记录到日志中
        token = request_data.token if hasattr(request_data, 'token') and request_data.token else None
        cookie = request_data.cookie if hasattr(request_data, 'cookie') and request_data.cookie else None


        # 调用服务层方法（保持原有同步执行逻辑完全不变）
        result = service.crawl_and_import_tasks(
            crawler_type=request_data.crawler_type,
            user_id=user_id,
            skip_duplicates=request_data.skip_duplicates,
            auto_start=request_data.auto_start,
            token=token,  # 新增参数
            cookie=cookie,  # 新增参数
            **crawl_kwargs
        )
        
        # ==================== 成功完成后：写入 completed 状态 ====================
        # 获取之前写入的 start_time（从状态中读取）
        existing_status = get_crawl_import_status(db, user_id)
        existing_progress = existing_status.get("progress", {}) if existing_status else {}
        start_time = existing_progress.get("start_time", datetime.utcnow().isoformat())
        
        # 构建完整的 progress 数据
        completed_progress = {
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "result": result  # 保存服务层返回的完整结果
        }
        save_crawl_import_status(db, user_id, "completed", completed_progress)
        logger.info(f"Crawl and import completed - User: {user_id_for_logging}")
        
        # ==================== 【核心规范0.2】统一响应处理 ====================
        # 根据结果返回不同响应
        
        # 1. 爬取失败
        if result['crawl_status'] == 'failed':
            return create_error_response(
                message=f"爬取失败: {result.get('error_message', '未知错误')}",
                code=500
            )
        
        # 2. 爬取成功，但导入全部失败（需要区分"没有数据导入"和"导入失败"）
        import_result = result.get('import_result')
        if import_result and import_result['success'] == 0:
            # 如果total=0且failed=0，说明没有数据需要导入（正常情况）
            if import_result['total'] == 0 and import_result['failed'] == 0:
                return create_response(
                    data=result,
                    message="爬取成功，无新增数据需要导入",
                    code=200
                )
            # 否则是导入失败
            return create_error_response(
                message="爬取成功，但导入全部失败",
                code=400,
                data=result
            )
        
        # 3. 爬取成功，导入部分成功
        if result.get('import_result') and result['import_result']['failed'] > 0:
            return create_response(
                data=result,
                message="爬取成功，导入部分成功",
                code=207
            )
        
        # 4. 爬取和导入全部成功
        return create_response(
            data=result,
            message="爬取并导入成功",
            code=200
        )
    
    # ==================== 【核心规范0.3】异常处理（使用提取的变量记录日志） ====================
    except ValueError as e:
        # 参数错误
        logger.warning(
            f"参数错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}"
        )
        # 异常处理：写入 failed 状态
        # 获取之前写入的 start_time（从状态中读取，如果存在）
        existing_status = get_crawl_import_status(db, user_id)
        existing_progress = existing_status.get("progress", {}) if existing_status else {}
        start_time = existing_progress.get("start_time", datetime.utcnow().isoformat())
        
        failed_progress = {
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        save_crawl_import_status(db, user_id, "failed", failed_progress)
        return create_error_response(message=f"参数错误: {str(e)}", code=400)
    
    except CrawlerConfigError as e:
        # 爬虫配置错误
        logger.error(
            f"爬虫配置错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}"
        )
        # 异常处理：写入 failed 状态
        existing_status = get_crawl_import_status(db, user_id)
        existing_progress = existing_status.get("progress", {}) if existing_status else {}
        start_time = existing_progress.get("start_time", datetime.utcnow().isoformat())
        
        failed_progress = {
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        save_crawl_import_status(db, user_id, "failed", failed_progress)
        return create_error_response(message=f"爬虫配置错误: {str(e)}", code=400)
    
    except CrawlerError as e:
        # 爬虫执行错误
        logger.error(
            f"爬虫执行错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}",
            exc_info=True
        )
        # 异常处理：写入 failed 状态
        existing_status = get_crawl_import_status(db, user_id)
        existing_progress = existing_status.get("progress", {}) if existing_status else {}
        start_time = existing_progress.get("start_time", datetime.utcnow().isoformat())
        
        failed_progress = {
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        save_crawl_import_status(db, user_id, "failed", failed_progress)
        return create_error_response(message=f"爬虫执行错误: {str(e)}", code=500)
    
    except SQLAlchemyError as e:
        # 数据库错误（服务层已rollback）
        logger.error(
            f"数据库错误 - 用户ID: {user_id_for_logging}, 错误: {str(e)}",
            exc_info=True
        )
        # 异常处理：写入 failed 状态
        existing_status = get_crawl_import_status(db, user_id)
        existing_progress = existing_status.get("progress", {}) if existing_status else {}
        start_time = existing_progress.get("start_time", datetime.utcnow().isoformat())
        
        failed_progress = {
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        save_crawl_import_status(db, user_id, "failed", failed_progress)
        return create_error_response(message="数据库操作失败", code=1002)
    
    except Exception as e:
        # 未知错误
        logger.error(
            f"未知错误 - 用户ID: {user_id_for_logging}, "
            f"错误类型: {type(e).__name__}, 错误: {str(e)}",
            exc_info=True
        )
        # 异常处理：写入 failed 状态
        existing_status = get_crawl_import_status(db, user_id)
        existing_progress = existing_status.get("progress", {}) if existing_status else {}
        start_time = existing_progress.get("start_time", datetime.utcnow().isoformat())
        
        failed_progress = {
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        save_crawl_import_status(db, user_id, "failed", failed_progress)
        return create_error_response(message="服务器内部错误", code=1000) 