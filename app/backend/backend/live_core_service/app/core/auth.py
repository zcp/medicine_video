import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class JWTAuth:
    @staticmethod
    def _get_jwt_config():
        """延迟获取JWT配置，避免模块导入时的问题"""
        from app.core.config import settings
        return settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM, settings.JWT_LEEWAY_SECONDS

    @staticmethod
    def verify_token(token: str) -> Dict:
        """验证JWT Token"""
        try:
            # 延迟获取配置
            JWT_SECRET_KEY, JWT_ALGORITHM, JWT_LEEWAY = JWTAuth._get_jwt_config()

            if not JWT_SECRET_KEY:
                logger.error("JWT_SECRET_KEY 环境变量未配置")
                raise HTTPException(status_code=500, detail="JWT配置错误")

            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                leeway=JWT_LEEWAY,
            )

            # 验证必要字段
            if "user_id" not in payload:
                logger.warning("JWT Token中缺少user_id字段")
                raise HTTPException(status_code=401, detail="认证凭证无效")

            # 仅接受 access token：refresh token（type=refresh，有效期 7 天）不得用于
            # 访问业务/管理 API（与 users 侧 deps.verify_token 校验对齐，防跨服务冒充）
            if payload.get("type") != "access":
                logger.warning(f"JWT Token类型错误，拒绝访问: type={payload.get('type')}")
                raise HTTPException(status_code=401, detail="认证凭证无效")

            logger.info(f"JWT Token验证成功: user_id={payload.get('user_id')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT Token已过期")
            raise HTTPException(status_code=401, detail="认证凭证已过期")
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT Token无效: {str(e)}")
            raise HTTPException(status_code=401, detail="认证凭证无效")
        except Exception as e:
            logger.error(f"JWT Token验证失败: {str(e)}")
            raise HTTPException(status_code=401, detail="认证失败")

    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
        """获取当前认证用户信息"""
        if not credentials:
            logger.warning("请求中缺少认证凭证")
            raise HTTPException(status_code=401, detail="认证凭证缺失")

        if not credentials.credentials:
            logger.warning("认证凭证为空")
            raise HTTPException(status_code=401, detail="认证凭证缺失")

        return JWTAuth.verify_token(credentials.credentials)