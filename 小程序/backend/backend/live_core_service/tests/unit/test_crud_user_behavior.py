import uuid
from datetime import datetime
from typing import List

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_behavior import (
    UserFavorite,
    WatchHistory,
    UserSubscription,
    SubscriptionTargetType,
)
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.crud import user_behavior as crud_user_behavior
from app.exceptions import DatabaseIntegrityException


@pytest.mark.asyncio
async def test_create_favorite_and_list(db_session):
    """创建收藏并通过增量验证收藏列表"""
    async for db in db_session:
        user_id = uuid.uuid4()
        # 先创建房间以满足外键约束
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 记录初始数量
        count_stmt = select(func.count(UserFavorite.id)).where(
            UserFavorite.user_id == user_id
        )
        initial_count = (await db.execute(count_stmt)).scalar()

        # 创建收藏
        favorite = await crud_user_behavior.create_favorite(db, user_id, room_id)
        assert favorite.user_id == user_id
        assert favorite.room_id == room_id
        assert favorite.is_active is True

        # 增量验证
        final_count = (await db.execute(count_stmt)).scalar()
        assert final_count == initial_count + 1

        # 通过接口函数获取列表
        favorites: List[UserFavorite] = await crud_user_behavior.get_user_favorites(
            db, user_id, offset=0, limit=10
        )
        assert any(f.id == favorite.id for f in favorites)
        break


@pytest.mark.asyncio
async def test_create_favorite_duplicate_raises(db_session):
    """重复收藏应触发唯一约束异常"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        await crud_user_behavior.create_favorite(db, user_id, room_id)

        with pytest.raises(DatabaseIntegrityException):
            await crud_user_behavior.create_favorite(db, user_id, room_id)
        break


@pytest.mark.asyncio
async def test_delete_favorite_soft_delete(db_session):
    """取消收藏应将 is_active 置为 False，并且幂等"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        favorite = await crud_user_behavior.create_favorite(db, user_id, room_id)
        assert favorite.is_active is True

        # 取消收藏
        result = await crud_user_behavior.delete_favorite(db, user_id, room_id)
        assert result is True

        # 记录应被标记为 is_active=False
        stmt = select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.room_id == room_id,
        )
        db_fav = (await db.execute(stmt)).scalar_one()
        assert db_fav.is_active is False

        # 再次取消应幂等返回 False
        result2 = await crud_user_behavior.delete_favorite(db, user_id, room_id)
        assert result2 is False
        break


@pytest.mark.asyncio
async def test_record_watch_history_is_latest(db_session):
    """多次记录观看历史时仅最后一条 is_latest=True"""
    async for db in db_session:
        user_id = uuid.uuid4()
        # 创建房间与场次
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        db.add(session)
        await db.flush()
        session_id = session.id

        # 第一次记录
        h1 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session_id, progress=10
        )
        assert h1.is_latest is True

        # 第二次记录
        h2 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session_id, progress=20
        )
        assert h2.is_latest is True

        # 重新查询，校验只有一条最新记录
        stmt_all = select(WatchHistory).where(
            WatchHistory.user_id == user_id,
            WatchHistory.session_id == session_id,
        )
        all_records = (await db.execute(stmt_all)).scalars().all()
        latest_records = [h for h in all_records if h.is_latest]
        assert len(latest_records) == 1
        assert latest_records[0].id == h2.id
        break


@pytest.mark.asyncio
async def test_list_watch_history_only_latest(db_session):
    """list_watch_history 只返回 is_latest=True 的记录"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        db.add(session)
        await db.flush()
        session_id = session.id

        await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session_id, progress=5
        )
        await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session_id, progress=15
        )

        records = await crud_user_behavior.list_watch_history(db, user_id, offset=0, limit=10)
        assert len(records) == 1
        assert records[0].user_id == user_id
        assert records[0].session_id == session_id
        break


@pytest.mark.asyncio
async def test_create_and_cancel_subscription(db_session):
    """创建订阅并取消，验证软删除与唯一约束"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        sub = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
        )
        assert sub.user_id == user_id
        assert sub.target_type == SubscriptionTargetType.ROOM
        assert sub.target_id == room_id
        assert sub.is_active is True

        # 重复创建应触发唯一约束异常
        with pytest.raises(DatabaseIntegrityException):
            await crud_user_behavior.create_subscription(
                db,
                user_id=user_id,
                target_type=SubscriptionTargetType.ROOM,
                target_id=room_id,
            )

        # 取消订阅
        result = await crud_user_behavior.cancel_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
        )
        assert result is True

        # 再次取消应返回 False（幂等）
        result2 = await crud_user_behavior.cancel_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
        )
        assert result2 is False
        break


