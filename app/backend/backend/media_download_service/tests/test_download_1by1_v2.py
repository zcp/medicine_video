# tests/test_download_1by1.py (Final Corrected Version)
import uuid
from uuid import uuid4

import pytest
from httpx import AsyncClient

# It's good practice to import any Enums or Schemas you use for validation
from app.schemas.download import TaskStatus, VideoType

from app.schemas.download import DownloadedVideo

from app.models.download import DownloadTask, DownloadFailure
from sqlalchemy.ext.asyncio import AsyncSession

#from backend.media_download_service.tests.conftest.py import sample_m3u8_failure

TEST_HLS_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"


@pytest.fixture
async def task_pending_basic_for_image_download(db_session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    async for session in db_session:
        task = DownloadTask(
            video_id=uuid.uuid4(),
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

@pytest.mark.asyncio
async def test_start_download_image_task_success(async_client: AsyncClient, task_pending_basic_for_image_download: DownloadTask):
    """测试成功重试下载任务"""
    async for client in async_client:
        task = await task_pending_basic_for_image_download
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "重试下载任务成功" in data["message"]
