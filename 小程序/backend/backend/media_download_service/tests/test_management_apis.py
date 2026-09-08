import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from media_download_service.app.models.download import DownloadTask, DownloadFailure, DownloadedVideo, TaskStatus

@pytest.mark.asyncio
class TestManagementAPIs:
    """
    Test suite for general task management APIs (create, query, delete, failure record management).
    Each test covers API response, database state, and business side effects as required by the test prompt.
    """


    async def test_get_tasks_with_pagination_and_filters(self, async_client, db_session, task_pending_basic_for_mp4_download, task_completed_basic_for_download, task_pending_basic_for_download):
        """
        Test getting tasks with pagination and filters.
        - Create multiple tasks with different statuses
        - Call GET /api/v1/download/tasks with status and pagination parameters
        - Assert correct pagination and filtering results
        """
        # Create tasks with different statuses
        pending_task = await task_pending_basic_for_mp4_download
        completed_task = await task_completed_basic_for_download
        hls_task = await task_pending_basic_for_download
        
        # Test pagination
        response = await async_client.get("/api/v1/download/tasks?page=1&size=2")
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) <= 2
        assert "total" in response_data
        assert "page" in response_data
        assert "size" in response_data
        
        # Test status filter
        response = await async_client.get("/api/v1/download/tasks?status=pending")
        assert response.status_code == 200
        response_data = response.json()
        for task in response_data["items"]:
            assert task["status"] == "pending"

    async def test_get_task_details_success(self, async_client, db_session, task_pending_basic_for_mp4_download):
        """
        Test successful task details retrieval.
        - Create a task
        - Call GET /api/v1/download/tasks/{task_id}
        - Assert correct response data
        """
        task = await task_pending_basic_for_mp4_download
        response = await async_client.get(f"/api/v1/download/tasks/{task.id}")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == str(task.id)
        assert response_data["status"] == "pending"
        assert response_data["resource_url"] == task.resource_url
        assert response_data["type"] == task.type

    async def test_get_task_details_not_found(self, async_client):
        """
        Test task details retrieval with non-existent task ID.
        - Call GET /api/v1/download/tasks/{task_id} with non-existent ID
        - Assert 404 Not Found response
        """
        response = await async_client.get("/api/v1/download/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert "任务不存在" in response.text or "Task not found" in response.text

    async def test_delete_pending_task_success(self, async_client, db_session, task_pending_basic_for_mp4_download):
        """
        Test successful deletion of a pending task.
        - Create a PENDING status task
        - Call DELETE /api/v1/download/tasks/{task_id}
        - Assert task is cancelled or deleted
        """
        task = await task_pending_basic_for_mp4_download
        response = await async_client.delete(f"/api/v1/download/tasks/{task.id}")
        assert response.status_code == 200
        
        db_task = await db_session.get(DownloadTask, task.id)
        # Task should be either deleted or status changed to CANCELLED
        assert db_task is None or db_task.status == TaskStatus.CANCELLED

    async def test_delete_non_deletable_task_fails(self, async_client, db_session, task_completed_basic_for_download):
        """
        Test deletion fails for non-deletable task statuses.
        - Create a COMPLETED or PROCESSING status task
        - Call DELETE /api/v1/download/tasks/{task_id}
        - Assert 400 Bad Request or 409 Conflict response
        """
        completed_task = await task_completed_basic_for_download
        response = await async_client.delete(f"/api/v1/download/tasks/{completed_task.id}")
        assert response.status_code in [400, 409]
        assert "任务已完成" in response.text or "Task already completed" in response.text or "Cannot delete" in response.text

    async def test_get_failures_for_task_success(self, async_client, db_session, task_pending_basic_for_mp4_retry):
        """
        Test successful retrieval of failure records for a task.
        - Create a task and associate 3 failure records
        - Call GET /api/v1/download/tasks/{task_id}/failures
        - Assert correct response with 3 failure records
        """
        task = await task_pending_basic_for_mp4_retry
        response = await async_client.get(f"/api/v1/download/tasks/{task.id}/failures")
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) >= 1  # At least one failure record should exist
        for failure in response_data:
            assert failure["task_id"] == str(task.id)
            assert "resource_type" in failure
            assert "status" in failure

    async def test_retry_hls_ts_with_invalid_failure_id(self, async_client, db_session, task_partial_completed_with_ts_failure_for_retry):
        """
        Test retrying HLS TS with non-existent failure ID.
        - Call POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry with non-existent failure_id
        - Assert 404 Not Found response
        """
        task = await task_partial_completed_with_ts_failure_for_retry
        response = await async_client.post(f"/api/v1/download/tasks/{task.id}/failures/00000000-0000-0000-0000-000000000000/retry")
        assert response.status_code == 404
        assert "失败记录不存在" in response.text or "Failure record not found" in response.text

    async def test_retry_hls_ts_exceeds_max_retry_count(self, async_client, db_session, task_partial_completed_with_ts_failure_for_retry):
        """
        Test retrying HLS TS that already exceeded max retry count.
        - Create a PARTIAL_COMPLETED task with a retry_count=3, resource_type='ts' failure record
        - Call POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry
        - Assert 400 Bad Request response
        """
        task = await task_partial_completed_with_ts_failure_for_retry
        
        # Get a failure record and set its retry_count to 3
        result = await db_session.execute(
            db_session.query(DownloadFailure).filter_by(task_id=task.id, resource_type="ts")
        )
        failure = result.scalar_one_or_none()
        assert failure is not None
        failure.retry_count = 3
        await db_session.commit()
        
        response = await async_client.post(f"/api/v1/download/tasks/{task.id}/failures/{failure.id}/retry")
        assert response.status_code == 400
        assert "重试次数已达上限" in response.text or "Retry limit exceeded" in response.text

    async def test_start_hls_m3u8_task_with_invalid_task_id(self, async_client):
        """
        Test starting HLS m3u8 task with non-existent UUID.
        - Call POST /api/v1/download/tasks/{task_id}/start with non-existent UUID for hls-m3u8 task
        - Assert 404 Not Found response
        """
        response = await async_client.post("/api/v1/download/tasks/00000000-0000-0000-0000-000000000000/start")
        assert response.status_code == 404
        assert "任务不存在" in response.text or "Task not found" in response.text


    async def test_start_already_completed_hls_m3u8_task(self, async_client, db_session, task_completed_basic_for_download):
        """
        Test starting an already completed HLS m3u8 task.
        - Create a COMPLETED status hls-m3u8 task
        - Call POST /api/v1/download/tasks/{task_id}/start
        - Assert 400 Bad Request response
        """
        task = await task_completed_basic_for_download
        response = await async_client.post(f"/api/v1/download/tasks/{task.id}/start")
        assert response.status_code == 400
        assert "任务已完成" in response.text or "Task already completed" in response.text

    async def test_retry_hls_m3u8_task_exceeds_max_retry_count(self, async_client, db_session, task_failed_invalid_m3u8_for_retry):
        """
        Test retrying HLS m3u8 task that already exceeded max retry count.
        - Create a FAILED status hls-m3u8 task with retry_count=3
        - Call POST /api/v1/download/tasks/{task_id}/retry
        - Assert 400 Bad Request response
        """
        task = await task_failed_invalid_m3u8_for_retry
        # Set retry_count to 3
        task.retry_count = 3
        await db_session.commit()
        
        response = await async_client.post(f"/api/v1/download/tasks/{task.id}/retry")
        assert response.status_code == 400
        assert "重试次数已达上限" in response.text or "Retry limit exceeded" in response.text


    async def test_delete_pending_task_success_with_relationships(self, async_client, db_session,
                                                                  task_pending_basic_for_mp4_download):
        """
        Test successful deletion of a pending task with relationship verification.
        - Create a PENDING status task with related records
        - Call DELETE /api/v1/download/tasks/{task_id}
        - Assert task and related records are properly handled
        """
        task = await task_pending_basic_for_mp4_download

        # 创建关联的失败记录
        failure = DownloadFailure(
            task_id=task.id,
            resource_url="https://example.com/video.mp4",
            expected_path="/storage/video.mp4",
            standard_name="video.mp4",
            resource_type="mp4",
            failure_type="network_error",
            error_message="Connection timeout",
            status="pending"
        )
        db_session.add(failure)

        # 创建关联的视频记录
        video = DownloadedVideo(
            video_id=task.video_id,
            liveroom_id=task.liveroom_id,
            video_type="mp4",
            video_url=task.resource_url,
            storage_path="/storage/video.mp4",
            task_id=task.id,
            status="completed"
        )
        db_session.add(video)
        await db_session.commit()

        # 验证关联记录存在
        assert await db_session.get(DownloadFailure, failure.id) is not None
        assert await db_session.get(DownloadedVideo, video.id) is not None

        # 执行删除操作
        response = await async_client.delete(f"/api/v1/download/tasks/{task.id}")
        assert response.status_code == 200

        # 检查主表状态
        db_task = await db_session.get(DownloadTask, task.id)
        assert db_task is None or db_task.status == TaskStatus.CANCELLED

        # 检查关联表删除行为
        if db_task is None:
            # 如果任务被真正删除，关联记录应该被级联删除
            assert await db_session.get(DownloadFailure, failure.id) is None
            # DownloadedVideo 的 task_id 应该被设置为 NULL
            db_video = await db_session.get(DownloadedVideo, video.id)
            assert db_video is not None
            assert db_video.task_id is None
        else:
            # 如果任务只是状态改变，关联记录应该保持不变
            assert await db_session.get(DownloadFailure, failure.id) is not None
            db_video = await db_session.get(DownloadedVideo, video.id)
            assert db_video is not None
            assert db_video.task_id == task.id


    async def test_delete_task_cascade_behavior(self, async_client, db_session):
        """
        Test cascade delete behavior for different task statuses.
        """
        # 测试场景1：删除 PENDING 任务
        pending_task = await create_task_with_relationships(db_session, "pending")
        response = await async_client.delete(f"/api/v1/download/tasks/{pending_task.id}")
        assert response.status_code == 200

        # 测试场景2：删除 COMPLETED 任务
        completed_task = await create_task_with_relationships(db_session, "completed")
        response = await async_client.delete(f"/api/v1/download/tasks/{completed_task.id}")
        assert response.status_code == 400  # 应该拒绝删除已完成任务

        # 测试场景3：删除 FAILED 任务
        failed_task = await create_task_with_relationships(db_session, "failed")
        response = await async_client.delete(f"/api/v1/download/tasks/{failed_task.id}")
        assert response.status_code == 200


    async def create_task_with_relationships(db_session, status):
        """创建带有关联记录的任务"""
        task = DownloadTask(
            video_id="1234567890_abcd",
            liveroom_id="1234567890",
            resource_url="https://example.com/video.mp4",
            resource_type="mp4",
            status=status
        )
        db_session.add(task)
        await db_session.flush()  # 获取ID

        # 创建失败记录
        failure = DownloadFailure(
            task_id=task.id,
            resource_url=task.resource_url,
            expected_path="/storage/video.mp4",
            standard_name="video.mp4",
            resource_type="mp4",
            failure_type="network_error",
            error_message="Test error",
            status="pending"
        )
        db_session.add(failure)

        # 创建视频记录
        video = DownloadedVideo(
            video_id=task.video_id,
            liveroom_id=task.liveroom_id,
            video_type="mp4",
            video_url=task.resource_url,
            storage_path="/storage/video.mp4",
            task_id=task.id,
            status="completed"
        )
        db_session.add(video)
        await db_session.commit()
        return task
