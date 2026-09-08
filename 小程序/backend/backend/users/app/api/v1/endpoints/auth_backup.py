"""
认证相关API端点 - 用户功能服务
实现验证码生成、OTP发送和用户登录功能
"""
import uuid
import base64
import hashlib
import logging
import random
import string
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_async_db
from app.core.redis_client import get_redis_client
from app.core.responses import success_response, error_response
from app.crud import crud_user
from app.models.users import EntityStatus

# 条件导入captcha库
try:
    from captcha.image import ImageCaptcha
    CAPTCHA_AVAILABLE = True
except ImportError:
    CAPTCHA_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Pydantic 模型定义
# ============================================================================

class VerificationCodeRequest(BaseModel):
    """发送验证码请求模型"""
    channel: str = Field(..., description="发送渠道: EMAIL, SMS")
    recipient: str = Field(..., description="接收者: 邮箱或手机号")
    scenario: str = Field(..., description="使用场景: REGISTER, RESET_PASSWORD, LOGIN")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")


class LoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")


# 批次二新增模型
class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: str = Field(..., description="用户邮箱")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")


class PasswordResetConfirmRequest(BaseModel):
    """密码重置确认模型"""
    reset_token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, description="新密码")


# ============================================================================
# 工具函数
# ============================================================================

def generate_captcha_solution(length: int = 5) -> str:
    """生成随机验证码答案"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_otp(length: int = 6) -> str:
    """生成数字OTP验证码"""
    return ''.join(random.choice(string.digits) for _ in range(length))


def hash_password(password: str) -> str:
    """简单的密码哈希（生产环境应使用bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def mask_recipient(recipient: str) -> str:
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


import jwt
from datetime import datetime, timedelta


def generate_jwt_token(user_id: int) -> dict:
    """生成标准JWT令牌"""

    # JWT配置 - 从配置模块读取
    from app.core.config import settings
    JWT_SECRET_KEY = settings.JWT_SECRET_KEY
    JWT_ALGORITHM = settings.JWT_ALGORITHM

    # 当前时间
    now = datetime.utcnow()

    # Access Token (短期有效，1小时)
    access_payload = {
        "user_id": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=1)
    }

    # Refresh Token (长期有效，7天)
    refresh_payload = {
        "user_id": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7)
    }

    # 生成JWT
    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# 批次二新增JWT工具函数
def create_access_token(user_id: int) -> str:
    """创建访问令牌"""
    from app.core.config import settings
    JWT_SECRET_KEY = settings.JWT_SECRET_KEY
    JWT_ALGORITHM = settings.JWT_ALGORITHM
    
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": str(uuid.uuid4())  # 添加唯一标识符确保token唯一性
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """创建刷新令牌"""
    from app.core.config import settings
    JWT_SECRET_KEY = settings.JWT_SECRET_KEY
    JWT_ALGORITHM = settings.JWT_ALGORITHM
    
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7),
        "jti": str(uuid.uuid4())  # 添加唯一标识符确保token唯一性
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """验证JWT令牌"""
    try:
        from app.core.config import settings
        JWT_SECRET_KEY = settings.JWT_SECRET_KEY
        JWT_ALGORITHM = settings.JWT_ALGORITHM
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT令牌已过期")
        return None
    except jwt.InvalidTokenError:
        logger.warning("JWT令牌无效")
        return None


async def is_token_blacklisted(token: str) -> bool:
    """检查令牌是否在黑名单中"""
    try:
        redis_client = get_redis_client()
        blacklisted = await redis_client.get(f"blacklist:token:{token}")
        return blacklisted is not None
    except Exception:
        return False


async def blacklist_token(token: str, expire_time: int = 3600) -> bool:
    """将令牌加入黑名单"""
    try:
        redis_client = get_redis_client()
        await redis_client.set(f"blacklist:token:{token}", "1", ex=expire_time)
        return True
    except Exception:
        return False


def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 6:
        return False
    return True


# ============================================================================
# API 端点实现
# ============================================================================

@router.get("/captcha")
async def get_captcha():
    """
    获取图形验证码
    
    Returns:
        包含验证码ID和图片的响应
    """
    logger.info("开始处理获取图形验证码请求")
    
    try:
        # 生成唯一ID和随机答案
        captcha_id = str(uuid.uuid4())
        captcha_solution = generate_captcha_solution()
        
        logger.info(f"生成验证码: captcha_id={captcha_id}")
        
        # 存储到Redis
        redis_client = get_redis_client()
        cache_key = f"captcha:solution:{captcha_id}"
        await redis_client.set(cache_key, captcha_solution.lower(), ex=180)  # 3分钟过期
        
        # 生成图片
        if CAPTCHA_AVAILABLE:
            image_captcha = ImageCaptcha(width=160, height=60)
            image_data = image_captcha.generate(captcha_solution)
            image_base64 = base64.b64encode(image_data.getvalue()).decode('utf-8')
        else:
            # 如果captcha库不可用，返回模拟数据
            image_base64 = base64.b64encode(b"fake_image_data").decode('utf-8')
            logger.warning("captcha库不可用，返回模拟图片数据")
        
        logger.info(f"成功生成图形验证码: captcha_id={captcha_id}")
        
        return success_response(data={
            "captcha_id": captcha_id,
            "image_base64": f"data:image/png;base64,{image_base64}"
        })
        
    except Exception as e:
        logger.error(f"生成图形验证码失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误", data={"error": "无法连接到缓存服务"})
        )


