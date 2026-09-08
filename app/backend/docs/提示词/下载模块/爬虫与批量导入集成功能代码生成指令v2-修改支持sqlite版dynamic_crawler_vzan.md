下面是一份“改进版代码生成提示词”，你之后可以直接丢给另一个 AI，让它在**尽量少改动**的前提下，专门去更新 `app/crawlers/base_crawler.py` 和 `app/crawlers/vzan_crawler.py`，使其适配**SQLite 版爬虫 `dynamicCrawler_vzan_v3.py`**（状态用 SQLite，增量数据仍输出独立 CSV）。这份提示词默认其它集成代码（比如 `DownloadService.crawl_and_import_tasks`）保持不变。

---

## 【给 AI 的代码生成提示词】

### 主题：适配 SQLite 版微赞爬虫 dynamicCrawler_vzan_v3，最小改动升级 BaseCrawler 与 VzanCrawler

---

## 一、角色与目标

你是一名资深 Python 后端工程师，熟悉爬虫、Playwright、SQLite、CSV 处理以及微服务集成，擅长在**最小改动现有代码**的前提下做重构和适配。

当前项目中已经存在完整的“爬取 + 批量导入”集成方案，`DownloadService.crawl_and_import_tasks()`、API 层等逻辑已经按照旧版爬虫实现完成，不允许随意重写这些业务逻辑。

**你的任务只聚焦于：**

1. 在**最小改动**的前提下，更新：

   * `app/crawlers/base_crawler.py`
   * `app/crawlers/vzan_crawler.py`
2. 让它们能够正确适配新版爬虫实现 `dynamicCrawler_vzan_v3.py`：

   * 新版爬虫使用 **SQLite** (`vzan_crawler.db`) 作为主状态库（成功 & 失败数据）；
   * 增量数据仍然输出到一个独立的 CSV 文件（用于后续导入 PostgreSQL）；
3. 保持对上层调用（比如 `DownloadService.crawl_and_import_tasks`）的返回字段结构和语义**尽量兼容**，避免大面积修改上层代码。

---

## 二、现有结构与调用关系（简要）

### 2.1 现有爬虫抽象层

* `app/crawlers/base_crawler.py`：定义 `BaseCrawler` 抽象类，约定：

  * 初始化接收 `config: Dict`
  * 抽象方法：

    * `crawl(self, config: Dict, **kwargs) -> Dict`
    * `validate_config(self) -> bool`

* `app/crawlers/vzan_crawler.py`：

  * `VzanCrawler(BaseCrawler)` 的具体实现，内部复用已有爬虫 `DuanShuCrawler_vzan`；
  * `crawl()` 调用底层爬虫 `parse_all_liveroomlist_data(config)` 后，返回一个字典：

    ```python
    {
        "csv_file": csv_file,
        "incremental_file": incremental_file,
        "failed_file": failed_file,
        "total_rows": total_rows,
        "incremental_rows": incremental_rows,
        "failed_rows": failed_rows,
    }
    ```



* 内部带有 `_count_csv_rows` 和 `_convert_csv_columns` 等工具方法，对 CSV 做行数统计和“中文列名 → 英文列名”的转换。

### 2.2 上层服务依赖

* `DownloadService.crawl_and_import_tasks()`（在 `app/services/download_service.py` 中）依赖上述 `crawl()` 的返回结构，尤其是：

  * `csv_file`
  * `incremental_file`
  * `failed_file`
  * `total_rows`
  * `incremental_rows`
  * `failed_rows`
* 服务层会：

  1. **优先使用增量文件**导入；
  2. 若增量文件不可用，会回退到 `csv_file`，并强制开启去重；

**要求：在适配新版爬虫时，要尽量保持这个返回结构不变，或者只做向后兼容的扩展（例如增加新字段），不能破坏现有调用。**

---

## 三、新版爬虫 dynamicCrawler_vzan_v3 的核心变化（来自既有设计文档）

### 3.1 状态管理从 CSV 迁移到 SQLite

旧版依赖 `liveroomlist_vzan_api.csv` 作为主状态库；新版要求：

1. 使用 SQLite 数据库 `vzan_crawler.db` 维护两张核心表：

   * `liversoms`：存储每一个直播间的最终状态（成功 / 失败）。

     * 主键：`id TEXT PRIMARY KEY`
     * 其他字段来自 `extract_liveroomlist_data()` 的 `live_info` 字典，如：`title`, `addtime`, `starttime`, `zbId`, `liveType`, `viewCount`, `videosrc`, `liveroom_url`, `video_url`, `cover_url`, `original_playback_url`, `edited_playback_url`, `enc_tpid`, `error_reason` 等。
   * `failed_pages`：记录分页接口失败的页面 URL：

     * `page_url TEXT PRIMARY KEY`

