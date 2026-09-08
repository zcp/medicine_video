"""
Token加密工具测试

测试 app/core/encryption.py 中的TokenEncryption类
"""
import pytest
from cryptography.fernet import Fernet, InvalidToken
from unittest.mock import patch
from app.core.encryption import TokenEncryption, get_token_encryption


class TestTokenEncryption:
    """Token加密工具测试类"""
    
    @pytest.fixture
    def test_encryption_key(self):
        """测试用加密密钥"""
        return Fernet.generate_key().decode()
    
    @pytest.fixture
    def token_encryption(self, test_encryption_key):
        """创建TokenEncryption实例"""
        with patch('app.core.encryption.settings.TOKEN_ENCRYPTION_KEY', test_encryption_key):
            return TokenEncryption()
    
    def test_generate_key(self):
        """
        测试用例1: 测试密钥生成
        
        验证点:
        - 生成的密钥不为空
        - 生成的密钥是bytes类型
        - 密钥可用于创建Fernet实例
        """
        key = Fernet.generate_key()
        
        assert key is not None, "生成的密钥不应为空"
        assert isinstance(key, bytes), "密钥应该是bytes类型"
        
        # 验证密钥可用于创建Fernet实例
        cipher = Fernet(key)
        assert cipher is not None, "密钥应该可以创建Fernet实例"
    
    def test_encrypt_decrypt_success(self, token_encryption):
        """
        测试用例2: 测试加密解密成功流程
        
        准备:
        - 准备测试token字符串
        
        执行:
        - 使用TokenEncryption加密token
        - 使用TokenEncryption解密token
        
        验证点:
        - 加密后的token不等于原始token
        - 解密后的token等于原始token
        - 加密token是字符串
        """
        original_token = "test_token_123456"
        
        # 加密
        encrypted = token_encryption.encrypt(original_token)
        
        # 验证加密后的格式
        assert isinstance(encrypted, str), "加密后应返回字符串"
        assert encrypted != original_token, "加密后的token应与原始token不同"
        
        # 解密
        decrypted = token_encryption.decrypt(encrypted)
        
        # 验证解密成功
        assert decrypted == original_token, "解密后应恢复原始token"
    
    def test_encrypt_empty_token(self, token_encryption):
        """
        测试用例3: 测试加密空token
        
        执行:
        - 尝试加密空字符串
        
        验证点:
        - 抛出ValueError异常
        - 异常消息包含"token不能为空"
        """
        with pytest.raises(ValueError, match="token不能为空"):
            token_encryption.encrypt("")
    
    def test_decrypt_invalid_token(self, token_encryption):
        """
        测试用例4: 测试解密无效token
        
        执行:
        - 尝试解密不是有效Fernet格式的字符串
        
        验证点:
        - 抛出InvalidToken异常
        """
        with pytest.raises(InvalidToken):
            token_encryption.decrypt("invalid_token_format")
    
    def test_decrypt_with_wrong_key(self, test_encryption_key):
        """
        测试用例5: 测试使用错误密钥解密
        
        准备:
        - 使用密钥A加密token
        - 创建新的密钥B
        
        执行:
        - 使用密钥B尝试解密
        
        验证点:
        - 抛出InvalidToken异常
        """
        # 使用密钥A加密
        with patch('app.core.encryption.settings.TOKEN_ENCRYPTION_KEY', test_encryption_key):
            encryption_a = TokenEncryption()
            encrypted = encryption_a.encrypt("test_token")
        
        # 生成新密钥B
        new_key = Fernet.generate_key().decode()
        
        # 使用密钥B解密（应该失败）
        with patch('app.core.encryption.settings.TOKEN_ENCRYPTION_KEY', new_key):
            encryption_b = TokenEncryption()
            with pytest.raises(InvalidToken):
                encryption_b.decrypt(encrypted)
    
    def test_singleton_pattern(self, test_encryption_key):
        """
        测试用例6: 测试单例模式
        
        执行:
        - 多次调用get_token_encryption()
        
        验证点:
        - 返回的实例是同一个对象（id相同）
        """
        with patch('app.core.encryption.settings.TOKEN_ENCRYPTION_KEY', test_encryption_key):
            # 重置单例
            import app.core.encryption
            app.core.encryption._encryption_instance = None
            
            instance1 = get_token_encryption()
            instance2 = get_token_encryption()
            
            assert instance1 is instance2, "应返回同一个实例（单例模式）"

