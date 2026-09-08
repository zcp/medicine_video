# 标签管理 V2 dev 词表清理与重建——SQL 方案

> **创建日期**: 2026-09-06（V1.1 代码事实复核修订）
> **版本修订（V1.1，依据后端代码逐条核验）**: ① admin 建词通道**无内容安全校验**（仅用户 resolve 通道有，services/content_management_service.py:359 vs :320）；② 重名返回 **500/1002 而非 4001**（crud 抛 DatabaseIntegrityException → endpoint 未捕获，endpoints/content_management.py:219）；③ 补环境核对、FK 级联预检、resolve 回归与 seed_tags 防复活项
> **执行环境**: dev（live_core dev 库）；**执行人**: 用户/后端侧（本仓前端只读后端，不代执行写操作）
> **适用范围（重要）**: 本方案**仅限 dev（live_core_test）**；**严禁在生产复刻清理 SQL**（生产若存在真实运营词/用户词/真实场次关联，全量删除不可逆）。生产启用词表只走《正式医学标签词表建议清单》增量导入 + 运营治理，流程详见《标签管理V2-生产启用-增量导入与治理预案》
> **决策依据**: 用户判定 dev 现有 tags 全量为测试数据，可全部删除后重建正式医学词表
> **代码事实（后端只读核验）**: `tags` 表（models/content_management.py:21）；`session_tags`（:132）`session_id → live_sessions.id ON DELETE CASCADE`（:137）、`tag_id → tags.id ON DELETE CASCADE`（:143）→ 删 tags 自动级联清关联行，无需也无法产生孤儿行

## 一、边界声明（最高优先，违规即停）

| 允许 DML | 说明 |
|---|---|
| `tags` | 本次清理目标表 |
| `session_tags` | 仅"被删 tags 的关联行"（推荐显式两步删除便于审计；即使跳过，FK CASCADE 也会自动清理） |
| **禁止触碰** | `live_sessions`、`live_rooms`、各类 tabs、`categories`/`experts`/`brands` 及其关联表、`content_safety_rules` 等规则表、用户/房间/场次任何业务行 |
| **禁止操作** | DROP / TRUNCATE / ALTER / 按前缀模糊 DELETE；不删 tags 之外的任何行 |

> 影响说明：若某测试词曾绑定到演示场次，删词后该场次只是"不再展示该标签"（session_tags 关联行被级联删除），场次行本身及其它字段零影响——符合"测试词不应展示"预期。

## 二、执行前置（目标核对 → FK 预检 → 备份，务必可回滚）

0. **目标环境核对（最高优先）**：本机存在多套项目副本目录（`live-streaming-saas-v2-main` / `(wechat)` / `-1` 等），清错库不可逆。执行前 `docker ps` 确认目标 postgres 容器与库名（compose-db.yml 项目，库 `live_core_test`，容器名通常形如 `live-streaming-saas-v2-main-postgres-1`）；连接串/容器与预期不符即停。可先执行步骤 1a，用现有词表特征（来源分布、词名）人工复核是否确为要清理的库——与预期不符即停。
1. **FK 级联预检**（只读）：确认 `session_tags.tag_id` 外键为 ON DELETE CASCADE；若实际非级联/无约束，步骤 2b 将因外键冲突被拒并整体回滚（安全失败方向），但需提前知道以决定是否调整两步删除顺序。
   ```sql
   SELECT conname, confdeltype FROM pg_constraint
   WHERE conrelid = 'session_tags'::regclass AND contype = 'f';
   -- confdeltype = 'c' 表示 CASCADE；出现非 'c' 即停止并排查
   ```
2. **备份（容器内执行，任选其一，务必可回滚）**：
   - `docker compose -f compose-db.yml exec postgres pg_dump -U postgres -d live_core_test -t tags -t session_tags --data-only -f /tmp/tags_bak_20260906.dump`，随后 `docker cp` 取出到本机留档；或
   - 只读导出：`\copy (SELECT * FROM tags) TO '.../tags_bak_20260906.csv' CSV HEADER`（session_tags 同）
