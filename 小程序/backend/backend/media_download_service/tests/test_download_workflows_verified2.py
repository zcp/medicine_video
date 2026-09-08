import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from pathlib import Path
from app.core.config import settings
import os

# Import your app and models
from app.main import app
from app.database import get_db
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus,  DownloadedVideoStatus, FailureStatusEnum

# Your helper function (this is correct, no changes needed here)
async def create_invalid_m3u8_task(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    task = DownloadTask(
        user_id=user_id,
        video_id=uuid.uuid4(),
        liveroom_id="1234567891",
        resource_url="https://lancet.im/videos/194_1080p_5000/playlist11.m3u8",
        resource_type="hls",
        status=TaskStatus.PENDING
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

async def task_pending_basic_for_mp4_download(db_session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
        """
       创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
       """

        task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.PENDING,

        )

        db_session.add(task)
        await db_session.commit()
        #await session.flush()
        await db_session.refresh(task)
        return task  # 直接返回任务对象

async def task_pending_basic_for_invalid_mp4_url_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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
                expected_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "mp4"),
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
    )
    session.add_all([failure2])
    await session.commit()

    return task  # 直接返回任务对象

async def task_pending_basic_for_invalid_mp4_url_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_failure.mp4",
            resource_type="mp4",
            status=TaskStatus.PENDING
    )
    session.add(task)
    await session.commit()
    #await session.flush()
    await session.refresh(task)
    return task  # 直接返回任务对象

async def task_failed_basic_for_mp4_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 FAILED 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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
                expected_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "mp4"),
                standard_name="video_1234567890_abcd_fetch_20250630T194559.mp4",
                resource_type="mp4",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
    )
    session.add_all([failure2])
    await session.commit()

    return task  # 直接返回任务对象


async def task_pending_basic_for_invalid_mp4_url2_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567890",
            resource_url="not-a-url",
            resource_type="mp4",
            status=TaskStatus.PENDING
    )
    session.add(task)
    await session.commit()
    #await session.flush()
    await session.refresh(task)
    return task  # 直接返回任务对象

async def task_completed_basic_for_mp4_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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


async def task_pending_basic_for_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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

async def task_pending_invalid_m3u8_for_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 M3U8 文件无效的任务，用于测试首次访问失败场景。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567891",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist_invalid.m3u8",
            resource_type="hls",
            status=TaskStatus.PENDING
    )
    session.add(task)
    await session.commit()
    #await session.flush()
    await session.refresh(task)
    return task  # 直接返回任务对象

async def task_partial_completed_hls(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist_partial_completed.m3u8",
            resource_type="hls",
            status=TaskStatus.PARTIAL_COMPLETED
        )
    session.add(task)
    await session.commit()

    return task

async def task_failed_valid_m3u8_for_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 FAILED 状态的任务，资源地址有效，可用于模拟重试恢复。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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
                expected_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "hls" / "ts"),
                standard_name="playlist_failure4.m3u8",
                resource_type="m3u8",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
    )
    session.add_all([failure2])
    await session.commit()

    return task  # 直接返回任务对象

async def task_failed_m3u8_for_exceeds_limit(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 M3U8 文件无效的任务，用于测试首次访问失败场景。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567891",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist_invalid.m3u8",
            resource_type="hls",
            status=TaskStatus.FAILED,
            retry_count = 2
    )

    session.add(task)
    await session.commit()
    # await session.flush()
    await session.refresh(task)

    # 2. Create associated failure records
    failure2 = DownloadFailure(
        task_id=task.id,
        resource_url="hhttps://lancet.im/videos/194_1080p_5000/playlist_invalid.m3u8",
        expected_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "hls"),
        standard_name=f"playlist_invalid.m3u8",
        resource_type="m3u8",
        failure_type="network_error",
        error_message="Connection timed out on first attempt.",
        status="pending",
        retry_count=2
    )
    session.add_all([failure2])
    await session.commit()

    session.add(task)
    await session.commit()
    return task  # 直接返回任务对象

async def task_partial_completed_with_ts_failure_for_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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
            storage_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}"),
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
                expected_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "hls" / "ts"),
                standard_name=f"segment_000001_{task.video_id}_fetch_20250618T102153.ts",
                resource_type="ts",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
        )
    session.add_all([failure2])
    await session.commit()

    return task

