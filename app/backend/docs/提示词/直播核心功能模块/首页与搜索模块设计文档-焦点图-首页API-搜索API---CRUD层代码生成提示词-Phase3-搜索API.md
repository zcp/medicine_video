# 首页与搜索模块 - CRUD层代码生成提示词 (Phase3: 搜索API)

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块设计文档-焦点图-首页API-搜索API  
**Phase**: Phase3 - 搜索API（跨多表全文搜索）  
**目标文件**: `backend/live_core_service/app/crud/homepage_search.py` (追加)  
**生成日期**: 2026-01-18  

---

## 📋 实施说明

本模块采用**分阶段实施策略**：
- **Phase1（已完成）**: 焦点图CRUD - 基础的增删改查操作
- **Phase2（已完成提示词）**: 首页API - 复杂的多表JOIN和业务逻辑
- **Phase3（本文档）**: 搜索API - 跨多个表的全文搜索

**Phase3特点**：
- ⚠️ **高复杂度**：跨4个表全文搜索（room/expert/topic/brand）
- ⚠️ **性能要求**：需要使用UNION ALL合并结果
- ⚠️ **搜索质量**：支持匹配分数计算和高亮

---

## 1. 角色定义

你是一名精通Clean Architecture、Python异步编程和PostgreSQL全文搜索的资深后端开发工程师。你的任务是根据本提示词文档，生成搜索API的CRUD层代码（追加到现有文件）。

---

## 2. 核心要求

### 2.1. CRUD层职责（Phase3特殊要求）

Phase3的CRUD层需要处理跨多个表的全文搜索：
- ✅ 执行跨多个表的UNION ALL查询
- ✅ 使用PostgreSQL的ILIKE进行模糊搜索（MVP阶段）
- ✅ 计算匹配分数（基于关键词位置）
- ✅ 返回统一格式的搜索结果
- ❌ 不负责高亮处理（由Service层处理）
- ❌ 不负责结果排序（返回原始分数，由Service层排序）

### 2.2. 关键技术要求

1. **异步编程**: 所有函数必须是`async def`
2. **类型提示**: 返回`Tuple[List[Dict[str, Any]], int]`
3. **查询策略**: 
   - **MVP阶段**：使用`ILIKE`实现基础搜索
   - **未来优化**：可升级到PostgreSQL全文搜索或Elasticsearch
4. **UNION ALL**: 合并多个表的搜索结果
5. **日志记录**: 记录搜索关键词和结果数量

---

## 3. 需要生成的CRUD函数清单（Phase3）

### 3.1. Search 查询函数（1个）

#### 函数: `search_global_resources`

**函数签名**:
```python
async def search_global_resources(
    db: AsyncSession,
    keyword: str,
    page: int = 1,
    size: int = 10,
    resource_types: Optional[List[str]] = None,  # ['room', 'expert', 'topic', 'brand']
    category_id: Optional[UUID] = None  # 仅对room有效
) -> Tuple[List[Dict[str, Any]], int]
```

**功能**: 全局搜索（跨多个表）

**执行流程** (15步，参考设计文档):

1. **参数校验**: 
   - 验证keyword长度（至少2个字符）
   - 验证page >= 1, size在1-50之间
   - 如果未提供resource_types，默认搜索所有类型

2. **构建搜索关键词**: 
   - 去除首尾空格
   - 转换为模糊搜索模式：`%keyword%`

3. **确定搜索范围**: 根据resource_types决定搜索哪些表

4. **构建子查询 - room搜索**:
   ```sql
   SELECT 
       'room' AS type,
       id,
       title,
       summary,
       cover_url,
       (CASE 
           WHEN title ILIKE '%keyword%' THEN 1.0
           WHEN summary ILIKE '%keyword%' THEN 0.7
           ELSE 0.5
       END) AS match_score,
       NULL AS metadata_json  -- metadata稍后在Service层填充
   FROM live_rooms
   WHERE (title ILIKE '%keyword%' OR summary ILIKE '%keyword%')
       AND (category_id = :category_id OR :category_id IS NULL)
   ```

5. **构建子查询 - expert搜索**:
   ```sql
   SELECT 
       'expert' AS type,
       id,
       name AS title,
       bio AS summary,
       avatar_url AS cover_url,
       (CASE 
           WHEN name ILIKE '%keyword%' THEN 1.0
           WHEN bio ILIKE '%keyword%' THEN 0.8
           WHEN expertise_areas ILIKE '%keyword%' THEN 0.6
           ELSE 0.5
       END) AS match_score,
       jsonb_build_object(
           'hospital', hospital,
           'title', title
       ) AS metadata_json
   FROM experts
   WHERE (name ILIKE '%keyword%' OR bio ILIKE '%keyword%' OR expertise_areas ILIKE '%keyword%')
   ```

