"""
微赞爬虫适配器模块

使用适配器模式复用 backend/dynamicCrawler_vzan.py
"""
import csv
import logging
import os
import tempfile
import shutil
import threading
import concurrent.futures
from typing import Dict
from pathlib import Path
import sqlite3
from .base_crawler import BaseCrawler
from app.core.exceptions import CrawlerError, CrawlerConfigError

# 导入已有爬虫实现
from pathlib import Path

import asyncio
import sys

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
        #self.username = config.get('username')
        #self.password = config.get('password')
        self.token = config.get('token')
        self.cookie = config.get("cookie")
        
        # ⚠️ 延迟初始化：不在 __init__ 中创建 crawler，避免 Playwright 初始化失败
        # 将在首次调用 crawl() 时通过 _ensure_crawler() 创建
        self.crawler = None
        self._init_lock = threading.Lock()  # 线程安全锁
        self._executor = None  # ⚠️ 新增：保存线程池引用，用于后续关闭操作
        logger.info("VzanCrawler: Initialized (crawler will be created on first use)")

    # vzan_crawler.py


    def _create_duanshu_crawler(self):
        # 只在这个线程里使用 Proactor
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return DuanShuCrawler_vzan()

    def _ensure_crawler(self):
        if self.crawler is None:
            with self._init_lock:
                if self.crawler is None:
                    logger.info("VzanCrawler: Creating crawler instance in separate thread...")
                    try:
                            # ⚠️ 关键修改：不使用 with 语句，手动管理线程池生命周期
                            # 保存线程池引用，确保后续可以在同一线程中关闭
                            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                            future = self._executor.submit(self._create_duanshu_crawler)
                            self.crawler = future.result(timeout=30)
                            logger.info("VzanCrawler: DuanShuCrawler_vzan instance created successfully")
                    except Exception as e:
                            logger.error(f"VzanCrawler: Failed to create crawler instance - {str(e)}")
                            # 清理线程池
                            if self._executor:
                                self._executor.shutdown(wait=False)
                                self._executor = None
                            raise CrawlerConfigError(f"爬虫初始化失败: {str(e)}")

    def close(self):
        """
        供 DownloadService 调用，统一关闭内部爬虫资源

        注意：Playwright 对象在线程中创建，需要在同一线程中关闭
        """
        if not self.crawler:
            return

        crawler_to_close = self.crawler  # 保存引用
        executor_to_close = self._executor  # 保存线程池引用

        try:
            if hasattr(crawler_to_close, 'close'):
                # ⚠️ 关键修改：使用创建时的线程池，在同一线程中关闭
                if executor_to_close:
                    try:
                        def _close_crawler(crawler):
                            try:
                                if hasattr(crawler, 'close'):
                                    crawler.close()
                                    logger.info("VzanCrawler: Browser closed in creation thread")
                            except Exception as e:
                                logger.warning(f"VzanCrawler: Error closing crawler: {e}")
                                # 如果关闭失败，尝试进程级别清理
                                self._force_cleanup_browser_processes()

                        # 在同一线程池中执行关闭操作
                        future = executor_to_close.submit(_close_crawler, crawler_to_close)
                        future.result(timeout=10)  # 等待关闭完成
                        logger.info("VzanCrawler: Browser closed via executor")
                    except Exception as e:
                        logger.warning(f"VzanCrawler: Failed to close via executor: {e}")
                        # 兜底：尝试直接关闭
                        try:
                            crawler_to_close.close()
                            logger.info("VzanCrawler: Browser closed directly (fallback)")
                        except Exception as e2:
                            logger.warning(f"VzanCrawler: Direct close also failed: {e2}")
                            # 最后兜底：进程级别清理
                            self._force_cleanup_browser_processes()
                    finally:
                        # 关闭线程池
                        if executor_to_close:
                            executor_to_close.shutdown(wait=True)
                            self._executor = None
                else:
                    # 如果没有线程池引用，尝试直接关闭
                    logger.warning("VzanCrawler: No executor reference, trying direct close")
                    try:
                        crawler_to_close.close()
                        logger.info("VzanCrawler: Browser closed directly")
                    except Exception as e:
                        logger.warning(f"VzanCrawler: Direct close failed: {e}")
                        # 兜底：进程级别清理
                        self._force_cleanup_browser_processes()
        except Exception as e:
            logger.warning(f"VzanCrawler: Failed to close browser in close(): {e}")
            # 兜底：进程级别清理
            self._force_cleanup_browser_processes()
        finally:
            self.crawler = None
            # 确保线程池被关闭
            if self._executor:
                try:
                    self._executor.shutdown(wait=False)
                except:
                    pass
                self._executor = None

    def _force_cleanup_browser_processes(self):
        """强制清理浏览器进程（兜底方案）"""
        try:
            import psutil
            cleaned_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # 检查是否是 Playwright 启动的 Chromium 进程
                    if 'chromium' in proc.info['name'].lower() and '--remote-debugging-port' in cmdline:
                        proc.terminate()
                        cleaned_count += 1
                        logger.info(f"VzanCrawler: Terminated browser process {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            if cleaned_count > 0:
                logger.info(f"VzanCrawler: Cleaned up {cleaned_count} browser processes")
        except ImportError:
            logger.warning("VzanCrawler: psutil not available, cannot cleanup browser processes")
        except Exception as e:
            logger.warning(f"VzanCrawler: Failed to cleanup browser processes: {e}")



    def validate_config(self) -> bool:
        """
        验证配置
        
        Returns:
            bool: 配置是否有效
        """
        if not all([self.token, self.cookie]):
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
            self._ensure_crawler()  # 首次使用时初始化
            # 验证配置
            if not self.validate_config():
                raise CrawlerConfigError("VzanCrawler配置无效：缺少username, password或token")
            
            logger.info("VzanCrawler: Starting crawl")
            
            # 调用已有爬虫的核心方法
            self.crawler.clear_db_data()
            self.crawler.parse_all_liveroomlist_data(config)
            
            logger.info("VzanCrawler: Crawl completed, starting CSV column conversion")
            
            # ⚠️ 重要：转换CSV列名（中文 → 英文）
            # 必须在返回前完成，确保导入模块能正确读取
            csv_file = getattr(self.crawler, 'liveroom_list_savefile', None)
            incremental_file = getattr(self.crawler, 'liveroom_list_savefile_inc', None)
            failed_file = getattr(self.crawler, 'failed_liveroomlist_url', None)

            # 先处理增量文件（优先）
            if incremental_file and os.path.exists(incremental_file):
                self._convert_csv_columns(incremental_file)
                logger.info(f"VzanCrawler: Incremental CSV converted - {incremental_file}")
            
            # 再处理全量文件（如果存在的话）
            if csv_file and os.path.exists(csv_file):
                self._convert_csv_columns(csv_file)
                logger.info(f"VzanCrawler: Main CSV converted - {csv_file}")
            
            logger.info("VzanCrawler: CSV conversion completed, extracting file paths")
            
            # 统计增量文件行数
            incremental_rows = self._count_csv_rows(incremental_file) if (incremental_file and os.path.exists(incremental_file)) else 0

            # 基于 SQLite 统计总数与失败数（优先）。如失败则回退到 CSV 文本统计以保证健壮性
            db_file = getattr(self.crawler, 'db_file', None)
            total_rows, failed_rows = self._count_sqlite_stats(db_file)

            # 如 SQLite 不可用且存在全量/失败文件，可回退计数
            if total_rows is None:
                total_rows = self._count_csv_rows(csv_file) if (csv_file and os.path.exists(csv_file)) else 0
            if failed_rows is None:
                failed_rows = self._count_csv_rows(failed_file) if (failed_file and os.path.exists(failed_file)) else 0
            
            result = {
                "csv_file": csv_file if (csv_file and os.path.exists(csv_file)) else None,
                "incremental_file": incremental_file if (incremental_file and os.path.exists(incremental_file)) else None,
                "failed_file": failed_file if (failed_file and os.path.exists(failed_file)) else None,
                "total_rows": total_rows,
                "incremental_rows": incremental_rows,
                "failed_rows": failed_rows
            }

            # 可选扩展字段
            if db_file and os.path.exists(db_file):
                result["db_file"] = db_file
            
            logger.info(
                f"VzanCrawler: Crawl result - "
                f"total: {total_rows}, incremental: {incremental_rows}, failed: {failed_rows}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"VzanCrawler: Crawl failed - {str(e)}", exc_info=True)
            raise CrawlerError(f"爬取失败: {str(e)}")
        
        finally:
            # ⚠️ 注意：不在这里关闭浏览器，由 close() 方法统一处理
            # 因为 Playwright 对象在线程中创建，在主线程中关闭会有线程切换错误
            # 浏览器资源会在 DownloadService 调用 close() 时统一关闭
            pass

    def _count_sqlite_stats(self, db_file: str):
        """
        从 SQLite 统计 total_rows 与 failed_rows。
        返回 (total_rows, failed_rows)，如果统计失败则任意一项为 None。
        """
        try:
            if not db_file or not os.path.exists(db_file):
                return None, None
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM liversoms")
            total = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM liversoms WHERE (video_url IS NULL OR video_url = '')")
            failed = cur.fetchone()[0] or 0
            conn.close()
            return int(total), int(failed)
        except Exception as e:
            logger.error(f"VzanCrawler: SQLite 统计失败 - {str(e)}")
            return None, None
    
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