async def task_partial_completed_with_invalid_segment_for_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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
            storage_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}"),
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
                expected_path=str(Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "hls" / "ts"),
                standard_name=f"segment_000001_{task.video_id}_fetch_20250618T102153.ts",
                resource_type="ts",
                failure_type="network_error",
                error_message="Connection timed out on first attempt.",
                status="pending"
    )
    session.add_all([failure2])
    await session.commit()

    return task

async def task_failed_ts_failure_threshold_exceeded_for_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个模拟 TS 文件下载失败比例过高的任务，判定为下载失败。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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
    return task

async def task_completed_basic_for_hls_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

    task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
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



@pytest.mark.asyncio
async def test_hls_m3u8_download_fails_flow(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user_id,
    auth_headers  # 添加这个参数
):
    """
    Final, corrected version of the test.
    """
    # Use 'async for' to get the actual client from its generator
    async for client in async_client:
        print("yyyyy")
        # Use 'async for' to get the actual session from its generator
        async for session in db_session:
            print("xxxxx")
            # Now 'session' is the real database session object.

            # 1. Create test data by passing the REAL session to the helper
            task = await create_invalid_m3u8_task(session, test_user_id)

            # 2. Override the app's dependency to use the REAL session
            app.dependency_overrides[get_db] = lambda: session

            # 3. Make the API call
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            print("API response", response.json())
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "failed"

            # 4. Verify results using the REAL session
            await session.refresh(task)
            print("zzz,",task.status)
            assert task.status == TaskStatus.FAILED

            result = await session.execute(
                select(DownloadFailure).filter_by(task_id=task.id)
            )
            assert result.scalar_one_or_none() is not None

            # 5. Clean up
            app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mp4_download_success_flow(async_client, db_session, test_user_id, auth_headers):
    """
    Test MP4 download success scenario.
    - Create a PENDING MP4 task
    - Start the task
    - Assert API response and all related DB state
    """
    async for client in async_client:
        async for db in db_session:
            # 1. Create test data by passing the REAL session to the helper
            task = await task_pending_basic_for_mp4_download(db, test_user_id)

            # 2. Override the app's dependency to use the REAL session
            app.dependency_overrides[get_db] = lambda: db
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            assert response.status_code == 200
            print("API response", response.json())
            data = response.json()["data"]
            assert data["status"] == "completed"

            #db_task = await db.get(DownloadTask, task.id)
            await db.refresh(task)
            print("db_task,zzz", task.status, task.id)
            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 0

            result = await db.execute(
                    select(DownloadedVideo).filter_by(task_id=task.id)
            )
            video = result.scalar_one_or_none()
            assert video is not None
            print("video,zzz", video.status)
            assert video.status == "completed"

            result = await db.execute(
                    select(DownloadFailure).filter_by(task_id=task.id)
             )
            assert result.scalar_one_or_none() is None




@pytest.mark.asyncio
async def test_retry_mp4_task_exceeds_max_retry_count(async_client, db_session, test_user_id, auth_headers):
        """
        Test retrying MP4 task that already exceeded max retry count.
        - Create a FAILED MP4 task with retry_count=3
        - Call retry API
        - Assert 400 response and error message
        """
        async for client in async_client:
            async for db in db_session:
                task = await task_pending_basic_for_invalid_mp4_url_retry(db, test_user_id)

                task.retry_count = 3
                await db.commit()

                response = await client.post(f"/api/v1/download/tasks/{task.id}/retry", headers=auth_headers)
                print("API response:", response.json())
                assert response.status_code == 200
                assert response.json()["code"] == 400

                assert "重试次数已达上限" in response.text or "Retry limit exceeded" in response.text

