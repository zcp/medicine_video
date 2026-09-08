"""
LiveCore Service - FileHandler Unit Tests

This module contains unit tests for the FileHandler utility class,
testing file validation, storage, and management operations.
"""

import pytest
import uuid
import os
from io import BytesIO
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
from fastapi import UploadFile, HTTPException

from app.core.file_handler import FileHandler


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


# ==================== validate_image_file 测试 ====================

def test_validate_image_file_success_jpg():
    """
    测试JPG文件验证通过的情况
    - 准备：创建有效的JPG图片文件
    - 执行：调用FileHandler.validate_image_file()
    - 验证：返回True，不抛出异常
    """
    # 准备 - 创建有效的JPG文件
    mock_file = create_mock_upload_file(
        filename="test_cover.jpg",
        content_type="image/jpeg"
    )
    
    # 执行验证
    result = FileHandler.validate_image_file(mock_file)
    
    # 断言验证通过
    assert result is True


def test_validate_image_file_success_png():
    """
    测试PNG文件验证通过的情况
    - 准备：创建有效的PNG图片文件
    - 执行：调用FileHandler.validate_image_file()
    - 验证：返回True，不抛出异常
    """
    # 准备 - 创建有效的PNG文件
    mock_file = create_mock_upload_file(
        filename="test_cover.png",
        content_type="image/png"
    )
    
    # 执行验证
    result = FileHandler.validate_image_file(mock_file)
    
    # 断言验证通过
    assert result is True


def test_validate_image_file_invalid_extension():
    """
    测试文件扩展名不允许的情况
    - 准备：创建.exe等非图片文件
    - 执行：调用FileHandler.validate_image_file()
    - 验证：抛出HTTPException，状态码400
    """
    # 准备 - 创建不允许的文件类型
    mock_file = create_mock_upload_file(
        filename="malicious.exe",
        content_type="application/x-msdownload"
    )
    
    # 执行并验证抛出异常
    with pytest.raises(HTTPException) as exc_info:
        FileHandler.validate_image_file(mock_file)
    
    # 断言异常信息
    assert exc_info.value.status_code == 400
    assert "不支持的文件类型" in exc_info.value.detail


def test_validate_image_file_invalid_mime_type():
    """
    测试MIME类型不允许的情况
    - 准备：创建MIME类型为application/pdf的文件
    - 执行：调用FileHandler.validate_image_file()
    - 验证：抛出HTTPException，错误消息包含MIME类型
    """
    # 准备 - 创建MIME类型不允许的文件
    mock_file = create_mock_upload_file(
        filename="document.jpg",  # 扩展名是jpg但MIME类型不对
        content_type="application/pdf"
    )
    
    # 执行并验证抛出异常
    with pytest.raises(HTTPException) as exc_info:
        FileHandler.validate_image_file(mock_file)
    
    # 断言异常信息
    assert exc_info.value.status_code == 400
    assert "MIME类型" in exc_info.value.detail or "不支持" in exc_info.value.detail


# ==================== generate_cover_path 测试 ====================

def test_generate_cover_path_format():
    """
    测试封面路径生成的格式正确性
    - 准备：提供room_id和扩展名
    - 执行：调用FileHandler.generate_cover_path()
    - 验证：返回的路径符合规范格式
    """
    # 准备 - 生成测试数据
    room_id = uuid.uuid4()
    extension = "jpg"
    
    # Mock os.makedirs避免实际创建目录
    with patch("os.makedirs"):
        # 执行路径生成
        fs_path, url_path = FileHandler.generate_cover_path(room_id, extension)
    
    # 断言文件系统路径格式
    assert f"rooms/{room_id}" in fs_path or f"rooms\\{room_id}" in fs_path  # Windows使用反斜杠
    assert "cover_" in fs_path
    assert fs_path.endswith(".jpg")
    
    # 断言URL路径格式
    assert url_path.startswith("/media/")
    assert f"rooms/{room_id}" in url_path
    assert "cover_" in url_path
    assert url_path.endswith(".jpg")


