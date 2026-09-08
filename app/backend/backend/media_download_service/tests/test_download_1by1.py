# tests/test_download_1by1.py (Final Corrected Version)
from uuid import uuid4

import pytest
from httpx import AsyncClient

# It's good practice to import any Enums or Schemas you use for validation
from app.schemas.download import TaskStatus, VideoType

from app.schemas.download import DownloadedVideo

from app.models.download import DownloadTask, DownloadFailure


TEST_HLS_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"


@pytest.mark.asyncio
async def test_create_download_task(async_client: AsyncClient):
    """
    测试创建下载任务

    修正说明：
    由于测试环境未能自动解析fixture，我们使用 'async for' 循环来
    显式地从 async_client 生成器中获取 yielded 的 client 对象。
    """
    # async for 循环会正确地“解包”异步生成器 fixture
    async for client in async_client:
        # 1. 定义请求体 (请确保所有必填字段都已提供)
        task_data = {
            "video_id": "1234567890_abcd",
            "liveroom_id": "12345678901",
            "liveroom_title": "测试直播间",
            "liveroom_url": "https://example.com/live/1234567890",
            "resource_url": TEST_HLS_URL,
            "resource_type": "hls"
            # 根据您的schema，还有 duration, file_size, max_retries, priority 等字段
            # 如果它们在Create模型中不是必填项，则可以省略
        }

        # 2. 现在 'client' 是一个真正的 httpx.AsyncClient 实例，可以调用 .post()
        response = await client.post("/api/v1/download/tasks", json=task_data)
        print("API Response:", response.json())
        # 3. 断言结果
        # 注意: 请根据您API的真实响应码和结构来调整断言
        assert response.status_code == 200  # 或者 201

        response_data = response.json()
        print(response_data["code"])
        assert response_data["code"] == 201
        assert response_data["data"]["status"] == "pending"

        # 因为我们的 fixture 只 yield 一次，所以在此处跳出循环
        break


# tests/test_download_1by1.py (Corrected test_get_task_status function)

@pytest.mark.asyncio
async def test_get_task_status(async_client: AsyncClient, task_pending_basic_for_download: DownloadTask):
    """测试获取任务状态"""
    # 1. 使用与第一个测试相同的正确模式来获取 client
    async for client in async_client:
        # 2. 'sample_task' 已经是解析好的 ORM 对象，直接使用即可
        #    不需要 'async for task in sample_task:'
        task = await task_pending_basic_for_download

        # 3. 发起请求
        response = await client.get(f"/api/v1/download/tasks/{task.id}")

        # 4. 断言结果
        print("API Response:", response.json())
        assert response.status_code == 200

        # 假设您的API响应也遵循统一的包装格式
        response_data = response.json()
        assert response_data["code"] == 200

        data = response_data["data"]
        print(data)
        # 将UUID和datetime对象转换为字符串进行比较，这是最稳健的方式
        assert data["id"] == str(task.id)
        assert data["video_id"] == task.video_id
        # 当比较枚举时，比较其 .value (即字符串值)
        assert data["status"] == task.status

        # 5. 跳出循环
        break

@pytest.mark.asyncio
async def test_get_task_status_not_found(async_client: AsyncClient):
    """测试获取不存在的任务状态"""
    async for client in async_client:

        response = await client.get("/api/v1/download/tasks/999")
        print("API response:", response.json())
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_cancel_pending_task_success(async_client: AsyncClient, task_pending_basic_for_download: DownloadTask):
    """测试成功取消待处理任务"""
    """测试成功取消待处理任务"""
    async for client in async_client:
        # 先 await task_pending_basic_for_download  获取任务对象
        task = await task_pending_basic_for_download
        response = await client.delete(f"/api/v1/download/tasks/{task.id}")
        print("API Response:", response.json())
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "删除下载任务成功" in data["message"].lower()

@pytest.mark.asyncio
async def test_cancel_completed_task_fails(async_client: AsyncClient, task_completed_basic_for_download: DownloadTask):
    """测试成功取消待处理任务"""
    async for client in async_client:
        # 先 await sample_task 获取任务对象
        task = await task_completed_basic_for_download
        response = await client.delete(f"/api/v1/download/tasks/{task.id}")
        print("API Response:", response.json())
        print(response.status_code)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "不能删除已完成任务" in data["message"].lower()

@pytest.mark.asyncio
async def test_get_failures_for_task(async_client: AsyncClient, task_failed_valid_m3u8_for_retry: DownloadFailure):
    """测试获取任务的失败记录"""
    async for client in async_client:
        task = await task_failed_valid_m3u8_for_retry
        response = await client.get(f"/api/v1/download/tasks/{task.id}/failures")
        assert response.status_code == 200
        data = response.json()
        print(data)
        #assert len(data) == 4
        #assert data["task_id"] == task.task_id
        #assert data["resource_url"] == task.resource_url


