"""
直播间与公众号关联模块的 Service 层
负责权限检查、业务编排，禁止 db.commit/rollback
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import liveroom_official_accounts as crud_oa
from app.crud import room as crud_room
from app.schemas.liveroom_official_accounts import (
    OfficialAccountCreate,
    OfficialAccountUpdate,
    OfficialAccountItem,
    LiveRoomOfficialAccountsSetRequest,
    RoomBriefItem,
    PaginatedData,
)
from app.schemas.content_management import PaginatedData as PaginatedDataSchema
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.core.exceptions import DatabaseIntegrityException
from app.core.permissions import check_admin_permission

logger = logging.getLogger(__name__)


class LiveroomOfficialAccountsService:
    async def get_official_accounts_admin(
        self,
        db: AsyncSession,
        user_id: UUID,
        role: Optional[str],
        page: int,
        size: int,
        q: Optional[str] = None,
        search_type: Optional[str] = None,
        include_inactive: bool = False,
    ):
        check_admin_permission(role)
        total, items = await crud_oa.get_paginated_official_accounts(
            db, page=page, size=size, q=q, search_type=search_type, include_inactive=include_inactive
        )
        data = PaginatedDataSchema(total=total, page=page, size=size, items=[OfficialAccountItem.model_validate(x) for x in items])
        return {"code": 200, "message": "success", "data": data.model_dump(mode="json"), "timestamp": datetime.utcnow().isoformat() + "Z"}

    async def get_official_account_by_id(
        self, db: AsyncSession, user_id: UUID, role: Optional[str], account_id: UUID
    ) -> OfficialAccountItem:
        check_admin_permission(role)
        account = await crud_oa.get_official_account_by_id(db, account_id)
        if not account:
            raise NotFoundException("公众号不存在")
        return OfficialAccountItem.model_validate(account)

    async def create_official_account(
        self, db: AsyncSession, body: OfficialAccountCreate, user_id: UUID, role: Optional[str]
    ) -> OfficialAccountItem:
        check_admin_permission(role)
        try:
            account = await crud_oa.create_official_account(db, body)
            return OfficialAccountItem.model_validate(account)
        except DatabaseIntegrityException as e:
            raise InvalidParameterException(str(e.message) if hasattr(e, 'message') else "公众号名称已存在", code=2002)

    async def update_official_account(
        self,
        db: AsyncSession,
        account_id: UUID,
        body: OfficialAccountUpdate,
        user_id: UUID,
        role: Optional[str],
    ) -> OfficialAccountItem:
        check_admin_permission(role)
        account = await crud_oa.update_official_account(db, account_id, body)
        if not account:
            raise NotFoundException("公众号不存在")
        try:
            return OfficialAccountItem.model_validate(account)
        except DatabaseIntegrityException as e:
            raise InvalidParameterException(str(e.message) if hasattr(e, 'message') else "公众号名称已存在", code=2002)

    async def soft_delete_official_account(
        self, db: AsyncSession, account_id: UUID, user_id: UUID, role: Optional[str]
    ):
        check_admin_permission(role)
        ok = await crud_oa.soft_delete_official_account(db, account_id)
        if not ok:
            raise NotFoundException("公众号不存在")
        return {"code": 200, "message": "success", "data": {"status": "soft_deleted"}, "timestamp": datetime.utcnow().isoformat() + "Z"}

    async def get_official_accounts_by_room_id(self, db: AsyncSession, room_id: UUID) -> List[OfficialAccountItem]:
        room = await crud_room.get(db, room_id, user_id=None)
        if not room:
            raise NotFoundException("房间不存在")
        items = await crud_oa.get_official_accounts_by_room_id(db, room_id)
        return [OfficialAccountItem.model_validate(x) for x in items]

    async def set_room_official_accounts(
        self,
        db: AsyncSession,
        user_id: UUID,
        role: Optional[str],
        room_id: UUID,
        body: LiveRoomOfficialAccountsSetRequest,
    ):
        check_admin_permission(role)
        room = await crud_room.get(db, room_id, user_id=None)
        if not room:
            raise NotFoundException("房间不存在")
        account_ids = list(body.account_ids)
        if account_ids:
            for aid in account_ids:
                acc = await crud_oa.get_official_account_by_id(db, aid)
                if not acc or not acc.is_active:
                    raise InvalidParameterException(f"公众号不存在或未启用: {aid}", code=4001)
        await crud_oa.set_room_official_accounts(db, room_id, account_ids, body.mode)
        items = await crud_oa.get_official_accounts_by_room_id(db, room_id)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "room_id": str(room_id),
                "mode": body.mode,
                "accounts": [OfficialAccountItem.model_validate(x).model_dump(mode="json") for x in items],
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    async def delete_room_official_account(
        self, db: AsyncSession, user_id: UUID, role: Optional[str], room_id: UUID, account_id: UUID
    ):
        check_admin_permission(role)
        ok = await crud_oa.delete_room_official_account(db, room_id, account_id)
        if not ok:
            raise NotFoundException("关联不存在")
        return {"code": 200, "message": "success", "timestamp": datetime.utcnow().isoformat() + "Z"}

    async def get_rooms_by_account_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        role: Optional[str],
        account_id: UUID,
        page: int,
        size: int,
    ):
        check_admin_permission(role)
        account = await crud_oa.get_official_account_by_id(db, account_id)
        if not account or not account.is_active:
            raise NotFoundException("公众号不存在或已禁用")
        total, rooms = await crud_oa.get_rooms_by_account_id_paginated(db, account_id, page=page, size=size)
        items = [
            RoomBriefItem(id=r.id, title=r.title, slug=getattr(r, "slug", None))
            for r in rooms
        ]
        data = PaginatedDataSchema(total=total, page=page, size=size, items=items)
        return {"code": 200, "message": "success", "data": data.model_dump(mode="json"), "timestamp": datetime.utcnow().isoformat() + "Z"}
