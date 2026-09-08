"""账号注销后 live_core 私货清理与身份解绑（16-D2）"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deactivated_users import mark_user_deactivated
from app.core.redis_cache import invalidate_all_message_caches
from app.models.experts import Expert, UserExpertSubscription
from app.models.search import UserSearchHistory
from app.models.user_behavior import UserFavorite, UserSubscription, WatchHistory
from app.models.user_preference_notification import Notification, UserPreferences

logger = logging.getLogger(__name__)


class DeactivateCleanupService:
    """按 public_id 清私货、解绑 Admin 专家绑定，并写已注销标记。幂等。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, user_public_id: uuid.UUID) -> Dict[str, Any]:
        # 最先写标记，便于 D3 尽快生效
        await mark_user_deactivated(user_public_id)
        # 清留言列表缓存，避免缓存里仍是注销前快照昵称
        await invalidate_all_message_caches()

        deleted_counts: Dict[str, Any] = {}

        # 解绑 Admin 绑定的 experts.user_id（专家页主体保留）
        expert_result = await self.db.execute(
            update(Expert)
            .where(Expert.user_id == user_public_id)
            .values(user_id=None)
        )
        unbound_experts = expert_result.rowcount or 0

        # 收藏 / 内容订阅：软藏
        fav_result = await self.db.execute(
            update(UserFavorite)
            .where(
                UserFavorite.user_id == user_public_id,
                UserFavorite.is_active.is_(True),
            )
            .values(is_active=False)
        )
        deleted_counts["user_favorites"] = fav_result.rowcount or 0

        sub_result = await self.db.execute(
            update(UserSubscription)
            .where(
                UserSubscription.user_id == user_public_id,
                UserSubscription.is_active.is_(True),
            )
            .values(is_active=False)
        )
        deleted_counts["user_subscriptions"] = sub_result.rowcount or 0

        # 其余：物理删
        for key, model in (
            ("watch_history", WatchHistory),
            ("user_expert_subscriptions", UserExpertSubscription),
            ("user_preferences", UserPreferences),
            ("notifications", Notification),
            ("user_search_history", UserSearchHistory),
        ):
            result = await self.db.execute(
                delete(model).where(model.user_id == user_public_id)
            )
            deleted_counts[key] = result.rowcount or 0

        await self.db.commit()

        logger.info(
            "deactivate-cleanup 完成 user=%s unbound_experts=%s counts=%s",
            user_public_id,
            unbound_experts,
            deleted_counts,
        )
        return {
            "user_public_id": str(user_public_id),
            "deleted_counts": deleted_counts,
            "unbound_experts": unbound_experts,
            # 兼容旧响应字段；品牌成员能力已废弃
            "removed_brand_members": 0,
        }
