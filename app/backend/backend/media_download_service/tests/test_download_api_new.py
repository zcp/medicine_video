import pytest
import uuid
import asyncio
import time
from datetime import datetime, timedelta
from faker import Faker
import random

# FastAPI 测试相关
from httpx import AsyncClient

# SQLAlchemy 异步支持
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# 应用模型和枚举
from app.models.download import DownloadTask, DownloadFailure, DownloadedVideo
from app.schemas.download import TaskStatus, FailureStatusEnum

from backend.media_download_service.tests.conftest import test_user_id, auth_headers

# 确保导入所有必要的测试fixture
# 注意：这些fixture应该在conftest.py中已经定义
# async_client, db_session, test_app 等

fake = Faker()


def create_test_download_task(db_session,
                              user_id,
                              status=TaskStatus.COMPLETED,
                              video_id=None):
    """创建测试用的DownloadTask数据"""
    if video_id is None:
        video_id = uuid.uuid4()
    
    task_data = {
        "video_id": video_id,
        "user_id":  user_id,
        "liveroom_id": f"room_{fake.random_int(min=1000, max=9999)}",
        "liveroom_title": fake.sentence(nb_words=4),
        "liveroom_url": fake.url(),
        "resource_url": fake.url(),
        "resource_type": random.choice(["hls", "mp4", "image"]),
        "status": status,
        "progress": 1.0 if status == TaskStatus.COMPLETED else 0.0,
        "retry_count": 0,
        "last_error": None,
        "created_at": datetime.utcnow() - timedelta(hours=1),
        "updated_at": datetime.utcnow()
    }
    return DownloadTask(**task_data)


def create_test_downloaded_video(db_session, task_id, video_id):
    """创建测试用的DownloadedVideo数据"""
    video_data = {
        "video_id": video_id,
        "task_id": task_id,
        "liveroom_id": f"room_{fake.random_int(min=1000, max=9999)}",
        "liveroom_title": fake.sentence(nb_words=4),
        "liveroom_url": fake.url(),
        "video_type": "hls",
        "video_url": fake.url(),
        "storage_path": f"/media/video_{video_id}/hls/",
        "file_size": fake.random_int(min=1000000, max=5000000000),
        "duration": fake.random_int(min=300, max=7200),
        "resolution": random.choice(["720p", "1080p", "1440p"]),
        "format": "hls",
        "status": "completed",
        "created_at": datetime.utcnow(),
        "download_end_time": datetime.utcnow()
    }
    return DownloadedVideo(**video_data)


def create_test_download_failure(db_session, task_id, status="pending", failure_type="network_error"):
    """创建测试用的DownloadFailure数据"""
    failure_data = {
        "task_id": task_id,
        "resource_url": fake.url(),
        "expected_path": f"/media/downloads/{fake.uuid4()}/ts/",
        "standard_name": f"segment_{fake.random_int(min=1, max=999):06d}_{uuid.uuid4().hex[:8]}.ts",
        "resource_type": random.choice(["ts", "m3u8", "mp4", "image"]),
        "failure_type": failure_type,
        "error_message": fake.sentence(nb_words=8),
        "status": status,
        "retry_count": fake.random_int(min=0, max=3),
        "created_at": datetime.utcnow() - timedelta(minutes=30),
        "updated_at": datetime.utcnow()
    }
    return DownloadFailure(**failure_data)


