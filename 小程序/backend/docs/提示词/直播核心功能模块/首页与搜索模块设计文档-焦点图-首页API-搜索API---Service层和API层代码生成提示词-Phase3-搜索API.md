# 首页与搜索模块 - Service层和API层代码生成提示词 (Phase3: 搜索API)

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块设计文档-焦点图-首页API-搜索API  
**Phase**: Phase3 - 搜索API（高亮和metadata处理）  
**目标文件**: 
- `backend/live_core_service/app/services/homepage_search_service.py` (追加)
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py` (追加)

**生成日期**: 2026-01-18  

---

## 📋 实施说明

本模块采用**分阶段实施策略**：
- **Phase1（已完成）**: 焦点图CRUD - Service层和API层
- **Phase2（已完成提示词）**: 首页API - 复杂业务逻辑处理
- **Phase3（本文档）**: 搜索API - 高亮和metadata处理

**Phase3特点**：
- ⚠️ **高亮处理**：将匹配的关键词用`<em>`标签包裹
- ⚠️ **metadata填充**：根据资源类型填充不同的元数据
- ⚠️ **性能优化**：Service层处理业务逻辑，避免多次数据库查询

---

## 1. Service层方法清单（Phase3）

### 1.1. Search API Service方法（1个核心方法）

#### 方法: `search_resources`

**函数签名**:
```python
async def search_resources(
    self,
    db: AsyncSession,
    keyword: str,
    page: int = 1,
    size: int = 10,
    resource_types: Optional[List[str]] = None,
    category_id: Optional[UUID] = None
) -> dict
```

**功能**: 全局搜索（处理高亮和metadata）

**执行流程**:

1. **参数校验**: 验证keyword长度（至少2个字符）

2. **调用CRUD层**: 获取原始搜索结果
   ```python
   results_raw, total = await crud.search_global_resources(
       db, keyword, page, size, resource_types, category_id
   )
   ```

3. **遍历每个结果，应用业务逻辑**:
   
   **3.1. 生成高亮文本**:
   ```python
   def _generate_highlight(text: str, keyword: str) -> str:
       """
       生成高亮文本
       
       将匹配的关键词用<em>标签包裹
       """
       import re
       # 不区分大小写的替换
       pattern = re.compile(re.escape(keyword), re.IGNORECASE)
       highlighted = pattern.sub(lambda m: f"<em>{m.group()}</em>", text)
       return highlighted
   ```

   **3.2. 填充metadata**:
   ```python
   def _fill_metadata(result: Dict) -> Dict[str, Any]:
       """
       根据资源类型填充metadata
       
       - room: 需要查询live_status和viewer_count（可选，MVP阶段可返回空）
       - expert: 使用CRUD层返回的metadata_json
       - topic: 需要查询room_count（可选，MVP阶段可返回空）
       - brand: 返回空metadata
       """
       result_type = result['type']
       
       if result_type == 'room':
           # MVP阶段：返回简化的metadata
           return {}
       
       elif result_type == 'expert':
           # 使用CRUD层返回的metadata_json
           return result.get('metadata_json') or {}
       
       elif result_type == 'topic':
           # MVP阶段：返回简化的metadata
           return {}
       
       elif result_type == 'brand':
           return {}
       
       return {}
   ```

4. **构造SearchResultItem**:
   ```python
   search_item = SearchResultItem(
       type=SearchResultType(result['type']),
       id=result['id'],
       title=result['title'],
       summary=result['summary'],
       cover_url=result['cover_url'],
       match_score=result['match_score'],
       highlight=highlight_text,
       metadata=metadata
   )
   ```

5. **构造分页响应**:
   ```python
   paginated_data = PaginatedData(
       total=total,
       page=page,
       size=size,
       items=search_items
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

## 2. API层端点清单（Phase3）

### 2.1. 公开端点（1个）

#### 端点: 全局搜索

**路由定义**:
```python
@router.get("/search", response_model=None, tags=["Search API"])
async def search_resources_endpoint(
    q: str = Query(..., min_length=2, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    type: Optional[str] = Query(None, description="资源类型筛选（逗号分隔）"),
    category_id: Optional[UUID] = Query(None, description="分类ID筛选（仅对room有效）"),
    db: AsyncSession = Depends(get_db)
):
    """
    全局搜索接口
    
    - 无需认证
    - 支持跨直播间、专家、专题、品牌的模糊搜索
    - 支持分页
    - 支持资源类型筛选
    - 返回匹配分数和高亮文本
    """
    try:
        # 解析type参数（逗号分隔）
        resource_types = None
        if type:
            resource_types = [t.strip() for t in type.split(',')]
        
        service = HomepageSearchService()
        result = await service.search_resources(
            db, q, page, size, resource_types, category_id
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except InvalidParameterException as e:
        logger.warning(f"搜索参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

**请求示例**:
```
GET /api/v1/search?q=肝胆外科&page=1&size=10&type=room,expert&category_id=uuid-123
```

**响应示例** (参考设计文档第1335-1388行):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "items": [
      {
        "type": "room",
        "id": "room_uuid_1",
        "title": "肝胆胰外科手术直播演示",
        "summary": "演示最新的微创技术...",
        "cover_url": "/media/rooms/.../cover1.jpg",
        "match_score": 0.95,
        "highlight": "肝胆胰<em>外科</em>手术直播演示",
        "metadata": {}
      },
      {
        "type": "expert",
        "id": "expert_uuid_doc_B",
        "title": "李四 教授",
        "summary": "主任医师，擅长微创肝胆手术",
        "cover_url": "/media/experts/.../avatar.jpg",
        "match_score": 0.88,
        "highlight": "擅长微创<em>肝胆</em>手术",
        "metadata": {
          "hospital": "XX 医院",
          "title": "主任医师"
        }
      }
    ]
  },
  "timestamp": "2025-10-23T17:00:00Z"
}
```

---

## 3. 导入语句要求（Phase3追加）

### 3.1. Service层导入（追加）

```python
# Phase3追加导入
import re
from app.schemas.homepage_search import (
    SearchResultType,
    SearchResultItem,
    SearchResponse
)
```

### 3.2. API层导入（追加）

```python
# Phase3追加导入
from fastapi import Query
```

---

## 4. 代码组织要求

### 4.1. Service层（追加到现有类）

```python
class HomepageSearchService:
    """首页与搜索模块Service层"""
    
    # ... Phase1方法（焦点图CRUD）...
    # ... Phase2方法（首页API）...
    
    # ==================== Search API Service方法 (Phase3) ====================
    
    def _generate_highlight(self, text: str, keyword: str) -> str:
        """生成高亮文本（私有方法）"""
        # 实现...
    
    def _fill_metadata(self, result: Dict, result_type: str) -> Dict[str, Any]:
        """填充metadata（私有方法）"""
        # 实现...
    
    async def search_resources(
        self,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        size: int = 10,
        resource_types: Optional[List[str]] = None,
        category_id: Optional[UUID] = None
    ) -> dict:
        """全局搜索（公开方法）"""
        # 实现...
```

### 4.2. API层（追加到现有路由器）

```python
# backend/live_core_service/app/api/v1/endpoints/homepage_search.py

# ... Phase1端点（焦点图CRUD）...
# ... Phase2端点（首页API）...

# ==================== Search API端点 (Phase3) ====================

@router.get("/search", response_model=None, tags=["Search API"])
async def search_resources_endpoint(...):
    """全局搜索接口"""
    # 实现...
```

---

## 5. 业务逻辑详细说明

### 5.1. 高亮生成逻辑

**要求**:
- 不区分大小写匹配
- 使用`<em>`标签包裹匹配的关键词
- 保留原始大小写

**实现示例**:
```python
import re

def _generate_highlight(text: str, keyword: str) -> str:
    if not text or not keyword:
        return text or ""
    
    # 不区分大小写的替换
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f"<em>{m.group()}</em>", text)
    
    return highlighted
```

### 5.2. metadata填充逻辑

**MVP阶段（简化）**:
- room: 返回空字典`{}`（避免额外查询）
- expert: 使用CRUD层返回的`metadata_json`
- topic: 返回空字典`{}`（避免额外查询）
- brand: 返回空字典`{}`

**未来优化**:
- room: 查询live_status和viewer_count
- topic: 查询room_count

---

## 6. 测试验证要点

生成代码后，请确保：

1. ✅ 高亮文本正确生成（关键词被`<em>`标签包裹）
2. ✅ 高亮不区分大小写
3. ✅ metadata根据资源类型正确填充
4. ✅ 搜索结果包含所有必需字段
5. ✅ 分页响应结构正确
6. ✅ API参数验证正确（keyword至少2个字符）
7. ✅ type参数正确解析（逗号分隔）
8. ✅ 异常处理完整
9. ✅ 日志记录完整

---

## 7. Phase3完成标准

Phase3（搜索API的Service和API）完成后，应该能够：

1. ✅ 调用API执行全局搜索
2. ✅ 搜索结果包含高亮文本
3. ✅ 搜索结果包含匹配分数
4. ✅ metadata根据资源类型正确填充
5. ✅ 支持分页、类型筛选、分类筛选
6. ✅ 所有业务逻辑符合设计文档要求

**至此，首页与搜索模块的所有3个Phase全部完成！**

---

**版本历史**:
- V1.0 (2026-01-18): Phase3 - 搜索API Service和API初始版本
