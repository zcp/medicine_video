# 内容管理模块增量开发设计文档 - Categories 科室图片能力

**版本**: 增量版  
**基于**: 《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》  
**状态**: 增量设计（与主设计文档配套使用，冲突时以主文档为准，本文档仅描述增量）

---

## 1. 核心定位说明

### 1.1 范围与关系

本增量在**不新增表、不新增字段、不改变既有响应结构**的前提下，为内容管理模块的 **Categories（科室/分类）** 新增完整图片管理能力：

1. **上传科室图片**：上传图片并写入 `categories.icon`，返回更新后的分类信息。
2. **更新科室图片**：覆盖旧图（先删旧文件再存新文件，更新 `categories.icon`）。
3. **删除科室图片**：删除物理文件并将 `categories.icon` 置为 NULL。

与主设计文档关系：主文档 Section 2.2 已定义 `categories.icon VARCHAR(255)`，Section 3.x 已有 CategoryItem/CategoryUpdate 含 icon；本增量仅补充分类图片的**上传/覆盖/删除**接口与 FileHandler/CRUD/Service 行为，与现有 categories 管理接口权限一致（Admin）。

**阅读顺序**：先阅读主设计文档全文（尤其 Section 1、2、3、4 及权限/业务码规范），再阅读本文档。本文档仅描述在上述基础上的增量变更，不重复主文档已有内容。

### 1.2 增量原则

- 最小幅度修改，仅影响科室图片相关：FileHandler 新增方法、Categories 上传/删除端点及对应 Service/CRUD 调用。
- **复用** `categories.icon` 字段存储图片 URL，不新增数据库字段。
- 复用 `file_handler.py` 的 `validate_image_file`、`ROOM_MEDIA_ROOT_PATH`、`/media/` URL 风格；不新增存储系统。
- 不改变现有 categories 响应结构（如 CategoryItem、CategoryAdminListResponse 等）。
- 图片 URL 必须以 `/media/` 开头，存储路径基于 `ROOM_MEDIA_ROOT_PATH`。

---

## 2. 依赖与参考

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|----------|----------|----------|
| 1 | 《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》 | 主设计文档，本文档在其基础上补充分类图片能力 | API 4.2.x、CRUD、FileHandler |
| 2 | 现有实现 `backend/live_core_service/app/core/file_handler.py` | 复用校验、存储、URL、删除旧文件逻辑与命名风格 | FileHandler 新增方法 |

---

## 3. 修改点总览

| 序号 | 修改位置 | 变更内容 |
|------|----------|----------|
| 1 | 主设计文档 Section 4.2（Categories API） | 补漏：新增上传科室图片、删除科室图片接口说明（请求/响应/错误码）。 |
| 2 | FileHandler（app/core/file_handler.py） | 新增：`generate_category_icon_path(category_id, extension)`、`save_category_icon(file, category_id)`、`delete_old_category_icon(icon_url)`。 |
| 3 | API（app/api/v1/endpoints/content_management.py） | 新增：POST /categories/{category_id}/icon（上传/覆盖），DELETE /categories/{category_id}/icon（删除图片）。 |
| 4 | Service（app/services/content_management_service.py） | 新增：`upload_category_icon`、`delete_category_icon`；权限与现有 categories 管理一致（_check_admin_permission）。 |
| 5 | CRUD（app/crud/content_management.py） | 无新增函数；上传/删除时通过既有 `update_category` 更新 `icon` 字段（CategoryUpdate(icon=url) 或 icon=None）。 |

---

## 4. 与主文档关系及合并决策说明

| 序号 | 修改位置 | 变更类型 | 合并决策 | 简要说明 |
|------|----------|----------|----------|----------|
| 1 | 主文档 Section 4.2 Categories API | 补漏 | 并入主文档对应位置 | 主文档未约定科室图片上传/删除接口，本增量补充。 |
| 2 | FileHandler | 新增 | 以本文档为准 | 与既有 cover/banner/logo/avatar 风格一致。 |
| 3 | API / Service / CRUD | 新增行为 | 以本文档为准 | 仅新增端点与调用，不改变既有接口。 |

---

## 5. 数据库变更

无。不新增表、不新增字段。继续使用主文档 Section 2.2 的 `categories.icon VARCHAR(255)` 存储图片 URL。

---

## 6. Schema 变更

无。请求体与响应 Schema 不变；上传接口请求为 `multipart/form-data`（UploadFile），响应为既有 CategoryItem；删除接口无 body，响应为统一成功结构。

---

## 7. API 变更

### 7.1 新增端点

#### 7.1.1 POST /api/v1/content/categories/{category_id}/icon（上传/更新科室图片）

- **认证**: Strict Auth（`Depends(get_current_user)`）。
- **权限**: Admin（Service 内 `_check_admin_permission(role)`），与现有 PUT /categories/{id}、DELETE /categories/{id} 一致。
- **请求**: `multipart/form-data`，字段名 `file`（或与现有项目一致，如 room cover 使用 `file`），类型为图片文件。
- **校验**: 使用 `FileHandler.validate_image_file(file)`；文件大小不超过 `UPLOAD_MAX_SIZE`（与 file_handler 一致）。
- **执行流程**:
  1. 校验 category 存在（get_category_by_id）；不存在返回 404（2001）。
  2. 若已有 icon 且为 `/media/` 开头：调用 `FileHandler.delete_old_category_icon(category.icon)`。
  3. 调用 `FileHandler.save_category_icon(file, category_id)` 得到 URL（以 `/media/` 开头）。
  4. 调用 CRUD `update_category(db, category_id, CategoryUpdate(icon=url))`，提交事务。
  5. 返回更新后的 CategoryItem（结构不变）。