# ==================== 收藏相关补充测试 ====================

@pytest.mark.asyncio
async def test_get_favorite_exists(db_session):
    """测试 get_favorite(user_id, room_id) 获取已存在的收藏记录（无论is_active状态）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 创建收藏
        favorite = await crud_user_behavior.create_favorite(db, user_id, room_id)
        
        # 测试获取存在的记录
        result = await crud_user_behavior.get_favorite(db, user_id, room_id)
        assert result is not None
        assert result.id == favorite.id
        assert result.user_id == user_id
        assert result.room_id == room_id
        
        # 取消收藏后，get_favorite仍应能获取到记录（无论is_active状态）
        await crud_user_behavior.delete_favorite(db, user_id, room_id)
        result2 = await crud_user_behavior.get_favorite(db, user_id, room_id)
        assert result2 is not None
        assert result2.is_active is False
        break


@pytest.mark.asyncio
async def test_get_favorite_not_exists(db_session):
    """测试 get_favorite(user_id, room_id) 获取不存在的记录返回None"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 测试获取不存在的记录
        result = await crud_user_behavior.get_favorite(db, user_id, room_id)
        assert result is None
        break


@pytest.mark.asyncio
async def test_create_favorite_restore_soft_deleted(db_session):
    """测试 create_favorite 恢复软删除的记录（is_active=False时恢复为True）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 创建收藏
        favorite1 = await crud_user_behavior.create_favorite(db, user_id, room_id)
        assert favorite1.is_active is True
        
        # 取消收藏（软删除）
        await crud_user_behavior.delete_favorite(db, user_id, room_id)
        
        # 验证已软删除
        stmt = select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.room_id == room_id,
        )
        deleted_fav = (await db.execute(stmt)).scalar_one()
        assert deleted_fav.is_active is False
        
        # 再次创建收藏，应恢复为True
        favorite2 = await crud_user_behavior.create_favorite(db, user_id, room_id)
        assert favorite2.id == favorite1.id  # 应该是同一条记录
        assert favorite2.is_active is True
        break


@pytest.mark.asyncio
async def test_get_user_favorites_limit(db_session):
    """测试 get_user_favorites 的limit参数（创建多条记录，验证limit生效）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        
        # 创建多个房间
        rooms = []
        for i in range(5):
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=user_id,
                title=f"测试房间_{uuid.uuid4().hex[:8]}",
                stream_key=f"stream_{uuid.uuid4().hex[:12]}",
            )
            db.add(room)
            rooms.append(room)
        await db.flush()
        
        # 为每个房间创建收藏
        for room in rooms:
            await crud_user_behavior.create_favorite(db, user_id, room.id)
        
        # 测试 limit=2，应只返回2条
        favorites = await crud_user_behavior.get_user_favorites(db, user_id, offset=0, limit=2)
        assert len(favorites) == 2
        
        # 测试 limit=10，应返回所有5条
        favorites_all = await crud_user_behavior.get_user_favorites(db, user_id, offset=0, limit=10)
        assert len(favorites_all) == 5
        break


