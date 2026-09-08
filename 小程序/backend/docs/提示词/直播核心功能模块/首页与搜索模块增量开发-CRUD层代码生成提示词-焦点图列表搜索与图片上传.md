# 首页与搜索模块增量开发 - CRUD 层代码生成提示词（焦点图列表搜索与图片上传）

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块（焦点图管理）  
**增量主题**: 焦点图列表搜索（q/search_type）与图片上传  
**目标文件**: `backend/live_core_service/app/crud/homepage_search.py`  
**基准提示词**: 《首页与搜索模块设计文档-焦点图-首页API-搜索API---CRUD层代码生成提示词-Phase1-焦点图.md》

---

## 1. 角色定义

在既有首页与搜索模块 Phase1 焦点图 CRUD 提示词基础上，按本增量提示词**仅修改**下列函数，不重写未变更函数。CRUD 层职责、异步与类型提示、事务与异常约定、日志脱敏等与基准提示词一致。

---

## 2. Model 字段变更摘要

无。本次不涉及 Model 变更。`FeaturedContent` 已有字段 `id`（UUID）、`title`、`subtitle`、`image_url`、`sort_order`、`created_at` 等，见 `app/models/homepage_search.py`。

---

## 3. 需要修改的 CRUD 函数清单

### 3.1 修改：`get_featured_content_list_paginated`

**函数签名（修改后）**:

```python
async def get_featured_content_list_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    q: Optional[str] = None,
    search_type: Optional[str] = None
) -> Tuple[List[FeaturedContent], int]:
```

**功能**: 获取焦点图列表（管理员用，分页）。不施加 is_active、start_at、end_at 过滤；支持按关键词 `q` 与 `search_type` 过滤（与前端《列表筛选与搜索规范》对齐）；排序 `sort_order ASC, created_at DESC`；总数与列表使用同一套 WHERE 条件。

**执行流程（变更步骤）**:

1. 保留现有 page/size 校验与 `offset = (page - 1) * size`。
2. **构建 where_conditions**（在 count 与 list 查询前）：
   - 若 `q` 非空且 `search_type == "id"`：
     - 尝试 `featured_id = UUID(q)`；成功则 `where_conditions = [FeaturedContent.id == featured_id]`；
     - 若 `ValueError`，则 `where_conditions = [text("1=0")]`（兜底，与 API 层 400 语义一致）。
   - 否则若 `q` 非空：`where_conditions = [or_(FeaturedContent.title.ilike(f"%{q}%"), FeaturedContent.subtitle.ilike(f"%{q}%"))]`。
   - 若 `q` 为空或 None：`where_conditions = []`。
3. **总数查询**：`count_query = select(func.count()).select_from(FeaturedContent)`；若 `where_conditions` 非空则 `count_query = count_query.where(and_(*where_conditions))`；执行得 `total`。
4. **列表查询**：`query = select(FeaturedContent)`；若 `where_conditions` 非空则 `query = query.where(and_(*where_conditions))`；然后 `.order_by(FeaturedContent.sort_order.asc(), FeaturedContent.created_at.desc()).offset(offset).limit(size)`；执行得 `items`。
5. **日志**：return 前 `logger.info(..., q=q, search_type=search_type)`（与现有 page、size、total 一并记录）。
6. `return items, total`。

**导入**: 确保有 `from uuid import UUID`（或使用 `uuid.UUID`）；已有 `from sqlalchemy import select, func, or_, and_, text` 及 `Optional`、`Tuple`、`List`。

**注意**: `FeaturedContent.id` 为 UUID 类型，使用 `FeaturedContent.id == UUID(q)`。

---

## 4. 需要约定的 CRUD 函数（无代码变更）

- `get_featured_content_by_id`、`update_featured_content` 等：本次未修改，图片上传流程中由 Service 层调用现有 `get_featured_content_by_id` 与 `update_featured_content`，无需在 CRUD 层新增函数。

---

## 5. 质量标准

与既有 CRUD 提示词在「异步、类型提示、事务与 IntegrityError、日志脱敏、安全异步异常处理」等方面要求一致。不改变未被列出的 CRUD 函数的签名与行为。
