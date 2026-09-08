import os
import uuid

import pytest
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import your app and models
from app.main import app
from app.database import get_db
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo

from app.schemas.download import TaskStatus,  DownloadedVideoStatus, FailureStatusEnum

from app.core.config import settings

from backend.media_download_service.tests.test_download_workflows_verified2 import task_partial_completed_hls, \
    task_completed_basic_for_mp4_download, task_pending_basic_for_mp4_download


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