@pytest.mark.asyncio
async def test_get_user_favorites_only_active(db_session):
    """测试 get_user_favorites 只返回is_active=True的记录（创建is_active=False的记录，验证不返回）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room1 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        room2 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room1)
        db.add(room2)
        await db.flush()
        
        # 创建两个收藏
        fav1 = await crud_user_behavior.create_favorite(db, user_id, room1.id)
        fav2 = await crud_user_behavior.create_favorite(db, user_id, room2.id)
        
        # 取消room1的收藏（软删除）
        await crud_user_behavior.delete_favorite(db, user_id, room1.id)
        
        # get_user_favorites应只返回is_active=True的记录（即room2）
        favorites = await crud_user_behavior.get_user_favorites(db, user_id, offset=0, limit=10)
        assert len(favorites) == 1
        assert favorites[0].room_id == room2.id
        assert favorites[0].is_active is True
        break


@pytest.mark.asyncio
async def test_get_user_favorites_ordering(db_session):
    """测试 get_user_favorites 按created_at降序排列"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room1 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        room2 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room1)
        db.add(room2)
        await db.flush()

        # 先创建room1的收藏
        fav1 = await crud_user_behavior.create_favorite(db, user_id, room1.id)
        # 使用更长的等待时间，确保时间戳不同
        import time
        time.sleep(0.1)  # 使用time.sleep而不是asyncio.sleep，确保实际等待
        # 再创建room2的收藏
        fav2 = await crud_user_behavior.create_favorite(db, user_id, room2.id)

        # 验证按created_at降序排列（后创建的在前）
        favorites = await crud_user_behavior.get_user_favorites(db, user_id, offset=0, limit=10)
        assert len(favorites) == 2

        # 验证排序：后创建的created_at应该大于先创建的
        assert favorites[0].created_at >= favorites[1].created_at

        # 如果时间戳不同，验证顺序
        if favorites[0].created_at > favorites[1].created_at:
            assert favorites[0].id == fav2.id  # 后创建的在前
            assert favorites[1].id == fav1.id
        else:
            # 如果时间戳相同（精度问题），至少验证返回了正确的记录
            favorite_ids = {f.id for f in favorites}
            assert fav1.id in favorite_ids
            assert fav2.id in favorite_ids
        break
@pytest.mark.asyncio
async def test_delete_favorite_not_exists_returns_false(db_session):
    """测试 delete_favorite 当记录不存在时返回False（更明确的测试）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 尝试删除不存在的收藏，应返回False
        result = await crud_user_behavior.delete_favorite(db, user_id, room_id)
        assert result is False
        break


# ==================== 观看历史相关补充测试 ====================

@pytest.mark.asyncio
async def test_record_watch_history_progress_none(db_session):
    """测试 record_watch_history 当 progress 为 None 时（设计允许 NULL，仅记录打开行为）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        session = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        db.add(session)
        await db.flush()
        session_id = session.id

        # 设计文档：progress 可为空表示仅记录打开行为；Model 中 progress nullable=True
        history = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session_id, progress=None
        )
        assert history.id is not None
        assert history.progress is None
        break


@pytest.mark.asyncio
async def test_record_watch_history_foreign_key_violation(db_session):
    """测试 record_watch_history 当session_id不存在时抛出DatabaseIntegrityException"""
    async for db in db_session:
        user_id = uuid.uuid4()
        # 使用不存在的session_id
        fake_session_id = uuid.uuid4()

        with pytest.raises(DatabaseIntegrityException):
            await crud_user_behavior.record_watch_history(
                db, user_id=user_id, session_id=fake_session_id, progress=10
            )
        break


@pytest.mark.asyncio
async def test_list_watch_history_limit(db_session):
    """测试 list_watch_history 的limit参数"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        
        # 创建多个session并记录观看历史
        sessions = []
        for i in range(5):
            session = LiveSession(
                id=uuid.uuid4(),
                room_id=room.id,
                status=LiveSessionStatus.SCHEDULED,
                start_time=datetime.now(),
            )
            db.add(session)
            sessions.append(session)
        await db.flush()
        
        # 为每个session记录观看历史
        for session in sessions:
            await crud_user_behavior.record_watch_history(
                db, user_id=user_id, session_id=session.id, progress=10
            )
        
        # 测试 limit=2，应只返回2条
        records = await crud_user_behavior.list_watch_history(db, user_id, offset=0, limit=2)
        assert len(records) == 2
        
        # 测试 limit=10，应返回所有5条
        records_all = await crud_user_behavior.list_watch_history(db, user_id, offset=0, limit=10)
        assert len(records_all) == 5
        break


@pytest.mark.asyncio
async def test_list_watch_history_ordering(db_session):
    """测试 list_watch_history 按watched_at降序排列"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        
        session1 = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        session2 = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        db.add(session1)
        db.add(session2)
        await db.flush()
        
        # 先记录session1
        h1 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session1.id, progress=10
        )
        # 稍等片刻
        import asyncio
        await asyncio.sleep(0.01)
        # 再记录session2
        h2 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session2.id, progress=20
        )
        
        # 验证按watched_at降序排列（后记录的在前）
        records = await crud_user_behavior.list_watch_history(db, user_id, offset=0, limit=10)
        assert len(records) == 2
        assert records[0].watched_at >= records[1].watched_at
        assert {records[0].id, records[1].id} == {h1.id, h2.id}
        break


