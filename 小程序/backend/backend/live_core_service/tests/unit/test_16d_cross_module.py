"""16-D2 / 16-D3 / 16-D5 跨模块单元测试"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.core.deactivated_users import DEACTIVATED_DISPLAY_NAME
from app.schemas.live_features import (
    apply_deactivated_display,
    apply_live_user_profile,
    build_message_user_snapshot,
    resolve_message_user_display,
)
from app.services.deactivate_cleanup_service import DeactivateCleanupService
from app.models.user_behavior import UserFavorite
from app.models.brand import Brand
from app.models.experts import Expert
from app.crud import room as crud_room
from app.schemas.live_core import LiveRoomCreate


@pytest.mark.asyncio
async def test_apply_deactivated_display_overrides_snapshot():
    """16-D3：命中已注销标记时昵称占位、头像 null。"""
    name, info = build_message_user_snapshot(
        {"user_display_name": "李医生", "avatar_url": "https://x/a.png"}
    )
    name2, info2 = apply_deactivated_display(name, info, is_deactivated=True)
    assert name2 == DEACTIVATED_DISPLAY_NAME
    assert info2 is not None
    assert info2.nickname == DEACTIVATED_DISPLAY_NAME
    assert info2.avatar_url is None

    name3, info3 = apply_deactivated_display(name, info, is_deactivated=False)
    assert name3 == "李医生"
    assert info3.avatar_url == "https://x/a.png"


@pytest.mark.asyncio
async def test_apply_live_user_profile_overrides_snapshot():
    """07-V4：个人中心当前资料覆盖发送时快照。"""
    name, info = build_message_user_snapshot(
        {"user_display_name": "旧昵称", "avatar_url": "https://x/old.png"}
    )
    name2, info2 = apply_live_user_profile(
        name,
        info,
        {"nickname": "新昵称", "avatar_url": "https://x/new.png", "username": "u1"},
    )
    assert name2 == "新昵称"
    assert info2 is not None
    assert info2.nickname == "新昵称"
    assert info2.avatar_url == "https://x/new.png"


@pytest.mark.asyncio
async def test_apply_live_user_profile_falls_back_without_profile():
    """batch 失败/空 map：保持快照。"""
    name, info = build_message_user_snapshot(
        {"user_display_name": "快照名", "avatar_url": "https://x/s.png"}
    )
    name2, info2 = apply_live_user_profile(name, info, None)
    assert name2 == "快照名"
    assert info2.avatar_url == "https://x/s.png"
    name3, info3 = apply_live_user_profile(name, info, {})
    assert name3 == "快照名"
    assert info3.avatar_url == "https://x/s.png"


@pytest.mark.asyncio
async def test_resolve_message_user_display_order_live_then_d3():
    """组装顺序：快照 → live → D3；注销压过 live。"""
    extra = {"user_display_name": "旧名", "avatar_url": "https://x/old.png"}
    profile = {"nickname": "新名", "avatar_url": "https://x/new.png"}

    name, info = resolve_message_user_display(extra, profile, is_deactivated=False)
    assert name == "新名"
    assert info.avatar_url == "https://x/new.png"

    name2, info2 = resolve_message_user_display(extra, profile, is_deactivated=True)
    assert name2 == DEACTIVATED_DISPLAY_NAME
    assert info2.nickname == DEACTIVATED_DISPLAY_NAME
    assert info2.avatar_url is None


@pytest.mark.asyncio
async def test_fetch_user_profiles_degrades_without_config(mocker):
    """公共客户端未配置时返回空 map（留言降级快照）。"""
    from app.services.user_profile_client import fetch_user_profiles

    mocker.patch("app.core.config.settings.USER_SERVICE_URL", "")
    mocker.patch("app.core.config.settings.INTERNAL_SERVICE_TOKEN", "")
    profiles = await fetch_user_profiles([uuid.uuid4()])
    assert profiles == {}


@pytest.mark.asyncio
async def test_deactivate_cleanup_soft_hides_and_unbinds(db_session, test_user, mocker):
    """16-D2：收藏软藏、解绑专家 user_id；不碰 live_rooms。"""
    mocker.patch(
        "app.services.deactivate_cleanup_service.mark_user_deactivated",
        new_callable=AsyncMock,
        return_value=True,
    )

    async for db in db_session:
        async for user in test_user:
            uid = user["public_id"]
            room = await crud_room.create(
                db=db,
                obj_in=LiveRoomCreate(title="d2-room", description="x"),
                user_id=uid,
            )
            await db.commit()

            fav = UserFavorite(
                id=uuid.uuid4(),
                user_id=uid,
                room_id=room.id,
                is_active=True,
            )
            db.add(fav)

            expert = Expert(
                id=uuid.uuid4(),
                name="专家甲",
                user_id=uid,
                is_active=True,
            )
            db.add(expert)
            await db.commit()

            service = DeactivateCleanupService(db)
            result = await service.run(uid)

            assert result["removed_brand_members"] == 0
            assert result["unbound_experts"] >= 1
            assert result["deleted_counts"]["user_favorites"] >= 1

            await db.refresh(fav)
            assert fav.is_active is False
            await db.refresh(expert)
            assert expert.user_id is None

            # 16-D1：房间仍在
            still = await crud_room.get(db=db, room_id=room.id)
            assert still is not None
            break
        break


@pytest.mark.asyncio
async def test_delete_brand_soft_keeps_entity(db_session):
    """16-D5：软删品牌保留品牌行（is_active=false）。"""
    from app.crud import brand as crud_brand

    async for db in db_session:
        brand = Brand(
            id=uuid.uuid4(),
            name=f"soft_{uuid.uuid4().hex[:6]}",
            is_active=True,
        )
        db.add(brand)
        await db.commit()

        await crud_brand.delete_brand(db, brand.id, hard_delete=False)

        await db.refresh(brand)
        assert brand.is_active is False
        break
