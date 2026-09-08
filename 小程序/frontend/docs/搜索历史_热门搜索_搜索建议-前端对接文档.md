# 搜索历史、热门搜索、搜索建议 - 前端对接文档

> **生成时间**：2026-05-27
> **版本**：V1.0
> **状态**：已上线可用
> **后端服务**：live_core_service
> **基础路径**：`/api/v1`

---

## 0. 功能总览

本次新增 3 个功能模块，共 6 个 API 接口：

| 功能 | 接口数量 | 认证要求 | 说明 |
|------|----------|----------|------|
| 搜索历史 | 3 个 | 必须登录 | 查看、删除单条、清空全部 |
| 热门搜索 | 1 个 | 公开 | 平台热词排行 |
| 搜索建议 | 1 个 | 公开 | 输入时前缀联想 |
| 搜索记录联动 | 1 个（改造） | 可选 | 搜索接口自动记录历史 |

---

## 1. 接口一览表

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/v1/search/hot-keywords` | 不需要 | 获取热门搜索词 |
| GET | `/api/v1/search/suggestions?keyword=xxx` | 不需要 | 获取搜索建议 |
| GET | `/api/v1/search?q=xxx` | 可选 | 综合搜索（自动记录历史） |
| GET | `/api/v1/users/me/search-history` | 需要 Token | 获取当前用户搜索历史 |
| DELETE | `/api/v1/users/me/search-history/{id}` | 需要 Token | 删除单条历史 |
| DELETE | `/api/v1/users/me/search-history` | 需要 Token | 清空全部历史 |

---

## 2. 接口详细说明

### 2.1 热门搜索

获取平台搜索次数最多的关键词，用于搜索页默认展示。

**请求**

```
GET /api/v1/search/hot-keywords
```

**Query 参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 10 | 返回条数，范围 1-50 |
| days | int | 否 | 7 | 统计天数窗口，范围 1-30 |

**请求示例**

```javascript
// 获取最近7天 Top 10 热词
fetch('/api/v1/search/hot-keywords')

// 获取最近3天 Top 20 热词
fetch('/api/v1/search/hot-keywords?limit=20&days=3')
```

**响应示例**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "keyword": "心血管",
            "search_count": 4,
            "last_searched_at": "2026-05-27T10:33:11.101057Z"
        },
        {
            "keyword": "直播",
            "search_count": 2,
            "last_searched_at": "2026-05-27T09:15:00.000000Z"
        }
    ],
    "timestamp": "2026-05-27T10:34:45.184075Z"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| keyword | string | 热词关键词 |
| search_count | int | 搜索总次数 |
| last_searched_at | string | 最近一次搜索时间（ISO 8601） |

**注意事项**
- 返回的热词按 `search_count` 降序排列
- 只返回最近 N 天内被搜过至少 2 次的词
- 如果没有任何热词，返回空数组 `[]`

---

### 2.2 搜索建议

用户输入时返回前缀匹配的联想词，用于搜索框下拉提示。

**请求**

```
GET /api/v1/search/suggestions?keyword=xxx
```

**Query 参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 是 | - | 用户输入的关键词，1-255 字符 |
| limit | int | 否 | 10 | 返回条数，范围 1-20 |

**请求示例**

```javascript
fetch('/api/v1/search/suggestions?keyword=心血')
```

**响应示例**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        { "keyword": "心血管" },
        { "keyword": "心血管疾病" },
        { "keyword": "心血管内科" }
    ],
    "timestamp": "2026-05-27T10:34:45.549356Z"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| keyword | string | 匹配的完整关键词 |

**注意事项**
- 匹配规则：前缀匹配（`LIKE 'keyword%'`）
- 排除与输入完全相同的词
- 结果按该词的历史搜索总次数降序排列
- 无匹配时返回空数组 `[]`
- **建议做防抖**：用户停止输入 300ms 后再请求

---

### 2.3 综合搜索（自动记录历史）

原有的综合搜索接口，登录用户搜索时会自动记录搜索历史。

**请求**

```
GET /api/v1/search?q=xxx
```

**Query 参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| q | string | 是 | - | 搜索关键词，最少 2 个字符 |
| page | int | 否 | 1 | 页码 |
| size | int | 否 | 10 | 每页数量，最大 50 |
| type | string | 否 | - | 资源类型筛选，逗号分隔 |
| category_id | UUID | 否 | - | 分类 ID 筛选 |
| Authorization | string | 否 | - | `Bearer {token}`，登录用户传入 |

**请求示例**

```javascript
// 匿名搜索（不记录历史）
fetch('/api/v1/search?q=心血管&page=1&size=10')

