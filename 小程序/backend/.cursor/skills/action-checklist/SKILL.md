---
name: action-checklist
description: >-
  Step-by-step action checklist with self-test for live-streaming-saas backend
  tasks (code, docs, analysis, debugging). MUST: user-visible checklist before
  edits, follow in order, finish with self-test. Prefer 最小化最友好; 防填洞.
---

# 行动清单 + 自测收尾

## 本 Skill 做什么

做**任何**非单句问答的任务时：先分流并读匹配 Agent → 选最小化最友好方案 → **把行动清单写进对用户可见的回复** → 按步执行 → 自测收尾。  
不替代 [live-saas-workflow](.cursor/skills/live-saas-workflow/SKILL.md) 的分流；分流之后用本 Skill 管执行节奏。  
相关文档跳转见 [AI-工作约定 §8](add-docs/AI-工作约定.md)。

> 源自 Live-Saas-Wechat 同名 Skill；角色名改为 `backend`。

## 为何必须「写出来再做」

| 错误做法 | 为何不算执行 |
|----------|----------------|
| 只 Read 了本文件，心里默念就改代码 | 用户看不见清单 |
| 只建内部 Todo | 对用户不可见 = 未列清单 |
| §3 写了 `backend` 却不 Read [backend Agent](.cursor/agents/backend.md) | 只贴了角色名 |
| 报 bug 按「单句问答」跳过清单 | 例外被滥用 |

**口令**：没写进回复的清单 = 没做；没 Read 的 Agent = 没分流到位。

## 何时启用

| 启用（必须） | 可不启用（唯一例外） |
|--------------|----------------------|
| 改代码、改文档、排查/修 bug、设计梳理、多步分析 | 纯单点事实问答且一眼能答 |

**默认从宽启用**：拿不准时，**启用**。

## 方案原则

**最小化、最友好** —— 动手前先选方案再写清单。

| 原则 | 做法 |
|------|------|
| 最小化 | 只改达成请求所需最少文件/行；能补丁不重写 |
| 最友好 | 优先可感知、风险低、可回退；复用已有口径 |
| 先选方案 | 清单里写清「采用的最小友好方案」一句话 |

### 防「永远填不完的洞」

| 项 | 要求 |
|----|------|
| 一句话定位 | 本变更只服务一条闭环 |
| 完成定义 | 几步内能验证主路径即算完成 |
| 非目标封印 | 明确「本次永不做」；另开任务再做 |

### 后端增量额外检查

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 文档依据 | `add-docs` 链接 + Endpoint/章节已摘录 |
| 2 | 权限 | 与文档 Auth（Public/JWT/Admin/房主）一致 |
| 3 | Schema | 长度/枚举/`tag_ids` 上下限等与文档一致 |
| 4 | Docker | 需重建时用 `rebuild-live-core-only`；不碰 volume |
| 5 | 非目标 | 未扩到用户未点名的服务/表 |

## 流程（必须按序）

### 0. 分流 + 读 Agent

1. 按 [AI-工作约定](add-docs/AI-工作约定.md) §3 / [live-saas-workflow](.cursor/skills/live-saas-workflow/SKILL.md) 定角色：`explorer` | `backend` | `docs`  
2. **Read** [`.cursor/agents/<角色>.md`](.cursor/agents/)  
3. 回复里点明本轮角色

### 1. 写行动清单（先写进回复）

```text
行动清单
- [ ] S1 …（目标一句话；含采用的最小友好方案）
- [ ] S2 …
- [ ] S3 …
- [ ] S4 自测收尾
```

改 `backend/**` 时：清单须含**文档依据**（可跳转链接 + 章节/Endpoint）并**摘录必要字段**。

### 2. 按步执行

严格按序；清单不对先改清单；冒出「顺便重构」→ 停住。

### 3. 自测收尾

```text
自测
| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 是否覆盖用户请求 | ✅/❌ | … |
| 2 | 是否超出范围 | ✅/❌ | … |
| 3 | 是否最小化、最友好 | ✅/❌ | … |
| 4 | 是否 Read 了匹配 Agent | ✅/❌ | explorer/backend/docs |
| 5 | 清单是否对用户可见且按步执行 | ✅/❌ | … |
| 6 | （任务相关检查） | ✅/❌ | … |
```

## 禁止

- 无**可见**清单直接大改  
- 默念清单 / 仅内部 Todo 当作已列清单  
- 定了角色却不 Read 对应 Agent  
- 做完不自测就报完成  
- 无文档依据发明字段或偏离契约  
- 日常清库式 Docker 操作  

