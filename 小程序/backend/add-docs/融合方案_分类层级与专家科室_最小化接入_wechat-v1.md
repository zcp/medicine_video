# 融合方案：分类层级 + 专家科室受控词表（A2+C 零偏差接入 · wechat-v1）

> **版本**: V1.1（对齐 A2+C 定稿 + 工作区落地核对）  
> **日期**: 2026-08-12  
> **基线分支**: 本地 `wechat-v1`（`721e1ad`）  
> **功能真源**: `app修改记录` 中 A2+C 定稿（**零偏差**：不新增、不减少）  
> **代码参考**: `huang-backend/main`（文件级移植）→ **工作区已落地**（相对 HEAD 多为未提交增量）  
> **范围**: A2+C 全量能力（受控词表自适应补全 + 分类层级 / `is_primary` / 发现层多对多）  
> **合并方式**: **最小化、最友好**——文件级加法移植 + 过渡期双轨；**禁止**用「裁剪」代替友好合并  
> **状态**: 🟢 后端工作区已落地；口径归集见 `add-docs/20-分类层级与专家科室受控词表-后端设计文档.md`  
> **实现修正**: Admin 科室面以代码为准为 **9** 端点（非实施清单旧写「5」）；`categories.is_public` **未加**（非本轮缺口）

---

## 〇、真源与写作约束

### 0.1 真源优先级（冲突时以上为准）

| 优先级 | 文档 | 用途 |
|:------:|:-----|:-----|
| 1 | `app修改记录/融合方案最终设计_A2+C.md` | 架构定稿 |
| 2 | `app修改记录/融合方案_最终评估_无触发器版.md` | 同步机制：应用层，无触发器 |
| 3 | `app修改记录/融合方案最终评估报告.md` | **10 业务场景 = 验收真源** |
| 4 | `app修改记录/融合方案_实施清单.md` | P0–P5 实施面与改动清单 |
| 5 | `app修改记录/融合方案P1~P4_*_代码生成提示词.md` | 实施细节（Model/CRUD/Service/API/迁移） |
| 6 | `app修改记录/专家与直播间分类规则冻结方案.md` | 直播间以 `live_room_categories` 为权威 |

本文件只描述：**如何把上述真源接到 wechat-v1**（友好合并战术），**不重新定义功能集合**。

### 0.2 零偏差纪律

| 允许 | 禁止 |
|:-----|:-----|
| 与 A2+C **同构的行为与 API 面** | 把自适应建词 / merge / unmapped / P2 匹配标成「可选/后置」 |
| wechat 已有能力 **复用、不重做** | 相对 A2+C **少做**任何能力点 |
| 过渡期双轨（旧列暂留 + 新权威） | 相对 A2+C **多做**本真源未定义的增强 |
| 文件级摘模块 / 摘函数 | `git merge` 整树、整文件覆盖 wechat 私有逻辑 |

### 0.3 写作模版维度（跨分支融合可复用）

| # | 维度 | 目的 |
|:--|:-----|:-----|
| 1 | 元信息 | 可追溯 |
| 2 | 一句话目标 | 对齐预期 |
| 3 | 非目标 | 只列真非目标（非裁剪清单） |
| 4 | 现状矩阵 | wechat 已有 vs A2+C 缺口 |
| 5 | 决策原则 | 友好合并裁决 |
| 6 | 分项决策 | 一比一对齐 A2+C |
| 7 | 阶段路线 | 对齐实施清单 P0–P5 |
| 8 | 改动清单 | 防漏改 |
| 9 | 契约 | 过渡期兼容 |
| 10 | 验收 | 对齐 10 场景 |
| 11 | 回滚与终态 | 过渡 vs 破坏性收紧分离 |

---

## 一、一句话目标

在 **不破坏 wechat-v1 登录 / 内容安全 / 私密试播** 的前提下，把 A2+C **完整能力**接到本地：

1. **科室**：`expert_departments` 受控词表 + `is_verified` + 同义词自学习 + 自适应创建 + Admin 全套（含 unmapped / merge）+ 应用层同步 `experts.category_id`。  
2. **分类**：`parent_id` 层级（已有则复用）+ `is_primary` 写入 + 发现层读 `live_room_categories`（含子孙展开）+ 房间 `primary_category_name`。  
3. **合并手段**：加法移植 + 过渡双轨；**功能不裁剪**。

---

## 二、非目标（仅这些）

