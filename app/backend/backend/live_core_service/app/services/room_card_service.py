"""
直播间卡片聚合服务（阶段3 P2）

为「我的收藏 / 我的订阅 / 观看历史」三个列表批量组装卡片展示字段，
避免前端逐条 N+1 请求，并将前端随机 Mock 数据替换为真实数据或空值。

核心约定：
- 字段命名与前端展示字段对齐（room_title/room_cover_url/expert_name/expert_avatar/duration/view_count/comment_count 等）
- 代表场次：每个房间取 created_at DESC, id DESC 的最新一场（LATERAL，禁止普通 JOIN 造成多行）
- 第一专家：按 sort_order ASC, created_at ASC, id ASC 取关联顺序第一条（与首页规则一致）
- 创建者信息：批量 fetch_user_profiles，失败降级 name="用户"、avatar_url=None
- 统计字段：view_count = total_viewer_count（缺失退 peak_viewer_count）；comment_count 无真实来源恒为 None
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_profile_client import fetch_user_profiles

logger = logging.getLogger(__name__)

# 房间卡片字段（FavoriteItem 卡片子集，键名与 Schema 字段名对齐）
ROOM_CARD_FIELDS = (
    "room_title",
    "room_cover_url",
    "room_live_status",
    "expert_name",
    "expert_avatar",
    "expert_title",
    "expert_hospital",
    "duration",
    "view_count",
    "comment_count",
)

# 场次卡片字段（WatchHistoryItem 卡片子集，键名与 Schema 字段名对齐）
SESSION_CARD_FIELDS = (
    "room_id",
    "room_title",
    "room_cover_url",
    "title",
    "session_title",
    "cover_url",
    "status",
    "expert_name",
    "expert_avatar",
    "expert_title",
    "expert_hospital",
    "duration",
    "view_count",
    "comment_count",
)

_ROOM_CARD_SQL = """
    SELECT
        lr.id AS room_id,
        lr.title AS room_title,
        lr.cover_url AS room_cover_url,
        lr.user_id AS room_owner_user_id,
        ls.id AS session_id,
        ls.status AS session_status,
        CASE
            WHEN ls.end_time IS NOT NULL AND ls.start_time IS NOT NULL
            THEN EXTRACT(EPOCH FROM (ls.end_time - ls.start_time))::INTEGER
            ELSE NULL
        END AS duration,
        ss.total_viewer_count,
        ss.peak_viewer_count,
        e.name AS expert_name,
        e.title AS expert_title,
        e.hospital AS expert_hospital,
        e.avatar_url AS expert_avatar
    FROM live_rooms lr
    LEFT JOIN LATERAL (
        SELECT ls2.id, ls2.status, ls2.start_time, ls2.end_time
        FROM live_sessions ls2
        WHERE ls2.room_id = lr.id
        ORDER BY ls2.created_at DESC, ls2.id DESC
        LIMIT 1
    ) ls ON TRUE
    LEFT JOIN LATERAL (
        SELECT lse.expert_id
        FROM live_session_experts lse
        WHERE lse.session_id = ls.id
        ORDER BY lse.sort_order ASC, lse.created_at ASC, lse.id ASC
        LIMIT 1
    ) lse ON TRUE
    LEFT JOIN experts e ON lse.expert_id = e.id
    LEFT JOIN session_statistics ss ON ls.id = ss.session_id
    WHERE lr.id IN ({placeholders})
"""

_SESSION_CARD_SQL = """
    SELECT
        ls.id AS session_id,
        ls.room_id,
        ls.status AS session_status,
        lr.title AS room_title,
        lr.cover_url AS room_cover_url,
        lr.user_id AS room_owner_user_id,
        CASE
            WHEN ls.end_time IS NOT NULL AND ls.start_time IS NOT NULL
            THEN EXTRACT(EPOCH FROM (ls.end_time - ls.start_time))::INTEGER
            ELSE NULL
        END AS duration,
        ss.total_viewer_count,
        ss.peak_viewer_count,
        e.name AS expert_name,
        e.title AS expert_title,
        e.hospital AS expert_hospital,
        e.avatar_url AS expert_avatar
    FROM live_sessions ls
    JOIN live_rooms lr ON ls.room_id = lr.id
    LEFT JOIN LATERAL (
        SELECT lse.expert_id
        FROM live_session_experts lse
        WHERE lse.session_id = ls.id
        ORDER BY lse.sort_order ASC, lse.created_at ASC, lse.id ASC
        LIMIT 1
    ) lse ON TRUE
    LEFT JOIN experts e ON lse.expert_id = e.id
    LEFT JOIN session_statistics ss ON ls.id = ss.session_id
    WHERE ls.id IN ({placeholders})