def test_generate_cover_path_creates_directory():
    """
    测试路径生成时自动创建目录
    - 准备：提供room_id和扩展名
    - 执行：调用FileHandler.generate_cover_path()
    - 验证：os.makedirs被调用，参数包含exist_ok=True
    """
    # 准备 - 生成测试数据
    room_id = uuid.uuid4()
    extension = "png"
    
    # Mock os.makedirs
    with patch("os.makedirs") as mock_makedirs:
        # 执行路径生成
        fs_path, url_path = FileHandler.generate_cover_path(room_id, extension)
        
        # 断言makedirs被调用
        mock_makedirs.assert_called_once()
        # 验证参数包含exist_ok=True
        call_args = mock_makedirs.call_args
        assert call_args[1].get("exist_ok") is True


# ==================== save_cover_file 测试 ====================

@pytest.mark.asyncio
async def test_save_cover_file_success():
    """
    测试成功保存封面文件
    - 准备：创建有效的图片文件
    - 执行：调用FileHandler.save_cover_file()
    - 验证：返回正确的URL路径
    """
    # 准备 - 创建有效的图片文件
    room_id = uuid.uuid4()
    image_content = b"fake image content" * 100
    mock_file = create_mock_upload_file(
        filename="test_cover.jpg",
        content=image_content,
        content_type="image/jpeg"
    )
    
    # Mock文件系统操作
    with patch("builtins.open", mock_open()) as mock_file_open, \
         patch("os.makedirs"):
        
        # 执行保存操作
        url_path = await FileHandler.save_cover_file(mock_file, room_id)
        
        # 断言返回URL路径格式正确
        assert url_path is not None
        assert url_path.startswith("/media/")
        assert f"rooms/{room_id}" in url_path
        assert "cover_" in url_path
        assert url_path.endswith(".jpg")
        
        # 验证文件被写入
        mock_file_open.assert_called_once()


@pytest.mark.asyncio
async def test_save_cover_file_size_exceeded():
    """
    测试文件大小超出限制的情况
    - 准备：创建大于5MB的文件
    - 执行：调用FileHandler.save_cover_file()
    - 验证：抛出HTTPException，状态码400
    """
    # 准备 - 创建超大文件（> 5MB）
    room_id = uuid.uuid4()
    large_content = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1byte
    mock_file = create_mock_upload_file(
        filename="large.jpg",
        content=large_content,
        content_type="image/jpeg"
    )
    
    # 设置UPLOAD_MAX_SIZE为5MB，确保测试文件超出限制
    # 注意：.env.example中可能是10MB，但测试需要验证5MB限制
    # 直接patch file_handler模块中的UPLOAD_MAX_SIZE变量
    with patch("app.core.file_handler.UPLOAD_MAX_SIZE", 5 * 1024 * 1024):
        # Mock os.makedirs避免实际创建目录
        with patch("os.makedirs"):
            # 执行并验证抛出异常
            with pytest.raises(HTTPException) as exc_info:
                await FileHandler.save_cover_file(mock_file, room_id)
            
            # 断言异常信息
            assert exc_info.value.status_code == 400, f"Expected 400 but got {exc_info.value.status_code}: {exc_info.value.detail}"
            assert "文件大小超出限制" in exc_info.value.detail


# ==================== delete_old_cover 测试 ====================

def test_delete_old_cover_success():
    """
    测试成功删除旧封面文件
    - 准备：提供有效的cover_url
    - 执行：调用FileHandler.delete_old_cover()
    - 验证：os.remove被调用，无异常抛出
    """
    # 准备 - 提供有效的cover_url
    cover_url = "/media/rooms/test-room-id/cover_1234567890.jpg"
    
    # Mock文件系统操作
    with patch("os.path.exists", return_value=True) as mock_exists, \
         patch("os.remove") as mock_remove:
        
        # 执行删除操作
        FileHandler.delete_old_cover(cover_url)
        
        # 断言os.remove被调用
        mock_remove.assert_called_once()


