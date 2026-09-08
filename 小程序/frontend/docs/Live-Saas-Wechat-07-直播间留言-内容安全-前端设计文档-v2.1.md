# 直播间留言 — 内容安全增量前端设计文档（V2）

**版本**: V2.1  
**日期**: 2026-07-04  
**状态**: 📋 设计定稿，待开发  
**基于**: 《Live-Saas-Wechat-07-直播间留言-前端设计文档-v1.3.md》V1.0  
**后端对齐**: 《07-直播间留言-V2-内容安全增量设计文档》V2.1  
**共享能力**: 《Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0》§3（**含 §3.0 全员人话原则**）

---

## ⚠️ 重要声明

- 留言表结构、列表分页、删除逻辑 **不变**
- 仅 **发送留言** 失败路径增加 2004/2005 处理
- warn（2006）：HTTP 200，留言发布成功，**用户无感知**（与 allow 相同 UI）

---

## 📌 变更范围

| 变更类型 | 说明 |
|----------|------|
| 【修改】 | `LiveView.vue` → `handleSendMessage` 错误处理 |
| 【修改】 | `roomMessage.ts` 调用处设 `showError: false`（API 签名不变） |
| 【无改】 | 留言 API 路径、请求体、类型定义 |

---

## 一、涉及文件

```
src/pages/live/LiveView.vue     # handleSendMessage（约 L1188）
src/api/roomMessage.ts          # createRoomMessage — 路径不变
```

**API**：`POST /api/core/rooms/{roomId}/messages`，body `{ content }`（1–500 字符）

---

## 二、交互设计

### 2.1 发送成功（200，含 allow 与 warn）

- 留言插入列表顶部
- 清空输入框
- Toast「留言成功」
- warn 时不额外提示（后端 `reason_code=2006` 仅写审计日志）

### 2.2 内容被拦截（422 / code=2005）

- Toast：**「暂无法发布，请修改内容后再试」**（固定文案，**不展示**后端 message）
- **保留** `messageInputContent` 输入内容
- 不插入列表

### 2.3 暂时无法提交（422 / code=2004）

- 默认 Toast：**「暂时无法提交，请稍后再试」**
- 限流等人话 message（如「发送过于频繁，请 5 秒后再试」）可透传
- 保留输入内容

### 2.4 实现示例

```typescript
import { handleContentSafetyError } from '@/utils/contentSafety'
import { createRoomMessage } from '@/api/roomMessage'

async function handleSendMessage() {
  const content = messageInputContent.value.trim()
  if (!content || messageSending.value || !roomId.value) return
  messageSending.value = true
  try {
    const resp = await createRoomMessage(roomId.value, { content })
    // 若 createRoomMessage 不支持第三参，在 api 层或 request 调用处设 showError: false
    const newMsg = resp.data
    messages.value.unshift(newMsg)
    messageInputContent.value = ''
    uni.showToast({ title: '留言成功', icon: 'success' })
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getRoomMessageErrorMessage(extractBusinessCode(e) ?? undefined, extractErrorMessage(e)), icon: 'none' })
  } finally {
    messageSending.value = false
  }
}
```

> **实现说明**：在 `createRoomMessage` 内部或 `request.post` 调用处统一设 `{ showError: false }`，避免 422 时 request 层先弹默认「参数校验失败」覆盖后端 message。

---

## 三、行动清单

| # | 任务 | 验收 |
|---|------|------|
| 1 | 留言 POST 设 `showError: false` | 2005 Toast 为固定人话文案，不含规则名 |
| 2 | 接入 `handleContentSafetyError` | §四 自测通过 |
| 3 | block 时不清空输入框 | 用户体验 |
| 4 | warn 路径不增加 UI 分支 | §四 #6 |

---

## 四、自测清单

| # | 测试项 | 预期 | 验证 |
|---|--------|------|------|
| 1 | `大家好` | 发布成功，无审计日志（allow） | [ ] |
| 2 | `http://abc.com` | 2005，内容保留 | [ ] |
| 3 | `13800138000` | 2005 | [ ] |
| 4 | `加V领取资料` | 2005 | [ ] |
| 5 | 敏感词 | 2005 | [ ] |
| 6 | 命中 message warn 规则 | HTTP 200，发布成功，Toast「留言成功」 | [ ] |
| 7 | 安全服务故障 | 2004 | [ ] |
| 8 | 管理端改 message 规则 pattern | 下次留言立即生效 | [ ] |
| 9 | 删除留言 | 与 V1.0 一致 | [ ] |

---

## 五、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.0 | 2026-07-04 | 初版 |
| V2.3 | 2026-07-09 | 对齐《12》V1.2 全员人话原则 |
| V2.2 | 2026-07-09 | C 端 Toast 固定人话文案，禁止透传后端审计 message |
| V2.1 | 2026-07-04 | 审计修订：warn 自测、showError 实现说明、管理端规则生效项 |

---

**文档结束** ✅
