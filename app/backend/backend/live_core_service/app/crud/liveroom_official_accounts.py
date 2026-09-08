"""
直播间与公众号关联模块的 CRUD 层
负责 official_accounts、live_room_official_accounts 的数据访问
"""
from typing import List, Literal, Optional, Tuple
from uuid import UUID
import uuid as uuid_module
import logging

from sqlalchemy import select, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.liveroom_official_accounts import OfficialAccount, LiveRoomOfficialAccount
from app.models.live_core import LiveRoom
from app.schemas.liveroom_official_accounts import OfficialAccountCreate, OfficialAccountUpdate
from app.core.exceptions import DatabaseIntegrityException, DatabaseOperationException

logger = logging.getLogger(__name__)

OFFICIAL_ACCOUNT_LIST_SEARCH_FIELDS = ["name"]


async def get_paginated_official_accounts(
    db: AsyncSession,
    page: int,
    size: int,
    q: Optional[str] = None,
    search_type: Optional[str] = None,
    include_inactive: bool = False,
) -> Tuple[int, List[OfficialAccount]]:
    """分页获取公众号列表；WHERE 含 is_active、q/search_type（字符串搜索字段 name）。"""
    conditions = []
    if not include_inactive:
        conditions.append(OfficialAccount.is_active == True)
    if q and str(q).strip():
        q_clean = str(q).strip()
        if search_type == "id":
            try:
                conditions.append(OfficialAccount.id == UUID(q_clean))
            except (ValueError, TypeError):
                pass
        else:
            or_clauses = [
                getattr(OfficialAccount, f).ilike(f"%{q_clean}%")
                for f in OFFICIAL_ACCOUNT_LIST_SEARCH_FIELDS
                if hasattr(OfficialAccount, f)
            ]
            if or_clauses:
                conditions.append(or_(*or_clauses))

    query = select(OfficialAccount).order_by(OfficialAccount.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    return (total, list(items))


async def get_official_account_by_id(
    db: AsyncSession, account_id: UUID
) -> Optional[OfficialAccount]:
    """按 id 查单条公众号。"""
    query = select(OfficialAccount).where(OfficialAccount.id == account_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_official_account(
    db: AsyncSession, obj_in: OfficialAccountCreate
) -> OfficialAccount:
    """创建公众号；id 应用层生成。"""
    try:
        data = obj_in.model_dump()
        data["id"] = uuid_module.uuid4()
        account = OfficialAccount(**data)
        db.add(account)
        await db.flush()
        await db.refresh(account)
        logger.info(f"创建公众号成功: id={str(account.id)[:8]}, name={account.name}")
        return account
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"创建公众号失败（唯一性冲突）: {str(e)}", exc_info=True)
        raise DatabaseIntegrityException("公众号名称已存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建公众号失败: {str(e)}", exc_info=True)
        raise DatabaseOperationException("创建公众号时发生数据库错误")


async def update_official_account(
    db: AsyncSession, account_id: UUID, obj_in: OfficialAccountUpdate
) -> Optional[OfficialAccount]:
    """部分更新公众号。"""
    try:
        query = select(OfficialAccount).where(OfficialAccount.id == account_id)
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        if account is None:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)
        await db.flush()
        await db.refresh(account)
        logger.info(f"更新公众号成功: id={str(account_id)[:8]}")
        return account
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"更新公众号失败（唯一性冲突）: {str(e)}", exc_info=True)
        raise DatabaseIntegrityException("公众号名称已存在")


async def soft_delete_official_account(db: AsyncSession, account_id: UUID) -> bool:
    """软删除公众号（设置 is_active=false）。"""
    try:
        query = select(OfficialAccount).where(OfficialAccount.id == account_id)
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        if account is None:
            return False
        account.is_active = False
        await db.flush()
        logger.info(f"软删除公众号成功: id={str(account_id)[:8]}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"软删除公众号失败: id={str(account_id)[:8]}, error={str(e)}", exc_info=True)
        raise DatabaseOperationException("软删除公众号时发生数据库错误")


async def get_official_accounts_by_room_id(
    db: AsyncSession, room_id: UUID
) -> List[OfficialAccount]:
    """联表查询某直播间关联的已启用公众号列表。"""
    query = (
        select(OfficialAccount)
        .join(LiveRoomOfficialAccount, OfficialAccount.id == LiveRoomOfficialAccount.account_id)
        .where(LiveRoomOfficialAccount.room_id == room_id)
        .where(OfficialAccount.is_active == True)
        .order_by(OfficialAccount.name.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def set_room_official_accounts(
    db: AsyncSession,
    room_id: UUID,
    account_ids: List[UUID],
    mode: Literal["replace", "append"],
) -> None:
    """批量设置直播间-公众号关联；replace=先删后插，append=仅追加。"""
    try:
        if mode == "replace":
            await db.execute(delete(LiveRoomOfficialAccount).where(LiveRoomOfficialAccount.room_id == room_id))
            await db.flush()
        elif mode == "append":
            existing = await db.execute(
                select(LiveRoomOfficialAccount.account_id).where(LiveRoomOfficialAccount.room_id == room_id)
            )
            existing_ids = set(row[0] for row in existing.all())
            account_ids = [aid for aid in account_ids if aid not in existing_ids]

        for account_id in account_ids:
            link = LiveRoomOfficialAccount(room_id=room_id, account_id=account_id)
            db.add(link)
        await db.flush()
        logger.info(f"设置房间公众号关联: room_id={str(room_id)[:8]}, mode={mode}, count={len(account_ids)}")
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"设置房间公众号关联失败: room_id={str(room_id)[:8]}, error={str(e)}", exc_info=True)
        raise DatabaseIntegrityException("房间或公众号不存在")
    except Exception as e:
        await db.rollback()
        logger.error(f"设置房间公众号关联失败: room_id={str(room_id)[:8]}, error={str(e)}", exc_info=True)
        raise DatabaseOperationException("设置关联时发生数据库错误")


async def delete_room_official_account(
    db: AsyncSession, room_id: UUID, account_id: UUID
) -> bool:
    """删除直播间-公众号单条关联。"""
    try:
        stmt = delete(LiveRoomOfficialAccount).where(
            LiveRoomOfficialAccount.room_id == room_id,
            LiveRoomOfficialAccount.account_id == account_id,
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(f"删除房间公众号关联失败: room_id={str(room_id)[:8]}, account_id={str(account_id)[:8]}, error={str(e)}", exc_info=True)
        raise DatabaseOperationException("删除关联时发生数据库错误")


async def get_rooms_by_account_id_paginated(
    db: AsyncSession, account_id: UUID, page: int, size: int
) -> Tuple[int, List[LiveRoom]]:
    """联表分页查询某公众号关联的直播间列表。"""
    join_query = (
        select(LiveRoom)
        .join(LiveRoomOfficialAccount, LiveRoom.id == LiveRoomOfficialAccount.room_id)
        .where(LiveRoomOfficialAccount.account_id == account_id)
    )
    count_query = select(func.count()).select_from(join_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    query = join_query.order_by(LiveRoom.updated_at.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    return (total, list(items))