| 不做项 | 原因 |
|:-------|:-----|
| `git merge huang-backend/main` | 无共同祖先；用文件级移植 |
| 引入 DB 触发器 | A2+C 无触发器定稿；应用层显式同步 |
| 整文件覆盖 `experts.py` / `homepage_search.py` / `content_management.py` 等 | 保护 wechat 私有改动；只摘函数/补模块 |
| 国家医学标准整树重构（V10 等） | **不在 A2+C 范围** |
| 改 wechat 登录 / 内容安全 / 私密试播 | 正交，本轮不碰 |

> **注意**：以下 **不是**非目标（旧 V0.1 误标为不做/后置，现已撤销）：  
> 自适应 `is_verified=false`、merge/同义词、P2 医学词匹配、unmapped API、发现层多对多、`primary_category_name`、数据迁移、前端 P4、终态删旧列。

---

## 三、双方现状矩阵（wechat 已有 → 只补缺口）

### 3.1 分类层级

| 能力点（A2+C） | wechat-v1 | 本轮动作 |
|:---------------|:---------:|:---------|
| `categories.parent_id` / tree API | ✅ | **复用本地** |
| `live_room_categories` + `is_primary` 列 | ✅ 列在未用 | **补写入逻辑（必做）** |
| 设分类 `primary_category_id` | ❌ | **按 A2+C/main 接入** |
| 发现层 EXISTS + 子孙展开 | ❌（等值） | **必做**（对齐冻结方案权威源） |
| 房间响应 `primary_category_name` | ❌ | **必做**（评估报告场景 7） |
| `categories` 运行时录入不写 | 需核对 | **对齐 A2+C：运行时只读** |
| 「其他」兜底分类 | 需核对 | **P0 必做** |
| `is_public` / 部分唯一索引 | ❌ 无 is_public | **本轮不加** `is_public`（代码未落地；非 wechat 阻塞项） |
| `live_rooms.category_id` | ✅ 仍用 | **过渡双写**；筛选/展示权威转多对多；删列进终态 Phase |

### 3.2 专家科室（A2+C 核心）

| 能力点（A2+C） | wechat-v1 | 本轮动作 |
|:---------------|:---------:|:---------|
| `expert_departments`（synonyms / is_verified / is_active） | ❌ | **整模块移植** |
| seed 已审核词表 + 别名 | ❌ | **必做** |
| `experts.department_id` FK | ❌ | **必做** |
| `experts.category_id` 缓存列 | ❌ | **必做** |
| 解析：P1 精确 → P1b 同义词 → P2 医学词 → UPSERT `is_verified=false` | ❌ | **必做（不可关）** |
| `update_department_category` 应用层同步专家 | ❌ | **必做** |
| `merge_departments`（同义词上限 20） | ❌ | **必做** |
| Admin：列表/CUD/`unmapped`/`merge`/改分类/`batch-verify`/详情 | ❌→工作区✅ | **9 端点全做**（以代码为准） |
| 搜索 JOIN `expert_departments.name` | ❌ | **必做**（场景 5） |
| 响应 `department_name` / `department_id` / `category_name` | ❌ | **必做** |
| 存量 `department` → 词表迁移 | ❌ | **P3 必做** |
| `experts.department` 文本列 | ✅ | **过渡期保留并回填**；删列 = 终态（覆盖达标后） |
| `category_id` NOT NULL | — | **有「其他」+ 迁移覆盖后再收紧**（终态） |

---

## 四、决策原则

1. **功能真源 = A2+C**：行为与 API 面一比一；本文件只规定接入手法。  
2. **基底 = wechat-v1**：只摘文件/函数，不覆盖登录/内容安全/私密试播。  
3. **友好合并 = 双轨过渡，不是减配**：  
   - 权威读写跟 A2+C；旧列可暂留并双写/回填。  
   - 禁止把「双轨」理解成「不做自适应 / 不做 merge」。  
4. **应用层同步**：改 `expert_departments.category_id` 时，同事务 `UPDATE experts.category_id`（无触发器）。  
5. **categories 纯净**：运行时录入路径不写 `categories`；新科室只进 `expert_departments`。  
6. **破坏性收紧后置执行、不后置目标**：删 `department`、删 `live_rooms.category_id`、`category_id` NOT NULL 仍是 A2+C 终态，进 **Phase T（收紧）**，验收覆盖率后再跑。

---

## 五、分项决策表（与 A2+C 对齐）

### 5.1 科室

