"""
用户注册API端点 - 用户功能服务
实现用户注册功能（重构后：业务逻辑已迁移到服务层）
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.schemas.users import UserResponse, UserUpdateSelf, PhoneBindRequest
from app.models.users import User
from app.api.v1.deps import get_current_user
from app.services.user_service import (
    UserService,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    ValidationError,
    CaptchaErrorException,
    NoUpdateDataProvidedError,
    ActiveSubscriptionError,
    InvalidPasswordError,
    WeakPasswordError
)
from app.content_safety.exceptions import ContentSafetyBlockedException, ContentSafetyServiceException
from app.services.avatar_upload_service import AvatarUploadService, AvatarUploadError
from app.services.auth_service import (
    AuthService,
    InvalidTokenException as AuthInvalidTokenException,
    WeakPasswordException as AuthWeakPasswordException,
    InvalidCredentialsException as AuthInvalidCredentialsException,
)
from app.schemas.auth import PhoneRegisterRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================================
# Pydantic 模型定义
# ============================================================================


class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., max_length=255, description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    nickname: str = Field(..., min_length=1, max_length=50, description="昵称")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    current_password: Optional[str] = Field(None, description="当前密码（无密码用户可为空）")
    new_password: str = Field(..., min_length=8, description="新密码")


class DeactivateAccountRequest(BaseModel):
    """注销账号请求模型"""
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")


# ============================================================================
# API 端点实现
# ============================================================================

@router.post("/register")
async def register(
    request: UserRegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户注册
    
    Args:
        request: 注册请求
        req: FastAPI请求对象  
        db: 数据库会话
        
    Returns:
        注册结果响应
    """
    # 主动变量提取
    username_for_logging = request.username
    email_for_logging = request.email
    
    logger.info(f"开始处理用户注册请求: username={username_for_logging}, email={email_for_logging}")
    
    try:
        # 实例化服务
        user_service = UserService(db)
        
        # 调用服务层方法
        new_user = await user_service.register_user(request)
        
        # 序列化用户数据
        user_response = UserResponse.model_validate(new_user)
        
        # 构建响应数据（只返回安全的用户信息）
        response_data = {
            "public_id": str(user_response.public_id),
            "username": user_response.username,
            "nickname": user_response.nickname,
            "email": user_response.email,
            "created_at": user_response.created_at.isoformat() + "Z"
        }
        
        logger.info(f"用户注册成功: username={username_for_logging}")
        
        return success_response(data=response_data, message="注册成功")
        
    except AuthInvalidCredentialsException as e:
        logger.warning(f"注册未同意服务条款: username={username_for_logging}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message=str(e))
        )
    except UsernameAlreadyExistsError as e:
        logger.warning(f"用户名已存在: username={username_for_logging}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=4009, message=str(e))
        )
    except EmailAlreadyExistsError as e:
        logger.warning(f"邮箱已存在: email={email_for_logging}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=4009, message=str(e))
        )
    except ValidationError as e:
        logger.warning(f"参数验证失败: {e.field}={getattr(request, e.field, 'N/A')}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=e.message)
        )
    except CaptchaErrorException as e:
        logger.warning(f"验证码错误: username={username_for_logging}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4003, message=str(e))
        )
    except Exception as e:
        logger.error(f"用户注册失败: username={username_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误", data={"error": "数据库操作失败"})
        )


