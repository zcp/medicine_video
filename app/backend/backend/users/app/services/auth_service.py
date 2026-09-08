"""
认证服务层 - AuthService
封装所有认证相关的业务逻辑，包括验证码、登录、JWT管理等
"""
import re
import uuid
import base64
import hashlib
import json
import logging
import random
import string
import os
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


import jwt
from jwt import PyJWKClient
from jwt import InvalidTokenError, ExpiredSignatureError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis_client
from app.core.config import settings  # ✅ 导入配置
from app.core.password import hash_password, verify_password, is_legacy_sha256_hash
from app.core.phone import is_valid_cn_phone, normalize_cn_phone, validate_cn_phone
from app.services.sms_provider import AliyunSmsProvider, MockSmsProvider, SmsProvider
from app.services.carrier_auth_provider import (
    MockCarrierAuthProvider,
    CarrierAuthProvider,
)
from app.crud import crud_user
from app.models.users import EntityStatus
from app import schemas
from app.exceptions import InvalidTokenException, InvalidCredentialsException, ValidationError

# Authing SDK导入
from authing import AuthenticationClient

# 条件导入captcha库
try:
    from captcha.image import ImageCaptcha
    CAPTCHA_AVAILABLE = True
except ImportError:
    CAPTCHA_AVAILABLE = False

logger = logging.getLogger(__name__)


class CaptchaErrorException(Exception):
    """图形验证码错误异常"""
    pass


class RateLimitException(Exception):
    """频率限制异常"""
    pass


class UserAlreadyExistsException(Exception):
    """用户已存在异常"""
    pass


class InvalidCredentialsException(Exception):
    """无效凭证异常"""
    pass


class InvalidTokenException(Exception):
    """无效令牌异常"""
    pass


class InvalidResetTokenException(Exception):
    """无效重置令牌异常"""
    pass


class WeakPasswordException(Exception):
    """密码强度不足异常"""
    pass


