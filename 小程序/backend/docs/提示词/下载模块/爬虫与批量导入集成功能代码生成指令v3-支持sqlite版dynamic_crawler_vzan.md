

---

# 爬虫与批量导入集成功能增量开发提示词 v3.1（支持 SQLite 版 dynamicCrawler_vzan_v3）

**版本更新**：v3.1（2025-11-19）
- **文件创建时机**：确保增量文件在API调用之前创建，即使API失败文件也存在（至少包含表头）
- **异常处理**：token/cookie错误时抛出异常而不是静默返回，异常消息明确说明是token/cookie错误
- **文件选择策略**：增量文件不存在或为空时直接返回空结果（正常情况），不再回退到主文件
- **API响应**：正确区分"没有数据导入"（正常，code 200）和"导入失败"（错误，code 400）
- **资源管理（v3.1补充）**：Playwright 浏览器对象在单独线程中创建，保存线程池引用（`self._executor`），确保关闭操作在同一线程中执行；如果创建线程已退出，使用进程级别的清理作为兜底方案

## 一、角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy、Pydantic、爬虫技术和系统集成，并擅长根据详细的设计文档和代码上下文，编写出职责清晰、分层明确、健壮可靠的微服务代码。你熟悉适配器模式、资源管理、异步编程等高级技术。

## 二、任务目标 (Task Objective)

你的任务是**扩展/维护**现有的**媒体下载服务**，通过**最小幅度修改已有文件和新增文件**的方式，实现并持续完善“爬虫 + 批量导入”的自动化集成功能。

> **重要前提：**
>
> * v2 版本的 CSV 爬虫集成已经实现并可以正常工作；
> * 爬虫主体已升级为 **SQLite 版本 `dynamicCrawler_vzan_v3.py`**；
> * 你在修改时必须遵守“**最小改动**”原则，优先在适配层修正，而不是大改业务层。

具体要求：

1. **保持 v2 中已经实现的整体集成结构**（配置、异常、服务层、API 层、Schema、爬虫工厂等）不变或做最小调整；
2. **在 SQLite 版爬虫的基础上，完善并适配爬虫抽象层与微赞适配器**：

   * `app/crawlers/base_crawler.py`
   * `app/crawlers/vzan_crawler.py`
3. 确保集成逻辑 `DownloadService.crawl_and_import_tasks()`、API 层等对上层调用的返回字段结构和语义**保持兼容**：

   * `csv_file` / `incremental_file` / `failed_file`
   * `total_rows` / `incremental_rows` / `failed_rows`
4. 新版爬虫使用 **SQLite (`vzan_crawler.db`) 做状态存储**，但仍然通过**增量 CSV 文件**对接下游 PostgreSQL 的批量导入：

   * 必须正确使用增量 CSV，并继续完成“中文列名 → 英文列名”的转换。

---

## 三、核心上下文信息 (Core Context Information)

### 3.1 项目结构（保持 v2 结构，爬虫升级为 v3）

```bash
backend/media_download_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── download.py  # <-- 追加API端点
│   ├── schemas/
│   │   └── download.py          # <-- 追加Schema定义
│   ├── services/
│   │   └── download_service.py  # <-- 追加服务层方法
│   ├── models/
│   │   └── download.py          # <-- 已存在，无需修改
│   ├── crawlers/                # <-- 新增/已有目录
│   │   ├── __init__.py          # <-- 爬虫工厂
│   │   ├── base_crawler.py      # <-- 爬虫基类（需要适配SQLite版）
│   │   └── vzan_crawler.py      # <-- 微赞爬虫适配器（需要适配SQLite版）
│   └── core/
│       ├── config.py            # <-- 追加爬虫配置
│       ├── exceptions.py        # <-- 追加爬虫异常类
│       ├── encryption.py        # <-- Token加密工具
│       └── response.py          # <-- 已存在
├── scripts/
│   └── encrypt_token.py         # <-- Token加密脚本
└── backend/
    └── dynamicCrawler_vzan_v3.py  # <-- 【已存在】SQLite版微赞爬虫实现，复用此文件
```

> 如果上述文件已经根据 v2 提示词生成且可以正常工作，则本提示词以“**增量改造**”为目标：
>
> * 除 `base_crawler.py`、`vzan_crawler.py` 外的文件**尽量不改或只做必要小修**；
> * 避免对业务流程和 API 结构做破坏性调整。

### 3.2 已存在的核心依赖（沿用 v2）

保持 v2 中对以下模块的描述与用法不变：

1. **批量导入功能（已实现）**

   * `DownloadService.batch_import_tasks_from_csv(...)`
   * API `POST /tasks/batch-import`
   * `BatchImportResult` Schema

2. **核心基础设施**

   * `create_response` / `create_error_response`
   * `DownloadServiceError` / `DatabaseError`
   * `Settings` + `.env`
   * `get_current_user()` / `get_db()`

