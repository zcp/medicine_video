"""
LiveCore Service - Experts API Integration Tests

This module contains integration tests for all API endpoints in the experts module.
"""

import uuid
import pytest
import json
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
from httpx import AsyncClient
from fastapi import FastAPI

# 项目内导入
from app.crud import experts as crud_experts
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert, SessionExpertRole
from app.schemas.experts import ExpertCreate, ExpertUpdate

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_expert_db(db: AsyncSession, **kwargs) -> Expert:
    """在数据库中创建测试专家"""
    default_data = {
        "name": fake.name(),
        "title": fake.job(),
        "hospital": fake.company(),
        "department": fake.word(),
        "expertise_areas": fake.text(max_nb_chars=100),
        "bio": fake.text(max_nb_chars=200),
        "avatar_url": fake.image_url(),
        "is_featured": True,
        "sort_order": fake.random_int(min=0, max=100)
    }
    expert_data = ExpertCreate(**{**default_data, **kwargs})
    expert = await crud_experts.create_expert(db, expert_data)
    await db.commit()
    await db.refresh(expert)
    return expert


# ==================== 专家信息管理API测试 ====================

class TestExpertAPIPublic:
    """专家公开API测试"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_featured_experts_success(self, async_client):
        """测试获取推荐专家列表成功"""
        async for client in async_client:
            # 发送请求
            response = await client.get("/api/v1/featured-experts?limit=10")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            assert isinstance(data["data"], list)
            break

    @pytest.mark.asyncio
    async def test_get_public_experts_list_success_default_active_only(self, async_client, db_session):
        """测试公共专家列表默认仅返回启用专家"""
        async for db in db_session:
            await create_test_expert_db(db, name="公共专家-启用", is_active=True)
            await create_test_expert_db(db, name="公共专家-停用", is_active=False)

            async for client in async_client:
                response = await client.get("/api/v1/experts?page=1&size=50")

                assert response.status_code == 200
                payload = response.json()
                assert payload["code"] == 200
                assert "data" in payload
                assert "items" in payload["data"]
                assert payload["data"]["page"] == 1
                assert payload["data"]["size"] == 50
                assert all(item["is_active"] is True for item in payload["data"]["items"])
                break
            break

    @pytest.mark.asyncio
    async def test_get_public_experts_list_filter_by_keyword_and_department(self, async_client, db_session):
        """测试公共专家列表支持关键词与科室组合筛选"""
        async for db in db_session:
            await create_test_expert_db(
                db,
                name="心脏王医生",
                department="心内科",
                hospital="第一人民医院",
                is_active=True,
            )
            await create_test_expert_db(
                db,
                name="骨科李医生",
                department="骨科",
                hospital="第二人民医院",
                is_active=True,
            )

            async for client in async_client:
                response = await client.get(
                    "/api/v1/experts?page=1&size=50&keyword=心脏&department=心内"
                )

                assert response.status_code == 200
                payload = response.json()
                assert payload["code"] == 200
                items = payload["data"]["items"]
                assert len(items) >= 1
                assert all("心" in (item["department"] or "") or "心" in item["name"] for item in items)
                break
            break

    @pytest.mark.asyncio
    async def test_get_public_experts_list_size_exceeds_limit(self, async_client):
        """测试公共专家列表 size 超上限返回参数错误"""
        async for client in async_client:
            response = await client.get("/api/v1/experts?page=1&size=101")

            assert response.status_code == 400
            payload = response.json()
            assert payload["code"] == 4001
            break

    @pytest.mark.asyncio
    async def test_get_expert_detail_success_anonymous(self, async_client, db_session):
        """测试获取专家详情成功（匿名用户）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db, name="测试专家", is_featured=True)
            async for client in async_client:
                # 发送请求（无Token）
                response = await client.get(f"/api/v1/experts/{expert.id}")

                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["name"] == "测试专家"
                assert data["data"]["id"] == str(expert.id)
                break
            break

    @pytest.mark.asyncio
    async def test_get_expert_detail_success_authenticated(
        self, async_client, db_session, regular_user_token
    ):
        """测试获取专家详情成功（已认证）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db, name="测试专家2", is_featured=True)
            async for client in async_client:
                # 发送请求（带Token）
                response = await client.get(
                    f"/api/v1/experts/{expert.id}",
                    headers={"Authorization": f"Bearer {regular_user_token}"}
                )

                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["data"]["name"] == "测试专家2"
                break
            break

    @pytest.mark.asyncio
    async def test_get_expert_detail_not_found(self, async_client):
        """测试获取专家详情不存在"""
        non_existent_id = uuid.uuid4()

        async for client in async_client:
            # 发送请求
            response = await client.get(f"/api/v1/experts/{non_existent_id}")

            # 验证响应
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001
            break

    @pytest.mark.asyncio
    async def test_get_expert_detail_invalid_uuid(self, async_client):
        """测试获取专家详情（无效UUID）"""
        async for client in async_client:
            # 发送请求（无效UUID格式）
            response = await client.get("/api/v1/experts/invalid-uuid")

            # 验证响应：当前实现会走业务层参数校验，返回 400
            assert response.status_code == 400
            break

    @pytest.mark.asyncio
    async def test_get_expert_sessions_success(self, async_client, db_session):
        """测试获取专家场次列表成功"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            async for client in async_client:
                # 发送请求
                response = await client.get(
                    f"/api/v1/experts/{expert.id}/sessions?page=1&size=10"
                )

                # 验证响应
                assert response.status_code == 200
                payload = response.json()
                assert payload["code"] == 200
                # 响应结构为 {"code":200,"data":{"expert_info":{...},"sessions":{...}},...}
                data = payload["data"]
                assert "expert_info" in data
                assert "sessions" in data
                assert "items" in data["sessions"]
                assert "page" in data["sessions"]
                assert "size" in data["sessions"]
                break
            break


