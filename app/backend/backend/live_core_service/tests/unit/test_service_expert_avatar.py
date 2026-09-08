"""
专家Service层测试 - 头像上传功能

测试覆盖：
- upload_expert_avatar() 成功场景
- upload_expert_avatar() 权限验证
- upload_expert_avatar() 资源验证
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from app.services.expert_service import ExpertService
from app.models.experts import Expert
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


class TestExpertServiceAvatarUpload:
    """专家Service层头像上传测试"""
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_success(self, db_session):
        """测试管理员成功上传头像"""
        async for db in db_session:
            # 0. 创建测试分类（experts.category_id NOT NULL）
            from app.models.content_management import Category
            cat = Category(id=uuid.uuid4(), name=f"分类_{uuid.uuid4().hex[:8]}", sort_order=0, is_active=True)
            db.add(cat)
            await db.flush()

            # 1. 创建测试专家
            expert = Expert(
                id=uuid.uuid4(),
                name=f"测试专家_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                title="测试职称",
                category_id=cat.id
            )
            db.add(expert)
            await db.commit()
            await db.refresh(expert)
            
            # 2. 创建测试图片文件（使用Mock对象）
            image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
            mock_file = create_mock_upload_file(
                filename="test_avatar.jpg",
                content=image_content,
                content_type="image/jpeg"
            )
            
            # 3. Mock文件系统操作（让FileHandler真正执行，但mock文件系统）
            with patch("builtins.open", mock_open()), \
                 patch("os.makedirs"), \
                 patch("app.core.file_handler.FileHandler.validate_image_file"):
                
                # 4. 调用Service层方法（严格按照设计文档的函数签名）
                service = ExpertService(db)  # 注意：专家Service需要传入db参数
                avatar_url = await service.upload_expert_avatar(
                    expert_id=expert.id,  # 参数名必须与设计文档一致
                    file=mock_file,
                    current_user_id=uuid.uuid4(),  # 参数名必须与设计文档一致
                    role="ADMIN"  # 参数名必须与设计文档一致
                )
                
                # 5. 验证返回的URL路径
                assert avatar_url.startswith("/media/experts/")
                assert str(expert.id) in avatar_url
                
                # 6. 验证数据库字段已更新（字段名必须与设计文档一致）
                await db.refresh(expert)
                assert expert.avatar_url == avatar_url
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_permission_denied(self, db_session):
        """测试非管理员上传失败"""
        async for db in db_session:
            from app.models.content_management import Category
            cat = Category(id=uuid.uuid4(), name=f"分类_{uuid.uuid4().hex[:8]}", sort_order=0, is_active=True)
            db.add(cat)
            await db.flush()

            expert = Expert(
                id=uuid.uuid4(),
                name=f"测试专家_{uuid.uuid4().hex[:8]}",  # ✅ 使用UUID生成唯一名称
                category_id=cat.id
            )
            db.add(expert)
            await db.commit()
            await db.refresh(expert)
            
            mock_file = create_mock_upload_file(
                filename="test_avatar.jpg",
                content=b'\xff\xd8\xff\xe0' + b'0' * 100,
                content_type="image/jpeg"
            )
            
            service = ExpertService(db)
            with pytest.raises(PermissionDeniedException):
                await service.upload_expert_avatar(
                    expert_id=expert.id,
                    file=mock_file,
                    current_user_id=uuid.uuid4(),
                    role="REGULAR"  # 非管理员角色
                )
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_expert_not_found(self, db_session):
        """测试专家不存在"""
        async for db in db_session:
            non_existent_expert_id = uuid.uuid4()
            
            mock_file = create_mock_upload_file(
                filename="test_avatar.jpg",
                content=b'\xff\xd8\xff\xe0' + b'0' * 100,
                content_type="image/jpeg"
            )
            
            service = ExpertService(db)
            with pytest.raises(NotFoundException):
                await service.upload_expert_avatar(
                    expert_id=non_existent_expert_id,
                    file=mock_file,
                    current_user_id=uuid.uuid4(),
                    role="ADMIN"
                )