### 3.3 已存在的爬虫实现（从 CSV 版升级为 SQLite 版）

**文件**: `backend/dynamicCrawler_vzan_v3.py`（取代 `dynamicCrawler_vzan.py`，名称必须与实际文件一致）

**关键类**: `DuanShuCrawler_vzan`（保持类名不变）

#### 3.3.1 SQLite 状态库

CSV 版本中主状态保存在 `liveroomlist_vzan.csv`；现在改为 SQLite：

1. 数据库文件：`vzan_crawler.db`（通常位于 `temp_dir`，如 `/tmp/vzan_crawler/vzan_crawler.db`）
2. 重点表：

   * `liversoms`：直播间最终状态（成功/失败）

     * 主键：`id TEXT PRIMARY KEY`
     * 关键字段：`title`, `addtime`, `starttime`, `zbId`, `liveType`, `viewCount`, `videosrc`, `liveroom_url`, `video_url`, `cover_url`, `original_playback_url`, `edited_playback_url`, `enc_tpid`, `error_reason` 等
   * `failed_pages`：分页接口失败的页面

     * `page_url TEXT PRIMARY KEY`
3. 最新成功时间 `latest_success_time`：

   * 基于 `starttime` 计算，而不是 `addtime`
   * 只在 `video_url` 非空的记录中取 `MAX(starttime)`
   * `starttime` 以可比较的时间字符串格式存储（例如 `YYYY-MM-DD HH:MM:SS`）

#### 3.3.2 输出文件策略（SQLite + 增量 CSV）

1. 主状态全部存入 SQLite，**不再依赖 CSV 作为主状态库**；
2. 保留增量 CSV 文件（`self.liveroom_list_savefile_inc`），例如：

   * `/tmp/vzan_crawler/liveroomlist_inc_vzan_backup.csv`
   * 仅包含“本次新增或重试成功的记录”，按 ID 去重；
3. 全量 CSV（如存在 `self.liveroom_list_savefile`）只作为**兼容/调试用途**，集成逻辑**优先使用增量 CSV**。

#### 3.3.3 爬取策略概念（内部细节，由 v3 负责）

`dynamicCrawler_vzan_v3.py` 内部采用“三重循环 + 页面级停止 + 失败重试”的增量策略：

1. 循环 1：重试历史 `failed_pages`；
2. 循环 2：按时间顺序做增量爬取，对整页全为旧数据才停止；
3. 循环 3：对 `liversoms` 中 `video_url` 为空的记录做 ID 级重试；
4. 所有成功数据 → SQLite + 本轮增量 CSV；失败数据 → SQLite，供下次重试。

> **适配层（`VzanCrawler`）不需要实现上述逻辑，只需要正确调用 v3 并消费它的输出。**

### 3.4 CSV 字段说明与列名转换（沿用 v2 + 幂等化要求）

尽管主状态迁移到 SQLite，**增量 CSV 输出格式仍然保持 v2 版的“中文列名”**，必须在适配层转换为英文列名才能供 `batch_import_tasks_from_csv` 使用。

**中文 → 英文映射：**

| 原始列名（中文） | 目标列名（英文）         | 说明          |
| -------- | ---------------- | ----------- |
| `直播间ID`  | `liveroom_id`    | 必填，直播间唯一标识  |
| `标题`     | `liveroom_title` | 可选，直播间标题    |
| `直播间url` | `liveroom_url`   | 可选，直播间 URL  |
| `播放url`  | `resource_url`   | 必填，视频资源播放地址 |

新增字段：`resource_type`，默认 `'hls'`（微赞默认 HLS）。

**输出列顺序（必须统一）：**

```python
OUTPUT_COLUMNS = [
    'liveroom_id',
    'liveroom_title',
    'liveroom_url',
    'resource_url',
    'resource_type',
]
```

> `_convert_csv_columns()` 必须是**幂等的**：
>
> * 若 CSV 已经是英文表头（包含 `liveroom_id`, `resource_url`, `resource_type`），则仅做格式校验并跳过转换；
> * 若是中文表头，则按上述映射一次性转换并覆盖原文件；
> * 若表头既非预期中文，也非预期英文，应抛出异常。

---

## 四、整体功能流程与关键特性（保持 v2 设计）

### 4.1 流程：爬取 + 导入一体化

总体流程不变，只是爬虫内部实现从 CSV 状态转为 SQLite 状态：

```text
API 请求
 → 检查参数、认证
 → 调用 DownloadService.crawl_and_import_tasks
   → 创建爬虫实例（CrawlerFactory + VzanCrawler）
   → 执行 crawl()
     → 调用 dynamicCrawler_vzan_v3.parse_all_liveroomlist_data(config)
     → v3 内部：SQLite 状态 + 增量 CSV
   → VzanCrawler 转换 CSV 列名（中文 → 英文）
   → DownloadService 选择 CSV 文件（优先增量文件）
   → 调用 batch_import_tasks_from_csv 导入到 PostgreSQL
   → 清理增量/失败文件，保留主文件（如有）
 → 返回统一响应
```

