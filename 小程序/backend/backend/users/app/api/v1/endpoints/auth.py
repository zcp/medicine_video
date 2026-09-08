"""
认证相关API端点 - 用户功能服务 (重构版)
仅负责FastAPI请求处理，所有业务逻辑委托给AuthService
"""
import logging
import base64
from typing import Optional

from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.services.auth_service import (
    AuthService,
    CaptchaErrorException,
    RateLimitException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException,
    InvalidResetTokenException,
    WeakPasswordException,
)
from app.schemas import (
    VerificationCodeRequest,
    VerifyCodeRequest,
    LoginRequest,
    PhoneLoginRequest,
    EmailLoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
)
from app.schemas.auth import SSOLoginRequest, OneTapLoginRequest, CloudFunctionLoginRequest, WeChatLoginRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _invalid_credentials_response(
    e: InvalidCredentialsException,
    *,
    default_message: str = "用户名或密码错误",
) -> JSONResponse:
    """统一映射登录凭证异常；条款未同意与账户状态异常均返回 3002。"""
    msg = str(e)
    if "同意服务条款" in msg:
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message=msg),
        )
    if "状态异常" in msg:
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message="账户状态异常"),
        )
    return JSONResponse(
        status_code=401,
        content=error_response(code=3001, message=default_message),
    )


# ============================================================================
# API 端点实现
# ============================================================================

@router.get("/captcha")
async def get_captcha(db: AsyncSession = Depends(get_async_db)):
    """
    获取图形验证码
    
    Returns:
        包含验证码ID和图片的响应
    """
    logger.info("开始处理获取图形验证码请求")
    
    try:
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 调用服务层方法
        captcha_data = await auth_service.generate_captcha()
        
        logger.info("成功处理获取图形验证码请求")
        return success_response(data=captcha_data)
        
    except Exception as e:
        logger.error(f"生成图形验证码失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误", data={"error": "无法连接到缓存服务"})
        )


