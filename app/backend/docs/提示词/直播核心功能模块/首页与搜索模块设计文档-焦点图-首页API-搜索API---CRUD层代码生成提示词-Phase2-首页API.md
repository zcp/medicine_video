# 首页与搜索模块 - CRUD层代码生成提示词 (Phase2: 首页API)

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块设计文档-焦点图-首页API-搜索API  
**Phase**: Phase2 - 首页API（复杂多表JOIN查询）  
**目标文件**: `backend/live_core_service/app/crud/homepage_search.py` (追加)  
**生成日期**: 2026-01-18  

---

## 📋 实施说明

本模块采用**分阶段实施策略**：
- **Phase1（已完成）**: 焦点图CRUD - 基础的增删改查操作
- **Phase2（本文档）**: 首页API - 复杂的多表JOIN和业务逻辑
- **Phase3（待生成）**: 搜索API - 跨多个表的全文搜索

**Phase2特点**：
- ⚠️ **高复杂度**：15步执行流程，多表JOIN
- ⚠️ **性能要求**：需要使用窗口函数和子查询优化
- ⚠️ **业务逻辑复杂**：Host选择、热度计算、状态判断

---

## 1. 角色定义

你是一名精通Clean Architecture、Python异步编程和PostgreSQL高级查询的资深后端开发工程师。你的任务是根据本提示词文档，生成首页API的CRUD层代码（追加到现有文件）。

---

## 2. 核心要求

### 2.1. CRUD层职责（Phase2特殊要求）

Phase2的CRUD层需要处理复杂的多表JOIN查询：
- ✅ 执行复杂的联表查询（5个表以上）
- ✅ 使用PostgreSQL高级特性（窗口函数、LATERAL JOIN）
- ✅ 返回结构化的字典数据（用于Service层组装）
- ❌ 不负责业务逻辑（Host选择、热度计算由Service层处理）
- ❌ 不负责权限检查（由Service层处理）

### 2.2. 关键技术要求

1. **异步编程**: 所有函数必须是`async def`
2. **类型提示**: 返回`List[Dict[str, Any]]`（字典列表）
3. **查询优化**: 
   - 使用`LATERAL JOIN`获取优先级最高的专家
   - 使用`LEFT JOIN`处理可能不存在的关联数据
   - 一次查询获取所有需要的数据（避免N+1问题）
4. **日志记录**: 记录查询参数和结果数量
5. **分页支持**: 需要两次查询（COUNT + SELECT）

---

## 3. 需要生成的CRUD函数清单（Phase2）

### 3.1. Homepage Rooms 查询函数（2个）

#### 函数1: `get_homepage_rooms_with_details`

**函数签名**:
```python
async def get_homepage_rooms_with_details(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    category_id: Optional[UUID] = None,
    sort: str = "heat:desc"
) -> Tuple[List[Dict[str, Any]], int]
```

**功能**: 获取首页直播间列表（含详细信息）

**执行流程** (15步):

1. **参数校验**: 验证page >= 1, size在1-100之间
2. **构建基础查询**: 从`live_rooms`表开始
3. **分类筛选**: 若提供`category_id`，添加`WHERE lr.category_id = :category_id`
4. **JOIN live_sessions**: 获取场次信息（LEFT JOIN）
5. **使用LATERAL JOIN获取场次专家**: 
   ```sql
   LEFT JOIN LATERAL (
       SELECT expert_id, role
       FROM live_session_experts
       WHERE session_id = ls.id
       ORDER BY 
           CASE role
               WHEN '主讲' THEN 1
               WHEN '主持' THEN 2
               WHEN '嘉宾' THEN 3
           END,
           sort_order ASC
       LIMIT 1
   ) lse ON TRUE
   ```
6. **JOIN experts**: 获取专家详细信息（LEFT JOIN）
7. **JOIN session_statistics**: 获取统计数据（LEFT JOIN）
8. **COUNT查询**: 执行COUNT查询获取总数
9. **排序处理**: 根据`sort`参数应用排序
   - `heat:desc`: 按热度降序（需要Service层计算）
   - `start_time:asc`: 按`ls.start_time`升序
   - `created_at:desc`: 按`lr.created_at`降序
10. **分页**: 应用`LIMIT`和`OFFSET`
11. **执行查询**: 获取当前页数据
12. **结果映射**: 将SQL结果映射为字典列表
13. **日志记录**: 记录查询参数和结果数量
14. **返回结果**: 返回`(rooms_list, total_count)`

**核心SQL模板**:
```sql
SELECT 
    -- 直播间基础信息
    lr.id AS room_id,
    lr.title AS room_title,
    lr.cover_url AS room_cover_url,
    lr.summary AS room_summary,
    lr.user_id AS room_owner_user_id,
    lr.created_at AS room_created_at,
    
    -- 场次信息
    ls.id AS session_id,
    ls.status AS session_status,
    ls.start_time AS session_start_time,
    
    -- 场次专家信息（通过LATERAL JOIN获取）
    lse.expert_id AS session_expert_id,
    lse.role AS session_expert_role,
    
    -- 专家详细信息
    e.id AS expert_id,
    e.name AS expert_name,
    e.title AS expert_title,
    e.hospital AS expert_hospital,
    
    -- 统计信息
    ss.peak_viewer_count,
    ss.total_viewer_count,
    ss.total_message_count,
    ss.total_play_count,
    ss.duration_seconds
    
FROM live_rooms lr
LEFT JOIN live_sessions ls ON ls.room_id = lr.id
-- 获取场次关联的优先级最高的专家（主讲 > 主持 > 嘉宾）
LEFT JOIN LATERAL (
    SELECT expert_id, role
    FROM live_session_experts
    WHERE session_id = ls.id
    ORDER BY 
        CASE role
            WHEN '主讲' THEN 1
            WHEN '主持' THEN 2
            WHEN '嘉宾' THEN 3
        END,
        sort_order ASC
    LIMIT 1
) lse ON TRUE
LEFT JOIN experts e ON lse.expert_id = e.id
LEFT JOIN session_statistics ss ON ls.id = ss.session_id
WHERE lr.category_id = :category_id  -- 可选条件
ORDER BY 
    CASE 
        WHEN :sort = 'start_time:asc' THEN ls.start_time
        WHEN :sort = 'created_at:desc' THEN lr.created_at
    END
LIMIT :size OFFSET :offset;
```