class TestDownloadApiNew:
    """新增下载服务API接口测试类"""

    # ===== GET /videos/{video_id} API 测试 =====

    @pytest.mark.asyncio
    async def test_get_downloaded_video_success(self, async_client, db_session, test_user_id, auth_headers):
        """测试成功获取已下载视频详情"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                # 1. 清空相关表数据
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 2. 创建测试数据
                test_video_id = uuid.uuid4()
                test_task = create_test_download_task(db, test_user_id, status=TaskStatus.COMPLETED, video_id=test_video_id)
                db.add(test_task)
                await db.commit()
                await db.refresh(test_task)
                
                test_video = create_test_downloaded_video(db, test_task.id, test_video_id)
                db.add(test_video)
                await db.commit()
                await db.refresh(test_video)
                
                # === 执行 (Act) ===
                response = await client.get(f"/api/v1/download/videos/{test_video_id}", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                assert response_data["message"] == "获取已下载视频详情成功"
                
                # 验证返回的视频数据
                video_data = response_data["data"]
                assert video_data["video_id"] == str(test_video_id)
                assert video_data["liveroom_id"] == test_video.liveroom_id
                assert video_data["storage_path"] == test_video.storage_path
                assert video_data["status"] == "completed"
                assert "created_at" in video_data

                #assert "download_end_time" in video_data
                
                # === 数据库状态验证 ===
                result = await db.execute(
                    select(DownloadedVideo).where(DownloadedVideo.video_id == test_video_id)
                )
                db_video = result.scalar_one_or_none()
                assert db_video is not None
                assert db_video.status == "completed"
                assert db_video.storage_path == test_video.storage_path

    @pytest.mark.asyncio
    async def test_get_downloaded_video_not_found(self, async_client, db_session,  auth_headers):
        """测试查询不存在的视频返回404"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                # 清空数据库确保没有数据
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 使用不存在的video_id
                non_existent_video_id = uuid.uuid4()
                
                # === 执行 (Act) ===
                response = await client.get(f"/api/v1/download/videos/{non_existent_video_id}", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.json()["code"] == 404
                error_data = response.json()
                assert "不存在" in error_data.get("message", "")

    @pytest.mark.asyncio
    async def test_get_downloaded_video_invalid_uuid_format(self, async_client, auth_headers):
        """测试使用无效UUID格式调用API返回422"""
        async for client in async_client:
            # === 执行 (Act) ===
            response = await client.get("/api/v1/download/videos/invalid-uuid", headers=auth_headers)
            
            # === 断言 (Assert) ===
            assert response.status_code == 422
            error_data = response.json()
            assert "detail" in error_data

    # ===== GET /failures API 测试 =====

    @pytest.mark.asyncio
    async def test_list_all_failures_success_with_data(self, async_client, db_session, test_user_id, auth_headers):
        """测试成功获取失败记录列表（有数据）"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                # 1. 清空相关表数据
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 2. 创建测试数据：3个任务，每个任务2条失败记录
                tasks = []
                for i in range(3):
                    task = create_test_download_task(db, test_user_id, status=TaskStatus.FAILED)
                    db.add(task)
                    tasks.append(task)
                
                await db.commit()
                for task in tasks:
                    await db.refresh(task)
                
                # 为每个任务创建2条失败记录
                failures = []
                for task in tasks:
                    for j in range(2):
                        failure = create_test_download_failure(
                            db, 
                            task.id, 
                            status=random.choice(["pending", "abandoned"]),
                            failure_type=random.choice(["network_error", "timeout"])
                        )
                        db.add(failure)
                        failures.append(failure)
                
                await db.commit()
                
                # === 执行 (Act) ===
                response = await client.get("/api/v1/download/failures?page=1&size=10", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                assert response_data["message"] == "获取全局失败记录列表成功"
                
                # 验证分页数据
                data = response_data["data"]
                assert data["total"] == 6  # 3个任务 × 2条失败记录
                assert len(data["items"]) == 6
                
                # 验证每个失败记录包含必要字段
                for item in data["items"]:
                    assert "failure_id" in item or "id" in item
                    assert "task_id" in item
                    assert "resource_url" in item
                    assert "failure_type" in item
                    assert "status" in item

    @pytest.mark.asyncio
    async def test_list_all_failures_with_status_filter(self, async_client, db_session, test_user_id,auth_headers):
        """测试按状态筛选失败记录"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 创建任务
                task = create_test_download_task(db, test_user_id,status=TaskStatus.FAILED)
                db.add(task)
                await db.commit()
                await db.refresh(task)
                
                # 创建不同状态的失败记录
                pending_failures = []
                abandoned_failures = []
                
                for i in range(2):
                    pending_failure = create_test_download_failure(db, task.id, status="pending")
                    db.add(pending_failure)
                    pending_failures.append(pending_failure)
                    
                    abandoned_failure = create_test_download_failure(db, task.id, status="abandoned")
                    db.add(abandoned_failure)
                    abandoned_failures.append(abandoned_failure)
                
                await db.commit()
                
                # === 执行 (Act) ===
                response = await client.get("/api/v1/download/failures?status=pending", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                
                data = response_data["data"]
                assert data["total"] == 2
                
                # 验证所有返回的记录状态都为pending
                for item in data["items"]:
                    assert item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_all_failures_with_failure_type_filter(self, async_client, db_session, test_user_id ,auth_headers):
        """测试按失败类型筛选失败记录"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 创建任务
                task = create_test_download_task(db, test_user_id,status=TaskStatus.FAILED)
                db.add(task)
                await db.commit()
                await db.refresh(task)
                
                # 创建不同类型的失败记录
                for i in range(2):
                    network_failure = create_test_download_failure(db, task.id, failure_type="network_error")
                    db.add(network_failure)
                    
                    timeout_failure = create_test_download_failure(db, task.id, failure_type="timeout")
                    db.add(timeout_failure)
                
                await db.commit()
                
                # === 执行 (Act) ===
                response = await client.get("/api/v1/download/failures?failure_type=network_error", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                
                data = response_data["data"]
                assert data["total"] == 2
                
                # 验证所有返回的记录类型都为network_error
                for item in data["items"]:
                    assert item["failure_type"] == "network_error"

    @pytest.mark.asyncio
    async def test_list_all_failures_pagination(self, async_client, db_session, test_user_id ,auth_headers):
        """测试失败记录分页功能"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 创建任务
                task = create_test_download_task(db, test_user_id, status=TaskStatus.FAILED)
                db.add(task)
                await db.commit()
                await db.refresh(task)
                
                # 创建15条失败记录
                for i in range(15):
                    failure = create_test_download_failure(db, task.id)
                    db.add(failure)
                
                await db.commit()
                
                # === 执行 (Act) ===
                # 测试第一页
                response1 = await client.get("/api/v1/download/failures?page=1&size=10", headers=auth_headers)
                # 测试第二页
                response2 = await client.get("/api/v1/download/failures?page=2&size=10", headers=auth_headers)
                
                # === 断言 (Assert) ===
                # 第一页
                assert response1.status_code == 200
                data1 = response1.json()["data"]
                assert data1["total"] == 15
                assert len(data1["items"]) == 10
                
                # 第二页
                assert response2.status_code == 200
                data2 = response2.json()["data"]
                assert data2["total"] == 15
                assert len(data2["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_all_failures_empty_result(self, async_client, db_session, auth_headers):
        """测试查询失败记录返回空结果"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                # 确保数据库中没有失败记录
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # === 执行 (Act) ===
                response = await client.get("/api/v1/download/failures", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                
                data = response_data["data"]
                assert data["total"] == 0
                assert data["items"] == []

    # ===== GET /failures/{failure_id} API 测试 =====

    @pytest.mark.asyncio
    async def test_get_failure_details_success(self, async_client, db_session, test_user_id, auth_headers):
        """测试成功获取单个失败记录详情"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 创建任务
                task = create_test_download_task(db, test_user_id,status=TaskStatus.FAILED)
                db.add(task)
                await db.commit()
                await db.refresh(task)
                
                # 创建失败记录
                failure = create_test_download_failure(
                    db, 
                    task.id, 
                    status="pending", 
                    failure_type="network_error"
                )
                failure.retry_count = 1
                failure.standard_name = f"segment_{fake.random_int(min=1, max=999):06d}_{uuid.uuid4().hex[:8]}.ts"
                failure.expected_path = f"/media/downloads/{task.id}/ts/"
                db.add(failure)
                await db.commit()
                await db.refresh(failure)
                
                # === 执行 (Act) ===
                response = await client.get(f"/api/v1/download/failures/{failure.id}", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] == 200
                assert response_data["message"] == "获取失败记录详情成功"
                
                # 验证失败记录详情
                failure_data = response_data["data"]
                assert failure_data["failure_id"] == str(failure.id) or failure_data["id"] == str(failure.id)
                assert failure_data["task_id"] == str(failure.task_id)
                assert failure_data["resource_url"] == failure.resource_url
                assert failure_data["standard_name"] == failure.standard_name
                assert failure_data["expected_path"] == failure.expected_path
                assert failure_data["retry_count"] == 1
                assert "created_at" in failure_data
                assert "updated_at" in failure_data
                
                # === 数据库状态验证 ===
                result = await db.execute(
                    select(DownloadFailure).where(DownloadFailure.id == failure.id)
                )
                db_failure = result.scalar_one_or_none()
                assert db_failure is not None
                assert db_failure.status == "pending"
                assert db_failure.failure_type == "network_error"

    @pytest.mark.asyncio
    async def test_get_failure_details_not_found(self, async_client, db_session, auth_headers):
        """测试查询不存在的失败记录返回404"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 使用不存在的failure_id
                non_existent_failure_id = uuid.uuid4()
                
                # === 执行 (Act) ===
                response = await client.get(f"/api/v1/download/failures/{non_existent_failure_id}", headers=auth_headers)
                
                # === 断言 (Assert) ===
                assert response.json()["code"] == 404
                error_data = response.json()
                assert "不存在" in error_data.get("message", "")

    @pytest.mark.asyncio
    async def test_get_failure_details_invalid_uuid_format(self, async_client, auth_headers):
        """测试使用无效UUID格式查询失败记录返回422"""
        async for client in async_client:
            # === 执行 (Act) ===
            response = await client.get("/api/v1/download/failures/invalid-uuid", headers=auth_headers)
            
            # === 断言 (Assert) ===
            assert response.status_code == 422
            error_data = response.json()
            assert "detail" in error_data

    # ===== 边界条件测试 =====

    @pytest.mark.asyncio
    async def test_api_endpoints_with_sql_injection_attempts(self, async_client, auth_headers):
        """测试API接口的SQL注入防护"""
        async for client in async_client:
            # 尝试SQL注入攻击
            malicious_inputs = [
                "'; DROP TABLE download_tasks--",
                "' OR '1'='1",
                "1; DELETE FROM download_failures--"
            ]
            
            for malicious_input in malicious_inputs:
                # 测试视频详情接口
                response1 = await client.get(f"/api/v1/download/videos/{malicious_input}", headers=auth_headers)
                assert response1.status_code in [400, 422]  # 应该被参数验证拦截
                
                # 测试失败记录详情接口
                response2 = await client.get(f"/api/v1/download/failures/{malicious_input}", headers=auth_headers)
                assert response2.status_code in [400, 422]  # 应该被参数验证拦截

    @pytest.mark.asyncio
    async def test_api_endpoints_with_extremely_long_parameters(self, async_client, auth_headers):
        """测试API接口处理超长参数的能力"""
        async for client in async_client:
            # 生成超长字符串（1000个字符）
            extremely_long_param = "a" * 1000
            
            # 测试视频详情接口
            response1 = await client.get(f"/api/v1/download/videos/{extremely_long_param}", headers=auth_headers)
            assert response1.status_code in [400, 422]
            
            # 测试失败记录详情接口
            response2 = await client.get(f"/api/v1/download/failures/{extremely_long_param}", headers=auth_headers)
            assert response2.status_code in [400, 422]

    # ===== 性能测试 =====

    @pytest.mark.asyncio
    async def test_api_response_time_benchmark(self, async_client, db_session, test_user_id, auth_headers):
        """测试API响应时间基准"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 创建一些测试数据
                task = create_test_download_task(db, test_user_id, status=TaskStatus.FAILED)
                db.add(task)
                await db.commit()
                await db.refresh(task)
                
                for i in range(10):
                    failure = create_test_download_failure(db, task.id)
                    db.add(failure)
                await db.commit()
                
                # === 执行 (Act) ===
                start_time = time.time()
                response = await client.get("/api/v1/download/failures", headers=auth_headers)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # === 断言 (Assert) ===
                assert response.status_code == 200
                assert response_time < 2.0  # API响应时间应小于2秒

    @pytest.mark.asyncio
    async def test_concurrent_api_access_safety(self, async_client, db_session, test_user_id, auth_headers):
        """测试并发访问API的安全性"""
        async for client in async_client:
            async for db in db_session:
                # === 准备 (Arrange) ===
                await db.execute(delete(DownloadedVideo))
                await db.execute(delete(DownloadFailure))
                await db.execute(delete(DownloadTask))
                await db.commit()
                
                # 创建测试数据
                task = create_test_download_task(db, test_user_id, status=TaskStatus.FAILED)
                db.add(task)
                await db.commit()
                await db.refresh(task)
                
                for i in range(5):
                    failure = create_test_download_failure(db, task.id)
                    db.add(failure)
                await db.commit()
                
                # === 执行 (Act) ===
                # 创建多个并发请求
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(
                        client.get("/api/v1/download/failures", headers=auth_headers)
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                
                # === 断言 (Assert) ===
                # 验证所有请求都成功
                for response in responses:
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["code"] == 200