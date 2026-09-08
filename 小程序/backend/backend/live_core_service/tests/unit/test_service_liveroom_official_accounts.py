"""
直播间与公众号关联模块 - Service 层测试
测试策略: Academic（Mock CRUD）
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.liveroom_official_accounts_service import LiveroomOfficialAccountsService
from app.schemas.liveroom_official_accounts import OfficialAccountCreate, OfficialAccountUpdate
from app.models.liveroom_official_accounts import OfficialAccount
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException


@pytest.fixture
def service():
    return LiveroomOfficialAccountsService()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_official_accounts_admin_permission_denied(service, mock_db):
    """非 Admin 调用 get_official_accounts_admin 抛出 PermissionDeniedException"""
    with pytest.raises(PermissionDeniedException):
        await service.get_official_accounts_admin(
            mock_db, user_id=uuid4(), role="REGULAR", page=1, size=10, include_inactive=False
        )


@pytest.mark.asyncio
async def test_get_official_account_by_id_not_found(service, mock_db):
    """CRUD 返回 None 时 raise NotFoundException"""
    with patch("app.services.liveroom_official_accounts_service.crud_oa.get_official_account_by_id", new_callable=AsyncMock) as m:
        m.return_value = None
        with pytest.raises(NotFoundException):
            await service.get_official_account_by_id(mock_db, uuid4(), "ADMIN", uuid4())


@pytest.mark.asyncio
async def test_get_official_account_by_id_success(service, mock_db):
    """存在时返回 OfficialAccountItem"""
    acc = OfficialAccount(
        id=uuid4(), name="测试公众号", is_active=True,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
    )
    with patch("app.services.liveroom_official_accounts_service.crud_oa.get_official_account_by_id", new_callable=AsyncMock) as m:
        m.return_value = acc
        result = await service.get_official_account_by_id(mock_db, uuid4(), "ADMIN", acc.id)
        assert result.id == acc.id
        assert result.name == acc.name


@pytest.mark.asyncio
async def test_create_official_account_success(service, mock_db):
    """Mock create 返回 OfficialAccount，Service 返回 OfficialAccountItem"""
    acc = OfficialAccount(
        id=uuid4(), name="新公众号", is_active=True,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
    )
    with patch("app.services.liveroom_official_accounts_service.crud_oa.create_official_account", new_callable=AsyncMock) as m:
        m.return_value = acc
        body = OfficialAccountCreate(name="新公众号", is_active=True)
        result = await service.create_official_account(mock_db, body, uuid4(), "ADMIN")
        assert result.name == acc.name
        assert result.id == acc.id


@pytest.mark.asyncio
async def test_soft_delete_official_account_not_found(service, mock_db):
    """CRUD 返回 False 时 raise NotFoundException"""
    with patch("app.services.liveroom_official_accounts_service.crud_oa.soft_delete_official_account", new_callable=AsyncMock) as m:
        m.return_value = False
        with pytest.raises(NotFoundException):
            await service.soft_delete_official_account(mock_db, uuid4(), uuid4(), "ADMIN")


@pytest.mark.asyncio
async def test_get_official_accounts_by_room_id_room_not_found(service, mock_db):
    """房间不存在时 raise NotFoundException"""
    with patch("app.services.liveroom_official_accounts_service.crud_room.get", new_callable=AsyncMock) as m:
        m.return_value = None
        with pytest.raises(NotFoundException):
            await service.get_official_accounts_by_room_id(mock_db, uuid4())


@pytest.mark.asyncio
async def test_set_room_official_accounts_permission_denied(service, mock_db):
    """非 Admin 调用 set_room_official_accounts 抛出 PermissionDeniedException"""
    from app.schemas.liveroom_official_accounts import LiveRoomOfficialAccountsSetRequest
    body = LiveRoomOfficialAccountsSetRequest(account_ids=[uuid4()], mode="replace")
    with pytest.raises(PermissionDeniedException):
        await service.set_room_official_accounts(mock_db, uuid4(), "REGULAR", uuid4(), body)  # user_id, role, room_id, body


@pytest.mark.asyncio
async def test_get_rooms_by_account_id_permission_denied(service, mock_db):
    """非 Admin 调用 get_rooms_by_account_id 抛出 PermissionDeniedException"""
    with pytest.raises(PermissionDeniedException):
        await service.get_rooms_by_account_id(mock_db, uuid4(), "REGULAR", uuid4(), 1, 10)
