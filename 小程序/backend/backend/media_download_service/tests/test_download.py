# test_download.py (Corrected Version)
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4, UUID
from datetime import datetime

from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus, VideoType

TEST_HLS_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
TEST_MP4_URL = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"


# 注意：所有 @pytest.fixture 定义都已从此文件删除，因为它们由 conftest_backup.py 全局提供

# 4.1 创建下载任务测试
@pytest.mark.asyncio
async def test_create_task_success(async_client: AsyncClient):
    """测试成功创建下载任务"""
    task_data = {
        "video_id": uuid.uuid4(),
        "liveroom_id": "1234567890",
        "liveroom_title": "测试直播间",
        "liveroom_url": "https://example.com/live/1234567890",
        "video_url": TEST_HLS_URL,
        "video_type": VideoType.HLS,
        "title": "测试视频标题",  # 根据您提供的schemas.py，这是一个必填字段
    }
    response = await async_client.post("/api/v1/download/tasks", json=task_data)

    # 根据API响应结构进行断言
    assert response.status_code == 200  # 假设您的统一响应函数返回200
    data = response.json()
    assert data["code"] == 201
    assert data["data"]["status"] == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_create_task_duplicate(async_client: AsyncClient, db_session: AsyncSession):
    """测试创建重复任务（假设逻辑是检查downloaded_videos表）"""
    video_id_to_test = uuid.uuid4(),
    video = DownloadedVideo(
        video_id=video_id_to_test,
        liveroom_id="1234567890",
        video_type="hls",
        video_url=TEST_HLS_URL,
        storage_path="/test_output/test.mp4",
        status="completed"
    )
    db_session.add(video)
    await db_session.commit()

    task_data = {
        "video_id": video_id_to_test,
        "liveroom_id": "1234567890",
        "video_url": TEST_HLS_URL,
        "video_type": "hls",
        "title": "重复任务测试"
    }
    response = await async_client.post("/api/v1/download/tasks", json=task_data)
    assert response.status_code == 409


