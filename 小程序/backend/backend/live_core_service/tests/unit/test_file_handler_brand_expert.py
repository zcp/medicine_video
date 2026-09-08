"""
FileHandler层测试 - 品牌Logo和专家头像上传

测试覆盖：
- generate_brand_logo_path() 路径生成
- save_brand_logo() 文件保存
- generate_expert_avatar_path() 路径生成
- save_expert_avatar() 文件保存
"""

import pytest
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from io import BytesIO
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from app.core.file_handler import FileHandler, ROOM_MEDIA_ROOT_PATH, UPLOAD_MAX_SIZE


# ==================== 辅助函数 ====================

def create_mock_upload_file(
    filename: str = "test.jpg",
    content: bytes = b"fake image content",
    content_type: str = "image/jpeg"
) -> MagicMock:
    """创建模拟的UploadFile对象"""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.read = AsyncMock(return_value=content)  # 注意：使用AsyncMock
    return mock_file


class TestBrandLogoFileHandler:
    """品牌Logo文件处理测试"""
    
    def test_generate_brand_logo_path(self):
        """测试品牌Logo路径生成"""
        brand_id = uuid.uuid4()
        extension = "jpg"
        
        fs_path, url_path = FileHandler.generate_brand_logo_path(brand_id, extension)
        
        # 验证文件系统路径格式
        assert str(brand_id) in fs_path
        assert "brands" in fs_path
        assert "logo_" in fs_path
        assert fs_path.endswith(f".{extension}")
        assert fs_path.startswith(ROOM_MEDIA_ROOT_PATH)
        
        # 验证URL路径格式
        assert url_path.startswith("/media/brands/")
        assert str(brand_id) in url_path
        assert "logo_" in url_path
        assert url_path.endswith(f".{extension}")
        
        # 验证目录已创建
        assert os.path.exists(os.path.dirname(fs_path))
    
    @pytest.mark.asyncio
    async def test_save_brand_logo_success(self):
        """测试成功保存品牌Logo"""
        brand_id = uuid.uuid4()
        
        # 创建测试图片文件（1KB的JPG）
        image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
        mock_file = create_mock_upload_file(
            filename="test_logo.jpg",
            content=image_content,
            content_type="image/jpeg"
        )
        
        # Mock文件系统操作
        with patch("builtins.open", mock_open()) as mock_file_open, \
             patch("os.makedirs"):
            
            # 执行保存操作
            url_path = await FileHandler.save_brand_logo(mock_file, brand_id)
            
            # 验证返回的URL路径格式
            assert url_path.startswith("/media/brands/")
            assert str(brand_id) in url_path
            assert "logo_" in url_path
            assert url_path.endswith(".jpg")
            
            # 验证文件被写入
            mock_file_open.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_brand_logo_invalid_format(self):
        """测试保存非图片格式文件"""
        brand_id = uuid.uuid4()
        
        # 创建非图片文件
        mock_file = create_mock_upload_file(
            filename="test.txt",
            content=b"This is not an image",
            content_type="text/plain"
        )
        
        with pytest.raises(HTTPException):  # HTTPException会被抛出
            await FileHandler.save_brand_logo(mock_file, brand_id)
    
    @pytest.mark.asyncio
    async def test_save_brand_logo_file_too_large(self):
        """测试保存超过大小限制的文件"""
        brand_id = uuid.uuid4()
        
        # 创建超过限制的文件（UPLOAD_MAX_SIZE + 1）
        large_content = b'\xff\xd8\xff\xe0' + b'0' * (UPLOAD_MAX_SIZE + 1)
        mock_file = create_mock_upload_file(
            filename="large_logo.jpg",
            content=large_content,
            content_type="image/jpeg"
        )
        
        # Mock os.makedirs避免实际创建目录
        with patch("os.makedirs"):
            with pytest.raises(HTTPException) as exc_info:
                await FileHandler.save_brand_logo(mock_file, brand_id)
            
            # 断言异常信息
            assert exc_info.value.status_code == 400
            assert "文件大小超出限制" in exc_info.value.detail


class TestExpertAvatarFileHandler:
    """专家头像文件处理测试"""
    
    def test_generate_expert_avatar_path(self):
        """测试专家头像路径生成"""
        expert_id = uuid.uuid4()
        extension = "png"
        
        fs_path, url_path = FileHandler.generate_expert_avatar_path(expert_id, extension)
        
        # 验证文件系统路径格式
        assert str(expert_id) in fs_path
        assert "experts" in fs_path
        assert "avatar_" in fs_path
        assert fs_path.endswith(f".{extension}")
        assert fs_path.startswith(ROOM_MEDIA_ROOT_PATH)
        
        # 验证URL路径格式
        assert url_path.startswith("/media/experts/")
        assert str(expert_id) in url_path
        assert "avatar_" in url_path
        assert url_path.endswith(f".{extension}")
        
        # 验证目录已创建
        assert os.path.exists(os.path.dirname(fs_path))
    
    @pytest.mark.asyncio
    async def test_save_expert_avatar_success(self):
        """测试成功保存专家头像"""
        expert_id = uuid.uuid4()
        
        # 创建测试图片文件（1KB的PNG）
        image_content = b'\x89PNG\r\n\x1a\n' + b'0' * 1000
        mock_file = create_mock_upload_file(
            filename="test_avatar.png",
            content=image_content,
            content_type="image/png"
        )
        
        # Mock文件系统操作
        with patch("builtins.open", mock_open()) as mock_file_open, \
             patch("os.makedirs"):
            
            # 执行保存操作
            url_path = await FileHandler.save_expert_avatar(mock_file, expert_id)
            
            # 验证返回的URL路径格式
            assert url_path.startswith("/media/experts/")
            assert str(expert_id) in url_path
            assert "avatar_" in url_path
            assert url_path.endswith(".png")
            
            # 验证文件被写入
            mock_file_open.assert_called_once()
