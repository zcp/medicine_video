
### **修改提示词文档**

#### **1. 目标**

将现有爬虫代码 `dynamicCrawler_vzan_v3.py` 修改为符合新的爬虫修改提示词 v2 中的要求，具体修改内容包括：

* **URL 标准化**：在存储 URL 到 SQLite 之前，确保对所有的 URL 字段进行标准化（包括 `video_url`、`cover_url`、`liveroom_url` 等）。
* **除重设计**：通过使用 `zlib` 和基于 `zbId`、`id` 和 `video_url` 的复合唯一索引，实现数据库层级的除重。
* **修改要点**：遵循“最小化修改，增加开发”原则，确保只修改必要的部分。

#### **2. 关键修改要求**

* **URL 标准化**：在存入数据库之前，所有 URL 字段必须进行标准化处理。新的标准化方法已在 `爬虫修改提示词v2.md` 中描述，并提供了 `normalize_url(url)` 方法。
* **数据库层级除重**：在 SQLite 数据库中，使用 `zbId + id + video_url` 的组合来实现去重，通过唯一索引保证数据的唯一性。

#### **3. 修改步骤**

1. **增加 `normalize_url` 方法**：

   * 在 `dynamicCrawler_vzan_v3.py` 中增加 URL 标准化的方法。该方法将在所有 URL 字段存入数据库之前执行，确保统一的 URL 格式。
   * **示例代码**：

     ```python
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
     ```

2. **修改 `save_single_to_db` 方法**：

   * 在 `save_single_to_db` 方法中，修改存储逻辑，确保在将 `video_url` 和其他 URL 字段存储到 SQLite 数据库之前，调用 `normalize_url()` 进行标准化。
   * **示例代码**：

     ```python
     def save_single_to_db(self, live_info):
         """
         将单条数据写入SQLite数据库
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
                 live_info.get('starttime', ''),
                 live_info.get('zbId', ''),
                 live_info.get('liveType', ''),
                 live_info.get('viewCount', 0),
                 live_info.get('videosrc', ''),
                 live_info.get('liveroom_url', ''),
                 live_info.get('video_url', ''),
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
     ```

3. **增加数据库除重设计**：

   * 修改数据库设计，确保 `zbId`、`id` 和 `video_url` 组合唯一。为此，需要在 SQLite 中添加复合唯一索引。
   * **示例代码**：

     ```python
     cursor.execute(''' 
         CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_liveroom_video 
         ON liversoms(zbId, id, video_url);
     ''')
     ```

4. **最小化修改其他代码**：

   * 确保爬虫的其他部分保持不变，只在需要进行 URL 标准化和除重的地方进行修改。
   * 确保在所有存储数据的地方使用标准化 URL。

---

#### **4. 额外注意事项**

* **只修改必要部分**：确保修改仅限于 URL 标准化和除重的相关部分，不修改其他业务逻辑。
* **性能优化**：`INSERT OR REPLACE` 已经使用了 SQLite 的唯一索引来处理除重，因此不需要额外的查询来判断是否存在。
* **测试**：在修改后，确保进行充分的测试，检查 URL 的标准化效果及数据库中的去重是否有效。

---

