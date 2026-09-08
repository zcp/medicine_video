"""
品牌API层测试 - Logo上传端点

测试覆盖：
- POST /api/v1/admin/brands/{brand_id}/logo 成功场景
- 权限验证（403 Forbidden, code: 3003）
- 资源验证（404 Not Found, code: 2001）
- 文件验证（400 Bad Request, code: 4001）
- 响应结构验证（严格按照设计文档）
"""

import pytest
import uuid
from io import BytesIO
from app.models.brand import Brand


class TestBrandLogoUploadAPI:
    """品牌Logo上传API测试"""
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_success(self, async_client, db_session, admin_user_token):
        """测试管理员成功上传Logo"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建测试品牌
                brand = Brand(
                    id=uuid.uuid4(),
                    name=f"测试品牌_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                    description="测试描述"
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                # 2. 创建测试图片文件
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_logo.jpg", BytesIO(image_content), "image/jpeg")
                }
                
                # 3. 调用API端点（严格按照设计文档的路径和参数）
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",  # 路径必须与设计文档一致
                    files=files,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                
                # 4. 验证HTTP状态码（必须与设计文档一致）
                assert response.status_code == 200
                
                # 5. 验证响应结构（必须与设计文档完全一致）
                data = response.json()
                assert "code" in data
                assert data["code"] == 200  # 业务状态码必须与设计文档一致
                assert "message" in data
                assert "data" in data
                assert "timestamp" in data
                
                # 6. 验证响应数据字段（字段名必须与设计文档一致）
                assert "brand_id" in data["data"]
                assert "logo_url" in data["data"]
                assert data["data"]["brand_id"] == str(brand.id)
                assert data["data"]["logo_url"].startswith("/media/brands/")
                break
            break
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_permission_denied(self, async_client, db_session, regular_user_token):
        """测试非管理员上传返回403 Forbidden (code: 3003)"""
        async for client in async_client:
            async for db in db_session:
                brand = Brand(
                    id=uuid.uuid4(),
                    name=f"测试品牌_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                files = {
                    "file": ("test_logo.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
                }
                
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {regular_user_token}"}
                )
                
                # 验证HTTP状态码和业务状态码（必须与设计文档一致）
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3003  # 权限不足错误码必须与设计文档一致
                assert "权限不足" in data["message"]
                break
            break
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_brand_not_found(self, async_client, db_session, admin_user_token):
        """测试品牌不存在返回404 Not Found (code: 2001)"""
        async for client in async_client:
            non_existent_brand_id = uuid.uuid4()
            
            files = {
                "file": ("test_logo.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
            }
            
            response = await client.post(
                f"/api/v1/admin/brands/{non_existent_brand_id}/logo",
                files=files,
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )
            
            # 验证HTTP状态码和业务状态码（必须与设计文档一致）
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001  # 资源不存在错误码必须与设计文档一致
            assert "品牌不存在" in data["message"]
            break
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_invalid_file_format(self, async_client, db_session, admin_user_token):
        """测试无效文件格式返回400 Bad Request (code: 4001)"""
        async for client in async_client:
            async for db in db_session:
                brand = Brand(
                    id=uuid.uuid4(),
                    name=f"测试品牌_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                # 上传非图片文件
                files = {
                    "file": ("test.txt", BytesIO(b"This is not an image"), "text/plain")
                }
                
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                
                # 验证HTTP状态码和业务状态码（必须与设计文档一致）
                assert response.status_code == 400
                data = response.json()
                assert data["code"] == 4001  # 参数校验失败错误码必须与设计文档一致
                break
            break
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_file_too_large(self, async_client, db_session, admin_user_token):
        """测试文件过大返回400 Bad Request (code: 4001)"""
        async for client in async_client:
            async for db in db_session:
                brand = Brand(
                    id=uuid.uuid4(),
                    name=f"测试品牌_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                # 创建超过5MB的文件
                from app.core.file_handler import UPLOAD_MAX_SIZE
                large_content = b'\xff\xd8\xff\xe0' + b'0' * (UPLOAD_MAX_SIZE + 1)
                
                files = {
                    "file": ("large_logo.jpg", BytesIO(large_content), "image/jpeg")
                }
                
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_user_token}"}
                )
                
                assert response.status_code == 400
                data = response.json()
                assert data["code"] == 4001
                break
            break
