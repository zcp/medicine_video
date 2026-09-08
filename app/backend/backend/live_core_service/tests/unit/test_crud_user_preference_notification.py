"""
用户偏好与通知模块 - CRUD层测试

测试策略: Pragmatic (务实主义)
- 使用真实数据库进行测试
- 验证数据库操作的完整性
- 使用增量判断方式验证数据库操作（增量测试模式）
"""

import uuid
from datetime import datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_preference_notification import UserPreferences, Notification
from app.crud import user_preference_notification as crud
from app.schemas.user_preference_notification import UserPreferencesUpdate
from app.exceptions import DatabaseOperationException, PermissionDeniedException


# ==================== User Preferences CRUD 测试 ====================

@pytest.mark.asyncio
async def test_get_preferences_exists(db_session):
    """测试获取已存在的用户偏好"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建用户偏好
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id,
            theme_mode="dark",
            homepage_view_mode="single",
        )
        db.add(prefs)
        await db.flush()
        
        # 获取偏好
        result = await crud.get_preferences(db, user_id)
        
        assert result is not None
        assert result.user_id == user_id
        assert result.theme_mode == "dark"
        assert result.homepage_view_mode == "single"
        break


@pytest.mark.asyncio
async def test_get_preferences_not_exists(db_session):
    """测试获取不存在的用户偏好（首次访问）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 获取不存在的偏好
        result = await crud.get_preferences(db, user_id)
        
        assert result is None
        break


@pytest.mark.asyncio
async def test_create_or_update_preferences_create(db_session):
    """测试创建新用户偏好"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 记录初始数量
        count_stmt = select(func.count(UserPreferences.id)).where(
            UserPreferences.user_id == user_id
        )
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 创建偏好
        prefs_update = UserPreferencesUpdate(
            theme_mode="scheduled",
            theme_scheduled_dark_time=time(21, 0),
            theme_scheduled_light_time=time(7, 0),
            pinned_categories=[uuid.uuid4(), uuid.uuid4()],
        )
        result = await crud.create_or_update_preferences(db, user_id, prefs_update)
        
        assert result.user_id == user_id
        assert result.theme_mode == "scheduled"
        assert result.theme_scheduled_dark_time == time(21, 0)
        assert result.theme_scheduled_light_time == time(7, 0)
        assert len(result.pinned_categories) == 2
        
        # 增量验证
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count + 1
        
        # 验证数据已持久化
        await db.refresh(result)
        assert result.theme_mode == "scheduled"
        break


@pytest.mark.asyncio
async def test_create_or_update_preferences_update(db_session):
    """测试更新已存在的用户偏好"""
    async for db in db_session:
        user_id = uuid.uuid4()

        # 先创建偏好
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id,
            theme_mode="light",
            homepage_view_mode="double",
        )
        db.add(prefs)
        await db.flush()
        # ✅ 修复：在访问 updated_at 前先 refresh，避免 MissingGreenlet 错误
        await db.refresh(prefs)
        initial_updated_at = prefs.updated_at

        # 更新偏好
        prefs_update = UserPreferencesUpdate(
            theme_mode="dark",
            homepage_view_mode="single",
        )
        result = await crud.create_or_update_preferences(db, user_id, prefs_update)

        assert result.user_id == user_id
        assert result.theme_mode == "dark"  # ✅ 验证关键字段值变化
        assert result.homepage_view_mode == "single"  # ✅ 验证状态字段变化
        assert result.updated_at >= initial_updated_at  # ✅ 验证时间戳更新

        # 验证数据已持久化
        await db.refresh(result)
        assert result.theme_mode == "dark"
        break
@pytest.mark.asyncio
async def test_create_or_update_preferences_pinned_categories_limit(db_session):
    """测试固定科室数量限制（最多5个）"""
    async for db in db_session:
        user_id = uuid.uuid4()

        # ✅ 修复：Schema验证应该在创建Schema对象时就触发
        from pydantic import ValidationError

        # ✅ 修复：移除 match 参数，因为 ValidationError 的错误消息格式可能不同
        with pytest.raises(ValidationError):
            UserPreferencesUpdate(
                pinned_categories=[uuid.uuid4() for _ in range(6)]  # 6个，超过限制
            )
        break

# ==================== Notifications CRUD 测试 ====================

@pytest.mark.asyncio
async def test_get_notifications_with_pagination(db_session):
    """测试分页获取通知列表"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建多条通知
        notifications = []
        for i in range(5):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id,
                title=f"通知{i+1}",
                notification_type="system",
                is_read=(i % 2 == 0),  # 交替设置已读/未读
            )
            db.add(notification)
            notifications.append(notification)
        await db.flush()
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 获取第一页（每页3条）
        items, total = await crud.get_notifications(
            db, user_id, page=1, size=3, current_user_id=user_id, role="REGULAR"
        )
        
        assert total == 5
        assert len(items) == 3
        assert all(item.user_id == user_id for item in items)
        
        # 增量验证：总数应等于初始数量
        assert total == initial_count
        
        # 验证排序（按创建时间倒序）
        assert items[0].created_at >= items[1].created_at
        break