| ID | 决策点 | 结论（对齐 A2+C） | 友好合并 |
|:---|:-------|:------------------|:---------|
| D1 | 建表 + seed | 移植 A2+C / main DDL（含 synonyms、is_verified） | 迁移幂等；缺分类名 seed 跳过并打日志 |
| D2 | `department_id` | FK → expert_departments | 过渡期可空；迁移后尽量填满 |
| D3 | `category_id` | 反范式缓存列；由词表推导 | 过渡可空；终态 NOT NULL +「其他」兜底 |
| D4 | 文本 `department` | **逻辑上不再作权威** | 物理列过渡保留；响应可回填文本兼容旧客户端 |
| D5 | 创建/更新解析 | P1→P1b→P2→UPSERT `is_verified=false` | **不可配置关闭**；对齐场景 1–3 |
| D6 | 改词表分类 | `update_department_category` 显式同步专家 | 同事务 commit |
| D7 | 合并 | `merge_departments` + 同义词上限 20 + verified 升级 | 对齐场景 8/10 |
| D8 | Admin API | **9 端点**（代码）：列表/创建/更新/软删/`unmapped`/`merge`/改 category/`batch-verify`/详情 | 权限：ADMIN\|SUPERADMIN；拒绝码 `3003` |
| D9 | 搜索 | 科室名走 `expert_departments` ILIKE | 对齐场景 5 |
| D10 | 删文本列 | A2+C 终态必达 | **Phase T** 执行，本轮不提前 DROP |

### 5.2 分类 / 直播间

| ID | 决策点 | 结论（对齐 A2+C / 冻结方案） | 友好合并 |
|:---|:-------|:-----------------------------|:---------|
| C1 | parent_id / tree | 复用 wechat 已有 | 不重写 |
| C2 | `is_primary` 写入 | 接入 `set_live_room_categories`；可传 `primary_category_id`，默认列表首个 | — |
| C3 | 发现层筛选 | 读 `live_room_categories` + 子孙展开 | 过渡期可双写单列，**筛选不以单列为权威** |
| C4 | `primary_category_name` | 房间列表/详情返回 | 对齐场景 7 |
| C5 | categories 只读 | 录入路径不自动写 categories | Admin 手动增删改仍可 |
| C6 | 「其他」 | P0 兜底分类 | 启发式失败归「其他」 |
| C7 | 删 `live_rooms.category_id` | A2+C/冻结终态 | **Phase T**；此前主分类双写保旧 SQL |

---

## 六、阶段路线（对齐实施清单；工时以清单为参考）

```text
P0  前置：「其他」兜底 + 已知 Bug 修复
P1  DB：expert_departments + experts FK/缓存列 + categories 缺口补齐
P2  后端：解析/自适应/merge/同步 + Admin 5 端点 + is_primary + 搜索/房间字段 + 发现层
P3  数据：department→词表映射 + 房间分类补齐（需业务确认部分单标）
P4  前端：分类 Tab / 科室选择 / Admin 审核·Merge·unmapped（可与后端并行，但不删除范围）
P5  观察期：监控 is_verified=false /「其他」增长 + 别名优化
T   终态收紧（覆盖达标后）：删 department 文本列、删 live_rooms.category_id、category_id NOT NULL
```

| Phase | 内容 | 依赖 | 建议工时（清单） | 阻塞 |
|:------|:-----|:-----|:-----------------|:-----|
| P0 | 「其他」+ 前置修复 | — | 0.5 人天 | 是 |
| P1 | DB 结构 | categories 存在 | 1 人天 | 是 |
| P2 | 后端全量行为 | P1 | 3 人天 | 是 |
| P3 | 数据迁移 | P2 | 1.5 人天 | 是（上线前） |
| P4 | 前端接入 | P2 契约 | 3 人天 | 可并行；API 可先撑运营 |
| P5 | 观察期 | 上线后 | 2–4 周 | 否 |
| T | 破坏性收紧 | P3/P5 覆盖率 | 另估 | 否（达标后） |

**开工顺序：P0 → P1 → P2 → P3 →（P4 并行）→ 冒烟（含 wechat 私有）→ P5 →（达标）T。**

---

## 七、改动清单（相对 wechat：新增 / 修改）

### 7.1 数据库

