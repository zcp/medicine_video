"""
Token加密工具模块

使用Fernet对称加密保护敏感Token
"""
import logging
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenEncryption:
    """Token加密工具类（使用Fernet对称加密）"""
    
    def __init__(self):
        """
        初始化加密器
        
        Raises:
            ValueError: 加密密钥未设置或格式错误
        """
        if not settings.TOKEN_ENCRYPTION_KEY:
            raise ValueError("TOKEN_ENCRYPTION_KEY环境变量未设置")
        
        try:
            self.cipher = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
        except Exception as e:
            raise ValueError(f"加密密钥格式错误: {str(e)}")
    
    def encrypt(self, token: str) -> str:
        """
        加密token
        
        Args:
            token: 原始token字符串
        
        Returns:
            str: Base64编码的加密字符串
        
        Raises:
            ValueError: token为空或加密失败
        """
        if not token:
            raise ValueError("token不能为空")
        
        try:
            encrypted = self.cipher.encrypt(token.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Token加密失败: {str(e)}")
            raise ValueError(f"加密失败: {str(e)}")
    
    def decrypt(self, encrypted_token: str) -> str:
        """
        解密token
        
        Args:
            encrypted_token: 加密后的token字符串
        
        Returns:
            str: 原始token字符串
        
        Raises:
            ValueError: encrypted_token为空
            InvalidToken: token无效或已损坏
        """
        if not encrypted_token:
            raise ValueError("encrypted_token不能为空")
        
        try:
            decrypted = self.cipher.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Token解密失败：Token无效或已损坏")
            raise InvalidToken("Token无效或已损坏")
        except Exception as e:
            logger.error(f"Token解密失败: {str(e)}")
            raise ValueError(f"解密失败: {str(e)}")


# 单例模式
_encryption_instance = None


def get_token_encryption() -> TokenEncryption:
    """
    获取Token加密器实例（单例模式）
    
    Returns:
        TokenEncryption: 加密器实例
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = TokenEncryption()
    return _encryption_instance