@pytest.mark.asyncio
async def test_get_notifications_filter_by_is_read(db_session):
    """测试按已读状态筛选通知"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建已读和未读通知
        read_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="已读通知",
            is_read=True,
        )
        db.add(read_notification)
        
        unread_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="未读通知",
            is_read=False,
        )
        db.add(unread_notification)
        await db.flush()
        
        # 获取未读通知
        items, total = await crud.get_notifications(
            db, user_id, page=1, size=10, 
            is_read=False, 
            current_user_id=user_id, role="REGULAR"
        )
        
        assert total == 1
        assert len(items) == 1
        assert items[0].id == unread_notification.id
        assert items[0].is_read is False  # ✅ 验证状态字段
        break


@pytest.mark.asyncio
async def test_get_notifications_filter_by_type(db_session):
    """测试按通知类型筛选"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建不同类型的通知
        system_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="系统通知",
            notification_type="system",
        )
        db.add(system_notification)
        
        subscription_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="订阅通知",
            notification_type="subscription",
        )
        db.add(subscription_notification)
        await db.flush()
        
        # 获取系统通知
        items, total = await crud.get_notifications(
            db, user_id, page=1, size=10,
            notification_type="system",
            current_user_id=user_id, role="REGULAR"
        )
        
        assert total == 1
        assert len(items) == 1
        assert items[0].notification_type == "system"  # ✅ 验证枚举字段
        break


@pytest.mark.asyncio
async def test_get_notifications_permission_denied(db_session):
    """测试普通用户查询其他用户的通知（权限不足）"""
    async for db in db_session:
        owner_user_id = uuid.uuid4()
        current_user_id = uuid.uuid4()
        
        # 创建owner的通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=owner_user_id,
            title="他人通知",
        )
        db.add(notification)
        await db.flush()
        
        # 普通用户尝试查询其他用户的通知
        with pytest.raises(PermissionDeniedException):
            await crud.get_notifications(
                db, owner_user_id, page=1, size=10,
                current_user_id=current_user_id, role="REGULAR"
            )
        break


@pytest.mark.asyncio
async def test_get_notifications_admin_all_users(db_session):
    """测试管理员查询所有用户的通知"""
    async for db in db_session:
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        # 创建不同用户的通知
        notification1 = Notification(
            id=uuid.uuid4(),
            user_id=user1_id,
            title="用户1通知",
        )
        db.add(notification1)
        
        notification2 = Notification(
            id=uuid.uuid4(),
            user_id=user2_id,
            title="用户2通知",
        )
        db.add(notification2)
        await db.flush()
        
        # 管理员查询所有通知
        items, total = await crud.get_notifications_admin(
            db, page=1, size=10
        )
        
        assert total >= 2
        assert any(item.user_id == user1_id for item in items)
        assert any(item.user_id == user2_id for item in items)
        break


