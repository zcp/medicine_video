"""
用户注册API端点 - 用户功能服务
实现用户注册功能
"""
import hashlib
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from app.database import get_async_db
from app.core.redis_client import get_redis_client
from app.core.responses import success_response, error_response
from app.crud import crud_user
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.models.users import User
from app.api.v1.deps import get_current_user

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


# 批次二新增模型
class UserUpdateSelf(BaseModel):
    """用户自我更新模型 - 仅包含用户可修改的字段"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码")


# ============================================================================
# 工具函数
# ============================================================================

def hash_password(password: str) -> str:
    """密码哈希处理（生产环境应使用bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    return len(password) >= 6


async def blacklist_user_tokens(user_id: int):
    """将用户的所有令牌加入黑名单（模拟实现）"""
    try:
        redis_client = get_redis_client()
        # 在实际实现中，这里需要查找用户的所有活跃令牌并加入黑名单
        # 目前是模拟实现
        key = f"user_tokens_blacklisted:{user_id}"
        await redis_client.set(key, "1", ex=3600 * 24 * 7)  # 7天过期
        logger.info(f"已将用户令牌加入黑名单: user_id={user_id}")
    except Exception as e:
        logger.error(f"加入令牌黑名单失败: user_id={user_id}, error={e}")


def validate_username(username: str) -> bool:
    """验证用户名格式"""
    # 简单验证：字母、数字、下划线，长度3-50
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return username.replace('_', '').isalnum()


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    # 简单验证：包含@和.
    if not email or '@' not in email or '.' not in email:
        return False
    return True


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
    logger.info(f"开始处理用户注册请求: username={request.username}, email={request.email}")
    
    try:
        # 1. 参数格式验证
        if not validate_username(request.username):
            logger.warning(f"用户名格式无效: username={request.username}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="用户名格式无效，应为3-50位字母数字下划线组合")
            )
        
        if not validate_email(request.email):
            logger.warning(f"邮箱格式无效: email={request.email}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="邮箱格式无效")
            )
        
        if len(request.password) < 6:
            logger.warning(f"密码长度不足: username={request.username}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="密码长度至少6位")
            )
        
        # 2. 图形验证码校验
        redis_client = get_redis_client()
        cache_key = f"captcha:solution:{request.captcha_id}"
        stored_solution = await redis_client.get(cache_key)
        
        if not stored_solution or stored_solution != request.captcha_solution.lower():
            logger.warning(f"注册时图形验证码校验失败: captcha_id={request.captcha_id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4003, message="图形验证码错误或已过期")
            )
        
        # 删除已使用的验证码
        await redis_client.delete(cache_key)
        
        # 3. 唯一性检查
        existing_user_by_username = await crud_user.get_by_username(db, request.username)
        if existing_user_by_username:
            logger.warning(f"用户名已存在: username={request.username}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=4009, message="用户名已被占用")
            )
        
        existing_user_by_email = await crud_user.get_by_email(db, request.email)
        if existing_user_by_email:
            logger.warning(f"邮箱已存在: email={request.email}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=4009, message="邮箱已被注册")
            )
        
        # 4. 密码哈希处理
        password_hash = hash_password(request.password)
        
        # 5. 构建UserCreate对象
        user_create = UserCreate(
            username=request.username,
            email=request.email,
            nickname=request.nickname,
            phone_number=None,  # 第一阶段不处理手机号
            social_provider=None,
            social_id=None
        )
        
        # 6. 创建用户
        new_user = await crud_user.create(db, user_create, password_hash)
        
        # 7. 构建响应数据
        user_response = UserResponse.model_validate(new_user)
        
        # 8. 构建成功响应（只返回安全的用户信息）
        response_data = {
            "public_id": str(user_response.public_id),
            "username": user_response.username,
            "nickname": user_response.nickname,
            "email": user_response.email,
            "created_at": user_response.created_at.isoformat() + "Z"
        }
        
        logger.info(f"用户注册成功: user_id={new_user.id}, username={new_user.username}")
        
        return success_response(data=response_data, message="注册成功")
        
    except IntegrityError as e:
        logger.warning(f"数据库唯一性约束冲突: username={request.username}, email={request.email}, error={e}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=4009, message="用户名或邮箱已存在")
        )
    except Exception as e:
        logger.error(f"用户注册失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1001, message="系统内部错误", data={"error": "数据库操作失败"})
        )


