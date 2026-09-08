# 搜索关键词 — 内容安全增量前端设计文档（V3）

**版本**: V3.1  
**日期**: 2026-07-04  
**状态**: 📋 设计定稿，待开发  
**基于**: `src/subpackages/search/index.vue` 现有搜索页  
**后端对齐**: 《搜索关键词-V3-内容安全增量设计文档》V3.1  
**共享能力**: 《Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0》§3（**含 §3.0 全员人话原则**）

---

## ⚠️ 重要声明

- 后端 **仅** 在以下接口做 `scene=search_query` 校验：
  - `GET /api/core/search?q=...`（综合搜索 / 写历史与热词）
  - `GET /api/core/search/suggestions?keyword=...`（搜索建议）
- **`GET /api/core/rooms?q=...`（searchRooms）不在校验范围**——违禁词仍可能从 rooms 接口返回结果，因此前端必须以 **`globalSearch` 为门禁**，2005 时 **不得** 继续 `fetchTabPage`
- 热词 `GET /search/hot-keywords` **无用户输入**，前端 **不改**
- 服务端历史/热词：block 时后端不写——前端也 **不得** 提前 `saveLocalHistory`
- warn（2006）仍返回 200 + 正常结果，前端无特殊处理

---

## 📌 变更范围

| API | 网关路径 | 前端封装 | 校验 |
|-----|----------|----------|------|
| 综合搜索（**门禁**） | `GET /api/core/search?q=` | `globalSearch` / `recordSearchQuery` | ✅ search_query |
| 搜索建议 | `GET /api/core/search/suggestions?keyword=` | `getSearchSuggestions` | ✅ search_query |
| 房间/专家/品牌分页 | `GET /api/core/rooms?q=` 等 | `searchRooms` / `searchExperts` / … | ❌ **无校验，须在门禁通过后调用** |

---

## 一、涉及文件

```
src/subpackages/search/index.vue   # runSearch、loadSuggestions — **重点改造**
src/api/search.ts                  # globalSearch、getSearchSuggestions — 路径不变
```

---

## 二、交互设计

### 2.1 现网问题（必须修复）

当前 `runSearch` 存在与后端不一致的三处行为：

| 现网问题 | 正确行为 |
|----------|----------|
| `recordSearchQuery(...).catch(() => {})` 静默吞掉 2005 | **必须 await**，2005 时中止整个搜索 |
| `saveLocalHistory(q)` 在 API 校验**之前**执行 | **仅** `globalSearch` 200 成功后写入 |
| 2005 后仍 `fetchTabPage`（`/rooms` 等） | 2005/2004 时 **不** 调用任何 Tab 分页 API |

### 2.2 综合搜索（主流程 — 重写）

```
用户输入 q → 点击搜索/回车
  → 1. await globalSearch(q, { page: 1, size: 1 })   // 门禁，不可 silent catch
  → 2. 422/2005：handleContentSafetyError → Toast「暂无法发布，请修改内容后再试」→ 中止
         · searchedKeyword 不更新
         · loaded=false，清空各 Tab 结果
         · 不 saveLocalHistory
         · 关键词保留在输入框（便于修改）
  → 3. 422/2004：同上
  → 4. 200（allow/warn 均为 200）：
         · searchedKeyword = q
         · saveLocalHistory(q)          // 本地历史
         · resetTabData + 并行 fetchTabPage(/rooms, /experts, /brands)
         · warn 对用户无感知，与 allow 相同
```

> `recordSearchQuery` 内部即 `globalSearch`，二者择一；**禁止** `.catch(() => {})` 忽略错误。

### 2.3 搜索建议

```
输入防抖 → loadSuggestions(keyword)
  → GET /search/suggestions?keyword=...
  → 2005：建议列表置空；默认不 Toast（showToast: false）
  → 2004：置空；可选轻提示
  → 200：正常渲染建议
```

