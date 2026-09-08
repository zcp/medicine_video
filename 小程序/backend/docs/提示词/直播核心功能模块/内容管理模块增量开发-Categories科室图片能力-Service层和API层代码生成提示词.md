# 内容管理模块增量开发 - Service 层和 API 层代码生成提示词（Categories 科室图片能力）

**基于**：已通过一致性检查的《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories科室图片能力.md》  
**定位**：在既有内容管理 Service（app/services/content_management_service.py）与 API（app/api/v1/endpoints/content_management.py）及 FileHandler（app/core/file_handler.py）基础上，按本增量提示词**新增**科室图片上传、删除能力；不修改未列出的方法或端点。

**使用前**：须先使用《增量开发设计文档与主设计文档一致性检查提示词母版》对上述增量设计文档与主设计文档（合并版）通过一致性检查后，再使用本提示词生成或修改代码。

---

## 角色定义

在既有内容管理 Service/API 及 file_handler 基础上，按本增量提示词**新增**：FileHandler 三个方法、Service 两个方法、API 两个端点（上传/删除科室图片）；权限与现有 categories 管理接口一致（Admin）。

---

## Schema 变更摘要

无。上传接口请求为 multipart（UploadFile），响应为既有 CategoryItem；删除接口无 body，响应为统一成功结构（如 `{"message": "删除成功"}` 或 success_response）。

---

## FileHandler 增量（app/core/file_handler.py）

须新增以下三个方法（命名与现有 generate_*_path、save_*、delete_old_* 一致）：

1. **generate_category_icon_path(category_id: uuid.UUID, extension: str) -> Tuple[str, str]**  
   生成存储路径与 URL。相对目录 `categories/{category_id}`，文件名 `icon_{timestamp}.{extension}`；文件系统路径使用 `ROOM_MEDIA_ROOT_PATH`，URL 为 `/media/categories/{category_id}/icon_{timestamp}.{ext}`。确保目录存在（os.makedirs(exist_ok=True)）。

2. **save_category_icon(file: UploadFile, category_id: uuid.UUID) -> str**  
   校验：`FileHandler.validate_image_file(file)`；取扩展名；调用 `generate_category_icon_path`；读取内容并校验大小 ≤ UPLOAD_MAX_SIZE，超则 HTTPException 400；写入文件；返回 URL。异常与现有 save_cover_file/save_banner_file 一致（HTTPException 重新抛出，其余 500）。

3. **delete_old_category_icon(icon_url: str) -> None**  
   若 icon_url 为空或非 `/media/` 开头则 return。否则：`relative_path = icon_url.replace("/media/", "")`，`fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)`；若 os.path.exists(fs_path) 则 os.remove(fs_path)；删除失败仅 logger.warning，不抛异常。

---

## 需要新增的 Service 方法清单

1. **upload_category_icon(self, db, category_id, file, current_user_id, role) -> CategoryItem**  
   - 权限：`_check_admin_permission(role)`。  
   - 校验分类存在：`get_category_by_id(db, category_id)`，不存在则 `raise NotFoundException("分类不存在")`。  
   - 若 category.icon 非空且以 `/media/` 开头：`FileHandler.delete_old_category_icon(category.icon)`。  
   - `url = await FileHandler.save_category_icon(file, category_id)`。  
   - `update_category(db, category_id, CategoryUpdate(icon=url))`，commit，refresh，返回 `CategoryItem.model_validate(category)`。  
   - 注意：需在 Service 内获取 category 对象（get_category_by_id），再根据 icon 决定是否删旧文件；save 后再次获取或使用 update 返回的 category 均可。

2. **delete_category_icon(self, db, category_id, current_user_id, role) -> dict**  
   - 权限：`_check_admin_permission(role)`。  
   - 校验分类存在：同上，不存在则 NotFoundException。  
   - 若 category.icon 非空且以 `/media/` 开头：`FileHandler.delete_old_category_icon(category.icon)`。  
   - `update_category(db, category_id, CategoryUpdate(icon=None))`，commit。  
   - 返回 `{"message": "删除成功"}`（与既有 delete_category 等一致）。

---

## 需要新增的 API 端点

1. **POST /categories/{category_id}/icon**  
   - 路由：挂载于 prefix=/content，完整路径 POST /api/v1/content/categories/{category_id}/icon。  
   - 参数：category_id: Path；file: UploadFile = File(...)。  
   - 依赖：get_db，get_current_user。  
   - 执行：提取 user_id、role（try 块前）；调用 `service.upload_category_icon(db, category_id, file, current_user_id, role)`；成功返回 200、data 为 CategoryItem（统一响应结构）。  
   - 异常：NotFoundException -> 404 code 2001；PermissionDeniedException -> 403 code 3003；HTTPException（file_handler 抛出）-> 按 status_code 与 detail 返回；其余 -> 500 code 1002。

2. **DELETE /categories/{category_id}/icon**  
   - 路由：DELETE /api/v1/content/categories/{category_id}/icon。  
   - 参数：category_id: Path。  
   - 依赖：get_db，get_current_user。  
   - 执行：提取 user_id、role；调用 `service.delete_category_icon(db, category_id, current_user_id, role)`；成功返回 200、统一成功结构。  
   - 异常：同上传；无图片时也返回 200（幂等）。

---

## 权限与异常

- 权限在 Service 层：两个新方法内均先调用 `_check_admin_permission(role)`。  
- API 层 try 块前提取 user_id、role；双轨鉴权、error_response/success_response 与既有 content_management 一致。  
- 不改变既有响应结构；上传返回的 data 为完整 CategoryItem（含 icon 等）。

---

## 质量标准

与既有 content_management Service/API 一致：权限在 Service 层、日志脱敏、try 块前提取 user_id/role、异常转换为 JSONResponse。不改变未列出的方法或端点。

**文档结束**
