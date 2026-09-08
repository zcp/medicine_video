# 首页与搜索模块 - Service层和API层代码生成提示词 (Phase2: 首页API)

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块设计文档-焦点图-首页API-搜索API  
**Phase**: Phase2 - 首页API（复杂业务逻辑处理）  
**目标文件**: 
- `backend/live_core_service/app/services/homepage_search_service.py` (追加)
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py` (追加)

**生成日期**: 2026-01-18  

---

## 📋 实施说明

本模块采用**分阶段实施策略**：
- **Phase1（已完成）**: 焦点图CRUD - Service层和API层
- **Phase2（本文档）**: 首页API - 复杂业务逻辑处理
- **Phase3（待生成）**: 搜索API - 全文搜索Service和API

**Phase2特点**：
- ⚠️ **高复杂度**：Host选择、热度计算、状态判断
- ⚠️ **数据转换**：将CRUD层的原始数据转换为API Schema
- ⚠️ **性能优化**：Service层处理业务逻辑，避免多次数据库查询

---

## 1. 角色定义

你是一名精通Clean Architecture和FastAPI的资深Python后端架构师。你的任务是根据本提示词文档，生成首页API的Service层和API层代码（追加到现有文件）。

---

## 2. 核心要求

### 2.1. Service层职责（Phase2特殊要求）

Phase2的Service层需要处理复杂的业务逻辑：
- ✅ 调用CRUD层获取原始数据
- ✅ Host选择逻辑（优先级：场次主讲专家 > 场次其他专家 > null）
- ✅ 热度计算（基于统计数据）
- ✅ live_status判断（live/scheduled/replay）
- ✅ status_data构造（根据状态填充不同字段）
- ✅ 数据转换为Pydantic Schema
- ❌ 不负责数据库操作（由CRUD层处理）

### 2.2. API层职责（Phase2特殊要求）

Phase2的API层是公开接口：
- ✅ 无需认证（公开访问）
- ✅ 参数解析（page、size、sort、category_id）
- ✅ 调用Service层方法
- ✅ 异常处理
- ✅ 返回JSON响应

---

## 3. Service层方法清单（Phase2）

### 3.1. Homepage API Service方法（1个核心方法）

#### 方法: `get_homepage_rooms`

**函数签名**:
```python
async def get_homepage_rooms(
    self,
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    sort: str = "heat:desc",
    category_id: Optional[UUID] = None
) -> dict
```

**功能**: 获取首页直播间列表（处理所有业务逻辑）

**执行流程**:

1. **调用CRUD层**: 获取原始数据
   ```python
   rooms_raw, total = await crud.get_homepage_rooms_with_details(
       db, page, size, category_id, sort
   )
   ```

2. **遍历每个房间，应用业务逻辑**:
   
   **2.1. Host选择逻辑**:
   ```python
   def _select_host(room_data: Dict) -> Optional[HomepageHostInfo]:
       """
       Host选择逻辑
       
       优先级：
       1. 场次主讲专家（session_expert_role == '主讲'）
       2. 场次其他专家（session_expert_role in ['主持', '嘉宾']）
       3. null（场次没有关联专家）
       
       注意：不再使用房主专家或房主用户ID
       """
       # 如果场次有关联专家
       if room_data.get('expert_id'):
           return HomepageHostInfo(
               expert_id=room_data['expert_id'],
               user_id=None,  # 专家情况下user_id为None
               name=room_data['expert_name'],
               title=room_data['expert_title'],
               hospital=room_data['expert_hospital']
           )
       
       # 场次没有关联专家，返回null
       return None
   ```

   **2.2. live_status判断**:
   ```python
   def _determine_live_status(session_status: Optional[str]) -> LiveStatusEnum:
       """
       确定直播状态
       
       映射关系：
       - session_status == 'live' → LiveStatusEnum.LIVE
       - session_status in ['ready', 'scheduled'] → LiveStatusEnum.SCHEDULED
       - session_status in ['ended', 'archived'] → LiveStatusEnum.REPLAY
       - session_status is None → LiveStatusEnum.REPLAY（默认）
       """
       if session_status == 'live':
           return LiveStatusEnum.LIVE
       elif session_status in ['ready', 'scheduled']:
           return LiveStatusEnum.SCHEDULED
       else:
           return LiveStatusEnum.REPLAY
   ```

   **2.3. status_data构造**:
   ```python
   def _build_status_data(
       live_status: LiveStatusEnum,
       room_data: Dict
   ) -> HomepageStatusData:
       """
       构造状态数据
       
       规则：
       - live: 填充viewer_count（peak_viewer_count）
       - scheduled: 填充start_time（session_start_time）
       - replay: 填充duration_seconds和play_count（total_play_count）
       """
       if live_status == LiveStatusEnum.LIVE:
           return HomepageStatusData(
               viewer_count=room_data.get('peak_viewer_count'),
               start_time=None,
               duration_seconds=None,
               play_count=None
           )
       elif live_status == LiveStatusEnum.SCHEDULED:
           return HomepageStatusData(
               viewer_count=None,
               start_time=room_data.get('session_start_time'),
               duration_seconds=None,
               play_count=None
           )
       else:  # REPLAY
           return HomepageStatusData(
               viewer_count=None,
               start_time=None,
               duration_seconds=room_data.get('duration_seconds'),
               play_count=room_data.get('total_play_count')
           )
   ```

   **2.4. 热度计算**:
   ```python
   def _calculate_heat(room_data: Dict) -> Optional[int]:
       """
       计算热度值
       
       公式（简化版）：
       heat = (
           peak_viewer_count * 10 +
           total_viewer_count * 1 +
           total_message_count * 5 +
           total_play_count * 2
       )
       
       注意：
       - 如果所有统计数据都为None，返回None
       - 如果部分数据为None，视为0
       """
       peak_viewer = room_data.get('peak_viewer_count') or 0
       total_viewer = room_data.get('total_viewer_count') or 0
       total_message = room_data.get('total_message_count') or 0
       total_play = room_data.get('total_play_count') or 0
       
       # 如果所有数据都是0（原始数据都是None），返回None
       if peak_viewer == 0 and total_viewer == 0 and total_message == 0 and total_play == 0:
           return None
       
       heat = (
           peak_viewer * 10 +
           total_viewer * 1 +
           total_message * 5 +
           total_play * 2
       )
       
       return heat
   ```

3. **构造HomepageRoomItem**:
   ```python
   room_item = HomepageRoomItem(
       id=room_data['room_id'],
       title=room_data['room_title'],
       cover_url=room_data['room_cover_url'],
       summary=room_data['room_summary'],
       live_status=live_status,
       host=host,
       status_data=status_data,
       heat=heat
   )
   ```

4. **应用排序**:
   - 如果`sort='heat:desc'`，需要在Service层按heat字段降序排序
   - 其他排序已在CRUD层完成

5. **构造分页响应**:
   ```python
   paginated_data = PaginatedData(
       total=total,
       page=page,
       size=size,
       items=room_items
   )
   ```

6. **返回响应**:
   ```python
   return {
       "code": 200,
       "message": "success",
       "data": paginated_data,
       "timestamp": datetime.utcnow()
   }
   ```

---

## 4. API层端点清单（Phase2）

### 4.1. 公开端点（1个）

#### 端点: 获取首页直播间列表

**路由定义**:
```python
@router.get("/homepage/rooms", response_model=None, tags=["Homepage API"])
async def get_homepage_rooms_endpoint(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: str = Query("heat:desc", regex="^(heat:desc|start_time:asc|created_at:desc)$", description="排序规则"),
    category_id: Optional[UUID] = Query(None, description="分类ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页直播间列表（公开接口）
    
    - 无需认证
    - 支持分页
    - 支持排序（热度、开始时间、创建时间）
    - 支持分类筛选
    - 包含实时状态、主讲专家、热度等信息
    """
    try:
        service = HomepageSearchService()
        result = await service.get_homepage_rooms(
            db, page, size, sort, category_id
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        logger.error(f"获取首页直播间列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

**请求示例**:
```
GET /api/v1/homepage/rooms?page=1&size=10&sort=heat:desc&category_id=uuid-123
```

**响应示例** (参考设计文档第1166-1236行):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "room_uuid_1",
        "title": "肝胆胰外科手术直播演示",
        "cover_url": "/media/rooms/.../cover1.jpg",
        "summary": "演示最新的微创技术...",
        "live_status": "live",
        "host": {
          "expert_id": "expert_uuid_doc_B",
          "user_id": null,
          "name": "李四 教授",
          "title": "主任医师",
          "hospital": "XX 医院"
        },
        "status_data": {
          "viewer_count": 1250,
          "start_time": null,
          "duration_seconds": null,
          "play_count": null
        },
        "heat": 8500
      }
    ]
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

---

## 5. 导入语句要求（Phase2追加）

### 5.1. Service层导入（追加）

```python
# Phase2追加导入
from typing import Dict
from app.schemas.homepage_search import (
    LiveStatusEnum,
    HomepageHostInfo,
    HomepageStatusData,
    HomepageRoomItem,
    HomepageRoomsResponse,
    PaginatedData
)
```

### 5.2. API层导入（追加）

```python
# Phase2追加导入
from uuid import UUID
from typing import Optional
from fastapi import Query
```

---

## 6. 代码组织要求

### 6.1. Service层（追加到现有类）

```python
class HomepageSearchService:
    """首页与搜索模块Service层"""
    
    # ... Phase1方法（焦点图CRUD）...
    
    # ==================== Homepage API Service方法 (Phase2) ====================
    
    def _select_host(self, room_data: Dict) -> Optional[HomepageHostInfo]:
        """Host选择逻辑（私有方法）"""
        # 实现...
    
    def _determine_live_status(self, session_status: Optional[str]) -> LiveStatusEnum:
        """确定直播状态（私有方法）"""
        # 实现...
    
    def _build_status_data(
        self,
        live_status: LiveStatusEnum,
        room_data: Dict
    ) -> HomepageStatusData:
        """构造状态数据（私有方法）"""
        # 实现...
    
    def _calculate_heat(self, room_data: Dict) -> Optional[int]:
        """计算热度值（私有方法）"""
        # 实现...
    
    async def get_homepage_rooms(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        sort: str = "heat:desc",
        category_id: Optional[UUID] = None
    ) -> dict:
        """获取首页直播间列表（公开方法）"""
        # 实现...
```

### 6.2. API层（追加到现有路由器）

```python
# backend/live_core_service/app/api/v1/endpoints/homepage_search.py

# ... Phase1端点（焦点图CRUD）...

# ==================== Homepage API端点 (Phase2) ====================

@router.get("/homepage/rooms", response_model=None, tags=["Homepage API"])
async def get_homepage_rooms_endpoint(...):
    """获取首页直播间列表"""
    # 实现...
```

---

## 7. 业务逻辑详细说明

### 7.1. Host选择逻辑（关键）

根据设计文档，Host选择逻辑已简化：
- ✅ **优先使用场次关联的专家**（通过`live_session_experts`表）
- ✅ **专家优先级**：主讲 > 主持 > 嘉宾（在CRUD层的LATERAL JOIN中已处理）
- ✅ **如果场次没有关联任何专家**：`host`为`null`
- ❌ **不再使用房主专家或房主用户ID**

**伪代码**:
```python
if room_data.get('expert_id'):
    host = HomepageHostInfo(
        expert_id=room_data['expert_id'],
        user_id=None,
        name=room_data['expert_name'],
        title=room_data['expert_title'],
        hospital=room_data['expert_hospital']
    )
else:
    host = None
```

### 7.2. 热度计算公式

**公式**:
```
heat = peak_viewer_count * 10 
     + total_viewer_count * 1 
     + total_message_count * 5 
     + total_play_count * 2
```

**说明**:
- 峰值观看人数权重最高（10）
- 留言数权重较高（5）
- 总观看人数权重较低（1）
- 播放次数权重中等（2）

**边界情况**:
- 如果所有统计数据都是`None`，返回`None`
- 如果部分数据是`None`，视为`0`

### 7.3. live_status判断

**映射规则**:
```python
session_status → live_status
'live'         → LiveStatusEnum.LIVE
'ready'        → LiveStatusEnum.SCHEDULED
'scheduled'    → LiveStatusEnum.SCHEDULED
'ended'        → LiveStatusEnum.REPLAY
'archived'     → LiveStatusEnum.REPLAY
None           → LiveStatusEnum.REPLAY
```

### 7.4. status_data构造

**规则**:
| live_status | viewer_count | start_time | duration_seconds | play_count |
|-------------|--------------|------------|------------------|------------|
| LIVE        | ✅ 填充      | ❌ null    | ❌ null          | ❌ null    |
| SCHEDULED   | ❌ null      | ✅ 填充    | ❌ null          | ❌ null    |
| REPLAY      | ❌ null      | ❌ null    | ✅ 填充          | ✅ 填充    |

---

## 8. 测试验证要点

生成代码后，请确保：

1. ✅ Host选择逻辑正确（场次专家优先）
2. ✅ 热度计算公式正确实现
3. ✅ live_status判断正确（三种状态）
4. ✅ status_data根据状态正确填充
5. ✅ 处理了专家不存在的情况（host=null）
6. ✅ 处理了统计数据不存在的情况（heat=null）
7. ✅ 分页响应结构正确
8. ✅ 排序逻辑正确（特别是heat:desc需要在Service层排序）
9. ✅ API参数验证正确（page >= 1, size在1-100之间）
10. ✅ 日志记录完整

---

## 9. Phase2完成标准

Phase2（首页API的Service和API）完成后，应该能够：

1. ✅ 调用API获取首页直播间列表
2. ✅ Host信息正确显示（场次专家优先）
3. ✅ 热度值正确计算
4. ✅ 直播状态正确判断
5. ✅ 状态数据正确填充
6. ✅ 分页、排序、筛选功能正常
7. ✅ 所有业务逻辑符合设计文档要求

**下一步**: Phase3将实现搜索API（跨多个表的全文搜索）

---

**版本历史**:
- V1.0 (2026-01-18): Phase2 - 首页API Service和API初始版本