// 登录搜索（自动记录历史）
fetch('/api/v1/search?q=心血管', {
    headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIs...'
    }
})
```

**响应示例**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total": 5,
        "page": 1,
        "size": 10,
        "items": [
            {
                "type": "room",
                "id": "xxx-xxx-xxx",
                "title": "心血管健康讲座",
                "subtitle": "...",
                "match_score": 0.85,
                "highlight": "<em>心血管</em>健康讲座"
            }
        ]
    },
    "timestamp": "2026-05-27T10:22:08.745751Z"
}
```

**注意事项**
- 搜索历史的记录对前端完全透明，不需要额外调用
- 历史记录失败不影响搜索结果返回
- 同一用户搜同一词会累加 `search_count`，不会重复创建

---

### 2.4 获取搜索历史

获取当前登录用户的搜索历史列表。

**请求**

```
GET /api/v1/users/me/search-history
```

**请求头**

```
Authorization: Bearer {token}
```

**Query 参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 10 | 返回条数，范围 1-20 |

**请求示例**

```javascript
fetch('/api/v1/users/me/search-history?limit=10', {
    headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIs...'
    }
})
```

**响应示例**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": "aa69acac-09d7-4981-b4c4-3ac7b6579b2c",
            "keyword": "直播",
            "search_count": 1,
            "last_searched_at": "2026-05-27T10:35:38.497683Z"
        },
        {
            "id": "28a9989c-e5a8-4a4c-b225-0e6e363ef22b",
            "keyword": "心血管",
            "search_count": 3,
            "last_searched_at": "2026-05-27T10:35:38.414033Z"
        }
    ],
    "timestamp": "2026-05-27T10:35:38.577341Z"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 历史记录 ID（删除时需要） |
| keyword | string | 搜索的关键词 |
| search_count | int | 该词累计搜索次数 |
| last_searched_at | string | 最近搜索时间（ISO 8601） |

**注意事项**
- 按 `last_searched_at` 倒序排列（最近搜索的在最前面）
- 每个用户最多保留 20 条历史，超出自动删除最早的
- 未登录调用返回 401

---

### 2.5 删除单条搜索历史

删除当前用户的某一条搜索历史。

**请求**

```
DELETE /api/v1/users/me/search-history/{history_id}
```

**请求头**

