# 直播间与公众号关联 --- CRUD 层代码生成提示词

**版本**: V1.0  
**基于**: 直播间与公众号关联---crud_service_endpoint代码生成提示词母版.md、设计文档 §2/§4/§6  
**目标文件**: `backend/live_core_service/app/crud/liveroom_official_accounts.py`

---

## 1. 角色与任务

你是精通 SQLAlchemy 2.0 与学院派分层的后端工程师。请根据设计文档与已有模型/Schema，生成**直播间与公众号关联**模块的 CRUD 层代码，且**仅**负责数据访问与事务，不包含权限判断（权限在 Service 层）。

**必须**先使用 `read_file()` 读取以下文件并提取摘要后再写代码：
- `backend/live_core_service/app/models/liveroom_official_accounts.py`（OfficialAccount, LiveRoomOfficialAccount 字段与关系）
- 设计文档 DDL §2.1、§2.2（表名、列、约束、索引一致）

---

## 2. 异常处理与事务规范（强制）

- 所有写操作（create/update/delete、批量设置关联）必须在 **try/except/finally** 中执行：try 内执行 SQL 与 `db.commit()`；捕获 `IntegrityError` 时 `db.rollback()`、`logger.error(..., exc_info=True)`、raise `DatabaseIntegrityException`（对应 2002 名称重复等）；其他异常 rollback 后 raise；finally 中不关闭 session（由调用方管理）。
- **禁止**在 CRUD 层做权限判断或业务状态码决策；仅做 DB 操作与基于 DB 的异常转换。

---

## 3. N+1 与分页规范

- 列表查询若需关联加载（如公众号列表当前为单表，无需 join 则不必 selectinload）；**按房间查公众号**、**按公众号查房间** 为联表查询，在 CRUD 内用 JOIN 一次查出，禁止在循环中再查。
- **分页**：分页接口必须**两次查询**：第一次 `count(*)` 得 total；第二次 `offset/limit` 得 items；WHERE 条件一致；禁止先查全表再内存分页。

---

## 4. SQL 级过滤与事务

- 公众号列表的 `include_inactive`、`q`、`search_type` 必须在 **SQL WHERE** 中完成（如 is_active、name ILIKE 或 id=），禁止查出后在内存中过滤。
- 单表/多表写操作均在 CRUD 的同一事务内完成（同一 `db` session）；replace 模式：先 DELETE 该 room_id 的 live_room_official_accounts，再批量 INSERT。

---

## 5. 需要实现的 CRUD 函数清单

| 函数名 | 说明 | 返回/异常 |
|--------|------|-----------|
| get_paginated_official_accounts(db, page, size, q, search_type, include_inactive) | 分页列表；WHERE 含 is_active、q/search_type（设计文档 §4.1.1 本列表字符串搜索字段为 name） | (total: int, items: List[OfficialAccount]) |
| get_official_account_by_id(db, account_id) | 按 id 查单条 | Optional[OfficialAccount] |
| create_official_account(db, obj_in: OfficialAccountCreate) | 创建；id 应用层 uuid.uuid4() | OfficialAccount；IntegrityError → DatabaseIntegrityException |
| update_official_account(db, account_id, obj_in: OfficialAccountUpdate) | 部分更新 | OfficialAccount；不存在可返回 None 由 Service 抛 2001 |
| soft_delete_official_account(db, account_id) | update is_active=false | 影响行数；不存在可返回 0 |
| get_official_accounts_by_room_id(db, room_id) | 联表 live_room_official_accounts + official_accounts，room_id 且 official_accounts.is_active=true，排序 | List[OfficialAccount] |
| set_room_official_accounts(db, room_id, account_ids: List[UUID], mode: Literal["replace","append"]) | replace：删该 room 后批量插入；append：仅插入（冲突忽略或跳过） | 无；IntegrityError 等 → rollback + raise |
| delete_room_official_account(db, room_id, account_id) | 删除 (room_id, account_id) | 影响行数；0 表示不存在 |
| get_rooms_by_account_id_paginated(db, account_id, page, size) | 联表 live_room_official_accounts + live_rooms，WHERE account_id=，分页 | (total: int, items: List[LiveRoom])，items 用于序列化为 RoomBriefItem |

---

## 6. 数据库初始化脚本

- 表由 `app/init_db.py` 通过 `import app.models` 自动识别，无需修改 init 脚本；若使用 Alembic，需在迁移中创建 official_accounts、live_room_official_accounts 及索引、外键、触发器。

---

## 7. 最终交付

- 生成完整可运行的 `app/crud/liveroom_official_accounts.py`。
- 在 `app/crud/__init__.py` 末尾追加本模块 CRUD 函数的导入（若项目约定导出）。
- 确保所有函数签名与上表一致，且异常与事务行为符合 §2。
