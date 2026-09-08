import uuid
from typing import List
from datetime import datetime
import pytest
from unittest.mock import AsyncMock

from app.services.user_behavior_service import UserBehaviorService
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
from app.exceptions import InvalidParameterException, DatabaseIntegrityException, NotFoundException


@pytest.mark.asyncio
async def test_add_favorite_success(mocker):
    """Service.add_favorite 调用 CRUD 并返回 FavoriteItem"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)

    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    # 模拟 CRUD 返回 ORM 对象（使用 Pydantic 从 dict 构造更简单）
    orm_obj = FavoriteItem(
        id=uuid.uuid4(),
        room_id=room_id,
        is_active=True,
        created_at=datetime.now(),  # 直接使用 datetime.now()
    )
    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.create_favorite",
        new_callable=AsyncMock,
        return_value=orm_obj,
    )

    result = await service.add_favorite(user_id, room_id)

    mock_crud.assert_awaited_once_with(mock_db, user_id, room_id)
    mock_db.commit.assert_awaited_once()
    assert isinstance(result, FavoriteItem)
    assert result.room_id == room_id


@pytest.mark.asyncio
async def test_add_favorite_duplicate_raises_invalid_parameter(mocker):
    """当 CRUD 抛出 DatabaseIntegrityException 时，应转换为 InvalidParameterException"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)

    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.create_favorite",
        new_callable=AsyncMock,
        side_effect=DatabaseIntegrityException("收藏已存在"),
    )

    with pytest.raises(InvalidParameterException) as exc_info:
        await service.add_favorite(user_id, room_id)

    mock_db.rollback.assert_awaited_once()
    assert "已收藏" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_favorites_success(mocker):
    """Service.get_favorites 应返回 FavoriteListResponse（分页）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)

    user_id = uuid.uuid4()
    room_id = uuid.uuid4()
    orm_list = [
        FavoriteItem(
            id=uuid.uuid4(),
            room_id=room_id,
            is_active=True,
            created_at=datetime.now(),
        )
    ]

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_user_favorites_count",
        new_callable=AsyncMock,
        return_value=1,
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_user_favorites",
        new_callable=AsyncMock,
        return_value=orm_list,
    )
    # P2 聚合：mock get_room_card_map 返回含该房间的最小卡片 map（避免真实 SQL，且竞态兜底不剔除）
    mocker.patch(
        "app.services.user_behavior_service.get_room_card_map",
        new_callable=AsyncMock,
        return_value={room_id: {"room_title": "测试房间"}},
    )

    result: FavoriteListResponse = await service.get_favorites(user_id)
    assert isinstance(result, FavoriteListResponse)
    assert result.total == 1
    assert result.page == 1
    assert result.size == 10
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_record_watch_event_success(mocker):
    """记录观看事件成功路径"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    req = WatchEventRequest(session_id=uuid.uuid4(), progress=30)

    orm_obj = WatchHistoryItem(
        id=uuid.uuid4(),
        session_id=req.session_id,
        progress=req.progress,
        watched_at=datetime.now(),  # 直接使用 datetime.now()
        is_latest=True,
    )

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.record_watch_history",
        new_callable=AsyncMock,
        return_value=orm_obj,
    )

    result = await service.record_watch_event(user_id, req)

    mock_crud.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    assert isinstance(result, WatchHistoryItem)
    assert result.session_id == req.session_id