2. `latest_success_time` 必须基于 `starttime` 计算，而不是 `addtime`：

   * 仅从 **video_url 非空** 的记录中取 `MAX(starttime)`；
   * `starttime` 必须以可比较格式存储（如 `YYYY-MM-DD HH:MM:SS` 文本）。

3. 失败记录（video_url 为空）不会影响 `latest_success_time`。

### 3.2 输出文件策略

1. 不再使用 CSV 做“主状态库”，主状态都进 SQLite。
2. **保留增量 CSV 文件**（通常是 `self.liveroom_list_savefile_inc`，例如 `liveroomlist_inc_vzan_backup.csv`），用于下游 PostgreSQL 导入：

   * 仅包含“本次爬取新增或重试成功的记录”，按 ID 去重。
3. 原来的全量 CSV（如 `liveroomlist_vzan_api.csv`）不再作为状态来源，可以不写，或者仅作为调试辅助（实际集成时尽量不要依赖它）。

### 3.3 爬取策略（概念上）

内部采用“三重循环 + 页面级停止 + 失败重试”的增量策略，确保既不漏爬，又避免过度重复：

1. 循环 1：重试 `failed_pages` 中记录的页面；
2. 循环 2：按时间顺序进行增量爬取（对整页“全是旧数据”才做页面级停止，页内不能因为某条旧数据直接 `break`）；
3. 循环 3：对 `liversoms` 中 `video_url` 为空的 ID 做 ID 级重试；
4. 所有成功数据写入 SQLite + 本次增量 CSV（去重），所有失败数据保留在 SQLite 中以供下次重试。

> **注意**：这些内部策略由 `dynamicCrawler_vzan_v3.py` 负责实现，`VzanCrawler` 只是适配层，不需要重写三重循环逻辑，只需正确调用并读取结果。

---

## 四、需要修改 / 保持不变的部分（高层要求）

### 4.1 必须保持不变或兼容的约定

1. `BaseCrawler.crawl()` 的返回值对上层仍然是一个 `Dict`，其键至少应包含：

   * `csv_file`: 可以是全量 CSV 路径或 `None`；
   * `incremental_file`: 新版中**必需**指向增量 CSV 文件路径（如 `self.crawler.liveroom_list_savefile_inc`）；
   * `failed_file`: 失败记录文件路径（如果底层仍有该文本文件）；
   * `total_rows`: 建议从 SQLite 或 CSV 统计总体条数；
   * `incremental_rows`: 增量 CSV 行数；
   * `failed_rows`: 失败记录数（可由 SQLite 或文本文件统计）。

2. 上层 `DownloadService.crawl_and_import_tasks()` 的逻辑不改：

   * **优先使用 `incremental_file` 导入**；
   * 如增量文件不可用，才回退到 `csv_file`，并且强制去重。

3. CSV 列名仍需在适配层（`VzanCrawler`）做一次“**中文列名 → 英文列名**”转换，转换规则与旧版保持一致：

   * 中文 → 英文：

     * `直播间ID` → `liveroom_id`
     * `标题` → `liveroom_title`
     * `直播间url` → `liveroom_url`
     * `播放url` → `resource_url`
   * 新增列：

     * `resource_type`，默认 `'hls'`；
   * 输出列顺序：

     ```python
     OUTPUT_COLUMNS = [
         'liveroom_id',
         'liveroom_title',
         'liveroom_url',
         'resource_url',
         'resource_type',
     ]
     ```

4. `_convert_csv_columns()` 需要具有**幂等性**：

   * 如果 CSV 已经是英文表头（包含 `liveroom_id, resource_url, resource_type`），则**跳过转换**但做格式校验；
   * 如果是中文表头，则执行一次性转换，并覆盖原文件。

### 4.2 可以 / 需要调整的部分

1. `BaseCrawler.crawl()` 的文档注释和返回字段说明，可以根据新版爬虫增加：

   * 可以新增可选字段：

     * `db_file`: SQLite 数据库路径，如 `self.crawler.db_file`；
     * `db_total_rows`: 从 SQLite 统计的总数据条数；
   * 但不能删掉原有字段。

2. `VzanCrawler.crawl()` 内部的“行数统计”和“文件路径获取”逻辑需要适配新版爬虫：

   * 不再假设有可靠的全量 CSV；
   * 可以优先从 **SQLite** 中计算 `total_rows` 和 `failed_rows`，从增量 CSV 计算 `incremental_rows`；
   * `csv_file` 字段可以：

     * 如果新版爬虫仍然输出全量 CSV，就填入路径并做列名转换；
     * 如果已经不再输出全量 CSV，可以设置为 `None` 或留空字符串，但不能让上层逻辑崩溃（配合存在性检查）。

