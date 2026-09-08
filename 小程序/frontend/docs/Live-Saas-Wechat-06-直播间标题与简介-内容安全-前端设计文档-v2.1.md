# 直播间标题与简介/Tab — 内容安全增量前端设计文档（V2）

**版本**: V2.1  
**日期**: 2026-07-04  
**状态**: 📋 设计定稿，待开发  
**基于**: 《Live-Saas-Wechat-06-直播间Tab管理-前端设计文档-v1.0.md》V1.1 + `CreateLive.vue`  
**后端对齐**: 《06-直播间标题与简介-V2-内容安全增量设计文档》V2.1  
**共享能力**: 《Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0》§3（**含 §3.0 全员人话原则**）

---

## ⚠️ 重要声明

- 公告（room_notice）**不在范围**
- 房间/Tab 查询展示逻辑 **不变**
- 三个 scene **相互独立**（与后端一致）：`room_title` / `room_description` / `room_tab`
- warn（2006）允许写入，HTTP 200，用户无感知

---

## 📌 变更范围

| scene | 目标字段 | 前端表单绑定 | 提交 API |
|-------|----------|--------------|----------|
| `room_title` | `title` | `CreateLive.vue` → `form.title` | 房间 POST/PATCH body `title` |
| `room_description` | `description` | `CreateLive.vue` → `form.summary` → `buildRoomDescription()` | 房间 POST/PATCH body `description` |
| `room_tab` | `tab_key`, `title`, `text_content` | `TabEditDialog.vue` 各字段；CreateLive 简介 Tab 的 `text_content` | Tab CRUD |

### 字段映射说明（避免测错 scene）

| 用户可见 | 代码字段 | 后端 scene | 说明 |
|----------|----------|------------|------|
| 直播标题 | `form.title` | `room_title` | 基础信息区 |
| 直播间简介（textarea） | `form.summary` → API `description` | `room_description` | **不是** room_tab |
| 简介 Tab 正文 | Tab `text_content`（CreateLive 提交简介 Tab 时） | `room_tab` | 与 `description` 不同 scene |
| Tab 管理弹窗 | `tab_key` / `title` / `text_content` | `room_tab` | 三字段同等校验 |

---

## 一、涉及文件

```
src/pages/live/CreateLive.vue              # handleSubmit — title + description + 简介 Tab
src/pages/admin/roomTab/TabEditDialog.vue  # Tab 保存
src/api/room.ts                            # 房间 CRUD（路径不变）
src/api/tabs.ts                            # Tab CRUD（路径不变）
```

---

## 二、交互设计

### 2.1 创建/编辑直播（CreateLive）

**触发**：用户点击「创建直播」/「保存修改」→ 房间 POST/PATCH（含 `title`、`description`）及 Tab 写入。

| 结果 | UI |
|------|-----|
| 200 | 原有成功流程（跳转/Toast） |
| 2005 | Toast「暂无法发布，请修改内容后再试」；**停留当前页**，`form.title` / `form.summary` 等保留 |
| 2004 | 「暂时无法提交，请稍后再试」（或限流等人话 message）；停留当前页 |

```typescript
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'

async function handleSubmit() {
  try {
    await createOrUpdateRoom(payload)  // showError: false；payload 含 title、description
    // 原有成功逻辑
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败，请稍后再试'), icon: 'none' })
  }
}
```

**无需**前端预校验 URL/手机号——后端统一拦截。

**联调提示**：
- 测 `room_description` → 在 **简介 textarea**（`form.summary`）输入违禁词
- 测 `room_title` → 在 **标题**（`form.title`）输入
- 测 `room_tab` → 在 Tab 弹窗或简介 Tab 的 `text_content` 输入

### 2.2 Tab 编辑（TabEditDialog）

三个文本字段任一被拦截均可能返回 2005；**C 端 Toast 不展示**后端规则名/拦截原因。

- 弹窗 **不关闭**
- 用户修改后重试

---

## 三、行动清单

| # | 任务 | 验收 |
|---|------|------|
| 1 | CreateLive `handleSubmit` 接入 `handleContentSafetyError` | 标题/简介违规可测 |
| 2 | TabEditDialog 保存接入同上 | Tab 三字段违规可测 |
| 3 | 提交 API 设 `showError: false` | 2005 Toast 为固定人话文案 |
| 4 | 文档/注释标明 `form.summary` → `room_description` | 联调不测错字段 |
| 5 | 区分简介 Tab `text_content`（room_tab）与 `description` | §四 #3/#5 可区分 |

---

## 四、自测清单

| # | 测试项 | 预期 | 验证 |
|---|--------|------|------|
| 1 | 标题正常文案 | 保存成功 | [ ] |
| 2 | `form.title` 含 `http://a.com` | 2005（room_title），表单保留 | [ ] |
| 3 | `form.summary` 含手机号 | 2005（room_description），表单保留 | [ ] |
| 4 | `form.summary` 含外链 | 2005（room_description） | [ ] |
| 5 | Tab `title` 含「加V」 | 2005（room_tab） | [ ] |
| 6 | Tab `text_content` 含敏感词 | 2005（room_tab） | [ ] |
| 7 | Tab `tab_key` 含违规内容 | 2005（room_tab） | [ ] |
| 8 | 简介命中 warn 规则 | HTTP 200，保存成功，用户无感知 | [ ] |
| 9 | 安全服务故障 | 2004 | [ ] |
| 10 | 直播间详情 Tab 展示 | 与改前一致 | [ ] |
| 11 | 公告相关 | 无变更 | [ ] |

---

## 五、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.0 | 2026-07-04 | 初版 |
| V2.3 | 2026-07-09 | 对齐《12》V1.2 全员人话原则 |
| V2.2 | 2026-07-09 | C 端 Toast 固定人话文案，禁止透传后端审计 message |
| V2.1 | 2026-07-04 | 审计修订：form.summary→description 映射、room_tab 区分、warn 自测 |

---

**文档结束** ✅
