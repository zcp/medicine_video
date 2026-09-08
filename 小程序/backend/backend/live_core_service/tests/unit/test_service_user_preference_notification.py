"""
用户偏好与通知模块 - Service层测试

测试策略: Academic (学院派)
- Mock掉CRUD层和I/O操作
- 验证Service层的业务逻辑和异常转换
- 使用真实Model类创建Mock对象（不使用MagicMock）
"""

import uuid
from datetime import datetime, time, timezone

import pytest
from unittest.mock import AsyncMock

from app.services.user_preference_notification_service import UserPreferenceNotificationService
from app.models.user_preference_notification import UserPreferences, Notification
from app.schemas.user_preference_notification import (
    UserPreferencesUpdate,
    UserPreferencesItem,
    NotificationItem,
    NotificationCreateRequest,
    NotificationBatchCreateResponse,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
    NotificationListResponse,
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
)


# ==================== User Preferences Service 测试 ====================

@pytest.mark.asyncio
async def test_get_preferences_exists(mocker):
    """测试获取已存在的用户偏好"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    # Mock CRUD返回ORM对象（使用真实Model类）
    prefs = UserPreferences(
        id=uuid.uuid4(),
        user_id=user_id,
        theme_mode="dark",
        homepage_view_mode="single",
        created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        updated_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.get_preferences",
        new_callable=AsyncMock,
        return_value=prefs,
    )
    
    result = await service.get_preferences(user_id, role)
    
    mock_crud.assert_awaited_once_with(mock_db, user_id)
    assert isinstance(result, UserPreferencesItem)
    assert result.user_id == user_id
    assert result.theme_mode == "dark"


@pytest.mark.asyncio
async def test_get_preferences_not_exists_returns_default(mocker):
    """测试获取不存在的用户偏好（首次访问，返回默认值）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    # Mock CRUD返回None（首次访问）
    mocker.patch(
        "app.services.user_preference_notification_service.crud.get_preferences",
        new_callable=AsyncMock,
        return_value=None,
    )
    
    result = await service.get_preferences(user_id, role)
    
    assert isinstance(result, UserPreferencesItem)
    assert result.user_id == user_id
    # 验证默认值
    assert result.theme_mode == "auto"  # 默认值
    assert result.homepage_view_mode == "double"  # 默认值


@pytest.mark.asyncio
async def test_update_preferences_create(mocker):
    """测试更新用户偏好（创建新偏好）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    prefs_update = UserPreferencesUpdate(
        theme_mode="scheduled",
        homepage_view_mode="double",  # ✅ 新增：第115行后面插入
        theme_scheduled_dark_time=time(21, 0),
        theme_scheduled_light_time=time(7, 0),
    )
    
    # Mock CRUD返回创建的ORM对象
    prefs = UserPreferences(
        id=uuid.uuid4(),
        user_id=user_id,
        theme_mode="scheduled",
        #theme_mode="auto",  # ✅ 新增：第114行后面插入
        homepage_view_mode="double",  # ✅ 新增：第115行后面插入
        theme_scheduled_dark_time=time(21, 0),
        theme_scheduled_light_time=time(7, 0),
        created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        updated_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.create_or_update_preferences",
        new_callable=AsyncMock,
        return_value=prefs,
    )
    
    result = await service.update_preferences(user_id, prefs_update, role)
    
    mock_crud.assert_awaited_once_with(mock_db, user_id, prefs_update)
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(prefs)
    assert isinstance(result, UserPreferencesItem)
    assert result.theme_mode == "scheduled"


@pytest.mark.asyncio
async def test_update_preferences_update(mocker):
    """测试更新用户偏好（更新现有偏好）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    prefs_update = UserPreferencesUpdate(
        theme_mode="dark",
        homepage_view_mode="single",
    )
    
    # Mock CRUD返回更新的ORM对象
    prefs = UserPreferences(
        id=uuid.uuid4(),
        user_id=user_id,
        theme_mode="dark",
        homepage_view_mode="single",
        created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        updated_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.create_or_update_preferences",
        new_callable=AsyncMock,
        return_value=prefs,
    )
    
    result = await service.update_preferences(user_id, prefs_update, role)
    
    mock_crud.assert_awaited_once_with(mock_db, user_id, prefs_update)
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(prefs)
    assert isinstance(result, UserPreferencesItem)
    assert result.theme_mode == "dark"
    assert result.homepage_view_mode == "single"