@router.post("/verification-codes")
async def send_verification_code(
    request: VerificationCodeRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    发送OTP验证码
    
    Args:
        request: 验证码发送请求
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        发送结果响应
    """
    logger.info(f"开始处理发送验证码请求: recipient={request.recipient}, scenario={request.scenario}")
    
    try:
        # 1. 图形验证码校验
        redis_client = get_redis_client()
        cache_key = f"captcha:solution:{request.captcha_id}"
        stored_solution = await redis_client.get(cache_key)
        
        if not stored_solution or stored_solution != request.captcha_solution.lower():
            logger.warning(f"图形验证码校验失败: captcha_id={request.captcha_id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4003, message="图形验证码错误或已过期")
            )
        
        # 删除已使用的验证码
        await redis_client.delete(cache_key)
        
        # 2. 频率限制检查
        client_ip = req.client.host
        rate_limit_key = f"rate_limit:verification_code:{client_ip}"
        request_count = await redis_client.get(rate_limit_key)
        
        if request_count and int(request_count) >= 5:  # 每小时最多5次
            logger.warning(f"IP请求频率超限: ip={client_ip}")
            return JSONResponse(
                status_code=429,
                content=error_response(code=4029, message="请求过于频繁", data={"error": "请在 60 秒后重试"})
            )
        
        # 3. 业务前置检查
        if request.scenario == "REGISTER":
            # 注册场景：检查用户是否已存在
            existing_user = await crud_user.get_by_email(db, request.recipient)
            if existing_user:
                logger.warning(f"注册验证码发送失败，用户已存在: email={request.recipient}")
                return JSONResponse(
                    status_code=409,
                    content=error_response(code=4009, message="该邮箱已被注册")
                )
        elif request.scenario == "RESET_PASSWORD":
            # 重置密码场景：检查用户是否存在
            existing_user = await crud_user.get_by_email(db, request.recipient)
            if not existing_user:
                logger.warning(f"重置密码验证码发送失败，用户不存在: email={request.recipient}")
                return JSONResponse(
                    status_code=404,
                    content=error_response(code=4004, message="用户不存在")
                )
        
        # 4. 生成和存储OTP
        otp_code = generate_otp()
        otp_key = f"otp:{request.scenario}:{request.recipient}"
        await redis_client.set(otp_key, otp_code, ex=300)  # 5分钟过期
        
        # 5. 更新频率限制计数
        await redis_client.incr(rate_limit_key)
        await redis_client.expire(rate_limit_key, 3600)  # 1小时过期
        
        # 6. 异步发送（模拟）
        logger.info(f"模拟发送验证码: code={otp_code}, recipient={request.recipient}")
        
        # 掩码处理收件人信息
        recipient_masked = mask_recipient(request.recipient)
        
        logger.info(f"成功处理验证码发送请求: recipient={recipient_masked}")
        
        return success_response(data={
            "message": "验证码已发送，请注意查收。",
            "recipient_masked": recipient_masked,
            "cooldown_seconds": 60
        })
        
    except Exception as e:
        logger.error(f"发送验证码失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/login")
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户登录
    
    Args:
        request: 登录请求
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        登录结果响应
    """
    logger.info(f"开始处理用户登录请求: username={request.username}")
    
    try:
        # 1. 图形验证码校验
        redis_client = get_redis_client()
        cache_key = f"captcha:solution:{request.captcha_id}"
        stored_solution = await redis_client.get(cache_key)
        
        if not stored_solution or stored_solution != request.captcha_solution.lower():
            logger.warning(f"登录时图形验证码校验失败: captcha_id={request.captcha_id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4003, message="图形验证码错误或已过期")
            )
        
        # 删除已使用的验证码
        await redis_client.delete(cache_key)
        
        # 2. 用户查询
        user = await crud_user.get_by_username(db, request.username)
        if not user:
            logger.warning(f"登录失败，用户不存在: username={request.username}")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3001, message="用户名或密码错误")
            )
        
        # 3. 状态和密码校验
        if user.status != EntityStatus.NORMAL:
            logger.warning(f"登录失败，用户状态异常: username={request.username}, status={user.status}")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3002, message="账户状态异常")
            )
        
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"登录失败，密码错误: username={request.username}")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3001, message="用户名或密码错误")
            )
        
        # 4. 生成Token
        tokens = generate_jwt_token(user.id)
        
        # 5. 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = req.client.host
        
        await db.commit()
        
        logger.info(f"用户登录成功: user_id={user.id}, username={user.username}")
        
        return success_response(data=tokens)
        
    except Exception as e:
        logger.error(f"用户登录失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


# ============================================================================
# 批次二新增API端点
# ============================================================================

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """
    刷新令牌
    
    Args:
        request: 刷新令牌请求
        
    Returns:
        新的访问令牌响应
    """
    logger.info("开始处理令牌刷新请求")
    
    try:
        # 验证refresh_token有效性
        payload = verify_token(request.refresh_token, token_type="refresh")
        if not payload:
            logger.warning("刷新令牌无效或已过期")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3003, message="凭证无效或已过期")
            )
        
        # 检查令牌是否在黑名单中
        if await is_token_blacklisted(request.refresh_token):
            logger.warning("刷新令牌已在黑名单中")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3003, message="凭证无效或已过期")
            )
        
        # 获取用户ID并生成新的access_token
        user_id = payload.get("user_id")
        new_access_token = create_access_token(user_id)
        
        logger.info(f"成功刷新令牌: user_id={user_id}")
        
        return success_response(data={
            "access_token": new_access_token,
            "token_type": "bearer"
        })
        
    except Exception as e:
        logger.error(f"令牌刷新失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    用户登出
    
    Args:
        authorization: Authorization header中的Token
        
    Returns:
        登出结果响应
    """
    logger.info("开始处理用户登出请求")
    
    try:
        # 解析Authorization头
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning("缺少或格式错误的Authorization头")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3004, message="认证凭证格式无效")
            )
        
        access_token = authorization[7:]  # 移除 "Bearer " 前缀
        
        # 验证access_token
        payload = verify_token(access_token, token_type="access")
        if not payload:
            logger.warning("访问令牌无效或已过期")
            return JSONResponse(
                status_code=401,
                content=error_response(code=3004, message="认证凭证格式无效")
            )
        
        # 将access_token加入黑名单
        await blacklist_token(access_token, expire_time=3600)
        
        user_id = payload.get("user_id")
        logger.info(f"用户成功登出: user_id={user_id}")
        
        return success_response(data=None)
        
    except Exception as e:
        logger.error(f"用户登出失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/password-reset-request")
async def password_reset_request(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    请求密码重置
    
    Args:
        request: 密码重置请求
        db: 数据库会话
        
    Returns:
        密码重置请求结果响应
    """
    logger.info(f"开始处理密码重置请求: email={request.email}")
    
    try:
        # 校验图形验证码
        redis_client = get_redis_client()
        cache_key = f"captcha:solution:{request.captcha_id}"
        stored_solution = await redis_client.get(cache_key)
        
        if not stored_solution or stored_solution != request.captcha_solution.lower():
            logger.warning(f"图形验证码校验失败: captcha_id={request.captcha_id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4003, message="图形验证码错误或已过期")
            )
        
        # 删除已使用的验证码
        await redis_client.delete(cache_key)
        
        # 检查用户是否存在
        user = await crud_user.get_by_email(db, request.email)
        
        # 为防止邮箱枚举，无论用户是否存在都返回成功响应
        if not user:
            logger.info(f"密码重置请求的邮箱不存在: email={request.email}")
        else:
            # 生成重置令牌
            reset_token = str(uuid.uuid4())
            reset_key = f"password_reset:{reset_token}"
            
            # 存储到Redis (15分钟过期)
            await redis_client.set(reset_key, str(user.id), ex=900)
            
            # 异步发送邮件（模拟）
            logger.info(f"模拟发送密码重置邮件: email={request.email}, reset_token={reset_token}")
        
        logger.info(f"成功处理密码重置请求: email={request.email}")
        
        return success_response(data={
            "message": "如果该邮箱已注册，一封密码重置邮件已发送至您的邮箱。"
        })
        
    except Exception as e:
        logger.error(f"密码重置请求失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/password-reset")
async def password_reset(
    request: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    执行密码重置
    
    Args:
        request: 密码重置确认请求
        db: 数据库会话
        
    Returns:
        密码重置结果响应
    """
    logger.info("开始处理密码重置执行请求")
    
    try:
        # 验证重置令牌
        redis_client = get_redis_client()
        reset_key = f"password_reset:{request.reset_token}"
        user_id_str = await redis_client.get(reset_key)
        
        if not user_id_str:
            logger.warning(f"重置令牌无效或已过期: reset_token={request.reset_token}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4005, message="无效的令牌", 
                                     data={"error": "密码重置链接无效或已过期"})
            )
        
        # 立即删除令牌防止重复使用
        await redis_client.delete(reset_key)
        
        # 验证新密码强度
        if not validate_password_strength(request.new_password):
            logger.warning("新密码不符合强度要求")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4006, message="新密码不符合强度要求")
            )
        
        # 获取用户并更新密码
        user_id = int(user_id_str)
        user = await crud_user.get(db, user_id)
        
        if not user:
            logger.warning(f"重置密码时用户不存在: user_id={user_id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4005, message="无效的令牌")
            )
        
        # 更新密码哈希
        user.password_hash = hash_password(request.new_password)
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"成功重置用户密码: user_id={user_id}")
        
        return success_response(message="密码重置成功", data=None)
        
    except Exception as e:
        logger.error(f"密码重置失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        ) 