"""
用户行为模块 CRUD 层

包括：
- 用户收藏 (UserFavorite)
- 观看历史 (WatchHistory)
- 用户订阅提醒 (UserSubscription)

注意：
- 所有函数为 async def。
- 不在本层调用 commit()/rollback()，由 Service 层控制事务。
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, func, exists, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.user_behavior import (
    UserFavorite,
    WatchHistory,
    UserSubscription,
    SubscriptionTargetType,
)
from app.models.live_core import LiveRoom, LiveSession
from app.exceptions import DatabaseIntegrityException

logger = logging.getLogger(__name__)


def _subscription_public_where():
    """
    订阅记录的公开过滤条件（阶段3 P2）：仅统计/返回目标仍存在且公开（is_private=false）的订阅。

    因 target_id 为多态（room/session），需按 target_type 分支：
    - room 订阅：目标房间存在且公开
    - session 订阅：目标场次存在，且所属房间公开
    """
    room_exists = exists(
        select(1).select_from(LiveRoom).where(
            LiveRoom.id == UserSubscription.target_id,
            LiveRoom.is_private.is_(False),
        )
    )
    session_exists = exists(
        select(1)
        .select_from(LiveSession)
        .join(LiveRoom, LiveSession.room_id == LiveRoom.id)
        .where(
            LiveSession.id == UserSubscription.target_id,
            LiveRoom.is_private.is_(False),
        )
    )
    return or_(
        and_(UserSubscription.target_type == SubscriptionTargetType.ROOM, room_exists),
        and_(UserSubscription.target_type == SubscriptionTargetType.SESSION, session_exists),
    )


# ==================== 用户收藏相关 ====================


async def create_favorite(
    db: AsyncSession,
    user_id: UUID,
    room_id: UUID,
) -> UserFavorite:
    """
    创建用户收藏记录。

    行为：
    - 如果已存在 is_active=True 的记录，抛出 DatabaseIntegrityException("收藏已存在")
    - 如果存在 is_active=False 的记录，则恢复为 True 并返回该记录
    - 否则插入新记录（is_active=True）
    """
    # 先查询是否已有记录
    stmt = select(UserFavorite).where(
        UserFavorite.user_id == user_id,
        UserFavorite.room_id == room_id,
    )
    result = await db.execute(stmt)
    favorite = result.scalar_one_or_none()

    if favorite:
        if favorite.is_active:
            logger.warning(
                "创建收藏失败，记录已存在: user_id=%s, room_id=%s, favorite_id=%s",
                str(user_id)[:8],
                str(room_id)[:8],
                str(favorite.id)[:8],
            )
            raise DatabaseIntegrityException("收藏已存在")
        # 恢复软删除的记录
        favorite.is_active = True
        await db.flush()
        await db.refresh(favorite)
        logger.info(
            "恢复收藏成功: user_id=%s, room_id=%s, favorite_id=%s",
            str(user_id)[:8],
            str(room_id)[:8],
            str(favorite.id)[:8],
        )
        return favorite

    # 新建记录
    new_fav = UserFavorite(user_id=user_id, room_id=room_id, is_active=True)
    db.add(new_fav)
    try:
        await db.flush()
        await db.refresh(new_fav)
        logger.info(
            "创建收藏成功: user_id=%s, room_id=%s, favorite_id=%s",
            str(user_id)[:8],
            str(room_id)[:8],
            str(new_fav.id)[:8],
        )
        return new_fav
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            "创建收藏失败（唯一性约束）: user_id=%s, room_id=%s, error=%s",
            str(user_id)[:8],
            str(room_id)[:8],
            str(e),
        )
        raise DatabaseIntegrityException("收藏已存在") from e


async def get_favorite(
    db: AsyncSession,
    user_id: UUID,
    room_id: UUID,
) -> Optional[UserFavorite]:
    """根据 user_id 和 room_id 获取收藏记录（无论 is_active 状态）。"""
    stmt = select(UserFavorite).where(
        UserFavorite.user_id == user_id,
        UserFavorite.room_id == room_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_favorites_count(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """获取指定用户收藏总数（is_active=True；2026-08-11 起含私密房——收藏=受邀者主动再进入口，决策 D5）。"""
    stmt = (
        select(func.count())
        .select_from(UserFavorite)
        .join(LiveRoom, UserFavorite.room_id == LiveRoom.id)
        .where(
            UserFavorite.user_id == user_id,
            UserFavorite.is_active.is_(True),
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_user_favorites(
    db: AsyncSession,
    user_id: UUID,
    offset: int = 0,
    limit: int = 10,
) -> List[UserFavorite]:
    """获取指定用户的收藏列表（分页），返回 is_active=True 的记录（2026-08-11 起含私密房），按创建时间倒序。"""
    stmt = (
        select(UserFavorite)
        .join(LiveRoom, UserFavorite.room_id == LiveRoom.id)
        .where(
            UserFavorite.user_id == user_id,
            UserFavorite.is_active.is_(True),
        )
        .order_by(UserFavorite.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    favorites = result.scalars().all()
    logger.info(
        "查询用户收藏列表: user_id=%s, offset=%d, limit=%d, count=%d",
        str(user_id)[:8],
        offset,
        limit,
        len(favorites),
    )
    return favorites


async def delete_favorite(
    db: AsyncSession,
    user_id: UUID,
    room_id: UUID,
) -> bool:
    """
    取消收藏：
    - 如果存在 is_active=True 的记录，将 is_active 置为 False
    - 如果不存在记录，返回 False
    - 不执行 commit，由 Service 层负责提交事务
    """
    stmt = (
        select(UserFavorite)
        .where(
            UserFavorite.user_id == user_id,
            UserFavorite.room_id == room_id,
            UserFavorite.is_active.is_(True),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    favorite = result.scalar_one_or_none()
    if not favorite:
        logger.info(
            "取消收藏：记录不存在或已取消，无需更新 user_id=%s, room_id=%s",
            str(user_id)[:8],
            str(room_id)[:8],
        )
        return False

    favorite.is_active = False
    await db.flush()
    logger.info(
        "取消收藏成功: user_id=%s, room_id=%s, favorite_id=%s",
        str(user_id)[:8],
        str(room_id)[:8],
        str(favorite.id)[:8],
    )
    return True


# ==================== 观看历史相关 ====================


async def record_watch_history(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    progress: Optional[int] = None,
) -> WatchHistory:
    """
    记录或更新观看历史：
    - 将之前的 is_latest=True 记录置为 False
    - 插入新的 is_latest=True 记录
    """
    try:
        # 将旧记录标记为非最新
        await db.execute(
            update(WatchHistory)
            .where(
                WatchHistory.user_id == user_id,
                WatchHistory.session_id == session_id,
                WatchHistory.is_latest.is_(True),
            )
            .values(is_latest=False)
        )

        history = WatchHistory(
            user_id=user_id,
            session_id=session_id,
            progress=progress,
        )
        db.add(history)
        await db.flush()
        await db.refresh(history)
        logger.info(
            "记录观看历史: user_id=%s, session_id=%s, history_id=%s, progress=%s",
            str(user_id)[:8],
            str(session_id)[:8],
            str(history.id)[:8],
            progress,
        )
        return history
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            "记录观看历史失败（外键约束或唯一性约束）: user_id=%s, session_id=%s, error=%s",
            str(user_id)[:8],
            str(session_id)[:8],
            str(e),
        )
        raise DatabaseIntegrityException("记录观看历史失败") from e
    except Exception as e:
        await db.rollback()
        logger.error(
            "记录观看历史失败（数据库错误）: user_id=%s, session_id=%s, error=%s",
            str(user_id)[:8],
            str(session_id)[:8],
            str(e),
        )
        raise


async def count_watch_history(db: AsyncSession, user_id: UUID) -> int:
    """获取用户观看历史总数（is_latest=True，仅统计所属房间公开的场次）。"""
    stmt = (
        select(func.count())
        .select_from(WatchHistory)
        .join(LiveSession, WatchHistory.session_id == LiveSession.id)
        .join(LiveRoom, LiveSession.room_id == LiveRoom.id)
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.is_latest.is_(True),
            LiveRoom.is_private.is_(False),
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def list_watch_history(
    db: AsyncSession,
    user_id: UUID,
    offset: int = 0,
    limit: int = 20,
) -> List[WatchHistory]:
    """获取用户观看历史（分页，只返回 is_latest=True 且所属房间公开的记录），按 watched_at 降序。"""
    stmt = (
        select(WatchHistory)
        .join(LiveSession, WatchHistory.session_id == LiveSession.id)
        .join(LiveRoom, LiveSession.room_id == LiveRoom.id)
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.is_latest.is_(True),
            LiveRoom.is_private.is_(False),
        )
        .order_by(WatchHistory.watched_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    logger.info(
        "查询观看历史: user_id=%s, offset=%d, limit=%d, count=%d",
        str(user_id)[:8],
        offset,
        limit,
        len(items),
    )
    return items


async def delete_watch_history_by_id(
    db: AsyncSession,
    history_id: UUID,
    user_id: UUID,
) -> bool:
    """
    按 history_id + user_id 硬删除单条观看历史。
    若记录不存在或 user_id 不匹配，返回 False；删除成功返回 True。
    不执行 commit，由 Service 层负责。
    """
    stmt = select(WatchHistory).where(
        WatchHistory.id == history_id,
        WatchHistory.user_id == user_id,
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        logger.info(
            "删除观看历史：记录不存在或非本人 user_id=%s, history_id=%s",
            str(user_id)[:8],
            str(history_id)[:8],
        )
        return False
    await db.delete(row)
    await db.flush()
    logger.info(
        "删除观看历史成功: user_id=%s, history_id=%s",
        str(user_id)[:8],
        str(history_id)[:8],
    )
    return True


# ==================== 订阅提醒相关 ====================


async def create_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    target_id: UUID,
) -> UserSubscription:
    """
    创建订阅记录。

    - 根据 (user_id, target_id, target_type) 唯一约束防止重复订阅。
    - 如果存在 is_active=False 的记录，可以恢复为 True。
    """
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == user_id,
        UserSubscription.target_type == target_type,
        UserSubscription.target_id == target_id,
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()

    if sub:
        if sub.is_active:
            logger.warning(
                "创建订阅失败，记录已存在: user_id=%s, target_type=%s, target_id=%s, sub_id=%s",
                str(user_id)[:8],
                target_type.value,
                str(target_id)[:8],
                str(sub.id)[:8],
            )
            raise DatabaseIntegrityException("订阅已存在")
        # 恢复软删除
        sub.is_active = True
        await db.flush()
        await db.refresh(sub)
        logger.info(
            "恢复订阅成功: user_id=%s, target_type=%s, target_id=%s, sub_id=%s",
            str(user_id)[:8],
            target_type.value,
            str(target_id)[:8],
            str(sub.id)[:8],
        )
        return sub

    new_sub = UserSubscription(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        is_active=True,
    )
    db.add(new_sub)
    try:
        await db.flush()
        await db.refresh(new_sub)
        logger.info(
            "创建订阅成功: user_id=%s, target_type=%s, target_id=%s, sub_id=%s",
            str(user_id)[:8],
            target_type.value,
            str(target_id)[:8],
            str(new_sub.id)[:8],
        )
        return new_sub
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            "创建订阅失败（唯一性约束）: user_id=%s, target_type=%s, target_id=%s, error=%s",
            str(user_id)[:8],
            target_type.value,
            str(target_id)[:8],
            str(e),
        )
        raise DatabaseIntegrityException("订阅已存在") from e


async def get_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    target_id: UUID,
) -> Optional[UserSubscription]:
    """根据 user_id + 目标条件获取单条订阅记录（无论 is_active 状态）。"""
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == user_id,
        UserSubscription.target_type == target_type,
        UserSubscription.target_id == target_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def count_subscriptions(
    db: AsyncSession,
    user_id: UUID,
    target_type: Optional[SubscriptionTargetType] = None,
    only_active: bool = True,
) -> int:
    """获取用户订阅总数，可按 target_type 过滤；仅统计目标仍存在且公开的订阅。"""
    stmt = select(func.count()).select_from(UserSubscription).where(
        UserSubscription.user_id == user_id
    )
    if target_type is not None:
        stmt = stmt.where(UserSubscription.target_type == target_type)
    if only_active:
        stmt = stmt.where(UserSubscription.is_active.is_(True))
    stmt = stmt.where(_subscription_public_where())
    result = await db.execute(stmt)
    return result.scalar() or 0


async def list_subscriptions(
    db: AsyncSession,
    user_id: UUID,
    target_type: Optional[SubscriptionTargetType] = None,
    only_active: bool = True,
    offset: int = 0,
    limit: int = 10,
) -> List[UserSubscription]:
    """获取用户的订阅列表（分页），可按 target_type 过滤；仅返回目标仍存在且公开的订阅。"""
    stmt = select(UserSubscription).where(UserSubscription.user_id == user_id)
    if target_type is not None:
        stmt = stmt.where(UserSubscription.target_type == target_type)
    if only_active:
        stmt = stmt.where(UserSubscription.is_active.is_(True))
    stmt = stmt.where(_subscription_public_where())
    stmt = stmt.order_by(UserSubscription.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    subs = result.scalars().all()
    logger.info(
        "查询订阅列表: user_id=%s, target_type=%s, offset=%d, limit=%d, count=%d",
        str(user_id)[:8],
        target_type,
        offset,
        limit,
        len(subs),
    )
    return subs


async def cancel_subscription(
    db: AsyncSession,
    user_id: UUID,
    target_type: SubscriptionTargetType,
    target_id: UUID,
) -> bool:
    """
    取消订阅：
    - 匹配 user_id + target_type + target_id
    - 如果存在 is_active=True 的记录，将 is_active 置为 False
    - 如果不存在记录，返回 False
    """
    stmt = (
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.target_type == target_type,
            UserSubscription.target_id == target_id,
            UserSubscription.is_active.is_(True),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        logger.info(
            "取消订阅：记录不存在或已取消 user_id=%s, target_type=%s, target_id=%s",
            str(user_id)[:8],
            target_type.value,
            str(target_id)[:8],
        )
        return False

    sub.is_active = False
    await db.flush()
    logger.info(
        "取消订阅成功: user_id=%s, target_type=%s, target_id=%s, sub_id=%s",
        str(user_id)[:8],
        target_type.value,
        str(target_id)[:8],
        str(sub.id)[:8],
    )
    return True