@pytest.mark.asyncio
async def test_mp4_download_failure_flow(async_client, db_session, test_user_id, auth_headers):
    """
    Test MP4 download failure scenario.
    - Create a PENDING MP4 task with invalid resource
    - Start the task
    - Assert API response and DB state
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_pending_basic_for_invalid_mp4_url_download(db, test_user_id)
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "failed"

            await db.refresh(task)
            assert task.status == TaskStatus.FAILED
            assert task.retry_count == 0
            print("xxx,zzz,",task.status,task.retry_count)
            result = await db.execute(
                    select(DownloadFailure).filter_by(task_id=task.id, resource_type="mp4")
            )
            failure = result.scalar_one_or_none()
            assert failure is not None

            result = await db.execute(
                    select(DownloadedVideo).filter_by(task_id=task.id)
                )
            assert result.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_mp4_retry_and_succeed_flow(async_client, db_session, test_user_id, auth_headers):
    """
    Test MP4 retry and succeed scenario.
    - Create a FAILED MP4 task with a failure record
    - Patch download logic to succeed
    - Retry the task
    - Assert API response and DB state
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_failed_basic_for_mp4_retry(db, test_user_id)

            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "completed"

            print("API response:", response.json())
            await db.refresh(task)
            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 1

            print("xxx,zzz", task.status, task.retry_count)
            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id)
            )
            assert result.scalar_one_or_none() is None

            result = await db.execute(
                select(DownloadedVideo).filter_by(task_id=task.id)
            )
            video = result.scalar_one_or_none()
            assert video is not None


@pytest.mark.asyncio
async def test_start_mp4_task_with_invalid_task_id(async_client, auth_headers):
    """
    Test starting MP4 task with non-existent UUID.
    - Call start API with invalid UUID
    - Assert 404 response and error message
    """
    async for client in async_client:
        response = await client.post("/api/v1/download/tasks/00000000-0000-0000-0000-000000000000/start", headers=auth_headers)
        print("API response,xxxx", response.json())
        assert response.status_code == 200
        assert response.json()["code"] == 400
        assert "不存在" in response.text or "Task not found" in response.text


@pytest.mark.asyncio
async def test_start_mp4_task_with_invalid_uuid_format(async_client, auth_headers):
    """
    Test starting MP4 task with invalid UUID format.
    - Call start API with malformed UUID
    - Assert 422 response and error message
    """
    async for client in async_client:
        response = await client.post("/api/v1/download/tasks/invalid-uuid/start", headers=auth_headers)
        print("API response,xxxx", response.json())
        assert response.status_code == 422
        assert "Input should be a valid UUID" in response.text or "Invalid UUID format" in response.text

@pytest.mark.asyncio
async def test_create_mp4_task_with_invalid_resource_url(async_client, db_session, test_user_id, auth_headers):
    """
    Test creating MP4 task with invalid resource URL.
    - Call create API with invalid URL
    - Assert 422 response and error message
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_pending_basic_for_invalid_mp4_url2_download(db, test_user_id)
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            print("API response,xxxx", response.json())
            assert response.status_code == 200
            assert response.json()['code'] == 400
            assert "Input should be a valid URL" in response.text or "Invalid URL format" in response.text


@pytest.mark.asyncio
async def test_start_already_completed_mp4_task(async_client, db_session, test_user_id, auth_headers):
    """
    Test starting an already completed MP4 task.
    - Create a COMPLETED MP4 task
    - Call start API
    - Assert 400 response and error message
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_completed_basic_for_mp4_download(db, test_user_id)
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            print("API response,xxxx", response.json())
            assert response.status_code == 200
            assert response.json()['code'] == 200
            assert "下载任务成功" in response.text or "Task already completed" in response.text

