# conftest_backup.py (Corrected Version)

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from uuid import uuid4

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus

# 测试数据库URL
#TEST_DATABASE_URL = "postgresql+asyncpg://postgres:324zq999@localhost:5432/media_download_test"

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "media_download_test")

# 异步连接字符串（用于应用）
TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


# 创建测试数据库引擎
engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# 创建异步会话工厂
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """在测试会话开始时创建所有表，在结束时删除所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

"""
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # 为每个测试提供一个独立的、可回滚的数据库会话
    async with async_session_factory() as session:
        yield session
        await session.rollback()
"""
# conftest_backup.py (请用这个版本替换)

import pytest
import traceback # 导入 traceback 模块

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    【调试版本】为每个测试提供一个独立的、可回滚的数据库会话
    """
    print("\n--- [DEBUG] Entering db_session fixture ---")
    try:
        print("--- [DEBUG] Attempting to create a new async session... ---")
        async with async_session_factory() as session:
            print("--- [DEBUG] SUCCESS: Session created. Yielding it to the test. ---")
            yield session
            print("--- [DEBUG] Test finished. Rolling back session. ---")
            await session.rollback()
            print("--- [DEBUG] Session rolled back. ---")

    except Exception as e:
        print("\n" + "="*80)
        print("!!! [DEBUG] CRITICAL ERROR: Failed to create database session !!!")
        print(f"!!! [DEBUG] Exception Type: {type(e).__name__}")
        print(f"!!! [DEBUG] Exception Details: {e}")
        print("!!! [DEBUG] Full Traceback:")
        traceback.print_exc()
        print("="*80 + "\n")
        # 让测试因为这个明确的错误而失败
        pytest.fail(f"Database session creation failed: {e}", pytrace=False)