### 4.2 CSV 文件选择策略（v3.1 更新）

**必须遵循（v3.1 修改）：**

1. **仅使用增量文件**：

   * 增量文件存在且非空（`incremental_rows > 0`）→ 导入增量文件；
   * 增量文件不存在或为空 → 直接返回空结果（正常情况，不是错误），不导入数据；
2. **不再回退到主文件**：

   * v3.1 移除了回退到主 CSV (`csv_file`) 的逻辑，避免重复导入历史数据；
   * 如果增量文件不存在或为空，说明没有新增数据，这是正常情况，不应视为错误。

> 由于 v3 版本爬虫主状态在 SQLite 中，**主 CSV 可选**（可有可无），但接口中 `csv_file` 字段仍需存在（可为 `None`），用于保持兼容。

### 4.3 资源管理 & 文件清理（v3.1 更新）

1. **Playwright 浏览器资源管理（v3.1 重要更新）**：
   - Playwright 浏览器对象在单独线程中创建（通过 `ThreadPoolExecutor`），避免与 FastAPI 事件循环冲突
   - `vzan_crawler.py` 的 `__init__` 方法需要添加 `self._executor = None` 保存线程池引用
   - `_ensure_crawler()` 方法需要保存线程池引用（不使用 `with` 语句自动关闭），确保后续可以在同一线程中关闭
   - `close()` 方法必须使用保存的线程池引用（`self._executor`）在同一线程中执行关闭操作
   - 如果创建线程已退出或关闭失败，使用进程级别的清理（`_force_cleanup_browser_processes()`）作为兜底方案
   - 浏览器必须在 `finally` 块中关闭（`self.crawler.close()`），确保资源释放
2. 只删除：

   * 增量 CSV 文件
   * 失败记录文件（可选）
3. **主状态文件 / SQLite DB 文件不得随意删除**，否则下次增量策略会失效。

---

## 五、具体代码生成 / 修改指令（v3 合并版）

> 下面内容以 v2 的大结构为基准，只在关键处（特别是 `base_crawler.py`、`vzan_crawler.py`、已有爬虫描述处）融合 SQLite 版 v3 的要求。
> **如果对应文件已经存在，请采用“对现有代码做最小修改”的方式完成调整。**

### 5.1 配置模块：`app/core/config.py`（与 v2 一致，可略微注释说明 SQLite）

保持 v2 中追加的爬虫配置项不变，仅在注释中承认 v3 使用 SQLite + 增量 CSV 模式即可：

```python
# ============ 爬虫配置 (Crawler Configuration) ============

# 微赞爬虫配置
VZAN_USERNAME: str = Field(default="", description="微赞用户名")
VZAN_PASSWORD: str = Field(default="", description="微赞密码")
VZAN_TOKEN: str = Field(default="", description="微赞API Token（加密后）")

# 爬虫通用配置
CRAWLER_TIMEOUT: int = Field(default=10, ge=1, le=600, description="爬虫单个请求超时时间（秒）")
CRAWLER_TEMP_DIR: str = Field(default="/tmp/vzan_crawler", description="爬虫临时文件目录（SQLite与增量CSV都会放在这里）")
CRAWLER_BATCH_SIZE: int = Field(default=100, ge=10, le=1000, description="批量写入CSV的数据条数")

# 集成配置
CRAWL_IMPORT_AUTO_START: bool = Field(default=False, description="导入后是否自动启动")
CRAWL_IMPORT_SKIP_DUPLICATES: bool = Field(default=True, description="是否跳过重复任务组合（resource_url + liveroom_id + liveroom_title）")
CRAWL_IMPORT_DELETE_TEMP_FILE: bool = Field(default=True, description="导入后是否删除增量文件和失败记录（注意：主状态文件/SQLite不会删除）")

# Token加密密钥
TOKEN_ENCRYPTION_KEY: str = Field(default="", description="Token加密密钥")
```

> 如果现有配置已包含这些字段，只需**补充说明注释**，不必调整字段名。

### 5.2 加密模块 / 异常模块 / Schema / 工厂 / 服务层 / API

以下内容可直接沿用 v2 文档中已经给出的实现要求，不再重复展开，只强调**与 SQLite 升级相关的兼容点**：

* `app/core/encryption.py`：Token 加密工具，逻辑与爬虫内部实现无关，**无须因 SQLite 升级而修改**；
* `app/core/exceptions.py`：`CrawlerError`、`CrawlerConfigError` 等异常类保持不变；
* `app/crawlers/__init__.py`：`CrawlerFactory` 注册 `vzan` → `VzanCrawler`，不变；
* `app/schemas/download.py`：
  * `CrawlAndImportRequest` 需要包含 `token` 和 `cookie` 可选字段，并添加格式验证器（Pydantic validator）
  * 验证规则：Token长度10-500，Cookie长度10-2000，检查非法字符（`<`, `>`, `"`, `'`, `;`, `\n`, `\r` 等）
  * `CrawlAndImportResponse` 结构不变