```
Authorization: Bearer {token}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| history_id | UUID | 历史记录 ID（从列表接口获取） |

**请求示例**

```javascript
fetch('/api/v1/users/me/search-history/aa69acac-09d7-4981-b4c4-3ac7b6579b2c', {
    method: 'DELETE',
    headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIs...'
    }
})
```

**成功响应**

```json
{
    "code": 200,
    "message": "删除成功",
    "data": null,
    "timestamp": "2026-05-27T10:35:04.442916Z"
}
```

**错误响应**

```json
{
    "code": 2001,
    "message": "历史记录不存在",
    "data": null,
    "timestamp": "2026-05-27T10:35:04.442916Z"
}
```

---

### 2.6 清空全部搜索历史

清空当前用户的所有搜索历史。

**请求**

```
DELETE /api/v1/users/me/search-history
```

**请求头**

```
Authorization: Bearer {token}
```

**请求示例**

```javascript
fetch('/api/v1/users/me/search-history', {
    method: 'DELETE',
    headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIs...'
    }
})
```

**成功响应**

```json
{
    "code": 200,
    "message": "清空成功",
    "data": {
        "deleted_count": 5
    },
    "timestamp": "2026-05-27T10:35:38.799067Z"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| deleted_count | int | 实际删除的记录数 |

---

## 3. 统一响应格式

所有接口遵循统一的响应格式：

```typescript
interface ApiResponse<T> {
    code: number;        // 业务状态码，200 表示成功
    message: string;     // 响应消息
    data: T;             // 响应数据
    timestamp: string;   // 服务器时间戳（ISO 8601）
}
```

**业务状态码**

| code | 含义 | 说明 |
|------|------|------|
| 200 | 成功 | 请求正常处理 |
| 2001 | 资源不存在 | 删除时 ID 无效 |
| 4001 | 参数错误 | 请求参数不合法 |
| 5001 | 服务器错误 | 服务端内部异常 |

**HTTP 状态码**

| HTTP Status | 场景 |
|-------------|------|
| 200 | 正常响应（包括业务错误） |
| 401 | 未登录或 Token 无效 |
| 404 | 资源不存在（DELETE 时） |
| 500 | 服务器内部错误 |

---

## 4. 前端集成指南

### 4.1 搜索页完整流程

```
页面加载
    │
    ├─→ GET /search/hot-keywords          ──→ 展示「热门搜索」
    │
    ▼
用户输入关键词
    │
    ├─→ (防抖 300ms) GET /search/suggestions?keyword=xxx  ──→ 展示「搜索建议」下拉
    │
    ▼
用户按回车/点击搜索
    │
    ├─→ GET /search?q=xxx                 ──→ 展示搜索结果
    │   (如果是登录用户，后端自动记录历史)
    │
    ▼
用户点击搜索框（聚焦）
    │
    ├─→ GET /users/me/search-history      ──→ 展示「搜索历史」
    │   (如果是登录用户)
```

### 4.2 前端代码示例

#### 4.2.1 API 请求封装

```typescript
const API_BASE = '/api/v1';

// 获取请求头（带 Token）
function getHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

// 统一请求方法
async function request<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
            ...getHeaders(),
            ...options?.headers,
        },
    });
    return response.json();
}
```

#### 4.2.2 热门搜索

```typescript
interface HotKeyword {
    keyword: string;
    search_count: number;
    last_searched_at: string;
}

// 获取热门搜索
async function getHotKeywords(limit = 10, days = 7): Promise<HotKeyword[]> {
    const res = await request<HotKeyword[]>(
        `/search/hot-keywords?limit=${limit}&days=${days}`
    );
    if (res.code === 200) {
        return res.data;
    }
    return [];
}
```

#### 4.2.3 搜索建议（带防抖）

```typescript
interface SearchSuggestion {
    keyword: string;
}

// 获取搜索建议
async function getSuggestions(keyword: string, limit = 10): Promise<string[]> {
    if (!keyword || keyword.trim().length < 1) {
        return [];
    }
    const res = await request<SearchSuggestion[]>(
        `/search/suggestions?keyword=${encodeURIComponent(keyword)}&limit=${limit}`
    );
    if (res.code === 200) {
        return res.data.map(item => item.keyword);
    }
    return [];
}

// 防抖封装
function useDebounce<T extends (...args: any[]) => any>(fn: T, delay: number) {
    let timer: ReturnType<typeof setTimeout>;
    return function (this: any, ...args: Parameters<T>) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// 使用示例
const debouncedGetSuggestions = useDebounce(async (keyword: string) => {
    const suggestions = await getSuggestions(keyword);
    // 更新 UI 展示 suggestions
    setSuggestionList(suggestions);
}, 300);
```

#### 4.2.4 搜索历史

```typescript
interface SearchHistoryItem {
    id: string;           // UUID
    keyword: string;
    search_count: number;
    last_searched_at: string;
}

// 获取搜索历史
async function getSearchHistory(limit = 10): Promise<SearchHistoryItem[]> {
    const res = await request<SearchHistoryItem[]>(
        `/users/me/search-history?limit=${limit}`
    );
    if (res.code === 200) {
        return res.data;
    }
    return [];
}

// 删除单条历史
async function deleteHistoryItem(historyId: string): Promise<boolean> {
    const res = await request<null>(
        `/users/me/search-history/${historyId}`,
        { method: 'DELETE' }
    );
    return res.code === 200;
}

// 清空全部历史
async function clearAllHistory(): Promise<number> {
    const res = await request<{ deleted_count: number }>(
        '/users/me/search-history',
        { method: 'DELETE' }
    );
    if (res.code === 200) {
        return res.data.deleted_count;
    }
    return 0;
}
```

#### 4.2.5 搜索（触发记录）

```typescript
// 搜索接口（登录用户会自动记录历史，前端无需额外操作）
async function search(keyword: string, page = 1, size = 10) {
    const res = await request(
        `/search?q=${encodeURIComponent(keyword)}&page=${page}&size=${size}`
    );
    return res;
}
```

### 4.3 Vue 3 组件示例

```vue
<template>
  <div class="search-page">
    <!-- 搜索框 -->
    <div class="search-box">
      <input
        v-model="keyword"
        @input="onInput"
        @focus="showHistory = true"
        @keyup.enter="doSearch"
        placeholder="搜索..."
      />
      <button @click="doSearch">搜索</button>
    </div>

    <!-- 搜索建议下拉 -->
    <div v-if="suggestions.length > 0" class="suggestions">
      <div
        v-for="item in suggestions"
        :key="item"
        class="suggestion-item"
        @click="selectSuggestion(item)"
      >
        {{ item }}
      </div>
    </div>

    <!-- 搜索历史（聚焦时显示） -->
    <div v-if="showHistory && historyList.length > 0" class="history">
      <div class="history-header">
        <span>搜索历史</span>
        <button @click="handleClearAll">清空</button>
      </div>
      <div
        v-for="item in historyList"
        :key="item.id"
        class="history-item"
      >
        <span @click="selectSuggestion(item.keyword)">{{ item.keyword }}</span>
        <button @click="handleDelete(item.id)">×</button>
      </div>
    </div>

    <!-- 热门搜索（无输入时显示） -->
    <div v-if="!keyword && hotKeywords.length > 0" class="hot-keywords">
      <div class="hot-header">热门搜索</div>
      <div
        v-for="item in hotKeywords"
        :key="item.keyword"
        class="hot-item"
        @click="selectSuggestion(item.keyword)"
      >
        {{ item.keyword }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const keyword = ref('');
const suggestions = ref<string[]>([]);
const historyList = ref<SearchHistoryItem[]>([]);
const hotKeywords = ref<HotKeyword[]>([]);
const showHistory = ref(false);

// 页面加载时获取热词
onMounted(async () => {
    hotKeywords.value = await getHotKeywords();
});

// 输入时获取建议（防抖）
const onInput = useDebounce(async () => {
    if (keyword.value.trim()) {
        suggestions.value = await getSuggestions(keyword.value);
    } else {
        suggestions.value = [];
    }
}, 300);

// 聚焦时获取历史
const onFocus = async () => {
    const token = localStorage.getItem('token');
    if (token) {
        historyList.value = await getSearchHistory();
    }
    showHistory.value = true;
};

// 执行搜索
const doSearch = async () => {
    if (!keyword.value.trim()) return;
    showHistory.value = false;
    suggestions.value = [];
    const result = await search(keyword.value);
    // 处理搜索结果...
};

// 选择建议/历史词
const selectSuggestion = (word: string) => {
    keyword.value = word;
    doSearch();
};

// 删除单条历史
const handleDelete = async (id: string) => {
    await deleteHistoryItem(id);
    historyList.value = historyList.value.filter(item => item.id !== id);
};

// 清空全部历史
const handleClearAll = async () => {
    await clearAllHistory();
    historyList.value = [];
};
</script>
```

---

## 5. 错误处理

### 5.1 未登录访问需认证接口

```json
// HTTP Status: 401
{
    "detail": "认证凭证缺失"
}
```

**处理方式**：跳转登录页或隐藏相关 UI

### 5.2 Token 过期

```json
// HTTP Status: 401
{
    "detail": "认证凭证已过期"
}
```

**处理方式**：清除本地 Token，跳转登录页

### 5.3 资源不存在

```json
// HTTP Status: 200
{
    "code": 2001,
    "message": "历史记录不存在"
}
```

**处理方式**：提示用户并刷新列表

### 5.4 服务器错误

```json
// HTTP Status: 200
{
    "code": 5001,
    "message": "服务器内部错误"
}
```

**处理方式**：提示用户稍后重试

---

## 6. 注意事项

### 6.1 认证

- 热门搜索和搜索建议是**公开接口**，不需要 Token
- 搜索历史相关接口**必须登录**，需要传 `Authorization: Bearer {token}`
- 综合搜索接口**可选认证**：登录用户自动记录历史，匿名用户不记录

### 6.2 性能

- 搜索建议接口建议做 **300ms 防抖**，避免频繁请求
- 热门搜索可在页面加载时请求一次，不需要频繁刷新
- 搜索历史在用户聚焦搜索框时请求即可

### 6.3 数据规则

- 每个用户最多保留 **20 条**搜索历史，超出自动删除最早的
- 同一用户搜同一词会累加次数，不会重复创建
- 热词只显示最近 N 天内被搜过 **至少 2 次**的词
- 关键词标准化：自动 trim + 转小写 + 压缩空白

### 6.4 时序要求

```
1. 页面加载       → GET /search/hot-keywords（展示热词）
2. 用户输入       → GET /search/suggestions?keyword=xxx（防抖 300ms）
3. 用户按回车     → GET /search?q=xxx（自动记录历史）
4. 搜索框聚焦     → GET /users/me/search-history（展示历史）
```

---

## 7. 测试账号

| 账号 | 密码 | 角色 |
|------|------|------|
| test@example.com | - | REGULAR |
| admin@example.com | - | ADMIN |

> Token 由 user_service 的登录接口返回，格式为 `Bearer {token}`

---

## 8. 接口变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-05-27 | V1.0 | 初始版本，6 个接口上线 |