3. `VzanCrawler` 需要改为导入新版爬虫：

   * 从 `dynamicCrawler_vzan_v3.py` 导入 `DuanShuCrawler_vzan`，并正确设置 `backend_dir` 到包含该文件的目录。

---

## 五、具体修改指令

### 5.1 更新 `app/crawlers/base_crawler.py`

1. **保持类名与接口不变**：

   * 仍然使用 `class BaseCrawler(ABC)`；
   * 保留 `crawl()` 和 `validate_config()` 两个抽象方法；

2. **根据新版含义调整 `crawl()` 的返回文档注释**（docstring）：

   请将 `crawl()` 的 docstring 更新为：

   * 明确说明 `crawl()` 需要返回的键包括（但不限于）：

     * `csv_file`: 全量 CSV 文件路径（如果没有可以为 `None`）；
     * `incremental_file`: 必须存在，指向本轮增量 CSV 文件；
     * `failed_file`: 失败记录文件路径（如有）；
     * `total_rows`: 推荐为 SQLite 中所有记录数；
     * `incremental_rows`: 本轮增量 CSV 行数；
     * `failed_rows`: 当前失败记录数量（可通过 SQLite 中 `video_url` 为空的记录数统计）。
   * 可以在文档中补充可选字段：

     * `db_file`: SQLite 状态库路径；
     * 其他统计信息。

3. **不修改 `BaseCrawler.__init__` 的行为**，但可以在注释中补充 SQLite 相关说明（例如 `config` 中可能包含 `db_file` 之类的键）。

> 目标：让抽象层的“契约”更贴近真实返回值，但不破坏现有子类实现。

---

### 5.2 更新 `app/crawlers/vzan_crawler.py`

请在保持整体结构不变的前提下，完成以下适配工作。

#### 5.2.1 导入新版爬虫

1. 确保 `VzanCrawler` 使用的是新版爬虫文件，如：

   ```python
   backend_dir = Path(__file__).parent.parent.parent.parent
   sys.path.insert(0, str(backend_dir))
   from dynamicCrawler_vzan_v3 import DuanShuCrawler_vzan
   ```

   * 如果实际文件名不同，请根据真实文件名调整，但要保证路径设置正确。

#### 5.2.2 配置与校验保持不变

2. `__init__` 中保留对 `username`, `password`, `token` 的读取以及 `validate_config()` 的实现逻辑，避免破坏上层配置方式：

   ```python
   self.username = config.get('username')
   self.password = config.get('password')
   self.token = config.get('token')
   ```



3. 如需用到 SQLite 路径（例如 `self.crawler.db_file`），在 `__init__` 中不要直接依赖，可在 `crawl()` 内调用底层爬虫后再读取。

#### 5.2.3 crawl() 适配新版行为

4. 在 `crawl()` 方法中，请遵循以下流程：

   1. **配置校验**（保持现有逻辑）：

      ```python
      if not self.validate_config():
          raise CrawlerConfigError("VzanCrawler配置无效：缺少username, password或token")
      ```



2. **调用新版爬虫**：

   * 调用 `self.crawler.parse_all_liveroomlist_data(config)`，这一步内部会：

     * 使用 SQLite 维护状态；
     * 执行三重循环增量爬取；
     * 输出本轮增量 CSV 文件。

3. **确定各类文件路径**：

   * 尝试从 `self.crawler` 对象上读取：

     * `self.crawler.liveroom_list_savefile_inc` → 作为 `incremental_file`；
     * 若仍存在 `self.crawler.liveroom_list_savefile` → 作为 `csv_file`（否则可设为 `None`）；
     * 若仍存在 `self.crawler.failed_liveroomlist_url` → 作为 `failed_file`（否则可设为 `None`）；
   * 若 `dynamicCrawler_vzan_v3` 中变量名略有差异，请以实际代码为准，但**不要擅自造新名字**，必须阅读源码确认。

4. **CSV 列名转换（只对存在的文件做）**：

   * 始终**优先对 `incremental_file` 调用 `_convert_csv_columns()`**；
   * 如果 `csv_file` 存在，也可以调用 `_convert_csv_columns()` 做兼容处理；
   * `_convert_csv_columns()` 需满足：

     * 如果表头已经是英文（包含 `liveroom_id`, `resource_url`, `resource_type`），则打印日志并直接返回；
     * 如果是中文表头，则执行转换：

       * 列名映射见上文；
       * 输出列顺序为 `OUTPUT_COLUMNS`；
       * 仅当 `liveroom_id` 和 `resource_url` 均非空时才写入；
     * 转换过程使用临时文件 + 原子替换（`shutil.move`）策略，异常时删除临时文件并抛出异常；

