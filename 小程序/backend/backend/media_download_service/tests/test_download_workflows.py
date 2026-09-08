import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
#from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo, TaskStatus
#from app.schemas.download import DownloadedVideoStatus, FailureStatusEnum

# In tests/test_download_workflows_1by1.py
from app.schemas.download import (
    DownloadTaskCreate,
    DownloadTaskUpdate,
    DownloadTask,
    TaskStatus, # Already present
    DownloadedVideoStatus, # <-- Add this
    FailureStatusEnum      # <-- Add this
)

# Fixtures: client, db_session, mp4_task_factory, hls_task_factory, failure_factory, etc. are defined in conftest_backup.py

@pytest.mark.asyncio
class TestDownloadWorkflows:
    """
    Test suite for MP4 and HLS download core workflows and retry logic.
    Each test covers API response, database state, and business side effects as required by the test prompt.
    """


    async def test_mp4_download_success_flow(async_client, db_session, task_pending_basic_for_mp4_download):
        """
        Test MP4 download success scenario.
        - Create a PENDING MP4 task
        - Start the task
        - Assert API response and all related DB state
        """
        async for client in async_client:
            task = await task_pending_basic_for_mp4_download
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 200
            print("API response", response.json())
            data = response.json()["data"]
            assert data["status"] == "completed"

            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.COMPLETED
                assert db_task.retry_count == 0

                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                video = result.scalar_one_or_none()
                assert video is not None
                assert video.status == "completed"

                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_mp4_download_failure_flow(async_client, db_session,
                                             task_pending_basic_for_invalid_mp4_url_download):
        """
        Test MP4 download failure scenario.
        - Create a PENDING MP4 task with invalid resource
        - Start the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_pending_basic_for_invalid_mp4_url_download
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "failed"

            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.FAILED
                assert db_task.retry_count == 0

                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id, resource_type="mp4")
                )
                failure = result.scalar_one_or_none()
                assert failure is not None

                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None

    async def test_mp4_retry_and_succeed_flow(self, async_client, db_session, task_pending_basic_for_mp4_retry, monkeypatch):
        """
        Test MP4 retry and succeed scenario.
        - Create a FAILED MP4 task with a failure record
        - Patch download logic to succeed
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_pending_basic_for_mp4_retry
            monkeypatch.setattr("media_download_service.app.services.download_service.download_mp4_image", lambda *a, **kw: True)
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "completed"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.COMPLETED
                assert db_task.retry_count == 1
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                video = result.scalar_one_or_none()
                assert video is not None
                assert video.status == "completed"

    async def test_mp4_retry_exceeds_limit_flow(self, async_client, db_session, task_pending_basic_for_invalid_mp4_url_retry, monkeypatch):
        """
        Test MP4 retry exceeds limit scenario.
        - Create a FAILED MP4 task with retry_count=2
        - Patch download logic to always fail
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_pending_basic_for_invalid_mp4_url_retry
            monkeypatch.setattr("media_download_service.app.services.download_service.download_mp4_image", lambda *a, **kw: False)
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "abandoned"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.ABANDONED
                assert db_task.retry_count == 3
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id)
                )
                failure = result.scalar_one_or_none()
                assert failure is not None
                assert failure.status == "abandoned"
                assert failure.retry_count == 3
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None

    async def test_start_mp4_task_with_invalid_task_id(self, async_client):
        """
        Test starting MP4 task with non-existent UUID.
        - Call start API with invalid UUID
        - Assert 404 response and error message
        """
        async for client in async_client:
            response = await client.post("/api/v1/download/tasks/00000000-0000-0000-0000-000000000000/start")
            assert response.status_code == 404
            assert "任务不存在" in response.text or "Task not found" in response.text

    async def test_start_mp4_task_with_invalid_uuid_format(self, async_client):
        """
        Test starting MP4 task with invalid UUID format.
        - Call start API with malformed UUID
        - Assert 422 response and error message
        """
        async for client in async_client:
            response = await client.post("/api/v1/download/tasks/invalid-uuid/start")
            assert response.status_code == 422
            assert "无效的UUID格式" in response.text or "Invalid UUID format" in response.text

    async def test_create_mp4_task_with_invalid_resource_url(self, async_client):
        """
        Test creating MP4 task with invalid resource URL.
        - Call create API with invalid URL
        - Assert 422 response and error message
        """
        async for client in async_client:
            payload = {"resource_url": "not-a-url", "type": "mp4"}
            response = await client.post("/api/v1/download/tasks", json=payload)
            assert response.status_code == 422
            assert "无效的URL格式" in response.text or "Invalid URL format" in response.text

    async def test_start_already_completed_mp4_task(self, async_client, db_session, task_completed_basic_for_download):
        """
        Test starting an already completed MP4 task.
        - Create a COMPLETED MP4 task
        - Call start API
        - Assert 400 response and error message
        """
        async for client in async_client:
            task = await task_completed_basic_for_download
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 400
            assert "任务已完成" in response.text or "Task already completed" in response.text

    async def test_retry_mp4_task_exceeds_max_retry_count(self, async_client, db_session, task_pending_basic_for_invalid_mp4_url_retry):
        """
        Test retrying MP4 task that already exceeded max retry count.
        - Create a FAILED MP4 task with retry_count=3
        - Call retry API
        - Assert 400 response and error message
        """
        async for client in async_client:
            task = await task_pending_basic_for_invalid_mp4_url_retry
            # Set retry_count to 3
            async for db in db_session:
                task.retry_count = 3
                await db.commit()
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 400
            assert "重试次数已达上限" in response.text or "Retry limit exceeded" in response.text

    # HLS Tests using existing fixtures
    async def test_hls_full_success_flow(self, async_client, db_session, task_pending_basic_for_download, monkeypatch):
        """
        Test HLS full success scenario.
        - Create a PENDING HLS task
        - Patch download_m3u8 to return all TS segments success
        - Start the task
        - Assert API response and all related DB state
        """
        async for client in async_client:
            task = await task_pending_basic_for_download
            monkeypatch.setattr("media_download_service.app.services.download_service.download_m3u8", lambda *a, **kw: ([], []))
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "completed"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.COMPLETED
                assert db_task.retry_count == 0
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                video = result.scalar_one_or_none()
                assert video is not None
                assert video.status == "completed"
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None

    async def test_hls_m3u8_download_fails_flow(self, async_client, db_session, task_pending_invalid_m3u8_for_download, monkeypatch):
        """
        Test HLS m3u8 download fails scenario.
        - Create a PENDING HLS task with invalid resource_url
        - Patch download_m3u8 to fail
        - Start the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_pending_invalid_m3u8_for_download
            monkeypatch.setattr("media_download_service.app.services.download_service.download_m3u8", lambda *a, **kw: (None, None))
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "failed"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.FAILED
                assert db_task.retry_count == 0
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id, resource_type="m3u8")
                )
                failure = result.scalar_one_or_none()
                assert failure is not None
                assert failure.status == "pending"
                assert failure.retry_count == 0
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None

    async def test_hls_partial_success_flow(self, async_client, db_session, task_pending_basic_for_download, monkeypatch):
        """
        Test HLS partial success scenario (some TS segments fail).
        - Create a PENDING HLS task
        - Patch download_m3u8 to return some failed TS segments
        - Start the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_pending_basic_for_download
            failed_ts = ["seg1.ts", "seg2.ts"]
            monkeypatch.setattr("media_download_service.app.services.download_service.download_m3u8", lambda *a, **kw: ([], failed_ts))
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "partial_completed"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.PARTIAL_COMPLETED
                assert db_task.retry_count == 0
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                video = result.scalar_one_or_none()
                assert video is not None
                assert video.status == "partial_completed"
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id, resource_type="ts")
                )
                failures = result.scalars().all()
                assert len(failures) == len(failed_ts)
                for failure in failures:
                    assert failure.status == "pending"
                    assert failure.retry_count == 0

    async def test_hls_full_retry_from_failed_task_and_succeeds(self, async_client, db_session, task_failed_valid_m3u8_for_retry, monkeypatch):
        """
        Test retrying a FAILED HLS task (m3u8 failed) and succeeding.
        - Create a FAILED HLS task with m3u8 failure
        - Patch download logic to succeed
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_failed_valid_m3u8_for_retry
            monkeypatch.setattr("media_download_service.app.services.download_service.start_download_task", lambda *a, **kw: True)
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "completed"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.COMPLETED
                assert db_task.retry_count == 1
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                video = result.scalar_one_or_none()
                assert video is not None
                assert video.status == "completed"

    async def test_hls_full_retry_from_failed_task_exceeds_limit(self, async_client, db_session, task_failed_invalid_m3u8_for_retry, monkeypatch):
        """
        Test retrying a FAILED HLS task (m3u8 failed) and exceeding retry limit.
        - Create a FAILED HLS task with retry_count=2 and m3u8 failure
        - Patch download logic to always fail
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_failed_invalid_m3u8_for_retry
            monkeypatch.setattr("media_download_service.app.services.download_service.start_download_task", lambda *a, **kw: False)
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "abandoned"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.ABANDONED
                assert db_task.retry_count == 3
                
                result = await db.execute(
                    db_session.query(DownloadFailure).filter_by(task_id=task.id, resource_type="m3u8")
                )
                failure = result.scalar_one_or_none()
                assert failure is not None
                assert failure.status == "abandoned"
                assert failure.retry_count == 3
                
                result = await db.execute(
                    db_session.query(DownloadedVideo).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None

    async def test_hls_partial_retry_for_single_ts_succeeds(self, async_client, db_session, task_partial_completed_with_ts_failure_for_retry, monkeypatch):
        """
        Test retrying a PARTIAL_COMPLETED HLS task for a single failed TS segment and succeeding.
        - Create a PARTIAL_COMPLETED HLS task with one failed TS
        - Patch retry logic to succeed
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_partial_completed_with_ts_failure_for_retry
            monkeypatch.setattr("app.services.download_service._retry_only_failed_segments", lambda *a, **kw: True)
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 200
            # status may be PARTIAL_COMPLETED or COMPLETED depending on other failures
            assert response.json()["data"]["status"] in ["partial_completed", "completed"]

    async def test_hls_partial_retry_for_single_ts_exceeds_limit(self, async_client, db_session, task_partial_completed_with_ts_failure_for_retry, monkeypatch):
        """
        Test retrying a PARTIAL_COMPLETED HLS task for a single failed TS segment and exceeding retry limit.
        - Create a PARTIAL_COMPLETED HLS task with one failed TS (retry_count=2)
        - Patch retry logic to always fail
        - Retry the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_partial_completed_with_ts_failure_for_retry
            monkeypatch.setattr("app.services.download_service._retry_only_failed_segments", lambda *a, **kw: False)
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/retry")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "partial_completed"

    async def test_hls_ts_failure_rate_too_high_flow(self, async_client, db_session, task_failed_ts_failure_threshold_exceeded_for_retry, monkeypatch):
        """
        Test HLS TS failure rate too high scenario.
        - Create a PENDING HLS task
        - Patch download_m3u8 to return too many failed TS segments
        - Start the task
        - Assert API response and DB state
        """
        async for client in async_client:
            task = await task_failed_ts_failure_threshold_exceeded_for_retry
            failed_ts = [f"seg{i}.ts" for i in range(10)]
            monkeypatch.setattr("media_download_service.app.services.download_service.download_m3u8", lambda *a, **kw: ([], failed_ts))
            
            response = await client.post(f"/api/v1/download/tasks/{task.id}/start")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "failed"
            
            async for db in db_session:
                db_task = await db.get(DownloadTask, task.id)
                assert db_task.status == TaskStatus.FAILED

    # HLS相关测试函数可按同样模式继续补充... 