| 变更 | 说明 |
|:-----|:-----|
| 「其他」分类 upsert | P0，幂等 |
| `YYYYMMDD_create_expert_departments.sql` | 表 + 索引 + seed（对齐 A2+C / main V4） |
| `experts.department_id` UUID + FK | ON DELETE SET NULL |
| `experts.category_id` UUID + FK | 缓存列；过渡可空 |
| categories 缺口 | **不加** `is_public`（代码未落地）；`parent_id` 已有则复用 |
| **本阶段不执行** DROP `department` / DROP `live_rooms.category_id` | 进 Phase T |

### 7.2 后端（对齐实施清单 + P1–P3 提示词）

**新增：**

- `models/expert_departments.py`
- `schemas/expert_departments.py`
- `crud/expert_departments.py`
- `api/v1/endpoints/expert_departments.py`（Admin **9** 端点）
- `core/category_constants.py`（wechat 分类名对齐的匹配常量）
- `migrations/20260812_create_expert_departments.sql`
- `scripts/seed_expert_departments.py` / `scripts/migrate_expert_departments.py`

**修改（摘函数，禁止整文件覆盖）：**

- `models/__init__.py` — 注册 `ExpertDepartment`（`schemas/__init__.py` / `crud/__init__.py` 可不导出，端点直引模块）  
- `models/experts.py` — FK + relationship；**过渡保留** `department` Column  
- `schemas/experts.py` — `department_name` / `department_id` / `category_name` 等（对齐 A2+C）  
- `services/expert_service.py` — `_resolve_department_and_category`、`_match_broad_category`、`merge_departments`、`update_department_category`、`_to_expert_item`  
- `crud/experts.py` / `endpoints/experts.py` — 读写与 format  
- `api/v1/api.py` — 注册 `expert_dept_admin_router`  
- `crud/content_management.py` + schemas — `is_primary` / `primary_category_id` + 双写单列；`get_category_descendant_ids`  
- `endpoints/room.py`（或等价）— `primary_category_name`  
- `crud/homepage_search.py` — 多对多 + 子孙；专家搜索 JOIN 词表  
- `app/seed.py` — 「其他」+ 二级 `parent_id`（维持）  

### 7.3 前端（实施清单 P4，范围不删）

- 分类 Tab / 专家列表筛选  
- 科室选择器  
- Admin：科室列表、待审核、unmapped、Merge  
- 房间卡片展示真实 `primary_category_name`  
- 相关 `api/*.ts`

> 后端可先于 UI 上线；**不得**因此从方案中删除 P4。

---

## 八、契约与兼容（过渡期）

### 8.1 专家

| 字段 | A2+C 权威 | 过渡期 wechat |
|:-----|:----------|:--------------|
| `department_id` / `department_name` | ✅ | ✅ 必返 |
| `category_id` / `category_name` | ✅ | ✅ 必返 |
| `department` 文本 | A2+C 终态删除 | **过渡继续返回**（从词表名回填优先） |

解析入参：支持 `department_id` 或科室名文本；文本走 P1→P1b→P2→自适应创建。

### 8.2 直播间设分类

| 字段 | 行为 |
|:-----|:-----|
| `category_ids` + `mode` | 同现网 |
| `primary_category_id` | 可选；默认列表首个 → 写 `is_primary` 并双写 `live_rooms.category_id` |

### 8.3 Admin（A2+C 全量，不可裁；**以代码 9 端点为准**）

- `GET/POST /api/v1/admin/expert-departments`
- `PATCH/DELETE /api/v1/admin/expert-departments/{department_id}`
- `GET /api/v1/admin/expert-departments/unmapped`
- `POST /api/v1/admin/expert-departments/merge`
- `PATCH /api/v1/admin/expert-departments/{department_id}/category`
- `POST /api/v1/admin/expert-departments/batch-verify`
- `GET /api/v1/admin/expert-departments/{department_id}`

Merge / 改分类走 `ExpertService`（同义词自学习 + 应用层同步）；Approve 走 `batch-verify` 或 PATCH `is_verified`。  
完整字段与错误码见 `add-docs/20-分类层级与专家科室受控词表-后端设计文档.md`。

---

## 九、验收标准（= 评估报告 10 场景 + wechat 冒烟）

### 9.1 A2+C 业务场景（必须全部通过）

