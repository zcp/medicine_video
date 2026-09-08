"""
用户服务层 - UserService
封装所有用户相关的业务逻辑，包括注册、更新、密码管理、账户注销等
"""
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.redis_client import get_redis_client
from app.core.password import hash_password, verify_password, is_legacy_sha256_hash
from app.core.phone import normalize_cn_phone
from app.crud import crud_user
from app.schemas.users import UserCreate, UserUpdateSelf
from app.models.users import User
import re

logger = logging.getLogger(__name__)


def _mask_recipient(recipient: str) -> str:
    """掩码处理收件人信息（邮箱或手机号），避免明文落入日志"""
    if not recipient:
        return "N/A"
    if "@" in recipient:
        local, domain = recipient.split("@", 1)
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    else:
        if len(recipient) <= 4:
            return "*" * len(recipient)
        return recipient[:3] + "*" * (len(recipient) - 6) + recipient[-3:]


# ============================================================================
# 业务异常定义
# ============================================================================

class UserServiceException(Exception):
    """用户服务基础异常"""
    pass


class UsernameAlreadyExistsError(UserServiceException):
    """用户名已存在异常"""
    def __init__(self, username: str):
        self.username = username
        super().__init__("该账号已被注册")


class EmailAlreadyExistsError(UserServiceException):
    """邮箱已存在异常"""
    def __init__(self, email: str):
        self.email = email
        super().__init__("该账号已被注册")


class InvalidPasswordError(UserServiceException):
    """无效密码异常"""
    def __init__(self, message: str = "当前密码不正确"):
        super().__init__(message)


class WeakPasswordError(UserServiceException):
    """密码强度不足异常"""
    def __init__(self, message: str = "密码必须至少8位，且包含大写字母、小写字母、数字和特殊字符"):
        super().__init__(message)


class NoUpdateDataProvidedError(UserServiceException):
    """没有提供更新数据异常"""
    def __init__(self, message: str = "没有提供有效的更新数据"):
        super().__init__(message)


class ActiveSubscriptionError(UserServiceException):
    """活跃订阅异常"""
    def __init__(self, message: str = "账户存在活跃订阅，无法注销"):
        super().__init__(message)


class CaptchaErrorException(UserServiceException):
    """图形验证码错误异常"""
    def __init__(self, message: str = "图形验证码错误或已过期"):
        super().__init__(message)


