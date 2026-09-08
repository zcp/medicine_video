import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room, session as crud_session
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.schemas.live_core import LiveRoomCreate, LiveSessionCreate


async def create_test_room(db: AsyncSession, title: Optional[str] = "Test Room") -> LiveRoom:
    """
    在数据库中创建一个测试用的 LiveRoom 并返回其 ORM 对象。
    """
    # 生成一个测试用户ID
    test_user_id = uuid.uuid4()
    
    room_in = LiveRoomCreate(title=title, description="A room for testing")
    room = await crud_room.create(db, obj_in=room_in, user_id=test_user_id)
    return room


async def create_test_session(
    db: AsyncSession, room_id: uuid.UUID, status: LiveSessionStatus
) -> LiveSession:
    """
    在数据库中创建一个具有指定状态的 LiveSession 并返回其 ORM 对象。
    """
    from datetime import datetime, timezone

    session_in = LiveSessionCreate(
        room_id=room_id, status=status, start_time=datetime.now(timezone.utc)
    )
    # 使用 create_with_stats 以确保关联的统计数据也被创建
    session = await crud_session.create_with_stats(db, obj_in=session_in)
    return session 