* `app/services/download_service.py`：

  * `crawl_and_import_tasks` 方法签名需要添加 `token: Optional[str] = None` 和 `cookie: Optional[str] = None` 参数
  * 优先级处理：前端参数 > 配置读取（`final_token = token if token else settings.VZAN_TOKEN`）
  * 对最终使用的 token 和 cookie 进行格式验证（双重保障，即使 Schema 层已验证）
  * 所有日志中**禁止**记录 token 和 cookie 的值，仅可记录来源（前端传递或配置读取）
  * 仍然通过 `crawler.crawl()` 获得 `csv_file` / `incremental_file` 等字段；
  * 新版 `crawl()` 可以**额外返回** `db_file` 等字段，但不能删除原有字段；
  * 批量导入时默认启用去重（skip_duplicates=True），去重键为：`(user_id, resource_url, liveroom_id)`；去重前对 `resource_url` 做标准化，并将标准化后的 `resource_url` 入库。
* `app/api/v1/endpoints/download.py`：

  * `POST /tasks/crawl-and-import` 需要从 `request_data` 提取 `token` 和 `cookie`（如果前端传递了）
  * 传递给服务层时作为可选参数：`token=request_data.token, cookie=request_data.cookie`
  * 注意：API 层不记录 token 和 cookie 到日志中

> 以上模块如已实现并能工作，除非有 SQLite 适配直接相关的问题，一般不需要修改。

### 5.3 重点一：更新爬虫基类 `app/crawlers/base_crawler.py`（融合 v2 + v3 要求）

**目标：** 保持接口不变，更新文档和注释，使其明确支持“SQLite + 增量 CSV”的返回约定。

```python
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
    
    所有具体的爬虫实现（如 VzanCrawler）必须继承此类并实现抽象方法
    """
    
    def __init__(self, config: Dict):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置字典，至少包含:
                - timeout: 超时时间（秒），默认10秒
                - temp_dir: 临时文件目录
                - 其他由具体爬虫决定的字段（如 username / password / token 等）
                
        说明:
            在 SQLite 版爬虫中，config 还可能影响 SQLite 数据库文件的存放路径，
            但 BaseCrawler 不直接依赖具体实现，只做透传。
        """
        self.config = config
        self.timeout = config.get('timeout', 10)
        
        logger.info(f"{self.__class__.__name__} initialized with timeout={self.timeout}s")
    
    @abstractmethod
    def crawl(self, config: Dict, **kwargs) -> Dict:
        """
        执行爬取任务（抽象方法，子类必须实现）
        
        Args:
            config: 爬虫配置字典，包含 username, password, token 等。
            **kwargs: 爬虫特定的额外参数，如:
                - page_size: 每页数据量（默认10）
                - max_pages: 最大爬取页数（默认全部）
        
        Returns:
            Dict: 爬取结果摘要，键至少包含（但不限于）：
            
                {
                    # === 与 CSV 输出相关的字段（对上层保持兼容）===
                    "csv_file": str | None,          # 全量 CSV 文件路径（如未生成可为 None）
                    "incremental_file": str | None,  # 本轮增量 CSV 文件路径（优先用于导入）
                    "failed_file": str | None,       # 失败记录文件路径（如有）
                    
                    "total_rows": int,               # 总记录数（推荐从 SQLite 统计，退化为 CSV 统计亦可）
                    "incremental_rows": int,         # 本轮增量 CSV 行数
                    "failed_rows": int,              # 失败记录数量（推荐从 SQLite 统计或基于失败文件）
                    
                    # === 可选的扩展字段（针对 SQLite 版爬虫）===
                    "db_file": str | None,           # SQLite 状态库路径（例如 vzan_crawler.db）
                    # "db_total_rows": int,          # (可选) 若方便，可返回 SQLite 中总行数
                    # ... 其他统计信息
                }
        
        Raises:
            CrawlerError: 爬取失败时抛出
            CrawlerTimeoutError: 爬取超时时抛出
            CrawlerAPIError: API 调用失败时抛出
        """
        raise NotImplementedError
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否完整有效（抽象方法，子类必须实现）
        
        Returns:
            bool: 配置是否有效
        """
        raise NotImplementedError
```

> 如果现有 `BaseCrawler` 已经存在，请**对照以上内容**，只更新 docstring 和必要字段说明，不要破坏类名与方法签名。

### 5.4 重点二：更新微赞适配器 `app/crawlers/vzan_crawler.py`（融合 v2 + v3 要求）

**核心目标：**
在"**最小改动**"的前提下，让 `VzanCrawler`：

