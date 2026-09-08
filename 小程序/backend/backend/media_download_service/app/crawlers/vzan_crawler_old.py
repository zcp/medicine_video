"""
微赞爬虫适配器模块

使用适配器模式复用 backend/dynamicCrawler_vzan.py
"""
import csv
import logging
import os
import tempfile
import shutil
from typing import Dict
from pathlib import Path
from .base_crawler import BaseCrawler
from app.core.exceptions import CrawlerError, CrawlerConfigError

# 导入已有爬虫实现
import sys
from pathlib import Path
# 添加backend目录到sys.path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))
from dynamicCrawler_vzan_v3 import DuanShuCrawler_vzan

logger = logging.getLogger(__name__)


class VzanCrawler(BaseCrawler):
    """
    微赞爬虫适配器
    
    将已有的 DuanShuCrawler_vzan 适配到 BaseCrawler 接口
    """
    
    def __init__(self, config: Dict):
        """
        初始化适配器
        
        Args:
            config: 爬虫配置字典
        
        Raises:
            CrawlerConfigError: 配置无效或爬虫初始化失败
        """
        super().__init__(config)
        
        # 提取配置
        self.username = config.get('username')
        self.password = config.get('password')
        self.token = config.get('token')
        
        # 创建已有爬虫实例
        try:
            self.crawler = DuanShuCrawler_vzan()
            logger.info("VzanCrawler: DuanShuCrawler_vzan instance created")
        except Exception as e:
            logger.error(f"VzanCrawler: Failed to create crawler instance - {str(e)}")
            raise CrawlerConfigError(f"爬虫初始化失败: {str(e)}")
    
    def validate_config(self) -> bool:
        """
        验证配置
        
        Returns:
            bool: 配置是否有效
        """
        if not all([self.username, self.password, self.token]):
            logger.error("VzanCrawler: Missing required config (username, password, token)")
            return False
        return True
    
    def crawl(self, config: Dict, **kwargs) -> Dict:
        """
        执行爬取（主入口）
        
        Args:
            config: 爬虫配置字典 (包含 username, password, token)
            **kwargs: 
                - page_size: 每页数据量（可选）
                - max_pages: 最大爬取页数（可选）
        
        Returns:
            Dict: 爬取结果摘要
        """
        try:
            # 验证配置
            if not self.validate_config():
                raise CrawlerConfigError("VzanCrawler配置无效：缺少username, password或token")
            
            logger.info("VzanCrawler: Starting crawl")
            
            # 调用已有爬虫的核心方法
            self.crawler.parse_all_liveroomlist_data(config)
            
            logger.info("VzanCrawler: Crawl completed, starting CSV column conversion")
            
            # ⚠️ 重要：转换CSV列名（中文 → 英文）
            # 必须在返回前完成，确保导入模块能正确读取
            csv_file = str(self.crawler.liveroom_list_savefile)
            incremental_file = str(self.crawler.liveroom_list_savefile_inc)
            
            # 转换主CSV文件
            if os.path.exists(csv_file):
                self._convert_csv_columns(csv_file)
                logger.info(f"VzanCrawler: Main CSV converted - {csv_file}")
            
            # 转换增量CSV文件
            if os.path.exists(incremental_file):
                self._convert_csv_columns(incremental_file)
                logger.info(f"VzanCrawler: Incremental CSV converted - {incremental_file}")
            
            logger.info("VzanCrawler: CSV conversion completed, extracting file paths")
            
            # 构造返回结果（获取已有爬虫生成的文件路径）
            failed_file = str(self.crawler.failed_liveroomlist_url)
            
            # 统计CSV行数
            total_rows = self._count_csv_rows(csv_file)
            incremental_rows = self._count_csv_rows(incremental_file)
            failed_rows = self._count_csv_rows(failed_file)
            
            result = {
                "csv_file": csv_file,
                "incremental_file": incremental_file,
                "failed_file": failed_file,
                "total_rows": total_rows,
                "incremental_rows": incremental_rows,
                "failed_rows": failed_rows
            }
            
            logger.info(
                f"VzanCrawler: Crawl result - "
                f"total: {total_rows}, incremental: {incremental_rows}, failed: {failed_rows}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"VzanCrawler: Crawl failed - {str(e)}", exc_info=True)
            raise CrawlerError(f"爬取失败: {str(e)}")
        
        finally:
            # ⚠️ 重要：关闭浏览器，释放资源
            try:
                if hasattr(self, 'crawler') and self.crawler:
                    self.crawler.close()
                    logger.info("VzanCrawler: Browser closed")
            except Exception as e:
                logger.warning(f"VzanCrawler: Failed to close browser - {str(e)}")
    
    def _count_csv_rows(self, csv_file: str) -> int:
        """
        统计CSV文件行数（不含表头）
        
        Args:
            csv_file: CSV文件路径
        
        Returns:
            int: 行数（不含表头），异常时返回0
        """
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过表头
                return sum(1 for _ in reader)
        except Exception as e:
            logger.warning(f"Failed to count rows in {csv_file}: {str(e)}")
            return 0
    
    def _convert_csv_columns(self, csv_file: str) -> None:
        """
        将中文列名CSV转换为英文列名CSV（原地覆盖）
        
        Args:
            csv_file: CSV文件路径
            
        Raises:
            ValueError: 如果必需字段缺失
            Exception: 转换失败
        """
        import tempfile
        import shutil
        
        # 列名映射字典
        COLUMN_MAPPING = {
            '直播间ID': 'liveroom_id',      # 必需
            '播放url': 'resource_url',       # 必需
            '标题': 'liveroom_title',        # 可选
            '直播间url': 'liveroom_url',     # 可选
        }
        
        # 输出列顺序
        OUTPUT_COLUMNS = ['liveroom_id', 'liveroom_title', 'liveroom_url', 'resource_url', 'resource_type']
        
        try:
            logger.info(f"VzanCrawler: Converting CSV columns - {csv_file}")
            
            # 读取原始CSV
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                
                if not fieldnames:
                    raise ValueError(f"CSV文件没有表头: {csv_file}")
                
                # ⚠️ 重要：检查文件是否已经是英文列名（已转换过）
                required_en_columns = {'liveroom_id', 'resource_url', 'resource_type'}
                if required_en_columns.issubset(set(fieldnames)):
                    logger.info(
                        f"VzanCrawler: CSV文件已经是英文列名，跳过转换 - {csv_file}, "
                        f"表头: {list(fieldnames)}"
                    )
                    # 即使跳过转换，也要验证文件格式是否正确
                    # 读取一行数据验证格式
                    rows = list(reader)
                    if rows:
                        logger.info(f"VzanCrawler: 英文列名CSV文件验证通过，包含 {len(rows)} 行数据")
                    return  # 已经是英文列名，不需要转换
                
                # 如果是中文列名，需要重新读取文件（因为reader已经被消耗）
                # 重新打开文件读取所有数据行
                f.seek(0)  # 重置文件指针
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # 验证必需字段
                if not rows:
                    logger.warning(f"VzanCrawler: Empty CSV file - {csv_file}")
                    return
                
                # 检查是否是中文列名
                first_row = rows[0]
                required_cn_columns = {'直播间ID', '播放url'}
                if not required_cn_columns.issubset(set(first_row.keys())):
                    raise ValueError(
                        f"CSV文件列名格式不正确。"
                        f"期望中文列名: {required_cn_columns} 或英文列名: {required_en_columns}, "
                        f"实际: {list(first_row.keys())}"
                    )
            
            # 使用临时文件写入转换后的数据
            temp_fd, temp_path = tempfile.mkstemp(suffix='.csv', text=True)
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
                    writer.writeheader()
                    
                    converted_count = 0
                    skipped_count = 0
                    
                    for row in rows:
                        try:
                            # 转换列名并构造新行
                            new_row = {}
                            for cn_col, en_col in COLUMN_MAPPING.items():
                                value = row.get(cn_col, '').strip()
                                new_row[en_col] = value if value else None
                            
                            # 添加固定字段
                            new_row['resource_type'] = 'hls'
                            
                            # 验证必需字段
                            if not new_row.get('liveroom_id') or not new_row.get('resource_url'):
                                logger.warning(
                                    f"VzanCrawler: Skipping row with missing required fields - "
                                    f"liveroom_id: {new_row.get('liveroom_id')}, "
                                    f"resource_url: {new_row.get('resource_url')}"
                                )
                                skipped_count += 1
                                continue
                            
                            writer.writerow(new_row)
                            converted_count += 1
                            
                        except Exception as e:
                            logger.warning(f"VzanCrawler: Failed to convert row - {str(e)}")
                            skipped_count += 1
                            continue
                
                # 原子替换：移动临时文件到目标文件
                shutil.move(temp_path, csv_file)
                
                # ⚠️ 验证转换后的CSV文件格式
                try:
                    with open(csv_file, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        actual_fieldnames = reader.fieldnames
                        
                        if not actual_fieldnames:
                            raise ValueError(f"转换后的CSV文件没有表头: {csv_file}")
                        
                        # 验证必需列是否存在
                        required_columns = {'liveroom_id', 'resource_url', 'resource_type'}
                        actual_columns_set = set(actual_fieldnames)
                        if not required_columns.issubset(actual_columns_set):
                            missing = required_columns - actual_columns_set
                            raise ValueError(
                                f"转换后的CSV文件表头缺少必需列: {missing}, "
                                f"实际列: {actual_columns_set}, "
                                f"文件: {csv_file}"
                            )
                        
                        logger.info(
                            f"VzanCrawler: 转换后的CSV文件验证通过 - "
                            f"表头: {list(actual_fieldnames)}, "
                            f"文件: {csv_file}"
                        )
                except Exception as e:
                    logger.error(f"VzanCrawler: 转换后的CSV文件验证失败: {str(e)}")
                    # 如果验证失败，删除有问题的文件
                    if os.path.exists(csv_file):
                        try:
                            os.remove(csv_file)
                            logger.warning(f"VzanCrawler: 已删除有问题的CSV文件: {csv_file}")
                        except:
                            pass
                    raise
                
                logger.info(
                    f"VzanCrawler: CSV conversion successful - {csv_file}, "
                    f"converted: {converted_count}, skipped: {skipped_count}"
                )
                
            except Exception as e:
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
                
        except Exception as e:
            logger.error(f"VzanCrawler: CSV conversion failed - {csv_file}: {str(e)}", exc_info=True)
            raise Exception(f"CSV列名转换失败: {str(e)}")