@pytest.mark.asyncio
async def test_get_failures_for_task_with_no_failures(async_client: AsyncClient, task_completed_basic_for_download: DownloadTask):
    """测试获取没有失败记录的任务"""
    async for client in  async_client:
            task = await task_completed_basic_for_download
            response = await client.get(f"/api/v1/download/tasks/{task.id}/failures")
            print("API response",response.json())
            assert response.status_code == 200
            data = response.json()
            assert data['data']['total'] == 0

@pytest.mark.asyncio
async def test_retry_specific_failure_not_found(async_client: AsyncClient):
    """测试重试不存在的失败记录"""
    async for client in async_client:
        fake_task_id = str(uuid4())
        response = await client.post(f"/api/v1/download/failures/{fake_task_id}/retry")
        print("API Response:", response.json())
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400

@pytest.mark.asyncio
async def test_get_task_details_success(async_client: AsyncClient, task_pending_basic_for_download: DownloadTask):
    """测试成功获取任务详情"""
    # Pytest 会自动处理 fixture 的依赖和执行，此处 sample_task 就是一个 ORM 对象
    async for client in async_client:
        task = await task_pending_basic_for_download
        response = await client.get(f"/api/v1/download/tasks/{task.id}")
        print("API Response:", response.json())
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["id"] == str(task.id)
        assert data["video_id"] == task.video_id


@pytest.mark.asyncio
async def test_get_task_details_not_found(async_client: AsyncClient):
    """测试获取不存在的任务详情"""
    async for client in async_client:
        response = await client.get(f"/api/v1/download/tasks/{uuid4()}")
        assert response.status_code == 200
        data = response.json()
        print("API response", data)
        assert data["code"] == 400

async def test_list_download_tasks_success(async_client: AsyncClient, sample_task: DownloadTask):
    """测试成功获取任务列表"""
    async for client in async_client:
        response = await client.get("/api/v1/download/tasks")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "size" in data["data"]
        assert "pages" in data["data"]
        # 检查是否包含我们创建的任务
        task_ids = [item["id"] for item in data["data"]["items"]]
        #assert str(task.id) in task_ids

@pytest.mark.asyncio
async def test_list_download_tasks_with_status_filter(async_client: AsyncClient, sample_task: DownloadTask):
    """测试按状态筛选任务列表"""
    async for client in async_client:
        response = await client.get("/api/v1/download/tasks?status=pending")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        # 检查所有返回的任务都是 pending 状态
        for item in data["data"]["items"]:
            assert item["status"] == "pending"