1. 从 **SQLite 版爬虫 `dynamicCrawler_vzan_v3.py`** 导入 `DuanShuCrawler_vzan`；
2. 调用 v3 的 `parse_all_liveroomlist_data(config)`；
3. 正确读取：

   * 增量 CSV 文件路径（必须）
   * 可能存在的全量 CSV / 失败文件 / SQLite DB 文件路径；
4. 对存在的 CSV 文件执行**幂等的"中文列名 → 英文列名"转换**；
5. 尽量从 SQLite 或 CSV 统计 `total_rows` / `incremental_rows` / `failed_rows`；
6. 返回结构与 v2 保持向后兼容。

**关键实现细节**（v3.1）：
- **文件创建时机**：`dynamicCrawler_vzan_v3.py` 的 `parse_all_liveroomlist_data` 方法在API调用之前创建增量文件，确保即使API失败，文件也存在（至少包含表头）
- **异常处理**：当token/cookie错误时，`parse_all_liveroomlist_data` 会抛出异常（而不是静默返回），异常消息明确说明是token/cookie错误；`vzan_crawler.py` 的 `crawl` 方法需要捕获异常并转换为 `CrawlerError`
- **异常传播**：异常会被正确传播到服务层和API层，最终返回错误响应给前端
- **资源管理（v3.1补充）**：Playwright 浏览器对象在单独线程中创建（通过 `ThreadPoolExecutor`），`vzan_crawler.py` 需要保存线程池引用（`self._executor`），确保关闭操作在同一线程中执行；如果创建线程已退出，使用进程级别的清理作为兜底方案

> **注意：**
>
> * 不重写 v3 内部逻辑，只负责"接口适配 + CSV 列名转换"；
> * **v3.1 更新**：浏览器资源管理：Playwright 在单独线程中创建，需要保存线程池引用，确保关闭操作在同一线程中执行；
> * 仍然在 `finally` 中关闭浏览器（通过 `crawler.close()` 方法）；
> * 必须正确处理异常，确保token/cookie错误能够传播到上层。

去重与 URL 标准化（在服务层生效，适配层无需实现）：
- 服务层在导入前对 `resource_url` 做标准化（scheme/host 小写、去掉路径尾斜杠、对 query 参数按键名升序重排）；
- 去重仅使用 `(user_id, resource_url, liveroom_id)` 组合；
- 数据库存储的 `resource_url` 为标准化后的 m3u8 URL。

示例实现（可在现有基础上做最小调整）：