6. **构建子查询 - topic搜索**:
   ```sql
   SELECT 
       'topic' AS type,
       id,
       title,
       description AS summary,
       banner_url AS cover_url,
       (CASE 
           WHEN title ILIKE '%keyword%' THEN 1.0
           WHEN description ILIKE '%keyword%' THEN 0.7
           ELSE 0.5
       END) AS match_score,
       jsonb_build_object(
           'room_count', (SELECT COUNT(*) FROM topic_rooms WHERE topic_id = topics.id)
       ) AS metadata_json
   FROM topics
   WHERE (title ILIKE '%keyword%' OR description ILIKE '%keyword%')
       AND status = 'published'
   ```

7. **构建子查询 - brand搜索**:
   ```sql
   SELECT 
       'brand' AS type,
       id,
       name AS title,
       description AS summary,
       logo_url AS cover_url,
       (CASE 
           WHEN name ILIKE '%keyword%' THEN 1.0
           WHEN description ILIKE '%keyword%' THEN 0.7
           ELSE 0.5
       END) AS match_score,
       NULL AS metadata_json
   FROM brands
   WHERE (name ILIKE '%keyword%' OR description ILIKE '%keyword%')
       AND is_active = true
   ```

8. **UNION ALL合并结果**:
   ```sql
   (room查询) UNION ALL (expert查询) UNION ALL (topic查询) UNION ALL (brand查询)
   ```

9. **外层查询排序**: `ORDER BY match_score DESC`

10. **COUNT查询**: 执行COUNT查询获取总结果数（在排序和分页之前）

11. **分页**: 应用`LIMIT :size OFFSET :offset`

12. **执行查询**: 获取当前页数据

13. **结果映射**: 将SQL结果映射为字典列表

14. **日志记录**: 记录搜索关键词和结果数量

15. **返回结果**: 返回`(results_list, total_count)`

**核心SQL模板**:
```sql
WITH search_results AS (
    -- room搜索
    SELECT 
        'room' AS type,
        id,
        title,
        summary,
        cover_url,
        (CASE 
            WHEN title ILIKE :keyword THEN 1.0
            WHEN summary ILIKE :keyword THEN 0.7
            ELSE 0.5
        END) AS match_score,
        NULL AS metadata_json
    FROM live_rooms
    WHERE (title ILIKE :keyword OR summary ILIKE :keyword)
        AND (:category_id IS NULL OR category_id = :category_id)
    
    UNION ALL
    
    -- expert搜索
    SELECT 
        'expert' AS type,
        id,
        name AS title,
        bio AS summary,
        avatar_url AS cover_url,
        (CASE 
            WHEN name ILIKE :keyword THEN 1.0
            WHEN bio ILIKE :keyword THEN 0.8
            WHEN expertise_areas ILIKE :keyword THEN 0.6
            ELSE 0.5
        END) AS match_score,
        jsonb_build_object('hospital', hospital, 'title', title) AS metadata_json
    FROM experts
    WHERE name ILIKE :keyword OR bio ILIKE :keyword OR expertise_areas ILIKE :keyword
    
    UNION ALL
    
    -- topic搜索
    SELECT 
        'topic' AS type,
        id,
        title,
        description AS summary,
        banner_url AS cover_url,
        (CASE 
            WHEN title ILIKE :keyword THEN 1.0
            WHEN description ILIKE :keyword THEN 0.7
            ELSE 0.5
        END) AS match_score,
        NULL AS metadata_json  -- room_count稍后在Service层填充
    FROM topics
    WHERE (title ILIKE :keyword OR description ILIKE :keyword)
        AND status = 'published'
    
    UNION ALL
    
    -- brand搜索
    SELECT 
        'brand' AS type,
        id,
        name AS title,
        description AS summary,
        logo_url AS cover_url,
        (CASE 
            WHEN name ILIKE :keyword THEN 1.0
            WHEN description ILIKE :keyword THEN 0.7
            ELSE 0.5
        END) AS match_score,
        NULL AS metadata_json
    FROM brands
    WHERE (name ILIKE :keyword OR description ILIKE :keyword)
        AND is_active = true
)
SELECT *
FROM search_results
ORDER BY match_score DESC
LIMIT :size OFFSET :offset;
```