- [ ] **场景 1**：已知科室名创建专家 → 命中词表，Tab 立即可见  
- [ ] **场景 2**：新科室名 → 自动 `is_verified=false` + 启发式归大类，待审核可见  
- [ ] **场景 3**：批量导入不因单行匹配失败中断  
- [ ] **场景 4**：按根分类 Tab 筛选不遗漏（含未审核词表下专家）  
- [ ] **场景 5**：搜索命中 `expert_departments.name`  
- [ ] **场景 6**：详情返回 `department_name` / `department_id` / `category_*`  
- [ ] **场景 7**：房间卡片 `primary_category_name` 非硬编码  
- [ ] **场景 8**：`is_verified=false` 列表 + Approve / Merge / Edit  
- [ ] **场景 9**：改词表 `category_id` → 关联专家应用层同步  
- [ ] **场景 10**：Merge 后同义词再导入命中，不重复建词  

### 9.2 分类 / 发现层

- [ ] 多分类设置后恰有一条 `is_primary=true`  
- [ ] 发现层按多对多 + 父分类子孙展开  
- [ ] 私密房间不出现在公开列表  

### 9.3 wechat 私有冒烟（友好合并底线）

- [ ] 登录 / 内容安全 / 私密试播无回归  
- [ ] 未误执行终态 DROP（除非已进入 Phase T 且获批）  

### 9.4 工程

- [ ] 迁移幂等可重复执行  
- [ ] 无 DB 触发器  
- [ ] 无整文件覆盖导致的 wechat 私有逻辑丢失  

---

## 十、回滚与终态

### 回滚

- **代码**：revert 对应 commit / PR。  
- **DB**：新表与可空列可保留；停用 Admin 路由即可降级；过渡期未删旧列，回滚简单。  
- **禁止**在未进 Phase T 前依赖「已删旧列」的回滚路径。

### Phase T（终态收紧，覆盖达标后）

| 项 | 条件 |
|:---|:-----|
| 删除 `experts.department` | 读写已全走词表；旧客户端已切 `department_name` |
| `experts.category_id` NOT NULL | 「其他」兜底 + 存量 0 NULL |
| 删除 `live_rooms.category_id` | 发现层/写入已只认多对多，双写可关 |

### 观察期（P5，非减配）

- 监控 `is_verified=false` 与「其他」增长  
- 别名 / 同义词优化  
- 与 A2+C 实施清单一致  

---

## 十一、关联文档（阅读顺序）

1. `app修改记录/融合方案最终设计_A2+C.md`  
2. `app修改记录/融合方案_最终评估_无触发器版.md`  
3. `app修改记录/融合方案最终评估报告.md`（10 场景）  
4. `app修改记录/融合方案_实施清单.md`  
5. `app修改记录/融合方案P1~P4_*_代码生成提示词.md`  
6. `app修改记录/专家与直播间分类规则冻结方案.md`  
7. `add-docs/01-科室分类管理-V2-增量设计文档.md`（本地 parent_id 背景）  
8. `add-docs/20-分类层级与专家科室受控词表-后端设计文档.md`（**代码零偏差归集**）  

---

## 十二、已确认开关（锁定）

| # | 问题 | 锁定结论 |
|:--|:-----|:---------|
| 1 | 未知科室文本是否自适应创建 `is_verified=false`？ | **是**（A2+C 核心，不可关） |
| 2 | 是否加 `experts.category_id`？ | **是** |
| 3 | 发现层多对多 + 子孙 / `primary_category_name` / merge / unmapped / P2？ | **是**（全做） |
| 4 | 过渡期是否暂留旧列并双写？ | **是**（友好合并；删列进 Phase T） |
| 5 | 功能真源？ | **`app修改记录` A2+C，零偏差** |

**实施顺序固定：P0 → P1 → P2 → P3 →（P4 并行）→ wechat 冒烟 → P5 →（达标）Phase T。**

---

## 十三、完整度核对纪要（V1.1）

| 项 | 融合方案 V1.0 | 工作区代码 | 处理 |
|----|---------------|------------|------|
| Admin 端点数 | 写「5」 | **9**（+merge/category/batch-verify/详情） | 已改为以代码为准 |
| `is_public` | 「缺啥补啥」 | **未实现** | 改为本轮不加 |
| `_build_expert_item` | 改动清单写法 | 实为 `_to_expert_item` | 已改名 |
| `category_constants.py` | 未列 | **有** | 已补进改动清单 |
| 迁移文件名 | `YYYYMMDD_…` 示意 | `20260812_create_expert_departments.sql` | 已点名 |
| 后端落地状态 | 「可实施」 | P0–P2 核心**已写在工作区**（相对 HEAD 未 commit） | 状态栏已更新 |
| 功能面 vs A2+C 10 场景 | 全覆盖要求 | 能力面对齐；验收勾选仍待冒烟 | 保持验收清单 |
