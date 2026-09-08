"""用户头像上传服务

头像只能通过 POST /api/v1/users/me/avatar 上传，不可经 PATCH /me 写入 avatar_url。
落盘前预留图片审核调用点；V1.0 placeholder 不检测、始终放行。
"""

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_safety.exceptions import ContentSafetyBlockedException, ContentSafetyServiceException
from app.crud import crud_user
from app.image_moderation.client import ImageModerationClient, ImageModerationServiceError
from app.models.users import User

logger = logging.getLogger(__name__)

AVATAR_DIR = Path("uploads/avatars")
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024


class AvatarUploadError(Exception):
    def __init__(self, message: str, *, code: int = 4001):
        self.message = message
        self.code = code
        super().__init__(message)


def _resolve_extension(file: UploadFile) -> str:
    content_type = (file.content_type or "").lower()
    by_type = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    if content_type in by_type:
        return by_type[content_type]
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS:
            return ext.lstrip(".")
    return ""


class AvatarUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.moderation = ImageModerationClient()

    async def upload_avatar(self, user: User, file: UploadFile) -> str:
        ext = _resolve_extension(file)
        if not ext:
            raise AvatarUploadError("仅支持 JPG/PNG/WEBP 格式头像")

        file_bytes = await file.read()
        if len(file_bytes) > MAX_AVATAR_BYTES:
            raise AvatarUploadError("头像文件过大，最大 5MB")
        if not file_bytes:
            raise AvatarUploadError("上传文件为空")

        # 审核调用点：placeholder 不检测；切换厂商后此处生效
        try:
            result = await self.moderation.moderate(
                file_bytes=file_bytes,
                content_type=file.content_type or f"image/{ext}",
                scene="avatar",
            )
        except ImageModerationServiceError as exc:
            raise ContentSafetyServiceException(str(exc)) from exc

        if not result.passed:
            raise ContentSafetyBlockedException("头像图片内容违规")

        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{user.public_id}_{uuid.uuid4().hex[:12]}.{ext}"
        dest = AVATAR_DIR / filename
        dest.write_bytes(file_bytes)

        avatar_url = f"/uploads/avatars/{filename}"
        await crud_user.update(self.db, user, {"avatar_url": avatar_url})
        logger.info("用户头像上传成功: user_id=%s path=%s", user.id, avatar_url)
        return avatar_url