"""


def _uuid_placeholders(ids: List[UUID]) -> str:
    """生成参数绑定的 IN 占位符（:rid0, :rid1, ...）。"""
    return ", ".join(f":rid{i}" for i in range(len(ids)))


def _uuid_params(ids: List[UUID]) -> Dict[str, str]:
    """生成与 _uuid_placeholders 对应的参数映射（key=ridN, value=str(UUID)）。"""
    return {f"rid{idx}": str(i) for idx, i in enumerate(ids)}


async def get_room_card_map(
    db: AsyncSession,
    room_ids: List[UUID],
    include_owner: bool = True,
) -> Dict[UUID, Dict[str, Any]]:
    """
    批量获取房间卡片字段。

    Args:
        db: 数据库会话
        room_ids: 房间ID列表（可为空）
        include_owner: 是否附带创建者信息（user_name/user_avatar_url）

    Returns:
        key 为房间ID；value 键与列表 Schema 卡片字段对齐，
        额外包含 user_name/user_avatar_url（include_owner=True 时）。
    """
    result_map: Dict[UUID, Dict[str, Any]] = {}
    if not room_ids:
        return result_map

    sql = text(_ROOM_CARD_SQL.format(placeholders=_uuid_placeholders(room_ids)))
    rows = (await db.execute(sql, _uuid_params(room_ids))).mappings().all()
    logger.info("批量查询房间卡片: room_ids=%d, rows=%d", len(room_ids), len(rows))

    owner_ids = set()
    for row in rows:
        duration = row["duration"]
        result_map[row["room_id"]] = {
            "room_title": row["room_title"],
            "room_cover_url": row["room_cover_url"],
            # 房间无独立状态列，直播状态取代表场次状态
            "room_live_status": row["session_status"],
            "expert_name": row["expert_name"],
            "expert_avatar": row["expert_avatar"],
            "expert_title": row["expert_title"],
            "expert_hospital": row["expert_hospital"],
            "duration": int(duration) if duration is not None else None,
            "view_count": row["total_viewer_count"]
            if row["total_viewer_count"] is not None
            else row["peak_viewer_count"],
            "comment_count": None,
        }
        if include_owner:
            owner_id = row["room_owner_user_id"]
            result_map[row["room_id"]]["room_owner_user_id"] = owner_id
            if owner_id is not None:
                owner_ids.add(owner_id)

    if include_owner:
        profiles: Dict[str, Dict[str, Any]] = {}
        if owner_ids:
            try:
                profiles = (await fetch_user_profiles(list(owner_ids))) or {}
            except Exception as e:  # noqa: BLE001
                logger.warning("获取房间卡片创建者资料失败，使用兜底: %s", e)
        for card in result_map.values():
            owner_id = card.pop("room_owner_user_id", None)
            profile = profiles.get(str(owner_id)) or {}
            user_name = profile.get("nickname") or profile.get("username") or "用户"
            user_avatar_url = profile.get("avatar_url")
            card["user_name"] = user_name
            card["user_avatar_url"] = user_avatar_url
            # 无关联专家时，卡片主展示人回退为创建者（设计文档 4.1 正式口径）
            if not card.get("expert_name"):
                card["expert_name"] = user_name
                card["expert_avatar"] = user_avatar_url

    return result_map


async def get_session_card_map(
    db: AsyncSession,
    session_ids: List[UUID],
) -> Dict[UUID, Dict[str, Any]]:
    """
    批量获取场次卡片字段（含所属房间信息与第一专家）。

    Args:
        db: 数据库会话
        session_ids: 场次ID列表（可为空）

    Returns:
        key 为场次ID；value 键与列表 Schema 卡片字段对齐。
    """
    result_map: Dict[UUID, Dict[str, Any]] = {}
    if not session_ids:
        return result_map

    sql = text(_SESSION_CARD_SQL.format(placeholders=_uuid_placeholders(session_ids)))
    rows = (await db.execute(sql, _uuid_params(session_ids))).mappings().all()
    logger.info("批量查询场次卡片: session_ids=%d, rows=%d", len(session_ids), len(rows))

    owner_ids = set()
    session_owners: Dict[UUID, Any] = {}
    for row in rows:
        duration = row["duration"]
        result_map[row["session_id"]] = {
            "room_id": row["room_id"],
            "room_title": row["room_title"],
            "room_cover_url": row["room_cover_url"],
            # 场次无独立标题，统一取房间标题
            "title": row["room_title"],
            "session_title": row["room_title"],
            "cover_url": row["room_cover_url"],
            "status": row["session_status"],
            "expert_name": row["expert_name"],
            "expert_avatar": row["expert_avatar"],
            "expert_title": row["expert_title"],
            "expert_hospital": row["expert_hospital"],
            "duration": int(duration) if duration is not None else None,
            "view_count": row["total_viewer_count"]
            if row["total_viewer_count"] is not None
            else row["peak_viewer_count"],
            "comment_count": None,
        }
        owner_id = row["room_owner_user_id"]
        if owner_id is not None:
            owner_ids.add(owner_id)
            session_owners[row["session_id"]] = owner_id

    # 无关联专家时，卡片主展示人回退为创建者（设计文档 4.1 正式口径）
    if owner_ids:
        profiles: Dict[str, Dict[str, Any]] = {}
        try:
            profiles = (await fetch_user_profiles(list(owner_ids))) or {}
        except Exception as e:  # noqa: BLE001
            logger.warning("获取场次卡片创建者资料失败，使用兜底: %s", e)
        for session_id, card in result_map.items():
            if card.get("expert_name"):
                continue
            owner_id = session_owners.get(session_id)
            profile = profiles.get(str(owner_id)) or {}
            user_name = profile.get("nickname") or profile.get("username") or "用户"
            user_avatar_url = profile.get("avatar_url")
            card["expert_name"] = user_name
            card["expert_avatar"] = user_avatar_url

    return result_map
