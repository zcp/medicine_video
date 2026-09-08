import shutil
import tempfile
from sys import prefix

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import json
import csv
import os
import sqlite3
from datetime import datetime


class DuanShuCrawler_vzan:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)  # 设置为False可以看到浏览器操作
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.liveroom_list_url = "https://live-liveapi.vzan.com/api/v1/topic/get_topicdatas"
        self.liveroom_url_prefix = "https://inter.dayilive.com/live/page/"
        self.topic_url_prefix = "https://live-play.vzan.com/api/topic/topic_config?isPcBrowser=true&topicId="

        self.liveroomlist_batchsize = 100
        self.liveroom_details_batchsize = 500
        self.timeout = 10

        # 使用当前项目目录作为保存路径
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(current_dir, 'vzan_crawler')

        # 所有文件都放在项目目录下的vzan_crawler文件夹
        # ⚠️ 阶段1-2: 添加数据库文件路径
        self.db_file = os.path.join(self.temp_dir, "vzan_crawler.db")
        self.liveroom_details_savefile = os.path.join(self.temp_dir, "liveroom_elements_vzan.csv")
        self.liveroom_watchers_savefile_prefix = "liveroom_watchers_vzan"
        self.liveroom_watchers_savedir = os.path.join(self.temp_dir, "watchers_vzan")

        # 用于记录每次爬取时获取的新增直播间id， 第一次爬取将获取所有的直播间id
        self.liveroom_list_savefile_inc = os.path.join(self.temp_dir, "liveroomlist_inc_vzan_backup.csv")
        self.liveroom_details_savefile_inc = os.path.join(self.temp_dir, "liveroomlist_elements_inc_vzan.csv")

        self.failed_liveroomlist_url = os.path.join(self.temp_dir, 'failed_liveroomlist_urls_vzan.txt')
        self.failed_liveroomdetails_url = os.path.join(self.temp_dir, 'failed_liveroomdetails_urls_vzan.txt')
        self.failed_liveroom_watchers_url = os.path.join(self.temp_dir, 'failed_watchers_urls_vzan.txt')

        # 初始化logger为None
        # 设置日志
        self.logger = None
        self.log_file = None

        self.create_storage()
        self.setup_logging()
        # ⚠️ 阶段1-2: 在 setup_logging() 之后调用 setup_database()
        self.setup_database()

    def create_storage(self):
        # 创建数据存储文件夹
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            print(f"创建数据存储文件夹: {self.temp_dir}")

        if not os.path.exists(self.liveroom_watchers_savedir):
            os.makedirs(self.liveroom_watchers_savedir)
            print(f"创建watchers文件夹: {self.liveroom_watchers_savedir}")

    def setup_logging(self):
        """配置日志系统，日志文件保存在项目目录下"""
        import logging
        from datetime import datetime
        import os

        # 生成日志文件名
        log_filename = f'vzan_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        log_file = os.path.join(self.temp_dir, log_filename)

        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__)
        # print(f"日志文件路径: {log_file}")

        # 保存日志文件路径，方便后续查看
        self.log_file = log_file

    def normalize_url(self, url):
        """
        标准化 URL：去除空格、多余斜杠、排序查询参数、去除锚点等。
        保证所有 URL 格式一致，避免因不同格式的 URL 导致重复存储或重复下载。
        
        :param url: 待标准化的 URL
        :return: 标准化后的 URL
        """
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

        # 处理空值或无效输入
        if not url or not isinstance(url, str):
            return url if url else ""

        # 去除 URL 中的空格
        url = url.strip()
        
        if not url:
            return ""

        try:
            # 解析 URL
            parsed_url = urlparse(url)

            # 去除末尾斜杠
            path = parsed_url.path.rstrip('/')

            # 对查询参数进行排序
            query = parsed_url.query
            if query:
                # 使用 parse_qsl 解析查询参数，返回 [(key, value), ...] 格式
                query_params = parse_qsl(query)
                # 按 key 排序，然后按 value 排序（如果 key 相同）
                sorted_params = sorted(query_params, key=lambda x: (x[0], x[1] or ''))
                sorted_query = urlencode(sorted_params)
            else:
                sorted_query = ""

            # 去除锚点（fragment）
            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                path,
                parsed_url.params,
                sorted_query,
                ''  # fragment 设为空字符串
            ))

            return new_url
        except Exception as e:
            # 如果解析失败，返回原 URL
            return url

    def setup_database(self):
        """
        ⚠️ 阶段1-3: 新增 setup_database 函数
        连接到数据库并创建表
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            
            # 连接到数据库
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # ⚠️ 创建 liversoms 表（注意表名是 liversoms，不是 liverooms）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS liversoms (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    status INTEGER,
                    isOnShelf INTEGER,
                    addtime TEXT,
                    starttime TEXT,
                    zbId TEXT,
                    liveType TEXT,
                    viewCount INTEGER,
                    videosrc TEXT,
                    liveroom_url TEXT,
                    video_url TEXT,
                    cover_url TEXT,
                    original_playback_url TEXT,
                    edited_playback_url TEXT,
                    enc_tpid TEXT,
                    error_reason TEXT
                )
            ''')
            
            # ⚠️ 创建 failed_pages 表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_pages (
                    page_url TEXT PRIMARY KEY
                )
            ''')
            
            # ⚠️ 为 starttime 创建索引（便于按时间筛选）
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_liversoms_starttime ON liversoms (starttime);')
            
            # ⚠️ 创建复合唯一索引实现除重（基于 zbId + id + video_url）
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_liveroom_video 
                ON liversoms(zbId, id, video_url);
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"数据库初始化完成: {self.db_file}")
            
        except Exception as e:
            self.logger.error(f"初始化数据库时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def load_state_from_db(self):
        """
        ⚠️ 阶段1-4: 新增 load_state_from_db 函数
        从数据库中加载状态信息
        
        Returns:
            tuple: (successful_ids, failed_ids, latest_success_time, pages_to_retry)
                - successful_ids: 爬取成功的直播间ID集合（有video_url）
                - failed_ids: 爬取失败的直播间ID集合（video_url为空）
                - latest_success_time: 最新成功爬取的时间（基于starttime字段）
                - pages_to_retry: 需要重试的页面URL列表
        """
        try:
            successful_ids = set()
            failed_ids = set()
            latest_success_time = None
            pages_to_retry = []
            
            if not os.path.exists(self.db_file):
                self.logger.info("数据库文件不存在，返回空状态")
                return successful_ids, failed_ids, latest_success_time, pages_to_retry
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # ⚠️ 填充 successful_ids：有 video_url 的记录
            cursor.execute('''
                SELECT id FROM liversoms
                WHERE video_url IS NOT NULL AND video_url != ''
            ''')
            successful_ids = set(row[0] for row in cursor.fetchall())
            
            # ⚠️ 填充 failed_ids（ID 级失败）：video_url 为空的记录
            cursor.execute('''
                SELECT id FROM liversoms
                WHERE (video_url IS NULL OR video_url = '')
            ''')
            failed_ids = set(row[0] for row in cursor.fetchall())
            
            # ⚠️ 获取 latest_success_time（时间锚点）：基于 starttime 字段
            cursor.execute('''
                SELECT MAX(starttime) FROM liversoms
                WHERE video_url IS NOT NULL AND video_url != ''
            ''')
            result = cursor.fetchone()
            if result and result[0]:
                latest_success_time = result[0]
            
            # ⚠️ 填充 pages_to_retry（Page 级失败）
            cursor.execute('SELECT page_url FROM failed_pages')
            pages_to_retry = [row[0] for row in cursor.fetchall()]
            
            # ⚠️ 添加详细日志，查看 failed_pages 表的内容
            if pages_to_retry:
                self.logger.info(f"从 failed_pages 表加载待重试页面: {pages_to_retry}")
            else:
                self.logger.info("failed_pages 表为空，没有待重试页面")
            
            # ⚠️ 读取完 pages_to_retry 后，删除 failed_pages 表中的所有记录
            # 这样本轮结束时只会写入仍然失败的页面
            if pages_to_retry:
                cursor.execute('DELETE FROM failed_pages')
                conn.commit()
                self.logger.info(f"已从 failed_pages 表删除 {len(pages_to_retry)} 条记录，准备重试")
            
            conn.close()
            
            self.logger.info(
                f"从数据库加载状态: 成功={len(successful_ids)}, 失败={len(failed_ids)}, "
                f"最新成功时间={latest_success_time}, 待重试页面={len(pages_to_retry)}"
            )
            
            return successful_ids, failed_ids, latest_success_time, pages_to_retry
            
        except Exception as e:
            self.logger.error(f"从数据库加载状态时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return set(), set(), None, []

    def save_single_to_db(self, live_info):
        """
        ⚠️ 阶段2-1: 新增 save_single_to_db 函数
        将单条数据写入SQLite数据库
        
        Args:
            live_info (dict): 直播间信息字典
        """
        try:
            if not live_info:
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 标准化所有URL字段
            url_fields = ['video_url', 'cover_url', 'liveroom_url', 'original_playback_url', 'edited_playback_url', 'videosrc']
            for field in url_fields:
                if field in live_info and live_info[field]:
                    live_info[field] = self.normalize_url(live_info[field])
            
            # 使用 INSERT OR REPLACE 写入数据
            cursor.execute('''
                INSERT OR REPLACE INTO liversoms (
                    id, title, status, isOnShelf, addtime, starttime, zbId, liveType,
                    viewCount, videosrc, liveroom_url, video_url, cover_url,
                    original_playback_url, edited_playback_url, enc_tpid, error_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(live_info.get('id', '')),
                live_info.get('title', ''),
                live_info.get('status', ''),
                1 if live_info.get('isOnShelf', False) else 0,
                live_info.get('addtime', ''),
                live_info.get('starttime', ''),  # ⚠️ 使用 starttime 作为时间锚点
                live_info.get('zbId', ''),
                live_info.get('liveType', ''),
                live_info.get('viewCount', 0),
                live_info.get('videosrc', ''),
                live_info.get('liveroom_url', ''),
                live_info.get('video_url', ''),  # ⚠️ 使用 video_url 判断成功/失败
                live_info.get('cover_url', ''),
                live_info.get('original_playback_url', ''),
                live_info.get('edited_playback_url', ''),
                live_info.get('enc_tpid', ''),
                live_info.get('error_reason', '')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"保存单条数据到数据库时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def load_failed_ids_from_db(self):
        """
        ⚠️ 阶段2-3: 新增 load_failed_ids_from_db 函数（循环3使用）
        从数据库中加载失败的ID列表
        
        Returns:
            set: 失败的ID集合
        """
        try:
            failed_ids = set()
            
            if not os.path.exists(self.db_file):
                return failed_ids
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM liversoms
                WHERE (video_url IS NULL OR video_url = '')
            ''')
            failed_ids = set(row[0] for row in cursor.fetchall())
            
            conn.close()
            
            self.logger.info(f"从数据库加载失败ID: {len(failed_ids)} 个")
            
            return failed_ids
            
        except Exception as e:
            self.logger.error(f"从数据库加载失败ID时出错: {str(e)}")
            return set()

    def crawl_single_item(self, item, total_count=0):
        """
        ⚠️ 阶段2: 新增 crawl_single_item 函数
        爬取单个直播间项目的详细信息
        
        Args:
            item (dict): API返回的直播间基本信息
            total_count (int): 总数据量
            
        Returns:
            tuple: (status, live_info)
                - status: "success" 或 "failed"
                - live_info: 直播间信息字典
        """
        try:
            live_info = {
                'count': total_count,
                'id': str(item.get('id', '')),
                'title': item.get('title', ''),
                'status': item.get('status', ''),
                'isOnShelf': item.get('isOnShelf', False),
                'addtime': item.get('addtime', ''),
                'starttime': item.get('starttime', ''),  # ⚠️ 时间锚点字段
                'zbId': item.get('zbId', ''),
                'liveType': item.get('liveType', ''),
                'viewCount': item.get('viewcts', 0),
                'videosrc': item.get('videosrc', ''),
            }
            live_info['liveroom_url'] = self.liveroom_url_prefix + str(live_info['id'])

            # 初始化URL字段
            live_info['enc_tpid'] = ""
            live_info['video_url'] = ""
            live_info['cover_url'] = ""

            # 判断直播状态：status: -1=未开始, 0=已结束, 1=直播中
            status_code = live_info.get('status', -1)

            # 对于未开始的直播，不需要获取播放URL
            if status_code == -1:
                self.logger.debug(f"直播间 {live_info['id']} 未开始（status=-1），跳过播放URL获取")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                # ⚠️ 如果 videosrc 为空，也算失败
                if not live_info['video_url']:
                    live_info['error_reason'] = "未开始的直播且无videosrc"
                    return "failed", live_info
                live_info['error_reason'] = ""
                return "success", live_info

            # 对于直播中或已结束的直播，尝试获取播放URL
            # 获取topic配置
            topic_url = self.topic_url_prefix + str(live_info['id'])
            try:
                response = requests.get(topic_url, timeout=self.timeout)
                response.raise_for_status()
            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                self.logger.warning(f"获取topic配置失败，直播间ID: {live_info['id']}, 使用videosrc")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                # ⚠️ 如果 videosrc 为空，也算失败
                if not live_info['video_url']:
                    live_info['error_reason'] = "无法获取topic配置且无videosrc"
                    return "failed", live_info
                live_info['error_reason'] = ""
                return "success", live_info

            if response.text is None:
                self.logger.warning(f"获取topic配置响应为空，直播间ID: {live_info['id']}, 使用videosrc")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                # ⚠️ 如果 videosrc 为空，也算失败
                if not live_info['video_url']:
                    live_info['error_reason'] = "topic配置响应为空且无videosrc"
                    return "failed", live_info
                live_info['error_reason'] = ""
                return "success", live_info

            # 提取enc_tpid
            enc_tpid = self.extract_enc_tpid(response.text)
            if not enc_tpid:
                self.logger.warning(f"提取enc_tpid失败，直播间ID: {live_info['id']}, 使用videosrc")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                live_info['enc_tpid'] = ""

                # 即使没有enc_tpid，对于已结束的直播仍然尝试获取回放URL
                live_info['original_playback_url'] = ""
                live_info['edited_playback_url'] = ""
                if status_code == 0:  # 已结束的直播
                    try:
                        self.logger.info(f"直播间 {live_info['id']} 已结束（无enc_tpid），尝试获取回放URL")
                        cookie = getattr(self, 'cookie', None)
                        original_url, edited_url = self.get_playback_download_urls(live_info['id'], cookie)
                        live_info['original_playback_url'] = original_url
                        live_info['edited_playback_url'] = edited_url
                        if original_url or edited_url:
                            self.logger.info(f"直播间 {live_info['id']} 成功获取回放URL")
                            # ⚠️ 有回放URL也算成功，设置 video_url
                            live_info['video_url'] = original_url or edited_url
                            live_info['error_reason'] = ""
                            return "success", live_info
                    except Exception as e:
                        self.logger.warning(f"获取回放URL失败: {str(e)}")

                live_info['error_reason'] = "无法获取video_url或回放URL"
                # ⚠️ 没有 video_url 也没有回放URL，返回 failed
                return "failed", live_info

            live_info['enc_tpid'] = enc_tpid

            # 获取视频配置
            video_url = f"https://live-play.vzan.com/api/topic/video_config?tpId={enc_tpid}&domain=inter.dayilive.com&agentId="
            try:
                response = requests.get(video_url, timeout=self.timeout)
                response.raise_for_status()
            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                self.logger.warning(f"获取视频配置失败，直播间ID: {live_info['id']}, 使用videosrc")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                # ⚠️ 如果 videosrc 为空，也算失败
                if not live_info['video_url']:
                    live_info['error_reason'] = "无法获取视频配置且无videosrc"
                    return "failed", live_info
                live_info['error_reason'] = ""
                return "success", live_info

            if response.text is None:
                self.logger.warning(f"获取视频配置响应为空，直播间ID: {live_info['id']}, 使用videosrc")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                # ⚠️ 如果 videosrc 为空，也算失败
                if not live_info['video_url']:
                    live_info['error_reason'] = "视频配置响应为空且无videosrc"
                    return "failed", live_info
                live_info['error_reason'] = ""
                return "success", live_info

            # 提取play_url
            (play_url, cover_url) = self.extract_play_url(response.text)
            if not play_url:
                self.logger.warning(f"提取play_url失败，直播间ID: {live_info['id']}, 使用videosrc")
                videosrc = live_info.get('videosrc', '')
                live_info['video_url'] = videosrc if videosrc else ''
                live_info['cover_url'] = item.get('topiccover', '')
                # ⚠️ 如果 videosrc 为空，也算失败
                if not live_info['video_url']:
                    live_info['error_reason'] = "无法提取play_url且无videosrc"
                    return "failed", live_info
                live_info['error_reason'] = ""
                return "success", live_info

            live_info['video_url'] = play_url
            live_info['cover_url'] = cover_url

            # 获取回放下载URL（仅对已结束的直播）
            live_info['original_playback_url'] = ""
            live_info['edited_playback_url'] = ""

            if status_code == 0:  # 已结束的直播
                try:
                    self.logger.info(f"直播间 {live_info['id']} 已结束，尝试获取回放URL")
                    cookie = getattr(self, 'cookie', None)
                    original_url, edited_url = self.get_playback_download_urls(live_info['id'], cookie)
                    live_info['original_playback_url'] = original_url
                    live_info['edited_playback_url'] = edited_url
                    # ⚠️ 如果获取到回放URL，可以保留，但不覆盖已有的 video_url（play_url优先）
                    if original_url or edited_url:
                        self.logger.info(f"直播间 {live_info['id']} 成功获取回放URL")
                except Exception as e:
                    self.logger.warning(f"获取回放URL失败: {str(e)}")

            # ⚠️ 确保 video_url 有值才算成功
            if not live_info.get('video_url'):
                live_info['error_reason'] = "无法获取video_url"
                return "failed", live_info

            live_info['error_reason'] = ""
            return "success", live_info

        except Exception as e:
            self.logger.error(f"爬取单个直播间时出错，直播间ID: {item.get('id', 'unknown')}, 错误: {str(e)}")
            live_info = {
                'id': str(item.get('id', '')),
                'title': item.get('title', ''),
                'starttime': item.get('starttime', ''),
                'video_url': '',
                'error_reason': f"处理数据时出错: {str(e)}"
            }
            return "failed", live_info

    def crawl_single_item_by_id(self, item_id, token=None):
        """
        ⚠️ 阶段2-3: 新增 crawl_single_item_by_id 函数（循环3使用）
        根据ID爬取单个直播间的详细信息
        
        Args:
            item_id (str): 直播间ID
            token (str): 认证token
            
        Returns:
            tuple: (status, live_info)
        """
        try:
            # ⚠️ 需要先从API获取该ID的基本信息
            # 这里简化处理，假设可以通过某个API获取
            # 实际可能需要遍历列表页找到对应的item
            # 为了简化，这里直接返回失败，实际实现时可以根据API调整
            self.logger.warning(f"crawl_single_item_by_id 未完全实现，ID: {item_id}")
            live_info = {
                'id': str(item_id),
                'video_url': '',
                'error_reason': '通过ID直接爬取功能未完全实现'
            }
            return "failed", live_info
            
        except Exception as e:
            self.logger.error(f"通过ID爬取直播间时出错，ID: {item_id}, 错误: {str(e)}")
            live_info = {
                'id': str(item_id),
                'video_url': '',
                'error_reason': f"处理数据时出错: {str(e)}"
            }
            return "failed", live_info

    def process_page_items(self, item_list, successful_ids, failed_ids, latest_success_time,
                          inc_data_for_this_run, inc_ids_processed, total_count=0):
        """
        ⚠️ 阶段2: 新增 process_page_items 函数
        处理页面中的所有item，实现页面级停止逻辑
        
        Args:
            item_list (list): 页面中的item列表
            successful_ids (set): 已成功的ID集合
            failed_ids (set): 已失败的ID集合
            latest_success_time (str): 最新成功时间
            inc_data_for_this_run (list): 本轮增量数据列表
            inc_ids_processed (set): 本轮已处理的ID集合（去重）
            total_count (int): 总数据量
            
        Returns:
            bool: 是否整页都是旧数据（页面级停止标志）
        """
        try:
            # ⚠️ 页面级停止判断：整页全部是旧数据且没有需要处理的ID
            page_is_entirely_old = True
            items_to_crawl = []

            # ⚠️ 第一遍遍历：筛选需要爬取的item（页内只用continue，不用break）
            for item in item_list:
                item_id = str(item.get("id", "")).strip()
                item_starttime = str(item.get("starttime", "")).strip()  # ⚠️ 时间锚点字段统一用 starttime

                # 决策 A：跳过已知 ID（成功或失败都有记录）
                if item_id in successful_ids or item_id in failed_ids:
                    continue

                # 决策 B：时间早于 latest_success_time 的旧数据
                if latest_success_time and item_starttime and item_starttime < latest_success_time:
                    # 旧数据，可以跳过，但不能 break
                    continue

                # 决策 C：需要处理的增量或失败补爬数据
                page_is_entirely_old = False
                items_to_crawl.append(item)

            # ⚠️ 第二遍遍历：实际爬取需要处理的item
            for item in items_to_crawl:
                status, live_info = self.crawl_single_item(item, total_count)
                
                # 写入数据库（INSERT OR REPLACE）
                self.save_single_to_db(live_info)
                
                # ⚠️ 只对成功数据写入本轮 inc，并按 ID 去重
                if status == "success":
                    item_id = str(live_info.get("id", "")).strip()
                    if item_id and item_id not in inc_ids_processed:
                        inc_data_for_this_run.append(live_info)
                        inc_ids_processed.add(item_id)

            # ⚠️ 返回页面级停止标志
            return page_is_entirely_old

        except Exception as e:
            self.logger.error(f"处理页面items时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def get_liveroom_list(self, authorization_token, page=1, psize=10, state=-2, keytype=1, keyword="", tag=0,
                          livescene=-1, typeid=-1, types=-1, chanid=0, isOnShelf=-1, isHQOut=0, isGHHQOut=0,
                          starttime="", endtime=""):
        """
        直接调用API获取直播间列表数据

        Args:
            authorization_token (str): JWT token
            page (int): 页码，默认1
            psize (int): 每页数量，默认10
            state (int): 状态，-2表示全部，默认-2
            keytype (int): 关键词类型，默认1
            keyword (str): 搜索关键词，默认空
            tag (int): 标签，默认0
            livescene (int): 直播场景，默认-1
            typeid (int): 类型ID，默认-1
            types (int): 类型，默认-1
            chanid (int): 频道ID，默认0
            isOnShelf (int): 是否上架，默认-1
            isHQOut (int): 是否高清，默认0
            isGHHQOut (int): 是否更高清，默认0
            starttime (str): 开始时间，默认空
            endtime (str): 结束时间，默认空

        Returns:
            dict: API响应数据
        """
        try:
            import requests
            import json

            self.logger.info(f"正在获取第{page}页数据...")

            # 准备请求头
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-US,en;q=0.9',
                'admin-token': 'undefined',
                'appcode': 'agent_setting',
                'authorization': f'Bearer {authorization_token}',
                'content-type': 'application/json;charset=UTF-8',
                'generalizeshopid': '0',
                'lid': '11749549',
                'origin': 'https://live.vzan.com',
                'referer': 'https://live.vzan.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                'zbid': '11749549'
            }

            # 准备请求数据
            data = {
                "keyword": keyword,
                "keytype": keytype,
                "state": state,
                "psize": psize,
                "tag": tag,
                "page": page,
                "livescene": livescene,
                "typeid": typeid,
                "types": types,
                "chanid": chanid,
                "isOnShelf": isOnShelf,
                "isHQOut": isHQOut,
                "isGHHQOut": isGHHQOut,
                "starttime": starttime,
                "endtime": endtime
            }

            # 发送请求
            url = self.liveroom_list_url
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout)

            # 检查响应状态
            if response.status_code == 200:

                response_json = response.json()
                # --- 新增的健壮性检查 ---
                # 检查API返回的业务逻辑是否成功
                # 错误日志显示 token 过期时 dataObj 为 None 且 code 为 -1
                if response_json.get('dataObj') is None or response_json.get('code') == -1:
                    api_msg = response_json.get('msg', 'API返回了空数据或未知错误')
                    self.logger.error(f"API请求逻辑失败 (第{page}页): {api_msg}")
                    return None  # 返回None，与HTTP 4xx/5xx错误保持一致
                # --- 检查结束 ---
                self.logger.info(f"成功获取第{page}页数据")
                return response.json()
            else:
                self.logger.error(f"请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"获取数据时出错: {str(e)}")
            return None

    def request_page_by_url(self, page_url, token):
        """
        ⚠️ 阶段2-1: 新增 request_page_by_url 函数（循环1使用）
        根据页面URL或参数重新请求页面数据
        
        Args:
            page_url (str): 页面URL或标识（可以是页码或其他标识）
            token (str): 认证token
            
        Returns:
            dict: API响应数据
        """
        try:
            # ⚠️ page_url 可能是页码字符串，需要解析
            # 这里假设 page_url 就是页码，实际可能需要根据你的实现调整
            try:
                page = int(page_url)
            except ValueError:
                # 如果不是数字，尝试从URL中提取页码
                # 这里简化处理，假设 page_url 就是页码字符串
                self.logger.warning(f"无法解析页面URL: {page_url}，使用默认页码1")
                page = 1
            
            return self.get_liveroom_list(
                authorization_token=token,
                page=page,
                psize=10
            )
            
        except Exception as e:
            self.logger.error(f"请求页面失败，page_url: {page_url}, 错误: {str(e)}")
            return None

    def login(self, username, password):
        """登录短书"""
        try:
            self.logger.info("正在登录短书...")
            self.page.goto(self.liveroom_list_url)

            # 等待页面完全加载
            self.page.wait_for_load_state('networkidle')
            time.sleep(3)  # 等待页面完全加载

            # 等待登录表单加载
            self.logger.info("等待登录表单加载...")

            # 首先等待并点击"账号登录"按钮
            try:
                # 等待账号登录按钮出现
                self.logger.info("等待账号登录按钮出现...")

                # 使用JavaScript检查页面元素
                self.logger.info("检查页面元素...")
                page_content = self.page.content()
                self.logger.info(f"页面内容: {page_content[:500]}")  # 只打印前500个字符

                # 等待页面加载完成
                self.page.wait_for_load_state('domcontentloaded')
                time.sleep(2)

                # 尝试使用JavaScript点击账号登录按钮
                self.logger.info("尝试使用JavaScript点击账号登录按钮...")
                clicked = self.page.evaluate('''() => {
                     // 尝试多种方式查找账号登录按钮
                     const selectors = [
                         '.login-type-switch',
                         '.login-type',
                         '[data-type="account"]',
                         'span:contains("账号登录")',
                         'div:contains("账号登录")'
                     ];

                     for (const selector of selectors) {
                         const elements = document.querySelectorAll(selector);
                         for (const el of elements) {
                             if (el.textContent.includes('账号登录')) {
                                 el.click();
                                 return true;
                             }
                         }
                     }

                     // 如果上面的方法都失败，尝试遍历所有元素
                     const allElements = document.querySelectorAll('*');
                     for (const el of allElements) {
                         if (el.textContent && el.textContent.includes('账号登录')) {
                             el.click();
                             return true;
                         }
                     }

                     return false;
                 }''')

                if clicked:
                    self.logger.info("成功使用JavaScript点击账号登录按钮")
                else:
                    self.logger.error("无法找到账号登录按钮")
                    return False

                # 等待账号密码输入框出现
                self.logger.info("等待账号密码输入框出现...")
                time.sleep(2)  # 等待输入框出现

                # 使用JavaScript检查输入框是否存在
                input_exists = self.page.evaluate('''() => {
                     const textInput = document.querySelector('input[type="text"]');
                     const passwordInput = document.querySelector('input[type="password"]');
                     return textInput && passwordInput;
                 }''')

                if not input_exists:
                    self.logger.error("无法找到输入框")
                    return False

            except Exception as e:
                self.logger.error(f"切换到账号登录模式失败: {str(e)}")
                return False

            # 输入用户名和密码
            self.logger.info("正在输入用户名和密码...")
            try:
                # 使用JavaScript输入用户名和密码
                self.page.evaluate(f'''(username, password) => {{
                     const textInput = document.querySelector('input[type="text"]');
                     const passwordInput = document.querySelector('input[type="password"]');

                     if (textInput && passwordInput) {{
                         textInput.value = username;
                         passwordInput.value = password;

                         // 触发input事件
                         textInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                         passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));

                         return true;
                     }}
                     return false;
                 }}''', username, password)

                time.sleep(1)  # 等待输入完成

            except Exception as e:
                self.logger.error(f"输入用户名密码失败: {str(e)}")
                return False

            # 点击登录按钮
            self.logger.info("点击登录按钮...")
            try:
                # 使用JavaScript点击登录按钮
                login_clicked = self.page.evaluate('''() => {
                     const selectors = [
                         'button[type="submit"]',
                         '.login-btn',
                         'button:contains("登录")',
                         '[class*="login-btn"]'
                     ];

                     for (const selector of selectors) {
                         const elements = document.querySelectorAll(selector);
                         for (const el of elements) {
                             if (el.textContent.includes('登录')) {
                                 el.click();
                                 return true;
                             }
                         }
                     }

                     return false;
                 }''')

                if not login_clicked:
                    self.logger.error("无法点击登录按钮")
                    return False

                self.logger.info("成功点击登录按钮")

            except Exception as e:
                self.logger.error(f"点击登录按钮失败: {str(e)}")
                return False

            # 等待登录成功
            try:
                self.logger.info("等待登录成功...")
                # 使用JavaScript检查登录状态
                for _ in range(10):  # 最多等待10秒
                    is_logged_in = self.page.evaluate('''() => {
                         return document.querySelector('.user-avatar') !== null ||
                                document.querySelector('.user-info') !== null ||
                                document.querySelector('.avatar') !== null;
                     }''')

                    if is_logged_in:
                        self.logger.info("登录成功！")
                        return True

                    time.sleep(1)

                self.logger.error("登录超时")
                return False

            except Exception as e:
                self.logger.error(f"等待登录成功超时: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"登录过程出错: {str(e)}")
            return False

    def extract_enc_tpid(self, response_data):
        """
        从API响应数据中提取enc_tpid值

        Args:
            response_data (str/dict): API响应数据，可以是JSON字符串或字典

        Returns:
            str: enc_tpid值，如果提取失败则返回空字符串
        """
        try:
            self.logger.info("开始提取enc_tpid...")

            # 检查输入是否为None
            if response_data is None:
                self.logger.error("输入数据为None")
                return ""

            # 如果输入是字符串，尝试解析JSON
            if isinstance(response_data, str):
                try:
                    import json
                    response_data = json.loads(response_data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {str(e)}")
                    return ""
                except Exception as e:
                    self.logger.error(f"解析JSON时发生未知错误: {str(e)}")
                    return ""

            # 检查响应数据格式
            if not isinstance(response_data, dict):
                self.logger.error(f"响应数据格式不正确，不是字典类型，实际类型为: {type(response_data)}")
                return ""

            # 检查dataObj字段
            if 'dataObj' not in response_data:
                self.logger.error("响应数据中缺少dataObj字段")
                return ""

            # 获取dataObj
            data_obj = response_data['dataObj']

            # 检查dataObj是否为None
            if data_obj is None:
                self.logger.error("dataObj字段为None")
                return ""

            # 检查dataObj类型
            if not isinstance(data_obj, dict):
                self.logger.error(f"dataObj格式不正确，不是字典类型，实际类型为: {type(data_obj)}")
                return ""

            # 检查enc_tpid字段
            if 'enc_tpid' not in data_obj:
                self.logger.error("dataObj中缺少enc_tpid字段")
                return ""

            # 获取enc_tpid值
            enc_tpid = data_obj.get('enc_tpid')

            # 检查enc_tpid值是否为空
            if enc_tpid is None:
                self.logger.warning("enc_tpid值为None")
                return ""

            # 确保enc_tpid是字符串类型
            if not isinstance(enc_tpid, str):
                try:
                    enc_tpid = str(enc_tpid)
                except Exception as e:
                    self.logger.error(f"转换enc_tpid为字符串失败: {str(e)}")
                    return ""

            # 检查enc_tpid是否为空字符串
            if not enc_tpid.strip():
                self.logger.warning("enc_tpid值为空字符串")
                return ""

            self.logger.info(f"成功提取enc_tpid: {enc_tpid}")
            return enc_tpid

        except Exception as e:
            self.logger.error(f"提取enc_tpid时出错: {str(e)}")
            # 打印更详细的错误信息
            import traceback
            self.logger.error("详细错误信息:")
            self.logger.error(traceback.format_exc())
            return ""

    def get_playback_download_urls(self, topic_id, cookie=None):
        """
        获取回放视频下载URL（原始回放和剪辑回放）
        只有已结束的直播才有回放视频

        Args:
            topic_id: 直播间ID
            cookie: 登录Cookie（可选）

        Returns:
            tuple: (original_playback_url, edited_playback_url)
        """
        try:
            # 使用正确的API端点
            download_api = "https://live.vzan.com/liveajax/GetTopicPlayUrl"

            # 准备请求数据（根据cURL命令）
            data = {
                "zid": "11749549",  # zbid
                "tpid": str(topic_id)  # topicId
            }

            # 添加请求头（包含认证信息）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://live.vzan.com',
                'Referer': 'https://live.vzan.com/admin/index.html?zbid=11749549',
                # 关键认证头
                'authorization': f'Bearer {getattr(self, "token", "")}',
                'buid': '5Li4cj/JZBdD91TrIhrAVuRi7WdPpR9tZbXgp7SiUwhPJK4BaVRXIywjoOYYGjZT/+cCFSKIE+DRFkNvJZc0yw==',
                'lid': '11749549',
                'zbid': '11749549',
            }

            # 如果提供了Cookie，添加到请求头
            if cookie:
                headers['Cookie'] = cookie

            response = requests.post(download_api, data=data, headers=headers, timeout=self.timeout)

            self.logger.info(f"回放API响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"回放API响应: isok={result.get('isok')}, msg={result.get('Msg', '')}")

                if result.get('isok') and 'dataObj' in result:
                    dataObj = result['dataObj']
                    original_url = dataObj.get('oldurl', '')  # 原始回放URL
                    edited_url = dataObj.get('newurl', '')  # 剪辑回放URL

                    if original_url or edited_url:
                        self.logger.info(
                            f"直播间 {topic_id} 成功获取回放URL: 原始={bool(original_url)}, 剪辑={bool(edited_url)}")
                        return original_url, edited_url
                    else:
                        self.logger.warning(f"直播间 {topic_id} API返回成功但URL为空")
                else:
                    self.logger.warning(f"直播间 {topic_id} API返回失败或缺少dataObj: {result}")
            else:
                self.logger.warning(f"直播间 {topic_id} 回放API请求失败，状态码: {response.status_code}")

            return "", ""

        except Exception as e:
            self.logger.error(f"获取回放URL时出错，直播间ID: {topic_id}, 错误: {str(e)}")
            return "", ""

    def extract_play_url(self, response_data):
        """
        从API响应数据中提取play_url值
        play_url的重要性更强，对其检查更多，对cover_url只做基本检查，如果出错，赋值为空

        Args:
            response_data (str/dict): API响应数据，可以是JSON字符串或字典

        Returns:
            tuple: (play_url, cover_url)
        """
        try:
            self.logger.info("开始提取play_url和cover_url...")

            # 检查输入是否为None
            if response_data is None:
                self.logger.error("输入数据为None")
                return "", ""

            # 如果输入是字符串，尝试解析JSON
            if isinstance(response_data, str):
                try:
                    import json
                    response_data = json.loads(response_data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {str(e)}")
                    return "", ""
                except Exception as e:
                    self.logger.error(f"解析JSON时发生未知错误: {str(e)}")
                    return "", ""

            # 检查响应数据格式
            if not isinstance(response_data, dict):
                self.logger.error(f"响应数据格式不正确，不是字典类型，实际类型为: {type(response_data)}")
                return "", ""

            # 检查dataObj字段
            if 'dataObj' not in response_data:
                self.logger.error("响应数据中缺少dataObj字段")
                return "", ""

            # 获取dataObj
            data_obj = response_data['dataObj']

            # 检查dataObj是否为None
            if data_obj is None:
                self.logger.error("dataObj字段为None")
                return "", ""

            # 检查dataObj类型
            if not isinstance(data_obj, dict):
                self.logger.error(f"dataObj格式不正确，不是字典类型，实际类型为: {type(data_obj)}")
                return "", ""

            # 检查playUrl字段
            if 'playUrl' not in data_obj:
                self.logger.error("dataObj中缺少playUrl字段")
                return "", ""

            # 获取playUrl值
            play_url = data_obj.get('playUrl')

            # 检查playUrl值是否为空
            if play_url is None:
                self.logger.warning("playUrl值为None")
                return "", ""

            # 确保play_url是字符串类型
            if not isinstance(play_url, str):
                try:
                    play_url = str(play_url)
                except Exception as e:
                    self.logger.error(f"转换playUrl为字符串失败: {str(e)}")
                    return "", ""

            # 检查play_url是否为空字符串
            if not play_url.strip():
                self.logger.warning("playUrl值为空字符串")
                return "", ""

            # 验证URL格式
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(play_url)
                if not all([parsed_url.scheme, parsed_url.netloc]):
                    self.logger.error("playUrl格式不正确")
                    return "", ""
            except Exception as e:
                self.logger.error(f"验证URL格式时出错: {str(e)}")
                return "", ""

            self.logger.info(f"成功提取playUrl: {play_url}")

            cover_url = data_obj.get('cover')

            if cover_url is None or not cover_url.strip() or not isinstance(cover_url, str):
                cover_url = ""

            return (play_url, cover_url)

        except Exception as e:
            self.logger.error(f"提取playUrl时出错: {str(e)}")
            # 打印更详细的错误信息
            import traceback
            self.logger.error("详细错误信息:")
            self.logger.error(traceback.format_exc())
            return "", ""

    def save_liveroomlist_to_csv(self, live_data, filename=None, mode='w'):
        """
        ⚠️ 阶段3-3: 保留 save_liveroomlist_to_csv 函数，因为仍被 inc.csv 的生成所需要
        将直播数据保存到CSV文件

        Args:
            live_data (list): 直播数据列表
            filename (str): 文件名，如果为None则使用默认文件名
            mode (str): 写入模式，'w'为覆盖，'a'为追加

        Returns:
            str: 保存的文件路径，如果保存失败则返回None
        """
        try:
            if not filename:
                filename = self.liveroom_list_savefile_inc

            self.logger.info(f"开始保存数据到文件: {filename}")

            # 定义CSV文件的表头
            headers = [
                '直播间ID',
                '标题',
                '直播间url',
                '创建时间',
                '开始时间',
                '结束时间',
                '直播类型',
                '直播状态',
                '视频源URL',
                '播放url',
                '封面图片',
                '原始回放URL',
                '剪辑回放URL',
                '观看次数',
                'zbID',
                "enc_tpid",
                '直播间总数'
            ]

            # 检查文件是否存在
            file_exists = os.path.exists(filename)

            # 确保目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, mode, newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)

                # 如果是新文件或覆盖模式，写入表头
                if not file_exists or mode == 'w':
                    writer.writeheader()
                    self.logger.info("写入CSV表头")

                # 写入数据
                for item in live_data:
                    try:
                        row = {
                            '直播间ID': item.get('id', ''),
                            '标题': item.get('title', ''),
                            '直播间url': item.get('liveroom_url', ''),
                            '创建时间': item.get('addtime', ''),
                            '开始时间': item.get('starttime', ''),
                            '结束时间': "",
                            '直播类型': item.get('liveType', ''),  # 直播类型（具体含义未知）
                            '直播状态': item.get('status', ''),  # -1=未开始, 0=已结束, 1=直播中
                            '视频源URL': item.get('videosrc', ''),
                            "播放url": item.get('video_url', ''),
                            "封面图片": item.get('cover_url', ''),
                            "原始回放URL": item.get('original_playback_url', ''),
                            "剪辑回放URL": item.get('edited_playback_url', ''),
                            "观看次数": item.get('viewCount', 0),
                            'zbID': item.get('zbId', ''),
                            'enc_tpid': item.get('enc_tpid', ''),
                            '直播间总数': item.get('count', 0)
                        }
                        writer.writerow(row)
                    except Exception as e:
                        self.logger.error(f"写入单条数据时出错: {str(e)}")
                        continue

            self.logger.info(f"成功保存 {len(live_data)} 条数据到文件: {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"保存CSV文件时出错: {str(e)}")
            return None

    def wait_for_page_load(self, url, timeout=10000):
        """
        等待页面加载并获取内容

        Args:
            url (str): 要访问的URL
            timeout (int): 超时时间（毫秒）

        Returns:
            tuple: (html_content, success)
                - html_content: 页面内容
                - success: 是否成功加载
        """
        try:
            self.logger.info(f"正在访问页面: {url}")

            # 访问页面
            self.page.goto(url, wait_until='domcontentloaded')

            # 等待pre标签出现
            try:
                self.page.wait_for_selector('pre', timeout=timeout)
                # print("成功找到pre标签")
            except Exception as e:
                # print(f"等待pre标签超时: {str(e)}")
                try:
                    self.page.wait_for_load_state('networkidle', timeout=5000)
                    # print("网络请求已完成")
                except Exception as e:
                    self.logger.info(f"等待网络请求完成超时: {str(e)}")

            # 额外等待确保数据加载完成
            time.sleep(2)

            # 获取页面内容
            html_content = self.page.content()

            # 检查是否包含数据
            if 'pre' not in html_content:
                self.logger.info("页面未包含数据")
                return None, False

            return html_content, True

        except Exception as e:
            self.logger.info(f"加载页面时出错: {str(e)}")
            return None, False

    def parse_all_liveroomlist_data(self, config):
        """
        ⚠️ 阶段2-3 和 阶段3: 修改 parse_all_liveroomlist_data 函数
        实现三重循环策略：Page失败重试 → 增量爬取 → ID失败重试
        
        Args:
            config (dict): 配置信息，包含token和cookie
        """
        try:
            self.logger.info("开始获取直播间列表数据...")

            # 保存认证信息到实例变量，供get_playback_download_urls使用
            self.cookie = config.get('cookie', None)
            self.token = config.get('token', '')

            # ⚠️ 阶段1-4: 加载状态
            successful_ids, failed_ids, latest_success_time, pages_to_retry = self.load_state_from_db()

            # ⚠️ 阶段1-5: 初始化本轮运行的增量缓存
            inc_data_for_this_run = []  # 本轮成功数据（用于 inc CSV）
            inc_ids_processed = set()  # 本轮已写入 inc 的 ID 集合（去重）
            newly_failed_pages = []  # 本轮新产生的 Page 失败

            # ⚠️ 修复问题1：在API调用之前创建增量文件，确保即使API失败，文件也存在（至少包含表头）
            # ⚠️ 阶段3-2: 创建增量文件（提前创建，确保文件始终存在）
            try:
                self.save_liveroomlist_to_csv(
                    [],
                    filename=self.liveroom_list_savefile_inc,
                    mode='w'
                )
                self.logger.info(f"创建增量文件: {self.liveroom_list_savefile_inc}")
            except Exception as e:
                self.logger.error(f"创建增量文件失败: {str(e)}")
                raise Exception(f"无法创建增量文件: {str(e)}")

            # 获取第一页数据来确定总数
            token = config['token']
            first_page_data = self.get_liveroom_list(
                authorization_token=token,
                page=1,
                psize=10
            )

            # ⚠️ 修复问题2：当token/cookie错误时，抛出异常而不是静默返回
            # 检查API响应
            if not first_page_data:
                error_msg = "获取第一页数据失败：API返回为空，可能是token或cookie无效"
                self.logger.error(error_msg)
                raise Exception(error_msg)

            if not isinstance(first_page_data, dict):
                error_msg = f"获取第一页数据失败：API返回格式错误，期望dict类型，实际为{type(first_page_data)}，可能是token或cookie无效"
                self.logger.error(error_msg)
                raise Exception(error_msg)

            if 'dataObj' not in first_page_data:
                # 检查是否是token/cookie错误（code == -1）
                api_code = first_page_data.get('code', 0)
                api_msg = first_page_data.get('msg', '未知错误')
                if api_code == -1:
                    error_msg = f"API认证失败（code=-1）: {api_msg}，请检查token或cookie是否正确"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
                else:
                    error_msg = f"获取第一页数据失败：API响应中缺少dataObj字段，code={api_code}, msg={api_msg}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)

            # 获取总数
            total_count = first_page_data['dataObj'].get('count', 0)
            if total_count == 0:
                self.logger.warning("API返回的直播间总数为0，将创建空文件")
                # ⚠️ 注意：total_count为0时，不抛出异常，因为这是正常情况（可能真的没有数据）
                # 文件已经创建（包含表头），后续流程会正确处理空数据

            self.logger.info(f"总共有 {total_count} 个直播间")

            # 计算总页数
            page_size = 10
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

            # ⚠️ 阶段2: 循环1 - Page失败重试
            self.logger.info(f"[循环1检查] pages_to_retry 长度: {len(pages_to_retry)}, 内容: {pages_to_retry}")
            
            if pages_to_retry:
                self.logger.info(f"开始 [循环1：Page失败重试]，共 {len(pages_to_retry)} 个页面...")

                for page_url in pages_to_retry:
                    try:
                        # 重新请求这个 page_url
                        page_data = self.request_page_by_url(page_url, token)
                        
                        if not page_data or 'dataObj' not in page_data:
                            raise Exception("page_data 无效")
                        
                        item_list = page_data["dataObj"].get("list", [])
                        if not item_list:
                            continue
                        
                        # 使用统一的页面处理逻辑
                        self.process_page_items(
                            item_list=item_list,
                            successful_ids=successful_ids,
                            failed_ids=failed_ids,
                            latest_success_time=latest_success_time,
                            inc_data_for_this_run=inc_data_for_this_run,
                            inc_ids_processed=inc_ids_processed,
                            total_count=total_count
                        )
                        
                    except Exception as e:
                        # 本次运行仍然失败的页面，加入 newly_failed_pages
                        self.logger.error(f"重试页面失败，page_url: {page_url}, 错误: {str(e)}")
                        newly_failed_pages.append(page_url)
            else:
                self.logger.info("[循环1跳过] 没有待重试的页面，跳过循环1")

            # ⚠️ 阶段2: 循环2 - 增量爬取（带页面级停止）
            self.logger.info("开始 [循环2：增量爬取（带页面级停止）]...")

            stop_pagination = False
            page = 1
            
            #while not stop_pagination and page <= total_pages:
            while not stop_pagination and page <= 5:
                try:
                    # 构造当前页的请求标识（用于失败记录）
                    page_url = str(page)
                    
                    try:
                        page_data = self.get_liveroom_list(
                            authorization_token=token,
                            page=page,
                            psize=page_size
                        )
                        
                        if not page_data or 'dataObj' not in page_data:
                            raise Exception("page_data 无效")
                            
                    except Exception as e:
                        self.logger.error(f"获取分页URL (页码 {page}) 失败: {e}")
                        newly_failed_pages.append(page_url)
                        page += 1
                        continue

                    item_list = page_data["dataObj"].get("list", []) or []
                    
                    if not item_list:
                        self.logger.warning(f"第 {page} 页没有数据，停止爬取")
                        stop_pagination = True
                        break

                    # ⚠️ 关键逻辑：页面级停止、页内不提前 break
                    page_is_entirely_old = self.process_page_items(
                        item_list=item_list,
                        successful_ids=successful_ids,
                        failed_ids=failed_ids,
                        latest_success_time=latest_success_time,
                        inc_data_for_this_run=inc_data_for_this_run,
                        inc_ids_processed=inc_ids_processed,
                        total_count=total_count
                    )

                    # ⚠️ 页面级停止判断：整页全是旧数据，且已经有 latest_success_time 时，停止翻页
                    if page_is_entirely_old and latest_success_time:
                        self.logger.info(f"第 {page} 页的所有数据均早于时间锚点 {latest_success_time}，[循环2] 停止。")
                        stop_pagination = True

                    # 添加短暂延迟，避免请求过快
                    time.sleep(1)
                    
                    page += 1

                except Exception as e:
                    self.logger.error(f"处理第 {page} 页时出错: {str(e)}")
                    newly_failed_pages.append(str(page))
                    page += 1
                    continue

            # ⚠️ 阶段2: 循环3 - 失败ID重试
            self.logger.info("刷新失败ID列表，为[循环3]做准备...")
            failed_ids = self.load_failed_ids_from_db()  # 重新刷新失败ID列表

            if failed_ids:
                self.logger.info(f"开始 [循环3：ID失败重试]，共 {len(failed_ids)} 个项目...")

                for item_id in failed_ids:
                    # 如果本轮已经成功处理过（例如在循环1或循环2中成功了），则跳过
                    if item_id in inc_ids_processed:
                        continue

                    # ⚠️ 注意：crawl_single_item_by_id 需要实际实现
                    # 这里简化处理，实际可能需要通过API获取item信息
                    status, live_info = self.crawl_single_item_by_id(item_id, token)
                    self.save_single_to_db(live_info)

                    if status == "success":
                        if item_id not in inc_ids_processed:
                            inc_data_for_this_run.append(live_info)
                            inc_ids_processed.add(item_id)

            # ⚠️ 阶段3-1: 移除写入 liveroomlist_vzan_api.csv 的逻辑（已删除）
            # ⚠️ 阶段3-2: 保留写入增量文件的逻辑
            if inc_data_for_this_run:
                try:
                    self.save_liveroomlist_to_csv(
                        inc_data_for_this_run,
                        filename=self.liveroom_list_savefile_inc,
                        mode='w'
                    )
                    self.logger.info(f"成功保存 {len(inc_data_for_this_run)} 条增量数据到文件")
                except Exception as e:
                    self.logger.error(f"保存增量数据时出错: {str(e)}")

            # ⚠️ 阶段3-3: 写回 Page 级失败状态
            if newly_failed_pages:
                try:
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    cursor.executemany(
                        "INSERT OR IGNORE INTO failed_pages (page_url) VALUES (?)",
                        [(url,) for url in newly_failed_pages]
                    )
                    conn.commit()
                    conn.close()
                    self.logger.info(f"写回 {len(newly_failed_pages)} 个失败的页面到数据库")
                except Exception as e:
                    self.logger.error(f"写回失败页面时出错: {str(e)}")

            # 输出爬取统计信息
            self.logger.info(
                f"本次爬取完成，共发现 {len(inc_data_for_this_run)} 个新增或重爬成功的直播间"
            )

        except Exception as e:
            self.logger.error(f"获取直播间列表数据时出错: {str(e)}")
            # 打印更详细的错误信息
            import traceback
            self.logger.error("详细错误信息:")
            self.logger.error(traceback.format_exc())
            # ⚠️ 修复问题2：重新抛出异常，让上层能够捕获并正确处理
            raise

    def save_failed_urls(self, failed_urls, filename):
        """
        保存失败的URL到文件

        Args:
            failed_urls (list): 失败的URL列表
            filename (str): 保存的文件名
        """
        try:
            # 如果文件已存在，先读取现有数据
            existing_urls = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_urls = json.load(f)

            # 合并新的失败URL
            all_failed_urls = list(set(existing_urls + failed_urls))

            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_failed_urls, f, ensure_ascii=False, indent=4)

            self.logger.info(f"已保存 {len(failed_urls)} 个失败的URL到 {filename}")

        except Exception as e:
            self.logger.info(f"保存失败URL时出错: {str(e)}")

    def clean_old_files(self):
        """清理之前运行产生的文件"""
        try:
            import shutil

            # 先关闭所有日志处理器
            if self.logger:
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)

            # 需要清理的文件列表（不再包含 liveroom_list_savefile，因为已替换为数据库）
            files_to_clean = [
                self.liveroom_details_savefile,
                self.failed_liveroomlist_url,
                self.failed_liveroomdetails_url,
                self.failed_liveroom_watchers_url
            ]

            # 清理文件
            for file in files_to_clean:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        self.logger.info(f"已删除文件: {file}")
                    except Exception as e:
                        self.logger.info(f"删除文件 {file} 时出错: {str(e)}")

            # 清理watchers文件夹
            if os.path.exists(self.liveroom_watchers_savedir):
                try:
                    shutil.rmtree(self.liveroom_watchers_savedir)
                    self.logger.info(f"已删除文件夹: {self.liveroom_watchers_savedir}")
                except Exception as e:
                    self.logger.info(f"删除文件夹 {self.liveroom_watchers_savedir} 时出错: {str(e)}")

            self.logger.info("文件清理完成,再次创建存储文件夹为下一次运行")
            self.create_storage()
        except Exception as e:
            self.logger.info(f"清理文件时出错: {str(e)}")
        finally:
            # 重新设置日志
            self.setup_logging()

    def show_db_data(self, limit=100, show_failed_only=False):
        """
        显示SQLite数据库中的数据
        
        Args:
            limit (int): 最多显示多少条记录，默认100
            show_failed_only (bool): 是否只显示失败的记录，默认False
        """
        try:
            if not os.path.exists(self.db_file):
                print(f"数据库文件不存在: {self.db_file}")
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 查询数据
            if show_failed_only:
                query = '''
                    SELECT id, title, starttime, video_url, error_reason 
                    FROM liversoms 
                    WHERE (video_url IS NULL OR video_url = '')
                    ORDER BY starttime DESC
                    LIMIT ?
                '''
                print("\n" + "="*80)
                print("失败的直播间记录（video_url为空）:")
                print("="*80)
            else:
                query = '''
                    SELECT id, title, starttime, video_url, error_reason 
                    FROM liversoms 
                    ORDER BY starttime DESC
                    LIMIT ?
                '''
                print("\n" + "="*80)
                print("所有直播间记录:")
                print("="*80)
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            if not rows:
                print("没有数据")
            else:
                print(f"共 {len(rows)} 条记录（最多显示 {limit} 条）:\n")
                print(f"{'ID':<20} {'标题':<30} {'开始时间':<20} {'video_url':<10} {'错误原因':<20}")
                print("-"*80)
                
                for row in rows:
                    item_id, title, starttime, video_url, error_reason = row
                    title_short = (title[:27] + "...") if title and len(title) > 30 else (title or "")
                    video_status = "有" if video_url else "无"
                    error_short = (error_reason[:17] + "...") if error_reason and len(error_reason) > 20 else (error_reason or "")
                    print(f"{item_id:<20} {title_short:<30} {starttime or '':<20} {video_status:<10} {error_short:<20}")
            
            # 统计信息
            cursor.execute('SELECT COUNT(*) FROM liversoms')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM liversoms WHERE video_url IS NOT NULL AND video_url != ""')
            success_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM liversoms WHERE (video_url IS NULL OR video_url = "")')
            failed_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM failed_pages')
            failed_pages_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT MAX(starttime) FROM liversoms WHERE video_url IS NOT NULL AND video_url != ""')
            latest_time = cursor.fetchone()[0]
            
            # 显示 failed_pages 表的内容
            print("\n" + "="*80)
            print("failed_pages 表内容:")
            print("="*80)
            cursor.execute('SELECT page_url FROM failed_pages ORDER BY page_url')
            failed_pages_rows = cursor.fetchall()
            
            if not failed_pages_rows:
                print("没有失败页面记录")
            else:
                print(f"共 {len(failed_pages_rows)} 个失败页面:\n")
                print(f"{'页面URL/页码':<30}")
                print("-"*80)
                for row in failed_pages_rows:
                    page_url = row[0]
                    print(f"{page_url:<30}")
            
            print("\n" + "="*80)
            print("数据库统计信息:")
            print("="*80)
            print(f"总记录数: {total_count}")
            print(f"成功记录数: {success_count}")
            print(f"失败记录数: {failed_count}")
            print(f"失败页面数: {failed_pages_count}")
            print(f"最新成功时间: {latest_time or '无'}")
            print("="*80 + "\n")
            
            conn.close()
            
        except Exception as e:
            print(f"显示数据库数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def clear_db_data(self, table_name=None):
        """
        清空SQLite数据库中的数据
        
        Args:
            table_name (str): 要清空的表名，如果为None则清空所有表
                - "liversoms": 只清空 liversoms 表
                - "failed_pages": 只清空 failed_pages 表
                - None: 清空所有表
        """
        try:
            if not os.path.exists(self.db_file):
                print(f"数据库文件不存在: {self.db_file}")
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            if table_name == "liversoms":
                cursor.execute('DELETE FROM liversoms')
                print("已清空 liversoms 表")
            elif table_name == "failed_pages":
                cursor.execute('DELETE FROM failed_pages')
                print("已清空 failed_pages 表")
            else:
                cursor.execute('DELETE FROM liversoms')
                cursor.execute('DELETE FROM failed_pages')
                print("已清空所有表")
            
            conn.commit()
            conn.close()
            
            print(f"数据库清空完成: {self.db_file}")
            
        except Exception as e:
            print(f"清空数据库数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def delete_db_file(self):
        """
        删除整个SQLite数据库文件
        """
        try:
            if os.path.exists(self.db_file):
                os.remove(self.db_file)
                print(f"已删除数据库文件: {self.db_file}")
            else:
                print(f"数据库文件不存在: {self.db_file}")
                
        except Exception as e:
            print(f"删除数据库文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def close(self):
        """关闭浏览器并输出日志文件位置"""
        self.logger.info(f"程序执行完成，日志文件保存在: {self.log_file}")
        self.context.close()
        self.browser.close()
        self.playwright.stop()


def main():
    # 配置信息
    config = {
        'token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2IjoiNiIsInJvbCI6IjIsMTIiLCJhaWQiOiI0OWU3YTk0ZC0xN2NkLTQ4NTUtYjAxNC0wMzFmMThjMmIzODkiLCJ1aWQiOiIyMjM4NTA1MDkiLCJsaWQiOiIxMTc0OTU0OSIsImFwcGlkIjoiMTgiLCJ0eXBlIjoiMCIsIm5iZiI6MTc2MzI2NDgwMywiZXhwIjoxNzYzMzA4MDMzLCJpYXQiOjE3NjMyNjQ4MzMsImlzcyI6InZ6YW4iLCJhdWQiOiJ2emFuIn0.nINvnVVLlcCVIrgrJ5pdathP7ZLbLWDyGorWleZniDM",
        'cookie': "LivesId=77fbbdce-e5ae-435d-8903-c6fe0a752df4; zbvz_userid=AA551D246F586E4C20F42113F44A4CA4; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22627117678128132096%22%2C%22first_id%22%3A%22196cd7b5c83110b-0d5339f140436c8-26011c51-1821369-196cd7b5c84c26%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_utm_source%22%3A%22bing%22%2C%22%24latest_utm_medium%22%3A%22cpc%22%2C%22%24latest_utm_campaign%22%3A%221P%E5%93%81%E7%89%8C-%E7%B2%BE%E7%A1%AE%22%2C%22%24latest_utm_content%22%3A%221P%E5%93%81%E7%89%8C%22%2C%22%24latest_utm_term%22%3A%22%E7%9B%B4%E6%92%AD%E6%9C%8D%E5%8A%A1%E5%B9%B3%E5%8F%B0%22%7D%2C%22%24device_id%22%3A%22196cd7b5c83110b-0d5339f140436c8-26011c51-1821369-196cd7b5c84c26%22%7D; Hm_lvt_29ea0df3279d9bf11c4ba5ff280126f3=1760924628,1761697822,1763107058,1763264723; Hm_lpvt_29ea0df3279d9bf11c4ba5ff280126f3=1763264723; HMACCOUNT=9D62D685DE38E4B6; fromtype=pc-www.vzan.com; UserCookieNew=49e7a94d-17cd-4855-b014-031f18c2b389; UserCookieToken=c42d2b4f379df63c6cdf437f3ddf693e; liveticket=5Li4cj/JZBdD91TrIhrAVuRi7WdPpR9tZbXgp7SiUwjqL50+th0M8iv4Uqxgrli2Ml/2KWzxnu8FXi0qde3eFA==; vzanuid=627117678128132096; UserEquipment=vzanChrome09Sy1Hwq; _uetsid=21849b60c21711f08f9cffeb4b91f391; _uetvid=65f663e0bf5a11f0b06fdbca7de6523d"
    }
    # 创建爬虫实例
    crawler = DuanShuCrawler_vzan()

    try:
        # ========== 数据库操作示例 ==========
        # 1. 查看数据库数据（显示前100条）
        crawler.show_db_data(limit=100)
        
        # 2. 只查看失败的记录
        #crawler.show_db_data(limit=50, show_failed_only=True)
        
        # 3. 清空所有表的数据
        crawler.clear_db_data()
        
        # 4. 只清空 liversoms 表
        # crawler.clear_db_data(table_name="liversoms")
        
        # 5. 只清空 failed_pages 表
        # crawler.clear_db_data(table_name="failed_pages")
        
        # 6. 删除整个数据库文件
        # crawler.delete_db_file()
        # ====================================
        
        # crawler.clean_old_files()
        # 登录
        # crawler.login(config['username'], config['password'])

        # 直接调用API获取数据
        start_time = time.time()
        crawler.parse_all_liveroomlist_data(config)
        end_time = time.time()
        execution_time1 = end_time - start_time

        start_time = time.time()
        # crawler.parse_watchers_data(config)
        end_time = time.time()
        execution_time3 = end_time - start_time

        crawler.logger.info(f"parse_all_liveroomlist_data的执行时间：{execution_time1:.2f} 秒")
        crawler.logger.info(f"parse_watchers_data的执行时间：{execution_time3:.2f} 秒")
        
        # 爬取完成后显示数据库数据
        # crawler.show_db_data(limit=50)

    except Exception as e:
        print(f"爬取过程出错: {str(e)}")
    finally:
        crawler.close()


if __name__ == "__main__":
    main()
