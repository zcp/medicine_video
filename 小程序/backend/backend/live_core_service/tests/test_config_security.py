"""
配置安全性测试

验证配置管理的安全性，确保生产环境配置符合安全要求
"""

import pytest
import os
from unittest.mock import patch
from app.core.config import Settings
from app.core.logging_utils import sanitize_log_message


class TestProductionConfigValidation:
    """生产环境配置验证测试"""
    
    def test_no_default_passwords_in_production(self):
        """测试：生产环境不允许默认密码"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "324zq999",  # 默认密码
            "JWT_SECRET_KEY": "a" * 32,  # 有效密钥
            "CORS_ORIGINS": "https://example.com",
            "DEBUG": "false"
        }):
            with pytest.raises(ValueError, match="不允许使用默认数据库密码"):
                Settings()
    
    def test_no_empty_password_in_production(self):
        """测试：生产环境不允许空密码"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "",  # 空密码
            "JWT_SECRET_KEY": "a" * 32,
            "CORS_ORIGINS": "https://example.com",
            "DEBUG": "false"
        }):
            with pytest.raises(ValueError, match="POSTGRES_PASSWORD 环境变量未设置"):
                Settings()
    
    def test_jwt_key_length_validation(self):
        """测试：JWT密钥长度验证"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "secure_password",
            "JWT_SECRET_KEY": "short",  # 太短
            "CORS_ORIGINS": "https://example.com",
            "DEBUG": "false"
        }):
            with pytest.raises(ValueError, match="长度不足32个字符"):
                Settings()
    
    def test_no_default_jwt_key_in_production(self):
        """测试：生产环境不允许默认JWT密钥"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "secure_password",
            "JWT_SECRET_KEY": "my-key",  # 默认密钥
            "CORS_ORIGINS": "https://example.com",
            "DEBUG": "false"
        }):
            with pytest.raises(ValueError, match="不允许使用默认JWT密钥"):
                Settings()
    
    def test_cors_not_wildcard_in_production(self):
        """测试：生产环境CORS不允许通配符"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "secure_password",
            "JWT_SECRET_KEY": "a" * 32,
            "CORS_ORIGINS": "*",  # 通配符
            "DEBUG": "false"
        }):
            with pytest.raises(ValueError, match="不允许使用.*\\*"):
                Settings()
    
    def test_debug_mode_off_in_production(self):
        """测试：生产环境必须关闭DEBUG模式"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "secure_password",
            "JWT_SECRET_KEY": "a" * 32,
            "CORS_ORIGINS": "https://example.com",
            "DEBUG": "true"  # DEBUG开启
        }):
            with pytest.raises(ValueError, match="必须关闭DEBUG模式"):
                Settings()
    
    def test_valid_production_config(self):
        """测试：有效的生产环境配置应该通过验证"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "POSTGRES_PASSWORD": "secure_password_12345",
            "JWT_SECRET_KEY": "a" * 32,
            "CORS_ORIGINS": "https://example.com,https://www.example.com",
            "DEBUG": "false"
        }):
            # 应该不抛出异常
            settings = Settings()
            assert settings.ENVIRONMENT == "production"
            assert not settings.DEBUG


class TestDevelopmentConfigWarnings:
    """开发环境配置警告测试"""
    
    def test_development_allows_default_password_with_warning(self):
        """测试：开发环境允许默认密码但会发出警告"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "POSTGRES_PASSWORD": "324zq999",
            "JWT_SECRET_KEY": "my-key"
        }):
            with pytest.warns(UserWarning, match="使用默认数据库密码"):
                Settings()
    
    def test_development_config_loads_successfully(self):
        """测试：开发环境配置加载成功"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "POSTGRES_PASSWORD": "dev_password",
            "JWT_SECRET_KEY": "dev_key_12345678901234567890123"
        }):
            settings = Settings()
            assert settings.ENVIRONMENT == "development"


class TestLogSanitization:
    """日志脱敏测试"""
    
    def test_sanitize_database_url(self):
        """测试：数据库URL脱敏"""
        message = "postgresql://user:password123@localhost:5432/db"
        sanitized = sanitize_log_message(message)
        
        assert "password123" not in sanitized
        assert "***" in sanitized
        assert "user" in sanitized
        assert "localhost" in sanitized
    
    def test_sanitize_async_database_url(self):
        """测试：异步数据库URL脱敏"""
        message = "postgresql+asyncpg://user:secret_pwd@localhost:5432/db"
        sanitized = sanitize_log_message(message)
        
        assert "secret_pwd" not in sanitized
        assert "***" in sanitized
    
    def test_sanitize_jwt_token(self):
        """测试：JWT Token脱敏"""
        message = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzIn0.signature"
        sanitized = sanitize_log_message(message)
        
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "Bearer ***" in sanitized
    
    def test_sanitize_environment_variables(self):
        """测试：环境变量脱敏"""
        test_cases = [
            ('JWT_SECRET_KEY="my-secret-key"', "JWT_SECRET_KEY"),
            ("PASSWORD='secret123'", "PASSWORD"),
            ("API_TOKEN: abc123def", "API_TOKEN"),
        ]
        
        for message, keyword in test_cases:
            sanitized = sanitize_log_message(message)
            # 确保敏感值被替换
            assert "secret" not in sanitized.lower() or "***" in sanitized
            assert "abc123def" not in sanitized or "***" in sanitized
            # 确保关键词保留
            assert keyword in sanitized
    
    def test_sanitize_authorization_header(self):
        """测试：Authorization头脱敏"""
        message = 'Authorization: "Bearer token123456"'
        sanitized = sanitize_log_message(message)
        
        assert "token123456" not in sanitized
        assert "***" in sanitized


class TestCORSConfiguration:
    """CORS配置测试"""
    
    def test_cors_single_origin(self):
        """测试：单个CORS源"""
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "https://example.com",
            "POSTGRES_PASSWORD": "pwd",
            "JWT_SECRET_KEY": "a" * 32
        }):
            settings = Settings()
            assert settings.BACKEND_CORS_ORIGINS == ["https://example.com"]
    
    def test_cors_multiple_origins(self):
        """测试：多个CORS源"""
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "https://example.com,https://www.example.com,http://localhost:3000",
            "POSTGRES_PASSWORD": "pwd",
            "JWT_SECRET_KEY": "a" * 32
        }):
            settings = Settings()
            assert len(settings.BACKEND_CORS_ORIGINS) == 3
            assert "https://example.com" in settings.BACKEND_CORS_ORIGINS
            assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
    
    def test_cors_wildcard_default(self):
        """测试：默认CORS通配符"""
        with patch.dict(os.environ, {
            "POSTGRES_PASSWORD": "pwd",
            "JWT_SECRET_KEY": "a" * 32
        }, clear=True):
            # 清除CORS_ORIGINS环境变量，使用默认值
            os.environ.pop("CORS_ORIGINS", None)
            settings = Settings()
            assert "*" in settings.BACKEND_CORS_ORIGINS