@pytest.mark.asyncio
async def test_create_subscription_param_validation(mocker):
    """订阅参数校验：target_id 和 target_type 必须提供"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()

    # 注意：由于 SubscriptionCreate 中 target_id 和 target_type 都是必填字段（...），
    # 如果缺少这些字段，Pydantic 会在构造时抛出 ValidationError，而不是在 Service 层
    # 因此这个测试主要用于验证 Service 层的基本流程
    from datetime import datetime
    sub_in = SubscriptionCreate(
        target_type=SubscriptionTargetType.ROOM, target_id=uuid.uuid4()
    )

    # Mock room.get() 返回一个存在的房间对象（用于验证通过）
    mock_room_get = mocker.patch(
        "app.services.user_behavior_service.room.get",
        new_callable=AsyncMock,
        return_value=AsyncMock()  # 返回一个 mock 对象，表示房间存在
    )

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.create_subscription",
        new_callable=AsyncMock,
        return_value=SubscriptionItem(
            id=uuid.uuid4(),
            target_id=sub_in.target_id,
            target_type=sub_in.target_type,
            is_active=True,
            created_at=datetime.now(),
        ),
    )

    result = await service.create_subscription(user_id, sub_in)
    assert result.target_id == sub_in.target_id
    assert result.target_type == sub_in.target_type
    # 验证 room.get() 被调用
    mock_room_get.assert_awaited_once_with(mock_db, sub_in.target_id)


@pytest.mark.asyncio
async def test_create_subscription_param_validation(mocker):
    """订阅参数校验：target_id 和 target_type 必须提供"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()

    from datetime import datetime
    sub_in = SubscriptionCreate(
        target_type=SubscriptionTargetType.ROOM, target_id=uuid.uuid4()
    )

    # Mock room.get() - 需要在 Service 方法调用之前 mock
    mock_room_get = mocker.patch(
        "app.crud.room.get",
        new_callable=AsyncMock,
        return_value=AsyncMock()  # 返回一个 mock 对象，表示房间存在
    )

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.create_subscription",
        new_callable=AsyncMock,
        return_value=SubscriptionItem(
            id=uuid.uuid4(),
            target_id=sub_in.target_id,
            target_type=sub_in.target_type,
            is_active=True,
            created_at=datetime.now(),
        ),
    )

    result = await service.create_subscription(user_id, sub_in)
    assert result.target_id == sub_in.target_id
    assert result.target_type == sub_in.target_type
    # 验证 room.get() 被调用
    mock_room_get.assert_awaited_once_with(mock_db, sub_in.target_id)


@pytest.mark.asyncio
async def test_create_subscription_duplicate(mocker):
    """重复订阅时转换为 InvalidParameterException"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    sub_in = SubscriptionCreate(
        target_type=SubscriptionTargetType.ROOM, target_id=uuid.uuid4()
    )

    # Mock room.get() - 需要在 Service 方法调用之前 mock
    mock_room_get = mocker.patch(
        "app.crud.room.get",
        new_callable=AsyncMock,
        return_value=AsyncMock()  # 返回一个 mock 对象，表示房间存在
    )

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.create_subscription",
        new_callable=AsyncMock,
        side_effect=DatabaseIntegrityException("订阅已存在"),
    )

    with pytest.raises(InvalidParameterException) as exc_info:
        await service.create_subscription(user_id, sub_in)

    mock_db.rollback.assert_awaited_once()
    assert "订阅已存在" in str(exc_info.value)
    # 验证 room.get() 被调用
    mock_room_get.assert_awaited_once_with(mock_db, sub_in.target_id)


@pytest.mark.asyncio
async def test_get_subscriptions_success(mocker):
    """获取订阅列表成功路径（分页）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()

    target_id = uuid.uuid4()
    orm_list = [
        SubscriptionItem(
            id=uuid.uuid4(),
            target_id=target_id,
            target_type=SubscriptionTargetType.ROOM,
            is_active=True,
            created_at=datetime.now(),
        )
    ]

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.count_subscriptions",
        new_callable=AsyncMock,
        return_value=1,
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.list_subscriptions",
        new_callable=AsyncMock,
        return_value=orm_list,
    )
    # P2 聚合：mock get_room_card_map（room 订阅分支），避免真实 SQL 且竞态兜底不剔除
    mocker.patch(
        "app.services.user_behavior_service.get_room_card_map",
        new_callable=AsyncMock,
        return_value={target_id: {"room_title": "测试房间"}},
    )
    mocker.patch(
        "app.services.user_behavior_service.get_session_card_map",
        new_callable=AsyncMock,
        return_value={},
    )

    result: SubscriptionListResponse = await service.get_subscriptions(
        user_id, target_type=SubscriptionTargetType.ROOM
    )
    assert isinstance(result, SubscriptionListResponse)
    assert result.total == 1
    assert result.page == 1
    assert result.size == 10
    assert len(result.items) == 1


# ==================== 收藏业务补充测试 ====================

