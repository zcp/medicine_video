from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.logging_utils import setup_sanitized_logging
from app.core.responses import error_response
from app.content_safety.exceptions import (
    ContentSafetyBlockedException,
    ContentSafetyServiceException,
)

# 配置日志脱敏
setup_sanitized_logging()

app = FastAPI()

# 设置CORS - 从配置模块读取
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 确保上传目录存在
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 导入路由
from app.api.v1.api import api_router
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
    return {
        "message": "欢迎使用用户服务",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# 挂载静态文件目录：使上传的头像等文件可通过 /uploads/ 访问
# 放在路由注册之后，遵循 FastAPI 官方建议
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")