- **响应**: 200，body 为统一响应结构，data 为 CategoryItem。
- **错误码**: 400 非法类型/超大小（4001 或与 file_handler 一致）、404 分类不存在（2001）、403 权限不足（3003）、500 内部错误（1002）。

#### 7.1.2 DELETE /api/v1/content/categories/{category_id}/icon（删除科室图片）

- **认证**: Strict Auth。
- **权限**: Admin。
- **请求**: 无 body。
- **执行流程**:
  1. 校验 category 存在；不存在返回 404（2001）。
  2. 若 `category.icon` 非空且以 `/media/` 开头：调用 `FileHandler.delete_old_category_icon(category.icon)` 删除物理文件。
  3. 调用 CRUD `update_category(db, category_id, CategoryUpdate(icon=None))`，将 icon 置为 NULL，提交事务。
  4. 返回成功响应（结构可与现有 delete 端点一致，如 `{"message": "删除成功"}` 或统一 success_response）。
- **响应**: 200。
- **错误码**: 404 分类不存在（2001）、403 权限不足（3003）、500（1002）。无图片时也返回 200（幂等）。

---

## 8. FileHandler 增量方法说明

以下方法均位于 `app/core/file_handler.py`，复用 `ROOM_MEDIA_ROOT_PATH`、`/media/` URL、`validate_image_file` 及现有大小/类型校验逻辑。

| 方法名 | 签名 | 功能 |
|--------|------|------|
| `generate_category_icon_path` | `(category_id: uuid.UUID, extension: str) -> Tuple[str, str]` | 生成存储路径与 URL；相对目录 `categories/{category_id}`，文件名 `icon_{timestamp}.{extension}`；URL 为 `/media/categories/{category_id}/icon_{timestamp}.{ext}`；确保目录存在。 |
| `save_category_icon` | `(file: UploadFile, category_id: uuid.UUID) -> str` | 校验（validate_image_file）、读内容、校验大小、生成路径、写入文件，返回 URL。 |
| `delete_old_category_icon` | `(icon_url: str) -> None` | 若 icon_url 为空或非 `/media/` 开头则 return；否则将 URL 转为 ROOM_MEDIA_ROOT_PATH 下文件系统路径并删除；删除失败仅打日志不抛异常。 |

路径命名与现有实现一致：与 `generate_banner_path`、`generate_expert_avatar_path` 等保持同一风格（实体 id 子目录 + 语义化文件名 + 时间戳）。

---

## 9. CRUD 变更说明

- **无新增 CRUD 函数**。上传与删除科室图片时，均通过既有 `update_category(db, category_id, category_data: CategoryUpdate)` 更新 `icon` 字段。
- 上传后：`CategoryUpdate(icon=new_url)`，仅更新 icon。
- 删除图片后：`CategoryUpdate(icon=None)`，将 icon 置为 NULL（与 Model `nullable=True` 一致）。

---

## 10. 覆盖策略与空值表现

- **覆盖策略**：上传时若该科室已有 icon（且为本地 `/media/` 路径），先调用 `delete_old_category_icon` 删除旧文件，再保存新文件并更新 `categories.icon`。
- **删除后空值**：`categories.icon` 置为 **NULL**（与主文档 DDL 及 Model `Column(String(255), nullable=True)` 一致）；Schema CategoryUpdate 支持 `icon: Optional[str] = None`，显式传 `icon=None` 即可在部分更新中清空字段。

---

## 11. 错误处理策略

- 与现有 content_management 及 file_handler 一致：文件类型/大小非法抛出 HTTPException 400；分类不存在返回 404、code 2001；权限不足 403、code 3003；内部错误 500、code 1002。不新增业务码。

---

## 12. 权限说明

- 上传、删除科室图片均要求 **Admin**（ADMIN 或 SUPERADMIN），与现有 POST/PUT/DELETE categories 接口一致；在 Service 内调用 `_check_admin_permission(role)`，API 层使用 `Depends(get_current_user)`。

---

## 13. 测试与回归清单

- 上传成功：返回 200，data 为 CategoryItem，icon 为以 `/media/` 开头的 URL。
- 上传非法类型：返回 400。
- 上传超大小：返回 400。
- 覆盖更新：先上传 A，再上传 B，最终 icon 为 B 的 URL，旧文件已删除。
- 删除成功：返回 200，该 category 的 icon 为 null。
- 删除无图片场景：返回 200（幂等）。
- 分类不存在：上传/删除均返回 404（2001）。
- 非 Admin：返回 403（3003）。

---

## 14. 文档结束语

本文档为主设计文档的补充，须与主设计文档配套使用；冲突时以主文档为准，本文档仅描述增量。功能增强的完整设计详见主文档 Section 2.2（categories 表）、Section 3（Schemas）、Section 4（API）；本增量涉及 FileHandler、API 新增端点、Service 新增方法及 CRUD 对既有 update_category 的用法。