@pytest.mark.asyncio
async def test_update_preferences_exception_rollback(mocker):
    """测试更新用户偏好异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    prefs_update = UserPreferencesUpdate(theme_mode="dark")
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.create_or_update_preferences",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.update_preferences(user_id, prefs_update, role)
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


# ==================== Notifications Service 测试 ====================

@pytest.mark.asyncio
async def test_get_notifications_list_success(mocker):
    """测试获取通知列表成功"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    page = 1
    size = 10
    
    # Mock CRUD返回(列表, 总数)
    notifications = [
        Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="通知1",
            notification_type="system",
            is_read=False,
            created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        ),
        Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="通知2",
            notification_type="subscription",
            is_read=True,
            created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        ),
    ]
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.get_notifications",
        new_callable=AsyncMock,
        return_value=(notifications, 2),
    )
    
    result = await service.get_notifications_list(
        user_id, page, size, None, None, role
    )
    
    mock_crud.assert_awaited_once_with(
        mock_db,
        user_id=user_id,
        page=page,
        size=size,
        is_read=None,
        notification_type=None,
        current_user_id=user_id,
        role=role,
    )
    assert isinstance(result, NotificationListResponse)
    assert len(result.items) == 2
    assert result.total == 2
    assert result.page == page
    assert result.size == size


@pytest.mark.asyncio
async def test_get_notifications_list_with_filters(mocker):
    """测试获取通知列表（带筛选条件）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    notifications = [
        Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="未读通知",
            notification_type="system",  # ✅ 修复：添加必需字段
            is_read=False,
            created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        ),
    ]
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.get_notifications",
        new_callable=AsyncMock,
        return_value=(notifications, 1),
    )
    
    result = await service.get_notifications_list(
        user_id, page=1, size=10, is_read=False, notification_type="system", role=role
    )
    
    mock_crud.assert_awaited_once_with(
        mock_db,
        user_id=user_id,
        page=1,
        size=10,
        is_read=False,
        notification_type="system",
        current_user_id=user_id,
        role=role,
    )
    assert len(result.items) == 1
    assert result.items[0].is_read is False
    assert result.items[0].notification_type == "system"


@pytest.mark.asyncio
async def test_get_unread_count_success(mocker):
    """测试获取未读通知数量"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.get_unread_count",
        new_callable=AsyncMock,
        return_value=5,
    )
    
    result = await service.get_unread_count(user_id)
    
    mock_crud.assert_awaited_once_with(mock_db, user_id)
    assert isinstance(result, dict)
    assert result["unread_count"] == 5


@pytest.mark.asyncio
async def test_mark_notification_as_read_success(mocker):
    """测试标记通知为已读成功"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    notification_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    # Mock CRUD返回通知对象
    notification = Notification(
        id=notification_id,
        user_id=user_id,
        title="通知",
        notification_type="system",  # ✅ 修复：添加必需字段
        is_read=True,  # 已标记为已读
        created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.mark_as_read",
        new_callable=AsyncMock,
        return_value=notification,
    )
    
    await service.mark_notification_as_read(notification_id, user_id, role)
    
    mock_crud.assert_awaited_once_with(mock_db, notification_id, user_id)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found(mocker):
    """测试标记通知为已读（通知不存在）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    notification_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    # Mock CRUD返回None（通知不存在）
    mocker.patch(
        "app.services.user_preference_notification_service.crud.mark_as_read",
        new_callable=AsyncMock,
        return_value=None,
    )
    
    with pytest.raises(NotFoundException) as exc_info:
        await service.mark_notification_as_read(notification_id, user_id, role)
    
    assert "通知不存在或不属于当前用户" in str(exc_info.value)
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_notification_as_read_exception_rollback(mocker):
    """测试标记通知为已读异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    notification_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role = "REGULAR"
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.mark_as_read",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.mark_notification_as_read(notification_id, user_id, role)
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_success(mocker):
    """测试标记所有通知为已读成功"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.mark_all_as_read",
        new_callable=AsyncMock,
        return_value=3,  # 更新了3条通知
    )
    
    result = await service.mark_all_notifications_as_read(user_id)
    
    mock_crud.assert_awaited_once_with(mock_db, user_id)
    mock_db.commit.assert_awaited_once()
    assert isinstance(result, dict)
    assert result["updated_count"] == 3


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_exception_rollback(mocker):
    """测试标记所有通知为已读异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    user_id = uuid.uuid4()
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.mark_all_as_read",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.mark_all_notifications_as_read(user_id)
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_notifications_batch_success(mocker):
    """测试批量创建通知成功（管理员）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    
    user_ids = [uuid.uuid4(), uuid.uuid4()]
    notification_data = NotificationCreateRequest(
        user_ids=user_ids,
        title="批量通知",
        content="通知内容",
        notification_type="system",
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.bulk_create_notifications",
        new_callable=AsyncMock,
        return_value=2,  # 创建了2条通知
    )
    
    result = await service.create_notifications_batch(
        user_ids, notification_data, admin_role
    )
    
    mock_crud.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    assert isinstance(result, NotificationBatchCreateResponse)
    assert result.total_created == 2
    assert len(result.user_ids) == 2