@pytest.mark.asyncio
async def test_list_download_tasks_with_pagination(async_client: AsyncClient):
    """测试任务列表分页功能"""
    async for client in async_client:
        response = await client.get("/api/v1/download/tasks?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["page"] == 1
        assert data["data"]["size"] == 5
        assert len(data["data"]["items"]) <= 5


@pytest.mark.asyncio
async def test_start_download_task_success(async_client: AsyncClient, task_pending_basic_for_download: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_pending_basic_for_download
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]

@pytest.mark.asyncio
async def test_start_mp4_download_task_success(async_client: AsyncClient, task_pending_basic_for_mp4_download: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_pending_basic_for_mp4_download
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_start_mp4_download_task_failure(async_client: AsyncClient, task_pending_basic_for_invalid_mp4_url_download: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_pending_basic_for_invalid_mp4_url_download
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]

@pytest.mark.asyncio
async def test_start_mp4_download_task_for_retry_success(async_client: AsyncClient, task_pending_basic_for_mp4_retry: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_pending_basic_for_mp4_retry
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]

@pytest.mark.asyncio
async def test_start_mp4_download_task_for_retry_failure(async_client: AsyncClient, task_pending_basic_for_invalid_mp4_url_retry: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_pending_basic_for_invalid_mp4_url_retry
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_start_download_task_completed(async_client: AsyncClient, task_completed_basic_for_download: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_completed_basic_for_download
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]

#多个ts下载失败，失败率超过了指定阈值，判定为下载失败
@pytest.mark.asyncio
async def test_start_download_task_failure(async_client: AsyncClient, task_pending_invalid_m3u8_for_download: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_pending_invalid_m3u8_for_download
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert data["data"]["status"] == "failed"
        #assert "暂停下载任务成功" in data["message"]


@pytest.mark.asyncio
async def test_start_download_task_partial_completed(async_client: AsyncClient, sample_partial_completed_task: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await sample_partial_completed_task
        response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "下载任务成功" in data["message"]

@pytest.mark.asyncio
async def test_cancel_completed_task_fails(async_client: AsyncClient, sample_completed_task: DownloadTask):
    """测试成功取消待处理任务"""
    async for client in async_client:
        # 先 await sample_task 获取任务对象
        task = await sample_completed_task
        response = await client.delete(f"/api/v1/download/tasks/{task.id}")
        print("API Response:", response.json())
        print(response.status_code)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "不能删除已完成任务" in data["message"].lower()


@pytest.mark.asyncio
async def test_retry_failed_mp4_max_retry_counts(
        async_client: AsyncClient,
        task_pending_basic_for_invalid_mp4_url_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in async_client:
        task = await task_pending_basic_for_invalid_mp4_url_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200



@pytest.mark.asyncio
async def test_retry_download_task_success(async_client: AsyncClient, task_failed_valid_m3u8_for_retry: DownloadTask):
    """测试成功重试下载任务"""
    async for client in async_client:
        task = await task_failed_valid_m3u8_for_retry
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert "重试下载任务成功" in data["message"]

@pytest.mark.asyncio
async def test_retry_download_task_not_found(async_client: AsyncClient):
    """测试重试不存在的任务"""
    async for client in async_client:
        fake_task_id = str(uuid4())
        response = await client.post(f"/api/v1/download/tasks/{fake_task_id}/retry")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400


@pytest.mark.asyncio
async def test_get_failures_for_task_with_no_failures(async_client: AsyncClient, task_failed_valid_m3u8: DownloadTask):
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:
            task = await task_failed_valid_m3u8
            response = await client.get(f"/api/v1/download/tasks/{task.id}/failures")
            print("API response",response.json())
            assert response.status_code == 200
            data = response.json()
            assert data['data']['total'] == 0

@pytest.mark.asyncio
async def test_retry_failed_segments(
        async_client: AsyncClient,
        task_partial_completed_with_ts_failure_for_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:

        task = await task_partial_completed_with_ts_failure_for_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

@pytest.mark.asyncio
async def test_retry_failed_mp4_max_retry_counts(
        async_client: AsyncClient,
        task_pending_basic_for_invalid_mp4_url_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:

        task = await task_pending_basic_for_invalid_mp4_url_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200


        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200



@pytest.mark.asyncio
async def test_retry_failed_segments_max_retry_counts(
        async_client: AsyncClient,
        task_partial_completed_with_invalid_segment_for_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:

        task = await task_partial_completed_with_invalid_segment_for_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200


        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200




@pytest.mark.asyncio
async def test_retry_invalid_m3u8(
        async_client: AsyncClient,
        task_failed_invalid_m3u8_for_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:

        task = await task_failed_invalid_m3u8_for_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

@pytest.mark.asyncio
async def test_retry_partial_completed_m3u8_for_retry(
        async_client: AsyncClient,
        task_partial_completed_with_ts_failure_for_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:

        task = await task_partial_completed_with_ts_failure_for_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200

#重新下载任务为failed的任务
#   1：下载失败的segments数超过了预定的阈值，被定义为失败的下载任务
#   2：合法m3u8下载失败的任务为下载失败的任务
#   3：非法m3u8下载失败的任务为下载失败任务
@pytest.mark.asyncio
async def test_retry_failed_tasks2(
        async_client: AsyncClient,
        task_failed_ts_failure_threshold_exceeded_for_retry: DownloadTask  # Use the new fixture
):
    """
    Tests successfully triggering a retry for a failed task.
    """
    # Setup: The fixture provides the failed task
    """测试获取没有失败记录的任务的失败记录"""
    async for client in  async_client:

        task = await task_failed_ts_failure_threshold_exceeded_for_retry
        original_retry_count = task.retry_count

        # Action: Call the retry endpoint
        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")

        # Verification (API Response)
        assert (response.status_code ==
                200)
        response_data = response.json()
        print("API RESPONSE", response_data)
        assert response_data["code"] == 200


@pytest.mark.asyncio
async def test_retry_failed_max_retry_counts(async_client: AsyncClient, task_failed_invalid_m3u8_for_retry: DownloadTask):
    """测试成功暂停下载任务"""
    async for client in async_client:
        task = await task_failed_invalid_m3u8_for_retry

        task.status = TaskStatus.FAILED


        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert data["data"]["status"] == "failed"
        #assert "暂停下载任务成功" in data["message"]

        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert data["data"]["status"] == "failed"

        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert data["data"]["status"] == "failed"

        response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
        assert response.status_code == 200
        data = response.json()
        print("API Response:", response.json())
        assert data["code"] == 200
        assert data["data"]["status"] == "failed"


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