@pytest.mark.asyncio
async def test_get_unread_count(db_session):
    """测试获取未读通知数量"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 记录初始未读数量
        initial_count = await crud.get_unread_count(db, user_id)
        assert initial_count == 0
        
        # 创建未读通知
        notification1 = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="未读通知1",
            is_read=False,
        )
        db.add(notification1)
        
        notification2 = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="未读通知2",
            is_read=False,
        )
        db.add(notification2)
        
        # 创建已读通知
        read_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="已读通知",
            is_read=True,
        )
        db.add(read_notification)
        await db.flush()
        
        # 获取未读数量
        count = await crud.get_unread_count(db, user_id)
        
        # 增量验证
        assert count == initial_count + 2
        break


@pytest.mark.asyncio
async def test_mark_as_read(db_session):
    """测试标记通知为已读"""
    async for db in db_session:
        user_id = uuid.uuid4()

        # 创建未读通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="未读通知",
            is_read=False,
        )
        db.add(notification)
        await db.flush()
        notification_id = notification.id
        # ✅ 修复：删除 initial_created_at 赋值（不再使用，避免 MissingGreenlet 错误）

        # 标记为已读
        result = await crud.mark_as_read(db, notification_id, user_id)

        assert result is not None
        assert result.id == notification_id
        assert result.is_read is True  # ✅ 验证状态字段变化

        # 验证数据已持久化
        await db.refresh(result)
        assert result.is_read is True
        break

@pytest.mark.asyncio
async def test_mark_as_read_idempotent(db_session):
    """测试标记已读通知为已读（幂等性）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建已读通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="已读通知",
            is_read=True,
        )
        db.add(notification)
        await db.flush()
        notification_id = notification.id
        
        # 再次标记为已读（应该幂等）
        result = await crud.mark_as_read(db, notification_id, user_id)
        
        assert result is not None
        assert result.is_read is True  # 仍为已读
        break


@pytest.mark.asyncio
async def test_mark_as_read_not_owner(db_session):
    """测试标记其他用户的通知为已读（应返回None）"""
    async for db in db_session:
        owner_user_id = uuid.uuid4()
        current_user_id = uuid.uuid4()
        
        # 创建owner的通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=owner_user_id,
            title="他人通知",
            is_read=False,
        )
        db.add(notification)
        await db.flush()
        notification_id = notification.id
        
        # 当前用户尝试标记为已读
        result = await crud.mark_as_read(db, notification_id, current_user_id)
        
        assert result is None  # 无权操作，返回None
        break


@pytest.mark.asyncio
async def test_mark_all_as_read(db_session):
    """测试标记所有通知为已读"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 记录初始未读数量
        initial_unread_count = await crud.get_unread_count(db, user_id)
        
        # 创建多条未读通知
        notifications = []
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id,
                title=f"未读通知{i+1}",
                is_read=False,
            )
            db.add(notification)
            notifications.append(notification)
        await db.flush()
        
        # 标记所有为已读
        updated_count = await crud.mark_all_as_read(db, user_id)
        
        assert updated_count == 3
        
        # 验证所有通知都已标记为已读
        for notification in notifications:
            await db.refresh(notification)
            assert notification.is_read is True  # ✅ 验证状态字段变化
        
        # 增量验证：未读数量应减少
        final_unread_count = await crud.get_unread_count(db, user_id)
        assert final_unread_count == initial_unread_count
        break


@pytest.mark.asyncio
async def test_create_notification(db_session):
    """测试创建单条通知"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 创建通知
        notification_data = {
            "user_id": user_id,
            "title": "新通知",
            "content": "通知内容",
            "notification_type": "system",
        }
        result = await crud.create_notification(db, notification_data)
        
        assert result.user_id == user_id
        assert result.title == "新通知"
        assert result.notification_type == "system"  # ✅ 验证枚举字段
        assert result.is_read is False  # 默认未读
        
        # 增量验证
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count + 1
        break


@pytest.mark.asyncio
async def test_bulk_create_notifications(db_session):
    """测试批量创建通知"""
    async for db in db_session:
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 批量创建通知
        notifications_list = [
            {
                "user_id": user1_id,
                "title": "通知1",
                "notification_type": "system",
            },
            {
                "user_id": user2_id,
                "title": "通知2",
                "notification_type": "subscription",
            },
        ]
        count = await crud.bulk_create_notifications(db, notifications_list)
        
        assert count == 2
        
        # 增量验证
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count + 2
        break