@pytest.mark.asyncio
async def test_create_notifications_batch_empty_user_ids_raises_exception(mocker):
    """测试批量创建通知（user_ids为空列表时抛出参数错误）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"

    notification_data = NotificationCreateRequest(
        user_ids=[],  # 空列表应该抛出异常
        title="全部用户通知",
        notification_type="system",
    )

    # 期望抛出InvalidParameterException
    with pytest.raises(InvalidParameterException) as exc_info:
        await service.create_notifications_batch(
            notification_data.user_ids, notification_data, admin_role
        )

    # 验证错误消息
    assert "user_ids不能为空" in str(exc_info.value)
    # 验证没有调用CRUD和commit（因为提前抛出异常）
    mock_db.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_create_notifications_batch_permission_denied(mocker):
    """测试批量创建通知（权限不足）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    regular_role = "REGULAR"  # 普通用户，无权操作
    
    user_ids = [uuid.uuid4()]
    notification_data = NotificationCreateRequest(
        user_ids=user_ids,
        title="通知",
        notification_type="system",
    )
    
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.create_notifications_batch(
            user_ids, notification_data, regular_role
        )
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_notifications_batch_exception_rollback(mocker):
    """测试批量创建通知异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    
    user_ids = [uuid.uuid4()]
    notification_data = NotificationCreateRequest(
        user_ids=user_ids,
        title="通知",
        notification_type="system",
    )
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.bulk_create_notifications",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.create_notifications_batch(
            user_ids, notification_data, admin_role
        )
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_notifications_list_admin_success(mocker):
    """测试管理员获取通知列表成功"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    page = 1
    size = 10
    
    notifications = [
        Notification(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="通知1",
            notification_type="system",
            is_read=False,  # ✅ 修复：添加必需字段
            created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
        ),
    ]
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.get_notifications_admin",
        new_callable=AsyncMock,
        return_value=(notifications, 1),
    )
    
    result = await service.get_notifications_list_admin(
        page, size, None, None, None, admin_role
    )
    
    mock_crud.assert_awaited_once_with(
        mock_db,
        page=page,
        size=size,
        user_id=None,
        notification_type=None,
        is_read=None,
    )
    assert isinstance(result, NotificationListResponse)
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_get_notifications_list_admin_permission_denied(mocker):
    """测试管理员获取通知列表（权限不足）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    regular_role = "REGULAR"  # 普通用户，无权操作
    
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.get_notifications_list_admin(
            1, 10, None, None, None, regular_role
        )
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_notification_success(mocker):
    """测试更新通知成功（管理员）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    notification_id = uuid.uuid4()
    
    update_data = NotificationUpdateRequest(
        title="新标题",
        content="新内容",
    )
    
    # Mock CRUD返回更新的通知对象
    notification = Notification(
        id=notification_id,
        user_id=uuid.uuid4(),
        title="新标题",
        content="新内容",
        notification_type="system",  # ✅ 修复：添加必需字段
        is_read=False,  # ✅ 修复：添加必需字段
        created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.update_notification",
        new_callable=AsyncMock,
        return_value=notification,
    )
    
    result = await service.update_notification(notification_id, update_data, admin_role)
    
    mock_crud.assert_awaited_once_with(
        mock_db, notification_id, update_data.model_dump(exclude_unset=True)
    )
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(notification)
    assert isinstance(result, NotificationItem)
    assert result.title == "新标题"
    assert result.content == "新内容"


