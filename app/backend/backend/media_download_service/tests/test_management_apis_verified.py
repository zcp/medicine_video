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
            video_id=uuid.uuid4(),
            user_id=user_id,
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000.mp4",
            resource_type="mp4",
            status=TaskStatus.PENDING
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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

async def task_pending_basic_for_invalid_mp4_url_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

    task = DownloadTask(
            video_id=uuid.uuid4(),
            user_id = user_id,
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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


async def task_pending_basic_for_invalid_mp4_url2_download(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id=uuid.uuid4(),
            user_id=user_id,
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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
            video_id=uuid.uuid4(),
            user_id = user_id,
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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

async def task_failed_m3u8_for_exceeds_limit(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 M3U8 文件无效的任务，用于测试首次访问失败场景。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id=uuid.uuid4(),
            user_id=user_id,
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
        expected_path=f"D:\\storage\\video_{task.video_id}\\hls",
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
            video_id=uuid.uuid4(),
            user_id=user_id,
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

async def task_partial_completed_with_invalid_segment_for_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id=uuid.uuid4(),
            user_id=user_id,
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

async def task_failed_ts_failure_threshold_exceeded_for_retry(session: AsyncSession, user_id: uuid.UUID) -> DownloadTask:
    """
    创建一个模拟 TS 文件下载失败比例过高的任务，判定为下载失败。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id=uuid.uuid4(),
            user_id=user_id,
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


async def test_get_task_details_success(async_client, db_session, test_user_id, auth_headers):
    """
    Test successful task details retrieval.
    - Create a task
    - Call GET /api/v1/download/tasks/{task_id}
    - Assert correct response data
    """
    async for client in async_client:
        async  for db in db_session:
            task = await task_pending_basic_for_mp4_download(db, test_user_id)
            response = await client.get(f"/api/v1/download/tasks/{task.id}", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["code"] == 200
            response_data = response.json()["data"]
            print("API response:", response_data)
            assert response_data["id"] == str(task.id)
            assert response_data["status"] == "pending"
            assert response_data["resource_url"] == task.resource_url
            assert response_data["resource_type"] == task.resource_type

async def test_get_task_details_not_found(async_client, auth_headers):
        """
        Test task details retrieval with non-existent task ID.
        - Call GET /api/v1/download/tasks/{task_id} with non-existent ID
        - Assert 404 Not Found response
        """
        async for client in async_client:
            response = await client.get("/api/v1/download/tasks/00000000-0000-0000-0000-000000000000", headers=auth_headers)
            print("API response:", response.json())
            assert response.status_code == 200
            assert response.json()["code"] == 400
            error_keywords = ["not found", "不存在", "Task not found", "任务不存在"]
            assert any(keyword in response.text for keyword in error_keywords)

async def test_delete_pending_task_success(async_client, db_session,test_user_id,auth_headers):
    """
    Test successful deletion of a pending task.
    - Create a PENDING status task
    - Call DELETE /api/v1/download/tasks/{task_id}
    - Assert task is cancelled or deleted
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_pending_basic_for_mp4_download(db, test_user_id)
            response = await client.delete(f"/api/v1/download/tasks/{task.id}", headers=auth_headers)
            print("API response:", response.json())
            assert response.status_code == 200

            result = await db.execute(
                select(DownloadTask).filter_by(id=task.id)
            )
            assert result.scalar_one_or_none() is None

async def test_delete_non_deletable_task_fails(async_client, db_session, test_user_id, auth_headers):
        """
        Test deletion fails for non-deletable task statuses.
        - Create a COMPLETED or PROCESSING status task
        - Call DELETE /api/v1/download/tasks/{task_id}
        - Assert 400 Bad Request or 409 Conflict response
        """
        async for client in async_client:
            async for db in db_session:
                completed_task = await task_completed_basic_for_mp4_download(db,test_user_id)
                response = await client.delete(f"/api/v1/download/tasks/{completed_task.id}", headers=auth_headers)
                print("API response:", response.json())
                assert response.status_code == 200
                assert response.json()['code'] == 400
                assert "不能删除已完成任务" in response.text


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

async def test_retry_hls_ts_with_invalid_failure_id(async_client, db_session, test_user_id, auth_headers):
        """
        Test retrying HLS TS with non-existent failure ID.
        - Call POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry with non-existent failure_id
        - Assert 404 Not Found response
        """
        async for client in async_client:
            async for db in db_session:
                task = await task_partial_completed_with_ts_failure_for_retry(db,test_user_id)
                response = await client.post(
                    f"/api/v1/download/tasks/{task.id}/failures/00000000-0000-0000-0000-000000000000/retry", headers=auth_headers)
                print("API response:", response.json())
                assert response.status_code == 200
                assert response.json()["code"] == 400
                assert "不存在" in response.text

async def test_retry_hls_ts_exceeds_max_retry_count(async_client, db_session, test_user_id, auth_headers):
    """
    Test retrying HLS TS that already exceeded max retry count.
    - Create a PARTIAL_COMPLETED task with a retry_count=3, resource_type='ts' failure record
    - Call POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry
    - Assert 400 Bad Request response
    """
    async for client in async_client:
        async for db in db_session:
            task = await task_partial_completed_with_ts_failure_for_retry(db,test_user_id)

            # Get a failure record and set its retry_count to 3
            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id, resource_type="ts")
            )
            failure = result.scalar_one_or_none()
            assert failure is not None
            failure.retry_count = 3
            await db.commit()

            response = await client.post(f"/api/v1/download/tasks/{task.id}/failures/{failure.id}/retry", headers=auth_headers)
            print("API response",response.json())
            assert response.status_code == 200
            assert response.json()["code"] == 400

            #assert "重试次数已达上限" in response.text or "Retry limit exceeded" in response.text

async def test_start_hls_m3u8_task_with_invalid_task_id(async_client, db_session,test_user_id, auth_headers):
        """
        Test starting HLS m3u8 task with non-existent UUID.
        - Call POST /api/v1/download/tasks/{task_id}/start with non-existent UUID for hls-m3u8 task
        - Assert 404 Not Found response
        """
        async for client in async_client:
            response = await client.post("/api/v1/download/tasks/00000000-0000-0000-0000-000000000000/start", headers=auth_headers)
            print("API response:", response.json())
            assert response.status_code == 200
            assert response.json()["code"] == 400
            assert "不存在" in response.text

async def test_delete_pending_task_success_with_relationships(async_client, db_session, test_user_id, auth_headers):
    """
    Test successful deletion of a pending task with relationship verification.
    - Create a PENDING status task with related records
    - Call DELETE /api/v1/download/tasks/{task_id}
    - Assert task and related records are properly handled
    """
    async for client in async_client:
        async for  db in db_session:

            task = await task_pending_basic_for_mp4_download(db,test_user_id)

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

            db.add(failure)

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
            db.add(video)
            await db.commit()

            # 验证关联记录存在
            await db.refresh(failure)
            await db.refresh(video)

            result = await db.execute(
                select(DownloadFailure).filter_by(task_id=task.id, resource_type="mp4")
            )
            failure = result.scalar_one_or_none()
            assert failure is not None

            result = await db.execute(
                select(DownloadedVideo).filter_by(task_id=task.id, video_type="mp4")
            )
            video = result.scalar_one_or_none()
            assert video is not None

            # 执行删除操作
            response = await client.delete(f"/api/v1/download/tasks/{task.id}", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["code"] == 200

            print("API response:", response.json())
            # 检查主表状态
            result = await db.execute(
                select(DownloadTask).filter_by(id=task.id)
            )
            assert result.scalar_one_or_none() is None

            # 检查关联表删除行为
            if result.scalar_one_or_none() is None:
                # 如果任务被真正删除，关联记录应该被级联删除
                print("Aaaaaa")

                result = await db.execute(
                    select(DownloadedVideo).filter_by(id=video.id)
                )

                video_obj = result.scalar_one_or_none()
                #print("xxxxx",video_obj.id, video_obj.task_id)
                assert video_obj is None  # 记录不在了

                result = await db.execute(
                    select(DownloadFailure).filter_by(task_id=task.id)
                )
                assert result.scalar_one_or_none() is None