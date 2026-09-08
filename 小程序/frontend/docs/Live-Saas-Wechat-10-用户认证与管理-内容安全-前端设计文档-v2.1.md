# 用户认证与管理 — 内容安全增量前端设计文档（V2）

**版本**: V2.1  
**日期**: 2026-07-04  
**状态**: 📋 设计定稿，待开发  
**基于**: 《Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7.md》V1.1  
**后端对齐**: 《10-用户认证与管理-V2-内容安全增量设计文档》V2.1、《12-全局内容安全与审核-后端设计文档》V2.3 §4.2.1  
**共享能力**: 《Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0》§三、§四（**含 §3.0 全员人话原则**）

---

## ⚠️ 重要声明

- 本文档为 **增量**，不替代 V1.0 认证/注册/Token 设计
- 登录、注册、密码、验证码流程 **不变**
- nickname/bio 文本规则在 **users 库**，**不受** live_core 管理端改规则影响（《10-V2》自测 #11）

---

## 📌 变更范围

| 变更类型 | 说明 |
|----------|------|
| 【修改】 | `UpdateProfileRequest` 移除 `avatar_url`，新增 `bio?`；nickname max **50**（V2 Schema） |
| 【修改】 | `uploadAvatar` multipart 字段名 `avatar` → **`file`** |
| 【修改】 | `ProfileEdit.vue`：头像与文本分通道保存 |
| 【新增】 | 2004/2005 统一处理（复用 `utils/contentSafety.ts`） |

---

## 一、涉及文件

```
src/types/auth.ts              # UpdateProfileRequest、AvatarUploadResponse
src/api/user.ts                # uploadAvatar name='file'
src/pages/profile/ProfileEdit.vue
src/store/auth.ts              # 头像上传成功后同步 userInfo.avatar_url
```

---

## 二、接口对齐

### 2.1 PATCH /users/me

**请求体（仅文本）**：

```typescript
{ nickname?: string; bio?: string }   // nickname 1-50
```

**禁止**：`avatar_url` → 后端 `code=4001`（HTTP **400 或 422**），message 提示使用 POST /me/avatar

### 2.2 POST /users/me/avatar

```typescript
// 微信小程序 — 后端要求 JPG / PNG / WEBP
uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'] })
  → request.upload({ url: '/me/avatar', filePath, name: 'file' })
  → 200: data.avatar_url
  → 422/2005: C 端 Toast「暂无法使用此图片，请更换后再试」（**不展示**后端审计 message）
  → 422/2004: 「暂时无法提交，请稍后再试」
```

**禁止**：将 `wxfile://` 或临时路径 PATCH 为头像。

### 2.3 GET /users/me

响应仍含 `avatar_url`（只读展示），无变更。

### 2.4 bio 校验说明

- 后端对 **有变更的** `bio` 执行 `check_content_safety(scene="nickname", field="bio")`
- 前端若 ProfileEdit 暂无 bio UI，可不 PATCH `bio`；有 UI 时必须走同一套 2004/2005 处理

---

## 三、ProfileEdit 交互设计

### 3.1 表单字段

| 字段 | 绑定 | 提交方式 |
|------|------|----------|
| 头像展示 | 本地 `displayAvatar`（来自 store + 上传返回值） | **仅** POST /me/avatar |
| 昵称 | `form.nickname` | PATCH /me |
| 简介 bio | `form.bio`（有 UI 时） | PATCH /me |

### 3.2 更换头像流程

```
点击头像
  → chooseImage（JPG/PNG/WEBP）
  → POST /me/avatar (file)
  → 成功：更新 displayAvatar + authStore.userInfo.avatar_url + Toast「头像已更新」
  → 2005：handleContentSafetyError → 固定人话 Toast（文本/图片见《12》§3.2）
  → 2004：「暂时无法提交，请稍后再试」
  → **不调用 PATCH**
```

### 3.3 保存资料流程

```
点击保存
  → 校验 nickname 非空、≤50
  → PATCH /me { nickname, bio? }   // 不含 avatar_url
  → 成功：同步 store + Toast「保存成功」+ navigateBack
  → 2005/2004：handleContentSafetyError，保留表单
  → 4001（误传 avatar_url）：经 getUserFacingErrorMessage 展示
```

### 3.4 代码要点（伪代码）

```typescript
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'

async function handleChangeAvatar() {
  try {
    const resp = await uploadAvatar(filePath)
    // ...
    uni.showToast({ title: '头像已更新', icon: 'success' })
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '头像上传失败，请稍后再试'), icon: 'none' })
  }
}

async function handleSave() {
  try {
    await updateMyProfile({ nickname: form.nickname.trim(), bio: form.bio?.trim() || undefined })
    // ...
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败，请稍后再试'), icon: 'none' })
  }
}
```

---

## 四、行动清单

| # | 任务 | 验收 |
|---|------|------|
| 1 | `UpdateProfileRequest` 去掉 `avatar_url`，加 `bio?`，nickname 注释 max 50 | 类型检查通过 |
| 2 | `uploadAvatar` 使用 `name: 'file'` | 与后端 multipart 一致 |
| 3 | ProfileEdit 移除 PATCH 中的 `avatar_url` | 自测 #5 |
| 4 | 接入 `handleContentSafetyError`（文本 + 头像） | §五 #2–4、#7–10 |
| 5 | 头像上传成功仅更新 store，不触发 PATCH | 网络面板仅见 POST /me/avatar |
| 6 | chooseImage 限制常见图片格式 | §五 #6 |

---

## 五、自测清单

| # | 测试项 | 预期 | 验证 |
|---|--------|------|------|
| 1 | 昵称 `张医生` | PATCH 成功 | [ ] |
| 2 | 昵称含 URL | 2005 Toast「暂无法发布…」，昵称保留；**无**规则名/违规等词 | [ ] |
| 3 | 昵称含手机号 | 2005 | [ ] |
| 4 | bio 含敏感词（如「根治」） | 2005 | [ ] |
| 5 | 正常流程 PATCH body | **不含** avatar_url | [ ] |
| 6 | 正常 JPG/PNG 图 POST /me/avatar | 200，头像更新 | [ ] |
| 7 | 占位 stub reject 违规图 | 2005，头像不变 | [ ] |
| 8 | 昵称命中 warn 规则 | HTTP 200，更新成功，用户无感知 | [ ] |
| 9 | 文本安全服务故障 | 422/2004 | [ ] |
| 10 | 图片审核服务故障 | 422/2004 | [ ] |
| 11 | live_core 管理端改 message 规则 | **不影响** users 昵称校验结果 | [ ] |

---

## 六、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.0 | 2026-07-04 | 初版 |
| V2.3 | 2026-07-09 | 对齐《12》V1.2 全员人话原则 |
| V2.2 | 2026-07-09 | C 端 Toast 固定人话文案，禁止透传后端审计 message |
| V2.1 | 2026-07-04 | 审计修订：4001 HTTP、头像格式、warn/2004 图片自测、管理端不影响 nickname |

---

**文档结束** ✅
