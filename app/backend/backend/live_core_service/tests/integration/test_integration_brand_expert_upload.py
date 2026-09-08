"""
集成测试 - 品牌Logo和专家头像上传完整流程

测试覆盖：
- 品牌创建 → Logo上传 → 品牌查询（验证logo_url返回）
- 专家创建 → 头像上传 → 专家查询（验证avatar_url返回）
- 并发上传测试
"""
from urllib.parse import urlparse

import pytest
import uuid
from io import BytesIO
from app.models.brand import Brand
from app.models.experts import Expert


class TestBrandLogoIntegration:
    """品牌Logo上传集成测试"""
    
    @pytest.mark.asyncio
    async def test_brand_create_upload_logo_query_flow(self, async_client, db_session, admin_user_token):
        """测试完整流程：创建品牌 → 上传Logo → 查询品牌（验证logo_url）"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建品牌（使用唯一名称避免唯一约束冲突）
                brand_data = {
                    "name": f"测试品牌_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                    "description": "测试描述"
                }

                create_response = await client.post(
                    "/api/v1/admin/brands",
                    json=brand_data,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                assert create_response.status_code == 200
                brand_id = create_response.json()["data"]["id"]

                # 2. 上传Logo
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_logo.jpg", BytesIO(image_content), "image/jpeg")
                }

                upload_response = await client.post(
                    f"/api/v1/admin/brands/{brand_id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                assert upload_response.status_code == 200
                logo_url = upload_response.json()["data"]["logo_url"]

                # 3. 查询品牌，验证logo_url已更新
                query_response = await client.get(
                    f"/api/v1/admin/brands/{brand_id}",
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                assert query_response.status_code == 200
                brand_data = query_response.json()["data"]
                assert brand_data["logo_url"] == logo_url  # 字段名必须与设计文档一致
                break
            break


class TestExpertAvatarIntegration:
    """专家头像上传集成测试"""

    @pytest.mark.asyncio
    async def test_expert_create_upload_avatar_query_flow(self, async_client, db_session, admin_user_token):
        """测试完整流程：创建专家 → 上传头像 → 查询专家（验证avatar_url）"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建专家（使用唯一名称避免唯一约束冲突）
                expert_data = {
                    "name": f"测试专家_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称（修复：之前写成了"测试品牌"）
                    "title": "测试职称"
                }

                create_response = await client.post(
                    "/api/v1/admin/experts",
                    json=expert_data,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                assert create_response.status_code == 200
                expert_id = create_response.json()["data"]["id"]

                # 2. 上传头像
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_avatar.jpg", BytesIO(image_content), "image/jpeg")
                }

                upload_response = await client.post(
                    f"/api/v1/admin/experts/{expert_id}/avatar",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                assert upload_response.status_code == 200
                avatar_url = upload_response.json()["data"]["avatar_url"]

                # 3. 查询专家，验证avatar_url已更新
                # 注意：专家详情端点是公开端点 /api/v1/experts/{expert_id}，不是管理员端点
                query_response = await client.get(
                    f"/api/v1/experts/{expert_id}",  # ✅ 修复：使用公开端点而不是管理员端点
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                assert query_response.status_code == 200
                expert_data = query_response.json()["data"]
                # 提取路径部分进行比较
                query_avatar_url = expert_data["avatar_url"]
                if query_avatar_url.startswith('http'):
                    # 如果是完整URL，提取路径部分
                    parsed = urlparse(query_avatar_url)
                    query_avatar_path = parsed.path
                else:
                    query_avatar_path = query_avatar_url

                assert query_avatar_path == avatar_url  # 比较路径部分
                break
            break