**返回数据结构示例**:
```python
[
    {
        "room_id": UUID("..."),
        "room_title": "肝胆胰外科手术直播演示",
        "room_cover_url": "/media/rooms/.../cover1.jpg",
        "room_summary": "演示最新的微创技术...",
        "room_owner_user_id": UUID("..."),
        "room_created_at": datetime(...),
        
        "session_id": UUID("..."),
        "session_status": "live",
        "session_start_time": datetime(...),
        
        "session_expert_id": UUID("..."),
        "session_expert_role": "主讲",
        
        "expert_id": UUID("..."),
        "expert_name": "李四 教授",
        "expert_title": "主任医师",
        "expert_hospital": "XX 医院",
        
        "peak_viewer_count": 1250,
        "total_viewer_count": 5000,
        "total_message_count": 320,
        "total_play_count": 500,
        "duration_seconds": 3650
    },
    ...
]
```

**注意事项**:
- ⚠️ 返回原始数据库字段，不进行业务逻辑处理
- ⚠️ Host选择逻辑、热度计算、live_status判断都在Service层完成
- ⚠️ 使用`LEFT JOIN`确保即使没有场次或专家也能返回房间信息
- ⚠️ LATERAL JOIN确保每个场次只返回一个优先级最高的专家

---

#### 函数2: `get_homepage_rooms_count`

**函数签名**:
```python
async def get_homepage_rooms_count(
    db: AsyncSession,
    category_id: Optional[UUID] = None
) -> int
```

**功能**: 获取首页直播间总数（用于分页）

**执行流程**:
1. 构建COUNT查询：`SELECT COUNT(DISTINCT lr.id) FROM live_rooms lr`
2. 若提供`category_id`，添加筛选条件
3. 执行查询并返回总数
4. 记录日志

**SQL模板**:
```sql
SELECT COUNT(DISTINCT lr.id)
FROM live_rooms lr
WHERE lr.category_id = :category_id;  -- 可选条件
```

---

## 4. 导入语句要求（Phase2追加）

在现有`crud/homepage_search.py`文件中追加以下导入：

```python
# Phase2追加导入
from typing import Dict, Any, Tuple
from sqlalchemy import text, and_, or_, case
from sqlalchemy.orm import aliased
```

---

## 5. 代码组织要求

### 5.1. 文件结构（追加到现有文件）

```python
# backend/live_core_service/app/crud/homepage_search.py

# ... Phase1代码（焦点图CRUD）...

# ==================== Homepage API CRUD (Phase2) ====================

async def get_homepage_rooms_with_details(...):
    """获取首页直播间列表（含详细信息）"""
    # 实现...

async def get_homepage_rooms_count(...):
    """获取首页直播间总数"""
    # 实现...
```

### 5.2. SQL查询模式

由于查询复杂度高，建议使用以下模式之一：

**模式1：使用SQLAlchemy ORM（推荐，类型安全）**
```python
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

stmt = select(
    LiveRoom,
    LiveSession,
    Expert,
    SessionStatistics
).select_from(LiveRoom).join(...).where(...)
```

**模式2：使用text()原生SQL（性能优先）**
```python
from sqlalchemy import text

query = text("""
    SELECT ...
    FROM live_rooms lr
    ...
""")
result = await db.execute(query, params)
```

**推荐**: 优先使用**模式1（SQLAlchemy ORM）**，如果性能不满足要求再使用模式2。

---

## 6. 性能优化要求

### 6.1. 查询优化

1. **避免N+1问题**: 一次查询获取所有数据
2. **使用索引**: 确保`room_id`、`session_id`、`expert_id`有索引
3. **LATERAL JOIN**: 用于获取每个场次的优先级最高的专家
4. **LIMIT优先**: 先分页再JOIN（如果可能）

### 6.2. 数据库索引需求

以下索引应该已存在（如不存在需要在迁移脚本中添加）：
- `live_rooms.category_id`
- `live_sessions.room_id`
- `live_session_experts.session_id`
- `session_statistics.session_id`

---

## 7. 测试验证要点

生成代码后，请确保：

1. ✅ 返回数据包含所有必需字段（room、session、expert、statistics）
2. ✅ 处理了场次不存在的情况（LEFT JOIN）
3. ✅ 处理了专家不存在的情况（LEFT JOIN）
4. ✅ LATERAL JOIN正确返回每个场次的优先级最高专家
5. ✅ 分页参数正确应用
6. ✅ 排序逻辑正确实现
7. ✅ COUNT查询结果正确
8. ✅ 日志记录完整

---

## 8. Phase2完成标准

Phase2（首页API的CRUD层）完成后，应该能够：

1. ✅ 执行复杂的多表JOIN查询
2. ✅ 返回结构化的原始数据（用于Service层处理）
3. ✅ 支持分页和排序
4. ✅ 支持分类筛选
5. ✅ 性能满足要求（单次查询，无N+1问题）

**下一步**: 生成Phase2的Service层和API层代码（处理Host选择、热度计算、状态判断等业务逻辑）

---

**版本历史**:
- V1.0 (2026-01-18): Phase2 - 首页API CRUD初始版本