class ValidationError(UserServiceException):
    """参数验证异常"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


# ============================================================================
# 用户服务类
# ============================================================================

class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        """
        初始化用户服务
        
        Args:
            db: 数据库会话
            redis_client: Redis客户端（可选，如果不提供会获取默认客户端）
        """
        self.db = db
        self.redis_client = redis_client or get_redis_client()
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def _hash_password(self, password: str) -> str:
        """安全的密码哈希（使用 bcrypt）"""
        return hash_password(password)
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码，兼容旧 SHA-256 与新版 bcrypt"""
        return verify_password(password, password_hash)

    async def _upgrade_password_hash_if_needed(self, user, password: str):
        """如果用户密码还是旧 SHA-256 格式，升级为 bcrypt"""
        if is_legacy_sha256_hash(user.password_hash):
            new_hash = self._hash_password(password)
            user.password_hash = new_hash
            await self.db.commit()
            logger.info(f"用户密码哈希已从 SHA-256 升级为 bcrypt: user_id={user.id}")
    
    def _validate_password_strength(self, password: str) -> bool:
        """验证密码强度 - 要求最小长度8位、大写字母、小写字母、数字和特殊字符"""
        if len(password) < 8:
            return False
        
        # 检查是否包含大写字母
        if not re.search(r'[A-Z]', password):
            return False
        
        # 检查是否包含小写字母
        if not re.search(r'[a-z]', password):
            return False
        
        # 检查是否包含数字
        if not re.search(r'\d', password):
            return False
        
        # 检查是否包含特殊字符
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            return False
        
        return True
    
    def _validate_username(self, username: str) -> bool:
        """验证用户名格式"""
        # 简单验证：字母、数字、下划线，长度3-50
        if not username or len(username) < 3 or len(username) > 50:
            return False
        return username.replace('_', '').isalnum()
    
    def _validate_email_old(self, email: str) -> bool:
        """验证邮箱格式"""
        # 简单验证：包含@和.
        if not email or '@' not in email or '.' not in email:
            return False
        return True

    def _validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        # 更严格的验证：检查基本格式
        if not email or '@' not in email or '.' not in email:
            return False

        # 检查 @ 符号前后都有内容
        parts = email.split('@')
        if len(parts) != 2:
            return False

        local_part = parts[0]
        domain_part = parts[1]

        # 检查本地部分（用户名）不为空
        if not local_part or len(local_part.strip()) == 0:
            return False

        # 检查域名部分包含点号且不为空
        if not domain_part or '.' not in domain_part or len(domain_part.strip()) == 0:
            return False

        # 检查域名部分的基本格式
        domain_parts = domain_part.split('.')
        if len(domain_parts) < 2:
            return False

        # 检查每个域名部分都不为空
        for part in domain_parts:
            if not part or len(part.strip()) == 0:
                return False

        return True

    async def _verify_captcha(self, captcha_id: str, captcha_solution: str) -> bool:
        """验证图形验证码"""
        try:
            cache_key = f"captcha:solution:{captcha_id}"
            stored_solution = await self.redis_client.get(cache_key)
            
            if not stored_solution or stored_solution != captcha_solution.lower():
                return False
            
            # 删除已使用的验证码
            await self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"验证图形验证码失败: {e}")
            return False
    
    async def _blacklist_user_tokens(self, user: User) -> None:
        """修改密码或注销后吊销用户所有会话（使旧 refresh token 失效）

        写入 user_sessions_revoked key，refresh_access_token 中的
        _is_user_sessions_revoked 检查会拦截旧 refresh token。

        Args:
            user: 用户对象，需包含 public_id
        """
        try:
            user_public_id = str(user.public_id)
            revocation_key = f"user_sessions_revoked:{user_public_id}"
            await self.redis_client.set(
                revocation_key,
                datetime.utcnow().isoformat(),
                ex=86400 * 7,  # 7 天过期（与 refresh token 有效期一致）
            )
            logger.info(f"已吊销用户所有会话: user_id={user.id}, public_id={user_public_id}")
        except Exception as e:
            logger.error(f"吊销用户会话失败: user_id={user.id}, error={e}")
    
    # ========================================================================
    # 主要业务方法
    # ========================================================================
    
    async def register_user(self, register_request, is_email_verified: bool = False) -> User:
        """
        用户注册

        Args:
            register_request: 注册请求对象
            is_email_verified: 邮箱是否已验证（通过OTP ticket）

        Returns:
            创建成功的用户对象

        Raises:
            ValidationError: 参数验证失败
            CaptchaErrorException: 验证码错误
            UsernameAlreadyExistsError: 用户名已存在
            EmailAlreadyExistsError: 邮箱已存在
        """
        logger.info(f"开始处理用户注册请求: username={register_request.username}, email={_mask_recipient(register_request.email)}")

        try:
            # 1. 参数格式验证
            if not self._validate_username(register_request.username):
                logger.warning(f"用户名格式无效: username={register_request.username}")
                raise ValidationError("username", "用户名格式无效，应为3-50位字母数字下划线组合")

            if not self._validate_email(register_request.email):
                logger.warning(f"邮箱格式无效: email={_mask_recipient(register_request.email)}")
                raise ValidationError("email", "邮箱格式无效")

            if not self._validate_password_strength(register_request.password):
                logger.warning(f"密码强度不足: username={register_request.username}")
                raise ValidationError("password", "密码必须至少8位，且包含大写字母、小写字母、数字和特殊字符")

            # 2. 图形验证码校验
            if not await self._verify_captcha(register_request.captcha_id, register_request.captcha_solution):
                logger.warning(f"注册时图形验证码校验失败: captcha_id={register_request.captcha_id}")
                raise CaptchaErrorException()

            # 3. 唯一性检查
            existing_user_by_username = await crud_user.get_by_username(self.db, register_request.username)
            if existing_user_by_username:
                logger.warning(f"用户名已存在: username={register_request.username}")
                raise UsernameAlreadyExistsError(register_request.username)

            existing_user_by_email = await crud_user.get_by_email(self.db, register_request.email)
            if existing_user_by_email:
                logger.warning(f"邮箱已存在: email={_mask_recipient(register_request.email)}")
                raise EmailAlreadyExistsError(register_request.email)

            # 4. 密码哈希处理
            password_hash = self._hash_password(register_request.password)

            # 5. 构建UserCreate对象
            user_create = UserCreate(
                username=register_request.username,
                email=register_request.email,
                nickname=register_request.nickname,
                phone_number=None,  # 第一阶段不处理手机号
                social_provider=None,
                social_id=None
            )

            # 6. 创建用户
            new_user = await crud_user.create(self.db, user_create, password_hash)

            # 7. 如果邮箱已验证（通过OTP ticket），设置验证状态
            if is_email_verified:
                new_user.is_email_verified = True
                await self.db.commit()
                await self.db.refresh(new_user)
                logger.info(f"用户邮箱已标记为已验证: user_id={new_user.id}")

            logger.info(f"用户注册成功: user_id={new_user.id}, username={new_user.username}")

            return new_user
            
        except (ValidationError, CaptchaErrorException, UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except IntegrityError as e:
            logger.warning(f"数据库唯一性约束冲突: username={register_request.username}, email={_mask_recipient(register_request.email)}, error={e}")
            raise UsernameAlreadyExistsError(register_request.username)
        except Exception as e:
            logger.error(f"用户注册失败: error={e}")
            raise
    
    async def update_profile(self, user_to_update: User, update_request: UserUpdateSelf) -> User:
        """
        更新用户个人资料
        
        Args:
            user_to_update: 要更新的用户对象
            update_request: 更新请求
            
        Returns:
            更新后的用户对象
            
        Raises:
            NoUpdateDataProvidedError: 没有提供更新数据
            ValidationError: 参数验证失败
        """
        user_id = user_to_update.id
        logger.info(f"开始处理更新用户信息请求: user_id={user_id}")
        
        try:
            # 验证更新数据
            update_data = update_request.model_dump(exclude_unset=True)
            
            if not update_data:
                logger.warning(f"更新用户信息失败，无有效更新数据: user_id={user_id}")
                raise NoUpdateDataProvidedError()
            
            # 验证昵称长度
            if "nickname" in update_data and len(update_data["nickname"]) > 50:
                logger.warning(f"昵称过长: user_id={user_id}")
                raise ValidationError("nickname", "昵称长度不能超过50个字符")

            # 验证用户名（如果提供）：格式 + 唯一性
            if "username" in update_data and update_data["username"] is not None:
                new_username = update_data["username"]
                if not self._validate_username(new_username):
                    logger.warning(f"用户名格式无效: user_id={user_id}")
                    raise ValidationError("username", "用户名格式无效，应为3-50位字母数字下划线组合")
                existing = await crud_user.get_by_username(self.db, new_username)
                if existing and existing.id != user_id:
                    logger.warning(f"用户名已被占用: user_id={user_id}, username={new_username}")
                    raise UsernameAlreadyExistsError(new_username)

            # 更新用户信息
            updated_user = await crud_user.update(self.db, user_to_update, update_data)
            
            logger.info(f"成功更新用户信息: user_id={updated_user.id}")
            
            return updated_user
            
        except (NoUpdateDataProvidedError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"更新用户信息失败: user_id={user_id}, error={e}")
            raise
    
    async def change_password(self, user: User, password_request) -> None:
        """
        修改用户密码
        
        Args:
            user: 用户对象
            password_request: 密码修改请求
            
        Raises:
            InvalidPasswordError: 当前密码错误
            WeakPasswordError: 新密码强度不足
            ValidationError: 新旧密码相同
        """
        user_id = user.id
        logger.info(f"开始处理用户密码修改请求: user_id={user_id}")
        
        try:
            # 检查用户是否已有密码
            has_password = bool(user.password_hash)
            
            if has_password:
                # 验证当前密码
                if not password_request.current_password:
                    raise InvalidPasswordError("必须提供当前密码")
                if not self._verify_password(password_request.current_password, user.password_hash):
                    logger.warning(f"密码修改失败，当前密码错误: user_id={user_id}")
                    raise InvalidPasswordError()
                
                # 检查新密码是否与当前密码相同
                if self._verify_password(password_request.new_password, user.password_hash):
                    logger.warning(f"新密码与当前密码相同: user_id={user_id}")
                    raise ValidationError("new_password", "新密码不能与当前密码相同")
            
            # 验证新密码强度
            if not self._validate_password_strength(password_request.new_password):
                logger.warning(f"新密码强度不足: user_id={user_id}")
                raise WeakPasswordError()
            
            # 更新密码
            new_password_hash = self._hash_password(password_request.new_password)
            await crud_user.update(self.db, user, {"password_hash": new_password_hash})
            
            # 使所有旧令牌失效
            await self._blacklist_user_tokens(user)
            
            logger.info(f"用户密码修改成功: user_id={user_id}")
            
        except (InvalidPasswordError, WeakPasswordError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"密码修改失败: user_id={user_id}, error={e}")
            raise
    
    async def deactivate_account(
        self,
        user: User,
        *,
        captcha_id: str,
        captcha_solution: str,
    ) -> None:
        """
        注销用户账户（软删除，需图形验证码防误删/防 CSRF）
        
        Args:
            user: 用户对象
            captcha_id: 图形验证码ID
            captcha_solution: 图形验证码答案
            
        Raises:
            CaptchaErrorException: 图形验证码错误或已过期
            ActiveSubscriptionError: 存在活跃订阅
        """
        user_id = user.id
        logger.info(f"开始处理用户账户注销请求: user_id={user_id}")
        
        try:
            if not await self._verify_captcha(captcha_id, captcha_solution):
                logger.warning(f"注销时图形验证码校验失败: user_id={user_id}, captcha_id={captcha_id}")
                raise CaptchaErrorException()

            # 业务检查：检查用户是否有进行中的业务
            # 这里可以检查会员状态、订单状态等
            # 目前是模拟检查，在真实场景中需要调用相关的crud方法检查订阅状态
            
            # 模拟检查活跃订阅（在实际实现中需要查询membership表）
            # has_active_subscription = await self._check_active_subscriptions(user_id)
            # if has_active_subscription:
            #     logger.warning(f"用户存在活跃订阅，无法注销: user_id={user_id}")
            #     raise ActiveSubscriptionError()
            
            # 执行软删除
            deleted_user = await crud_user.remove(self.db, user_id)
            
            # 将用户令牌加入黑名单
            await self._blacklist_user_tokens(user)

            # PR 7 (4.4): best-effort 调用 live_core 清理接口
            user_public_id = str(user.public_id)
            try:
                import httpx
                from app.core.config import settings as app_settings
                lc_url = getattr(app_settings, "LIVE_CORE_SERVICE_URL", None)
                token = getattr(app_settings, "INTERNAL_SERVICE_TOKEN", None)
                if lc_url and token:
                    url = f"{lc_url.rstrip('/')}/api/v1/internal/users/{user_public_id}/deactivate-cleanup"
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        resp = await client.post(url, headers={"X-Internal-Token": token})
                    if resp.status_code >= 300:
                        logger.warning("live_core 清理返回异常 status=%s body=%s", resp.status_code, resp.text[:200])
                else:
                    logger.warning("跳过 live_core 清理：LIVE_CORE_SERVICE_URL 或 INTERNAL_SERVICE_TOKEN 未配置")
            except Exception as e:
                logger.error("live_core 清理失败（不影响注销）: %s", e)
            
            logger.info(f"用户账户注销成功: user_id={deleted_user.id}")
            
        except ActiveSubscriptionError:
            raise
        except CaptchaErrorException:
            raise
        except Exception as e:
            logger.error(f"用户账户注销失败: user_id={user_id}, error={e}")
            raise
    
    async def bind_phone_number(self, db: AsyncSession, *, current_user: User, phone_number: str, bind_ticket: str) -> None:
        """
        绑定手机号
        
        Args:
            db: 数据库会话
            current_user: 当前用户
            phone_number: 手机号码
            bind_ticket: 绑定票据
            
        Raises:
            ValidationError: 验证码错误或手机号已被绑定
        """
        user_id = current_user.id
        logger.info(f"开始处理手机号绑定请求: user_id={user_id}, phone_number={_mask_recipient(phone_number)}")
        
        try:
            # a. 消费 ticket
            from app.services.auth_service import AuthService, InvalidTokenException
            auth_service = AuthService(db, self.redis_client)
            try:
                ticket_data = await auth_service.consume_ticket("BIND_PHONE", bind_ticket)
            except InvalidTokenException:
                logger.warning(f"绑定票据无效或已过期: user_id={user_id}, phone_number={_mask_recipient(phone_number)}")
                raise ValidationError("bind_ticket", "绑定票据无效或已过期")
            
            # 校验 ticket 中的手机号是否与请求一致（两侧归一化后比对，
            # 兼容历史 ticket 中存了非归一化格式的情况，见 §6.3.3）
            if normalize_cn_phone(ticket_data.get("recipient") or "") != normalize_cn_phone(phone_number):
                logger.warning(f"绑定票据与手机号不匹配: user_id={user_id}, phone_number={_mask_recipient(phone_number)}")
                raise ValidationError("phone_number", "绑定票据与手机号不匹配")
            
            # b. 检查手机号是否已被占用
            existing_user = await crud_user.get_by_phone_number(db, phone_number=phone_number)
            if existing_user and existing_user.id != current_user.id:
                logger.warning(f"手机号已被其他账号绑定: user_id={user_id}, phone_number={_mask_recipient(phone_number)}")
                raise ValidationError("phone_number", "该手机号已被其他账号绑定")
            
            # c. 更新用户信息
            current_user.phone_number = phone_number
            current_user.is_phone_verified = True
            
            # d. 提交事务
            db.add(current_user)
            await db.commit()
            
            logger.info(f"手机号绑定成功: user_id={user_id}, phone_number={_mask_recipient(phone_number)}")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"手机号绑定失败: user_id={user_id}, error={e}")
            raise
    
    async def _check_active_subscriptions(self, user_id: int) -> bool:
        """
        检查用户是否有活跃订阅（预留方法）
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否有活跃订阅
        """
        # 预留方法，在实际实现中需要查询用户的会员订阅状态
        # 例如：查询 user_membership 表中是否有状态为 ACTIVE 的记录
        return False 