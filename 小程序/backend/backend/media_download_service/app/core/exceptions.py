from typing import Any, Dict, Optional

class DownloadServiceError(Exception):
    """下载服务基础异常类"""
    def __init__(
        self,
        message: str,
        code: str = "DOWNLOAD_SERVICE_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class TaskNotFoundError(DownloadServiceError):
    """任务不存在异常"""
    def __init__(self, task_id: str):
        super().__init__(
            message=f"下载任务 {task_id} 不存在",
            code="TASK_NOT_FOUND",
            status_code=404,
            details={"task_id": task_id}
        )

class InvalidTaskStatusError(DownloadServiceError):
    """无效的任务状态异常"""
    def __init__(self, task_id: str, current_status: str, target_status: str):
        super().__init__(
            message=f"任务 {task_id} 当前状态 {current_status} 无法转换为 {target_status}",
            code="INVALID_TASK_STATUS",
            status_code=400,
            details={
                "task_id": task_id,
                "current_status": current_status,
                "target_status": target_status
            }
        )

class DatabaseError(DownloadServiceError):
    """数据库操作异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details
        )

class VideoNotFoundError(DownloadServiceError):
    """已下载视频记录未找到异常"""
    def __init__(self, video_id: str):
        super().__init__(
            message=f"已下载视频 {video_id} 不存在",
            code="VIDEO_NOT_FOUND",
            status_code=404,
            details={"video_id": video_id}
        )

class FailureRecordNotFoundError(DownloadServiceError):
    """失败记录未找到异常"""
    def __init__(self, failure_id: str):
        super().__init__(
            message=f"失败记录 {failure_id} 不存在",
            code="FAILURE_RECORD_NOT_FOUND",
            status_code=404,
            details={"failure_id": failure_id}
        )

# ============ 爬虫异常 (Crawler Exceptions) ============

class CrawlerError(Exception):
    """爬虫基础异常"""
    pass


class CrawlerConfigError(CrawlerError):
    """爬虫配置错误"""
    pass


class CrawlerTimeoutError(CrawlerError):
    """爬虫超时错误"""
    pass


class CrawlerAPIError(CrawlerError):
    """爬虫API调用错误"""
    pass


class CrawlerParseError(CrawlerError):
    """爬虫数据解析错误"""
    pass 