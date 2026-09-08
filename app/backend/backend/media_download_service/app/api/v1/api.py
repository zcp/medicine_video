from fastapi import APIRouter

from app.api.v1.endpoints import download

api_router = APIRouter()

# 注册下载服务路由
api_router.include_router(
    download.download_router,
    prefix="/download",
    tags=["download"]
) 