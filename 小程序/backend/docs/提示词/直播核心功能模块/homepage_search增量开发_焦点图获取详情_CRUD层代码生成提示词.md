# homepage_search 增量开发 - CRUD 层代码生成提示词（焦点图获取详情）

**版本**: 增量版  
**模块名称**: 首页与搜索模块 (homepage_search)  
**增量主题**: 焦点图获取详情接口（GET /api/v1/featured-content/admin/{content_id}）  
**对应设计文档**:
- 主设计文档：`docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`
- 增量设计文档：`docs/03_系统设计/首页与搜索模块增量开发设计文档-焦点图获取详情接口.md`

---

## 1. 角色定义

在既有 homepage_search CRUD 提示词基础上，按本增量提示词**仅确认以下约定**；本次增量**不修改、不新增**任何 CRUD 函数。

---

## 2. Model 字段变更摘要

无。本次增量不涉及 Model 变更。

---

## 3. 需要约定的 CRUD 函数（无代码变更）

| 函数名 | 约定说明 |
|--------|----------|
| `get_featured_content_by_id(db, content_id)` | **复用**。获取焦点图详情接口由 Service 层调用此函数；不施加 is_active/start_at/end_at 过滤；不存在时返回 `None`。 |

---

## 4. 需要修改的 CRUD 函数清单

无。CRUD 层无新增、无修改。

---

## 5. 质量标准

与既有 CRUD 提示词在「异步、类型提示、事务与 IntegrityError、日志脱敏、安全异步异常处理」等方面要求一致。本增量不改变任何 CRUD 函数的签名与行为。
