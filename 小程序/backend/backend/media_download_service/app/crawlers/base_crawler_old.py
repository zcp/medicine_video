"""
爬虫基类模块

定义所有爬虫必须实现的统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    爬虫基类，定义统一接口
    
    所有具体的爬虫实现（如VzanCrawler）必须继承此类并实现抽象方法
    """
    
    def __init__(self, config: Dict):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置字典，至少包含:
                - timeout: 超时时间（秒），默认10秒
                - temp_dir: 临时文件目录
        """
        self.config = config
        self.timeout = config.get('timeout', 10)
        
        logger.info(f"{self.__class__.__name__} initialized with timeout={self.timeout}s")
    
    @abstractmethod
    def crawl(self, config: Dict, **kwargs) -> Dict:
        """
        执行爬取任务（抽象方法，子类必须实现）
        
        Args:
            config: 爬虫配置字典，包含 username, password, token 等
            **kwargs: 爬虫特定的额外参数，如:
                - page_size: 每页数据量（默认10）
                - max_pages: 最大爬取页数（默认全部）
        
        Returns:
            Dict: 爬取结果摘要
                {
                    "csv_file": str,             # 主 CSV 文件路径
                    "incremental_file": str,     # 增量 CSV 文件路径
                    "failed_file": str,          # 失败记录文件路径
                    "total_rows": int,           # 总爬取行数
                    "failed_rows": int,          # 失败行数
                    "incremental_rows": int      # 本次新增行数
                }
        
        Raises:
            CrawlerError: 爬取失败时抛出
            CrawlerTimeoutError: 爬取超时时抛出
            CrawlerAPIError: API调用失败时抛出
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否完整有效（抽象方法，子类必须实现）
        
        Returns:
            bool: 配置是否有效
        """
        pass