```python
"""
微赞爬虫适配器模块（SQLite + 增量 CSV 版）

使用适配器模式复用 backend/dynamicCrawler_vzan_v3.py
"""
import csv
import logging
import os
import shutil
import tempfile
from typing import Dict, Optional

from .base_crawler import BaseCrawler
from app.core.exceptions import CrawlerError, CrawlerConfigError

import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 将 backend 目录加入 sys.path，导入 SQLite 版爬虫实现
backend_dir = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
from dynamicCrawler_vzan_v3 import DuanShuCrawler_vzan  # noqa: E402


class VzanCrawler(BaseCrawler):
    """
    微赞爬虫适配器（适配 SQLite 版 dynamicCrawler_vzan_v3）
    
    将已有的 DuanShuCrawler_vzan 适配到 BaseCrawler 统一接口。
    """
    
    # 列名映射和输出列顺序保持与 v2 一致，便于批量导入
    COLUMN_MAPPING = {
        "直播间ID": "liveroom_id",     # 必需
        "播放url": "resource_url",      # 必需
        "标题": "liveroom_title",       # 可选
        "直播间url": "liveroom_url",    # 可选
    }
    
    OUTPUT_COLUMNS = [
        "liveroom_id",
        "liveroom_title",
        "liveroom_url",
        "resource_url",
        "resource_type",
    ]
    
    def __init__(self, config: Dict):
        """
        初始化适配器
        
        Args:
            config: 爬虫配置字典
        
        Raises:
            CrawlerConfigError: 配置无效或爬虫初始化失败
        """
        super().__init__(config)
        
        # 提取基础配置（保持 v2 约定）
        self.username = config.get("username")
        self.password = config.get("password")
        self.token = config.get("token")
        
        # ⚠️ v3.1 新增：延迟初始化，不在 __init__ 中创建 crawler，避免 Playwright 初始化失败
        # 将在首次调用 crawl() 时通过 _ensure_crawler() 创建
        self.crawler = None
        self._init_lock = threading.Lock()  # 线程安全锁
        self._executor = None  # ⚠️ v3.1 新增：保存线程池引用，用于后续在同一线程中关闭浏览器
        logger.info("VzanCrawler: Initialized (crawler will be created on first use)")
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not all([self.username, self.password, self.token]):
            logger.error("VzanCrawler: Missing required config (username, password, token)")
            return False
        return True
    
    def _create_duanshu_crawler(self):
        """在单独线程中创建爬虫实例（v3.1 新增）"""
        # 只在这个线程里使用 Proactor
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return DuanShuCrawler_vzan()
    
    def _ensure_crawler(self):
        """延迟初始化爬虫实例（v3.1 更新：保存线程池引用）"""
        if self.crawler is None:
            with self._init_lock:
                if self.crawler is None:
                    logger.info("VzanCrawler: Creating crawler instance in separate thread...")
                    try:
                        # ⚠️ v3.1 关键修改：不使用 with 语句，手动管理线程池生命周期
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
        关闭浏览器资源（v3.1 更新：使用保存的线程池在同一线程中关闭）
        
        供 DownloadService 调用，统一关闭内部爬虫资源
        """
        if not self.crawler:
            return
        
        crawler_to_close = self.crawler
        executor_to_close = self._executor
        
        try:
            if hasattr(crawler_to_close, 'close'):
                # ⚠️ v3.1 关键修改：使用创建时的线程池，在同一线程中关闭
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
                        future.result(timeout=10)
                        logger.info("VzanCrawler: Browser closed via executor")
                    except Exception as e:
                        logger.warning(f"VzanCrawler: Failed to close via executor: {e}")
                        # 兜底：尝试直接关闭或进程级别清理
                        self._force_cleanup_browser_processes()
                    finally:
                        # 关闭线程池
                        if executor_to_close:
                            executor_to_close.shutdown(wait=True)
                            self._executor = None
                else:
                    # 如果没有线程池引用，尝试直接关闭或进程级别清理
                    logger.warning("VzanCrawler: No executor reference, using process cleanup")
                    self._force_cleanup_browser_processes()
        except Exception as e:
            logger.warning(f"VzanCrawler: Failed to close browser: {e}")
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
        """强制清理浏览器进程（兜底方案，v3.1 新增）"""
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
    
    def crawl(self, config: Dict, **kwargs) -> Dict:
        """
        执行爬取（主入口）
        
        说明:
            - 内部调用 dynamicCrawler_vzan_v3.parse_all_liveroomlist_data(config)，
              利用 SQLite 维护状态，并输出本轮增量 CSV。
            - 本方法负责:
                * CSV 列名转换（中文 → 英文，幂等）
                * 行数统计
                * 构造对上层兼容的结果字典
        """
        csv_file: Optional[str] = None
        incremental_file: Optional[str] = None
        failed_file: Optional[str] = None
        db_file: Optional[str] = None
        
        try:
            self._ensure_crawler()  # ⚠️ v3.1 新增：首次使用时初始化
            if not self.validate_config():
                raise CrawlerConfigError("VzanCrawler配置无效：缺少username, password或token")
            
            logger.info("VzanCrawler: Starting crawl with SQLite-based crawler (v3)")
            
            # 调用 v3 核心方法，内部使用 SQLite + 增量 CSV
            self.crawler.parse_all_liveroomlist_data(config)
            logger.info("VzanCrawler: Crawl completed, extracting file paths")
            
            # 从 v3 实例上获取各类文件路径（变量名必须与 v3 实现保持一致）
            csv_file = getattr(self.crawler, "liveroom_list_savefile", None)
            incremental_file = getattr(self.crawler, "liveroom_list_savefile_inc", None)
            failed_file = getattr(self.crawler, "failed_liveroomlist_url", None)
            db_file = getattr(self.crawler, "db_file", None)
            
            # 统一转为 str 或 None
            csv_file = str(csv_file) if csv_file else None
            incremental_file = str(incremental_file) if incremental_file else None
            failed_file = str(failed_file) if failed_file else None
            db_file = str(db_file) if db_file else None
            
            # === CSV 列名转换（幂等）===
            # 优先保证增量 CSV 格式正确
            if incremental_file and os.path.exists(incremental_file):
                self._convert_csv_columns(incremental_file)
                logger.info(f"VzanCrawler: Incremental CSV converted - {incremental_file}")
            
            # 如有全量 CSV，也可以做一次转换以保持一致
            if csv_file and os.path.exists(csv_file):
                self._convert_csv_columns(csv_file)
                logger.info(f"VzanCrawler: Main CSV converted - {csv_file}")
            
            # === 行数统计 ===
            incremental_rows = self._count_csv_rows(incremental_file) if incremental_file else 0
            
            # total_rows / failed_rows 理想情况下应该从 SQLite 统计，
            # 若 v3 实现暴露了统计属性/方法可优先使用，否则暂时回退为 CSV 统计。
            total_rows = self._count_csv_rows(csv_file) if csv_file else incremental_rows
            failed_rows = self._count_csv_rows(failed_file) if failed_file else 0
            
            result = {
                "csv_file": csv_file,
                "incremental_file": incremental_file,
                "failed_file": failed_file,
                "total_rows": total_rows,
                "incremental_rows": incremental_rows,
                "failed_rows": failed_rows,
            }
            
            # 向下兼容的同时，允许增加 SQLite 相关字段
            if db_file:
                result["db_file"] = db_file
            
            logger.info(
                "VzanCrawler: Crawl result - "
                f"total: {total_rows}, incremental: {incremental_rows}, failed: {failed_rows}, "
                f"csv_file: {csv_file}, incremental_file: {incremental_file}, failed_file: {failed_file}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"VzanCrawler: Crawl failed - {str(e)}", exc_info=True)
            raise CrawlerError(f"爬取失败: {str(e)}") from e
        
        finally:
            # 关闭浏览器，避免进程泄漏
            try:
                if hasattr(self, "crawler") and self.crawler:
                    self.crawler.close()
                    logger.info("VzanCrawler: Browser closed")
            except Exception as e:
                logger.warning(f"VzanCrawler: Failed to close browser - {str(e)}")
    
    def _count_csv_rows(self, csv_file: Optional[str]) -> int:
        """统计 CSV 行数（不含表头），异常时返回 0"""
        if not csv_file or not os.path.exists(csv_file):
            return 0
        try:
            with open(csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过表头
                return sum(1 for _ in reader)
        except Exception as e:
            logger.warning(f"VzanCrawler: Failed to count rows in {csv_file}: {str(e)}")
            return 0
    
    def _convert_csv_columns(self, csv_file: str) -> None:
        """
        将 CSV 列名转换为英文（原地覆盖，幂等）
        
        规则：
            - 若表头已是英文并包含必须列（liveroom_id, resource_url, resource_type），则只做校验直接返回；
            - 若表头为中文，则按照 COLUMN_MAPPING → OUTPUT_COLUMNS 进行转换；
            - 若表头既不是预期中文，也不是预期英文，抛出 ValueError。
        """
        if not os.path.exists(csv_file):
            logger.warning(f"VzanCrawler: CSV file not found, skip convert - {csv_file}")
            return
        
        logger.info(f"VzanCrawler: Converting CSV columns - {csv_file}")
        
        # 先读一遍，确认表头
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
        
        if not fieldnames:
            raise ValueError(f"CSV 文件无表头: {csv_file}")
        
        # 情况 1：已经是英文表头（幂等校验）
        english_required = {"liveroom_id", "resource_url", "resource_type"}
        if english_required.issubset(set(fieldnames)):
            logger.info(f"VzanCrawler: CSV already in English header, skip convert - {csv_file}")
            return
        
        # 情况 2：中文表头 → 进行转换
        if "直播间ID" in fieldnames and "播放url" in fieldnames:
            temp_fd, temp_path = tempfile.mkstemp(suffix=".csv", text=True)
            converted_count = 0
            skipped_count = 0
            
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8-sig", newline="") as wf:
                    writer = csv.DictWriter(wf, fieldnames=self.OUTPUT_COLUMNS)
                    writer.writeheader()
                    
                    for row in rows:
                        try:
                            new_row = {}
                            for cn, en in self.COLUMN_MAPPING.items():
                                value = (row.get(cn) or "").strip()
                                new_row[en] = value or None
                            
                            # resource_type 固定为 'hls'
                            new_row["resource_type"] = "hls"
                            
                            # 必需字段检查
                            if not new_row.get("liveroom_id") or not new_row.get("resource_url"):
                                skipped_count += 1
                                logger.warning(
                                    "VzanCrawler: Skip row with missing required fields - "
                                    f"liveroom_id={new_row.get('liveroom_id')}, "
                                    f"resource_url={new_row.get('resource_url')}"
                                )
                                continue
                            
                            writer.writerow(new_row)
                            converted_count += 1
                        except Exception as e:
                            skipped_count += 1
                            logger.warning(f"VzanCrawler: Failed to convert row - {str(e)}")
                
                shutil.move(temp_path, csv_file)
                logger.info(
                    "VzanCrawler: CSV conversion successful - "
                    f"{csv_file}, converted={converted_count}, skipped={skipped_count}"
                )
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                logger.error(f"VzanCrawler: CSV conversion failed - {csv_file}", exc_info=True)
                raise
            return
        
        # 情况 3：既不是预期中文也不是预期英文
        raise ValueError(
            f"CSV 表头不符合预期，无法转换: {csv_file}, fieldnames={fieldnames}"
        )
```

