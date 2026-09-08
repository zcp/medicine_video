# Categories 科室图片能力 - 修改文件清单与验证清单

**增量文档**: 《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories科室图片能力.md》  
**执行完成**: Step 1～6（Step 4 CRUD 无变更，已跳过）

---

## 一、修改的文件路径列表

| 序号 | 文件路径 | 变更类型 |
|------|----------|----------|
| 1 | `backend/live_core_service/app/core/file_handler.py` | 新增 3 个方法 |
| 2 | `backend/live_core_service/app/services/content_management_service.py` | 新增 2 个方法 + 导入 |
| 3 | `backend/live_core_service/app/api/v1/endpoints/content_management.py` | 新增 2 个端点 + 导入 |

**新增文档（未改代码）**：
- `docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories科室图片能力.md`
- `docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块增量开发设计文档-Categories科室图片能力-一致性检查报告.md`
- `docs/提示词/直播核心功能模块/内容管理模块增量开发-Categories科室图片能力-CRUD层代码生成提示词.md`
- `docs/提示词/直播核心功能模块/内容管理模块增量开发-Categories科室图片能力-Service层和API层代码生成提示词.md`

---

## 二、修改的函数/类/接口列表

| 位置 | 名称 | 说明 |
|------|------|------|
| file_handler.py | `generate_category_icon_path(category_id, extension)` | 新增，返回 (fs_path, url_path) |
| file_handler.py | `save_category_icon(file, category_id)` | 新增，校验+保存，返回 URL |
| file_handler.py | `delete_old_category_icon(icon_url)` | 新增，删除本地旧文件 |
| content_management_service.py | `upload_category_icon(db, category_id, file, current_user_id, role)` | 新增，返回 CategoryItem |
| content_management_service.py | `delete_category_icon(db, category_id, current_user_id, role)` | 新增，返回 {"message": "删除成功"} |
| content_management API | POST `/categories/{category_id}/icon` | 新增端点 |
| content_management API | DELETE `/categories/{category_id}/icon` | 新增端点 |

**CRUD**：无修改；上传/删除通过既有 `update_category` 更新 `icon`。

---

## 三、curl 示例

**上传科室图片**（需替换 `BASE_URL`、`CATEGORY_ID`、`JWT_TOKEN`、图片路径）：

```bash
curl -X POST "%BASE_URL%/api/v1/content/categories/%CATEGORY_ID%/icon" \
  -H "Authorization: Bearer %JWT_TOKEN%" \
  -F "file=@/path/to/icon.jpg"
```

**删除科室图片**：

```bash
curl -X DELETE "%BASE_URL%/api/v1/content/categories/%CATEGORY_ID%/icon" \
  -H "Authorization: Bearer %JWT_TOKEN%"
```

---

## 四、最小回归测试清单

| 用例 | 预期 |
|------|------|
| 上传成功 | 200，data 为 CategoryItem，icon 为以 `/media/` 开头的 URL |
| 上传非法类型（如 .txt） | 400，错误信息为不支持的文件类型 |
| 上传超大小（> UPLOAD_MAX_SIZE） | 400，错误信息为文件大小超出限制 |
| 覆盖更新 | 先上传 A，再上传 B；最终 icon 为 B 的 URL，旧文件已删除 |
| 删除成功 | 200，该 category 的 icon 为 null；物理文件已删除 |
| 删除无图片场景 | 200（幂等） |
| 分类不存在（上传/删除） | 404，code 2001 |
| 非 Admin 用户 | 403，code 3003 |

---

## 五、强制自检勾选

- [x] 已逐段通读母版
- [x] 已逐段通读主设计文档
- [x] 复用了 categories.icon 字段
- [x] 未新增数据库字段
- [x] 未猜测字段名或路径（从 file_handler/主文档/现有 API 推导）
- [x] 复用了 file_handler.py 风格（ROOM_MEDIA_ROOT_PATH、/media/、validate_image_file、delete 旧文件逻辑）
- [x] 未改变现有响应结构（CategoryItem 不变）
- [x] 所有修改为最小 diff
- [x] 已写入实际代码文件