@router.get("/captcha/image/{captcha_id}")
async def get_captcha_image(
    captcha_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Return the captcha image stored for a captcha id."""
    logger.info(f"开始处理获取图形验证码图片请求: captcha_id={captcha_id}")

    try:
        auth_service = AuthService(db)
        image_base64 = await auth_service.redis_client.get(f"captcha:image:{captcha_id}")

        if not image_base64:
            return JSONResponse(
                status_code=404,
                content=error_response(code=4004, message="图形验证码不存在或已过期")
            )

        if isinstance(image_base64, bytes):
            image_bytes = image_base64
        else:
            image_bytes = base64.b64decode(image_base64)

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Cache-Control": "no-store"}
        )

    except Exception as e:
        logger.error(f"获取图形验证码图片失败: captcha_id={captcha_id}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误")
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
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 获取客户端IP
        client_ip = req.client.host
        
        # 调用服务层方法
        result_data = await auth_service.send_otp_code(request, client_ip)
        
        logger.info("成功处理发送验证码请求")
        return success_response(data=result_data)
        
    except CaptchaErrorException as e:
        logger.warning(f"图形验证码校验失败: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4003, message="图形验证码错误或已过期")
        )
    except RateLimitException as e:
        logger.warning(f"请求频率超限: {e}")
        return JSONResponse(
            status_code=429,
            content=error_response(code=4029, message="请求过于频繁", data={"error": "请在 60 秒后重试"})
        )
    except UserAlreadyExistsException as e:
        logger.warning(f"用户已存在: {e}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=4009, message="该邮箱已被注册")
        )
    except RuntimeError as e:
        logger.error(f"短信/邮件发送失败: {e}")
        return JSONResponse(
            status_code=502,
            content=error_response(code=1003, message="短信/邮件服务发送失败，请稍后重试")
        )
    except Exception as e:
        logger.error(f"发送验证码失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="系统内部错误")
        )


@router.post("/verification-codes/verify")
async def verify_verification_code(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    校验 OTP 验证码并签发短期 ticket
    
    校验成功后返回一个 ticket，后续业务操作（重置密码、注册、绑定手机号）
    使用 ticket 而非原始 OTP，安全边界更清晰。
    
    Args:
        request: 验证码校验请求
        db: 数据库会话
        
    Returns:
        包含 ticket 和过期时间的响应
    """
    logger.info(f"开始处理验证码校验请求: recipient={request.recipient}, scenario={request.scenario}")
    
    try:
        auth_service = AuthService(db)
        result = await auth_service.verify_otp_and_issue_ticket(request)
        
        logger.info("成功校验验证码并签发 ticket")
        return success_response(data=result)
        
    except InvalidTokenException as e:
        logger.warning(f"验证码无效: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except InvalidCredentialsException as e:
        logger.warning(f"验证码错误: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4005, message=str(e))
        )
    except RateLimitException as e:
        logger.warning(f"验证码尝试次数超限: {e}")
        return JSONResponse(
            status_code=429,
            content=error_response(code=4029, message=str(e))
        )
    except Exception as e:
        logger.error(f"验证码校验失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="系统内部错误")
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
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 获取客户端IP
        client_ip = req.client.host
        
        # 调用服务层方法
        tokens = await auth_service.login_user(request, client_ip)
        
        logger.info("成功处理用户登录请求")
        return success_response(data=tokens)
        
    except CaptchaErrorException as e:
        logger.warning(f"图形验证码校验失败: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4003, message="图形验证码错误或已过期")
        )
    except RateLimitException as e:
        logger.warning(f"登录频率超限: {e}")
        return JSONResponse(
            status_code=429,
            content=error_response(code=4029, message="登录尝试过于频繁，请稍后重试")
        )
    except InvalidCredentialsException as e:
        logger.warning(f"登录凭证无效: {e}")
        return _invalid_credentials_response(e, default_message="用户名或密码错误")
    except Exception as e:
        logger.error(f"用户登录失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/login/phone")
async def login_by_phone(
    request: PhoneLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """手机号验证码登录：消费 LOGIN ticket 并签发 JWT。"""
    logger.info("开始处理手机号验证码登录请求")

    try:
        auth_service = AuthService(db)
        tokens = await auth_service.login_by_phone_ticket(request)

        logger.info("成功处理手机号验证码登录请求")
        return success_response(data=tokens)

    except InvalidTokenException as e:
        logger.warning(f"手机号验证码登录 ticket 无效: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except InvalidCredentialsException as e:
        logger.warning(f"手机号验证码登录凭证无效: {e}")
        return _invalid_credentials_response(e, default_message="登录凭证无效")
    except Exception as e:
        logger.error(f"手机号验证码登录失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/login/email")
async def login_by_email(
    request: EmailLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """邮箱验证码登录（V5）：消费 LOGIN ticket（channel=EMAIL）并签发 JWT。"""
    logger.info("开始处理邮箱验证码登录请求")

    try:
        auth_service = AuthService(db)
        tokens = await auth_service.login_by_email_ticket(request)

        logger.info("成功处理邮箱验证码登录请求")
        return success_response(data=tokens)

    except InvalidTokenException as e:
        logger.warning(f"邮箱验证码登录 ticket 无效: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except InvalidCredentialsException as e:
        logger.warning(f"邮箱验证码登录凭证无效: {e}")
        return _invalid_credentials_response(e, default_message="登录凭证无效")
    except Exception as e:
        logger.error(f"邮箱验证码登录失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    刷新令牌
    
    Args:
        request: 刷新令牌请求
        db: 数据库会话
        
    Returns:
        新的访问令牌响应
    """
    logger.info("开始处理令牌刷新请求")
    
    try:
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 调用服务层方法
        token_data = await auth_service.refresh_access_token(request.refresh_token)
        
        logger.info("成功处理令牌刷新请求")
        return success_response(data=token_data)
        
    except InvalidTokenException as e:
        logger.warning(f"令牌无效: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3003, message="凭证无效或已过期")
        )
    except Exception as e:
        logger.error(f"令牌刷新失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户登出
    
    Args:
        authorization: Authorization header中的Token
        db: 数据库会话
        
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
        
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 调用服务层方法
        await auth_service.logout_user(access_token)
        
        logger.info("成功处理用户登出请求")
        return success_response(data=None)
        
    except InvalidTokenException as e:
        logger.warning(f"令牌无效: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3004, message="认证凭证格式无效")
        )
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
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 调用服务层方法
        await auth_service.request_password_reset(request)
        
        logger.info("成功处理密码重置请求")
        return success_response(data={
            "message": "如果该邮箱已注册，一封密码重置邮件已发送至您的邮箱。"
        })
        
    except CaptchaErrorException as e:
        logger.warning(f"图形验证码校验失败: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4003, message="图形验证码错误或已过期")
        )
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
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 调用服务层方法
        await auth_service.perform_password_reset(request)
        
        logger.info("成功处理密码重置执行请求")
        return success_response(message="密码重置成功", data=None)
        
    except InvalidResetTokenException as e:
        logger.warning(f"重置令牌无效: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4005, message="无效的令牌", 
                                 data={"error": "密码重置链接无效或已过期"})
        )
    except WeakPasswordException as e:
        logger.warning(f"密码强度不足: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4006, message="新密码不符合强度要求")
        )
    except Exception as e:
        logger.error(f"密码重置失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/sso-login")
async def sso_login(
    request: SSOLoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authing SSO 登录
    
    Args:
        request: SSO登录请求
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        SSO登录结果响应
    """
    logger.info("开始处理 SSO 登录请求")
    
    try:
        # 实例化AuthService
        auth_service = AuthService(db)
        
        # 获取客户端IP
        client_ip = req.client.host
        
        # 调用服务层方法
        tokens = await auth_service.sso_login(db, id_token=request.id_token, client_ip=client_ip)
        
        logger.info("成功处理 SSO 登录请求")
        return success_response(message="SSO登录成功", data=tokens)
        #return tokens  # 直接返回 tokens 字典以匹配 response_model
        
    except InvalidTokenException as e:
        logger.warning(f"Authing Token 无效: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3005, message='认证凭证无效')
        )
    except InvalidCredentialsException as e:
        logger.warning(f"SSO登录凭证无效: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3004, message=str(e))
        )
    except Exception as e:
        logger.error(f"SSO登录失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='服务器内部错误')
        )


@router.post("/one-tap-login")
async def one_tap_login(
    request: OneTapLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    一键登录（Phase 4）

    App 端通过运营商 SDK 获取 carrier_token，后端用 token 换取手机号，
    查找或自动创建用户，签发 JWT。

    Mock 模式（开发）：carrier_token = "mock:+8613800138000"
    生产模式：carrier_token 为运营商 SDK 返回的真实 token
    """
    logger.info(f"开始处理一键登录请求")

    try:
        auth_service = AuthService(db)
        result = await auth_service.one_tap_login(request)

        logger.info(f"一键登录成功: is_new_user={result['is_new_user']}")
        return success_response(data=result)

    except InvalidTokenException as e:
        logger.warning(f"一键登录取号失败: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except InvalidCredentialsException as e:
        logger.warning(f"一键登录用户状态异常: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message=str(e))
        )
    except Exception as e:
        import traceback
        logger.error(f"一键登录失败: error={e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="系统内部错误")
        )


@router.post("/one-tap-login/cloud-function")
async def one_tap_login_cloud_function(
    request: CloudFunctionLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    云函数签名一键登录（Phase 4 安全方案B — HMAC签名验证）

    客户端从 DCloud 云函数拿到 {phone, sign, timestamp} 后提交，
    后端通过 HMAC 验签确保手机号来自云函数、未经客户端篡改。
    """
    logger.info("开始处理云函数签名一键登录请求")

    try:
        auth_service = AuthService(db)
        result = await auth_service.one_tap_login_direct(
            phone=request.phone,
            sign=request.sign,
            timestamp=request.timestamp,
            agreed_to_terms=request.agreed_to_terms,
        )

        logger.info(f"云函数一键登录成功: is_new_user={result['is_new_user']}")
        return success_response(data=result)

    except InvalidTokenException as e:
        logger.warning(f"云函数一键登录认证失败: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except InvalidCredentialsException as e:
        logger.warning(f"云函数一键登录用户状态异常: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message=str(e))
        )
    except Exception as e:
        import traceback
        logger.error(f"云函数一键登录失败: error={e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="系统内部错误")
        )


@router.post("/wechat-login")
async def wechat_login(
    request: WeChatLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    微信小程序一键授权登录（V4）

    小程序 wx.login 获取 code，后端换 openid，查找或自动创建用户，签发 JWT。

    Mock 模式（开发）：code = "mock:oxMOCK_OPENID_001"
    正式模式：code 为 wx.login 返回的真实 code
    """
    logger.info("开始处理微信一键授权登录请求")

    try:
        auth_service = AuthService(db)
        result = await auth_service.wechat_login(request)

        logger.info(f"微信登录成功: is_new_user={result['is_new_user']}")
        return success_response(data=result)

    except InvalidTokenException as e:
        logger.warning(f"微信登录换号失败: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except InvalidCredentialsException as e:
        logger.warning(f"微信登录业务拒绝: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message=str(e))
        )
    except Exception as e:
        import traceback
        logger.error(f"微信登录失败: error={e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="系统内部错误")
        )
 
