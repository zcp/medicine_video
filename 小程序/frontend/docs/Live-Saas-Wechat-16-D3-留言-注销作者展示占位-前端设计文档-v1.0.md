# 留言 · 注销作者展示占位 — 前端设计文档（16-D3）

**项目**: Live-Saas-Wechat  
**模块编号**: 16-D3  
**版本**: V1.0  
**日期**: 2026-07-23  
**状态**: 📋 设计定稿，待开发  
**技术栈**: uni-app + Vue 3 + TypeScript  
**基于**: 《Live-Saas-Wechat-07-直播间留言-前端设计文档-v1.3.md》V1.5（含 V3 昵称/头像快照）  
**后端对齐**: 《16-D3-留言-注销作者展示占位-后端设计文档》V1.1（最小落地）  
**依赖**: 后端 D2 cleanup 已能写 `deactivated_users` 标记；D3 读路径覆盖展示名/头像

---

## ⚠️ 重要声明

- 本文档是对留言展示的**增量**，不替代留言 V1/V3 列表、发送、删除设计
- **正文 `content` 一律不改**；仅作者展示名/头像按后端响应消费
- 前端 **不** 自行查 users、**不** 调 batch status、**不** 回写留言
- 后端 **P0 将在** 列表/详情/Admin 组装层覆盖（现网组装待改，见后端「最终路由表」）：`nickname` / `user_display_name` = `账号已注销`，`avatar_url` = `null`
- 标记查询失败时后端**降级快照**——前端按快照正常展示即可，无特殊 UI
- 现网 `resolveMessageAvatarSrc` **已**对空头像回退默认图；真正缺口在 **auth 兜底会盖住 `avatar_url=null`**（见 §3.1）

---

## 📌 变更范围

| 变更类型 | 说明 |
|----------|------|
| 【修改·展示】 | C 端留言列表：消费后端占位昵称；`avatar_url=null` 走默认头像 |
| 【修改·展示】 | 管理端留言列表：P0 与 C 端同一套展示规则 |
| 【修改·文案】 | `resolveMessageDisplayName` 缺昵称兜底仍为「匿名用户」；**已注销**以服务端返回的「账号已注销」为准 |
| 【无改】 | 留言 API 路径、请求体、发送/删除流程、类型字段结构 |
| 【不做·P0】 | WS 历史改名广播；Admin 额外「原始快照昵称」字段（P1） |

---

## 一、涉及文件

```
src/components/MessageItem.vue              # 单条留言：昵称 + 头像
src/utils/roomMessageNormalize.ts           # 归一化 / resolveMessageAvatarSrc / resolveMessageDisplayName
src/pages/live/LiveView.vue                 # 直播间留言区（列表渲染）
src/pages/admin/roomMessage/RoomMessageList.vue  # 管理端列表展示名
src/types/roomMessage.ts                    # 类型不变（已支持 null avatar）
src/common/constants.ts                     # DEFAULT_CONFIG.DEFAULT_AVATAR（默认头像）
```

**API（路径不变，仅响应语义增量）**：

| 端点 | 网关路径（示意） | 前端封装 |
|------|------------------|----------|
| 房间留言列表 | `GET /api/core/rooms/{roomId}/messages` | `roomMessage.ts` |
| Admin 留言列表 | 现网 Admin messages | `roomMessage.ts` |

---

## 二、契约与展示规则

### 2.1 与 V3 快照的关系（前端必读）

| 场景 | 后端响应 | 前端展示 |
|------|----------|----------|
| 作者未注销 | `user.nickname` / `user_display_name` = 发送时快照；`avatar_url` = 快照 URL | 与 V1.5 / V3 一致 |
| 作者已注销 | `nickname` / `user_display_name` = **`账号已注销`**；`avatar_url` = **`null`** | 文案原样展示；头像走默认图 |
| 标记存储失败（后端降级） | 仍为快照 | 按快照展示，无额外 Toast |

> `content` 与注销前完全一致，前端 **禁止** 因注销隐藏或改写正文。

### 2.2 响应示例（已注销）

```json
{
  "id": "msg-uuid",
  "content": "这个剂量在指南里如何调整？",
  "user_id": "owner-public-id",
  "user_display_name": "账号已注销",
  "user": {
    "nickname": "账号已注销",
    "avatar_url": null
  },
  "created_at": "2026-07-01T08:00:00Z"
}
```

### 2.3 前端禁止事项

- ❌ 用本地 auth 兜底「盖掉」服务端返回的「账号已注销」（已注销作者若曾是本人，仍应显示占位，不以当前登录昵称覆盖）
- ❌ 头像为 `null` 时留白或裂图不兜底
- ❌ 因作者注销隐藏留言、灰化正文、加「已删」类标签（产品定案：正文保留 + 身份占位）
- ❌ 前端主动调 users /internal 或 batch 判断注销状态

---

## 三、交互设计

### 3.1 C 端留言列表（LiveView + MessageItem）

```
拉列表 / 刷新
  → normalizeRoomMessageItem(raw)
  → displayName = resolveMessageDisplayName(...)
       · 优先 user.nickname / user_display_name（含「账号已注销」）
       · 皆空 → 「匿名用户」（历史无快照）
  → avatarSrc = resolveMessageAvatarSrc(user.avatar_url)
       · null/空 → DEFAULT_CONFIG.DEFAULT_AVATAR
  → 正文原样渲染 content
```

