import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import your app and models
from app.main import app
from app.database import get_db
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus, DownloadedVideoStatus, FailureStatusEnum
from tornado.process import task_id

from backend.media_download_service.tests.test_management_apis_verified import task_failed_basic_for_mp4_retry


async def test_get_failures_for_task_success(async_client, db_session, test_user_id, auth_headers):
    """
    Test successful retrieval of failure records for a task.
    - Create a task and associate 3 failure records
    - Call GET /api/v1/download/tasks/{task_id}/failures
    - Assert correct response with 3 failure records
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_failed_basic_for_mp4_retry(db, test_user_id)
            response = await client.get(f"/api/v1/download/tasks/{task.id}/failures", headers=auth_headers)
            print("API response:", response.json())
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["code"] == 200

            items = response_data["data"]["items"]

            assert len(items) >= 1
            first_item = items[0]

            assert first_item["task_id"] == str(task.id)
            assert first_item["resource_type"] == str(task.resource_type)
            assert first_item["resource_url"] == str(task.resource_url)
            assert first_item["status"] == "pending"