3. 记录执行时间与执行人；低峰执行（避免与直播创建/标签绑定写入并发）。

## 三、清理步骤（全部在 dev，事务内）

### 步骤 1：只读盘点（人工留档）

```sql
-- 1a. 全量 tags 清单（判定依据，确认无保留项后进入删除）
SELECT id, name, source, is_active, created_at
FROM tags
ORDER BY created_at;

-- 1b. 将受影响的 session_tags 关联行数（预期 = 绑定过测试词的场次关联数）
SELECT count(*) AS st_rows
FROM session_tags
WHERE tag_id IN (SELECT id FROM tags);

-- 1c. 受影响场次分布（只读展示，确认均属测试/可弃；不修改）
-- 注：live_sessions 无 title 字段，房间标题在 live_rooms，须 JOIN live_rooms 取标题
SELECT s.id AS session_id, r.title, s.status
FROM session_tags st
JOIN live_sessions s ON s.id = st.session_id
JOIN live_rooms r ON r.id = s.room_id
WHERE st.tag_id IN (SELECT id FROM tags)
ORDER BY s.created_at DESC;

-- 1d. 守护基线（记录删除前后对比，证明边界未越）
SELECT (SELECT count(*) FROM live_sessions) AS sessions_before,
       (SELECT count(*) FROM tags)         AS tags_before,
       (SELECT count(*) FROM session_tags) AS session_tags_before;
```

人工核对 1a/1c 输出：确认全部为测试词且关联场次无真实留存诉求 → 留档记录。

### 步骤 2：清理（显式两步，事务 + 计数审计）

```sql
BEGIN;

-- 2a. 先清被删 tags 的 session_tags 关联（显式，便于计数审计；FK CASCADE 兜底）
DELETE FROM session_tags
WHERE tag_id IN (SELECT id FROM tags);

-- 2b. 删除全部 tags（用户已判定全量测试数据）
DELETE FROM tags;

COMMIT;
```

### 步骤 3：残留核验（=0 才算通过）

```sql
SELECT count(*) AS tags_remaining        FROM tags;          -- 期望 0
SELECT count(*) AS orphan_st_remaining   FROM session_tags;  -- 期望 0（级联已清）
SELECT count(*) AS sessions_after        FROM live_sessions; -- 期望 = 1d 的 sessions_before（未触碰）
SELECT count(*) AS rules_after           FROM content_safety_rules; -- 期望不变（规则表零触碰）
```

核验输出回填本文档尾表；任一不满足即回滚事务并复盘（备份恢复路径见前置）。

## 四、重建（正式医学词表，source=admin）

**推荐 A：Admin API 逐条导入**（自动落 `source=admin` + `created_by=<当前管理员>`，溯源完整、经后端校验）
```http
POST /api/v1/admin/tags        # admin_yu 登录态
{ "name": "高血压管理", "description": "<可选>" }
```
> 词表内容按《正式医学标签词表建议清单》执行。**通道事实（代码核对后修正，务必遵守）**：
> - **本通道无内容安全校验**：`check_scene_fields` 仅挂在用户 resolve 通道（services/content_management_service.py:359），`POST /api/v1/admin/tags` 不经过（:320）——合规防线=词表清单 §一 人工自检；
> - **重名返回 500/1002 而非 4001**（crud/content_management.py:319 抛 DatabaseIntegrityException → endpoint 未捕获落入 generic 500，endpoints/content_management.py:219）。**导入前先 `GET /api/v1/admin/tags` 分页拉全量，按 name 去重比对**；导入中遇 500 一律人工复核是否已存在，不得自动忽略；
> - **导入后 resolve 回归（关键）**：以 an_test 登录态对每条词 `POST /api/v1/content/tags/resolve {name}`：200 且 `created=false` = 通过（词已 active 可直接复用）；422 = 该词在用户绑定侧会被拦截，**必须换词**。**顺序严禁颠倒：先 admin 导入、后 resolve 自检**——空表上先 resolve 会把每条词建成 source=user（= 清理白做）。