class AuthService:
    """认证服务类"""

    def __init__(self, db: AsyncSession, redis_client=None):
        """
        初始化认证服务

        Args:
            db: 数据库会话
            redis_client: Redis客户端（可选，如果不提供会获取默认客户端）
        """
        self.db = db
        self.redis_client = redis_client or get_redis_client()

        self.sms_provider: SmsProvider = self._build_sms_provider()
        self.carrier_auth_provider: CarrierAuthProvider = self._build_carrier_auth_provider()

        # JWT配置 - 从配置模块读取
        self.jwt_secret_key = settings.JWT_SECRET_KEY
        self.jwt_algorithm = settings.JWT_ALGORITHM

        # Authing 客户端配置 - 从配置模块读取
        try:
            app_id = settings.VITE_CLIENT_ID
            app_secret = settings.USER_POOL_SECRET
            app_host = settings.APP_HOST
            redirect_url = settings.REDIRECT_URL
            
            if app_id and app_secret:
                self.auth_client = AuthenticationClient(
                    app_id=app_id,
                    app_secret=app_secret,
                    app_host=app_host,
                    redirect_uri=redirect_url
                )
                logger.info("Authing 客户端初始化成功")
            else:
                logger.warning("Authing 配置缺失（VITE_CLIENT_ID 或 USER_POOL_SECRET 未设置），SSO功能将不可用")
                self.auth_client = None
        except Exception as e:
            logger.error(f"Authing 客户端初始化失败: {e}")
            self.auth_client = None

    def _build_sms_provider(self) -> SmsProvider:
        """Build SMS provider from explicit configuration."""
        if settings.SMS_PROVIDER == "mock":
            return MockSmsProvider()
        if settings.SMS_PROVIDER == "aliyun":
            return AliyunSmsProvider(
                access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
                access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
                sign_name=settings.ALIYUN_SMS_SIGN_NAME,
                template_code=settings.ALIYUN_SMS_TEMPLATE_CODE,
            )
        raise ValueError("SMS_PROVIDER must be mock, or aliyun")

    def _build_carrier_auth_provider(self) -> CarrierAuthProvider:
        """Build carrier auth provider from explicit configuration."""
        if not settings.CARRIER_AUTH_PROVIDER or settings.CARRIER_AUTH_PROVIDER == "mock":
            return MockCarrierAuthProvider()
        raise ValueError("CARRIER_AUTH_PROVIDER must be mock or empty")

    # ========================================================================
    # 工具方法
    # ========================================================================

    def _generate_captcha_solution(self, length: int = 5) -> str:
        """生成随机验证码答案"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _generate_otp(self, length: int = 6) -> str:
        """生成数字OTP验证码"""
        return ''.join(random.choice(string.digits) for _ in range(length))

    def _hash_password(self, password: str) -> str:
        """安全的密码哈希（使用 bcrypt）"""
        return hash_password(password)

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码，兼容旧 SHA-256 与新版 bcrypt"""
        return verify_password(password, password_hash)

    async def _upgrade_password_hash_if_needed(self, user, password: str):
        """如果用户密码还是旧 SHA-256 格式，登录成功后自动升级为 bcrypt"""
        if is_legacy_sha256_hash(user.password_hash):
            new_hash = self._hash_password(password)
            user.password_hash = new_hash
            await self.db.commit()
            logger.info(f"用户密码哈希已从 SHA-256 升级为 bcrypt: user_id={user.id}")

    def _mask_recipient(self, recipient: str) -> str:
        """掩码处理收件人信息"""
        if "@" in recipient:  # 邮箱
            local, domain = recipient.split("@", 1)
            if len(local) <= 2:
                masked_local = "*" * len(local)
            else:
                masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
            return f"{masked_local}@{domain}"
        else:  # 手机号
            if len(recipient) <= 4:
                return "*" * len(recipient)
            return recipient[:3] + "*" * (len(recipient) - 6) + recipient[-3:]

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

    def _create_access_token(
        self,
        user_public_id: int,
        user_role: str = None,
        username: Optional[str] = None,
        nickname: Optional[str] = None,
        can_stream: bool = True,
        avatar_url: Optional[str] = None,
    ) -> str:
        """生成访问令牌
        
        Args:
            user_public_id: 用户的公开ID（UUID字符串）
            user_role: 用户角色（为None或空字符串时使用空字符串""表示游客）
            username: 用户名（可选，用于前端展示）
            nickname: 用户昵称（可选，用于前端展示）
            can_stream: 是否可开播，默认 true，false 表示管理员禁播
            avatar_url: 头像 URL（可选，用于头像等场景前端展示）
        """
        now = datetime.utcnow()
        # 验证user_public_id是有效的UUID字符串
        try:
            uuid.UUID(user_public_id)
        except ValueError:
            logger.error(f"无效的UUID格式: {user_public_id}")
            raise ValueError(f"user_public_id必须是有效的UUID字符串")

        payload: Dict[str, Any] = {
            "user_id": user_public_id,  # 使用UUID字符串
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": str(uuid.uuid4()),
        }
        # 始终包含role字段：如果有角色则使用角色值，否则使用空字符串表示访客
        # 这样前端逻辑更统一，不需要检查字段是否存在
        if user_role and user_role.strip():
            payload["role"] = user_role
        else:
            payload["role"] = ""  # 空字符串表示访客

        payload["can_stream"] = can_stream

        # 可选：在JWT中包含用户名、昵称、头像，方便前端展示用户信息
        if username:
            payload["username"] = username
        if nickname:
            payload["nickname"] = nickname
        if avatar_url:
            payload["avatar_url"] = avatar_url

        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

    def _create_refresh_token(self, user_public_id: int) -> str:
        """创建刷新令牌"""
        now = datetime.utcnow()
        # 验证user_public_id是有效的UUID字符串
        try:
            uuid.UUID(user_public_id)
        except ValueError:
            logger.error(f"无效的UUID格式: {user_public_id}")
            raise ValueError(f"user_public_id必须是有效的UUID字符串")

        payload = {
            "user_id": user_public_id,  # 使用UUID字符串
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=7),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

    def _verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=[self.jwt_algorithm],
                leeway=settings.JWT_LEEWAY_SECONDS,
            )
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("JWT令牌无效")
            return None

    async def _is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        try:
            blacklisted = await self.redis_client.get(f"blacklist:token:{token}")
            return blacklisted is not None
        except Exception:
            return False

    async def _blacklist_token(self, token: str, expire_time: int = 3600) -> bool:
        """将令牌加入黑名单"""
        try:
            await self.redis_client.set(f"blacklist:token:{token}", "1", ex=expire_time)
            return True
        except Exception:
            return False

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

    # ========================================================================
    # 主要业务方法
    # ========================================================================

    async def generate_captcha(self) -> dict:
        """
        生成图形验证码

        Returns:
            包含captcha_id和image_base64的字典

        Raises:
            Exception: 当Redis操作失败或图片生成失败时
        """
        logger.info("开始生成图形验证码")

        try:
            # 1. 生成唯一ID和随机答案
            captcha_id = str(uuid.uuid4())
            captcha_solution = self._generate_captcha_solution()

            logger.info(f"生成验证码: captcha_id={captcha_id}")

            # 2. 存储到Redis
            cache_key = f"captcha:solution:{captcha_id}"
            await self.redis_client.set(cache_key, captcha_solution.lower(), ex=180)  # 3分钟过期

            # 3. 生成图片
            # 使用320x120像素以支持高DPI设备（2x DPR），在标准设备上自动缩小仍保持清晰
            if CAPTCHA_AVAILABLE:
                image_captcha = ImageCaptcha(width=320, height=120)
                image_data = image_captcha.generate(captcha_solution)
                image_bytes = image_data.getvalue()
                image_base64 = base64.b64encode(image_data.getvalue()).decode('utf-8')
            else:
                # 如果captcha库不可用，返回模拟数据
                image_base64 = base64.b64encode(b"fake_image_data").decode('utf-8')
                image_bytes = b"fake_image_data"
                logger.warning("captcha库不可用，返回模拟图片数据")

            # 返回可访问的图片 URL（防缓存可由前端自行拼 ?ts=Date.now()）
            # Redis client decodes responses as text, so store captcha image as base64.
            await self.redis_client.set(f"captcha:image:{captcha_id}", image_base64, ex=180)

            image_url = f"api/v1/auth/captcha/image/{captcha_id}"
            logger.info(f"成功生成图形验证码: captcha_id={captcha_id}")

            return {
                "captcha_id": captcha_id,
                "image_url": image_url,
                # 兼容保留（可选）
                "image_base64": f"data:image/png;base64,{image_base64}"
            }

        except Exception as e:
            logger.error(f"生成图形验证码失败: error={e}")
            raise

    async def send_otp_code(self, otp_request: schemas.VerificationCodeRequest, client_ip: str = None) -> dict:
        """
        发送OTP验证码

        Args:
            otp_request: 验证码发送请求
            client_ip: 客户端IP地址（用于频率限制）

        Returns:
            包含发送结果的字典

        Raises:
            CaptchaErrorException: 图形验证码错误
            RateLimitException: 请求频率超限
            UserAlreadyExistsException: 注册场景下用户已存在
        """
        logger.info(f"开始处理发送验证码请求: recipient={self._mask_recipient(otp_request.recipient)}, scenario={otp_request.scenario}")

        try:
            # 1. 图形验证码校验（LOGIN 场景跳过，由 IP 限流 + OTP 尝试次数兜底）
            if otp_request.scenario != "LOGIN":
                if not await self._verify_captcha(otp_request.captcha_id, otp_request.captcha_solution):
                    logger.warning(f"图形验证码校验失败: captcha_id={otp_request.captcha_id}")
                    raise CaptchaErrorException("图形验证码错误或已过期")

            # 2. 频率限制检查
            if client_ip:
                rate_limit_key = f"rate_limit:verification_code:{client_ip}"
                request_count = await self.redis_client.get(rate_limit_key)

                if request_count and int(request_count) >= 5:  # 每小时最多5次
                    logger.warning(f"IP请求频率超限: ip={client_ip}")
                    raise RateLimitException("请求过于频繁，请在 60 秒后重试")

            # 3. 业务前置检查（按 channel 路由）
            if otp_request.scenario == "REGISTER":
                existing_user = await self._find_user_by_channel(otp_request.channel, otp_request.recipient)
                if existing_user:
                    logger.warning(f"注册验证码发送失败，用户已存在: recipient={self._mask_recipient(otp_request.recipient)}")
                    raise UserAlreadyExistsException("该账号已被注册")
            elif otp_request.scenario == "RESET_PASSWORD":
                existing_user = await self._find_user_by_channel(otp_request.channel, otp_request.recipient)
                if not existing_user:
                    logger.warning(f"重置密码验证码发送失败，用户不存在: recipient={self._mask_recipient(otp_request.recipient)}")
                    return {
                        "message": "验证码已发送，请注意查收。",
                        "recipient_masked": self._mask_recipient(otp_request.recipient),
                        "cooldown_seconds": 60
                    }

            # 4. 生成和存储OTP（JSON 格式，包含尝试次数）
            otp_code = self._generate_otp()
            otp_key = f"otp:{otp_request.scenario}:{otp_request.recipient}"
            otp_data = {
                "code": otp_code,
                "attempts": 0,
                "max_attempts": 5,
                "created_at": datetime.utcnow().isoformat(),
            }
            await self.redis_client.set(otp_key, json.dumps(otp_data), ex=300)  # 5分钟过期

            # 5. 更新频率限制计数
            if client_ip:
                await self.redis_client.incr(rate_limit_key)
                await self.redis_client.expire(rate_limit_key, 3600)  # 1小时过期

            # 6. 调用 provider 发送（SMS 走短信、EMAIL 仍日志模拟）
            if otp_request.channel == "SMS":
                sent = await self.sms_provider.send(
                    phone=otp_request.recipient,
                    code=otp_code,
                    template_params={"minutes": "5"},
                )
                if not sent:
                    raise RuntimeError("短信服务发送失败")
            logger.info(f"验证码已生成: recipient={self._mask_recipient(otp_request.recipient)}, "
                        f"code_length={len(otp_code)}, scenario={otp_request.scenario}, channel={otp_request.channel}")

            # 掩码处理收件人信息
            recipient_masked = self._mask_recipient(otp_request.recipient)

            logger.info(f"成功处理验证码发送请求: recipient={recipient_masked}")

            return {
                "message": "验证码已发送，请注意查收。",
                "recipient_masked": recipient_masked,
                "cooldown_seconds": 60
            }

        except (CaptchaErrorException, RateLimitException, UserAlreadyExistsException):
            raise
        except Exception as e:
            logger.error(f"发送验证码失败: error={e}")
            raise

    async def login_user(self, login_request: schemas.LoginRequest, client_ip: str = None) -> dict:
        """
        用户登录

        Args:
            login_request: 登录请求
            client_ip: 客户端IP地址

        Returns:
            包含access_token和refresh_token的字典

        Raises:
            CaptchaErrorException: 图形验证码错误
            RateLimitException: 登录频率超限
            InvalidCredentialsException: 用户名或密码错误
        """
        logger.info(f"开始处理用户登录请求: username={login_request.username}")

        # IP限流key（预先定义，供多个分支使用）
        rate_limit_key = f"rate_limit:login_ip:{client_ip}" if client_ip else None

        try:
            # 0. IP级别频率限制（防暴力破解）
            if client_ip:
                attempt_count = await self.redis_client.get(rate_limit_key)
                if attempt_count and int(attempt_count) >= 10:
                    logger.warning(f"登录IP请求频率超限: ip={client_ip}")
                    raise RateLimitException("登录尝试过于频繁，请稍后重试")

            # 1. 图形验证码校验
            if not await self._verify_captcha(login_request.captcha_id, login_request.captcha_solution):
                logger.warning(f"登录时图形验证码校验失败: captcha_id={login_request.captcha_id}")
                raise CaptchaErrorException("图形验证码错误或已过期")

            # 2. 用户查询（三合一：手机号/邮箱/用户名）
            #    纯数字输入只可能是手机号：非法格式统一按凭证错误处理（防枚举），合法则归一化后再查库
            username = login_request.username
            if username.isdigit():
                if not is_valid_cn_phone(username):
                    logger.warning(f"登录失败，纯数字非手机号: username={username}")
                    raise InvalidCredentialsException("账号或密码错误")
                username = normalize_cn_phone(username)
            user = await crud_user.get_by_login_identifier(self.db, identifier=username)
            if not user:
                logger.warning(f"登录失败，用户不存在: username={login_request.username}")
                raise InvalidCredentialsException("账号或密码错误")

            # 提前提取用户属性以防止MissingGreenlet错误
            user_id = user.id
            user_public_id = str(user.public_id)  # 新增：获取public_id
            user_username = user.username
            user_nickname = getattr(user, "nickname", None)
            user_status = user.status
            user_password_hash = user.password_hash
            # 获取角色值：已登录用户的role一定存在（数据库约束：nullable=False, default=REGULAR）
            # 如果未来需要支持访客token，可以在这里处理role为空的情况
            user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            user_can_stream = bool(getattr(user, "can_stream", True))
            user_avatar_url = getattr(user, "avatar_url", None)

            # 3. 状态和密码校验
            if user_status != EntityStatus.NORMAL:
                logger.warning(f"登录失败，用户状态异常: username={login_request.username}, status={user_status}")
                raise InvalidCredentialsException("账户状态异常")

            if not self._verify_password(login_request.password, user_password_hash):
                logger.warning(f"登录失败，密码错误: username={login_request.username}")
                # 记录IP失败次数（防暴力破解计数）
                if client_ip and rate_limit_key:
                    await self.redis_client.incr(rate_limit_key)
                    await self.redis_client.expire(rate_limit_key, 3600)
                raise InvalidCredentialsException("账号或密码错误")

            # 4. 生成Token（包含角色信息与用户展示信息）
            access_token = self._create_access_token(
                user_public_id,
                user_role,
                username=user_username,
                nickname=user_nickname,
                can_stream=user_can_stream,
                avatar_url=user_avatar_url,
            )
            refresh_token = self._create_refresh_token(user_public_id)

            # 5. 更新登录信息
            user.last_login_at = datetime.utcnow()
            if client_ip:
                user.last_login_ip = client_ip
                # 登录成功后重置IP计数
                if rate_limit_key:
                    await self.redis_client.delete(rate_limit_key)

            # 5.1 如果密码是旧 SHA-256 格式，自动升级为 bcrypt（无感滚动迁移）
            await self._upgrade_password_hash_if_needed(user, login_request.password)

            await self.db.commit()

            logger.info(f"用户登录成功: user_id={user_id}, public_id={user_public_id}, username={user_username}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }

        except (CaptchaErrorException, InvalidCredentialsException):
            raise
        except Exception as e:
            logger.error(f"用户登录失败: error={e}")
            raise



    def verify_id_token_pyjwt(self, id_token: str, issuer: str, audience: str, timeout: int = 5) -> dict:
        """
        使用 PyJWT 的 PyJWKClient 校验 RS256 OIDC id_token
        issuer 例：https://uni-app-multiplatform.authing.cn/oidc
        audience 例：你的 App ID（从环境变量 VITE_CLIENT_ID 读取）
        """
        issuer = issuer.rstrip("/")
        jwks_url = f"{issuer}/.well-known/jwks.json"

        jwk_client = PyJWKClient(jwks_url, timeout=timeout)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)

        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},  # 可按需调整
            leeway=60,  # 允许 60s 时间漂移
        )
        return payload

    async def sso_login(self, db: AsyncSession, *, id_token: str, client_ip: str) -> dict:
        """
        Authing SSO 登录

        Args:
            db: 数据库会话
            id_token: Authing ID Token
            client_ip: 客户端IP地址

        Returns:
            包含access_token和refresh_token的字典

        Raises:
            InvalidTokenException: Token无效
            InvalidCredentialsException: 用户状态异常
        """
        logger.info("开始处理 SSO 登录请求")

        try:
            # 1. 验证 Authing ID Token - 从配置模块读取
            audience = settings.VITE_CLIENT_ID
            issuer = settings.ISSUER
            logger.info(f"OIDC 配置: ISSUER={issuer}, VITE_CLIENT_ID={audience}")
            payload = self.verify_id_token_pyjwt(
                id_token=id_token,
                audience=audience,
                issuer=issuer
            )

            # 2. 从 payload 提取用户信息
            authing_user_id = payload["sub"]
            user_email = payload.get("email")
            user_nickname = payload.get("nickname")

            logger.info(f"Authing Token 验证成功: user_id={authing_user_id}, email={self._mask_recipient(user_email) if user_email else 'N/A'}")

            # 3. 查找或创建用户
            user = None

            # 3a. 首先根据 social_id 精确查找
            user = await crud_user.get_by_social_id(
                db, provider="authing", social_id=authing_user_id
            )

            # 3b. 如果未找到且有邮箱，尝试链接现有账户
            if not user and user_email:
                user = await crud_user.get_by_email(db, user_email)
                if user:
                    # 更新现有账户的社交登录信息
                    user.social_provider = "authing"
                    user.social_id = authing_user_id
                    await db.commit()
                    logger.info(f"链接现有账户: user_id={user.id}, email={self._mask_recipient(user_email) if user_email else 'N/A'}")

            # 3c. 如果仍未找到，创建新用户
            if not user:
                from app.schemas.users import UserCreate
                user_create = UserCreate(
                    username=f"authing_{authing_user_id[:8]}",  # 生成唯一用户名
                    email=user_email,
                    nickname=user_nickname or "Authing用户",
                    social_provider="authing",
                    social_id=authing_user_id
                )
                user = await crud_user.create(db, user_create, password_hash=None)
                logger.info(f"创建新用户: user_id={user.id}, email={self._mask_recipient(user_email) if user_email else 'N/A'}")

            # 提前提取用户属性以防止MissingGreenlet错误
            user_id = user.id
            user_public_id = str(user.public_id)  # 新增：获取public_id
            user_status = user.status
            # 获取角色值：已登录用户的role一定存在（数据库约束：nullable=False, default=REGULAR）
            # 如果未来需要支持访客token，可以在这里处理role为空的情况
            user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            user_can_stream = bool(getattr(user, "can_stream", True))
            user_avatar_url = getattr(user, "avatar_url", None)

            # 4. 检查用户状态
            if user_status == EntityStatus.BANNED:
                logger.warning(f"SSO登录失败，用户被封禁: user_id={user_id}")
                raise InvalidCredentialsException("账户已被封禁")

            # 5. 生成应用的 JWT - 使用public_id而不是id（包含角色信息）
            access_token = self._create_access_token(user_public_id, user_role, can_stream=user_can_stream, avatar_url=user_avatar_url)
            refresh_token = self._create_refresh_token(user_public_id)

            # 6. 更新登录信息
            user.last_login_at = datetime.utcnow()
            if client_ip:
                user.last_login_ip = client_ip

            await db.commit()

            logger.info(f"SSO登录成功: user_id={user_id}, public_id={user_public_id}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }

        except Exception as e:
            if "invalid" in str(e).lower() or "expired" in str(e).lower():
                logger.warning(f"Authing Token 验证失败: {e}")
                raise InvalidTokenException("身份验证失败")
            else:
                logger.error(f"SSO登录失败: error={e}")
                raise
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新access_token的字典
            
        Raises:
            InvalidTokenException: 令牌无效或已过期
        """
        logger.info("开始处理令牌刷新请求")
        
        try:
            # 1. Token验证
            payload = self._verify_token(refresh_token, token_type="refresh")
            if not payload:
                logger.warning("刷新令牌无效或已过期")
                raise InvalidTokenException("凭证无效或已过期")
            
            # 2. 黑名单检查
            if await self._is_token_blacklisted(refresh_token):
                logger.warning("刷新令牌已在黑名单中")
                raise InvalidTokenException("凭证无效或已过期")
            
            # 3. Token生成
            user_id = payload.get("user_id")
            # 验证user_id是有效的UUID
            try:
                uuid.UUID(user_id)
            except (ValueError, TypeError):
                logger.error(f"刷新令牌中的user_id无效: {user_id}")
                raise InvalidTokenException("令牌格式无效")

            # 3.1 检查用户会话是否已被吊销（密码重置后旧 token 失效）
            # 提取 token 签发时间，仅当 iat < 吊销时间时才拒绝
            iat_timestamp = payload.get("iat")
            token_iat = datetime.utcfromtimestamp(iat_timestamp) if iat_timestamp else None
            if await self._is_user_sessions_revoked(user_id, token_iat=token_iat):
                logger.warning(f"用户会话已被吊销，拒绝刷新: user_id={user_id}")
                raise InvalidTokenException("凭证已失效，请重新登录")

            # 3.2 将旧 refresh_token 加入黑名单（轮换：单次使用，防止重放攻击）
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                remaining = max(int(exp_timestamp - datetime.utcnow().timestamp()), 0)
                await self._blacklist_token(refresh_token, expire_time=remaining)
            else:
                await self._blacklist_token(refresh_token, expire_time=86400 * 7)

            # 从数据库查询用户角色（刷新token时需要获取最新角色）
            user = await crud_user.get_by_uuid(self.db, public_id=uuid.UUID(user_id))
            if not user:
                logger.warning(f"刷新令牌时用户不存在: user_id={user_id}")
                raise InvalidTokenException("用户不存在")
            
            # 获取角色值
            user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            user_can_stream = bool(getattr(user, "can_stream", True))
            user_avatar_url = getattr(user, "avatar_url", None)
            new_access_token = self._create_access_token(user_id, user_role, can_stream=user_can_stream, avatar_url=user_avatar_url)
            new_refresh_token = self._create_refresh_token(user_id)
            
            logger.info(f"成功刷新令牌: user_id={user_id}, role={user_role}")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"令牌刷新失败: error={e}")
            raise
    
    async def logout_user(self, access_token: str):
        """
        用户登出
        
        Args:
            access_token: 访问令牌
            
        Raises:
            InvalidTokenException: 令牌无效
        """
        logger.info("开始处理用户登出请求")
        
        try:
            # 1. Token验证
            payload = self._verify_token(access_token, token_type="access")
            if not payload:
                logger.warning("访问令牌无效或已过期")
                raise InvalidTokenException("认证凭证格式无效")
            
            # 2. 将access_token加入黑名单
            await self._blacklist_token(access_token, expire_time=3600)
            
            # 3. 吊销该用户所有 refresh token，防止登出后继续使用
            user_public_id = payload.get("user_id")
            if user_public_id:
                await self._revoke_user_sessions(user_public_id)
            logger.info(f"用户成功登出并吊销会话: public_id={user_public_id}")
            
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"用户登出失败: error={e}")
            raise
    
    async def request_password_reset(self, reset_request: schemas.PasswordResetRequest):
        """
        请求密码重置
        
        Args:
            reset_request: 密码重置请求
            
        Raises:
            CaptchaErrorException: 图形验证码错误
        """
        logger.info(f"开始处理密码重置请求: email={self._mask_recipient(reset_request.email)}")
        
        try:
            # 1. 图形验证码校验
            if not await self._verify_captcha(reset_request.captcha_id, reset_request.captcha_solution):
                logger.warning(f"图形验证码校验失败: captcha_id={reset_request.captcha_id}")
                raise CaptchaErrorException("图形验证码错误或已过期")
            
            # 2. 用户查询
            user = await crud_user.get_by_email(self.db, reset_request.email)
            
            # 3. 安全处理：如果用户不存在，为了防止邮箱枚举攻击，直接返回
            if not user:
                logger.info(f"密码重置请求的邮箱不存在: email={self._mask_recipient(reset_request.email)}")
                return  # 直接返回，不执行任何操作也不抛出异常

            # 3.1 检查账号状态（BANNED/DELETED 用户不允许重置）
            if user.status in (EntityStatus.BANNED, EntityStatus.DELETED):
                logger.info(f"禁止重置密码的用户尝试重置: user_id={user.id}, status={user.status}")
                return  # 仍返回成功，防枚举

            # 4. Token生成
            reset_token = secrets.token_urlsafe(32)
            
            # 5. 存入缓存
            reset_key = f"password_reset:{reset_token}"
            await self.redis_client.set(reset_key, str(user.id), ex=900)  # 15分钟过期
            
            # 6. 异步发送邮件（模拟）
            logger.info(f"密码重置 token 已生成: email={self._mask_recipient(reset_request.email)}")
            
            logger.info(f"成功处理密码重置请求: email={self._mask_recipient(reset_request.email)}")
            
        except CaptchaErrorException:
            raise
        except Exception as e:
            logger.error(f"密码重置请求失败: error={e}")
            raise
    
    async def perform_password_reset(self, confirm_request: schemas.PasswordResetConfirmRequest):
        """
        执行密码重置（支持邮箱 reset_token 和 OTP 验证后的 reset_ticket 两种路径）
        
        Args:
            confirm_request: 密码重置确认请求
            
        Raises:
            InvalidResetTokenException: 重置凭据无效
            WeakPasswordException: 密码强度不足
            InvalidCredentialsException: 凭据缺失或账号状态异常
        """
        logger.info("开始处理密码重置执行请求")
        
        # 0. 校验至少提供了一种凭据
        if not confirm_request.reset_token and not confirm_request.reset_ticket:
            raise InvalidCredentialsException("缺少重置凭据")
        
        # 0.1 先校验密码强度（两种路径共用，避免弱密码浪费凭据）
        if not self._validate_password_strength(confirm_request.new_password):
            logger.warning("新密码不符合强度要求")
            raise WeakPasswordException("密码必须至少8位，且包含大写字母、小写字母、数字和特殊字符")
        
        try:
            # ---- reset_ticket 路径（OTP 验证后签发）----
            if confirm_request.reset_ticket:
                ticket_data = await self._consume_ticket(
                    purpose="RESET_PASSWORD",
                    ticket_id=confirm_request.reset_ticket,
                )
                user_id = int(ticket_data["user_id"])
            
            # ---- reset_token 路径（邮箱链接，保留兼容）----
            elif confirm_request.reset_token:
                reset_key = f"password_reset:{confirm_request.reset_token}"
                user_id_str = await self.redis_client.get(reset_key)
                
                if not user_id_str:
                    logger.warning("重置令牌无效或已过期")
                    raise InvalidResetTokenException("密码重置链接无效或已过期")
                
                # 原子删除 token
                deleted = await self.redis_client.delete(reset_key)
                if not deleted:
                    raise InvalidResetTokenException("密码重置链接已被使用")
                
                user_id = int(user_id_str)
            else:
                raise InvalidCredentialsException("缺少重置凭据")
            
            # 查用户、检查状态
            user = await crud_user.get(self.db, user_id)
            if not user:
                logger.warning(f"重置密码时用户不存在: user_id={user_id}")
                raise InvalidResetTokenException("无效的凭据")

            # 检查账号状态（BANNED/DELETED 用户禁止重置）
            if user.status in (EntityStatus.BANNED, EntityStatus.DELETED):
                raise InvalidCredentialsException("账户状态异常，无法重置密码")

            # 新旧密码一致性校验：重置后的密码不得与原密码相同（与修改密码场景 user_service 一致）
            if self._verify_password(confirm_request.new_password, user.password_hash):
                logger.warning(f"新密码与原密码相同: user_id={user_id}")
                raise ValidationError("new_password", "新密码不能与原密码相同")

            # 密码哈希和更新
            new_password_hash = self._hash_password(confirm_request.new_password)
            update_data = {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
            await crud_user.update(self.db, db_obj=user, obj_in=update_data)

            # 重置成功后吊销所有旧 refresh token / 会话
            user_public_id = str(user.public_id)
            await self._revoke_user_sessions(user_public_id)
            
            logger.info(f"成功重置用户密码: user_id={user_id}")
            
        except (InvalidResetTokenException, WeakPasswordException, InvalidCredentialsException):
            raise
        except Exception as e:
            logger.error(f"密码重置失败: error={e}")
            raise

    async def _revoke_user_sessions(self, user_public_id: str):
        """密码重置后吊销该用户所有现存 refresh token

        当前项目无双持久化的 refresh token 表，因此使用 Redis 时间戳截止线方案：
        - 记录吊销时间戳
        - refresh_token 接口在签发新 access token 前，对比 token iat 与吊销时间
        - iat 早于吊销时间的 token 一律拒绝
        """
        revocation_key = f"user_sessions_revoked:{user_public_id}"
        await self.redis_client.set(
            revocation_key,
            datetime.utcnow().isoformat(),
            ex=86400 * 7,  # 7 天过期（与 refresh token 有效期一致）
        )
        logger.info(f"已吊销用户所有会话: public_id={user_public_id}")

    async def _is_user_sessions_revoked(self, user_public_id: str, token_iat: Optional[datetime] = None) -> bool:
        """检查用户会话是否已被吊销

        与 _revoke_user_sessions 配对使用。
        当提供 token_iat（token 签发时间）时，仅当 token 签发早于吊销时间才视为已吊销，
        避免误伤重置后新签发的 token。

        Args:
            user_public_id: 用户公开 UUID 字符串
            token_iat: 令牌的签发时间（datetime），从 JWT payload 中的 iat 转换而来

        Returns:
            True 表示会话已吊销（且 token 签发在吊销之前），False 表示有效
        """
        revocation_key = f"user_sessions_revoked:{user_public_id}"
        revocation_time_str = await self.redis_client.get(revocation_key)
        if not revocation_time_str:
            return False
        if token_iat is None:
            # 没有提供签发时间时，保守视为已吊销（向后兼容）
            return True
        try:
            revocation_time = datetime.fromisoformat(revocation_time_str)
            return token_iat < revocation_time
        except (ValueError, TypeError):
            logger.warning(f"解析吊销时间戳失败: {revocation_time_str}")
            return True

    # ========================================================================
    # Phase 3: 手机号注册
    # ========================================================================

    async def consume_ticket(self, purpose: str, ticket_id: str) -> dict:
        """公开的 ticket 消费接口（供 endpoint 层调用）"""
        return await self._consume_ticket(purpose, ticket_id)

    async def login_by_phone_ticket(self, login_request) -> dict:
        """手机号验证码登录：消费 LOGIN ticket 后签发 JWT。"""
        ticket_data = await self._consume_ticket("LOGIN", login_request.login_ticket)

        if ticket_data.get("channel") != "SMS":
            raise InvalidCredentialsException("登录凭证无效")

        phone = ticket_data.get("recipient")
        if not phone:
            raise InvalidCredentialsException("登录凭证无效")

        user = await crud_user.get_by_phone_number(self.db, phone_number=phone)
        if not user:
            raise InvalidCredentialsException("账号或密码错误")

        user_id = user.id
        user_public_id = str(user.public_id)
        user_status = user.status
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        user_username = user.username if hasattr(user, "username") else None
        user_nickname = user.nickname if hasattr(user, "nickname") else None
        user_can_stream = bool(getattr(user, "can_stream", True))
        user_avatar_url = getattr(user, "avatar_url", None)

        if user_status != EntityStatus.NORMAL:
            raise InvalidCredentialsException("账户状态异常")

        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        access_token = self._create_access_token(
            user_public_id,
            user_role,
            username=user_username,
            nickname=user_nickname,
            can_stream=user_can_stream,
            avatar_url=user_avatar_url,
        )
        refresh_token = self._create_refresh_token(user_public_id)

        logger.info(f"手机号验证码登录成功: user_id={user_id}, phone={self._mask_recipient(phone)}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_public_id": user_public_id,
            "username": user_username or "",
            "nickname": user_nickname or "",
            "phone_masked": self._mask_recipient(phone),
        }

    async def register_by_phone_ticket(self, register_request) -> dict:
        """手机号注册：消费 register_ticket → 创建用户 → 签发 JWT

        Args:
            register_request: PhoneRegisterRequest，含 register_ticket / password / nickname

        Returns:
            {user, access_token, refresh_token, token_type, is_new_user}

        Raises:
            InvalidTokenException: ticket 无效
            UserAlreadyExistsException: 手机号已注册
            WeakPasswordException: 密码强度不足
        """
        # 1. 消费 ticket，获取手机号
        ticket_data = await self._consume_ticket("REGISTER", register_request.register_ticket)
        phone = ticket_data["recipient"]

        # 2. 校验手机号未被占用
        existing = await crud_user.get_by_phone_number(self.db, phone_number=phone)
        if existing:
            raise UserAlreadyExistsException("该手机号已被注册")

        # 3. 校验密码强度
        if not self._validate_password_strength(register_request.password):
            raise WeakPasswordException("密码必须至少8位，且包含大写字母、小写字母、数字和特殊字符")

        # 4. 创建用户
        from app.schemas.users import UserCreate
        import uuid as _uuid

        username = f"u_{_uuid.uuid4().hex[:10]}"

        user_create = UserCreate(
            username=username,
            email=None,
            nickname=register_request.nickname,
            phone_number=phone,
            social_provider=None,
            social_id=None,
        )
        new_user = await crud_user.create(self.db, user_create, self._hash_password(register_request.password))

        # 5. 标记手机号已验证 — 在 commit 前提取属性
        new_user.is_phone_verified = True
        _reg_username = new_user.username
        _reg_nickname = new_user.nickname
        _reg_avatar_url = getattr(new_user, "avatar_url", None)
        await self.db.commit()
        await self.db.refresh(new_user)

        # 6. 签发 JWT
        user_public_id = str(new_user.public_id)
        access_token = self._create_access_token(
            user_public_id, "REGULAR",
            can_stream=bool(getattr(new_user, "can_stream", True)),
            avatar_url=_reg_avatar_url,
        )
        refresh_token = self._create_refresh_token(user_public_id)

        logger.info(
            f"手机号注册成功: user_id={new_user.id}, phone={self._mask_recipient(phone)}"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "is_new_user": True,
            "phone_masked": self._mask_recipient(phone),
            "user_public_id": user_public_id,
            "username": _reg_username or "",
            "nickname": _reg_nickname or "",
        }

    # ========================================================================
    # Phase 4: 一键登录
    # ========================================================================

    async def one_tap_login(self, one_tap_request) -> dict:
        """一键登录：运营商 token → 手机号 → 查/建用户 → 签发 JWT

        Args:
            one_tap_request: OneTapLoginRequest，含 carrier_token

        Returns:
            {access_token, refresh_token, token_type, is_new_user, phone_masked}

        Raises:
            InvalidTokenException: carrier_token 无效
        """
        # 0. 检查用户是否同意服务条款（自动注册场景的合规要求）
        if not getattr(one_tap_request, 'agreed_to_terms', False):
            logger.warning("一键登录失败：用户未同意服务条款")
            raise InvalidCredentialsException("请先同意服务条款和隐私政策")

        # 1. 调用号码认证服务，用 carrier_token 换取真实手机号
        try:
            phone = await self.carrier_auth_provider.get_phone_number(
                one_tap_request.carrier_token
            )
        except (ValueError, NotImplementedError) as e:
            logger.warning(f"一键登录取号失败: {e}")
            raise InvalidTokenException("取号失败，请使用其他方式登录")

        # 1.1 防御性校验与归一化（运营商返回值不经 Schema，是外部输入；日志不记明文手机号）
        try:
            phone = validate_cn_phone(phone)
        except ValueError:
            logger.warning(f"运营商取号返回非法手机号: provider={one_tap_request.provider}")
            raise InvalidTokenException("取号失败，请使用其他方式登录")

        # 2. 按手机号查用户
        user = await crud_user.get_by_phone_number(self.db, phone_number=phone)
        is_new_user = False

        # 3. 用户不存在 → 自动注册
        if not user:
            from app.schemas.users import UserCreate
            import uuid as _uuid

            username = f"u_{_uuid.uuid4().hex[:10]}"
            user_create = UserCreate(
                username=username,
                email=None,
                nickname=f"用户{phone[-4:]}",
                phone_number=phone,
                social_provider="carrier",
                social_id=f"carrier:{phone}",
            )
            user = await crud_user.create(self.db, user_create, password_hash=None)
            # crud_user.create 内部已 commit+refresh，user 属性可直接读取
            user.is_phone_verified = True
            is_new_user = True
            logger.info(f"一键登录自动注册: user_id={user.id}, phone={self._mask_recipient(phone)}")

        # 4. 提取用户属性（在 commit 之前，防止 SQLAlchemy expire_on_commit 导致的 greenlet 错误）
        user_id = user.id
        user_public_id = str(user.public_id)
        user_status = user.status
        user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        user_username = user.username if hasattr(user, 'username') else None
        user_nickname = user.nickname if hasattr(user, 'nickname') else None
        user_can_stream = bool(getattr(user, "can_stream", True))
        user_avatar_url = getattr(user, "avatar_url", None)

        # 5. 检查用户状态
        if user_status == EntityStatus.BANNED:
            raise InvalidCredentialsException("账户已被封禁")
        if user_status == EntityStatus.DELETED:
            raise InvalidCredentialsException("账户已注销")

        # 6. 更新登录信息
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        # 7. 签发 JWT（使用已提取的属性）
        access_token = self._create_access_token(
            user_public_id, user_role,
            username=user_username, nickname=user_nickname,
            can_stream=user_can_stream,
            avatar_url=user_avatar_url,
        )
        refresh_token = self._create_refresh_token(user_public_id)

        logger.info(f"一键登录成功: user_id={user_id}, is_new={is_new_user}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "is_new_user": is_new_user,
            "phone_masked": self._mask_recipient(phone),
            "user_public_id": user_public_id,
            "username": user_username or "",
            "nickname": user_nickname or "",
        }

    async def one_tap_login_direct(self, phone: str, sign: str, timestamp: str) -> dict:
        """云函数签名一键登录（Phase 4 安全方案B — HMAC签名验证）

        客户端从 DCloud 云函数拿到 {phoneNumber, sign, timestamp} 后提交后端。
        后端通过 HMAC 验签确保手机号来自云函数、未经客户端篡改。

        Args:
            phone: 云函数解密后的真实手机号
            sign: HMAC-SHA256(phone + timestamp, PSK) 签名
            timestamp: 签名时间戳（毫秒）

        Returns:
            {access_token, refresh_token, token_type, is_new_user, phone_masked}

        Raises:
            InvalidTokenException: 签名无效或时间戳过期
            InvalidCredentialsException: 用户状态异常
        """
        # 1. 验证 PSK 已配置
        if not settings.DCLOUD_API_KEY:
            logger.error("DCLOUD_API_KEY 未配置，云函数签名一键登录不可用")
            raise InvalidTokenException("取号失败，请使用其他方式登录")

        # 2. 验证时间戳（60秒内有效，防重放）
        import time as _time
        now_ms = int(_time.time() * 1000)
        try:
            ts_ms = int(timestamp)
            if abs(now_ms - ts_ms) > 60_000:
                logger.warning(f"云函数签名时间戳过期: now={now_ms}, ts={ts_ms}")
                raise InvalidTokenException("取号失败，请使用其他方式登录")
        except (ValueError, TypeError):
            logger.warning("云函数签名时间戳格式无效")
            raise InvalidTokenException("取号失败，请使用其他方式登录")

        # 3. 验证 HMAC 签名
        import hashlib as _hashlib
        message = f"{phone}{timestamp}"
        expected_sign = hmac.new(
            settings.DCLOUD_API_KEY.encode("utf-8"),
            message.encode("utf-8"),
            _hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(sign, expected_sign):
            logger.warning("云函数 HMAC 签名验证失败")
            raise InvalidTokenException("取号失败，请使用其他方式登录")

        # 3.5 验签通过后，防御性校验并归一化为纯 11 位（§6.3.2 定稿顺序：先验签后归一化；
        #     validate_cn_phone 返回即归一化值；Schema 已校验但此处兜底防绕过）
        try:
            phone = validate_cn_phone(phone)
        except ValueError:
            logger.warning("云函数取号返回非法手机号")
            raise InvalidTokenException("取号失败，请使用其他方式登录")

        # 2. 按手机号查用户
        user = await crud_user.get_by_phone_number(self.db, phone_number=phone)
        is_new_user = False

        # 3. 用户不存在 → 自动注册
        if not user:
            from app.schemas.users import UserCreate
            import uuid as _uuid

            username = f"u_{_uuid.uuid4().hex[:10]}"
            user_create = UserCreate(
                username=username,
                email=None,
                nickname=f"用户{phone[-4:]}",
                phone_number=phone,
                social_provider="carrier",
                social_id=f"carrier:{phone}",
            )
            user = await crud_user.create(self.db, user_create, password_hash=None)
            user.is_phone_verified = True
            is_new_user = True
            logger.info(f"云函数一键登录自动注册: user_id={user.id}, phone={self._mask_recipient(phone)}")

        # 4. 提取用户属性
        user_id = user.id
        user_public_id = str(user.public_id)
        user_status = user.status
        user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        user_username = user.username if hasattr(user, 'username') else None
        user_nickname = user.nickname if hasattr(user, 'nickname') else None
        user_can_stream = bool(getattr(user, "can_stream", True))
        user_avatar_url = getattr(user, "avatar_url", None)

        # 5. 检查用户状态
        if user_status == EntityStatus.BANNED:
            raise InvalidCredentialsException("账户已被封禁")
        if user_status == EntityStatus.DELETED:
            raise InvalidCredentialsException("账户已注销")

        # 6. 更新登录信息
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        # 7. 签发 JWT
        access_token = self._create_access_token(
            user_public_id, user_role,
            username=user_username, nickname=user_nickname,
            can_stream=user_can_stream,
            avatar_url=user_avatar_url,
        )
        refresh_token = self._create_refresh_token(user_public_id)

        logger.info(f"云函数一键登录成功: user_id={user_id}, is_new={is_new_user}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "is_new_user": is_new_user,
            "phone_masked": self._mask_recipient(phone),
            "user_public_id": user_public_id,
            "username": user_username or "",
            "nickname": user_nickname or "",
        }

    # ========================================================================
    # OTP 校验与 Ticket 管理
    # ========================================================================

    async def verify_otp_and_issue_ticket(self, verify_request) -> dict:
        """校验 OTP 并签发短期 ticket

        调用时机：前端在用户输入验证码后调用此接口。
        校验成功后签发一个短期 ticket，后续业务操作（重置密码、注册等）
        只认 ticket 不认原始 OTP。

        Args:
            verify_request: VerifyCodeRequest，含 channel / recipient / scenario / code

        Returns:
            {"ticket": str, "expires_in": int}

        Raises:
            InvalidTokenException: OTP 不存在或已过期
            InvalidCredentialsException: 验证码错误
            RateLimitException: 尝试次数超限
        """
        otp_key = f"otp:{verify_request.scenario}:{verify_request.recipient}"
        otp_data_str = await self.redis_client.get(otp_key)

        if not otp_data_str:
            raise InvalidTokenException("验证码不存在或已过期")

        # 解析 OTP 数据（兼容旧版纯字符串格式）
        try:
            otp_data = json.loads(otp_data_str)
        except (json.JSONDecodeError, TypeError):
            otp_data = {"code": otp_data_str, "attempts": 0, "max_attempts": 5}

        # 检查尝试次数
        if otp_data.get("attempts", 0) >= otp_data.get("max_attempts", 5):
            await self.redis_client.delete(otp_key)
            raise RateLimitException("验证码尝试次数过多，请重新获取")

        # 比对验证码
        if otp_data["code"] != verify_request.code:
            otp_data["attempts"] = otp_data.get("attempts", 0) + 1
            ttl = await self.redis_client.ttl(otp_key)
            if ttl <= 0:
                await self.redis_client.delete(otp_key)
                raise InvalidTokenException("验证码不存在或已过期")
            await self.redis_client.set(otp_key, json.dumps(otp_data), ex=ttl)
            remaining = otp_data["max_attempts"] - otp_data["attempts"]
            raise InvalidCredentialsException(f"验证码错误，还剩 {remaining} 次机会")

        # ✅ 验证成功，立即删除 OTP
        await self.redis_client.delete(otp_key)

        # 签发 ticket
        ticket_id = secrets.token_urlsafe(32)
        ticket_data = {
            "purpose": verify_request.scenario,
            "recipient": verify_request.recipient,
            "channel": verify_request.channel,
            "created_at": datetime.utcnow().isoformat(),
        }

        # RESET_PASSWORD 场景：ticket 中嵌入 user_id，后续重置时直接使用
        if verify_request.scenario == "RESET_PASSWORD":
            user = await self._find_user_by_channel(verify_request.channel, verify_request.recipient)
            if not user:
                raise InvalidTokenException("验证码不存在或已过期")
            ticket_data["user_id"] = user.id
            ticket_data["user_public_id"] = str(user.public_id)

        ticket_key = f"ticket:{verify_request.scenario}:{ticket_id}"
        await self.redis_client.set(ticket_key, json.dumps(ticket_data), ex=600)

        logger.info(
            f"ticket 已签发: purpose={verify_request.scenario}, "
            f"recipient={self._mask_recipient(verify_request.recipient)}"
        )

        return {"ticket": ticket_id, "expires_in": 600}

    async def _find_user_by_channel(self, channel: str, recipient: str):
        """按 channel 路由查找用户（SMS → 手机号，EMAIL → 邮箱）"""
        if channel == "SMS":
            return await crud_user.get_by_phone_number(self.db, phone_number=recipient)
        return await crud_user.get_by_email(self.db, recipient)

    async def _consume_ticket(self, purpose: str, ticket_id: str) -> dict:
        """校验并消费 ticket（单次使用，读取后立即删除）

        Args:
            purpose: ticket 用途，如 RESET_PASSWORD / REGISTER
            ticket_id: ticket 唯一标识

        Returns:
            ticket 的 JSON payload

        Raises:
            InvalidTokenException: ticket 不存在或已过期
        """
        ticket_key = f"ticket:{purpose}:{ticket_id}"
        ticket_data_str = await self.redis_client.get(ticket_key)

        if not ticket_data_str:
            raise InvalidTokenException("凭证无效或已过期")

        # 原子消费：读取后立即删除
        await self.redis_client.delete(ticket_key)

        return json.loads(ticket_data_str) 
