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

class TestDownloadApiNew:
    """新增下载服务API接口测试类"""

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
                response = await client.get(f"/api/v1/download/failures/{non_existent_failure_id}",
                                            headers=auth_headers)

                # === 断言 (Assert) ===
                assert response.json()["code"] == 404
                error_data = response.json()
                assert "不存在" in error_data.get("message", "")