# 首页与搜索模块增量开发 - CRUD 层代码生成提示词（焦点图管理端分页列表）

**模块名称**: 首页与搜索模块  
**增量主题**: 焦点图管理端分页列表接口  
**目标文件**: `backend/live_core_service/app/crud/homepage_search.py`  
**基于**: 《首页与搜索模块增量开发设计文档-焦点图管理端分页列表接口.md》  
**配套**: 与《首页与搜索模块设计文档-焦点图-首页API-搜索API---CRUD层代码生成提示词-Phase1-焦点图.md》同构使用，仅新增下列函数。

---

## 1. 角色定义

在既有首页与搜索模块 Phase1 CRUD 提示词基础上，按本增量提示词**仅新增**下列函数；不修改已有函数签名与行为。

---

## 2. Model 字段变更摘要

无。沿用 `FeaturedContent` 模型（见 Phase1 提示词 Section 3.1）。

---

## 3. 需要新增的 CRUD 函数清单

### 3.1 函数：`get_featured_content_list_paginated`

**函数签名**:

```python
async def get_featured_content_list_paginated(
    db: AsyncSession,
    page: int = 1,
    size: int = 10
) -> Tuple[List[FeaturedContent], int]
```

**功能**: 获取焦点图列表（管理员用，分页）。不施加 `is_active`、`start_at`、`end_at` 过滤，返回全部记录的分页结果及总数。

**执行流程**:

1. 参数校验：若 `page < 1` 则设为 1；若 `size < 1` 则设为 10，若 `size > 100` 则设为 100。
2. 计算 `offset = (page - 1) * size`。
3. 总数查询：`select(func.count()).select_from(FeaturedContent)`，执行得 `total`。
4. 列表查询：`select(FeaturedContent).order_by(FeaturedContent.sort_order).offset(offset).limit(size)`，执行得当前页 `items`。
5. 记录日志：`logger.info(f"查询焦点图列表（分页），page={page}, size={size}, total={total}")`
6. 返回 `(list(items), total)`。

**异常/日志**: 仅 INFO 日志，UUID 不在此函数内输出；与既有 CRUD 风格一致。

**注意**: 不在此函数内做权限或 is_active/时间过滤；权限由 Service 层保证，本函数仅负责分页数据访问。

---

## 4. 质量标准

与既有 Phase1 CRUD 提示词在「异步、类型提示、事务、IntegrityError、日志脱敏」等方面要求一致。未列出的 CRUD 函数不得修改。
