from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import Settings
from app.core.response import error_response
from app.api.v1.api import api_router
from app.content_safety.exceptions import (
    ContentSafetyBlockedException,
    ContentSafetyServiceException,
)

import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化设置
settings = Settings()
# ------- 配置日志系统（放在最前面）-------
#setup_logging( level=logging.INFO)
# --- 1. 导入未配置的 celery_app 实例 ---
from app.tasks.celery_app import app as celery_app

# --- 2. 在这里对导入的实例进行生产环境配置 ---
celery_app.config_from_object(settings, namespace="CELERY")
celery_app.autodiscover_tasks(packages=["app.tasks"])



# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="直播核心服务 - 管理直播房间和会话",
    # 禁用自动重定向，避免307问题
    redirect_slashes=False
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # 从配置读取
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置媒体文件静态访问
ROOM_MEDIA_ROOT_PATH = os.getenv("ROOM_MEDIA_ROOT_PATH", "./media")
print(f"--- DIAGNOSIS [main.py]: FastAPI is SERVING static files from directory: '{os.path.abspath(ROOM_MEDIA_ROOT_PATH)}'")
# -
#print("ROOM_"ROOM_MEDIA_ROOT_PATH)
# 确保media目录存在
os.makedirs(ROOM_MEDIA_ROOT_PATH, exist_ok=True)

# 挂载静态文件目录
app.mount("/media", StaticFiles(directory=ROOM_MEDIA_ROOT_PATH), name="media")

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(ContentSafetyBlockedException)
async def content_safety_blocked_handler(request: Request, exc: ContentSafetyBlockedException):
    """内容违规统一 422/2005，避免漏捕变成 500"""
    return JSONResponse(
        status_code=422,
        content=error_response(
            code=exc.code,
            message=exc.message or "内容未通过审核，请修改后重试",
        ),
    )


@app.exception_handler(ContentSafetyServiceException)
async def content_safety_service_handler(request: Request, exc: ContentSafetyServiceException):
    """内容安全服务异常统一 422/2004"""
    return JSONResponse(
        status_code=422,
        content=error_response(
            code=exc.code,
            message=exc.message or "内容安全服务暂不可用，请稍后再试",
        ),
    )


@app.get("/")
async def root():
    """根路径"""
    return {"message": "LiveCore Service is running", "version": settings.VERSION} 