@pytest.mark.asyncio
async def test_update_notification_not_found(mocker):
    """测试更新通知（通知不存在）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    notification_id = uuid.uuid4()
    
    update_data = NotificationUpdateRequest(title="新标题")
    
    # Mock CRUD返回None（通知不存在）
    mocker.patch(
        "app.services.user_preference_notification_service.crud.update_notification",
        new_callable=AsyncMock,
        return_value=None,
    )
    
    with pytest.raises(NotFoundException) as exc_info:
        await service.update_notification(notification_id, update_data, admin_role)
    
    assert "通知不存在" in str(exc_info.value)
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_notification_permission_denied(mocker):
    """测试更新通知（权限不足）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    regular_role = "REGULAR"  # 普通用户，无权操作
    notification_id = uuid.uuid4()
    
    update_data = NotificationUpdateRequest(title="新标题")
    
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.update_notification(notification_id, update_data, regular_role)
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_notification_exception_rollback(mocker):
    """测试更新通知异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    notification_id = uuid.uuid4()
    
    update_data = NotificationUpdateRequest(title="新标题")
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.update_notification",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.update_notification(notification_id, update_data, admin_role)
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_notification_success(mocker):
    """测试删除通知成功（管理员）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    notification_id = uuid.uuid4()
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.delete_notification",
        new_callable=AsyncMock,
        return_value=True,  # 删除成功
    )
    
    await service.delete_notification(notification_id, admin_role)
    
    mock_crud.assert_awaited_once_with(mock_db, notification_id)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_notification_not_found(mocker):
    """测试删除通知（通知不存在）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    notification_id = uuid.uuid4()
    
    # Mock CRUD返回False（通知不存在）
    mocker.patch(
        "app.services.user_preference_notification_service.crud.delete_notification",
        new_callable=AsyncMock,
        return_value=False,
    )
    
    with pytest.raises(NotFoundException) as exc_info:
        await service.delete_notification(notification_id, admin_role)
    
    assert "通知不存在" in str(exc_info.value)
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_notification_permission_denied(mocker):
    """测试删除通知（权限不足）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    regular_role = "REGULAR"  # 普通用户，无权操作
    notification_id = uuid.uuid4()
    
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.delete_notification(notification_id, regular_role)
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_notification_exception_rollback(mocker):
    """测试删除通知异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    notification_id = uuid.uuid4()
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.delete_notification",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.delete_notification(notification_id, admin_role)
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_delete_notifications_success(mocker):
    """测试批量删除通知成功（管理员）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    
    delete_request = NotificationBatchDeleteRequest(
        notification_ids=[uuid.uuid4(), uuid.uuid4()],
    )
    
    mock_crud = mocker.patch(
        "app.services.user_preference_notification_service.crud.batch_delete_notifications",
        new_callable=AsyncMock,
        return_value=2,  # 删除了2条通知
    )
    
    result = await service.batch_delete_notifications(delete_request, admin_role)
    
    mock_crud.assert_awaited_once_with(
        mock_db,
        notification_ids=delete_request.notification_ids,
        delete_before=delete_request.delete_before,
        notification_type=delete_request.notification_type,
        is_read=delete_request.is_read,
    )
    mock_db.commit.assert_awaited_once()
    assert isinstance(result, dict)
    assert result["deleted_count"] == 2


@pytest.mark.asyncio
async def test_batch_delete_notifications_permission_denied(mocker):
    """测试批量删除通知（权限不足）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    regular_role = "REGULAR"  # 普通用户，无权操作
    
    delete_request = NotificationBatchDeleteRequest(
        notification_ids=[uuid.uuid4()],
    )
    
    with pytest.raises(PermissionDeniedException) as exc_info:
        await service.batch_delete_notifications(delete_request, regular_role)
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)


@pytest.mark.asyncio
async def test_batch_delete_notifications_exception_rollback(mocker):
    """测试批量删除通知异常时回滚"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    admin_role = "ADMIN"
    
    delete_request = NotificationBatchDeleteRequest(
        notification_ids=[uuid.uuid4()],
    )
    
    mocker.patch(
        "app.services.user_preference_notification_service.crud.batch_delete_notifications",
        new_callable=AsyncMock,
        side_effect=Exception("数据库错误"),
    )
    
    with pytest.raises(Exception):
        await service.batch_delete_notifications(delete_request, admin_role)
    
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_admin_permission_allows_admin(mocker):
    """测试权限检查（允许ADMIN）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    
    # ADMIN和SUPERADMIN应该通过
    service._check_admin_permission("ADMIN")
    service._check_admin_permission("SUPERADMIN")
    
    # 不应该抛出异常
    assert True


@pytest.mark.asyncio
async def test_check_admin_permission_denies_regular(mocker):
    """测试权限检查（拒绝REGULAR）"""
    mock_db = AsyncMock()
    service = UserPreferenceNotificationService(mock_db)
    
    with pytest.raises(PermissionDeniedException) as exc_info:
        service._check_admin_permission("REGULAR")
    
    assert "权限不足，需要管理员权限" in str(exc_info.value)
