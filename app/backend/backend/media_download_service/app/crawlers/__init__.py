"""
爬虫模块

提供爬虫工厂和统一的爬虫接口
"""
from typing import Dict
from .base_crawler import BaseCrawler
from .vzan_crawler import VzanCrawler
from app.core.exceptions import CrawlerError
import logging

logger = logging.getLogger(__name__)


class CrawlerFactory:
    """
    爬虫工厂类
    
    根据爬虫类型创建相应的爬虫实例
    """
    
    # 注册的爬虫类型映射
    _crawlers = {
        'vzan': VzanCrawler,
        # 未来可扩展其他爬虫
        # 'douyin': DouyinCrawler,
        # 'kuaishou': KuaishouCrawler,
    }
    
    @classmethod
    def create(cls, crawler_type: str, config: Dict) -> BaseCrawler:
        """
        创建爬虫实例
        
        Args:
            crawler_type: 爬虫类型（vzan, douyin等）
            config: 爬虫配置字典
        
        Returns:
            BaseCrawler: 爬虫实例
        
        Raises:
            CrawlerError: 不支持的爬虫类型
        """
        crawler_class = cls._crawlers.get(crawler_type.lower())
        
        if not crawler_class:
            supported_types = ', '.join(cls._crawlers.keys())
            logger.error(f"不支持的爬虫类型: {crawler_type}，支持的类型: {supported_types}")
            raise CrawlerError(
                f"不支持的爬虫类型: {crawler_type}。"
                f"支持的类型: {supported_types}"
            )
        
        logger.info(f"CrawlerFactory: 创建{crawler_type}爬虫实例")
        return crawler_class(config)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取支持的爬虫类型列表
        
        Returns:
            list: 支持的爬虫类型
        """
        return list(cls._crawlers.keys())


# 导出公共接口
__all__ = ['BaseCrawler', 'VzanCrawler', 'CrawlerFactory']

