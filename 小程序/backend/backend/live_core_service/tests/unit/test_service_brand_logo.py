"""
品牌Service层测试 - Logo上传功能

测试覆盖：
- upload_brand_logo() 成功场景
- upload_brand_logo() 权限验证
- upload_brand_logo() 资源验证
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from app.services.brand_service import BrandService
from app.models.brand import Brand
from app.exceptions import PermissionDeniedException, NotFoundException


# ==================== 辅助函数 ====================

def create_mock_upload_file(
    filename: str = "test.jpg",
    content: bytes = b"fake image content",
    content_type: str = "image/jpeg"
) -> MagicMock:
    """创建模拟的UploadFile对象"""
    from fastapi import UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.read = AsyncMock(return_value=content)
    return mock_file


class TestBrandServiceLogoUpload:
    """品牌Service层Logo上传测试"""
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_success(self, db_session):
        """测试管理员成功上传Logo"""
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
            
            # 2. 创建测试图片文件（使用Mock对象）
            image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
            mock_file = create_mock_upload_file(
                filename="test_logo.jpg",
                content=image_content,
                content_type="image/jpeg"
            )
            
            # 3. Mock文件系统操作（让FileHandler真正执行，但mock文件系统）
            with patch("builtins.open", mock_open()), \
                 patch("os.makedirs"), \
                 patch("app.core.file_handler.FileHandler.validate_image_file"):
                
                # 4. 调用Service层方法（严格按照设计文档的函数签名）
                service = BrandService()
                logo_url = await service.upload_brand_logo(
                    db=db,
                    brand_id=brand.id,  # 字段名必须与设计文档一致
                    file=mock_file,
                    current_user_id=uuid.uuid4(),  # 参数名必须与设计文档一致
                    role="ADMIN"  # 参数名必须与设计文档一致
                )
                
                # 5. 验证返回的URL路径
                assert logo_url.startswith("/media/brands/")
                assert str(brand.id) in logo_url
                
                # 6. 验证数据库字段已更新（字段名必须与设计文档一致）
                await db.refresh(brand)
                assert brand.logo_url == logo_url
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_permission_denied(self, db_session):
        """测试非管理员上传失败"""
        async for db in db_session:
            # 1. 创建测试品牌
            brand = Brand(
                id=uuid.uuid4(),
                name=f"测试品牌_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
            )
            db.add(brand)
            await db.commit()
            await db.refresh(brand)
            
            # 2. 创建测试图片文件
            mock_file = create_mock_upload_file(
                filename="test_logo.jpg",
                content=b'\xff\xd8\xff\xe0' + b'0' * 100,
                content_type="image/jpeg"
            )
            
            # 3. 使用非管理员角色调用（严格按照设计文档）
            service = BrandService()
            with pytest.raises(PermissionDeniedException):
                await service.upload_brand_logo(
                    db=db,
                    brand_id=brand.id,
                    file=mock_file,
                    current_user_id=uuid.uuid4(),
                    role="REGULAR"  # 非管理员角色
                )
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_brand_not_found(self, db_session):
        """测试品牌不存在"""
        async for db in db_session:
            # 使用不存在的品牌ID
            non_existent_brand_id = uuid.uuid4()
            
            mock_file = create_mock_upload_file(
                filename="test_logo.jpg",
                content=b'\xff\xd8\xff\xe0' + b'0' * 100,
                content_type="image/jpeg"
            )
            
            service = BrandService()
            with pytest.raises(NotFoundException):
                await service.upload_brand_logo(
                    db=db,
                    brand_id=non_existent_brand_id,
                    file=mock_file,
                    current_user_id=uuid.uuid4(),
                    role="ADMIN"
                )
