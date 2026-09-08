import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.crud import user_behavior as crud_user_behavior
from app.crud import session as crud_session
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
from app.services.room_card_service import (
    get_room_card_map,
    get_session_card_map,
    ROOM_CARD_FIELDS,
    SESSION_CARD_FIELDS,
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
            fav = await crud_user_behavior.create_favorite(self.db, current_user_id, room_id)
            result = FavoriteItem.model_validate(fav)
            await self.db.commit()
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
        # 批量聚合卡片字段，避免前端逐条 N+1（无专家时主展示人回退为创建者）
        card_map = await get_room_card_map(
            self.db, [f.room_id for f in favorites], include_owner=True
        )
        items: List[FavoriteItem] = []
        for f in favorites:
            # 竞态兜底：若 count 与 list 之间房间被删/转私密，card_map 查不到，跳过该条
            if f.room_id not in card_map:
                self.logger.info("收藏卡片聚合缺失，跳过（房间可能已删除/私密）: room_id=%s", f.room_id)
                continue
            base = FavoriteItem.model_validate(f)
            merged = base.model_dump()
            card = card_map.get(f.room_id) or {}
            merged.update({k: card[k] for k in ROOM_CARD_FIELDS if card.get(k) is not None})
            items.append(FavoriteItem(**merged))
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
        # 批量聚合卡片字段，避免前端逐条 N+1
        card_map = await get_session_card_map(self.db, [r.session_id for r in records])
        items: List[WatchHistoryItem] = []
        for r in records:
            # 竞态兜底：若 count 与 list 之间场次/所属房间被删或转私密，card_map 查不到，跳过该条
            if r.session_id not in card_map:
                self.logger.info("历史卡片聚合缺失，跳过（场次可能已删除/房间私密）: session_id=%s", r.session_id)
                continue
            base = WatchHistoryItem.model_validate(r)
            merged = base.model_dump()
            card = card_map.get(r.session_id) or {}
            merged.update({k: card[k] for k in SESSION_CARD_FIELDS if card.get(k) is not None})
            items.append(WatchHistoryItem(**merged))
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
        # 验证 target_id 对应的资源是否存在
        if sub_in.target_type == SubscriptionTargetType.ROOM:
            target_room = await crud_room.get(self.db, sub_in.target_id)
            if not target_room:
                raise NotFoundException(f"房间不存在: {sub_in.target_id}")
        elif sub_in.target_type == SubscriptionTargetType.SESSION:
            target_session = await crud_session.get(self.db, sub_in.target_id)
            if not target_session:
                raise NotFoundException(f"场次不存在: {sub_in.target_id}")
        try:
            sub = await crud_user_behavior.create_subscription(
                self.db,
                user_id=current_user_id,
                target_type=sub_in.target_type,
                target_id=sub_in.target_id,
            )
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
        # 按目标类型分流，批量聚合卡片字段，避免前端逐条 N+1
        room_ids = [s.target_id for s in subs if s.target_type == SubscriptionTargetType.ROOM]
        session_ids = [s.target_id for s in subs if s.target_type == SubscriptionTargetType.SESSION]
        room_card_map = await get_room_card_map(self.db, room_ids, include_owner=True)
        session_card_map = await get_session_card_map(self.db, session_ids)

        items: List[SubscriptionItem] = []
        for s in subs:
            # 竞态兜底：若 count 与 list 之间目标被删/转私密，对应 card_map 查不到，跳过该条
            if s.target_type == SubscriptionTargetType.ROOM:
                if s.target_id not in room_card_map:
                    self.logger.info("订阅卡片聚合缺失，跳过（房间可能已删除/私密）: target_id=%s", s.target_id)
                    continue
            elif s.target_id not in session_card_map:
                self.logger.info("订阅卡片聚合缺失，跳过（场次可能已删除/房间私密）: target_id=%s", s.target_id)
                continue
            base = SubscriptionItem.model_validate(s)
            merged = base.model_dump()
            if s.target_type == SubscriptionTargetType.ROOM:
                card = room_card_map.get(s.target_id) or {}
                fields = {
                    "room_title": card.get("room_title"),
                    "room_cover_url": card.get("room_cover_url"),
                    "title": card.get("room_title"),
                    "cover_url": card.get("room_cover_url"),
                    "status": card.get("room_live_status"),
                    "expert_name": card.get("expert_name"),
                    "expert_avatar": card.get("expert_avatar"),
                    "expert_title": card.get("expert_title"),
                    "expert_hospital": card.get("expert_hospital"),
                }
            else:
                card = session_card_map.get(s.target_id) or {}
                fields = {k: card.get(k) for k in SESSION_CARD_FIELDS}
            merged.update({k: v for k, v in fields.items() if v is not None})
            items.append(SubscriptionItem(**merged))
        return SubscriptionListResponse(total=total, page=page, size=size, items=items)

    async def check_is_subscribed(
        self,
        target_type: SubscriptionTargetType,
        target_id: UUID,
        current_user_id: UUID,
    ) -> Dict[str, bool]:
        """
        检查当前用户是否已订阅指定房间或场次。

        设计对齐 check_is_favorited()：
        1. 先验证 target 资源存在性 → 不存在抛 NotFoundException
        2. 再查订阅记录（复用已有的 get_subscription）
        3. 返回 {"is_subscribed": bool}

        Args:
            target_type: 订阅目标类型（room 或 session）
            target_id: 目标ID（live_rooms.id 或 live_sessions.id）
            current_user_id: 当前用户 public_id

        Returns:
            {"is_subscribed": True/False}

        Raises:
            NotFoundException: 目标资源不存在
        """
        # 1. 资源存在性校验
        if target_type == SubscriptionTargetType.ROOM:
            target_room = await crud_room.get(self.db, target_id)
            if target_room is None:
                raise NotFoundException(f"房间不存在: {target_id}")
        elif target_type == SubscriptionTargetType.SESSION:
            target_session = await crud_session.get(self.db, target_id)
            if target_session is None:
                raise NotFoundException(f"场次不存在: {target_id}")

        # 2. 查询订阅记录（复用已有的 CRUD 函数）
        sub = await crud_user_behavior.get_subscription(
            self.db, current_user_id, target_type, target_id
        )
        is_subscribed = sub is not None and sub.is_active

        self.logger.debug(
            "检查订阅状态: user_id=%s, target_type=%s, target_id=%s, is_subscribed=%s",
            str(current_user_id)[:8],
            target_type.value,
            str(target_id)[:8],
            is_subscribed,
        )
        return {"is_subscribed": is_subscribed}