@pytest.mark.asyncio
async def test_remove_favorite_success(mocker):
    """测试 remove_favorite 成功路径（Mock CRUD返回True，验证commit被调用）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.delete_favorite",
        new_callable=AsyncMock,
        return_value=True,
    )

    await service.remove_favorite(user_id, room_id)

    mock_crud.assert_awaited_once_with(mock_db, user_id, room_id)
    mock_db.commit.assert_awaited_once()
    mock_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_favorite_idempotent(mocker):
    """测试 remove_favorite 幂等路径（Mock CRUD返回False，验证不抛异常）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.delete_favorite",
        new_callable=AsyncMock,
        return_value=False,  # 记录不存在，返回False
    )

    # 幂等操作不应抛异常
    await service.remove_favorite(user_id, room_id)

    mock_crud.assert_awaited_once_with(mock_db, user_id, room_id)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_favorite_exception_rollback(mocker):
    """测试 remove_favorite 异常时执行rollback（Mock CRUD抛出异常，验证rollback被调用）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.delete_favorite",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )

    with pytest.raises(Exception):
        await service.remove_favorite(user_id, room_id)

    mock_crud.assert_awaited_once_with(mock_db, user_id, room_id)
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_favorites_empty_list(mocker):
    """测试 get_favorites 返回空列表（分页结构）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_user_favorites_count",
        new_callable=AsyncMock,
        return_value=0,
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_user_favorites",
        new_callable=AsyncMock,
        return_value=[],
    )

    result: FavoriteListResponse = await service.get_favorites(user_id)
    assert isinstance(result, FavoriteListResponse)
    assert result.total == 0
    assert result.page == 1
    assert result.size == 10
    assert len(result.items) == 0


# ==================== 观看历史业务补充测试 ====================

@pytest.mark.asyncio
async def test_record_watch_event_exception_rollback(mocker):
    """测试 record_watch_event 异常时回滚并记录日志（Mock CRUD抛出异常，验证rollback和logger.error被调用）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    req = WatchEventRequest(session_id=uuid.uuid4(), progress=30)

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.record_watch_history",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )

    with pytest.raises(Exception):
        await service.record_watch_event(user_id, req)

    mock_crud.assert_awaited_once()
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_watch_history_with_page_size(mocker):
    """测试 get_watch_history 的 page/size 参数（Mock CRUD，验证分页参数传递）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    page, size = 1, 10

    session_id = uuid.uuid4()
    orm_list = [
        WatchHistoryItem(
            id=uuid.uuid4(),
            session_id=session_id,
            progress=10,
            watched_at=datetime.now(),
            is_latest=True,
        )
    ]

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.count_watch_history",
        new_callable=AsyncMock,
        return_value=1,
    )
    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.list_watch_history",
        new_callable=AsyncMock,
        return_value=orm_list,
    )
    # P2 聚合：mock get_session_card_map（观看历史走 session 分支），避免真实 SQL 且竞态兜底不剔除
    mocker.patch(
        "app.services.user_behavior_service.get_session_card_map",
        new_callable=AsyncMock,
        return_value={session_id: {"title": "测试场次"}},
    )

    result: WatchHistoryListResponse = await service.get_watch_history(user_id, page=page, size=size)

    mock_crud.assert_awaited_once_with(mock_db, user_id, offset=0, limit=size)
    assert isinstance(result, WatchHistoryListResponse)
    assert result.total == 1
    assert result.page == page
    assert result.size == size
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_get_watch_history_empty_list(mocker):
    """测试 get_watch_history 返回空列表（分页结构）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.count_watch_history",
        new_callable=AsyncMock,
        return_value=0,
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.list_watch_history",
        new_callable=AsyncMock,
        return_value=[],
    )

    result: WatchHistoryListResponse = await service.get_watch_history(user_id)
    assert isinstance(result, WatchHistoryListResponse)
    assert result.total == 0
    assert result.page == 1
    assert result.size == 20
    assert len(result.items) == 0


# ==================== 订阅业务补充测试 ====================

# 修复 test_cancel_subscription_success
@pytest.mark.asyncio
async def test_cancel_subscription_success(mocker):
    """测试 cancel_subscription 成功路径（Mock CRUD返回True，验证commit被调用）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    target_type = SubscriptionTargetType.ROOM
    target_id = uuid.uuid4()

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.cancel_subscription",
        new_callable=AsyncMock,
        return_value=True,
    )

    await service.cancel_subscription(user_id, target_type, target_id)

    # 使用关键字参数断言，因为Service层使用关键字参数调用
    mock_crud.assert_awaited_once_with(
        mock_db,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
    )
    mock_db.commit.assert_awaited_once()
    mock_db.rollback.assert_not_awaited()

