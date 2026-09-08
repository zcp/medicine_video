"""
微赞爬虫测试

测试 app/crawlers/vzan_crawler.py 中的VzanCrawler
"""
import pytest
import csv
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock dynamicCrawler_vzan 模块，避免导入错误
sys.modules['dynamicCrawler_vzan'] = MagicMock()

from app.crawlers.vzan_crawler import VzanCrawler
from app.core.exceptions import CrawlerError, CrawlerConfigError


class TestVzanCrawler:
    """微赞爬虫测试类"""
    
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
    
    @pytest.fixture
    def vzan_crawler(self, test_crawler_config):
        """创建测试用的VzanCrawler实例"""
        return VzanCrawler(test_crawler_config)
    
    def test_vzan_crawler_initialization(self, vzan_crawler, test_crawler_config):
        """
        测试用例1: 测试初始化（适配器模式）
        
        验证点:
        - username属性正确设置
        - password属性正确设置
        - token正确设置
        - self.crawler是DuanShuCrawler_vzan实例（适配器模式核心）
        """
        assert vzan_crawler.username == 'test_user', "username应正确设置"
        assert vzan_crawler.password == 'test_pass', "password应正确设置"
        assert vzan_crawler.token == 'test_encrypted_token', "token应正确设置"
        assert vzan_crawler.crawler is not None, "应创建DuanShuCrawler_vzan实例"
        assert hasattr(vzan_crawler.crawler, 'parse_all_liveroomlist_data'), "应有parse_all_liveroomlist_data方法"
    
    def test_validate_config_success(self, vzan_crawler):
        """
        测试用例2: 测试配置验证成功
        
        执行:
        - 调用validate_config()
        
        验证点:
        - 返回True
        """
        assert vzan_crawler.validate_config() is True, "完整配置应验证成功"
    
    def test_validate_config_missing_fields(self, test_crawler_config):
        """
        测试用例3: 测试配置缺失
        
        准备:
        - 创建缺少username的配置
        
        执行:
        - 创建爬虫实例
        - 调用validate_config()
        
        验证点:
        - 返回False
        """
        # 创建缺少字段的配置
        config = test_crawler_config.copy()
        config['username'] = None
        
        crawler = VzanCrawler(config)
        assert crawler.validate_config() is False, "缺少username应验证失败"
    
    @patch.object(VzanCrawler, '_convert_csv_columns')
    def test_crawl_success(self, mock_convert, vzan_crawler, tmp_path):
        """
        测试用例4: 测试爬取成功（适配器模式Mock）
        
        准备:
        - Mock self.crawler.parse_all_liveroomlist_data（适配器模式核心）
        - Mock CSV文件已生成
        - Mock _convert_csv_columns（CSV转换）
        
        执行:
        - 调用crawl()
        
        验证点:
        - 返回Dict包含正确结构
        - self.crawler.parse_all_liveroomlist_data被调用
        - _convert_csv_columns被调用两次（主文件+增量文件）
        - self.crawler.close()被调用（浏览器清理）
        """
        # Mock CSV文件生成
        csv_file = tmp_path / "liveroomlist_vzan_api.csv"
        csv_file.write_text("liveroom_id,resource_url\n1234567890,https://test.m3u8", encoding='utf-8')
        incremental_file = tmp_path / "liveroomlist_inc_vzan_backup.csv"
        incremental_file.write_text("liveroom_id,resource_url\n1234567890,https://test.m3u8", encoding='utf-8')
        failed_file = tmp_path / "failed_urls.txt"
        failed_file.write_text("", encoding='utf-8')
        
        # Mock DuanShuCrawler_vzan的文件路径属性
        vzan_crawler.crawler.liveroom_list_savefile = str(csv_file)
        vzan_crawler.crawler.liveroom_list_savefile_inc = str(incremental_file)
        vzan_crawler.crawler.failed_liveroomlist_url = str(failed_file)
        
        # Mock parse_all_liveroomlist_data（不执行实际爬取）
        vzan_crawler.crawler.parse_all_liveroomlist_data = Mock()
        
        # Mock _convert_csv_columns
        mock_convert.return_value = None
        
        # Mock close方法
        vzan_crawler.crawler.close = Mock()
        
        # 执行爬取
        config = {'token': 'test_token', 'username': 'test', 'password': 'test'}
        result = vzan_crawler.crawl(config, page_size=10)
        
        # 验证返回结构
        assert isinstance(result, dict), "应返回字典"
        assert 'csv_file' in result, "应包含csv_file"
        assert 'incremental_file' in result, "应包含incremental_file"
        assert 'failed_file' in result, "应包含failed_file"
        assert 'total_rows' in result, "应包含total_rows"
        assert 'incremental_rows' in result, "应包含incremental_rows"
        assert 'failed_rows' in result, "应包含failed_rows"
        
        # 验证文件路径
        assert result['csv_file'] == str(csv_file), "csv_file路径应正确"
        assert result['incremental_file'] == str(incremental_file), "incremental_file路径应正确"
        assert result['failed_file'] == str(failed_file), "failed_file路径应正确"
        
        # 验证适配器方法调用
        vzan_crawler.crawler.parse_all_liveroomlist_data.assert_called_once_with(config)
        
        # 验证CSV列名转换被调用（主文件+增量文件）
        assert mock_convert.call_count == 2, "应调用_convert_csv_columns两次"
        
        # 验证浏览器关闭
        vzan_crawler.crawler.close.assert_called_once()
    
    def test_csv_column_conversion(self, vzan_crawler, tmp_path):
        """
        测试用例5: 测试CSV列名转换（中文 → 英文）
        
        准备:
        - 创建中文列名的CSV文件
        - 内容包含必需字段（直播间ID, 播放url）和可选字段（标题, 直播间url）
        
        执行:
        - 调用_convert_csv_columns()
        
        验证点:
        - CSV文件列名转换为英文
        - 必需字段正确映射
        - 可选字段正确映射
        - 自动添加 resource_type 列（默认值 'hls'）
        - 行数与原文件一致
        """
        # 创建中文列名CSV
        csv_file = tmp_path / "test_chinese.csv"
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['直播间ID', '标题', '直播间url', '播放url', '创建时间'])
            writer.writeheader()
            writer.writerow({
                '直播间ID': '1234567890',
                '标题': '测试直播间',
                '直播间url': 'https://test.com/live/123',
                '播放url': 'https://test.com/video.m3u8',
                '创建时间': '2025-01-13'
            })
        
        # 执行转换
        vzan_crawler._convert_csv_columns(str(csv_file))
        
        # 验证转换后的文件
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # 验证列名
            assert 'liveroom_id' in reader.fieldnames, "应有liveroom_id列"
            assert 'liveroom_title' in reader.fieldnames, "应有liveroom_title列"
            assert 'liveroom_url' in reader.fieldnames, "应有liveroom_url列"
            assert 'resource_url' in reader.fieldnames, "应有resource_url列"
            assert 'resource_type' in reader.fieldnames, "应有resource_type列"
            
            # 验证中文列名已删除
            assert '直播间ID' not in reader.fieldnames, "中文列名应已删除"
            assert '播放url' not in reader.fieldnames, "中文列名应已删除"
            
            # 验证数据正确性
            assert len(rows) == 1, "应有1行数据"
            assert rows[0]['liveroom_id'] == '1234567890', "liveroom_id应正确"
            assert rows[0]['liveroom_title'] == '测试直播间', "liveroom_title应正确"
            assert rows[0]['resource_url'] == 'https://test.com/video.m3u8', "resource_url应正确"
            assert rows[0]['resource_type'] == 'hls', "resource_type应为hls"
    
    def test_browser_cleanup(self, vzan_crawler, tmp_path):
        """
        测试用例6: 测试浏览器资源清理
        
        准备:
        - Mock DuanShuCrawler_vzan.close()
        - 模拟爬取过程抛出异常
        
        执行:
        - 调用crawl()并捕获异常
        
        验证点:
        - 即使爬取失败，self.crawler.close()也被调用（finally块）
        """
        # Mock close方法
        vzan_crawler.crawler.close = Mock()
        
        # Mock parse_all_liveroomlist_data抛出异常
        vzan_crawler.crawler.parse_all_liveroomlist_data = Mock(side_effect=Exception("Crawl failed"))
        
        # 执行爬取（预期失败）
        config = {'token': 'test_token', 'username': 'test', 'password': 'test'}
        
        try:
            vzan_crawler.crawl(config)
        except Exception:
            pass  # 预期异常
        
        # 验证浏览器被关闭（即使爬取失败）
        vzan_crawler.crawler.close.assert_called_once()
    
    def test_crawl_result_structure(self, vzan_crawler, tmp_path):
        """
        测试用例7: 测试爬取结果结构完整性
        
        准备:
        - Mock成功的爬取流程
        - 生成完整的CSV文件
        
        执行:
        - 调用crawl()
        
        验证点:
        - 返回Dict包含所有必需字段
        - 字段类型正确
        """
        # Mock CSV文件
        csv_file = tmp_path / "main.csv"
        csv_file.write_text("liveroom_id,resource_url\n1,url1\n2,url2", encoding='utf-8')
        incremental_file = tmp_path / "inc.csv"
        incremental_file.write_text("liveroom_id,resource_url\n3,url3", encoding='utf-8')
        failed_file = tmp_path / "failed.txt"
        failed_file.write_text("error1\nerror2", encoding='utf-8')
        
        vzan_crawler.crawler.liveroom_list_savefile = str(csv_file)
        vzan_crawler.crawler.liveroom_list_savefile_inc = str(incremental_file)
        vzan_crawler.crawler.failed_liveroomlist_url = str(failed_file)
        
        vzan_crawler.crawler.parse_all_liveroomlist_data = Mock()
        vzan_crawler.crawler.close = Mock()
        
        # Mock _convert_csv_columns
        with patch.object(vzan_crawler, '_convert_csv_columns'):
            config = {'token': 'test', 'username': 'test', 'password': 'test'}
            result = vzan_crawler.crawl(config)
        
        # 验证结构
        assert isinstance(result, dict), "应返回字典"
        assert isinstance(result['csv_file'], str), "csv_file应为字符串"
        assert isinstance(result['incremental_file'], str), "incremental_file应为字符串"
        assert isinstance(result['failed_file'], str), "failed_file应为字符串"
        assert isinstance(result['total_rows'], int), "total_rows应为整数"
        assert isinstance(result['incremental_rows'], int), "incremental_rows应为整数"
        assert isinstance(result['failed_rows'], int), "failed_rows应为整数"