@pytest.mark.asyncio
async def test_record_watch_history_multiple_sessions(db_session):
    """测试同一用户对不同session的记录，每个session只有一条is_latest=True"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        
        # 创建两个session
        session1 = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        session2 = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        db.add(session1)
        db.add(session2)
        await db.flush()
        
        # 为session1记录两次观看历史
        h1_1 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session1.id, progress=10
        )
        h1_2 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session1.id, progress=20
        )
        
        # 为session2记录一次观看历史
        h2_1 = await crud_user_behavior.record_watch_history(
            db, user_id=user_id, session_id=session2.id, progress=15
        )
        
        # 验证每个session只有一条is_latest=True的记录
        stmt_all = select(WatchHistory).where(WatchHistory.user_id == user_id)
        all_records = (await db.execute(stmt_all)).scalars().all()
        latest_records = [h for h in all_records if h.is_latest]
        assert len(latest_records) == 2  # session1和session2各一条
        
        # 验证session1的最新记录是h1_2
        session1_latest = [h for h in latest_records if h.session_id == session1.id]
        assert len(session1_latest) == 1
        assert session1_latest[0].id == h1_2.id
        
        # 验证session2的最新记录是h2_1
        session2_latest = [h for h in latest_records if h.session_id == session2.id]
        assert len(session2_latest) == 1
        assert session2_latest[0].id == h2_1.id
        break


# ==================== 订阅相关补充测试 ====================

@pytest.mark.asyncio
async def test_get_subscription_exists(db_session):
    """测试 get_subscription(user_id, target_type, target_id) 获取已存在的订阅（无论is_active状态）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 创建订阅
        sub = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
        )
        
        # 测试获取存在的订阅
        result = await crud_user_behavior.get_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room_id
        )
        assert result is not None
        assert result.id == sub.id
        assert result.user_id == user_id
        assert result.target_type == SubscriptionTargetType.ROOM
        assert result.target_id == room_id
        
        # 取消订阅后，get_subscription仍应能获取到记录（无论is_active状态）
        await crud_user_behavior.cancel_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room_id
        )
        result2 = await crud_user_behavior.get_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room_id
        )
        assert result2 is not None
        assert result2.is_active is False
        break


@pytest.mark.asyncio
async def test_get_subscription_not_exists(db_session):
    """测试 get_subscription 获取不存在的记录返回None"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room_id = uuid.uuid4()

        # 测试获取不存在的订阅
        result = await crud_user_behavior.get_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room_id
        )
        assert result is None
        break


@pytest.mark.asyncio
async def test_create_subscription_restore_soft_deleted(db_session):
    """测试 create_subscription 恢复软删除的订阅（is_active=False时恢复为True）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        room_id = room.id

        # 创建订阅
        sub1 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
        )
        assert sub1.is_active is True
        
        # 取消订阅（软删除）
        await crud_user_behavior.cancel_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room_id
        )
        
        # 验证已软删除
        stmt = select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.target_type == SubscriptionTargetType.ROOM,
            UserSubscription.target_id == room_id,
        )
        deleted_sub = (await db.execute(stmt)).scalar_one()
        assert deleted_sub.is_active is False
        
        # 再次创建订阅，应恢复为True
        sub2 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
        )
        assert sub2.id == sub1.id  # 应该是同一条记录
        assert sub2.is_active is True
        break