# 修复 test_cancel_subscription_idempotent
@pytest.mark.asyncio
async def test_cancel_subscription_idempotent(mocker):
    """测试 cancel_subscription 幂等路径（Mock CRUD返回False，验证不抛异常）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    target_type = SubscriptionTargetType.ROOM
    target_id = uuid.uuid4()

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.cancel_subscription",
        new_callable=AsyncMock,
        return_value=False,  # 记录不存在，返回False
    )

    # 幂等操作不应抛异常
    await service.cancel_subscription(user_id, target_type, target_id)

    # 使用关键字参数断言，因为Service层使用关键字参数调用
    mock_crud.assert_awaited_once_with(
        mock_db,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
    )
    mock_db.commit.assert_awaited_once()


# 修复 test_cancel_subscription_exception_rollback
@pytest.mark.asyncio
async def test_cancel_subscription_exception_rollback(mocker):
    """测试 cancel_subscription 异常时执行rollback"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    target_type = SubscriptionTargetType.ROOM
    target_id = uuid.uuid4()

    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.cancel_subscription",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )

    with pytest.raises(Exception):
        await service.cancel_subscription(user_id, target_type, target_id)

    # 使用关键字参数断言，因为Service层使用关键字参数调用
    mock_crud.assert_awaited_once_with(
        mock_db,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
    )
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_subscriptions_filter_by_target_type(mocker):
    """测试 get_subscriptions 按 target_type 过滤（分页）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()
    target_type = SubscriptionTargetType.ROOM

    target_id = uuid.uuid4()
    orm_list = [
        SubscriptionItem(
            id=uuid.uuid4(),
            target_id=target_id,
            target_type=SubscriptionTargetType.ROOM,
            is_active=True,
            created_at=datetime.now(),
        )
    ]

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.count_subscriptions",
        new_callable=AsyncMock,
        return_value=1,
    )
    mock_crud = mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.list_subscriptions",
        new_callable=AsyncMock,
        return_value=orm_list,
    )
    # P2 聚合：mock get_room_card_map（room 订阅分支），避免真实 SQL 且竞态兜底不剔除
    mocker.patch(
        "app.services.user_behavior_service.get_room_card_map",
        new_callable=AsyncMock,
        return_value={target_id: {"room_title": "测试房间"}},
    )
    mocker.patch(
        "app.services.user_behavior_service.get_session_card_map",
        new_callable=AsyncMock,
        return_value={},
    )

    result: SubscriptionListResponse = await service.get_subscriptions(user_id, target_type=target_type)

    mock_crud.assert_awaited_once_with(
        mock_db,
        user_id=user_id,
        target_type=target_type,
        only_active=True,
        offset=0,
        limit=10,
    )
    assert isinstance(result, SubscriptionListResponse)
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].target_type == SubscriptionTargetType.ROOM


@pytest.mark.asyncio
async def test_get_subscriptions_empty_list(mocker):
    """测试 get_subscriptions 返回空列表（分页结构）"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.count_subscriptions",
        new_callable=AsyncMock,
        return_value=0,
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.list_subscriptions",
        new_callable=AsyncMock,
        return_value=[],
    )

    result: SubscriptionListResponse = await service.get_subscriptions(user_id)
    assert isinstance(result, SubscriptionListResponse)
    assert result.total == 0
    assert result.page == 1
    assert result.size == 10
    assert len(result.items) == 0


# ==================== 增量：check_is_favorited（检查是否已收藏） ====================


