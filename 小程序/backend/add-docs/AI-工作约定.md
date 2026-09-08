# AI 工作约定（工具无关 · 全项目）

**版本**: V1.0（自 Live-Saas-Wechat 迁入并按本仓裁剪）  
**日期**: 2026-09-01  
**定位**: 任意 AI（Cursor / 粘贴提示词）的**唯一习惯真源**；不替代业务设计文档  
**Cursor 适配**: [`.cursor/rules/`](.cursor/rules/)、[`.cursor/skills/`](.cursor/skills/)、[`.cursor/agents/`](.cursor/agents/) 为指针与角色；细则以本文 + `add-docs` 为准  
**上游**: 结构与习惯对齐 `D:\Programming\Live-Saas-Wechat\docs\AI-工作约定.md`；本文件为本仓真源

---

## 1. 项目是什么

| 项 | 说明 |
|----|------|
| 本仓 | 直播 SaaS **后端**（FastAPI 多服务；主开发面 `live_core_service`） |
| 代码主目录 | [`backend/live_core_service/`](backend/live_core_service/)、[`backend/users/`](backend/users/)、[`backend/media_download_service/`](backend/media_download_service/) |
| 设计文档 | [`add-docs/`](add-docs/)（编号模块设计 / 增量 / 模板） |
| 前端边界 | 微信小程序在 **`D:\Programming\Live-Saas-Wechat`**；本仓不改其 `src/**`，契约以本仓 `add-docs` 为准 |
| 规范与模板 | [`add-docs/后端设计文档模板.md`](add-docs/后端设计文档模板.md)；[`add-docs/增量设计文档模板.md`](add-docs/增量设计文档模板.md) |
| 运行 | Docker Compose；改 `live_core` 代码后用 [`rebuild-live-core-only.bat`](rebuild-live-core-only.bat) / `.sh`；**禁止**日常 `down -v` |

---

## 2. 文档分层（禁止混写）

| 层 | 管什么 | 禁止 |
|----|--------|------|
| 模块后端设计（如《02》《12》） | Endpoint / Schema / DDL / 错误码 | 把前端交互细节写满替代契约 |
| 增量设计（V2/V3…） | 相对基线的【新增/修改/废弃】 | 整篇重写基线当增量 |
| 跨模块决策 / 全景 | 清/留/占位/过滤等跨服务规则 | 在单模块文里改写已拍板决策 |
| 本文 | AI 习惯与分流 | 写进业务决策文档 |

---

## 3. 接到任务怎么分流

按**用户本轮说了什么**选行；未命中的行不要预读、不要开工。

| 任务类型 | 先读（仅该类需要时） | 可改范围 | 默认角色 |
|----------|----------------------|----------|----------|
| 只问「在哪 / 谁调用」 | 相关 `backend/**`；必要时 `add-docs` | 只读 | [`explorer`](.cursor/agents/explorer.md) |
| 改 API / Service / CRUD / Model / 迁移 | 命中的 [`add-docs`](add-docs/) 设计/增量 + 现网代码 | `backend/**`（按用户范围） | [`backend`](.cursor/agents/backend.md) |
| 新建/重命名/改设计文档 | 模板 + 基线文档 | `add-docs/**` 等用户指定 | [`docs`](.cursor/agents/docs.md) |
| 只要建议 | 按需只读 | 不改仓库 | 只读 |
| 前端实现（他仓） | 本仓契约文档 + 他仓规范 | **默认不改本仓**；用户点名他仓路径时再改 | 说明边界；需要时打开他仓 |

未明确要求时：**只分析建议，不改代码、不改决策结论、不 git commit。**

---

## 4. 执行方式：行动清单 + 自测收尾

非单句问答的任务一律：

1. **先分流并打开对应 Agent 文件**（§3 + [`.cursor/agents/`](.cursor/agents/)；只「心里归类」不算）  
2. **先选最小化、最友好修改方案**  
3. **先把行动清单写进对用户可见的回复**；默念清单 / 只建内部 Todo = **未执行**  
4. **按清单逐步做**  
5. **自测收尾**（覆盖请求 / 越界 / 最小友好 / 是否 Read Agent / 任务相关项）