**返回数据结构示例**:
```python
[
    {
        "type": "room",
        "id": UUID("..."),
        "title": "肝胆胰外科手术直播演示",
        "summary": "演示最新的微创技术...",
        "cover_url": "/media/rooms/.../cover1.jpg",
        "match_score": 1.0,
        "metadata_json": None
    },
    {
        "type": "expert",
        "id": UUID("..."),
        "title": "李四 教授",
        "summary": "主任医师，擅长微创肝胆手术",
        "cover_url": "/media/experts/.../avatar.jpg",
        "match_score": 0.88,
        "metadata_json": {"hospital": "XX 医院", "title": "主任医师"}
    },
    ...
]
```

**注意事项**:
- ⚠️ 返回原始匹配分数，不进行业务逻辑处理
- ⚠️ 高亮文本在Service层生成
- ⚠️ metadata字段在Service层根据type填充更多信息
- ⚠️ 使用ILIKE（MVP阶段），未来可升级到PostgreSQL全文搜索或Elasticsearch

---

## 4. 导入语句要求（Phase3追加）

在现有`crud/homepage_search.py`文件中追加以下导入（如尚未导入）：

```python
# Phase3追加导入
from typing import List
```

---

## 5. 代码组织要求

### 5.1. 文件结构（追加到现有文件）

```python
# backend/live_core_service/app/crud/homepage_search.py

# ... Phase1代码（焦点图CRUD）...
# ... Phase2代码（首页API）...

# ==================== Search API CRUD (Phase3) ====================

async def search_global_resources(...):
    """全局搜索（跨多个表）"""
    # 实现...
```

### 5.2. SQL查询模式

**推荐使用text()原生SQL**（因为跨多个表的UNION ALL查询在SQLAlchemy ORM中难以表达）:

```python
from sqlalchemy import text

query = text("""
    WITH search_results AS (
        ...
    )
    SELECT * FROM search_results
    ORDER BY match_score DESC
    LIMIT :size OFFSET :offset
""")

result = await db.execute(query, {
    "keyword": f"%{keyword}%",
    "category_id": category_id,
    "size": size,
    "offset": (page - 1) * size
})
```

---

## 6. 性能优化要求

### 6.1. 查询优化

1. **使用UNION ALL而非UNION**: UNION ALL不去重，性能更好
2. **索引需求**: 确保搜索字段有适当的索引（或使用全文搜索索引）
3. **限制搜索范围**: 通过resource_types参数减少搜索的表数量

### 6.2. 未来优化方向

**阶段1（当前 - MVP）**: 使用ILIKE实现基础搜索
- ✅ 简单易实现
- ⚠️ 性能较差（全表扫描）
- ⚠️ 不支持中文分词

**阶段2（优化）**: 使用PostgreSQL全文搜索
```sql
-- 添加全文搜索列和索引
ALTER TABLE live_rooms ADD COLUMN search_vector tsvector;
CREATE INDEX idx_live_rooms_search ON live_rooms USING gin(search_vector);

-- 搜索查询
SELECT *, ts_rank(search_vector, query) AS rank
FROM live_rooms, to_tsquery('肝胆 & 外科') query
WHERE search_vector @@ query
ORDER BY rank DESC;
```

**阶段3（高级）**: 集成Elasticsearch
- ✅ 支持中文分词
- ✅ 支持同义词和拼音搜索
- ✅ 更精确的相关性评分
- ⚠️ 需要额外的基础设施

---

## 7. 测试验证要点

生成代码后，请确保：

1. ✅ 搜索能覆盖所有指定的表（room/expert/topic/brand）
2. ✅ 匹配分数计算正确（标题匹配分数最高）
3. ✅ UNION ALL正确合并所有结果
4. ✅ 分页参数正确应用
5. ✅ COUNT查询结果正确
6. ✅ 支持resource_types筛选
7. ✅ 支持category_id筛选（仅对room有效）
8. ✅ 日志记录完整
9. ✅ 关键词长度验证（至少2个字符）

---

## 8. Phase3完成标准

Phase3（搜索API的CRUD层）完成后，应该能够：

1. ✅ 执行跨多个表的全文搜索
2. ✅ 返回统一格式的搜索结果
3. ✅ 计算匹配分数
4. ✅ 支持分页和类型筛选
5. ✅ 性能满足MVP阶段要求（使用ILIKE）

**下一步**: 生成Phase3的Service层和API层代码（处理高亮、metadata填充等）

---

**版本历史**:
- V1.0 (2026-01-18): Phase3 - 搜索API CRUD初始版本