@pytest.mark.asyncio
async def test_check_is_favorited_true(mocker):
    """检查是否已收藏：房间存在且已收藏时返回 is_favorited=True"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Mock 调用链：先 crud_room.get 再 get_favorite
    mocker.patch(
        "app.services.user_behavior_service.crud_room.get",
        new_callable=AsyncMock,
        return_value=object(),  # 任意非 None 表示房间存在
    )
    mock_fav = type("UserFavorite", (), {"is_active": True})()
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_favorite",
        new_callable=AsyncMock,
        return_value=mock_fav,
    )

    result = await service.check_is_favorited(room_id=room_id, current_user_id=user_id)

    assert result["is_favorited"] is True


@pytest.mark.asyncio
async def test_check_is_favorited_false(mocker):
    """检查是否已收藏：房间存在但未收藏时返回 is_favorited=False"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_room.get",
        new_callable=AsyncMock,
        return_value=object(),
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_favorite",
        new_callable=AsyncMock,
        return_value=None,
    )

    result = await service.check_is_favorited(room_id=room_id, current_user_id=user_id)

    assert result["is_favorited"] is False


@pytest.mark.asyncio
async def test_check_is_favorited_room_not_found_raises(mocker):
    """检查是否已收藏：房间不存在时抛出 NotFoundException"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_room.get",
        new_callable=AsyncMock,
        return_value=None,
    )

    with pytest.raises(NotFoundException):
        await service.check_is_favorited(room_id=room_id, current_user_id=user_id)


# ==================== 增量：check_is_subscribed（检查是否已订阅） ====================


@pytest.mark.asyncio
async def test_check_is_subscribed_room_true(mocker):
    """检查房间订阅：资源存在且已订阅时返回 is_subscribed=True"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_room.get",
        new_callable=AsyncMock,
        return_value=object(),
    )
    mock_sub = type("UserSubscription", (), {"is_active": True})()
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_subscription",
        new_callable=AsyncMock,
        return_value=mock_sub,
    )

    result = await service.check_is_subscribed(
        target_type=SubscriptionTargetType.ROOM,
        target_id=room_id,
        current_user_id=user_id,
    )

    assert result["is_subscribed"] is True


@pytest.mark.asyncio
async def test_check_is_subscribed_room_false(mocker):
    """检查房间订阅：资源存在但未订阅时返回 is_subscribed=False"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_room.get",
        new_callable=AsyncMock,
        return_value=object(),
    )
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_subscription",
        new_callable=AsyncMock,
        return_value=None,
    )

    result = await service.check_is_subscribed(
        target_type=SubscriptionTargetType.ROOM,
        target_id=room_id,
        current_user_id=user_id,
    )

    assert result["is_subscribed"] is False


@pytest.mark.asyncio
async def test_check_is_subscribed_room_not_found_raises(mocker):
    """检查房间订阅：房间不存在时抛出 NotFoundException"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_room.get",
        new_callable=AsyncMock,
        return_value=None,
    )

    with pytest.raises(NotFoundException):
        await service.check_is_subscribed(
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
            current_user_id=user_id,
        )


@pytest.mark.asyncio
async def test_check_is_subscribed_session_true(mocker):
    """检查场次订阅：资源存在且已订阅时返回 is_subscribed=True"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_session.get",
        new_callable=AsyncMock,
        return_value=object(),
    )
    mock_sub = type("UserSubscription", (), {"is_active": True})()
    mocker.patch(
        "app.services.user_behavior_service.crud_user_behavior.get_subscription",
        new_callable=AsyncMock,
        return_value=mock_sub,
    )

    result = await service.check_is_subscribed(
        target_type=SubscriptionTargetType.SESSION,
        target_id=session_id,
        current_user_id=user_id,
    )

    assert result["is_subscribed"] is True


@pytest.mark.asyncio
async def test_check_is_subscribed_session_not_found_raises(mocker):
    """检查场次订阅：场次不存在时抛出 NotFoundException"""
    mock_db = AsyncMock()
    service = UserBehaviorService(mock_db)
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mocker.patch(
        "app.services.user_behavior_service.crud_session.get",
        new_callable=AsyncMock,
        return_value=None,
    )

    with pytest.raises(NotFoundException):
        await service.check_is_subscribed(
            target_type=SubscriptionTargetType.SESSION,
            target_id=session_id,
            current_user_id=user_id,
        )