def test_delete_old_cover_file_not_exists():
    """
    测试删除不存在的文件
    - 准备：提供cover_url
    - 执行：调用FileHandler.delete_old_cover()
    - 验证：os.remove不被调用，无异常抛出
    """
    # 准备 - 提供cover_url
    cover_url = "/media/rooms/test-room-id/cover_9999999999.jpg"
    
    # Mock文件系统操作 - 文件不存在
    with patch("os.path.exists", return_value=False) as mock_exists, \
         patch("os.remove") as mock_remove:
        
        # 执行删除操作
        FileHandler.delete_old_cover(cover_url)
        
        # 断言os.remove不被调用
        mock_remove.assert_not_called()


def test_delete_old_cover_failure_no_exception():
    """
    测试删除文件失败时不抛出异常
    - 准备：提供cover_url
    - 执行：调用FileHandler.delete_old_cover()，os.remove抛出OSError
    - 验证：只记录警告日志，不抛出异常
    """
    # 准备 - 提供cover_url
    cover_url = "/media/rooms/test-room-id/cover_1234567890.jpg"
    
    # Mock文件系统操作 - 删除失败
    with patch("os.path.exists", return_value=True), \
         patch("os.remove", side_effect=OSError("Permission denied")):
        
        # 执行删除操作 - 应该不抛出异常
        try:
            FileHandler.delete_old_cover(cover_url)
            # 如果没有抛出异常，测试通过
        except Exception as e:
            pytest.fail(f"delete_old_cover should not raise exception, but got: {e}")


# ==================== delete_featured_content_media 测试 ====================

def test_delete_featured_content_media_success():
    """
    测试成功删除焦点图媒体目录
    - 准备：提供属于该焦点图的 /media/ 路径
    - 执行：调用FileHandler.delete_featured_content_media()
    - 验证：shutil.rmtree 被调用
    """
    content_id = uuid.uuid4()
    image_url = f"/media/featured_content/{content_id}/image_1234567890.jpg"

    with patch("os.path.isdir", return_value=True), \
         patch("shutil.rmtree") as mock_rmtree, \
         patch("os.path.exists", return_value=False):
        FileHandler.delete_featured_content_media(content_id, image_url)
        mock_rmtree.assert_called_once()


def test_delete_featured_content_media_wrong_content_id_no_delete():
    """
    测试 image_url 不属于该焦点图目录时不删除（路径白名单防护）
    """
    content_id = uuid.uuid4()
    other_id = uuid.uuid4()
    image_url = f"/media/featured_content/{other_id}/image_1234567890.jpg"

    with patch("os.path.isdir") as mock_isdir, \
         patch("shutil.rmtree") as mock_rmtree:
        FileHandler.delete_featured_content_media(content_id, image_url)
        mock_rmtree.assert_not_called()
        mock_isdir.assert_not_called()


def test_delete_featured_content_media_external_url_no_delete():
    """
    测试外部URL（非 /media/ 路径）不触发删除
    """
    content_id = uuid.uuid4()
    image_url = "https://example.com/image.jpg"

    with patch("os.path.isdir") as mock_isdir, \
         patch("shutil.rmtree") as mock_rmtree:
        FileHandler.delete_featured_content_media(content_id, image_url)
        mock_rmtree.assert_not_called()
        mock_isdir.assert_not_called()


def test_delete_featured_content_media_dir_not_exists():
    """
    测试目录不存在时静默跳过，不抛异常
    """
    content_id = uuid.uuid4()
    image_url = f"/media/featured_content/{content_id}/image_1234567890.jpg"

    with patch("os.path.isdir", return_value=False), \
         patch("shutil.rmtree") as mock_rmtree:
        FileHandler.delete_featured_content_media(content_id, image_url)
        mock_rmtree.assert_not_called()


