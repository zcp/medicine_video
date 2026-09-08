"""
LiveCore Service - Topic Banner Upload Service Unit Tests (Incremental)

本文件包含专题横幅上传功能的Service层单元测试。
这是对现有test_service_topic.py的增量补充，测试新增的banner上传功能。

⚠️ 使用说明：
将本文件中的 TestTopicBannerManagement 类添加到 tests/unit/test_service_topic.py 文件末尾。
"""

import uuid
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import UploadFile, HTTPException

from app.services.topic_service import TopicService
from app.models.topic import Topic, TopicStatus
from app.exceptions import (
    TopicNotFoundException,
    TopicPermissionDeniedException
)


# ==================== 新增：专题横幅管理测试 ====================

class TestTopicBannerManagement:
    """专题横幅上传功能测试（新增）"""
    
    @pytest.mark.asyncio
    async def test_upload_topic_banner_success(self, mocker):
        """
        测试成功上传专题横幅
        
        验证点:
        1. 调用 crud_topic.get() 验证专题存在
        2. 验证用户权限通过（user_id匹配）
        3. 调用 FileHandler.save_banner_file() 保存文件
        4. 调用 crud_topic.update_banner_url() 更新数据库
        5. 返回更新后的Topic对象，banner_url不为空
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        
        # 创建Mock专题对象（初始没有横幅）
        mock_topic = Topic(
            id=topic_id,
            user_id=user_id,  # ✅ 相同的用户ID，权限检查通过
            title="Test Topic",
            description="Test Description",
            banner_url=None,  # 初始没有横幅
            status=TopicStatus.DRAFT
        )
        
        # 创建Mock文件
        mock_file = mocker.Mock(spec=UploadFile)
        mock_file.filename = "test_banner.png"
        
        # 更新后的专题对象
        updated_topic = Topic(
            id=topic_id,
            user_id=user_id,
            title="Test Topic",
            description="Test Description",
            banner_url="/media/topics/xxx/banner_123.png",  # ✅ 已更新
            status=TopicStatus.DRAFT
        )
        
        # Mock CRUD函数（使用原始模块路径）
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_update_banner_url = mocker.patch(
            "app.crud.topic.update_banner_url",
            new_callable=AsyncMock,
            return_value=updated_topic
        )
        
        # Mock FileHandler方法
        mock_save_banner = mocker.patch(
            "app.core.file_handler.FileHandler.save_banner_file",
            new_callable=AsyncMock,
            return_value="/media/topics/xxx/banner_123.png"
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        result = await service.upload_topic_banner(
            topic_id=topic_id,
            file=mock_file,
            user_id=user_id,
            role=role  # ← 新增：权限参数
        )
        
        # Assert
        mock_get.assert_called_once_with(mock_db, topic_id)
        mock_save_banner.assert_called_once_with(file=mock_file, topic_id=topic_id)
        mock_update_banner_url.assert_called_once_with(
            db=mock_db,
            topic_id=topic_id,
            banner_url="/media/topics/xxx/banner_123.png"
        )
        assert result == updated_topic
        assert result.banner_url == "/media/topics/xxx/banner_123.png"


    @pytest.mark.asyncio
    async def test_upload_topic_banner_topic_not_found(self, mocker):
        """
        测试专题不存在时上传横幅
        
        验证点:
        1. crud_topic.get() 返回 None
        2. 抛出 TopicNotFoundException
        3. FileHandler方法未被调用
        4. 数据库更新方法未被调用
        """
        # Arrange
        mock_db = mocker.Mock()
        topic_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_file = mocker.Mock(spec=UploadFile)
        
        # Mock CRUD函数返回None（专题不存在）
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=None
        )
        
        # Mock FileHandler和CRUD方法（不应被调用）
        mock_save_banner = mocker.patch(
            "app.core.file_handler.FileHandler.save_banner_file",
            new_callable=AsyncMock
        )
        mock_update_banner_url = mocker.patch(
            "app.crud.topic.update_banner_url",
            new_callable=AsyncMock
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(TopicNotFoundException):
            await service.upload_topic_banner(
                topic_id=topic_id,
                file=mock_file,
                user_id=user_id,
                role=role  # ← 新增：权限参数
            )
        
        # 验证get被调用
        mock_get.assert_called_once_with(mock_db, topic_id)
        
        # 验证FileHandler方法未被调用
        mock_save_banner.assert_not_called()
        mock_update_banner_url.assert_not_called()


    @pytest.mark.asyncio
    async def test_upload_topic_banner_permission_denied(self, mocker):
        """
        测试权限不足时上传横幅
        
        验证点:
        1. crud_topic.get() 返回专题（不同的user_id）
        2. 抛出 TopicPermissionDeniedException
        3. FileHandler方法未被调用
        4. 数据库更新方法未被调用
        """
        # Arrange
        mock_db = mocker.Mock()
        owner_user_id = uuid.uuid4()
        different_user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        mock_file = mocker.Mock(spec=UploadFile)
        
        # 创建Mock专题对象（所有者是owner_user_id）
        mock_topic = Topic(
            id=topic_id,
            user_id=owner_user_id,  # 所有者ID
            title="Test Topic",
            description="Test Description",
            banner_url=None,
            status=TopicStatus.DRAFT
        )
        
        # Mock CRUD函数
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # Mock FileHandler和CRUD方法（不应被调用）
        mock_save_banner = mocker.patch(
            "app.core.file_handler.FileHandler.save_banner_file",
            new_callable=AsyncMock
        )
        mock_update_banner_url = mocker.patch(
            "app.crud.topic.update_banner_url",
            new_callable=AsyncMock
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        from app.exceptions import PermissionDeniedException  # ← 修改：使用正确的异常类型
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(PermissionDeniedException):
            await service.upload_topic_banner(
                topic_id=topic_id,
                file=mock_file,
                user_id=different_user_id,  # 不同的用户ID
                role=role  # ← 新增：权限参数
            )
        
        # 验证get被调用
        mock_get.assert_called_once_with(mock_db, topic_id)
        
        # 验证FileHandler方法未被调用
        mock_save_banner.assert_not_called()
        mock_update_banner_url.assert_not_called()


    @pytest.mark.asyncio
    async def test_upload_topic_banner_deletes_old_file(self, mocker):
        """
        测试上传新横幅时删除旧文件
        
        验证点:
        1. 专题已有旧的banner_url
        2. FileHandler.delete_old_banner() 被调用
        3. 删除旧文件的方法被正确调用（传入旧的banner_url）
        4. 保存新文件的方法被调用
        5. 数据库更新成功
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        old_banner_url = "/media/topics/xxx/banner_old.png"
        new_banner_url = "/media/topics/xxx/banner_new.png"
        
        # 创建Mock专题对象（已有旧横幅）
        mock_topic = Topic(
            id=topic_id,
            user_id=user_id,
            title="Test Topic",
            description="Test Description",
            banner_url=old_banner_url,  # ✅ 已有旧横幅
            status=TopicStatus.DRAFT
        )
        
        # 创建Mock文件
        mock_file = mocker.Mock(spec=UploadFile)
        mock_file.filename = "test_banner_new.png"
        
        # 更新后的专题对象
        updated_topic = Topic(
            id=topic_id,
            user_id=user_id,
            title="Test Topic",
            description="Test Description",
            banner_url=new_banner_url,  # 新横幅
            status=TopicStatus.DRAFT
        )
        
        # Mock CRUD函数
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        mock_update_banner_url = mocker.patch(
            "app.crud.topic.update_banner_url",
            new_callable=AsyncMock,
            return_value=updated_topic
        )
        
        # Mock FileHandler方法
        mock_delete_old_banner = mocker.patch(
            "app.core.file_handler.FileHandler.delete_old_banner"
        )
        
        mock_save_banner = mocker.patch(
            "app.core.file_handler.FileHandler.save_banner_file",
            new_callable=AsyncMock,
            return_value=new_banner_url
        )
        
        # ===== Act (执行) =====
        # ← 修改：传递权限参数
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        result = await service.upload_topic_banner(
            topic_id=topic_id,
            file=mock_file,
            user_id=user_id,
            role=role  # ← 新增：权限参数
        )
        
        # Assert
        # 验证删除旧文件被调用
        mock_delete_old_banner.assert_called_once_with(old_banner_url)
        
        # 验证保存新文件被调用
        mock_save_banner.assert_called_once_with(file=mock_file, topic_id=topic_id)
        
        # 验证数据库更新
        mock_update_banner_url.assert_called_once_with(
            db=mock_db,
            topic_id=topic_id,
            banner_url=new_banner_url
        )
        
        assert result == updated_topic
        assert result.banner_url == new_banner_url


    @pytest.mark.asyncio
    async def test_upload_topic_banner_file_validation_fails(self, mocker):
        """
        测试文件验证失败
        
        验证点:
        1. FileHandler.save_banner_file() 抛出 HTTPException(400)
        2. 异常被正确传播（不被捕获）
        3. 数据库更新方法未被调用
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        mock_file = mocker.Mock(spec=UploadFile)
        
        # 创建Mock专题对象
        mock_topic = Topic(
            id=topic_id,
            user_id=user_id,
            title="Test Topic",
            description="Test Description",
            banner_url=None,
            status=TopicStatus.DRAFT
        )
        
        # Mock CRUD函数
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # Mock FileHandler.save_banner_file() 抛出异常
        mock_save_banner = mocker.patch(
            "app.core.file_handler.FileHandler.save_banner_file",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=400,
                detail="不支持的文件类型"
            )
        )
        
        # Mock 数据库更新方法（不应被调用）
        mock_update_banner_url = mocker.patch(
            "app.crud.topic.update_banner_url",
            new_callable=AsyncMock
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_topic_banner(
                topic_id=topic_id,
                file=mock_file,
                user_id=user_id,
                role=role  # ← 新增：权限参数
            )
        
        # 验证异常详情
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "不支持的文件类型"
        
        # 验证get被调用
        mock_get.assert_called_once_with(mock_db, topic_id)
        
        # 验证save_banner_file被调用
        mock_save_banner.assert_called_once_with(file=mock_file, topic_id=topic_id)
        
        # 验证数据库更新未被调用
        mock_update_banner_url.assert_not_called()


    @pytest.mark.asyncio
    async def test_upload_topic_banner_update_url_fails(self, mocker):
        """
        测试数据库更新失败
        
        验证点:
        1. crud_topic.update_banner_url() 返回 None
        2. 抛出 Exception("更新横幅URL失败")
        3. 文件已保存但数据库更新失败的场景
        """
        # Arrange
        mock_db = mocker.Mock()
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        new_banner_url = "/media/topics/xxx/banner_123.png"
        mock_file = mocker.Mock(spec=UploadFile)
        
        # 创建Mock专题对象
        mock_topic = Topic(
            id=topic_id,
            user_id=user_id,
            title="Test Topic",
            description="Test Description",
            banner_url=None,
            status=TopicStatus.DRAFT
        )
        
        # Mock CRUD函数
        mock_get = mocker.patch(
            "app.crud.topic.get",
            new_callable=AsyncMock,
            return_value=mock_topic
        )
        
        # Mock FileHandler.save_banner_file() 成功保存
        mock_save_banner = mocker.patch(
            "app.core.file_handler.FileHandler.save_banner_file",
            new_callable=AsyncMock,
            return_value=new_banner_url
        )
        
        # Mock update_banner_url 返回 None（更新失败）
        mock_update_banner_url = mocker.patch(
            "app.crud.topic.update_banner_url",
            new_callable=AsyncMock,
            return_value=None  # ❌ 更新失败
        )
        
        # Act & Assert
        service = TopicService(mock_db)
        role = "REGULAR"  # ← 新增：权限参数
        with pytest.raises(Exception) as exc_info:
            await service.upload_topic_banner(
                topic_id=topic_id,
                file=mock_file,
                user_id=user_id,
                role=role  # ← 新增：权限参数
            )
        
        # 验证异常消息
        assert "更新横幅URL失败" in str(exc_info.value)
        
        # 验证get被调用
        mock_get.assert_called_once_with(mock_db, topic_id)
        
        # 验证save_banner_file被调用
        mock_save_banner.assert_called_once_with(file=mock_file, topic_id=topic_id)
        
        # 验证update_banner_url被调用
        mock_update_banner_url.assert_called_once_with(
            db=mock_db,
            topic_id=topic_id,
            banner_url=new_banner_url
        )
