"""
专家API层测试 - 头像上传端点

测试覆盖：
- POST /api/v1/admin/experts/{expert_id}/avatar 成功场景
- 权限验证（403 Forbidden, code: 3003）
- 资源验证（404 Not Found, code: 2001）
- 文件验证（400 Bad Request, code: 4001）
- 响应结构验证（严格按照设计文档）
"""

import pytest
import uuid
from io import BytesIO
from app.models.experts import Expert


class TestExpertAvatarUploadAPI:
    """专家头像上传API测试"""
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_success(self, async_client, db_session, admin_user_token):
        """测试管理员成功上传头像"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建测试专家
                expert = Expert(
                    id=uuid.uuid4(),
                    name=f"测试专家_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                    title="测试职称"
                )
                db.add(expert)
                await db.commit()
                await db.refresh(expert)
                
                # 2. 创建测试图片文件
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_avatar.jpg", BytesIO(image_content), "image/jpeg")
                }
                
                # 3. 调用API端点（严格按照设计文档的路径）
                response = await client.post(
                    f"/api/v1/admin/experts/{expert.id}/avatar",  # 路径必须与设计文档一致
                    files=files,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                
                # 4. 验证HTTP状态码和响应结构（必须与设计文档完全一致）
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "data" in data
                assert "expert_id" in data["data"]  # 字段名必须与设计文档一致
                assert "avatar_url" in data["data"]  # 字段名必须与设计文档一致
                assert data["data"]["expert_id"] == str(expert.id)
                assert data["data"]["avatar_url"].startswith("/media/experts/")
                break
            break
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_permission_denied(self, async_client, db_session, regular_user_token):
        """测试非管理员上传返回403 Forbidden (code: 3003)"""
        async for client in async_client:
            async for db in db_session:
                expert = Expert(
                    id=uuid.uuid4(),
                    name=f"测试专家_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                )
                db.add(expert)
                await db.commit()
                await db.refresh(expert)
                
                files = {
                    "file": ("test_avatar.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
                }
                
                response = await client.post(
                    f"/api/v1/admin/experts/{expert.id}/avatar",
                    files=files,
                    headers={"Authorization": f"Bearer {regular_user_token}"}
                )
                
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3003  # 必须与设计文档一致
                assert "权限不足" in data["message"]
                break
            break
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_expert_not_found(self, async_client, db_session, admin_user_token):
        """测试专家不存在返回404 Not Found (code: 2001)"""
        async for client in async_client:
            non_existent_expert_id = uuid.uuid4()
            
            files = {
                "file": ("test_avatar.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
            }
            
            response = await client.post(
                f"/api/v1/admin/experts/{non_existent_expert_id}/avatar",
                files=files,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001  # 必须与设计文档一致
            assert "专家不存在" in data["message"]
            break
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_invalid_uuid(self, async_client, db_session, admin_user_token):
        """测试无效UUID格式返回400 Bad Request (code: 4001)"""
        async for client in async_client:
            files = {
                "file": ("test_avatar.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
            }
            
            # 使用无效的UUID格式
            response = await client.post(
                "/api/v1/admin/experts/invalid-uuid/avatar",
                files=files,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["code"] == 4001
            break
