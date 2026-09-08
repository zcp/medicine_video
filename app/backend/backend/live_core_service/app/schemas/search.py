"""
搜索历史与热词 Schemas
"""
import uuid
import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field


# ==================== 搜索历史 ====================

class SearchHistoryItem(BaseModel):
    """搜索历史项"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    keyword: str
    search_count: int
    last_searched_at: datetime.datetime


class SearchHistoryListResponse(BaseModel):
    """搜索历史列表响应"""
    code: int = 200
    message: str = "success"
    data: List[SearchHistoryItem]
    timestamp: datetime.datetime


# ==================== 热门搜索 ====================

class HotKeywordItem(BaseModel):
    """热门搜索项"""
    model_config = ConfigDict(from_attributes=True)

    keyword: str = Field(alias='keyword_norm')
    search_count: int = Field(alias='total_count')
    last_searched_at: datetime.datetime


class HotKeywordsResponse(BaseModel):
    """热门搜索响应"""
    code: int = 200
    message: str = "success"
    data: List[HotKeywordItem]
    timestamp: datetime.datetime


# ==================== 搜索建议 ====================

class SearchSuggestionItem(BaseModel):
    """搜索建议项"""
    keyword: str


class SearchSuggestionsResponse(BaseModel):
    """搜索建议响应"""
    code: int = 200
    message: str = "success"
    data: List[SearchSuggestionItem]
    timestamp: datetime.datetime