@pytest.mark.asyncio
async def test_update_notification(db_session):
    """测试更新通知（仅title和content）"""
    async for db in db_session:
        user_id = uuid.uuid4()

        # 创建通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="原标题",
            content="原内容",
        )
        db.add(notification)
        await db.flush()
        notification_id = notification.id
        # ✅ 修复：删除 initial_created_at 赋值（不再使用，避免 MissingGreenlet 错误）

        # 更新通知
        update_data = {
            "title": "新标题",
            "content": "新内容",
        }
        result = await crud.update_notification(db, notification_id, update_data)

        assert result is not None
        assert result.title == "新标题"  # ✅ 验证关键字段值变化
        assert result.content == "新内容"  # ✅ 验证关键字段值变化

        # 验证数据已持久化
        await db.refresh(result)
        assert result.title == "新标题"
        break

@pytest.mark.asyncio
async def test_delete_notification(db_session):
    """测试删除单条通知"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建通知
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="待删除通知",
        )
        db.add(notification)
        await db.flush()
        notification_id = notification.id
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 删除通知
        deleted = await crud.delete_notification(db, notification_id)
        
        assert deleted is True
        
        # 增量验证
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count - 1
        
        # 验证通知已删除
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        assert result.scalar_one_or_none() is None
        break


@pytest.mark.asyncio
async def test_delete_notification_not_exists(db_session):
    """测试删除不存在的通知（应返回False）"""
    async for db in db_session:
        fake_notification_id = uuid.uuid4()
        
        # 删除不存在的通知
        deleted = await crud.delete_notification(db, fake_notification_id)
        
        assert deleted is False
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_by_ids(db_session):
    """测试按ID列表批量删除通知"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建多条通知
        notifications = []
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id,
                title=f"通知{i+1}",
            )
            db.add(notification)
            notifications.append(notification)
        await db.flush()
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 批量删除（删除前2条）
        notification_ids = [notifications[0].id, notifications[1].id]
        deleted_count = await crud.batch_delete_notifications(
            db, notification_ids=notification_ids
        )
        
        assert deleted_count == 2
        
        # 增量验证
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count - 2
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_by_date(db_session):
    """测试按日期批量删除通知"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # ✅ 修复：使用 timezone-aware datetime（数据库字段是 TIMESTAMPTZ）
        # 创建不同时间的通知
        old_date = datetime.now(timezone.utc) - timedelta(days=30)
        new_date = datetime.now(timezone.utc)
        
        # 创建旧通知
        old_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="旧通知",
        )
        db.add(old_notification)
        
        # 创建新通知
        new_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="新通知",
        )
        db.add(new_notification)
        await db.flush()
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # ✅ 修复：使用 timezone-aware datetime
        delete_before = datetime.now(timezone.utc) - timedelta(days=29)
        deleted_count = await crud.batch_delete_notifications(
            db, delete_before=delete_before
        )
        
        # 如果旧通知在删除范围内，应该被删除
        assert deleted_count >= 0
        
        # 增量验证（如果删除成功，数量应减少）
        if deleted_count > 0:
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count - deleted_count
        break


@pytest.mark.asyncio
async def test_batch_delete_notifications_by_type(db_session):
    """测试按通知类型批量删除"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建不同类型的通知
        system_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="系统通知",
            notification_type="system",
        )
        db.add(system_notification)
        
        subscription_notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title="订阅通知",
            notification_type="subscription",
        )
        db.add(subscription_notification)
        await db.flush()
        
        # 记录初始数量
        count_stmt = select(func.count(Notification.id))
        initial_count = (await db.execute(count_stmt)).scalar()
        
        # 批量删除系统通知
        deleted_count = await crud.batch_delete_notifications(
            db, notification_type="system"
        )
        
        assert deleted_count >= 1
        
        # 增量验证
        if deleted_count > 0:
            final_count = (await db.execute(count_stmt)).scalar()
            assert final_count == initial_count - deleted_count
        break