# ==================== 专家管理API测试（Admin） ====================

class TestExpertAPIAdmin:
    """专家管理API测试（Admin）"""

    @pytest.mark.asyncio
    async def test_create_expert_success(self, async_client, admin_user_token):
        """测试创建专家成功"""
        # 准备请求数据
        expert_data = {
            "name": "新专家",
            "title": "主任医师",
            "hospital": "测试医院",
            "department": "测试科室",
            "is_featured": True,
            "sort_order": 1
        }

        async for client in async_client:
            # 发送请求
            response = await client.post(
                "/api/v1/admin/experts",
                json=expert_data,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["name"] == "新专家"
            break

    @pytest.mark.asyncio
    async def test_create_expert_unauthorized(self, async_client):
        """测试创建专家未认证"""
        expert_data = {
            "name": "新专家",
            "title": "主任医师",
            "hospital": "测试医院"
        }

        async for client in async_client:
            # 发送请求（无Token）
            response = await client.post(
                "/api/v1/admin/experts",
                json=expert_data
            )

            # 验证响应
            assert response.status_code == 401
            break

    @pytest.mark.asyncio
    async def test_create_expert_forbidden(self, async_client, regular_user_token):
        """测试创建专家无权限"""
        expert_data = {
            "name": "新专家",
            "title": "主任医师",
            "hospital": "测试医院"
        }

        async for client in async_client:
            # 发送请求（普通用户Token）
            response = await client.post(
                "/api/v1/admin/experts",
                json=expert_data,
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应
            assert response.status_code == 403
            break

    @pytest.mark.asyncio
    async def test_get_experts_list_success(self, async_client, admin_user_token):
        """测试获取专家列表成功"""
        async for client in async_client:
            # 发送请求
            response = await client.get(
                "/api/v1/admin/experts?page=1&size=10",
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            assert "total" in data["data"]
            break

    @pytest.mark.asyncio
    async def test_get_experts_list_with_filters(self, async_client, admin_user_token, db_session):
        """测试获取专家列表（带筛选）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db, name="张医生", hospital="北京医院")
            async for client in async_client:
                # 发送请求（按名称筛选）
                response = await client.get(
                    "/api/v1/admin/experts?page=1&size=10&name=张",
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )

                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                break
            break

    @pytest.mark.asyncio
    async def test_get_experts_list_unauthorized(self, async_client):
        """测试获取专家列表未认证"""
        async for client in async_client:
            # 发送请求（无Token）
            response = await client.get("/api/v1/admin/experts?page=1&size=10")

            # 验证响应
            assert response.status_code == 401
            break

    @pytest.mark.asyncio
    async def test_update_expert_success(self, async_client, admin_user_token, db_session):
        """测试更新专家成功"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db, name="原名")
            
            # 准备更新数据
            update_data = {
                "name": "新名称",
                "title": "新职称"
            }
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.patch(
                f"/api/v1/admin/experts/{expert.id}",
                json=update_data,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["name"] == "新名称"
            break

    @pytest.mark.asyncio
    async def test_update_expert_not_found(self, async_client, admin_user_token):
        """测试更新专家不存在"""
        non_existent_id = uuid.uuid4()
        update_data = {"name": "新名称"}

        client = await async_client.__anext__()
        # 发送请求
        response = await client.patch(
            f"/api/v1/admin/experts/{non_existent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )

        # 验证响应
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_expert_forbidden(self, async_client, regular_user_token, db_session):
        """测试更新专家无权限"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            # 准备更新数据
            update_data = {"name": "新名称"}
            
            client = await async_client.__anext__()
            # 发送请求（普通用户Token）
            response = await client.patch(
                f"/api/v1/admin/experts/{expert.id}",
                json=update_data,
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应
            assert response.status_code == 403
            break

    @pytest.mark.asyncio
    async def test_delete_expert_success(self, async_client, admin_user_token, db_session):
        """测试删除专家成功"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.delete(
                f"/api/v1/admin/experts/{expert.id}",
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            break

    @pytest.mark.asyncio
    async def test_delete_expert_not_found(self, async_client, admin_user_token):
        """测试删除专家不存在"""
        non_existent_id = uuid.uuid4()

        client = await async_client.__anext__()
        # 发送请求
        response = await client.delete(
            f"/api/v1/admin/experts/{non_existent_id}",
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )

        # 验证响应
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_expert_forbidden(self, async_client, regular_user_token, db_session):
        """测试删除专家无权限"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            client = await async_client.__anext__()
            # 发送请求（普通用户Token）
            response = await client.delete(
                f"/api/v1/admin/experts/{expert.id}",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应
            assert response.status_code == 403
            break


# ==================== 专家关注API测试 ====================

class TestExpertAPIFollow:
    """专家关注API测试"""

    @pytest.mark.asyncio
    async def test_follow_expert_success(self, async_client, regular_user_token, db_session):
        """测试关注专家成功"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db, is_featured=True)
            
            # 准备请求数据
            follow_data = {"expert_id": str(expert.id)}
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.post(
                "/api/v1/users/me/followed-experts",
                json=follow_data,
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：REGULAR 用户应有权限关注专家
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            assert data["data"]["expert_id"] == str(expert.id)
            break

    @pytest.mark.asyncio
    async def test_set_session_experts_expert_not_found(self, async_client, admin_user_token):
        """测试设置场次专家列表失败（专家不存在）"""
        session_id = uuid.uuid4()
        non_existent_id = uuid.uuid4()

        # 准备请求数据（数组形式）
        request_data = [
            {"expert_id": str(non_existent_id), "role": "主讲", "sort_order": 1}
        ]

        client = await async_client.__anext__()
        # 发送请求
        response = await client.post(
            f"/api/v1/experts/sessions/{session_id}/experts",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )

        # 验证响应：当前实现使用业务参数校验，返回 400 + 业务错误码 2001
        assert response.status_code == 400
        payload = response.json()
        assert payload["code"] == 2001
        assert "专家不存在" in payload["message"]
    @pytest.mark.asyncio
    async def test_follow_expert_already_followed(
        self, async_client, regular_user_token, regular_user_id, db_session
    ):
        """测试关注专家失败（已关注）"""
        async for db in db_session:
            # 创建测试专家和关注记录
            expert = await create_test_expert_db(db, is_featured=True)
            await crud_experts.create_subscription(db, regular_user_id, expert.id)
            await db.commit()
            
            # 准备请求数据
            follow_data = {"expert_id": str(expert.id)}
            
            client = await async_client.__anext__()
            # 发送请求（重复关注）
            response = await client.post(
                "/api/v1/users/me/followed-experts",
                json=follow_data,
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：已关注时返回 409
            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 2002
            assert "您已关注" in data["message"]
            break

    @pytest.mark.asyncio
    async def test_follow_expert_unauthorized(self, async_client, db_session):
        """测试关注专家未认证"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            # 准备请求数据
            follow_data = {"expert_id": str(expert.id)}
            
            client = await async_client.__anext__()
            # 发送请求（无Token）
            response = await client.post(
                "/api/v1/users/me/followed-experts",
                json=follow_data
            )

            # 验证响应
            assert response.status_code == 401
            break

    @pytest.mark.asyncio
    async def test_unfollow_expert_success(
        self, async_client, regular_user_token, regular_user_id, db_session
    ):
        """测试取消关注成功"""
        async for db in db_session:
            # 创建测试专家和关注记录
            expert = await create_test_expert_db(db)
            await crud_experts.create_subscription(db, regular_user_id, expert.id)
            await db.commit()
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.delete(
                f"/api/v1/users/me/followed-experts/{expert.id}",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：REGULAR 用户应有权限取消关注
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            break

    @pytest.mark.asyncio
    async def test_unfollow_expert_not_followed(
        self, async_client, regular_user_token, db_session
    ):
        """测试取消关注失败（未关注）"""
        async for db in db_session:
            # 创建测试专家（未关注）
            expert = await create_test_expert_db(db)
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.delete(
                f"/api/v1/users/me/followed-experts/{expert.id}",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：未关注时返回 404
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001
            assert data.get("data") and "未关注" in data["data"].get("reason", "")
            break

    @pytest.mark.asyncio
    async def test_unfollow_expert_unauthorized(self, async_client, db_session):
        """测试取消关注未认证"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            client = await async_client.__anext__()
            # 发送请求（无Token）
            response = await client.delete(
                f"/api/v1/users/me/followed-experts/{expert.id}"
            )

            # 验证响应
            assert response.status_code == 401
            break

    @pytest.mark.asyncio
    async def test_get_followed_experts_success(
        self, async_client, regular_user_token, regular_user_id, db_session
    ):
        """测试获取关注列表成功"""
        async for db in db_session:
            # 创建测试专家和关注记录
            expert1 = await create_test_expert_db(db, name="专家1")
            expert2 = await create_test_expert_db(db, name="专家2")
            await crud_experts.create_subscription(db, regular_user_id, expert1.id)
            await crud_experts.create_subscription(db, regular_user_id, expert2.id)
            await db.commit()
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.get(
                "/api/v1/users/me/followed-experts",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：REGULAR 用户应有权限获取关注列表
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            assert isinstance(data["data"], list)
            assert len(data["data"]) >= 2
            assert all("expert_id" in item and "name" in item for item in data["data"])
            break

    @pytest.mark.asyncio
    async def test_get_followed_experts_with_live_status(
        self, async_client, regular_user_token, regular_user_id, db_session
    ):
        """测试获取关注列表（含直播状态）"""
        async for db in db_session:
            # 创建测试专家和关注记录
            expert = await create_test_expert_db(db)
            await crud_experts.create_subscription(db, regular_user_id, expert.id)
            await db.commit()
            
            client = await async_client.__anext__()
            # 发送请求（include_live_status=true）
            response = await client.get(
                "/api/v1/users/me/followed-experts?include_live_status=true",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：REGULAR 用户应有权限获取关注列表（含直播状态）
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            break

    @pytest.mark.asyncio
    async def test_get_followed_experts_unauthorized(self, async_client):
        """测试获取关注列表未认证"""
        client = await async_client.__anext__()
        # 发送请求（无Token）
        response = await client.get("/api/v1/users/me/followed-experts")

        # 验证响应
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_check_is_followed_true(
        self, async_client, regular_user_token, regular_user_id, db_session
    ):
        """测试检查已关注"""
        async for db in db_session:
            # 创建测试专家和关注记录
            expert = await create_test_expert_db(db)
            await crud_experts.create_subscription(db, regular_user_id, expert.id)
            await db.commit()
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.get(
                f"/api/v1/experts/{expert.id}/is-followed",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：已关注时返回 is_followed=true
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["is_followed"] is True
            break

    @pytest.mark.asyncio
    async def test_check_is_followed_false(
        self, async_client, regular_user_token, db_session
    ):
        """测试检查未关注"""
        async for db in db_session:
            # 创建测试专家（未关注）
            expert = await create_test_expert_db(db)
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.get(
                f"/api/v1/experts/{expert.id}/is-followed",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            # 验证响应：未关注时返回 is_followed=false
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["is_followed"] is False
            break

    @pytest.mark.asyncio
    async def test_check_is_followed_unauthorized(self, async_client, db_session):
        """测试检查关注状态未认证"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            client = await async_client.__anext__()
            # 发送请求（无Token）
            response = await client.get(
                f"/api/v1/experts/{expert.id}/is-followed"
            )

            # 验证响应
            assert response.status_code == 401
            break


# ==================== 场次专家关联API测试 ====================

class TestExpertAPISessionExperts:
    """场次专家关联API测试"""

    @pytest.mark.asyncio
    async def test_set_session_experts_success(self, async_client, admin_user_token, db_session):
        """测试设置场次专家列表成功"""
        async for db in db_session:
            # 先创建合法的 LiveRoom 和 LiveSession，避免外键约束错误
            from datetime import datetime
            from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus

            session_id = uuid.uuid4()

            # 创建房间
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"测试房间_{uuid.uuid4().hex[:8]}",
                stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
                is_private=False,
                record_by_default=True,
            )
            db.add(room)
            await db.flush()

            # 创建场次
            session = LiveSession(
                id=session_id,
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            db.add(session)
            await db.flush()

            # 创建测试专家
            expert1 = await create_test_expert_db(db)
            expert2 = await create_test_expert_db(db)

            # 准备请求数据（注意沿用上面创建的 session_id）
            request_data = [
                {"expert_id": str(expert1.id), "role": "主讲", "sort_order": 1},
                {"expert_id": str(expert2.id), "role": "嘉宾", "sort_order": 2}
            ]

            client = await async_client.__anext__()
            # 发送请求（请求体为专家列表数组）
            response = await client.post(
                f"/api/v1/experts/sessions/{session_id}/experts",
                json=request_data,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

            # 验证响应
            assert response.status_code == 200
            payload = response.json()
            assert payload["code"] == 200

            # data 是包含 session_id 和 experts 的对象
            data = payload["data"]
            assert "session_id" in data
            assert data["session_id"] == str(session_id)
            assert "experts" in data
            assert isinstance(data["experts"], list)
            assert len(data["experts"]) == 2
            break


    @pytest.mark.asyncio
    async def test_set_session_experts_expert_not_found(self, async_client, admin_user_token):
        """测试设置场次专家列表失败（专家不存在）"""
        session_id = uuid.uuid4()
        non_existent_id = uuid.uuid4()
        
        # 准备请求数据（数组形式）
        request_data = [
            {"expert_id": str(non_existent_id), "role": "主讲", "sort_order": 1}
        ]

        client = await async_client.__anext__()
        # 发送请求
        response = await client.post(
            f"/api/v1/experts/sessions/{session_id}/experts",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )

        # 验证响应：当前实现会在 Service 中抛 NotFound，期望 404
        assert response.status_code == 400
        payload = response.json()
        assert payload["code"] == 2001
        assert "专家不存在" in payload["message"]

    @pytest.mark.asyncio
    async def test_set_session_experts_invalid_role(self, async_client, admin_user_token, db_session):
        """测试设置场次专家列表失败（无效角色）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            # 准备请求数据（无效角色）
            session_id = uuid.uuid4()
            request_data = [
                {"expert_id": str(expert.id), "role": "无效角色", "sort_order": 1}
            ]
            
            client = await async_client.__anext__()
            # 发送请求
            response = await client.post(
                f"/api/v1/experts/sessions/{session_id}/experts",
                json=request_data,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

            # 验证响应：无效角色应命中业务参数校验，返回 400
            assert response.status_code == 400
            break

    @pytest.mark.asyncio
    async def test_set_session_experts_unauthorized(self, async_client, db_session):
        """测试设置场次专家列表未认证"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert_db(db)
            
            # 准备请求数据
            session_id = uuid.uuid4()
            request_data = [
                {"expert_id": str(expert.id), "role": "主讲", "sort_order": 1}
            ]
            
            client = await async_client.__anext__()
            # 发送请求（无Token）
            response = await client.post(
                f"/api/v1/experts/sessions/{session_id}/experts",
                json=request_data
            )

            # 验证响应：未认证用户应返回 401
            assert response.status_code == 401
            break

    @pytest.mark.asyncio
    async def test_set_session_experts_forbidden(self, async_client, regular_user_token, db_session):
        """测试设置场次专家列表无权限（非房主 REGULAR）"""
        async for db in db_session:
            from datetime import datetime
            from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus

            expert = await create_test_expert_db(db)
            session_id = uuid.uuid4()

            # 房间属于其他用户
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"测试房间_{uuid.uuid4().hex[:8]}",
                stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
                is_private=False,
                record_by_default=True,
            )
            db.add(room)
            await db.flush()

            session = LiveSession(
                id=session_id,
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            db.add(session)
            await db.flush()

            request_data = [
                {"expert_id": str(expert.id), "role": "主讲", "sort_order": 1}
            ]

            client = await async_client.__anext__()
            response = await client.post(
                f"/api/v1/experts/sessions/{session_id}/experts",
                json=request_data,
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )

            assert response.status_code == 403
            break

    @pytest.mark.asyncio
    async def test_set_session_experts_owner_success(
        self, async_client, regular_user_token, regular_user_id, db_session
    ):
        """REGULAR 房主可为场次设置多名专家（联动）"""
        async for db in db_session:
            from datetime import datetime
            from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus

            session_id = uuid.uuid4()
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=regular_user_id,
                title=f"测试房间_{uuid.uuid4().hex[:8]}",
                stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
                is_private=False,
                record_by_default=True,
            )
            db.add(room)
            await db.flush()

            session = LiveSession(
                id=session_id,
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            db.add(session)
            await db.flush()

            expert1 = await create_test_expert_db(db)
            expert2 = await create_test_expert_db(db)
            request_data = [
                {"expert_id": str(expert1.id), "role": "主讲", "sort_order": 1},
                {"expert_id": str(expert2.id), "role": "嘉宾", "sort_order": 2},
            ]

            client = await async_client.__anext__()
            response = await client.post(
                f"/api/v1/experts/sessions/{session_id}/experts",
                json=request_data,
                headers={"Authorization": f"Bearer {regular_user_token}"},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["code"] == 200
            assert len(payload["data"]["experts"]) == 2
            break

    @pytest.mark.asyncio
    async def test_get_session_experts_success(self, async_client, db_session):
        """测试获取场次专家列表成功"""
        session_id = uuid.uuid4()

        client = await async_client.__anext__()
        # 发送请求
        response = await client.get(
            f"/api/v1/experts/sessions/{session_id}/experts"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_get_session_experts_with_role_filter(self, async_client, db_session):
        """测试获取场次专家列表（带角色筛选）"""
        async for db in db_session:
            # 创建测试专家和场次专家关联（需要先创建合法的 LiveRoom 和 LiveSession，避免外键约束错误）
            from datetime import datetime
            from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus

            session_id = uuid.uuid4()

            # 创建房间
            room = LiveRoom(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                title=f"测试房间_{uuid.uuid4().hex[:8]}",
                stream_key=f"stream_key_{uuid.uuid4().hex[:16]}",
                is_private=False,
                record_by_default=True,
            )
            db.add(room)
            await db.flush()

            # 创建场次
            session = LiveSession(
                id=session_id,
                room_id=room.id,
                status=LiveSessionStatus.FINISHED,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            db.add(session)
            await db.flush()

            expert1 = await create_test_expert_db(db)
            expert2 = await create_test_expert_db(db)

            # 手动创建场次专家关联
            from app.models.experts import LiveSessionExpert, SessionExpertRole
            session_expert1 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session_id,
                expert_id=expert1.id,
                role=SessionExpertRole.MAIN_SPEAKER,
                sort_order=1
            )
            session_expert2 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session_id,
                expert_id=expert2.id,
                role=SessionExpertRole.GUEST,
                sort_order=2
            )
            db.add(session_expert1)
            db.add(session_expert2)
            await db.commit()

            client = await async_client.__anext__()
            # 发送请求（筛选主讲）
            response = await client.get(
                f"/api/v1/experts/sessions/{session_id}/experts?role=主讲"
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            break


# ==================== 增量测试：is_active、check_is_followed 404、batch-import ====================

@pytest.mark.asyncio
async def test_get_expert_detail_returns_is_active(async_client, db_session):
    """增量：专家详情响应含 is_active"""
    async for db in db_session:
        expert = await create_test_expert_db(db, name="IsActiveExpert", is_featured=True)
        async for client in async_client:
            response = await client.get(f"/api/v1/experts/{expert.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "is_active" in data["data"]
            assert data["data"]["is_active"] is True
            break
        break


@pytest.mark.asyncio
async def test_get_featured_experts_returns_is_active(async_client):
    """增量：推荐专家列表响应中每项含 is_active"""
    async for client in async_client:
        response = await client.get("/api/v1/featured-experts?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
        for item in data["data"]:
            assert "is_active" in item
        break


@pytest.mark.asyncio
async def test_get_experts_list_admin_filter_by_is_active(async_client, admin_user_token, db_session):
    """增量：Admin GET /admin/experts 支持 is_active 查询参数"""
    async for db in db_session:
        await create_test_expert_db(db, name="ActiveExpert", is_featured=False)
        async for client in async_client:
            response = await client.get(
                "/api/v1/admin/experts?page=1&size=10&is_active=true",
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "data" in data
            break
        break


@pytest.mark.asyncio
async def test_check_is_followed_inactive_expert_returns_404(async_client, regular_user_token, db_session):
    """增量：非 Admin 访问已下架专家的 check_is_followed 返回 404"""
    async for db in db_session:
        expert = await create_test_expert_db(db, name="InactiveExpert", is_featured=True)
        expert.is_active = False
        await db.commit()
        await db.refresh(expert)
        async for client in async_client:
            response = await client.get(
                f"/api/v1/experts/{expert.id}/is-followed",
                headers={"Authorization": f"Bearer {regular_user_token}"}
            )
            assert response.status_code == 404
            break
        break


@pytest.mark.asyncio
async def test_batch_import_experts_201_success(async_client, admin_user_token):
    """增量：合法 CSV 全成功返回 201"""
    async for client in async_client:
        files = {"file": ("experts.csv", b"name,title,hospital\nBatch Expert,Dr,Beijing", "text/csv")}
        data = {"skip_duplicates": "false"}
        response = await client.post(
            "/api/v1/admin/experts/batch-import",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["code"] == 200
        assert "data" in payload
        assert "total" in payload["data"]
        assert "success" in payload["data"]
        assert "created_expert_ids" in payload["data"]
        break


@pytest.mark.asyncio
async def test_batch_import_experts_401_unauthorized(async_client):
    """增量：未认证调用 batch-import 返回 401"""
    async for client in async_client:
        files = {"file": ("experts.csv", b"name,title,hospital\nTest,Dr,Hospital", "text/csv")}
        response = await client.post(
            "/api/v1/admin/experts/batch-import",
            files=files,
            data={"skip_duplicates": "false"},
        )
        assert response.status_code == 401
        break


@pytest.mark.asyncio
async def test_batch_import_experts_403_forbidden(async_client, regular_user_token):
    """增量：非 Admin 调用 batch-import 返回 403"""
    async for client in async_client:
        files = {"file": ("experts.csv", b"name,title,hospital\nTest,Dr,Hospital", "text/csv")}
        response = await client.post(
            "/api/v1/admin/experts/batch-import",
            files=files,
            data={"skip_duplicates": "false"},
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 3003
        break


@pytest.mark.asyncio
async def test_batch_import_experts_400_not_csv(async_client, admin_user_token):
    """增量：非 CSV 文件返回 400"""
    async for client in async_client:
        files = {"file": ("data.txt", b"name,title\nTest,Dr", "text/plain")}
        response = await client.post(
            "/api/v1/admin/experts/batch-import",
            files=files,
            data={"skip_duplicates": "false"},
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )
        assert response.status_code == 400
        break


@pytest.mark.asyncio
async def test_batch_import_experts_413_file_too_large(async_client, admin_user_token):
    """增量：文件过大返回 413（超过 10MB）"""
    async for client in async_client:
        over_10mb = b"name,title,hospital\n" + (b"x," * 50 + b"\n") * (10 * 1024 * 1024 // 100)
        if len(over_10mb) <= 10 * 1024 * 1024:
            over_10mb = over_10mb + b"x" * (10 * 1024 * 1024 - len(over_10mb) + 1)
        files = {"file": ("large.csv", over_10mb, "text/csv")}
        response = await client.post(
            "/api/v1/admin/experts/batch-import",
            files=files,
            data={"skip_duplicates": "false"},
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )
        assert response.status_code == 413
        break


@pytest.mark.asyncio
async def test_batch_import_experts_with_real_csv_data(async_client, admin_user_token, db_session):
    """测试使用真实 CSV 数据批量导入专家"""
    import os

    # 真实 CSV 文件路径（请根据实际路径调整）
    csv_path = r"D:\项目\陶伟\video_website\experts_cleaned.csv"

    # 检查文件是否存在
    if not os.path.exists(csv_path):
        pytest.skip(f"测试数据文件不存在: {csv_path}")

    async for client in async_client:
        # 读取 CSV 文件内容
        with open(csv_path, "rb") as f:
            csv_content = f.read()

        # 只取前 30 条数据进行测试（避免导入过多）
        lines = csv_content.decode("utf-8").strip().split("\n")
        header = lines[0]
        data_lines = lines[1:31]  # 取前 30 条数据
        test_csv_content = (header + "\n" + "\n".join(data_lines)).encode("utf-8")

        # 发送批量导入请求
        files = {"file": ("experts_test.csv", test_csv_content, "text/csv")}
        data = {"skip_duplicates": "true"}  # 跳过重复记录

        response = await client.post(
            "/api/v1/admin/experts/batch-import",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_user_token}"}
        )

        # 验证响应
        assert response.status_code in (201, 207), f"Expected 201 or 207, got {response.status_code}: {response.text}"
        payload = response.json()
        assert payload["code"] == 200
        assert "data" in payload

        result = payload["data"]
        assert "total" in result
        assert "success" in result
        assert "failed" in result

        # 打印导入结果便于调试
        print(f"\n批量导入结果:")
        print(f"  总数: {result['total']}")
        print(f"  成功: {result['success']}")
        print(f"  失败: {result['failed']}")
        print(f"  跳过: {result.get('skipped', 0)}")

        if result.get("failed_rows"):
            print(f"  失败详情: {result['failed_rows'][:5]}")  # 只显示前 5 条

        # 验证至少有部分成功导入
        assert result["success"] > 0 or result.get("skipped", 0) > 0, \
            f"导入全部失败: {result.get('failed_rows', [])[:3]}"

        # 验证创建的专家 ID 列表
        if result["success"] > 0:
            assert "created_expert_ids" in result
            assert len(result["created_expert_ids"]) > 0

        break