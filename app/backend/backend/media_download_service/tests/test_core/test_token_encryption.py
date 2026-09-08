"""
令牌加密工具测试

测试 app/core/encryption.py 中的TokenEncryption
"""
import pytest
import os
from cryptography.fernet import Fernet
from app.core.encryption import TokenEncryption, get_token_encryption
from app.core.config import settings


class TestTokenEncryption:
    """令牌加密测试类"""
    
    @pytest.fixture
    def encryption_key(self):
        """生成测试用加密密钥"""
        return Fernet.generate_key().decode()
    
    @pytest.fixture
    def token_encryption(self, encryption_key, monkeypatch):
        """创建测试用TokenEncryption实例"""
        # 临时设置环境变量
        monkeypatch.setattr(settings, 'TOKEN_ENCRYPTION_KEY', encryption_key)
        return TokenEncryption()
    
    def test_encrypt_decrypt_round_trip(self, token_encryption):
        """
        测试用例1: 测试加密解密往返
        
        执行:
        - 加密token
        - 解密token
        
        验证点:
        - 解密后的token与原始token一致
        """
        original_token = "my_secret_token_123"
        
        # 加密
        encrypted = token_encryption.encrypt(original_token)
        
        # 验证加密结果不同于原始token
        assert encrypted != original_token, "加密后应与原始token不同"
        
        # 解密
        decrypted = token_encryption.decrypt(encrypted)
        
        # 验证解密结果
        assert decrypted == original_token, "解密后应恢复原始token"
    
    def test_encrypt_different_results(self, token_encryption):
        """
        测试用例2: 测试加密结果随机性
        
        执行:
        - 对相同token加密两次
        
        验证点:
        - 两次加密结果不同（Fernet使用随机初始化向量）
        """
        token = "test_token"
        
        encrypted1 = token_encryption.encrypt(token)
        encrypted2 = token_encryption.encrypt(token)
        
        # Fernet加密包含随机初始化向量，因此每次结果不同
        assert encrypted1 != encrypted2, "多次加密结果应不同"
        
        # 但都能正确解密
        assert token_encryption.decrypt(encrypted1) == token
        assert token_encryption.decrypt(encrypted2) == token
    
    def test_decrypt_invalid_token(self, token_encryption):
        """
        测试用例3: 测试解密无效token
        
        执行:
        - 尝试解密无效的加密字符串
        
        验证点:
        - 抛出Exception
        """
        invalid_encrypted = "invalid_encrypted_token"
        
        with pytest.raises(Exception):
            token_encryption.decrypt(invalid_encrypted)
    
    def test_initialization_without_key(self, monkeypatch):
        """
        测试用例4: 测试未设置加密密钥
        
        执行:
        - 在未设置TOKEN_ENCRYPTION_KEY的情况下初始化
        
        验证点:
        - 抛出ValueError
        - 错误消息包含"TOKEN_ENCRYPTION_KEY环境变量未设置"
        """
        # 清空环境变量
        monkeypatch.setattr(settings, 'TOKEN_ENCRYPTION_KEY', '')
        
        with pytest.raises(ValueError) as exc_info:
            TokenEncryption()
        
        assert "TOKEN_ENCRYPTION_KEY环境变量未设置" in str(exc_info.value), \
            "错误消息应包含'TOKEN_ENCRYPTION_KEY环境变量未设置'"
    
    def test_get_token_encryption_singleton(self, encryption_key, monkeypatch):
        """
        测试用例5: 测试单例模式
        
        执行:
        - 调用get_token_encryption()两次
        
        验证点:
        - 返回同一个实例
        """
        monkeypatch.setattr(settings, 'TOKEN_ENCRYPTION_KEY', encryption_key)
        
        instance1 = get_token_encryption()
        instance2 = get_token_encryption()
        
        assert instance1 is instance2, "应返回同一个实例（单例模式）"
    
    def test_encrypt_empty_string(self, token_encryption):
        """
        测试用例6: 测试加密空字符串
        
        执行:
        - 尝试加密空字符串
        
        验证点:
        - 抛出ValueError
        - 错误消息包含"token不能为空"
        """
        empty_token = ""
        
        with pytest.raises(ValueError) as exc_info:
            token_encryption.encrypt(empty_token)
        
        assert "token不能为空" in str(exc_info.value), \
            "错误消息应包含'token不能为空'"
    
    def test_encrypt_unicode_token(self, token_encryption):
        """
        测试用例7: 测试加密Unicode字符
        
        执行:
        - 加密包含中文的token
        - 解密
        
        验证点:
        - 正确处理Unicode字符
        """
        unicode_token = "测试令牌_123_🔐"
        
        encrypted = token_encryption.encrypt(unicode_token)
        decrypted = token_encryption.decrypt(encrypted)
        
        assert decrypted == unicode_token, "应正确处理Unicode字符"

