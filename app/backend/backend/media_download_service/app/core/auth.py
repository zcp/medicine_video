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
        secret_key = os.getenv("JWT_SECRET_KEY", "my-key")
        algorithm =  os.getenv("JWT_ALGORITHM", "HS256")
        print("xxxx",secret_key, algorithm)
        return secret_key, algorithm

    @staticmethod
    def verify_token(token: str) -> Dict:
        """验证JWT Token"""
        try:
            # 延迟获取配置
            JWT_SECRET_KEY, JWT_ALGORITHM = JWTAuth._get_jwt_config()

            if not JWT_SECRET_KEY:
                logger.error("JWT_SECRET_KEY 环境变量未配置")
                raise HTTPException(status_code=500, detail="JWT配置错误")

            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )

            # 验证必要字段
            if "user_id" not in payload:
                logger.warning("JWT Token中缺少user_id字段")
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