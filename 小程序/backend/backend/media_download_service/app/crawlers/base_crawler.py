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

    说明：
    - 自 2025 起，部分爬虫将主状态从 CSV 迁移至 SQLite（例如 vzan 爬虫）。
    - 抽象层需允许返回增量 CSV 文件用于下游导入，同时总量/失败等统计推荐基于 SQLite 计算。
    """
    
    def __init__(self, config: Dict):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置字典，至少包含:
                - timeout: 超时时间（秒），默认10秒
                - temp_dir: 临时文件目录
            
            注：对于使用 SQLite 的实现，config 中可能包含与状态库相关的键（如 db_file 等），
            但是否使用与具体子类实现有关。
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
            Dict: 爬取结果摘要（键至少包含以下字段，子类可在不删除这些键的前提下扩展）
                {
                    "csv_file": str|None,            # 全量 CSV 文件路径；若无可为 None
                    "incremental_file": str,         # 本轮增量 CSV 文件路径（必须尽量存在）
                    "failed_file": str|None,         # 失败记录文件路径（如有）
                    "total_rows": int,               # 推荐从 SQLite 统计总记录数
                    "incremental_rows": int,         # 增量 CSV 行数（不含表头）
                    "failed_rows": int               # 当前失败记录数量（如 SQLite 中 video_url 为空的记录数）
                }

            可选扩展字段（建议但不强制，具体取决于子类实现）:
                {
                    "db_file": str|None,             # SQLite 状态库路径
                    "db_total_rows": int|None,       # 通过 SQLite 统计的总行数
                    "...": any                       # 其他统计信息
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

