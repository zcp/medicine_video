"""
搜索历史、热门搜索、搜索建议 API 端点

这些端点是对现有 GET /api/v1/search 的补充，不修改原有搜索契约。
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.crud import search as search_crud
from app.schemas.search import (
    SearchHistoryItem,
    HotKeywordItem,
    SearchSuggestionItem,
)
from app.core.response import success_response, error_response
import logging

from app.content_safety.exceptions import ContentSafetyBlockedException, ContentSafetyServiceException
from app.content_safety.schemas import ContentSafetyItem
from app.content_safety.service import check_content_safety

logger = logging.getLogger(__name__)

# 搜索历史路由（用户相关）
search_history_router = APIRouter()

# 热门搜索和搜索建议路由（公开）
search_extra_router = APIRouter()


# ==================== 搜索历史 ====================

@search_history_router.get("/search-history", response_model=None, tags=["搜索历史"])
async def get_search_history(
    limit: int = Query(10, ge=1, le=20, description="返回条数"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的搜索历史"""
    user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))

    try:
        items = await search_crud.get_user_history(db, user_id, limit)
        data = [SearchHistoryItem.model_validate(item).model_dump(mode='json') for item in items]
        return JSONResponse(status_code=200, content=success_response(data=data))
    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))


@search_history_router.delete("/search-history/{history_id}", response_model=None, tags=["搜索历史"])
async def delete_search_history(
    history_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除单条搜索历史"""
    user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))

    try:
        deleted = await search_crud.delete_user_history_item(db, user_id, history_id)
        if not deleted:
            return JSONResponse(status_code=404, content=error_response(code=2001, message="历史记录不存在"))
        return JSONResponse(status_code=200, content=success_response(data=None, message="删除成功"))
    except Exception as e:
        logger.error(f"删除搜索历史失败: {e}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))


@search_history_router.delete("/search-history", response_model=None, tags=["搜索历史"])
async def clear_search_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """清空当前用户的全部搜索历史"""
    user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))

    try:
        count = await search_crud.clear_user_history(db, user_id)
        return JSONResponse(status_code=200, content=success_response(
            data={"deleted_count": count}, message="清空成功"
        ))
    except Exception as e:
        logger.error(f"清空搜索历史失败: {e}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))


# ==================== 热门搜索 ====================

@search_extra_router.get("/hot-keywords", response_model=None, tags=["热门搜索"])
async def get_hot_keywords(
    limit: int = Query(10, ge=1, le=50, description="返回条数"),
    days: int = Query(7, ge=1, le=30, description="统计天数窗口"),
    db: AsyncSession = Depends(get_db)
):
    """获取平台热门搜索词（公开接口）"""
    try:
        items = await search_crud.get_hot_keywords(db, limit, days)
        data = [HotKeywordItem.model_validate(item).model_dump(mode='json') for item in items]
        return JSONResponse(status_code=200, content=success_response(data=data))
    except Exception as e:
        logger.error(f"获取热门搜索失败: {e}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))


# ==================== 搜索建议 ====================

@search_extra_router.get("/suggestions", response_model=None, tags=["搜索建议"])
async def get_suggestions(
    keyword: str = Query(..., min_length=1, max_length=255, description="输入关键词"),
    limit: int = Query(10, ge=1, le=20, description="返回条数"),
    db: AsyncSession = Depends(get_db)
):
    """获取搜索建议（公开接口，前缀匹配）"""
    try:
        await check_content_safety(
            db,
            scene="search_query",
            items=[ContentSafetyItem(field_name="keyword", value=keyword)],
            resource_type="search_suggestion",
        )
        keywords = await search_crud.get_suggestions(db, keyword, limit)
        data = [SearchSuggestionItem(keyword=kw).model_dump() for kw in keywords]
        return JSONResponse(status_code=200, content=success_response(data=data))
    except ContentSafetyBlockedException as e:
        return JSONResponse(status_code=422, content=error_response(code=e.code, message=e.message))
    except ContentSafetyServiceException as e:
        return JSONResponse(status_code=422, content=error_response(code=e.code, message=e.message))
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))


# ==================== 搜索推荐 ====================

@search_extra_router.get("/recommendations", response_model=None, tags=["搜索推荐"])
async def get_recommendations(
    keyword: Optional[str] = Query(None, description="搜索关键词（可选）"),
    limit: int = Query(8, ge=1, le=20, description="返回条数"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """搜索推荐（公开接口，可选认证以启用个性化）"""
    user_id = None
    if current_user:
        user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))

    try:
        items = await search_crud.get_recommendations(db, keyword, user_id, limit)
        return JSONResponse(status_code=200, content=success_response(data=items))
    except Exception as e:
        logger.error(f"获取搜索推荐失败: {e}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))