**备选 B：SQL 直插**（仅当 API 通道不可用时；需手工取 admin 用户 id；不推荐——无校验无溯源语义）
```sql
INSERT INTO tags (id, name, source, is_active, created_at, updated_at, created_by)
SELECT gen_random_uuid(), '高血压管理', 'admin', true, now(), now(), '<admin_yu 的 user_id>'
WHERE NOT EXISTS (SELECT 1 FROM tags WHERE name = '高血压管理');
```

## 五、清理/重建后前端验证（配合项）

- [x] an_test 创建直播 → 添加标签 → 联想为 72 条新词（用户手机端实测通过 2026-09-06）。注：DB 复核未见对应绑定/自建词痕迹（tags=72 admin/0 user、session_tags=0），疑前端联调指向其它环境；如需完全闭环可复测核对
- [x] 旧测试词验证：**按方案建议不执行**（避免在干净词表上重建 source=user 旧词）
- [x] 新词可点选/绑定/回显（手机端实测通过）；管理端「运营」徽章：接口层 source=admin 已全量核验（72/72），管理端 UI 徽章展示待管理端人工查看确认
- [x] 违禁样例「根治」在 resolve 通道仍 422 不落库（规则表未动，回归确认）——2026-09-06 复检 2 次均 422；首次探测(12:45)曾瞬时放行并落 1 条 user 词，已删除并记录（见 §六）
- [x] 72 条新词 resolve 回归全部 200 / created=false（无 422）——终检 OK=72/0，日志 backups\20260906\phase4_resolve_log.csv
- [x] 确认清理后**未重跑 `app/seed_tags.py`**（重跑会幂等复活 20 条测试词并重建 8 条场次关联；该脚本仅限历史用途，勿再执行）

## 六、执行结果回填

| 项 | 值 | 执行人/时间 |
|---|---|---|
| 盘点确认（1a/1c 无保留项） | ✅ 用户确认（731 条全部测试数据；含 user 测试词 医疗直播/孙悟空） | 2026-09-06 |
| 清理前 tags / session_tags / live_sessions 数 | 731 / 29 / 20 | 2026-09-06 |
| 删除 tags 数 | 731（session_tags 关联 29 同步清除，先干跑验证后事务提交） | 2026-09-06 |
| 清理后残留核验（tags=0、session_tags=0、sessions 不变、rules 不变） | 0 / 0 / 20(=20) / 260(=260)，rooms 61 不变 ✅ | 2026-09-06 |
| 备份位置 | `D:\live-streaming-saas-v2-main\backups\20260906\`（pg_dump SQL + 2 CSV，行数核验一致） | 2026-09-06 |
| 导入新词条数（source=admin） | 72/72（详见《正式医学标签词表建议清单》导入列全勾选） | 2026-09-06 |
| 执行过程记录 | ① 首轮导入因 PS5.1 默认非 UTF-8 编码产生 9 条乱码词（'?'），已 SQL 物理删除并修正脚本（HttpClient+UTF8）重导 72/72；② resolve 回归首测「根治」瞬时未拦截（12:45:25 落 1 条 source=user 词，已物理删除）；12:46 起复检 2 次均 422 拦截，logs 确认 block。疑与 12:23 规则管理端访问/进程内 60s 规则缓存窗口相关，已登记待观察（后续内容安全回归需含该样例）；③ 导入日志与回归日志见 backups\20260906\ | 2026-09-06 |
| resolve 回归结果 | 72 词全部 200/created=false；根治、阿莫西林 均 422（content_safety_logs 有 block 记录）；72 条均 source=admin、user 词 0 | 2026-09-06 |
| 前端验证（§五 勾选） | ✅ 手机端实测通过（2026-09-06）；DB 终态 tags=72/admin、user=0、session_tags=0；管理端徽章 UI 展示待管理端人工确认 | 2026-09-06 |