@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    提供一个配置了测试数据库的、可直接使用的异步HTTP客户端。
    这是标准的、可靠的定义方式。
    """
    # 这个函数将替换应用中原始的 get_db 依赖
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # httpx.AsyncClient 本身就是一个异步上下文管理器
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 'yield' 关键字将准备好的 client 对象传递给测试函数
        yield client

    # 测试结束后，清理工作会自动执行
    app.dependency_overrides.clear()


# --- Sample Data Fixtures ---

@pytest.fixture
async def task_pending_basic_for_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            resource_type="hls",
            status=TaskStatus.PENDING
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_mp4_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.PENDING
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_completed_basic_for_mp4_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.COMPLETED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_image_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/background_ipfs.png",
            resource_type="image",
            status=TaskStatus.PENDING
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_invalid_image_url_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/background_ipfsaaa.png",
            resource_type="image",
            status=TaskStatus.PENDING
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_invalid_mp4_url_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_500000.mp4",
            resource_type="mp4",
            status=TaskStatus.PENDING
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture



@pytest.fixture
async def task_pending_basic_for_mp4_retry(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 FAILED 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.FAILED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
                expected_path=f"D:\\storage\\video_{task.video_id}\\mp4",
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_valid_mp4_url_retry_count_2(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 FAILED 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.FAILED,
            retry_count=2
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
                expected_path=f"D:\\storage\\video_{task.video_id}\\mp4",
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending",
                retry_count=2
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_invalid_mp4_url_retry_count_2(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 FAILED 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000x.mp4",
            resource_type="mp4",
            status=TaskStatus.FAILED,
            retry_count=2
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000x.mp4",
                expected_path=f"D:\\storage\\video_{task.video_id}\\mp4",
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending",
                retry_count=2
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_basic_for_invalid_mp4_url_retry_count_3(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 FAILED 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000x.mp4",
            resource_type="mp4",
            status=TaskStatus.FAILED,
            retry_count=3
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000x.mp4",
                expected_path=f"D:\\storage\\video_{task.video_id}\\mp4",
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending",
                retry_count=2
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象


@pytest.fixture
async def task_pending_basic_for_invalid_mp4_url_retry(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_500000.mp4",
            resource_type="mp4",
            status=TaskStatus.FAILED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
                expected_path=f"D:\\storage\\video_{task.video_id}\\mp4",
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象


@pytest.fixture
async def task_completed_basic_for_download(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个已完成的下载任务（COMPLETED 状态）。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_abce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            resource_type="hls",
            status=TaskStatus.COMPLETED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_pending_invalid_m3u8_for_download(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个 M3U8 文件无效的任务，用于测试首次访问失败场景。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567891_abfe",
            liveroom_id="1234567891",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist11.m3u8",
            resource_type="hls",
            status=TaskStatus.PENDING
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)
        return task  # 直接返回任务对象

@pytest.fixture
async def task_failed_valid_m3u8(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个 FAILED 状态的任务，资源地址有效，可用于模拟重试恢复。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_01ce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            resource_type="hls",
            status=TaskStatus.FAILED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
                expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
                standard_name="playlist_failure4.m3u8",
                resource_type="m3u8",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return failure2 # 直接返回任务对象


@pytest.fixture
async def task_failed_valid_m3u8_for_retry(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个 FAILED 状态的任务，资源地址有效，可用于模拟重试恢复。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_01ce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            resource_type="hls",
            status=TaskStatus.FAILED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
                expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
                standard_name="playlist_failure4.m3u8",
                resource_type="m3u8",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象

@pytest.fixture
async def task_failed_invalid_m3u8_for_retry(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个 FAILED 状态的任务，资源地址无效，可用于模拟重试恢复。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_01ee",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist_failurexxx.m3u8",
            resource_type="hls",
            status=TaskStatus.FAILED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000/playlist_failure4.m3u8",
                expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
                standard_name="playlist_failure4.m3u8",
                resource_type="m3u8",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return task  # 直接返回任务对象

@pytest.fixture
async def task_partial_completed_with_invalid_segment_for_retry(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_adce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            resource_type="hls",
            status=TaskStatus.PARTIAL_COMPLETED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        video = DownloadedVideo(
            video_id=f"{task.video_id}",
            task_id=task.id,
            liveroom_id="1234567890",
            liveroom_url= "",
            video_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            video_type="hls",
            storage_path=f"D:\\storage\\video_{task.video_id}",
            format="hls",
            status=TaskStatus.PARTIAL_COMPLETED
        )

        session.add(video)
        await session.commit()
        #await session.flush()
        await session.refresh(video)

        # 2. Create associated failure records
        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000/segment_00x.ts",
                expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
                standard_name=f"segment_000001_{task.video_id}_fetch_20250618T102153.ts",
                resource_type="ts",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return task


@pytest.fixture
async def task_failed_ts_failure_threshold_exceeded_for_retry(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个模拟 TS 文件下载失败比例过高的任务，判定为下载失败。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_11ce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist_failure4.m3u8",
            resource_type="hls",
            status=TaskStatus.PENDING
        )

        session.add(task)
        await session.commit()
        # await session.flush()
        await session.refresh(task)
        # 2. Create associated failure records

        failure1 = DownloadFailure(
            task_id=task.id,
            resource_url="https://example.com/failed/segment1.ts",
            expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
            standard_name="segment_000001_1234567890_abce_fetch_20250618T102153.ts",
            resource_type="ts",
            failure_type="network_error",
            error_message="Connection timed out on first attempt.",
            status="pending"  # The failure itself is pending a retry
        )

        failure2 = DownloadFailure(
            task_id=task.id,
            resource_url="https://lancet.im/videos/194_1080p_5000/segment_000.ts",
            expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
            standard_name="segment_000000_1234567890_abce_fetch_20250618T102153.ts",
            resource_type="ts",
            failure_type="network_error",
            error_message="Connection timed out on first attempt.",
            status="pending"
        )
        session.add_all([failure1, failure2])
        await session.commit()

        return task


@pytest.fixture
async def task_partial_completed_with_ts_failure_for_retry(db_session: AsyncSession) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id="1234567890_adce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            resource_type="hls",
            status=TaskStatus.PARTIAL_COMPLETED
        )
        session.add(task)
        await session.commit()
        #await session.flush()
        await session.refresh(task)

        video = DownloadedVideo(
            video_id=f"{task.video_id}",
            task_id=task.id,
            liveroom_id="1234567890",
            liveroom_url= "",
            video_url="https://lancet.im/videos/194_1080p_5000/playlist.m3u8",
            video_type="hls",
            storage_path=f"D:\\storage\\video_{task.video_id}",
            format="hls",
            status=TaskStatus.PARTIAL_COMPLETED
        )

        session.add(video)
        await session.commit()
        #await session.flush()
        await session.refresh(video)

        # 2. Create associated failure records
        failure2 = DownloadFailure(
                task_id=task.id,
                resource_url="https://lancet.im/videos/194_1080p_5000/segment_001.ts",
                expected_path=f"D:\\storage\\video_{task.video_id}\\hls\\ts",
                standard_name=f"segment_000001_{task.video_id}_fetch_20250618T102153.ts",
                resource_type="ts",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
        session.add_all([failure2])
        await session.commit()

        return task