5. **行数统计**：

   * `incremental_rows`：

     * 若增量 CSV 存在且表头正确，可以使用 `_count_csv_rows(incremental_file)`（不含表头）；
   * `total_rows` 与 `failed_rows`：

     * 更推荐通过 SQLite 统计（若新版爬虫暴露了便捷的统计方法，如属性或辅助函数则优先使用）；
     * 如果暂时无法从 SQLite 轻松读到，可以沿用当前 `_count_csv_rows(csv_file)` / `_count_csv_rows(failed_file)` 的策略，以不报错为前提逐步优化。

6. **构造返回结果字典**（保持兼容）：

   ```python
   result = {
       "csv_file": csv_file,                 # 可能为 None
       "incremental_file": incremental_file, # 必须尽可能指向真实增量 CSV
       "failed_file": failed_file,           # 如有
       "total_rows": total_rows,
       "incremental_rows": incremental_rows,
       "failed_rows": failed_rows,
   }

   # 允许新增字段，但不能删掉这些键
   # 比如：
   # result["db_file"] = getattr(self.crawler, "db_file", None)
   ```

7. **异常处理与资源释放**：

   * 外层捕获异常并包装成 `CrawlerError("爬取失败: ...")` 向上抛出（保持现有逻辑）；
   * 在 `finally` 块中，仍然需要调用 `self.crawler.close()` 关闭 Playwright 浏览器，避免进程泄漏：

     ```python
     finally:
         try:
             if hasattr(self, 'crawler') and self.crawler:
                 self.crawler.close()
                 logger.info("VzanCrawler: Browser closed")
         except Exception as e:
             logger.warning(f"VzanCrawler: Failed to close browser - {str(e)}")
     ```



#### 5.2.4 `_convert_csv_columns()` 幂等化与验证

5. 参考现有实现，对 `_convert_csv_columns()` 做以下保证：

   * **第一次**遇到中文表头时：

     * 完成中文→英文映射，并写出只包含 `OUTPUT_COLUMNS` 的新 CSV；
     * 之后验证转换后的 CSV 表头至少包含 `liveroom_id`, `resource_url`, `resource_type`，否则视为错误并删除该文件；
   * **后续多次调用**（已经是英文表头）：

     * 检测到英文表头后直接记录日志“已是英文表头，跳过转换”，但可以读取一行以验证格式；
   * 如果 CSV 没有表头或表头既不是预期中文，也不是预期英文，抛出 `ValueError` 提醒上层。

---

## 六、编码规范与边界条件

1. **最小改动原则**：

   * 不修改 `DownloadService`、API 层、异常/响应封装等其它模块的代码；
   * 尽量不改动 `VzanCrawler` 的对外行为，只在内部细节上适配新版爬虫；

2. **字段命名禁止乱改**：

   * 所有字段名、文件名、属性名（尤其是 `self.crawler.liveroom_list_savefile_inc` 等）必须与 `dynamicCrawler_vzan_v3.py` 中保持一致；
   * 不允许凭空发明字段名，比如把 `video_url` 改成 `play_url` 等。

3. **异常与日志**：

   * 继续使用 `CrawlerError`、`CrawlerConfigError` 等异常类型；
   * 日志：

     * `info`：开始爬取、结束爬取、CSV 转换成功等；
     * `warning`：跳过行、删除异常文件、关闭浏览器失败；
     * `error`：爬取失败、CSV 转换失败、SQLite 统计失败等。

4. **兼容性**：

   * 上层如果仍然试图在增量 CSV 不存在时回退到 `csv_file`，你的实现要确保这种情况不会直接导致异常（例如 `csv_file` 为 `None` 时，`DownloadService` 会有存在性检查）。

---

## 七、交付检查清单（给你自己用）

完成后，请确保：

1. `BaseCrawler` 接口未被破坏，`crawl()` 返回结构兼容并文档清晰；
2. `VzanCrawler` 成功导入 `dynamicCrawler_vzan_v3.py`，并能正常调用 `parse_all_liveroomlist_data`；
3. `VzanCrawler.crawl()` 返回的 `incremental_file` 指向本轮生成的增量 CSV 文件；
4. `_convert_csv_columns()` 对增量 CSV 生效，列名转换为英文并可多次安全调用；
5. 浏览器在任何情况下都会被关闭；
6. 若增量 CSV 不生成或为空，上层仍然不会因为 `csv_file`/`incremental_file` 为 `None` 或不存在而崩溃（有合理的异常或日志）。

---

以上就是完整的“改进版提示词”。你可以把这段提示词（从标题开始到检查清单结束）原样交给另一个 AI，让它在阅读现有 `base_crawler.py`、`vzan_crawler.py` 和 `dynamicCrawler_vzan_v3.py` 的基础上，按上述要求做最小改动适配。