> 如你已有一个 v2 版的 `VzanCrawler`，可以：
>
> * 保留原有结构（类名、对外接口、日志规范等），仅将导入部分改为 `dynamicCrawler_vzan_v3`，并插入/修正上述要点；
> * `_convert_csv_columns` 如果已经存在，只需补上“幂等判断 + 预期英文头校验”。

---

## 六、编码规范与边界条件（综合 v2 + v3）

1. **最小修改原则**：

   * 除非必要，不改 `DownloadService`、API 层、异常/响应封装等其它模块代码；
   * 对 `BaseCrawler` 和 `VzanCrawler` 的改动要尽量局部化。

2. **字段命名禁止乱改**：

   * CSV 列名、属性名（如 `liveroom_list_savefile_inc`, `failed_liveroomlist_url`, `db_file` 等）必须与 v3 真正实现一致；
   * 不允许凭空发明新字段。

3. **异常与日志**：

   * 继续使用 `CrawlerError`、`CrawlerConfigError` 等异常类型；
   * `info`: 开始/结束/统计/成功转换（**禁止记录 token 和 cookie 的值**）；
   * `warning`: 跳过行、删除/关闭失败（**禁止记录 token 和 cookie 的值**）；
   * `error`: 任何爬取失败、转换失败、SQLite 统计失败等（**禁止记录 token 和 cookie 的值**）；
   * **安全规范**：所有日志中不记录 `token` 和 `cookie` 的实际值，可以记录来源（前端传递或配置读取），但不能记录值本身。