# ============================================================================
# 批次二新增端点 - 用户自我管理
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
    logger.info(f"开始处理获取用户信息请求: user_id={current_user.id}")
    
    try:
        # 序列化用户数据
        user_data = UserResponse.model_validate(current_user)
        
        # 转换为字典并调整字段名
        response_data = user_data.model_dump()
        response_data["uuid"] = str(response_data.pop("public_id"))  # 重命名字段
        response_data.pop("id", None)  # 移除内部ID
        
        logger.info(f"成功获取用户信息: user_id={current_user.id}")
        
        return success_response(data=response_data)
        
    except Exception as e:
        logger.error(f"获取用户信息失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


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
    logger.info(f"开始处理更新用户信息请求: user_id={current_user.id}")
    
    try:
        # 验证更新数据
        update_data = request.model_dump(exclude_unset=True)
        
        if not update_data:
            logger.warning(f"更新用户信息失败，无有效更新数据: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="没有提供有效的更新数据")
            )
        
        # 验证昵称长度
        if "nickname" in update_data and len(update_data["nickname"]) > 50:
            logger.warning(f"昵称过长: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="参数校验失败",
                                     data={"field": "nickname", "error": "昵称长度不能超过50个字符"})
            )
        
        # 更新用户信息
        updated_user = await crud_user.update(db, current_user, update_data)
        
        # 序列化响应数据
        user_data = UserResponse.model_validate(updated_user)
        response_data = user_data.model_dump()
        response_data["uuid"] = str(response_data.pop("public_id"))  # 重命名字段
        response_data.pop("id", None)  # 移除内部ID
        
        logger.info(f"成功更新用户信息: user_id={updated_user.id}")
        
        return success_response(data=response_data)
        
    except Exception as e:
        logger.error(f"更新用户信息失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        )


@router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    注销当前用户账户（软删除）
    
    Args:
        current_user: 当前已认证的用户
        db: 数据库会话
        
    Returns:
        注销结果响应
    """
    logger.info(f"开始处理用户账户注销请求: user_id={current_user.id}")
    
    try:
        # 业务检查：检查用户是否有进行中的业务
        # 这里可以检查会员状态、订单状态等
        # 目前暂时跳过这些检查，直接进行软删除
        
        # 执行软删除
        deleted_user = await crud_user.remove(db, current_user.id)
        
        # 将用户令牌加入黑名单
        await blacklist_user_tokens(current_user.id)
        
        logger.info(f"用户账户注销成功: user_id={deleted_user.id}")
        
        return success_response(data=None)
        
    except Exception as e:
        logger.error(f"用户账户注销失败: error={e}")
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
    logger.info(f"开始处理用户密码修改请求: user_id={current_user.id}")
    
    try:
        # 验证当前密码
        if not verify_password(request.current_password, current_user.password_hash):
            logger.warning(f"密码修改失败，当前密码错误: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4004, message="参数校验失败",
                                     data={"error": "当前密码不正确"})
            )
        
        # 验证新密码强度
        if not validate_password_strength(request.new_password):
            logger.warning(f"新密码强度不足: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="新密码长度至少6位")
            )
        
        # 检查新密码是否与当前密码相同
        if verify_password(request.new_password, current_user.password_hash):
            logger.warning(f"新密码与当前密码相同: user_id={current_user.id}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="新密码不能与当前密码相同")
            )
        
        # 更新密码
        new_password_hash = hash_password(request.new_password)
        await crud_user.update(db, current_user, {"password_hash": new_password_hash})
        
        # 使所有旧令牌失效
        await blacklist_user_tokens(current_user.id)
        
        logger.info(f"用户密码修改成功: user_id={current_user.id}")
        
        return success_response(data=None, message="密码修改成功")
        
    except Exception as e:
        logger.error(f"密码修改失败: error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库查询错误")
        ) 