```typescript
import { handleContentSafetyError } from '@/utils/contentSafety'
import { globalSearch, getSearchSuggestions } from '@/api/search'

async function loadSuggestions(q: string) {
  const keywordValue = normalizeKeyword(q)
  if (!keywordValue) {
    suggestions.value = []
    return
  }
  try {
    const resp = await getSearchSuggestions({ keyword: keywordValue, limit: 8 })
    suggestions.value =
      resp.code === 200 && Array.isArray(resp.data)
        ? resp.data.map((item) => normalizeKeyword(item?.keyword)).filter(Boolean)
        : []
  } catch (e) {
    if (handleContentSafetyError(e, { showToast: false })) {
      suggestions.value = []
      return
    }
    suggestions.value = []
  }
}

async function runSearch(refresh = true) {
  const q = keywordNormalized.value
  if (q.length < 2) {
    uni.showToast({ title: '请输入至少2个字符', icon: 'none' })
    return
  }
  if (loading.value) return

  loading.value = true
  error.value = null

  try {
    // Step 1: 门禁 — 对齐后端 search_query 校验
    const gate = await globalSearch(q, { page: 1, size: 1 })
    if (gate.code !== 200) {
      throw Object.assign(new Error(gate.message || '搜索失败'), { code: gate.code })
    }

    // Step 2: 仅通过后更新状态与历史
    if (refresh) {
      searchedKeyword.value = q
      suggestions.value = []
      resetTabData()
      activeTabIndex.value = 0
      saveLocalHistory(q)
    }

    // Step 3: 并行拉各 Tab 结果（/rooms 等无 search_query 校验）
    if (refresh) {
      loaded.value = false
      await Promise.allSettled(
        TAB_TYPES.map((t) => fetchTabPage({ q, type: t, page: 1, append: false, showGlobalError: false }))
      )
    } else {
      const t = activeType.value
      await fetchTabPage({ q, type: t, page: tabState[t].page + 1, append: true, showGlobalError: false })
    }
    loaded.value = true
  } catch (e) {
    if (handleContentSafetyError(e)) {
      loaded.value = false
      resetTabData()
      return
    }
    loaded.value = true
    error.value = getUserFacingErrorMessage(e, '搜索失败，请稍后再试')
    uni.showToast({ title: error.value, icon: 'none' })
  } finally {
    loading.value = false
  }
}
```

### 2.4 与《12》主文档原则对齐

- block 时 **保留** 搜索框关键词（与留言一致）
- **不** 在前端做违禁词预检

---

## 三、行动清单

| # | 任务 | 验收 |
|---|------|------|
| 1 | 删除 `recordSearchQuery(...).catch(() => {})` 静默忽略 | 2005 可被捕获 |
| 2 | `runSearch` 第一步 **await globalSearch** 作为门禁 | 2005 时不请求 `/rooms` |
| 3 | `saveLocalHistory` 移至 globalSearch 200 **之后** | block 无本地历史 |
| 4 | 2005/2004 时 `resetTabData`、不更新 `searchedKeyword` | §四 #2 |
| 5 | `loadSuggestions` 接入 `handleContentSafetyError({ showToast: false })` | §四 #6 |
| 6 | 移除对 `searchRooms` 作为内容安全门禁的误用 | 代码审查 |
| 7 | 热词接口回归 | §四 #9 |
| 8 | warn 搜索词仍走完全流程 | §四 #10 |

---

## 四、自测清单

| # | 测试项 | 预期 | 验证 |
|---|--------|------|------|
| 1 | `q=心血管` | 先 200 `/search`，再展示 rooms 等 Tab 结果 | [ ] |
| 2 | `q=http://abc.com` | 2005 Toast「暂无法发布…」（**无**规则名）；**无** Tab 结果；**无**本地历史 | [ ] |
| 3 | `q=13800138000` | 2005 | [ ] |
| 4 | `q=加V领取资料` | 2005 | [ ] |
| 5 | `q=敏感词` | 2005 | [ ] |
| 6 | 建议 `keyword=www.xxx.com` | 2005，建议列表空 | [ ] |
| 7 | 建议 `keyword=糖尿病` | 正常建议 | [ ] |
| 8 | 安全服务故障 | 2004，同 #2 中止行为 | [ ] |
| 9 | 热词列表 | 行为不变 | [ ] |
| 10 | 命中 search warn 规则 | HTTP 200，正常结果与历史，用户无 warn 提示 | [ ] |
| 11 | 管理端改 search_query 规则后 | 新规则即时生效 | [ ] |
| 12 | block 后服务端 `user_search_history` | 无新增（抓包/DB 验证） | [ ] |
| 13 | 2005 后输入框 | 关键词仍保留 | [ ] |

---

## 五、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V3.0 | 2026-07-04 | 初版 |
| V3.3 | 2026-07-09 | 对齐《12》V1.2 全员人话原则 |
| V3.2 | 2026-07-09 | C 端 Toast 固定人话文案，禁止透传后端审计 message |
| V3.1 | 2026-07-04 | 审计修订：globalSearch 门禁、修复现网三处问题、明确 /rooms 不在校验范围 |

---

**文档结束** ✅