4. **兼容性**：

   * 即使在 SQLite 模式下，`crawler.crawl()` 返回值仍然需要包含 v2 中依赖的字段；
   * **v3.1 修改**：上层如果检查到 `incremental_file` 不存在或为空，会直接返回空结果（正常情况），不再回退到 `csv_file`；
   * 增量文件在API调用之前创建，确保文件始终存在（至少包含表头）。

---

## 七、交付检查清单（合并后自检）

合并 v2 + v3 后，请逐项自检：

1. **项目结构**

   * [ ] backend 下爬虫文件名已更新为 `dynamicCrawler_vzan_v3.py`，且 `VzanCrawler` 正确导入此版本。

2. **BaseCrawler**

   * [ ] 类名、方法签名未变；
   * [ ] `crawl()` 的 docstring 已明确描述 SQLite + CSV 的返回契约（包含 `db_file` 等可选字段）；
   * [ ] 未强行依赖任何 SQLite 细节，只在注释中说明可能存在。

3. **VzanCrawler**（v3.1 更新）

   * [ ] 导入的是 `dynamicCrawler_vzan_v3.DuanShuCrawler_vzan`；
   * [ ] `parse_all_liveroomlist_data(config)` 被正常调用；
   * [ ] 正确读取 `liveroom_list_savefile_inc` 作为 `incremental_file`；
   * [ ] 若存在全量 CSV，则作为 `csv_file` 返回；否则允许为 `None`；
   * [ ] 若 v3 暴露 `db_file`，则作为可选字段返回；
   * [ ] `_convert_csv_columns()` 支持幂等：若已是英文头则跳过；
   * [ ] `crawl()` 返回的字段仍包括 `csv_file` / `incremental_file` / `failed_file` / `total_rows` / `incremental_rows` / `failed_rows`。
   * [ ] **v3.1 新增**：`__init__` 方法包含 `self._executor = None` 保存线程池引用；
   * [ ] **v3.1 新增**：`_ensure_crawler()` 方法保存线程池引用（不使用 `with` 语句自动关闭）；
   * [ ] **v3.1 新增**：`close()` 方法使用保存的线程池引用在同一线程中关闭浏览器；
   * [ ] **v3.1 新增**：实现了 `_force_cleanup_browser_processes()` 方法作为兜底方案。

4. **集成逻辑**（v3.1 更新）

   * [ ] `DownloadService.crawl_and_import_tasks()` 未因 SQLite 升级需要大改；
   * [ ] **仅使用增量文件**：增量文件存在且非空时导入，不存在或为空时返回空结果（正常情况），**不再回退到主文件**；
   * [ ] 只删除增量 CSV 与失败文件，保留主状态文件/SQLite。

5. **资源管理和异常**（v3.1 更新）

   * [ ] 任意异常情况下都能在 `finally` 块中关闭浏览器；
   * [ ] CSV 转换失败时会记录错误，但不会默默吞掉异常；
   * [ ] 对所有潜在路径不存在的场景有防御性处理（`None` / `os.path.exists` 判断）；
   * [ ] **文件创建时机**：`dynamicCrawler_vzan_v3.py` 在API调用之前创建增量文件，确保文件始终存在；
   * [ ] **异常处理**：token/cookie错误时抛出异常，异常会被正确传播到服务层和API层；
   * [ ] **API响应**：正确区分"没有数据导入"（正常，code 200）和"导入失败"（错误，code 400）；
   * [ ] **v3.1 新增**：线程池管理：`_ensure_crawler()` 保存线程池引用，`close()` 在同一线程中关闭浏览器；
   * [ ] **v3.1 新增**：浏览器关闭：使用保存的线程池引用执行关闭操作，失败时使用进程级别清理作为兜底。

---

上面这份就是**合并后的 v3 独立提示词文档**。你可以把它保存为：

> `爬虫与批量导入集成功能代码生成指令v3-支持sqlite版dynamic_crawler_vzan_v3.md`

然后在后续需要生成或调整代码时，直接把这份 v3 文档丢给 AI，让它在**不破坏现有功能**的前提下，根据最新 SQLite 版爬虫做增量开发或维护。
