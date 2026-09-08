"""
搜索历史与热词 CRUD
"""
import uuid
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import UserSearchHistory, SearchKeywordStats
import logging

logger = logging.getLogger(__name__)

MAX_HISTORY_PER_USER = 20


def _normalize_keyword(keyword: str) -> str:
    """标准化关键词：trim + 转小写 + 压缩空白"""
    return " ".join(keyword.strip().lower().split())


# ==================== 搜索落库（搜索接口内部调用） ====================

async def record_search(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    keyword: str
) -> None:
    """
    记录一次搜索行为（同步调用，不阻塞搜索结果返回）

    做两件事：
    1. upsert 用户历史表
    2. upsert 热词统计表
    """
    keyword_norm = _normalize_keyword(keyword)
    if not keyword_norm or len(keyword_norm) < 2:
        return

    # 1. upsert 用户历史（仅登录用户）
    if user_id:
        stmt = text("""
            INSERT INTO user_search_history (id, user_id, keyword, keyword_norm, search_count, last_searched_at)
            VALUES (:id, :user_id, :keyword, :keyword_norm, 1, now())
            ON CONFLICT (user_id, keyword_norm)
            DO UPDATE SET
                search_count = user_search_history.search_count + 1,
                last_searched_at = now(),
                updated_at = now()
        """)
        await db.execute(stmt, {
            'id': str(uuid.uuid4()),
            'user_id': str(user_id),
            'keyword': keyword.strip(),
            'keyword_norm': keyword_norm,
        })

        # 控制历史条数：删除超出的旧记录
        await _trim_user_history(db, user_id)

    # 2. upsert 热词统计
    stmt = text("""
        INSERT INTO search_keyword_stats (id, keyword_norm, keyword, total_count, last_searched_at)
        VALUES (:id, :keyword_norm, :keyword, 1, now())
        ON CONFLICT (keyword_norm)
        DO UPDATE SET
            total_count = search_keyword_stats.total_count + 1,
            last_searched_at = now(),
            updated_at = now()
    """)
    await db.execute(stmt, {
        'id': str(uuid.uuid4()),
        'keyword_norm': keyword_norm,
        'keyword': keyword.strip(),
    })

    await db.flush()
    logger.info(f"记录搜索: user={str(user_id)[:8] if user_id else 'anon'}, keyword={keyword_norm}")


async def _trim_user_history(db: AsyncSession, user_id: uuid.UUID) -> None:
    """保留最近 MAX_HISTORY_PER_USER 条历史，删除多余的"""
    stmt = text("""
        DELETE FROM user_search_history
        WHERE id IN (
            SELECT id FROM user_search_history
            WHERE user_id = :user_id
            ORDER BY last_searched_at DESC
            OFFSET :offset
        )
    """)
    result = await db.execute(stmt, {
        'user_id': str(user_id),
        'offset': MAX_HISTORY_PER_USER,
    })
    if result.rowcount > 0:
        logger.info(f"清理用户历史: user={str(user_id)[:8]}, 删除{result.rowcount}条")


# ==================== 搜索历史查询 ====================

async def get_user_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 10
) -> List[UserSearchHistory]:
    """获取用户搜索历史，按最近搜索时间倒序"""
    stmt = (
        select(UserSearchHistory)
        .where(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.last_searched_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_user_history_item(
    db: AsyncSession,
    user_id: uuid.UUID,
    history_id: uuid.UUID
) -> bool:
    """删除单条搜索历史"""
    stmt = delete(UserSearchHistory).where(
        UserSearchHistory.id == history_id,
        UserSearchHistory.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def clear_user_history(
    db: AsyncSession,
    user_id: uuid.UUID
) -> int:
    """清空用户全部搜索历史，返回删除条数"""
    stmt = delete(UserSearchHistory).where(UserSearchHistory.user_id == user_id)
    result = await db.execute(stmt)
    return result.rowcount


# ==================== 热门搜索查询 ====================

async def get_hot_keywords(
    db: AsyncSession,
    limit: int = 10,
    days: int = 7
) -> List[SearchKeywordStats]:
    """
    获取热门搜索词

    简单逻辑：最近 N 天内有搜索的词，按总搜索次数降序排列
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(SearchKeywordStats)
        .where(SearchKeywordStats.last_searched_at >= cutoff)
        .where(SearchKeywordStats.total_count >= 2)
        .order_by(SearchKeywordStats.total_count.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ==================== 搜索建议查询 ====================

async def get_suggestions(
    db: AsyncSession,
    keyword: str,
    limit: int = 10
) -> List[str]:
    """
    获取搜索建议（前缀匹配）

    优先级：热词表中以 keyword 开头的词，按搜索次数降序
    """
    keyword_norm = _normalize_keyword(keyword)
    if not keyword_norm:
        return []

    pattern = f"{keyword_norm}%"

    stmt = (
        select(SearchKeywordStats.keyword_norm)
        .where(SearchKeywordStats.keyword_norm.like(pattern))
        .where(SearchKeywordStats.keyword_norm != keyword_norm)
        .order_by(SearchKeywordStats.total_count.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


# ==================== 搜索推荐查询 ====================

async def get_recommendations(
    db: AsyncSession,
    keyword: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    limit: int = 8
) -> List[dict]:
    """
    获取搜索推荐
    - 有关键词: ILIKE包含匹配 + 个性化boost（用户历史+50分）
    - 无关键词: 返回全局热词
    """
    if keyword and keyword.strip():
        keyword_norm = _normalize_keyword(keyword)
        # 获取候选词（多取一些用于排序）
        stmt = (
            select(SearchKeywordStats)
            .where(SearchKeywordStats.keyword_norm.ilike(f"%{keyword_norm}%"))
            .order_by(SearchKeywordStats.total_count.desc())
            .limit(limit * 5)
        )
        result = await db.execute(stmt)
        candidates = list(result.scalars().all())

        # 个性化boost：查询用户历史
        user_history = set()
        if user_id:
            hist_stmt = (
                select(UserSearchHistory.keyword_norm)
                .where(UserSearchHistory.user_id == user_id)
                .order_by(UserSearchHistory.last_searched_at.desc())
                .limit(50)
            )
            hist_result = await db.execute(hist_stmt)
            user_history = {row[0] for row in hist_result.all()}

        # 计算得分并排序
        scored = []
        for item in candidates:
            base_score = float(item.total_count or 0)
            if item.keyword_norm in user_history:
                base_score += 50  # 历史匹配加分
            scored.append({
                'keyword': item.keyword or item.keyword_norm,
                'score': base_score
            })
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:limit]
    else:
        # 无关键词，返回全局热词
        stmt = (
            select(SearchKeywordStats)
            .order_by(SearchKeywordStats.total_count.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        return [
            {'keyword': item.keyword or item.keyword_norm, 'score': float(item.total_count or 0)}
            for item in items
        ]