**可不启用清单的唯一例外**：纯单点事实问答且一眼能答。报 bug、多文件排查 → **必须**清单。

细节见 Skill [`action-checklist`](.cursor/skills/action-checklist/SKILL.md)。

---

## 4.1 改代码须有文档依据（契约对齐 · 强制）

改 `backend/**`（尤其 endpoint / schema / service / crud）时：**禁止凭感觉发明字段或接口形状**。须先有可指认的文档依据，并**严格对齐**。

### 依据优先级（高 → 低）

1. 本模块 **后端设计 / 增量设计**（[`add-docs/`](add-docs/)）中的 Endpoint、Query/Body、Schema、错误码、DDL  
2. 跨模块决策文档（仅当任务命中）  
3. 现网代码（与文档冲突时标明偏差，不得 silently 改契约含义）

### 必须对齐

字段名、字段集合（不多不少）、必填/可选、类型与枚举、数量与长度、格式、method/path/权限、响应 `data` 形状。

### 执行要求

- 行动清单写出依据：文档链接 + 章节/Endpoint；**摘录必要字段**  
- 文档缺失 / 实现差集 / 行业常见未定义 → 「缺口/建议」，**未确认不进代码**  
- Docker：改 `live_core_service` 后提醒用 `rebuild-live-core-only`；不碰库 volume  

---

## 5. 文档命名、模板与规范

1. **能匹配到模板的用模板**：完整设计 → [`后端设计文档模板`](add-docs/后端设计文档模板.md)；增量 → [`增量设计文档模板`](add-docs/增量设计文档模板.md)；已有编号系列 → 沿用该系列体例（如 `02-…-V2-…增量`）  
2. 业务设计进 [`add-docs/`](add-docs/)；不随意新增顶层目录  
3. **补丁 vs 重写**：意思没变 → 局部补丁；意思变了 → 重写该节  

---

## 6. 改文档与短配置：补丁还是重写

| 情况 | 做法 |
|------|------|
| 错别字、版本号、日期、修订历史一行、表内改一两格 | 局部补丁 |
| 叠否定句纠正旧表述 | 重写该段/该节 |
| 章节职责或定位变化 | 重写该节；短文件优先整份重写 |

先改本文（若习惯有变），再对齐 Cursor 短文件。

---

## 7. 输出与协作习惯

- 简体中文；先结论，少铺垫  
- 改动最小化；不顺手重构、不扩写未点名文件  
- 密钥与 `.env*` 不进提交；用户未要求不 commit / 不 push  
- 禁止破坏性 Docker 操作清库，除非用户明确要求  

---

## 8. Skill 与 Agent

| 层级 | 路径 | 职责 |
|------|------|------|
| 真源 | [`add-docs/AI-工作约定.md`](add-docs/AI-工作约定.md) | 习惯与分流 |
| Rule | [`.cursor/rules/project-ai.mdc`](.cursor/rules/project-ai.mdc) | 提醒遵守本文 |
| Skill | [`live-saas-workflow`](.cursor/skills/live-saas-workflow/SKILL.md) | 分流、模板、补丁/重写；**须打开匹配 Agent** |
| Skill | [`action-checklist`](.cursor/skills/action-checklist/SKILL.md) | 可见行动清单 + 自测 |
| Agent | [`explorer`](.cursor/agents/explorer.md) / [`backend`](.cursor/agents/backend.md) / [`docs`](.cursor/agents/docs.md) | 只读 / 改后端 / 改文档 |

**Agent 用法**：§3 定角色后 **Read** 对应文件；禁止只写角色名。

**链接**：Skill/Agent 点名仓库内文件须用可跳转 Markdown 链接（相对仓库根 `live-streaming-saas-v2-main/`）。

---

## 9. 使用方式

- 直接说需求 → §3 分流 + §4 行动清单与自测  
- 「用 explorer / backend / docs：…」→ 固定角色  

---

## 📝 修订历史

| 版本 | 日期 | 内容 |
|------|------|------|
| V1.0 | 2026-09-01 | 自 Live-Saas-Wechat 迁入；裁剪为后端仓；角色 `frontend`→`backend`；文档根 `docs`→`add-docs` |

---

**文档结束**