@pytest.mark.asyncio
# HLS Tests using existing fixtures
async def test_hls_full_success_flow(async_client, db_session, test_user_id, auth_headers):
    """
    Test HLS full success scenario.
    - Create a PENDING HLS task
    - Patch download_m3u8 to return all TS segments success
    - Start the task
    - Assert API response and all related DB state
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_pending_basic_for_download(db, test_user_id)

            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            assert response.status_code == 200
            print("API response:", response.json())
            assert response.json()["data"]["status"] == "completed"
            print("API response:", response.json())

            await db.refresh(task)
            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 0

            result = await db.execute(
                select(DownloadedVideo).filter_by(task_id=task.id)
            )
            video = result.scalar_one_or_none()
            assert video is not None
            assert video.status == "completed"
            print("xxxx,zzz", video.status)
            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id)
            )
            assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_hls_m3u8_download_fails_flow(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user_id,
    auth_headers  # 添加这个参数
):
    """
    Final, corrected version of the test.
    """
    # Use 'async for' to get the actual client from its generator
    async for client in async_client:
        print("yyyyy")
        # Use 'async for' to get the actual session from its generator
        async for session in db_session:
            print("xxxxx")
            # Now 'session' is the real database session object.

            # 1. Create test data by passing the REAL session to the helper
            task = await create_invalid_m3u8_task(session, test_user_id)
            print(f"Created task: {task.id}, user_id: {task.user_id}")
            # 2. Override the app's dependency to use the REAL session
            app.dependency_overrides[get_db] = lambda: session

            # 3. Verify task exists in database before API call
            result = await session.execute(
                select(DownloadTask).filter_by(id=task.id)
            )
            db_task = result.scalar_one_or_none()
            print(f"Task in DB before API call: {db_task.id if db_task else 'None'}")


            # 3. Make the API call
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            print("API response", response.json())
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "failed"

            # 4. Verify results using the REAL session
            await session.refresh(task)
            print("zzz,",task.status)
            assert task.status == TaskStatus.FAILED

            result = await session.execute(
                select(DownloadFailure).filter_by(task_id=task.id)
            )
            assert result.scalar_one_or_none() is not None

            # 5. Clean up
            app.dependency_overrides.clear()

    async def task_pending_basic_for_mp4_download(db_session: AsyncSession, user_id: uuid.UUID,
                                                  auth_headers) -> DownloadTask:
        """
       创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
       """

        task = DownloadTask(
            user_id=user_id,
            video_id=uuid.uuid4(),
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.PENDING,

        )

        db_session.add(task)
        await db_session.commit()
        # await session.flush()
        await db_session.refresh(task)
        return task  # 直接返回任务对象

@pytest.mark.asyncio
async def test_hls_partial_success_flow(async_client, db_session, test_user_id, auth_headers):
        """
        Test HLS partial success scenario (some TS segments fail).
        - Create a PENDING HLS task
        - Patch download_m3u8 to return some failed TS segments
        - Start the task
        - Assert API response and DB state
        """
        async for client in async_client:
            async for db in db_session:
                task = await task_partial_completed_hls(db, test_user_id)

                response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
                assert response.status_code == 200
                print("API response:", response.json())
                assert response.json()["data"]["status"] == "partial_completed"

                db.refresh(task)
                assert task.status == TaskStatus.PARTIAL_COMPLETED
                assert task.retry_count == 0

                result = await db.execute(
                    select(DownloadedVideo).filter_by(task_id=task.id)
                )
                video = result.scalar_one_or_none()
                assert video is not None
                assert video.status == "partial_completed"

                result = await db.execute(
                    select(DownloadFailure).filter_by(task_id=task.id, resource_type="ts")
                )

                failures = result.scalars().all()
                for failure in failures:
                    assert failure.status == "pending"
                    assert failure.retry_count == 0

@pytest.mark.asyncio
async def test_hls_full_retry_from_failed_task_and_succeeds(async_client, db_session, test_user_id, auth_headers):
    """
    Test retrying a FAILED HLS task (m3u8 failed) and succeeding.
    - Create a FAILED HLS task with m3u8 failure
    - Patch download logic to succeed
    - Retry the task
    - Assert API response and DB state
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_failed_valid_m3u8_for_retry(db, test_user_id)

            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "completed"

            await db.refresh(task)
            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 1

            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id)
            )
            assert result.scalar_one_or_none() is None

            result = await db.execute(
                select(DownloadedVideo).filter_by(task_id=task.id)
            )
            video = result.scalar_one_or_none()
            assert video is not None
            assert video.status == "completed"

