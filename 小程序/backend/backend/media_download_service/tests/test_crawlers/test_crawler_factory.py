"""
爬虫工厂测试

测试 app/crawlers/__init__.py 中的CrawlerFactory
"""
import pytest
import sys
from unittest.mock import MagicMock, Mock, patch

# ✅ 关键：必须在导入 app.crawlers 之前设置 mock
# 否则 vzan_crawler.py 在导入时会尝试导入真实的 DuanShuCrawler_vzan
mock_crawler_class = MagicMock()
sys.modules['dynamicCrawler_vzan'] = MagicMock(
    DuanShuCrawler_vzan=mock_crawler_class
)

# ✅ 现在才导入（会使用上面的 mock）
from app.crawlers import CrawlerFactory
from app.crawlers.vzan_crawler import VzanCrawler
from app.core.exceptions import CrawlerConfigError, CrawlerError


class TestCrawlerFactory:
    """爬虫工厂测试类"""
    
    @pytest.fixture
    def valid_vzan_config(self):
        """有效的微赞配置"""
        return {
            'username': 'test_user',
            'password': 'test_pass',
            'token': 'test_token',
            'timeout': 10
        }
    
    def test_create_vzan_crawler_success(self, valid_vzan_config):
        """
        测试用例1: 测试创建微赞爬虫成功
        
        执行:
        - 调用CrawlerFactory.create('vzan', config)
        
        验证点:
        - 返回VzanCrawler实例
        - 配置正确传递
        """
        crawler = CrawlerFactory.create('vzan', valid_vzan_config)
        
        assert isinstance(crawler, VzanCrawler), "应返回VzanCrawler实例"
        assert crawler.username == 'test_user', "配置应正确传递"
    
    def test_create_unsupported_crawler_type(self, valid_vzan_config):
        """
        测试用例2: 测试创建不支持的爬虫类型
        
        执行:
        - 调用CrawlerFactory.create('invalid_type', config)
        
        验证点:
        - 抛出CrawlerError
        - 错误消息包含"不支持的爬虫类型"
        """
        with pytest.raises(CrawlerError) as exc_info:
            CrawlerFactory.create('invalid_type', valid_vzan_config)
        
        assert "不支持的爬虫类型" in str(exc_info.value), "错误消息应包含'不支持的爬虫类型'"
    
    def test_get_supported_types(self):
        """
        测试用例3: 测试获取支持的爬虫类型
        
        执行:
        - 调用CrawlerFactory.get_supported_types()
        
        验证点:
        - 返回列表
        - 包含'vzan'
        """
        types = CrawlerFactory.get_supported_types()
        
        assert isinstance(types, list), "应返回列表"
        assert 'vzan' in types, "应包含'vzan'"
    
    def test_factory_pattern_isolation(self, valid_vzan_config):
        """
        测试用例4: 测试工厂模式隔离性
        
        执行:
        - 创建两个独立的爬虫实例
        - 修改第一个实例的属性
        
        验证点:
        - 第二个实例不受影响
        """
        crawler1 = CrawlerFactory.create('vzan', valid_vzan_config)
        crawler2 = CrawlerFactory.create('vzan', valid_vzan_config)
        
        # 修改crawler1
        crawler1.username = 'modified_user'
        
        # crawler2应不受影响
        assert crawler2.username == 'test_user', "实例应相互隔离"
