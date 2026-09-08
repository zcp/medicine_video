# 内容管理模块增量开发 - CRUD 层代码生成提示词

**基于**：已通过一致性检查的《直播核心功能设计文档_v6_内容管理模块增量开发设计文档-直播间与分类多对多.md》  
**定位**：在既有内容管理 CRUD（app/crud/content_management.py）基础上，按本增量提示词仅新增下列函数。

---

## 角色定义

在既有内容管理 CRUD 提示词/实现基础上，按本增量提示词**新增**与 room_categories 相关的函数，不修改既有 Tags/Categories/Session_Tags 的 CRUD 函数。

---

## Model 字段变更摘要

**新增表 room_categories 对应 ORM**（在 app/models/content_management.py 中新增 RoomCategory）：

- room_id: UUID, FK(live_rooms.id, ON DELETE CASCADE), PK 之一
- category_id: UUID, FK(categories.id, ON DELETE CASCADE), PK 之一
- is_primary: Boolean, default False
- created_at: TIMESTAMPTZ, server_default=now()

---

## 需要新增的 CRUD 函数清单

### 1. get_categories_by_room_id(db, room_id) -> List[Category]

- **功能**：根据 room_id 查询该直播间关联的已启用分类列表。
- **执行流程**：select Category join room_categories on category_id = categories.id where room_categories.room_id = :room_id and categories.is_active == True；order_by Category.sort_order, Category.name。
- **返回**：List[Category]（空列表表示无关联或均已禁用）。
- **异常**：不抛业务异常，由 Service 层校验房间是否存在。

### 2. set_room_categories(db, room_id, category_ids, mode) -> List[Category]

- **功能**：为直播间批量设置分类；mode 同 session_tags：replace 先删后插，append 仅插入（冲突忽略）。
- **参数**：db: AsyncSession, room_id: UUID, category_ids: List[UUID], mode: Literal["replace","append"]。
- **执行流程**：若 mode=="replace"：delete RoomCategory where room_id=:room_id；然后对 category_ids 逐条 insert (room_id, category_id)。若 mode=="append"：查询该 room_id 已有 category_id 集合，仅对未存在的 category_id 插入。
- **返回**：设置后的 Category 列表（通过 get_categories_by_room_id 查询返回）。
- **异常**：IntegrityError（如外键不存在）-> DatabaseIntegrityException；其他 -> DatabaseOperationException。

### 3. delete_room_category(db, room_id, category_id) -> bool

- **功能**：删除 room_categories 中 (room_id, category_id) 一条记录（硬删除）。
- **返回**：True 表示删除成功，False 表示记录不存在。
- **异常**：数据库错误 -> DatabaseOperationException。

---

## 需要约定的 CRUD（无代码变更）

- 房间存在性由 Service 层通过 live_rooms 查询校验，CRUD 层不负责校验 room 是否存在；若需“房间不存在则 2001”，在 Service 中调用 room 相关 CRUD 或查询 live_rooms。

---

## 质量标准

与既有 content_management CRUD 一致：异步 AsyncSession、类型提示、IntegrityError 转换、日志脱敏、不重写未变更函数。

**文档结束**