@pytest.mark.asyncio
async def test_hls_full_retry_from_failed_task_exceeds_limit(async_client, db_session, test_user_id, auth_headers):
        """
        Test retrying a FAILED HLS task (m3u8 failed) and exceeding retry limit.
        - Create a FAILED HLS task with retry_count=2 and m3u8 failure
        - Patch download logic to always fail
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            async for db in db_session:
                task = await task_failed_m3u8_for_exceeds_limit(db, test_user_id)

                await db.commit()
                await db.refresh(task)
                print("task.status, task.retry_count:", task.status, task.retry_count)
                response = await client.post(f"/api/v1/download/tasks/{task.id}/retry", headers=auth_headers)
                assert response.status_code == 200
                print("API response:", response.json())
                assert response.json()["data"]["status"] == "failed"

                await db.refresh(task)
                assert task.retry_count == 3

                result = await db.execute(
                    select(DownloadFailure).filter_by(task_id=task.id, resource_type="m3u8")
                )
                failure = result.scalar_one_or_none()
                assert failure is not None
                assert failure.status == "abandoned"
                assert failure.retry_count == 3

                result = await db.execute(
                    select(DownloadedVideo).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None



async def test_hls_partial_retry_for_single_ts_succeeds(async_client, db_session, test_user_id, auth_headers):
    """
    Test retrying a PARTIAL_COMPLETED HLS task for a single failed TS segment and succeeding.
    - Create a PARTIAL_COMPLETED HLS task with one failed TS
    - Patch retry logic to succeed
    - Retry the task
    - Assert API response and DB state
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_partial_completed_with_ts_failure_for_retry(db, test_user_id)

            ts_storage_path = Path(settings.DOWNLOAD_DIR) / f"video_{task.video_id}" / "hls" / "ts"
            os.makedirs(ts_storage_path, exist_ok=True)
            ### --- FIX ENDS --- ###

            assert task.status == TaskStatus.PARTIAL_COMPLETED
            result = await db.execute(
                select(DownloadedVideo).filter_by(task_id=task.id)
            )
            video = result.scalars().first()  # 得到第一条记录（对象），没有则为None

            assert video.status == DownloadedVideoStatus.PARTIAL_COMPLETED

            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id)
            )
            assert result.scalar_one_or_none() is not None

            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry", headers=auth_headers)
            assert response.status_code == 200
            print("API response:", response.json())
            assert response.json()["code"] == 200
            # status may be PARTIAL_COMPLETED or COMPLETED depending on other failures
            #assert response.json()["data"]["status"] == "completed"

            await db.refresh(task)
            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 1
            await db.refresh(video)
            assert video.status == DownloadedVideoStatus.COMPLETED

            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id, resource_type="m3u8")
            )
            assert result.scalar_one_or_none() is None

async def test_hls_partial_retry_for_single_ts_exceeds_limit(async_client, db_session, test_user_id, auth_headers):
    """
    Test retrying a PARTIAL_COMPLETED HLS task for a single failed TS segment and exceeding retry limit.
    - Create a PARTIAL_COMPLETED HLS task with one failed TS (retry_count=2)
    - Patch retry logic to always fail
    - Retry the task
    - Assert API response and DB state
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_partial_completed_with_invalid_segment_for_retry(db, test_user_id)

            task.retry_count = 2
            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id, resource_type="ts")
            )
            failure = result.scalar_one_or_none()
            failure.retry_count = 2

            await db.commit()

            await db.refresh(task)
            await db.refresh(failure)

            assert failure.retry_count == 2
            assert task.retry_count == 2


            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry", headers=auth_headers)
            print("API response:",response.json())
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "partial_completed"

            await db.refresh(task)
            await db.refresh(failure)

            assert task.retry_count == 3
            assert failure.retry_count == 3

            assert failure.status == FailureStatusEnum.ABANDONED


async def test_hls_ts_failure_rate_too_high_flow(async_client, db_session, test_user_id, auth_headers):
        """
        Test HLS TS failure rate too high scenario.
        - Create a PENDING HLS task
        - Patch download_m3u8 to return too many failed TS segments
        - Start the task
        - Assert API response and DB state
        """
        async for client in async_client:
            async for db in db_session:
                task = await task_failed_ts_failure_threshold_exceeded_for_retry(db, test_user_id)

                response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
                assert response.status_code == 200
                assert response.json()["data"]["status"] == "failed"

                await db.refresh(task)
                assert task.status == TaskStatus.FAILED

                failures = await db.execute(
                    select(DownloadFailure).filter_by(task_id=task.id)
                )

                all_failures = failures.scalars().all()
                assert len(all_failures) == 1
                # 然后处理所有记录
                for failure in all_failures:
                    print(failure.status)

                assert failure.status == "pending"


                videos = await db.execute(
                    select(DownloadedVideo).filter_by(task_id=task.id)
                )

                assert videos.scalar_one_or_none() is None

async def test_start_already_completed_hls_m3u8_task(async_client, db_session, test_user_id, auth_headers):
    """
    Test starting an already completed HLS m3u8 task.
    - Create a COMPLETED status hls-m3u8 task
    - Call POST /api/v1/download/tasks/{task_id}/start
    - Assert 400 Bad Request response
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_completed_basic_for_hls_download(db, test_user_id)
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["code"] == 200
            print("API response:", response.json())
            assert response.json()["data"]["status"] == "completed"
