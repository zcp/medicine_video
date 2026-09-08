import uuid
import io
import time

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.deps import get_db, get_current_user
from tests.conftest import async_session_factory


# ==================== Test Fixtures ====================

@pytest.fixture
async def async_client_with_public_id(admin_user_id: uuid.UUID, admin_user_role: str) -> AsyncClient:
    """
    提供带有 public_id 和 ADMIN role 的异步客户端（用于 V6 幂等测试）
    注意：这个 fixture 覆盖了 get_current_user 依赖，添加了 public_id 和 role 字段
    使用Admin用户，因为批量导入需要Admin权限
    """
    import os
    from tests.conftest import async_session_factory
    
    # 设置测试环境变量
    os.environ["JWT_SECRET_KEY"] = "my-key"
    os.environ["JWT_ALGORITHM"] = "HS256"

    # 创建测试专用的FastAPI应用
    app = FastAPI(
        title="LiveCore Service Test",
        version="1.0.0",
        redirect_slashes=False
    )

    # 使用与main.py相同的路由结构
    app.include_router(api_router, prefix="/api/v1")

    # 覆盖数据库依赖，使用测试数据库
    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    # 覆盖JWT认证依赖，添加 public_id 和 role 字段（Admin用户）
    async def override_get_current_user():
        return {
            "public_id": str(admin_user_id),  # ← 修改：使用admin_user_id
            "user_id": str(admin_user_id),
            "sub": str(admin_user_id),
            "email": "admin@example.com",
            "role": admin_user_role,  # ← 新增：添加role字段（ADMIN）
            "exp": int(time.time()) + 3600
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 使用测试服务器
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


@pytest.mark.asyncio
async def test_batch_import_idempotent_same_csv_twice(async_client_with_public_id):
    """
    使用同一个 CSV 文件以 mode=apply 导入两次，第二次应命中幂等：
    - success_count 不变
    - items[*].skipped == True
    - skipped_count == 跳过行数
    """
    async for client in async_client_with_public_id:
        # 准备 CSV 内容：包含 external_room_id + 标题 + 播放url
        # 使用唯一的 external_room_id 和 playback_url，确保第一次导入不会命中幂等
        unique_suffix = uuid.uuid4().hex[:8]
        external_room_id = f"ext-room-{unique_suffix}"
        playback_url = f"http://example.com/playback/{unique_suffix}"
        
        csv_lines = [
            "external_room_id,标题,播放url",
            f"{external_room_id},测试直播间,{playback_url}",
        ]
        csv_content = ("\n".join(csv_lines)).encode("utf-8")

        # 第一次导入（apply）
        files1 = {
            "file": ("test_v6_batch_idempotent.csv", io.BytesIO(csv_content), "text/csv"),
        }
        resp1 = await client.post(
            "/api/v1/rooms/import/batch",
            params={"mode": "apply"},
            files=files1,
        )
        assert resp1.status_code == 200
        body1 = resp1.json()
        assert body1["code"] == 200

        data1 = body1["data"]
        assert data1["total_rows"] == 1
        assert data1["success_count"] == 1
        assert data1["failed_count"] == 0
        assert len(data1["items"]) == 1
        item1 = data1["items"][0]
        assert item1["status"] == "success"
        # 第一次导入可以认为未命中幂等（skipped=False 或缺省）
        assert item1.get("skipped") in (False, None)

        # 第二次导入同一文件（apply）
        files2 = {
            "file": ("test_v6_batch_idempotent.csv", io.BytesIO(csv_content), "text/csv"),
        }
        resp2 = await client.post(
            "/api/v1/rooms/import/batch",
            params={"mode": "apply"},
            files=files2,
        )
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert body2["code"] == 200

        data2 = body2["data"]
        assert data2["total_rows"] == 1
        assert data2["success_count"] == 1
        assert data2["failed_count"] == 0
        assert len(data2["items"]) == 1
        item2 = data2["items"][0]
        assert item2["status"] == "success"
        # 第二次应命中幂等
        assert item2.get("skipped") is True
        assert item2.get("skip_reason") == "duplicate_session_by_playback_url"

        # 顶层 skipped_count 可选存在，若存在则为 1
        skipped_count = data2.get("skipped_count")
        if skipped_count is not None:
            assert skipped_count == 1
        break


@pytest.mark.asyncio
async def test_import_session_idempotent_via_api(
    async_client_with_public_id, 
    db_session,
    admin_user_id: uuid.UUID
):
    """
    通过 Import Session API 连续导入两次相同的 playback_url：
    - 第二次返回的 id 与第一次相同
    - idempotent_hit 在第二次为 True
    """
    from uuid import UUID
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.crud import room as crud_room

    # 准备一个与 JWT 中 public_id 一致的用户 ID
    # ===== Arrange (准备) =====
    # 使用admin_user_id（从conftest.py获取，与async_client_with_public_id中的user_id一致）
    public_id = admin_user_id

    async for client in async_client_with_public_id:
        async for db in db_session:
            # 使用真实 CRUD 创建房间
            room = await crud_room.create(
                db,
                obj_in={
                    "id": uuid.uuid4(),
                    "title": "导入会话幂等测试房间",
                    "description": "",
                },
                user_id=public_id,
            )

            room_id = room.id
            payload = {
                "start_time": "2025-01-01T10:00:00Z",
                "end_time": "2025-01-01T11:00:00Z",
                "status": "finished",
                "playback_url": "http://example.com/playback/import-idempotent",
            }

            # 第一次导入
            resp1 = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=payload,
            )
            assert resp1.status_code == 200
            body1 = resp1.json()
            assert body1["code"] == 200
            data1 = body1["data"]
            session_id_1 = data1["id"]
            # 第一次通常不命中幂等
            assert data1.get("idempotent_hit") in (False, None)

            # 第二次导入相同 payload
            resp2 = await client.post(
                f"/api/v1/rooms/{room_id}/sessions/import",
                json=payload,
            )
            assert resp2.status_code == 200
            body2 = resp2.json()
            assert body2["code"] == 200
            data2 = body2["data"]
            session_id_2 = data2["id"]

            # 两次返回的 session_id 必须相同
            assert session_id_2 == session_id_1
            # 第二次命中幂等
            assert data2.get("idempotent_hit") is True
            break
        break