**实现要点（对照现网源码）**：

1. **现有** `resolveMessageAvatarSrc` 已在空头像时回退 `DEFAULT_CONFIG.DEFAULT_AVATAR`——无需新组件
2. **必须修 auth 兜底（头像路径是实锤缺口）**：`LiveView.fetchMessages` / `handleSendMessage` 调用 `normalizeRoomMessageItem(..., messageAuthFallback())`，其中 `messageAuthFallback()` 带当前用户 `nickname` + `avatar_url`  
   - 昵称：后端若已返回非空「账号已注销」，`nestedNickname` 优先，**一般不会**被 auth 盖掉  
   - 头像：后端 `avatar_url=null` → `pickNonEmpty` 视为空 → **会**回落到本人 `authFallback.avatar_url`，已注销作者若 `user_id` 仍等于当前登录（极端/联调窗口）或误匹配时可能露真头像  
   - **拍板**：`user` 对象已存在且 `avatar_url` 为 `null`/`''`，或昵称已是「账号已注销」时，**禁止** auth 兜底
3. `MessageItem` 二次 normalize 时只传 `user_id`（不传昵称/头像），主要风险在 LiveView 首次 normalize
4. 长按删除等权限仍按 `user_id` + 登录态判断，与展示名无关

### 3.2 管理端留言列表（RoomMessageList）

- P0：展示名与 C 端同一规则（直接消费「账号已注销」+ 默认头像）
- **现网风险**：`displayNickname` / `fetchData` 优先 `item.user_nickname`  
  ```ts
  user_display_name: item.user_nickname || normalized.user_display_name
  user_nickname: item.user_nickname || normalized.user?.nickname || null
  ```  
  若 Admin 响应里 `user_nickname` 仍为旧快照、而 `user.nickname` 已是「账号已注销」，前端会**继续露真名**。P0 须改为：优先 `user.nickname` / 归一化后的占位名；仅当后端未覆盖时再回退 `user_nickname`
- P1（可选，后端另加字段后）：可增加「原始快照」列，**仅 Admin**；本包 P0 **不做**

### 3.3 WebSocket `new_message`

- 发送瞬间作者未注销 → 推送仍为快照，前端 **不改**
- 注销后历史消息：下次拉列表即可看到占位；P0 **不**做改名广播

### 3.4 代码要点（伪代码）

```typescript
import {
  normalizeRoomMessageItem,
  resolveMessageAvatarSrc,
  resolveMessageDisplayName
} from '@/utils/roomMessageNormalize'

const DEACTIVATED_DISPLAY_NAME = '账号已注销'

// normalize 内：命中占位名时禁止 auth 覆盖
function shouldSkipAuthFallback(nickname: string | null): boolean {
  return nickname === DEACTIVATED_DISPLAY_NAME
}

// MessageItem / 列表
const displayName = resolveMessageDisplayName(normalized) // → 「账号已注销」或快照或「匿名用户」
const avatarSrc = resolveMessageAvatarSrc(normalized.user?.avatar_url) // null → 默认图
```

---

## 四、行动清单

| # | 任务 | 验收 |
|---|------|------|
| 1 | 确认 `MessageItem` / `resolveMessageAvatarSrc` 对 `avatar_url=null` 使用默认头像 | 无裂图、无空白头像（现网已具备，回归即可） |
| 2 | 修正 `normalizeRoomMessageItem`：占位名 / 显式空头像时跳过 auth 兜底 | 自测 #1、#2 |
| 3 | Admin `RoomMessageList`：去掉对旧 `user_nickname` 的优先覆盖，与 C 端一致 | 自测 #3 |
| 4 | 正文展示路径不加注销相关改写 | 自测 #1 content 不变 |
| 5 | 与后端 D2+D3 联调：注销后刷新列表见占位 | 自测 #4 |

---

## 五、自测清单

| # | 测试项 | 预期 | 验证 |
|---|--------|------|------|
| 1 | 作者已打注销标记的留言 | 正文不变；昵称=`账号已注销`；头像=默认图 | [ ] |
| 2 | 已注销作者曾是当前登录用户 | 仍显示「账号已注销」，不以当前昵称覆盖 | [ ] |
| 3 | Admin 列表同作者留言 | 与 C 端同一占位规则 | [ ] |
| 4 | 注销后重新拉列表（非依赖 WS） | 历史留言更新为占位 | [ ] |
| 5 | 作者未注销、仅改过昵称 | 仍显示发送时快照（V3 回归） | [ ] |
| 6 | 后端标记失败降级快照 | 显示快照昵称/头像，页面不挂、无错误 Toast | [ ] |
| 7 | 发送/删除留言 | 与留言 V1.5 一致 | [ ] |

---

## 六、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-23 | 初版：对齐后端 16-D3 V1.1 最小落地；默认头像 + 禁止 auth 覆盖占位名 |
| V1.0.1 | 2026-07-23 | 自测修订：澄清后端组装为 P0 待改；补 LiveView auth 头像兜底实锤缺口；补 Admin `user_nickname` 优先覆盖风险 |

---

**文档结束** ✅
