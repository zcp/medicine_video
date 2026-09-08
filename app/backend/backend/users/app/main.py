from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.logging_utils import setup_sanitized_logging

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