# 4.3 获取任务详情测试
@pytest.mark.asyncio
async def test_get_task_details_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功获取任务详情"""
    # Pytest 会自动处理 fixture 的依赖和执行，此处 sample_task 就是一个 ORM 对象
    response = await async_client.get(f"/api/v1/download/tasks/{sample_task.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(sample_task.id)
    assert data["video_id"] == sample_task.video_id


@pytest.mark.asyncio
async def test_get_task_details_not_found(async_client: AsyncClient):
    """测试获取不存在的任务详情"""
    response = await async_client.get(f"/api/v1/download/tasks/{uuid4()}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


# 4.3.1 获取任务列表测试
@pytest.mark.asyncio
async def test_list_download_tasks_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功获取任务列表"""
    response = await async_client.get("/api/v1/download/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
    assert "size" in data["data"]
    assert "pages" in data["data"]
    # 检查是否包含我们创建的任务
    task_ids = [item["id"] for item in data["data"]["items"]]
    assert str(sample_task.id) in task_ids


@pytest.mark.asyncio
async def test_list_download_tasks_with_status_filter(async_client: AsyncClient, sample_task: DownloadTask):
    """测试按状态筛选任务列表"""
    response = await async_client.get("/api/v1/download/tasks?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    # 检查所有返回的任务都是 pending 状态
    for item in data["data"]["items"]:
        assert item["status"] == "pending"


@pytest.mark.asyncio
async def test_list_download_tasks_with_pagination(async_client: AsyncClient):
    """测试任务列表分页功能"""
    response = await async_client.get("/api/v1/download/tasks?page=1&size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["page"] == 1
    assert data["data"]["size"] == 5
    assert len(data["data"]["items"]) <= 5


# 4.4 任务操作测试
@pytest.mark.asyncio
async def test_pause_download_task_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功暂停下载任务"""
    response = await async_client.post(f"/api/v1/download/tasks/{sample_task.id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "暂停下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_pause_download_task_not_found(async_client: AsyncClient):
    """测试暂停不存在的任务"""
    fake_task_id = str(uuid4())
    response = await async_client.post(f"/api/v1/download/tasks/{fake_task_id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


@pytest.mark.asyncio
async def test_resume_download_task_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功恢复下载任务"""
    response = await async_client.post(f"/api/v1/download/tasks/{sample_task.id}/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "恢复下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_resume_download_task_not_found(async_client: AsyncClient):
    """测试恢复不存在的任务"""
    fake_task_id = str(uuid4())
    response = await async_client.post(f"/api/v1/download/tasks/{fake_task_id}/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


@pytest.mark.asyncio
async def test_retry_download_task_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功重试下载任务"""
    response = await async_client.post(f"/api/v1/download/tasks/{sample_task.id}/retry")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "重试下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_retry_download_task_not_found(async_client: AsyncClient):
    """测试重试不存在的任务"""
    fake_task_id = str(uuid4())
    response = await async_client.post(f"/api/v1/download/tasks/{fake_task_id}/retry")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


# 4.5 取消任务测试
@pytest.mark.asyncio
async def test_cancel_pending_task_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功取消待处理任务"""
    response = await async_client.delete(f"/api/v1/download/tasks/{sample_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "删除下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_cancel_completed_task_fails(async_client: AsyncClient, sample_completed_task: DownloadTask):
    """测试取消已完成任务失败"""
    response = await async_client.delete(f"/api/v1/download/tasks/{sample_completed_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 400
    assert "不能删除已完成任务" in data["message"]


# 4.5 获取失败记录测试
@pytest.mark.asyncio
async def test_get_failures_for_task(async_client: AsyncClient, sample_failure: DownloadFailure):
    """测试获取任务的失败记录"""
    async for failure in sample_failure:
        response = await async_client.get(f"/api/v1/download/tasks/{failure.task_id}/failures")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) >= 1
        assert data["data"]["items"][0]["task_id"] == str(failure.task_id)
        assert data["data"]["items"][0]["resource_url"] == failure.resource_url


@pytest.mark.asyncio
async def test_get_failures_for_task_with_no_failures(async_client: AsyncClient, sample_completed_task: DownloadTask):
    """测试获取没有失败记录的任务的失败记录"""
    async for task in sample_completed_task:
        response = await async_client.get(f"/api/v1/download/tasks/{task.id}/failures")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 0


# 4.6 重试失败记录测试
@pytest.mark.asyncio
async def test_retry_specific_failure_success(async_client: AsyncClient, sample_failure: DownloadFailure):
    """测试重试特定失败记录（成功）"""
    async for failure in sample_failure:
        response = await async_client.post(f"/api/v1/download/failures/{failure.id}/retry")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == str(failure.id)
        assert data["data"]["retry_count"] == 1
        assert data["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_retry_specific_failure_not_found(async_client: AsyncClient):
    """测试重试不存在的失败记录"""
    fake_failure_id = str(uuid4())
    response = await async_client.post(f"/api/v1/download/failures/{fake_failure_id}/retry")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


@pytest.mark.asyncio
async def test_abandon_specific_failure_success(async_client: AsyncClient, sample_failure: DownloadFailure):
    """测试放弃特定失败记录（成功）"""
    async for failure in sample_failure:
        response = await async_client.post(f"/api/v1/download/failures/{failure.id}/abandon")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == str(failure.id)
        assert data["data"]["status"] == "abandoned"


@pytest.mark.asyncio
async def test_abandon_specific_failure_not_found(async_client: AsyncClient):
    """测试放弃不存在的失败记录"""
    fake_failure_id = str(uuid4())
    response = await async_client.post(f"/api/v1/download/failures/{fake_failure_id}/abandon")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


@pytest.mark.asyncio
async def test_retry_all_failures_success(async_client: AsyncClient, sample_failure: DownloadFailure):
    """测试重试所有失败记录（成功）"""
    async for failure in sample_failure:
        response = await async_client.post(f"/api/v1/download/tasks/{failure.task_id}/retry-all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == str(failure.id)
        assert data["data"][0]["retry_count"] == 1
        assert data["data"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_retry_all_failures_no_failures(async_client: AsyncClient, sample_completed_task: DownloadTask):
    """测试重试没有失败记录的任务的所有失败记录"""
    async for task in sample_completed_task:
        response = await async_client.post(f"/api/v1/download/tasks/{task.id}/retry-all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]) == 0


@pytest.mark.asyncio
async def test_abandon_all_failures_success(async_client: AsyncClient, sample_failure: DownloadFailure):
    """测试放弃所有失败记录（成功）"""
    async for failure in sample_failure:
        response = await async_client.post(f"/api/v1/download/tasks/{failure.task_id}/abandon-all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == str(failure.id)
        assert data["data"][0]["status"] == "abandoned"


@pytest.mark.asyncio
async def test_abandon_all_failures_no_failures(async_client: AsyncClient, sample_completed_task: DownloadTask):
    """测试放弃没有失败记录的任务的所有失败记录"""
    async for task in sample_completed_task:
        response = await async_client.post(f"/api/v1/download/tasks/{task.id}/abandon-all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]) == 0


@pytest.mark.asyncio
async def test_get_downloaded_videos(async_client: AsyncClient, sample_completed_task: DownloadTask):
    """测试获取已下载视频列表"""
    async for task in sample_completed_task:
        response = await async_client.get(f"/api/v1/download/tasks/{task.id}/videos")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) >= 1
        assert data["data"]["items"][0]["video_id"] == task.video_id
        assert data["data"]["items"][0]["liveroom_id"] == task.liveroom_id

@pytest.mark.asyncio
async def test_get_task_details_not_found(async_client: AsyncClient):
    """测试获取不存在的任务详情"""
    async for client in async_client:
        response = await client.get(f"/api/v1/download/tasks/{uuid4()}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
