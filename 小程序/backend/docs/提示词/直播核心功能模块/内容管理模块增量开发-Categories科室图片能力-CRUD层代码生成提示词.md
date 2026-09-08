# 内容管理模块增量开发 - CRUD 层代码生成提示词（Categories 科室图片能力）

**基于**：已通过一致性检查的《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories科室图片能力.md》  
**定位**：本增量**不新增、不修改**任何 CRUD 函数。上传/删除科室图片时，由 Service 层调用既有 `update_category(db, category_id, category_data: CategoryUpdate)` 更新 `icon` 字段；上传后传入 `CategoryUpdate(icon=new_url)`，删除图片后传入 `CategoryUpdate(icon=None)`（将 icon 置为 NULL）。

**使用前**：须先使用《增量开发设计文档与主设计文档一致性检查提示词母版》对上述增量设计文档与主设计文档（合并版）通过一致性检查后，再使用本提示词生成或修改代码。

---

## 角色定义

在既有内容管理 CRUD（app/crud/content_management.py）基础上，本增量**无需修改 CRUD 层**；仅约定 Service 层通过既有 `update_category` 更新 `categories.icon`。

---

## Model 字段变更摘要

无。继续使用 Category 既有字段 `icon`（String(255), nullable=True）。

---

## 需要修改的 CRUD 函数清单

无。无需修改任何 CRUD 函数。

---

## 需要约定的 CRUD（无代码变更）

- 上传科室图片后：Service 调用 `update_category(db, category_id, CategoryUpdate(icon=url))`，仅更新 icon，其他字段由 `exclude_unset=True` 保持不变。
- 删除科室图片后：Service 调用 `update_category(db, category_id, CategoryUpdate(icon=None))`，将 icon 置为 NULL；CRUD 层 `update_category` 已支持部分更新，传入 `icon=None` 即可清空该字段。
- 不得改变 `update_category` 的签名或行为；不得新增专门“只更新 icon”的 CRUD 函数（保持最小 diff）。

---

## 质量标准

与既有 content_management CRUD 一致。本增量不触及 CRUD 代码文件。

**文档结束**