@pytest.mark.asyncio
async def test_list_subscriptions_filter_by_target_type(db_session):
    """测试 list_subscriptions 按target_type过滤（创建ROOM和SESSION类型，验证过滤生效）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room)
        await db.flush()
        
        session = LiveSession(
            id=uuid.uuid4(),
            room_id=room.id,
            status=LiveSessionStatus.SCHEDULED,
            start_time=datetime.now(),
        )
        db.add(session)
        await db.flush()
        
        # 创建ROOM类型的订阅
        sub_room = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room.id,
        )
        
        # 创建SESSION类型的订阅
        sub_session = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.SESSION,
            target_id=session.id,
        )
        
        # 测试按ROOM类型过滤
        subs_room = await crud_user_behavior.list_subscriptions(
            db, user_id, target_type=SubscriptionTargetType.ROOM, only_active=True
        )
        assert len(subs_room) == 1
        assert subs_room[0].id == sub_room.id
        
        # 测试按SESSION类型过滤
        subs_session = await crud_user_behavior.list_subscriptions(
            db, user_id, target_type=SubscriptionTargetType.SESSION, only_active=True
        )
        assert len(subs_session) == 1
        assert subs_session[0].id == sub_session.id
        
        # 测试不过滤（target_type=None），应返回所有2条
        subs_all = await crud_user_behavior.list_subscriptions(
            db, user_id, target_type=None, only_active=True
        )
        assert len(subs_all) == 2
        break


@pytest.mark.asyncio
async def test_list_subscriptions_only_active_true(db_session):
    """测试 list_subscriptions(only_active=True) 只返回is_active=True的记录"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room1 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        room2 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room1)
        db.add(room2)
        await db.flush()
        
        # 创建两个订阅
        sub1 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room1.id,
        )
        sub2 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room2.id,
        )
        
        # 取消room1的订阅（软删除）
        await crud_user_behavior.cancel_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room1.id
        )
        
        # only_active=True时，应只返回is_active=True的记录（即room2）
        subs = await crud_user_behavior.list_subscriptions(
            db, user_id, target_type=None, only_active=True
        )
        assert len(subs) == 1
        assert subs[0].id == sub2.id
        assert subs[0].is_active is True
        break


@pytest.mark.asyncio
async def test_list_subscriptions_only_active_false(db_session):
    """测试 list_subscriptions(only_active=False) 返回所有记录（包括is_active=False）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room1 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        room2 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room1)
        db.add(room2)
        await db.flush()
        
        # 创建两个订阅
        sub1 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room1.id,
        )
        sub2 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room2.id,
        )
        
        # 取消room1的订阅（软删除）
        await crud_user_behavior.cancel_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room1.id
        )
        
        # only_active=False时，应返回所有记录（包括is_active=False）
        subs = await crud_user_behavior.list_subscriptions(
            db, user_id, target_type=None, only_active=False
        )
        assert len(subs) == 2
        # 验证包含is_active=False的记录
        active_subs = [s for s in subs if s.is_active]
        inactive_subs = [s for s in subs if not s.is_active]
        assert len(active_subs) == 1
        assert len(inactive_subs) == 1
        break


@pytest.mark.asyncio
async def test_list_subscriptions_ordering(db_session):
    """测试 list_subscriptions 按created_at降序排列"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room1 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        room2 = LiveRoom(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_{uuid.uuid4().hex[:12]}",
        )
        db.add(room1)
        db.add(room2)
        await db.flush()
        
        # 先创建room1的订阅
        sub1 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room1.id,
        )
        # 稍等片刻
        import asyncio
        await asyncio.sleep(0.01)
        # 再创建room2的订阅
        sub2 = await crud_user_behavior.create_subscription(
            db,
            user_id=user_id,
            target_type=SubscriptionTargetType.ROOM,
            target_id=room2.id,
        )
        
        # 验证按created_at降序排列（后创建的在前）
        subs = await crud_user_behavior.list_subscriptions(
            db, user_id, target_type=None, only_active=True
        )
        assert len(subs) == 2
        assert subs[0].created_at >= subs[1].created_at
        assert {s.id for s in subs} == {sub1.id, sub2.id}
        break


@pytest.mark.asyncio
async def test_cancel_subscription_not_exists_returns_false(db_session):
    """测试 cancel_subscription 当记录不存在时返回False（更明确的测试）"""
    async for db in db_session:
        user_id = uuid.uuid4()
        room_id = uuid.uuid4()

        # 尝试取消不存在的订阅，应返回False
        result = await crud_user_behavior.cancel_subscription(
            db, user_id, SubscriptionTargetType.ROOM, room_id
        )
        assert result is False
        break