@router.post("/register/phone")
async def register_by_phone(
    request: PhoneRegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    手机号注册（Phase 3：基于 register_ticket）

    流程：发验证码 → 验 OTP 换 register_ticket → 调用此接口注册
    此接口不接收明文 OTP，只信任后端签发的 ticket。
    """
    logger.info("开始处理手机号注册请求")

    try:
        auth_service = AuthService(db)
        result = await auth_service.register_by_phone_ticket(request)

        response_data = {
            "public_id": result.get("user_public_id", ""),
            "username": result.get("username", ""),
            "nickname": result.get("nickname", ""),
            "phone_number": result.get("phone_masked", ""),
            "is_phone_verified": True,
            "is_new_user": result["is_new_user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
        }

        logger.info(f"手机号注册成功: public_id={response_data['public_id']}")
        return success_response(data=response_data, message="注册成功")

    except AuthInvalidTokenException as e:
        logger.warning(f"ticket 无效: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4004, message=str(e))
        )
    except AuthInvalidCredentialsException as e:
        logger.warning(f"手机号注册未同意服务条款: {e}")
        return JSONResponse(
            status_code=401,
            content=error_response(code=3002, message=str(e))
        )
    except AuthWeakPasswordException as e:
        logger.warning(f"密码强度不足: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4002, message=str(e))
        )
    except Exception as e:
        logger.error(f"手机号注册失败: error={e}")
        if "已被注册" in str(e):
            return JSONResponse(
                status_code=409,
                content=error_response(code=4009, message=str(e))
            )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误")
        )


# ============================================================================
# 用户自我管理端点
# ============================================================================

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前已认证的用户
        
    Returns:
        用户信息响应
    """
    # 主动变量提取
    user_id_for_logging = current_user.id
    
    logger.info(f"开始处理获取用户信息请求: user_id={user_id_for_logging}")
    
    try:
        # 序列化用户数据
        user_data = UserResponse.model_validate(current_user)
        
        # 转换为字典并调整字段名
        response_data = user_data.model_dump()
        response_data["uuid"] = str(response_data.pop("public_id"))  # 重命名字段
        response_data.pop("id", None)  # 移除内部ID
        
        logger.info(f"成功获取用户信息: user_id={user_id_for_logging}")
        
        return success_response(data=response_data)
        
    except Exception as e:
        logger.error(f"获取用户信息失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/me/avatar")
async def upload_current_user_avatar(
    file: UploadFile = File(..., description="头像文件（JPG/PNG/WEBP，微信小程序 wx.uploadFile）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    上传用户头像（multipart 字段 file）。

    - 替代 PATCH /me 的 avatar_url 字段；PATCH 传 avatar_url 将被拒绝。
    - 文件落盘至 uploads/avatars/，并更新 users.avatar_url。
    - V1.0 图片审核为占位（IMAGE_MODERATION_PROVIDER=placeholder），不检测、始终放行。
    - 生产切换 WECHAT/ALIYUN/TENCENT 后，落盘前走第三方图片审核 API。
    """
    user_id_for_logging = current_user.id
    try:
        service = AvatarUploadService(db)
        avatar_url = await service.upload_avatar(current_user, file)
        await db.commit()
        return success_response(data={"avatar_url": avatar_url})
    except AvatarUploadError as e:
        return JSONResponse(status_code=400, content=error_response(code=e.code, message=e.message))
    except ContentSafetyBlockedException as e:
        await db.rollback()
        return JSONResponse(status_code=422, content=error_response(code=e.code, message=e.message))
    except ContentSafetyServiceException as e:
        await db.rollback()
        return JSONResponse(status_code=422, content=error_response(code=e.code, message=e.message))
    except Exception as e:
        await db.rollback()
        logger.error(f"头像上传失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库查询错误"))


@router.patch("/me")
async def update_current_user_info(
    request: UserUpdateSelf,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新当前用户信息
    
    Args:
        request: 用户更新请求
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        更新后的用户信息
    """
    # 主动变量提取
    user_id_for_logging = current_user.id
    
    logger.info(f"开始处理更新用户信息请求: user_id={user_id_for_logging}")
    
    try:
        # 实例化服务
        user_service = UserService(db)
        
        # 调用服务层方法
        updated_user = await user_service.update_profile(
            user_to_update=current_user, 
            update_request=request
        )
        
        # 序列化响应数据
        user_data = UserResponse.model_validate(updated_user)
        response_data = user_data.model_dump()
        response_data["uuid"] = str(response_data.pop("public_id"))  # 重命名字段
        response_data.pop("id", None)  # 移除内部ID
        
        logger.info(f"成功更新用户信息: user_id={user_id_for_logging}")
        
        return success_response(data=response_data)
        
    except NoUpdateDataProvidedError as e:
        logger.warning(f"更新用户信息失败，无有效更新数据: user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except ValidationError as e:
        logger.warning(f"更新用户信息参数验证失败: user_id={user_id_for_logging}, field={e.field}")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4001, 
                message="参数校验失败",
                data={"field": e.field, "error": e.message}
            )
        )
    except ContentSafetyBlockedException as e:
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message)
        )
    except ContentSafetyServiceException as e:
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message)
        )
    except Exception as e:
        logger.error(f"更新用户信息失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.delete("/me")
async def delete_current_user_account(
    request: DeactivateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    注销当前用户账户（软删除）
    
    Args:
        request: 注销请求（含图形验证码）
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        注销结果响应
    """
    # 主动变量提取
    user_id_for_logging = current_user.id
    
    logger.info(f"开始处理用户账户注销请求: user_id={user_id_for_logging}")
    
    try:
        # 实例化服务
        user_service = UserService(db)
        
        # 调用服务层方法
        await user_service.deactivate_account(
            user=current_user,
            captcha_id=request.captcha_id,
            captcha_solution=request.captcha_solution,
        )
        
        logger.info(f"用户账户注销成功: user_id={user_id_for_logging}")
        
        return success_response(data=None, message="账号已注销")
        
    except CaptchaErrorException as e:
        logger.warning(f"注销时图形验证码校验失败: user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4003, message=str(e))
        )
    except ActiveSubscriptionError as e:
        logger.warning(f"用户存在活跃订阅，无法注销: user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=2002, message=str(e))
        )
    except Exception as e:
        logger.error(f"用户账户注销失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/me/password")
async def change_current_user_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    修改当前用户密码
    
    Args:
        request: 密码修改请求
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        密码修改结果
    """
    # 主动变量提取
    user_id_for_logging = current_user.id
    
    logger.info(f"开始处理用户密码修改请求: user_id={user_id_for_logging}")
    
    try:
        # 实例化服务
        user_service = UserService(db)
        
        # 调用服务层方法
        await user_service.change_password(user=current_user, password_request=request)
        
        logger.info(f"用户密码修改成功: user_id={user_id_for_logging}")
        
        return success_response(data=None, message="密码修改成功")
        
    except InvalidPasswordError as e:
        logger.warning(f"密码修改失败，当前密码错误: user_id={user_id_for_logging}")
        detail = str(e).strip() or "当前密码错误"
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4004,
                message=detail,
                data={"error": detail}
            )
        )
    except WeakPasswordError as e:
        logger.warning(f"新密码强度不足: user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except ValidationError as e:
        logger.warning(f"密码修改验证失败: user_id={user_id_for_logging}, error={e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=e.message)
        )
    except Exception as e:
        logger.error(f"密码修改失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.post("/me/phone")
async def bind_phone_number(
    request: PhoneBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    绑定手机号
    
    Args:
        request: 手机号绑定请求
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        手机号绑定结果
    """
    # 安全日志准备
    user_id_for_logging = current_user.id
    
    logger.info(f"开始处理手机号绑定请求: user_id={user_id_for_logging}, phone_number={request.phone_number}")
    
    try:
        # 实例化服务
        user_service = UserService(db)
        
        # 调用业务逻辑
        await user_service.bind_phone_number(
            db,
            current_user=current_user,
            phone_number=request.phone_number,
            bind_ticket=request.bind_ticket
        )
        
        # 成功处理
        logger.info(f"手机号绑定成功: user_id={user_id_for_logging}")
        
        return success_response(data=None, message="手机号绑定成功")
        
    except ValidationError as e:
        logger.warning(f"手机号绑定验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4006, message=str(e))
        )
    except Exception as e:
        logger.error(f"手机号绑定失败: user_id={user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='服务器内部错误')
        ) 