import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import your app and models
from app.main import app
from app.database import get_db
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus, DownloadedVideoStatus, FailureStatusEnum


# Your helper function (this is correct, no changes needed here)
async def create_invalid_m3u8_task(session: AsyncSession) -> DownloadTask:
    task = DownloadTask(
        video_id="1234567891_abfe",
        liveroom_id="1234567891",
        resource_url="https://lancet.im/videos/194_1080p_5000/playlist11.m3u8",
        resource_type="hls",
        status=TaskStatus.PENDING
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

async def task_pending_basic_for_mp4_download(db_session: AsyncSession) -> DownloadTask:
        """
       创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
       """

        task = DownloadTask(
            video_id="1234567890_abcd",
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

async def task_pending_basic_for_invalid_mp4_url_retry(session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
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

async def task_pending_basic_for_invalid_mp4_url_download(session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

    task = DownloadTask(
            video_id="1234567890_abcd",
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

async def task_failed_basic_for_mp4_retry(session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 FAILED 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

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


async def task_pending_basic_for_invalid_mp4_url2_download(session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id="1234567890_abcd",
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

async def task_completed_basic_for_mp4_download(session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象

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


async def task_pending_basic_for_download(session: AsyncSession) -> DownloadTask:
    """
      创建一个最基本的 PENDING 状态的下载任务，用于测试普通流程。
      """
    # 先 await db_session 获取会话对象
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

async def task_pending_invalid_m3u8_for_download(session: AsyncSession) -> DownloadTask:
    """
    创建一个 M3U8 文件无效的任务，用于测试首次访问失败场景。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id="1234567891_abfe",
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

async def task_partial_completed_hls(session: AsyncSession) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id="1234567890_adce",
            liveroom_id="1234567890",
            resource_url="https://lancet.im/videos/194_1080p_5000/playlist_partial_completed.m3u8",
            resource_type="hls",
            status=TaskStatus.PARTIAL_COMPLETED
        )
    session.add(task)
    await session.commit()

    return task

async def task_failed_valid_m3u8_for_retry(session: AsyncSession) -> DownloadTask:
    """
    创建一个 FAILED 状态的任务，资源地址有效，可用于模拟重试恢复。
    """
    # 先 await db_session 获取会话对象
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

async def task_failed_m3u8_for_exceeds_limit(session: AsyncSession) -> DownloadTask:
    """
    创建一个 M3U8 文件无效的任务，用于测试首次访问失败场景。
    """
    # 先 await db_session 获取会话对象
    task = DownloadTask(
            video_id="1234567891_abfe",
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

async def task_partial_completed_with_ts_failure_for_retry(session: AsyncSession) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
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

async def task_partial_completed_with_invalid_segment_for_retry(session: AsyncSession) -> DownloadTask:
    """
    创建一个 PARTIAL_COMPLETED 任务 + 一个失败段，用于模拟断点续传。
    """
    # 先 await db_session 获取会话对象
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

async def task_failed_ts_failure_threshold_exceeded_for_retry(session: AsyncSession) -> DownloadTask:
    """
    创建一个模拟 TS 文件下载失败比例过高的任务，判定为下载失败。
    """
    # 先 await db_session 获取会话对象
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
    return task

