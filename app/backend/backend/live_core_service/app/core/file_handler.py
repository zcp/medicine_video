"""
LiveCore Service - File Handler

This module contains the FileHandler utility class for handling file upload,
validation, storage, and management operations.
"""

import os
import uuid
import time
import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

# 设置日志
logger = logging.getLogger(__name__)

# 从环境变量读取配置
ROOM_MEDIA_ROOT_PATH = os.getenv("ROOM_MEDIA_ROOT_PATH", "./media")
UPLOAD_MAX_SIZE = int(os.getenv("UPLOAD_MAX_SIZE", "5242880"))
UPLOAD_ALLOWED_EXTENSIONS = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif").split(",")

# 允许的MIME类型
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/gif"]


class FileHandler:
    """文件处理工具类"""
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> bool:
        """
        验证文件类型和大小
        
        Args:
            file: 上传的文件对象
            
        Returns:
            验证通过返回True
            
        Raises:
            HTTPException: 验证失败时抛出异常
        """
        logger.debug(f"开始验证文件: filename={file.filename}, content_type={file.content_type}")
        
        # 检查文件扩展名
        if file.filename:
            file_ext = file.filename.rsplit(".", 1)[-1].lower()
            if file_ext not in UPLOAD_ALLOWED_EXTENSIONS:
                logger.warning(f"文件类型不允许: extension={file_ext}")
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型。仅允许：{', '.join(UPLOAD_ALLOWED_EXTENSIONS)}"
                )
        
        # 检查MIME类型
        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"MIME类型不允许: content_type={file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"不支持的MIME类型。仅允许：{', '.join(ALLOWED_MIME_TYPES)}"
            )
        
        # 检查文件大小
        # 注意：由于file.size可能不可用，我们在读取时检查大小
        logger.debug(f"文件验证通过: filename={file.filename}")
        return True
    
    @staticmethod
    def generate_cover_path(room_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成封面存储路径
        
        Args:
            room_id: 房间ID
            extension: 文件扩展名
            
        Returns:
            (文件系统路径, URL路径)的元组
        """
        # 生成时间戳
        timestamp = int(time.time())
        
        # 构建路径
        relative_dir = f"rooms/{room_id}"
        filename = f"cover_{timestamp}.{extension}"
        
        # 文件系统路径
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        
        # URL路径
        url_path = f"/media/{relative_dir}/{filename}"
        
        # 确保目录存在
        os.makedirs(fs_dir, exist_ok=True)
        logger.debug(f"生成封面路径: fs_path={fs_path}, url_path={url_path}")
        
        return fs_path, url_path
    
    @staticmethod
    async def save_cover_file(file: UploadFile, room_id: uuid.UUID) -> str:
        """
        保存封面文件并返回URL
        
        Args:
            file: 上传的文件对象
            room_id: 房间ID
            
        Returns:
            文件的URL路径
            
        Raises:
            HTTPException: 保存失败时抛出异常
        """
        logger.info(f"开始保存封面文件: room_id={room_id}, filename={file.filename}")
        
        try:
            # 1. 验证文件
            FileHandler.validate_image_file(file)
            
            # 2. 获取文件扩展名
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            
            # 3. 生成存储路径
            fs_path, url_path = FileHandler.generate_cover_path(room_id, file_ext)
            
            # 4. 读取文件内容并检查大小
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            
            # 5. 保存文件
            with open(fs_path, "wb") as f:
                f.write(contents)
            
            logger.info(f"封面文件保存成功: room_id={room_id}, path={url_path}")
            return url_path
            
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            logger.error(f"保存封面文件失败: room_id={room_id}, error={str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="文件保存失败"
            )
    
    @staticmethod
    def delete_old_cover(cover_url: str) -> None:
        """
        删除旧的封面文件
        
        Args:
            cover_url: 封面URL路径
        """
        if not cover_url:
            return
        
        try:
            # 从URL路径转换为文件系统路径
            # URL格式: /media/rooms/{room_id}/cover_{timestamp}.{ext}
            # 移除开头的 /media/
            relative_path = cover_url.replace("/media/", "")
            fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
            
            # 检查文件是否存在
            if os.path.exists(fs_path):
                os.remove(fs_path)
                logger.info(f"成功删除旧封面文件: path={fs_path}")
            else:
                logger.debug(f"旧封面文件不存在: path={fs_path}")
                
        except Exception as e:
            # 删除失败时只记录警告，不中断流程
            logger.warning(f"删除旧封面文件失败: cover_url={cover_url}, error={str(e)}")
    
    # ==================== Tab 图片上传（不覆盖房间封面，每张独立存储）====================
    
    @staticmethod
    def generate_tab_image_path(room_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成 Tab 图片存储路径（每次上传独立文件，不覆盖已有文件）。

        Args:
            room_id: 房间ID
            extension: 文件扩展名

        Returns:
            (文件系统路径, URL路径)的元组
        """
        timestamp = int(time.time())
        unique = uuid.uuid4().hex[:8]
        relative_dir = f"rooms/{room_id}/tabs"
        filename = f"tab_{unique}_{timestamp}.{extension}"
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        url_path = f"/media/{relative_dir}/{filename}"
        os.makedirs(fs_dir, exist_ok=True)
        return fs_path, url_path
    
    @staticmethod
    async def save_tab_image_file(file: UploadFile, room_id: uuid.UUID) -> str:
        """
        保存 Tab 图片并返回相对 URL 路径。
        与房间封面上传独立，不删除任何已有文件，多 Tab 多图互不覆盖。

        Args:
            file: 上传的文件对象
            room_id: 房间ID

        Returns:
            文件的 URL 路径（相对路径，如 /media/rooms/{room_id}/tabs/tab_xxx.ext）

        Raises:
            HTTPException: 验证失败或保存失败时抛出
        """
        logger.info(f"开始保存 Tab 图片: room_id={room_id}, filename={file.filename}")
        try:
            FileHandler.validate_image_file(file)
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            fs_path, url_path = FileHandler.generate_tab_image_path(room_id, file_ext)
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            with open(fs_path, "wb") as f:
                f.write(contents)
            logger.info(f"Tab 图片保存成功: room_id={room_id}, path={url_path}")
            return url_path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存 Tab 图片失败: room_id={room_id}, error={str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="文件保存失败")
    
    # ==================== 专题横幅文件处理方法 ====================
    
    @staticmethod
    def generate_banner_path(topic_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成横幅存储路径
        
        完全复用 generate_cover_path 的逻辑，只调整路径前缀和文件名前缀。
        
        Args:
            topic_id: 专题ID
            extension: 文件扩展名
            
        Returns:
            (文件系统路径, URL路径)的元组
        """
        # 生成时间戳
        timestamp = int(time.time())
        
        # 构建路径（改为 topics 和 banner）
        relative_dir = f"topics/{topic_id}"
        filename = f"banner_{timestamp}.{extension}"
        
        # 文件系统路径
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        
        # URL路径
        url_path = f"/media/{relative_dir}/{filename}"
        
        # 确保目录存在
        os.makedirs(fs_dir, exist_ok=True)
        logger.debug(f"生成横幅路径: fs_path={fs_path}, url_path={url_path}")
        
        return fs_path, url_path
    
    @staticmethod
    async def save_banner_file(file: UploadFile, topic_id: uuid.UUID) -> str:
        """
        保存横幅文件并返回URL
        
        完全复用 save_cover_file 的逻辑，只调整路径（通过调用 generate_banner_path）。
        
        Args:
            file: 上传的文件对象
            topic_id: 专题ID
            
        Returns:
            文件的URL路径
            
        Raises:
            HTTPException: 保存失败时抛出异常
        """
        logger.info(f"开始保存横幅文件: topic_id={topic_id}, filename={file.filename}")
        
        try:
            # 1. 验证文件
            FileHandler.validate_image_file(file)
            
            # 2. 获取文件扩展名
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            
            # 3. 生成存储路径（调用 generate_banner_path）
            fs_path, url_path = FileHandler.generate_banner_path(topic_id, file_ext)
            
            # 4. 读取文件内容并检查大小
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            
            # 5. 同步保存文件
            with open(fs_path, "wb") as f:
                f.write(contents)
            
            logger.info(f"横幅文件保存成功: topic_id={topic_id}, path={url_path}")
            return url_path
            
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            logger.error(f"保存横幅文件失败: topic_id={topic_id}, error={str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="文件保存失败"
            )
    
    @staticmethod
    def delete_old_banner(banner_url: str) -> None:
        """
        删除旧的横幅文件
        
        完全复用 delete_old_cover 的逻辑，只调整路径处理。
        
        Args:
            banner_url: 横幅URL路径
        """
        if not banner_url:
            return
        
        try:
            # 从URL路径转换为文件系统路径
            # URL格式: /media/topics/{topic_id}/banner_{timestamp}.{ext}
            # 移除开头的 /media/
            relative_path = banner_url.replace("/media/", "")
            fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
            
            # 检查文件是否存在
            if os.path.exists(fs_path):
                os.remove(fs_path)
                logger.info(f"成功删除旧横幅文件: path={fs_path}")
            else:
                logger.debug(f"旧横幅文件不存在: path={fs_path}")
                
        except Exception as e:
            # 删除失败时只记录警告，不中断流程
            logger.warning(f"删除旧横幅文件失败: banner_url={banner_url}, error={str(e)}")
    
    # ==================== 品牌Logo文件处理方法 ====================
    
    @staticmethod
    def generate_brand_logo_path(brand_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成品牌Logo存储路径
        
        Args:
            brand_id: 品牌ID
            extension: 文件扩展名
            
        Returns:
            (文件系统路径, URL路径)的元组
        """
        # 生成时间戳
        timestamp = int(time.time())
        
        # 构建路径
        relative_dir = f"brands/{brand_id}"
        filename = f"logo_{timestamp}.{extension}"
        
        # 文件系统路径
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        
        # URL路径
        url_path = f"/media/{relative_dir}/{filename}"
        
        # 确保目录存在
        os.makedirs(fs_dir, exist_ok=True)
        logger.debug(f"生成品牌Logo路径: fs_path={fs_path}, url_path={url_path}")
        
        return fs_path, url_path
    
    @staticmethod
    async def save_brand_logo(file: UploadFile, brand_id: uuid.UUID) -> str:
        """
        保存品牌Logo文件并返回URL
        
        完全复用现有文件保存逻辑，仅调整路径生成。
        
        Args:
            file: 上传的文件对象
            brand_id: 品牌ID
            
        Returns:
            文件的URL路径
            
        Raises:
            HTTPException: 保存失败时抛出异常
        """
        logger.info(f"开始保存品牌Logo: brand_id={brand_id}, filename={file.filename}")
        
        try:
            # 1. 验证文件
            FileHandler.validate_image_file(file)
            
            # 2. 获取文件扩展名
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            
            # 3. 生成存储路径
            fs_path, url_path = FileHandler.generate_brand_logo_path(brand_id, file_ext)
            
            # 4. 读取文件内容并检查大小
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            
            # 5. 保存文件
            with open(fs_path, "wb") as f:
                f.write(contents)
            
            logger.info(f"品牌Logo保存成功: brand_id={brand_id}, path={url_path}")
            return url_path
            
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            logger.error(f"保存品牌Logo失败: brand_id={brand_id}, error={str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="文件保存失败")
    
    # ==================== 专家头像文件处理方法 ====================
    
    @staticmethod
    def generate_expert_avatar_path(expert_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成专家头像存储路径
        
        Args:
            expert_id: 专家ID
            extension: 文件扩展名
            
        Returns:
            (文件系统路径, URL路径)的元组
        """
        timestamp = int(time.time())
        
        relative_dir = f"experts/{expert_id}"
        filename = f"avatar_{timestamp}.{extension}"
        
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        
        url_path = f"/media/{relative_dir}/{filename}"
        
        os.makedirs(fs_dir, exist_ok=True)
        logger.debug(f"生成专家头像路径: fs_path={fs_path}, url_path={url_path}")
        
        return fs_path, url_path
    
    @staticmethod
    async def save_expert_avatar(file: UploadFile, expert_id: uuid.UUID) -> str:
        """
        保存专家头像文件并返回URL
        
        完全复用现有文件保存逻辑，仅调整路径生成。
        
        Args:
            file: 上传的文件对象
            expert_id: 专家ID
            
        Returns:
            文件的URL路径
            
        Raises:
            HTTPException: 保存失败时抛出异常
        """
        logger.info(f"开始保存专家头像: expert_id={expert_id}, filename={file.filename}")
        
        try:
            FileHandler.validate_image_file(file)
            
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            
            fs_path, url_path = FileHandler.generate_expert_avatar_path(expert_id, file_ext)
            
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            
            with open(fs_path, "wb") as f:
                f.write(contents)
            
            logger.info(f"专家头像保存成功: expert_id={expert_id}, path={url_path}")
            return url_path
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存专家头像失败: expert_id={expert_id}, error={str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="文件保存失败")

    # ==================== 焦点图图片文件处理方法 ====================

    @staticmethod
    def generate_featured_content_image_path(content_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成焦点图图片存储路径

        Args:
            content_id: 焦点图ID
            extension: 文件扩展名

        Returns:
            (文件系统路径, URL路径)的元组
        """
        timestamp = int(time.time())
        relative_dir = f"featured_content/{content_id}"
        filename = f"image_{timestamp}.{extension}"
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        url_path = f"/media/{relative_dir}/{filename}"
        os.makedirs(fs_dir, exist_ok=True)
        logger.debug(f"生成焦点图图片路径: fs_path={fs_path}, url_path={url_path}")
        return fs_path, url_path

    @staticmethod
    async def save_featured_content_image(file: UploadFile, content_id: uuid.UUID) -> str:
        """
        保存焦点图图片并返回 URL 路径。

        Args:
            file: 上传的文件对象
            content_id: 焦点图ID

        Returns:
            文件的 URL 路径（如 /media/featured_content/{content_id}/image_xxx.ext）

        Raises:
            HTTPException: 验证失败或保存失败时抛出
        """
        logger.info(f"开始保存焦点图图片: content_id={content_id}, filename={file.filename}")
        try:
            FileHandler.validate_image_file(file)
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            fs_path, url_path = FileHandler.generate_featured_content_image_path(content_id, file_ext)
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            with open(fs_path, "wb") as f:
                f.write(contents)
            logger.info(f"焦点图图片保存成功: content_id={content_id}, path={url_path}")
            return url_path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存焦点图图片失败: content_id={content_id}, error={str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="文件保存失败")

    @staticmethod
    def delete_old_featured_content_image(image_url: str) -> None:
        """
        删除旧的焦点图图片文件（本地 /media/ 路径时）。

        Args:
            image_url: 焦点图图片 URL 路径
        """
        if not image_url or not image_url.startswith("/media/"):
            return
        try:
            relative_path = image_url.replace("/media/", "")
            fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
            if os.path.exists(fs_path):
                os.remove(fs_path)
                logger.info(f"成功删除旧焦点图图片: path={fs_path}")
            else:
                logger.debug(f"旧焦点图图片不存在: path={fs_path}")
        except Exception as e:
            logger.warning(f"删除旧焦点图图片失败: image_url={image_url}, error={str(e)}")

    @staticmethod
    def delete_featured_content_media(content_id: uuid.UUID, image_url: str) -> None:
        """
        删除焦点图本地媒体目录（featured_content/{content_id}/）。

        仅当 image_url 位于该焦点图自己的 /media/featured_content/{content_id}/ 目录下时
        才执行删除，防止误删其他路径；目录不存在时静默忽略。

        Args:
            content_id: 焦点图ID
            image_url: 焦点图图片 URL 路径
        """
        expected_prefix = f"/media/featured_content/{content_id}/"
        if not image_url or not image_url.startswith(expected_prefix):
            logger.debug(f"跳过焦点图媒体删除: image_url 不在预期目录: {image_url}")
            return
        relative_dir = image_url.replace("/media/", "", 1).rsplit("/", 1)[0]
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        if not os.path.isdir(fs_dir):
            logger.debug(f"焦点图媒体目录不存在，跳过: {fs_dir}")
            return
        try:
            shutil.rmtree(fs_dir, ignore_errors=True)
            if not os.path.exists(fs_dir):
                logger.info(f"删除焦点图媒体目录: {fs_dir}")
            else:
                logger.warning(f"焦点图媒体目录删除不完整（可能存在无法删除的文件）: {fs_dir}")
        except Exception as e:
            logger.warning(f"删除焦点图媒体目录失败: fs_dir={fs_dir}, error={str(e)}")

    # ==================== 科室（分类）图标文件处理方法 ====================

    @staticmethod
    def generate_category_icon_path(category_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成科室（分类）图标存储路径

        Args:
            category_id: 分类ID
            extension: 文件扩展名

        Returns:
            (文件系统路径, URL路径)的元组
        """
        timestamp = int(time.time())
        relative_dir = f"categories/{category_id}"
        filename = f"icon_{timestamp}.{extension}"
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        url_path = f"/media/{relative_dir}/{filename}"
        os.makedirs(fs_dir, exist_ok=True)
        logger.debug(f"生成科室图标路径: fs_path={fs_path}, url_path={url_path}")
        return fs_path, url_path

    @staticmethod
    async def save_category_icon(file: UploadFile, category_id: uuid.UUID) -> str:
        """
        保存科室（分类）图标文件并返回 URL 路径。

        Args:
            file: 上传的文件对象
            category_id: 分类ID

        Returns:
            文件的 URL 路径（如 /media/categories/{category_id}/icon_xxx.ext）

        Raises:
            HTTPException: 验证失败或保存失败时抛出
        """
        logger.info(f"开始保存科室图标: category_id={category_id}, filename={file.filename}")
        try:
            FileHandler.validate_image_file(file)
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
            fs_path, url_path = FileHandler.generate_category_icon_path(category_id, file_ext)
            contents = await file.read()
            if len(contents) > UPLOAD_MAX_SIZE:
                logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
                )
            with open(fs_path, "wb") as f:
                f.write(contents)
            logger.info(f"科室图标保存成功: category_id={category_id}, path={url_path}")
            return url_path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存科室图标失败: category_id={category_id}, error={str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="文件保存失败")

    @staticmethod
    def delete_old_category_icon(icon_url: str) -> None:
        """
        删除旧的科室（分类）图标文件（本地 /media/ 路径时）。

        Args:
            icon_url: 科室图标 URL 路径
        """
        if not icon_url or not icon_url.startswith("/media/"):
            return
        try:
            relative_path = icon_url.replace("/media/", "")
            fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
            if os.path.exists(fs_path):
                os.remove(fs_path)
                logger.info(f"成功删除旧科室图标: path={fs_path}")
            else:
                logger.debug(f"旧科室图标不存在: path={fs_path}")
        except Exception as e:
            logger.warning(f"删除旧科室图标失败: icon_url={icon_url}, error={str(e)}")

