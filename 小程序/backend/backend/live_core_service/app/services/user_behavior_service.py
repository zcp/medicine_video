import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.crud import user_behavior as crud_user_behavior
from app.schemas.user_behavior import (
    FavoriteCreate,
    FavoriteItem,
    FavoriteListResponse,
    WatchEventRequest,
    WatchHistoryItem,
    WatchHistoryListResponse,
    SubscriptionTargetType,
    SubscriptionCreate,
    SubscriptionItem,
    SubscriptionListResponse,
)
from app.exceptions import (
    InvalidParameterException,
    DatabaseIntegrityException,
    NotFoundException,
)


class UserBehaviorService:
    """用户行为模块 Service 层：收藏、观看历史、订阅提醒。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # ================ 收藏相关 =================

    async def add_favorite(self, current_user_id: UUID, room_id: UUID) -> FavoriteItem:
        try:
            self.logger.info(f"[Service] 开始创建收藏: user_id={str(current_user_id)[:8]}, room_id={str(room_id)[:8]}")
            fav = await crud_user_behavior.create_favorite(self.db, current_user_id, room_id)
            self.logger.info(f"[Service] CRUD 返回对象: type={type(fav).__name__}, id={str(fav.id)[:8]}")
            # 🚨 必须在 commit() 前进行 model_validate，否则 ORM 对象变成 detached 状态
            # 会触发 Pydantic 的 greenlet 错误
            self.logger.info(f"[Service] 开始 model_validate...")
            result = FavoriteItem.model_validate(fav)
            self.logger.info(f"[Service] model_validate 成功: {result}")
            self.logger.info(f"[Service] 开始 commit...")
            await self.db.commit()
            self.logger.info(f"[Service] commit 成功")
        except DatabaseIntegrityException as e:
            await self.db.rollback()
            raise InvalidParameterException("已收藏该直播间") from e
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            self.logger.error(
                "创建收藏失败: user_id=%s, room_id=%s, error=%s",
                str(current_user_id)[:8],
                str(room_id)[:8],
                e,
            )
            raise
        return result

    async def remove_favorite(self, current_user_id: UUID, room_id: UUID) -> None:
        try:
            await crud_user_behavior.delete_favorite(self.db, current_user_id, room_id)
            await self.db.commit()
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            self.logger.error(
                "取消收藏失败: user_id=%s, room_id=%s, error=%s",
                str(current_user_id)[:8],
                str(room_id)[:8],
                e,
            )
            raise

    async def get_favorites(
        self,
        current_user_id: UUID,
        page: int = 1,
        size: int = 10,
    ) -> FavoriteListResponse:
        total = await crud_user_behavior.get_user_favorites_count(self.db, current_user_id)
        offset = (page - 1) * size
        favorites = await crud_user_behavior.get_user_favorites(
            self.db, current_user_id, offset=offset, limit=size
        )
        items: List[FavoriteItem] = [FavoriteItem.model_validate(f) for f in favorites]
        return FavoriteListResponse(total=total, page=page, size=size, items=items)

    async def check_is_favorited(self, room_id: UUID, current_user_id: UUID) -> Dict[str, bool]:
        """
        检查当前用户是否已收藏指定直播间。
        若直播间不存在则抛出 NotFoundException。
        """
        room = await crud_room.get(self.db, room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        favorite = await crud_user_behavior.get_favorite(self.db, current_user_id, room_id)
        is_favorited = favorite is not None and favorite.is_active
        self.logger.debug(
            "检查收藏状态: user_id=%s, room_id=%s, is_favorited=%s",
            str(current_user_id)[:8],
            str(room_id)[:8],
            is_favorited,
        )
        return {"is_favorited": is_favorited}

    # ================ 观看历史相关 =================

    async def record_watch_event(
        self,
        current_user_id: UUID,
        watch_event: WatchEventRequest,
    ) -> WatchHistoryItem:
        try:
            history = await crud_user_behavior.record_watch_history(
                self.db,
                user_id=current_user_id,
                session_id=watch_event.session_id,
                progress=watch_event.progress,
            )
            # 🚨 必须在 commit() 前进行 model_validate，否则 ORM 对象变成 detached 状态
            result = WatchHistoryItem.model_validate(history)
            await self.db.commit()
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            self.logger.error(
                "记录观看历史失败: user_id=%s, session_id=%s, error=%s",
                str(current_user_id)[:8],
                str(watch_event.session_id)[:8],
                e,
            )
            raise
        return result

    async def get_watch_history(
        self,
        current_user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> WatchHistoryListResponse:
        total = await crud_user_behavior.count_watch_history(self.db, current_user_id)
        offset = (page - 1) * size
        records = await crud_user_behavior.list_watch_history(
            self.db, current_user_id, offset=offset, limit=size
        )
        items: List[WatchHistoryItem] = [WatchHistoryItem.model_validate(r) for r in records]
        return WatchHistoryListResponse(total=total, page=page, size=size, items=items)

    async def delete_watch_history(
        self,
        current_user_id: UUID,
        history_id: UUID,
    ) -> None:
        """删除单条观看历史（硬删除）。记录不存在或非本人则抛出 NotFoundException。"""
        deleted = await crud_user_behavior.delete_watch_history_by_id(
            self.db, history_id, current_user_id
        )
        if not deleted:
            raise NotFoundException("观看历史记录不存在或无权删除")
        try:
            await self.db.commit()
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            self.logger.error(
                "删除观看历史失败: user_id=%s, history_id=%s, error=%s",
                str(current_user_id)[:8],
                str(history_id)[:8],
                e,
            )
            raise

    # ================ 订阅提醒相关 =================

    async def create_subscription(
        self,
        current_user_id: UUID,
        sub_in: SubscriptionCreate,
    ) -> SubscriptionItem:
        # 基本参数校验：根据 target_type 验证 target_id 对应的资源是否存在
        # 注意：target_id 的验证在 Service 层完成，不在 Schema 层

        # 基本参数校验：根据 target_type 验证 target_id 对应的资源是否存在
        # 注意：target_id 的验证在 Service 层完成，不在 Schema 层
        from app.crud import room as crud_room, session as crud_session
        from app.exceptions import NotFoundException

        # 验证target_id对应的资源是否存在
        if sub_in.target_type == SubscriptionTargetType.ROOM:
            room_obj = await crud_room.get(self.db, sub_in.target_id)
            if not room_obj:
                raise NotFoundException(f"房间不存在: {sub_in.target_id}")
        elif sub_in.target_type == SubscriptionTargetType.SESSION:
            session_obj = await crud_session.get(self.db, sub_in.target_id)
            if not session_obj:
                raise NotFoundException(f"场次不存在: {sub_in.target_id}")
        try:
            sub = await crud_user_behavior.create_subscription(
                self.db,
                user_id=current_user_id,
                target_type=sub_in.target_type,
                target_id=sub_in.target_id,
            )
            # 🚨 必须在 commit() 前进行 model_validate，否则 ORM 对象变成 detached 状态
            result = SubscriptionItem.model_validate(sub)
            await self.db.commit()
        except DatabaseIntegrityException as e:
            await self.db.rollback()
            raise InvalidParameterException("订阅已存在") from e
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            self.logger.error(
                "创建订阅失败: user_id=%s, target_type=%s, target_id=%s, error=%s",
                str(current_user_id)[:8],
                sub_in.target_type.value,
                str(sub_in.target_id)[:8],
                e,
            )
            raise
        return result

    async def cancel_subscription(
        self,
        current_user_id: UUID,
        target_type: SubscriptionTargetType,
        target_id: UUID,
    ) -> None:
        try:
            await crud_user_behavior.cancel_subscription(
                self.db,
                user_id=current_user_id,
                target_type=target_type,
                target_id=target_id,
            )
            await self.db.commit()
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            self.logger.error(
                "取消订阅失败: user_id=%s, target_type=%s, target_id=%s, error=%s",
                str(current_user_id)[:8],
                target_type.value,
                str(target_id)[:8],
                e,
            )
            raise

    async def get_subscriptions(
        self,
        current_user_id: UUID,
        target_type: Optional[SubscriptionTargetType] = None,
        page: int = 1,
        size: int = 10,
    ) -> SubscriptionListResponse:
        total = await crud_user_behavior.count_subscriptions(
            self.db,
            user_id=current_user_id,
            target_type=target_type,
            only_active=True,
        )
        offset = (page - 1) * size
        subs = await crud_user_behavior.list_subscriptions(
            self.db,
            user_id=current_user_id,
            target_type=target_type,
            only_active=True,
            offset=offset,
            limit=size,
        )
        items: List[SubscriptionItem] = [SubscriptionItem.model_validate(s) for s in subs]
        return SubscriptionListResponse(total=total, page=page, size=size, items=items)

