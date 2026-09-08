"""
爬虫基类测试

测试 app/crawlers/base_crawler.py 中的BaseCrawler
"""
import pytest
from typing import Dict
from app.crawlers.base_crawler import BaseCrawler


class TestBaseCrawler:
    """爬虫基类测试"""
    
    @pytest.fixture
    def test_crawler_config(self):
        """测试用爬虫配置"""
        return {
            'username': 'test_user',
            'password': 'test_pass',
            'token': 'test_encrypted_token',
            'timeout': 10,
            'temp_dir': '/tmp/vzan_crawler',
            'batch_size': 100
        }
    
    def test_base_crawler_initialization(self, test_crawler_config):
        """
        测试用例1: 测试基类初始化
        
        准备:
        - 提供完整的配置字典
        
        执行:
        - 创建BaseCrawler的具体子类实例
        
        验证点:
        - timeout属性正确设置
        - config属性正确保存
        """
        # 创建一个简单的子类用于测试
        class TestCrawler(BaseCrawler):
            def crawl(self, config: Dict, **kwargs) -> Dict:
                return {
                    "csv_file": "/tmp/test.csv",
                    "incremental_file": "/tmp/test_inc.csv",
                    "failed_file": "/tmp/failed.txt",
                    "total_rows": 0,
                    "incremental_rows": 0,
                    "failed_rows": 0
                }
            
            def validate_config(self) -> bool:
                return True
        
        crawler = TestCrawler(test_crawler_config)
        
        assert crawler.timeout == test_crawler_config['timeout'], "timeout应正确设置"
        assert crawler.config == test_crawler_config, "config应正确保存"
    
    def test_base_crawler_abstract_methods(self):
        """
        测试用例2: 测试抽象方法强制实现
        
        执行:
        - 尝试直接实例化BaseCrawler（应失败）
        - 尝试实例化未实现抽象方法的子类（应失败）
        
        验证点:
        - 抛出TypeError异常
        """
        # 测试直接实例化
        with pytest.raises(TypeError):
            BaseCrawler({})
        
        # 测试未实现抽象方法的子类
        class IncompleteCrawler(BaseCrawler):
            pass  # 未实现crawl和validate_config
        
        with pytest.raises(TypeError):
            IncompleteCrawler({})
    
    def test_base_crawler_timeout_default(self):
        """
        测试用例3: 测试timeout默认值
        
        准备:
        - 不提供timeout配置
        
        执行:
        - 创建爬虫实例
        
        验证点:
        - timeout使用默认值10
        """
        class TestCrawler(BaseCrawler):
            def crawl(self, config: Dict, **kwargs) -> Dict:
                return {
                    "csv_file": "/tmp/test.csv",
                    "incremental_file": "/tmp/test_inc.csv",
                    "failed_file": "/tmp/failed.txt",
                    "total_rows": 0,
                    "incremental_rows": 0,
                    "failed_rows": 0
                }
            
            def validate_config(self) -> bool:
                return True
        
        config_without_timeout = {'username': 'test'}
        crawler = TestCrawler(config_without_timeout)
        
        assert crawler.timeout == 10, "timeout应使用默认值10"

