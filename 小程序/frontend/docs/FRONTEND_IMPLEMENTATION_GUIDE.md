# 前端实现指南 —— 项目B独有功能

> 基于后端已同步的API，逐功能说明前端如何实现。
> 基础路径: `live-streaming-saas-v2-main/backend/live_core_service/`
> API前缀: `/api/v1`

---

## 一、科室分类管理（Category）

### 1.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/content/categories` | 公开 | 获取所有分类（按sort_order排序） |
| 2 | GET | `/admin/categories` | Admin | 管理端分类列表（分页+搜索） |
| 3 | GET | `/content/categories/{category_id}` | 公开 | 获取单个分类详情 |
| 4 | POST | `/admin/categories` | Admin | 创建分类 |
| 5 | PATCH | `/admin/categories/{category_id}` | Admin | 更新分类 |
| 6 | DELETE | `/admin/categories/{category_id}` | Admin | 删除分类（软删除） |
| 7 | POST | `/admin/categories/{category_id}/icon` | Admin | 上传分类图标 |
| 8 | DELETE | `/admin/categories/{category_id}/icon` | Admin | 删除分类图标 |
| 9 | GET | `/rooms/{room_id}/categories` | 公开 | 获取直播间关联的分类 |
| 10 | POST | `/admin/rooms/{room_id}/categories` | Admin | 设置直播间分类（replace/append） |
| 11 | DELETE | `/admin/rooms/{room_id}/categories/{category_id}` | Admin | 解除直播间分类关联 |

### 1.2 数据结构

```typescript
// 分类数据结构
interface Category {
  id: string;           // UUID
  name: string;         // 分类名称，全局唯一，1-100字符
  slug?: string;        // URL友好标识符
  icon?: string;        // 图标名称或URL
  description?: string; // 描述
  sort_order: number;   // 排序值，>=0
  is_active: boolean;   // 是否启用
  created_at: string;
  updated_at: string;
}

// 创建分类
interface CategoryCreate {
  name: string;         // 必填
  slug?: string;
  icon?: string;
  description?: string;
  sort_order?: number;  // 默认0
  is_active?: boolean;  // 默认true
}

// 更新分类（所有字段可选）
interface CategoryUpdate {
  name?: string;
  slug?: string;
  icon?: string;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

// 设置直播间分类
interface LiveRoomCategoriesSetRequest {
  category_ids: string[];  // 分类ID列表，0-50个
  mode: "replace" | "append";  // replace=替换全部, append=追加
}
```

### 1.3 前端页面实现

#### 页面A：分类管理列表（管理端）

**路由建议**: `/admin/categories`

**页面功能**:
- 表格展示所有分类，支持搜索（按名称）
- 每行显示：图标、名称、slug、排序值、状态、操作
- 操作按钮：编辑、删除、上传/更换图标
- 顶部：新增分类按钮

**API调用流程**:
```
1. 页面加载 → GET /admin/categories?page=1&page_size=20&q=搜索词
2. 点击新增 → 弹窗表单 → POST /admin/categories
3. 点击编辑 → 弹窗表单(预填) → PATCH /admin/categories/{id}
4. 上传图标 → POST /admin/categories/{id}/icon (multipart/form-data)
5. 删除图标 → DELETE /admin/categories/{id}/icon
6. 删除分类 → 确认弹窗 → DELETE /admin/categories/{id}
```

**表单字段**:
| 字段 | 类型 | 校验 | 说明 |
|------|------|------|------|
| name | 输入框 | 必填，1-100字符 | 分类名称 |
| slug | 输入框 | 可选，1-120字符 | URL标识符 |
| icon | 图片上传 | 可选 | 上传后自动填入URL |
| description | 文本域 | 可选，最大500字符 | 描述 |
| sort_order | 数字输入 | 可选，>=0 | 排序值，越小越靠前 |
| is_active | 开关 | 默认开启 | 是否启用 |

#### 页面B：直播间分类关联（管理端直播间编辑页内嵌）

**位置**: 直播间编辑页面的"分类"Tab/区块

**UI组件**: 多选标签选择器（类似Tag选择）

**API调用流程**:
```
1. 加载 → GET /rooms/{room_id}/categories （获取已关联分类）
2. 加载 → GET /content/categories （获取全部可选分类）
3. 选择后保存 → POST /admin/rooms/{room_id}/categories
   body: { category_ids: [...], mode: "replace" }
4. 移除单个 → DELETE /admin/rooms/{room_id}/categories/{category_id}
```

#### 页面C：首页科室导航（用户端）

**位置**: 首页顶部科室Tab栏

**UI组件**: 横向滚动Tab，每个Tab显示科室图标+名称

**API调用**:
```
GET /content/categories （自动按sort_order排序，仅返回is_active=true的）
```

**交互**: 点击Tab → 筛选该分类下的直播间（通过 `GET /homepage/rooms?category_id=xxx`）

### 1.4 种子数据参考

seed.py 中预置了15个医学分类：普通外科、神经外科、心内科、骨科、肿瘤科、妇产科、儿科、眼科、耳鼻喉科、消化科、内分泌科、泌尿外科、心胸外科、血管外科、皮肤科。

---

## 二、标签管理（Tag）

### 2.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/content/tags` | 公开+可选认证 | 获取标签列表（支持q搜索、search_type） |
| 2 | GET | `/content/tags/{tag_id}` | - | 获取单个标签（隐含在路由中） |
| 3 | POST | `/admin/tags` | Admin | 创建标签 |
| 4 | PATCH | `/admin/tags/{tag_id}` | Admin | 更新标签 |
| 5 | DELETE | `/admin/tags/{tag_id}` | Admin | 删除标签（软删除） |
| 6 | POST | `/content/sessions/{session_id}/tags` | Admin | 为场次设置标签 |
| 7 | GET | `/content/sessions/{session_id}/tags` | 公开 | 获取场次标签列表 |
| 8 | GET | `/content/tags/search/sessions` | 公开 | 根据标签搜索场次（AND/OR匹配） |
| 9 | DELETE | `/content/sessions/{session_id}/tags/{tag_id}` | Admin | 解除场次标签关联 |

### 2.2 数据结构

```typescript
interface Tag {
  id: string;
  name: string;         // 标签名，全局唯一，1-80字符
  slug?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface TagCreate {
  name: string;         // 必填
  slug?: string;
  description?: string; // 最大500字符
  is_active?: boolean;
}

interface TagUpdate {
  name?: string;
  slug?: string;
  description?: string;
  is_active?: boolean;
}

// 为场次设置标签
interface SessionTagsSetRequest {
  tag_ids: string[];    // 1-50个标签ID
  mode: "replace" | "append";
}
```

### 2.3 前端页面实现

#### 页面A：标签管理（管理端）

**路由建议**: `/admin/tags`

**页面功能**:
- 表格展示所有标签，支持搜索（按名称，参数 `q`）
- 操作：新增、编辑、删除
- 搜索类型支持：`search_type` 参数可选

**API调用流程**:
```
1. 加载 → GET /content/tags?q=搜索词&include_inactive=true
2. 新增 → POST /admin/tags
3. 编辑 → PATCH /admin/tags/{id}
4. 删除 → 确认 → DELETE /admin/tags/{id}
```

#### 页面B：场次标签管理（场次编辑页内嵌）

**位置**: 直播场次编辑页面的"标签"区块

**UI组件**: 带搜索的多选下拉框（Select with Search, Multi）

**API调用流程**:
```
1. 加载 → GET /content/sessions/{session_id}/tags （已有标签）
2. 加载 → GET /content/tags （全部可选标签）
3. 添加标签 → POST /content/sessions/{session_id}/tags
   body: { tag_ids: [新选的标签ID], mode: "append" }
4. 移除标签 → DELETE /content/sessions/{session_id}/tags/{tag_id}
```

#### 页面C：按标签搜索场次（用户端）

**位置**: 搜索结果页或标签点击后的筛选页

**API调用**:
```
GET /content/tags/search/sessions?tag_ids=xxx&tag_ids=yyy&match_all=true
```
- `match_all=true` = AND匹配（同时包含所有标签）
- `match_all=false` = OR匹配（包含任一标签即可）

---

## 三、首页焦点图管理（Featured Content / Banner）

### 3.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/featured-content` | 公开 | 获取首页焦点图（最多10条，仅启用+在有效期内） |
| 2 | GET | `/admin/featured-content` | Admin | 管理端焦点图列表（分页+搜索） |
| 3 | POST | `/admin/featured-content` | Admin | 创建焦点图 |
| 4 | GET | `/admin/featured-content/{content_id}` | Admin | 获取焦点图详情 |
| 5 | PATCH | `/admin/featured-content/{content_id}` | Admin | 更新焦点图（部分更新） |
| 6 | DELETE | `/admin/featured-content/{content_id}` | Admin | 删除焦点图（软删除） |
| 7 | POST | `/admin/featured-content/{content_id}/image` | Admin | 上传焦点图图片 |

### 3.2 数据结构

```typescript
interface FeaturedContent {
  id: string;              // UUID
  title: string;           // 焦点图标题，1-255字符
  subtitle?: string;       // 副标题，最大512字符
  image_url: string;       // 图片URL，必填
  target_type?: string;    // 跳转目标类型: "room" | "session" | "topic" | "brand" | "external"
  target_id?: string;      // 目标UUID（当target_type非external时使用）
  target_url?: string;     // 外部链接URL（优先级高于target_id）
  sort_order: number;      // 排序值
  is_active: boolean;      // 是否启用
  start_at?: string;       // 上线时间（ISO 8601）
  end_at?: string;         // 下线时间（ISO 8601）
  created_at: string;
  updated_at: string;
}

interface FeaturedContentCreate {
  title: string;           // 必填
  subtitle?: string;
  image_url: string;       // 必填
  target_type?: string;
  target_id?: string;
  target_url?: string;
  sort_order?: number;     // 默认0
  is_active?: boolean;     // 默认true
  start_at?: string;
  end_at?: string;
}

// 部分更新，所有字段可选
interface FeaturedContentUpdate {
  title?: string;
  subtitle?: string;
  image_url?: string;
  target_type?: string;
  target_id?: string;
  target_url?: string;
  sort_order?: number;
  is_active?: boolean;
  start_at?: string;
  end_at?: string;
}
```

### 3.3 前端页面实现

#### 页面A：焦点图管理（管理端）

**路由建议**: `/admin/featured-content`

**页面功能**:
- 表格展示所有焦点图（含未启用的）
- 每行显示：缩略图、标题、目标类型、排序、状态（启用/禁用）、有效期、操作
- 拖拽排序（可选，通过PATCH更新sort_order）
- 操作：新增、编辑、删除、上传/更换图片

**API调用流程**:
```
1. 加载 → GET /admin/featured-content?page=1&page_size=20
2. 新增 → POST /admin/featured-content
3. 编辑 → PATCH /admin/featured-content/{id}
4. 上传图片 → POST /admin/featured-content/{id}/image (multipart/form-data)
5. 删除 → 确认 → DELETE /admin/featured-content/{id}
```

**表单字段**:
| 字段 | 类型 | 校验 | 说明 |
|------|------|------|------|
| title | 输入框 | 必填，1-255字符 | 焦点图标题 |
| subtitle | 输入框 | 可选，最大512字符 | 副标题 |
| image_url | 图片上传 | 必填 | 上传后自动填入URL，建议尺寸 750x320 |
| target_type | 下拉选择 | 可选 | room/session/topic/brand/external |
| target_id | 关联选择 | 条件必填 | 当target_type非external时，弹窗选择对应资源 |
| target_url | 输入框 | 条件必填 | 当target_type=external时填写 |
| sort_order | 数字 | 可选 | 排序值 |
| is_active | 开关 | 默认开启 | 是否启用 |
| start_at | 日期时间选择器 | 可选 | 上线时间 |
| end_at | 日期时间选择器 | 可选 | 下线时间，须晚于start_at |

**target_type联动逻辑**:
```
target_type = "room"    → 显示直播间选择器，选中后填入target_id
target_type = "session" → 显示场次选择器，选中后填入target_id
target_type = "topic"   → 显示专题选择器，选中后填入target_id
target_type = "brand"   → 显示品牌选择器，选中后填入target_id
target_type = "external"→ 显示URL输入框，填入target_url
未选择                  → 纯展示图，不跳转
```

#### 页面B：首页焦点图轮播（用户端）

**位置**: 首页顶部轮播区域

**UI组件**: Swiper/Carousel轮播组件

**API调用**:
```
GET /featured-content
```

**渲染逻辑**:
```typescript
// 响应自动过滤：is_active=true 且当前时间在start_at~end_at之间
// 最多返回10条，按sort_order排序
const banners = await fetch('/api/v1/featured-content');

// 点击跳转逻辑
function handleClick(banner: FeaturedContent) {
  if (banner.target_url) {
    window.open(banner.target_url);  // 外部链接优先
  } else if (banner.target_id) {
    switch (banner.target_type) {
      case 'room':    navigate(`/rooms/${banner.target_id}`); break;
      case 'session': navigate(`/sessions/${banner.target_id}`); break;
      case 'topic':   navigate(`/topics/${banner.target_id}`); break;
      case 'brand':   navigate(`/brands/${banner.target_id}`); break;
    }
  }
}
```

### 3.4 种子数据参考

seed.py 中预置了5条焦点图数据，target_type涵盖 room 和 external 两种。

---

## 四、专家管理（Expert）

### 4.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/featured-experts` | 公开 | 获取首页推荐专家 |
| 2 | GET | `/experts` | 公开 | 专家列表（分页） |
| 3 | GET | `/experts/{expert_id}` | 公开 | 专家详情 |
| 4 | GET | `/experts/{expert_id}/sessions` | 公开 | 专家参与的场次列表 |
| 5 | GET | `/experts/{expert_id}/is-followed` | 登录用户 | 检查是否已关注 |
| 6 | POST | `/admin/experts` | Admin | 创建专家 |
| 7 | GET | `/admin/experts` | Admin | 管理端专家列表（分页） |
| 8 | PATCH | `/admin/experts/{expert_id}` | Admin | 更新专家 |
| 9 | DELETE | `/admin/experts/{expert_id}` | Admin | 删除专家（软删除） |
| 10 | POST | `/admin/experts/{expert_id}/avatar` | Admin | 上传专家头像 |
| 11 | POST | `/admin/experts/batch-import` | Admin | CSV批量导入专家 |
| 12 | POST | `/users/me/followed-experts` | 登录用户 | 关注专家 |
| 13 | DELETE | `/users/me/followed-experts/{expert_id}` | 登录用户 | 取消关注 |
| 14 | GET | `/users/me/followed-experts` | 登录用户 | 获取关注的专家列表 |
| 15 | POST | `/experts/sessions/{session_id}/experts` | Admin **或** 场次所属房间 owner | 为场次设置专家（可绑任意启用专家，支持联动） |
| 16 | GET | `/experts/sessions/{session_id}/experts` | 公开 | 获取场次专家列表 |

### 4.2 数据结构

```typescript
interface Expert {
  id: string;               // UUID
  user_id?: string;         // 关联的用户ID
  name: string;             // 专家姓名
  title?: string;           // 职称（如主任医师、教授）
  hospital?: string;        // 所属医院
  department?: string;      // 所属科室
  expertise_areas?: string; // 擅长领域描述
  bio?: string;             // 个人简介
  avatar_url?: string;      // 头像URL
  is_featured: boolean;     // 是否推荐
  is_active: boolean;       // 是否启用
  sort_order: number;       // 排序值
  contact_info?: object;    // 联系方式（JSONB）
  created_at: string;
  updated_at: string;
}

interface ExpertCreate {
  name: string;             // 必填
  title?: string;
  hospital?: string;
  department?: string;
  expertise_areas?: string;
  bio?: string;
  is_featured?: boolean;
  is_active?: boolean;
  sort_order?: number;
  contact_info?: object;
}

interface ExpertUpdate {
  name?: string;
  title?: string;
  hospital?: string;
  department?: string;
  expertise_areas?: string;
  bio?: string;
  is_featured?: boolean;
  is_active?: boolean;
  sort_order?: number;
  contact_info?: object;
}

// 场次关联专家
interface SessionExpertItem {
  expert_id: string;
  role: string;  // "主讲" | "主持" | "嘉宾" 等
}

// 关注专家
interface ExpertFollowRequest {
  expert_id: string;
}
```

### 4.3 前端页面实现

#### 页面A：专家管理列表（管理端）

**路由建议**: `/admin/experts`

**页面功能**:
- 表格展示所有专家，支持分页
- 每行显示：头像、姓名、职称、医院、科室、是否推荐、状态、操作
- 操作：编辑、删除、上传/更换头像、批量导入
- 顶部：新增专家、批量导入按钮

**API调用流程**:
```
1. 加载 → GET /admin/experts?page=1&page_size=20
2. 新增 → POST /admin/experts
3. 编辑 → PATCH /admin/experts/{id}
4. 上传头像 → POST /admin/experts/{id}/avatar (multipart/form-data)
5. 删除 → 确认 → DELETE /admin/experts/{id}
6. 批量导入 → 上传CSV文件 → POST /admin/experts/batch-import
```

**表单字段**:
| 字段 | 类型 | 校验 | 说明 |
|------|------|------|------|
| name | 输入框 | 必填 | 专家姓名 |
| title | 输入框 | 可选 | 职称 |
| hospital | 输入框 | 可选 | 所属医院 |
| department | 输入框 | 可选 | 所属科室 |
| expertise_areas | 文本域 | 可选 | 擅长领域 |
| bio | 文本域 | 可选 | 个人简介 |
| avatar | 图片上传 | 可选 | 上传后自动填入URL |
| is_featured | 开关 | 默认关闭 | 是否推荐到首页 |
| is_active | 开关 | 默认开启 | 是否启用 |
| sort_order | 数字 | 可选 | 排序值 |

#### 页面B：专家详情页（用户端）

**路由建议**: `/experts/{expert_id}`

**页面功能**:
- 专家头像、姓名、职称、医院、科室
- 擅长领域、个人简介
- 关注/取消关注按钮
- 参与的直播场次列表

**API调用流程**:
```
1. 加载专家信息 → GET /experts/{expert_id}
2. 检查关注状态 → GET /experts/{expert_id}/is-followed （需登录）
3. 加载关联场次 → GET /experts/{expert_id}/sessions
4. 关注 → POST /users/me/followed-experts  body: { expert_id }
5. 取消关注 → DELETE /users/me/followed-experts/{expert_id}
```

#### 页面C：首页推荐专家（用户端）

**位置**: 首页"推荐专家"区块

**UI组件**: 横向滚动卡片列表

**API调用**:
```
GET /featured-experts
```

**卡片内容**: 头像、姓名、职称、医院、科室、关注按钮

#### 页面D：场次专家管理（管理端场次编辑页内嵌）

**位置**: 场次编辑页面的"专家"区块

**UI组件**: 带角色选择的专家选择器

**API调用流程**:
```
1. 加载 → GET /experts/sessions/{session_id}/experts （已有专家）
2. 加载 → GET /experts?is_active=true （全部可选专家）
3. 设置 → POST /experts/sessions/{session_id}/experts
   body: [{ expert_id: "xxx", role: "主讲" }, { expert_id: "yyy", role: "嘉宾" }]
```

### 4.4 种子数据参考

seed.py 中从CSV文件导入了约400名专家数据。

---

## 五、品牌管理（Brand）

### 5.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/brands` | 公开 | 获取品牌列表 |
| 2 | GET | `/brands/{brand_id}/content` | 公开 | 获取品牌详情及关联专题 |
| 3 | POST | `/admin/brands` | Admin | 创建品牌 |
| 4 | GET | `/admin/brands` | Admin | 管理端品牌列表（分页） |
| 5 | GET | `/admin/brands/{brand_id}` | Admin | 获取品牌详情 |
| 6 | PATCH | `/admin/brands/{brand_id}` | Admin | 更新品牌 |
| 7 | DELETE | `/admin/brands/{brand_id}` | Admin | 删除品牌 |
| 8 | POST | `/admin/brands/{brand_id}/logo` | Admin | 上传品牌Logo |
| 9 | POST | `/admin/brands/{brand_id}/topics` | Admin | 批量关联专题到品牌 |
| 10 | DELETE | `/admin/brands/{brand_id}/topics/{topic_id}` | Admin | 解除品牌-专题关联 |
| 11 | GET | `/admin/brands/{brand_id}/topics` | Admin | 获取品牌关联的专题列表 |
| 12 | GET | `/admin/brands/{brand_id}/rooms` | Admin | 获取品牌关联的直播间列表 |
| 13 | POST | `/admin/rooms/{room_id}/brands` | Admin **或** 房间 owner | 绑定直播间品牌（可绑任意启用品牌，支持联动） |
| 14 | GET | `/admin/rooms/{room_id}/brands` | Admin | 获取直播间绑定的品牌 |
| 15 | GET | `/rooms/{room_id}/brands` | 公开 | 获取直播间品牌Tab内容 |

### 5.2 数据结构

```typescript
interface Brand {
  id: string;            // UUID
  name: string;          // 品牌名称
  slug?: string;         // URL标识符
  logo_url?: string;     // Logo图片URL
  description?: string;  // 品牌描述
  website_url?: string;  // 品牌官网
  sort_order: number;    // 排序值
  is_active: boolean;    // 是否启用
  created_at: string;
  updated_at: string;
}

interface BrandCreate {
  name: string;          // 必填
  slug?: string;
  description?: string;
  website_url?: string;
  sort_order?: number;
  is_active?: boolean;
}

interface BrandUpdate {
  name?: string;
  slug?: string;
  description?: string;
  website_url?: string;
  sort_order?: number;
  is_active?: boolean;
}

// 品牌关联专题
interface BrandTopicBindIn {
  topic_ids: string[];   // 专题ID列表
}

// 品牌关联直播间
interface BrandRoomBindIn {
  brand_ids: string[];   // 品牌ID列表
}

// 品牌详情页内容
interface BrandContentData {
  brand: Brand;
  topics: TopicBriefItem[];  // 关联的专题列表
}
```

### 5.3 前端页面实现

#### 页面A：品牌管理列表（管理端）

**路由建议**: `/admin/brands`

**页面功能**:
- 表格展示所有品牌
- 每行显示：Logo、名称、官网、排序、状态、操作
- 操作：编辑、删除、上传/更换Logo、管理关联专题

**API调用流程**:
```
1. 加载 → GET /admin/brands?page=1&page_size=20
2. 新增 → POST /admin/brands
3. 编辑 → PATCH /admin/brands/{id}
4. 上传Logo → POST /admin/brands/{id}/logo (multipart/form-data)
5. 删除 → 确认 → DELETE /admin/brands/{id}
```

**表单字段**:
| 字段 | 类型 | 校验 | 说明 |
|------|------|------|------|
| name | 输入框 | 必填 | 品牌名称 |
| slug | 输入框 | 可选 | URL标识符 |
| logo | 图片上传 | 可选 | Logo图片 |
| description | 文本域 | 可选 | 品牌描述 |
| website_url | 输入框 | 可选 | 品牌官网URL |
| sort_order | 数字 | 可选 | 排序值 |
| is_active | 开关 | 默认开启 | 是否启用 |

#### 页面B：品牌详情页（用户端）

**路由建议**: `/brands/{brand_id}`

**页面功能**:
- 品牌Logo、名称、描述、官网链接
- 关联的专题列表（可点击跳转）

**API调用**:
```
GET /brands/{brand_id}/content
```

#### 页面C：品牌-专题关联管理（管理端品牌详情页内嵌）

**位置**: 品牌编辑页面的"关联专题"Tab

**API调用流程**:
```
1. 加载已关联专题 → GET /admin/brands/{brand_id}/topics
2. 加载全部专题 → GET /topics （用于选择）
3. 批量关联 → POST /admin/brands/{brand_id}/topics  body: { topic_ids: [...] }
4. 解除关联 → DELETE /admin/brands/{brand_id}/topics/{topic_id}
```

#### 页面D：直播间品牌绑定（管理端直播间编辑页内嵌）

**位置**: 直播间编辑页面的"品牌"区块

**API调用流程**:
```
1. 加载已绑定品牌 → GET /admin/rooms/{room_id}/brands
2. 加载全部品牌 → GET /brands （用于选择）
3. 绑定 → POST /admin/rooms/{room_id}/brands  body: { brand_ids: [...] }
```

### 5.4 种子数据参考

seed.py 中预置了10个品牌数据（医疗行业合作伙伴）。

---

## 六、直播间Tab管理（Live Room Tabs）

### 6.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/admin/rooms/{room_id}/tabs` | Admin **或** 房间 owner | 获取房间所有Tab |
| 2 | POST | `/admin/rooms/{room_id}/tabs` | Admin **或** 房间 owner | 创建房间Tab |
| 3 | POST | `/admin/rooms/{room_id}/tabs/image` | Admin **或** 房间 owner | 上传Tab图片 |
| 4 | PATCH | `/admin/tabs/{tab_id}` | Admin **或** 房间 owner | 更新Tab |
| 5 | DELETE | `/admin/tabs/{tab_id}` | Admin **或** 房间 owner | 删除Tab |

### 6.2 数据结构

```typescript
interface LiveRoomTab {
  id: string;
  room_id: string;
  title: string;         // Tab标题
  content?: string;      // Tab内容（富文本/HTML）
  image_url?: string;    // Tab图片URL
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface LiveRoomTabCreate {
  title: string;         // 必填
  content?: string;
  sort_order?: number;
  is_active?: boolean;
}

interface LiveRoomTabUpdate {
  title?: string;
  content?: string;
  sort_order?: number;
  is_active?: boolean;
}
```

### 6.3 前端页面实现

#### 页面：直播间Tab管理（管理端直播间编辑页内嵌）

**位置**: 直播间编辑页面的"Tab配置"区块

**UI组件**: Tab列表（可拖拽排序）+ 每个Tab的编辑表单

**API调用流程**:
```
1. 加载 → GET /admin/rooms/{room_id}/tabs
2. 新增Tab → POST /admin/rooms/{room_id}/tabs
3. 上传Tab图片 → POST /admin/rooms/{room_id}/tabs/image (multipart/form-data)
4. 编辑Tab → PATCH /admin/tabs/{tab_id}
5. 删除Tab → 确认 → DELETE /admin/tabs/{tab_id}
```

**Tab编辑表单字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| title | 输入框 | Tab标题，必填 |
| content | 富文本编辑器 | Tab内容 |
| image | 图片上传 | Tab图片 |
| sort_order | 数字 | 排序值 |

**用户端展示**: 直播间详情页内，以Tab切换形式展示不同内容板块。

---

## 七、直播间留言（Room Messages）

### 7.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | POST | `/rooms/{room_id}/messages` | 登录用户 | 发送留言 |
| 2 | GET | `/rooms/{room_id}/messages` | 公开 | 获取留言列表 |

### 7.2 数据结构

```typescript
interface LiveRoomMessageCreate {
  content: string;       // 留言内容
  // 可能还有 parent_id 等字段用于回复
}

interface LiveRoomMessage {
  id: string;
  room_id?: string;
  user_id?: string;
  content: string;
  created_at: string;
  /** 兼容旧字段：优先用 user.nickname */
  user_display_name?: string;
  /** 用户展示信息（发送时快照；对齐设计文档） */
  user?: {
    nickname?: string;
    avatar_url?: string;
  };
}
```

**前端展示建议**:
```
昵称 = msg.user?.nickname || msg.user_display_name || '匿名用户'
头像 = msg.user?.avatar_url || 默认头像
```
> 注意：需重新登录或 refresh Token 后，新留言才会带上头像快照；历史留言若无 `extra` 快照则昵称/头像可为空。

### 7.3 前端页面实现

#### 页面：直播间留言区（用户端直播间详情页内嵌）

**位置**: 直播间详情页底部或侧边栏

**UI组件**: 留言列表 + 输入框

**API调用流程**:
```
1. 加载留言 → GET /rooms/{room_id}/messages?page=1&page_size=20
2. 发送留言 → POST /rooms/{room_id}/messages  body: { content: "留言内容" }
```

**交互**: 发送后刷新列表，支持分页加载更多。

---

## 八、用户行为功能（Favorites / Watch History / Subscriptions）

### 8.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | POST | `/users/me/favorites` | 登录用户 | 添加收藏 |
| 2 | GET | `/users/me/favorites` | 登录用户 | 获取收藏列表 |
| 3 | DELETE | `/users/me/favorites/{room_id}` | 登录用户 | 取消收藏 |
| 4 | GET | `/rooms/{room_id}/is-favorited` | 登录用户 | 检查是否已收藏 |
| 5 | POST | `/users/me/watch-history` | 登录用户 | 记录观看历史 |
| 6 | GET | `/users/me/watch-history` | 登录用户 | 获取观看历史 |
| 7 | DELETE | `/users/me/watch-history/{history_id}` | 登录用户 | 删除观看记录 |
| 8 | POST | `/users/me/subscriptions` | 登录用户 | 添加订阅 |
| 9 | GET | `/users/me/subscriptions` | 登录用户 | 获取订阅列表 |
| 10 | DELETE | `/users/me/subscriptions` | 登录用户 | 取消订阅 |

### 8.2 数据结构

```typescript
interface FavoriteCreate {
  room_id: string;
}

interface FavoriteItem {
  id: string;
  user_id: string;
  room_id: string;
  created_at: string;
  room?: LiveRoom;  // 嵌套的直播间信息
}

interface WatchEventRequest {
  room_id: string;
  session_id?: string;
  event_type: string;  // "start" | "end" | "progress"
  progress?: number;   // 观看进度（秒）
  duration?: number;   // 观看时长（秒）
}

interface HistoryItem {
  id: string;
  user_id: string;
  room_id: string;
  session_id?: string;
  last_position: number;  // 上次播放位置
  total_duration: number; // 总时长
  watched_at: string;     // 最后观看时间
}

interface SubscriptionCreate {
  target_type: string;  // "room" | "expert" 等
  target_id: string;
}
```

### 8.3 前端页面实现

#### 页面A：我的收藏（用户端）

**路由建议**: `/user/favorites`

**API调用**:
```
GET /users/me/favorites?page=1&page_size=20
```

#### 页面B：观看历史（用户端）

**路由建议**: `/user/history`

**API调用**:
```
GET /users/me/watch-history?page=1&page_size=20
```

**交互**: 继续观看按钮（根据 `last_position` 跳转到上次位置）

#### 页面C：收藏按钮组件（通用组件）

**位置**: 直播间卡片、直播间详情页

**API调用流程**:
```
1. 检查状态 → GET /rooms/{room_id}/is-favorited
2. 收藏 → POST /users/me/favorites  body: { room_id }
3. 取消收藏 → DELETE /users/me/favorites/{room_id}
```

#### 页面D：观看记录上报（直播间播放器内嵌逻辑）

**位置**: 直播/回放播放器组件

**上报时机**:
- 进入直播间: `{ event_type: "start" }`
- 每30秒: `{ event_type: "progress", progress: 当前秒数 }`
- 离开直播间: `{ event_type: "end", progress: 当前秒数, duration: 总时长 }`

**API调用**:
```
POST /users/me/watch-history
body: { room_id, session_id, event_type, progress, duration }
```

---

## 九、用户偏好与通知（Preferences & Notifications）

### 9.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/users/me/preferences` | 登录用户 | 获取用户偏好设置 |
| 2 | PATCH | `/users/me/preferences` | 登录用户 | 更新用户偏好 |
| 3 | GET | `/users/me/notifications` | 登录用户 | 获取通知列表 |
| 4 | GET | `/users/me/notifications/{id}` | 登录用户 | 获取通知详情 |
| 5 | GET | `/users/me/notifications/unread-count` | 登录用户 | 获取未读通知数量 |
| 6 | POST | `/users/me/notifications/{id}/read` | 登录用户 | 标记单条通知已读 |
| 7 | POST | `/users/me/notifications/read-all` | 登录用户 | 标记所有通知已读 |
| 8 | POST | `/admin/notifications` | Admin | 创建通知（管理员） |
| 9 | GET | `/admin/notifications` | Admin | 获取通知列表（管理员） |
| 10 | PATCH | `/admin/notifications/{id}` | Admin | 更新通知 |
| 11 | DELETE | `/admin/notifications/{id}` | Admin | 删除通知 |
| 12 | POST | `/admin/notifications/batch-delete` | Admin | 批量删除通知 |

### 9.2 数据结构

```typescript
interface UserPreferences {
  pinned_categories?: string[];  // 固定的科室ID列表（最多5个）
  notification_settings?: object; // 通知偏好设置
  // 其他偏好字段...
}

interface UserPreferencesUpdate {
  pinned_categories?: string[];  // JSONB数组，最多5个UUID
  notification_settings?: object;
}

interface Notification {
  id: string;
  title: string;
  content: string;
  type?: string;        // 通知类型
  is_read: boolean;
  created_at: string;
}

interface NotificationCreateRequest {
  title: string;
  content: string;
  type?: string;
  target_users?: string[]; // 目标用户ID列表，空则全站通知
}
```

### 9.3 前端页面实现

#### 页面A：通知中心（用户端）

**路由建议**: `/user/notifications`

**页面功能**:
- 通知列表，已读/未读样式区分
- 未读数量角标（Header通知图标上）
- 全部标记已读按钮

**API调用流程**:
```
1. 加载通知 → GET /users/me/notifications?page=1&page_size=20
2. 获取未读数 → GET /users/me/notifications/unread-count
3. 点击通知 → 标记已读 → POST /users/me/notifications/{id}/read
4. 全部已读 → POST /users/me/notifications/read-all
```

#### 页面B：用户偏好设置（用户端）

**路由建议**: `/user/settings/preferences`

**页面功能**:
- 科室星标固定（最多选择5个科室）
- 通知偏好设置

**API调用流程**:
```
1. 加载偏好 → GET /users/me/preferences
2. 加载科室列表 → GET /content/categories
3. 保存偏好 → PATCH /users/me/preferences
   body: { pinned_categories: ["uuid1", "uuid2", ...] }
```

#### 页面C：通知管理（管理端）

**路由建议**: `/admin/notifications`

**API调用流程**:
```
1. 加载 → GET /admin/notifications?page=1&page_size=20
2. 创建 → POST /admin/notifications
3. 编辑 → PATCH /admin/notifications/{id}
4. 删除 → DELETE /admin/notifications/{id}
5. 批量删除 → POST /admin/notifications/batch-delete  body: { ids: [...] }
```

---

## 十、用户认证与管理（Auth & Users）

### 10.1 后端API清单

**认证模块** (`/auth`):

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/auth/captcha` | 公开 | 获取图形验证码 |
| 2 | POST | `/auth/verification-codes` | 公开 | 发送OTP验证码 |
| 3 | POST | `/auth/login` | 公开 | 用户登录 |
| 4 | POST | `/auth/refresh` | 公开 | 刷新访问令牌 |
| 5 | POST | `/auth/logout` | 登录用户 | 用户登出 |
| 6 | POST | `/auth/password-reset-request` | 公开 | 请求密码重置 |
| 7 | POST | `/auth/password-reset` | 公开 | 执行密码重置 |
| 8 | POST | `/auth/sso-login` | 公开 | Authing SSO登录 |

**用户模块** (`/users`):

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | POST | `/users/register` | 公开 | 用户注册 |
| 2 | GET | `/users/me` | 登录用户 | 获取当前用户信息 |
| 3 | PATCH | `/users/me` | 登录用户 | 更新个人信息 |
| 4 | DELETE | `/users/me` | 登录用户 | 注销账户 |
| 5 | POST | `/users/me/password` | 登录用户 | 修改密码 |
| 6 | POST | `/users/me/phone` | 登录用户 | 绑定手机号 |

**管理员模块** (`/admin/users`):

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/admin/users` | Admin | 用户列表（分页+筛选） |
| 2 | PATCH | `/admin/users/{user_uuid}` | Admin | 管理员更新用户 |

### 10.2 数据结构

```typescript
// 登录请求
interface LoginRequest {
  username: string;        // 用户名或邮箱
  password: string;
  captcha_id: string;      // 从 GET /auth/captcha 获取
  captcha_solution: string; // 验证码答案
}

// 登录响应
interface LoginResponse {
  access_token: string;    // JWT，1小时有效
  refresh_token: string;   // JWT，7天有效
  token_type: "bearer";
}

// 注册请求
interface RegisterRequest {
  username: string;        // 3-50字符
  email: string;           // 有效邮箱
  password: string;        // 8位+大小写+数字+特殊字符
  verification_code: string; // OTP验证码
}

// 发送验证码
interface VerificationCodeRequest {
  channel: "EMAIL" | "SMS";
  recipient: string;       // 邮箱或手机号
  scenario: "REGISTER" | "RESET_PASSWORD" | "LOGIN";
  captcha_id: string;
  captcha_solution: string;
}

// 刷新令牌
interface RefreshTokenRequest {
  refresh_token: string;
}

// 用户信息
interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  nickname?: string;
  avatar_url?: string;
  role: "USER" | "ADMIN" | "SUPERADMIN";
  status: string;
  phone?: string;
  created_at: string;
}
```

### 10.3 前端页面实现

#### 页面A：登录页

**路由**: `/login`

**登录流程**:
```
1. 加载验证码 → GET /auth/captcha → 获得 captcha_id + captcha_image
2. 用户输入用户名、密码、验证码
3. 提交 → POST /auth/login
4. 成功 → 存储 access_token + refresh_token → 跳转首页
5. access_token 过期 → POST /auth/refresh → 获取新 access_token
```

**Token管理**:
```
- access_token 存 localStorage，每次请求 Header: Authorization: Bearer {token}
- refresh_token 存 localStorage
- access_token 过期(401) → 自动调 /auth/refresh → 更新 access_token
- refresh_token 也过期 → 跳转登录页
```

#### 页面B：注册页

**路由**: `/register`

**注册流程**:
```
1. 加载验证码 → GET /auth/captcha
2. 填写邮箱 → 点击发送验证码 → POST /auth/verification-codes
   body: { channel: "EMAIL", recipient: email, scenario: "REGISTER", captcha_id, captcha_solution }
3. 填写用户名、密码、验证码
4. 提交 → POST /users/register
5. 成功 → 跳转登录页
```

**密码强度校验**（前端实时校验，与后端一致）:
- 最少8位
- 包含大写字母
- 包含小写字母
- 包含数字
- 包含特殊字符

#### 页面C：忘记密码/重置密码

**路由**: `/forgot-password`

**流程**:
```
1. GET /auth/captcha
2. POST /auth/password-reset-request  body: { email, captcha_id, captcha_solution }
3. 用户收到邮件中的 reset_token
4. POST /auth/password-reset  body: { reset_token, new_password }
```

#### 页面D：个人中心

**路由**: `/user/profile`

**API调用**:
```
1. GET /users/me → 展示用户信息
2. PATCH /users/me → 更新个人信息
3. POST /users/me/password → 修改密码
4. POST /users/me/phone → 绑定手机号（需验证码）
5. DELETE /users/me → 注销账户（二次确认）
```

#### 页面E：管理员用户管理

**路由**: `/admin/users`

**API调用**:
```
1. GET /admin/users?page=1&size=20&username=xxx&role=ADMIN&status=NORMAL&can_stream=false
2. PATCH /admin/users/{uuid} → 更新 status / can_stream / role（role 仅超管）
```

**体验约定（V2.1）**:
- 操作分离：**禁止开播 / 恢复开播** | **禁用/恢复账号** | **设为管理员**（仅超管）
- 开播开关为次要紧急操作；日常停人用禁用账号
- 用户侧：默认可创建直播；仅 `can_stream===false` 时灰显并提示「开播功能已被禁用」

### 10.4 Axios拦截器建议

```typescript
// 请求拦截器：自动附加Token
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：自动刷新Token
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        });
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 十一、媒体下载服务（Media Download Service）

> 独立微服务，端口通常不同，API前缀可能为 `/api/v1/download`

### 11.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | POST | `/download/tasks` | 登录用户 | 创建下载任务 |
| 2 | GET | `/download/tasks` | 登录用户 | 获取下载任务列表（分页） |
| 3 | GET | `/download/tasks/{task_id}` | 登录用户 | 获取任务详情 |
| 4 | PUT | `/download/tasks/{task_id}` | 登录用户 | 更新任务 |
| 5 | DELETE | `/download/tasks/{task_id}` | 登录用户 | 删除任务 |
| 6 | POST | `/download/tasks/{task_id}/start` | 登录用户 | 启动下载 |
| 7 | POST | `/download/tasks/{task_id}/retry` | 登录用户 | 重试下载 |
| 8 | GET | `/download/tasks/{task_id}/failures` | 登录用户 | 获取任务失败记录 |
| 9 | GET | `/download/tasks/{task_id}/videos` | 登录用户 | 获取已下载视频 |
| 10 | POST | `/download/tasks/{task_id}/failures/{id}/retry` | 登录用户 | 重试特定失败 |
| 11 | POST | `/download/tasks/{task_id}/failures/{id}/abandon` | 登录用户 | 放弃特定失败 |
| 12 | GET | `/download/videos` | 登录用户 | 全部已下载视频列表 |
| 13 | GET | `/download/videos/{video_id}` | 登录用户 | 视频详情 |
| 14 | GET | `/download/failures` | 登录用户 | 全部失败记录列表 |
| 15 | POST | `/download/tasks/batch-import` | 登录用户 | CSV批量导入任务 |
| 16 | POST | `/download/tasks/crawl-and-import` | 登录用户 | 爬取并批量导入 |
| 17 | GET | `/download/tasks/crawl-import-status` | 登录用户 | 查询爬取导入状态 |

### 11.2 数据结构

```typescript
// 下载任务状态枚举
type TaskStatus = "pending" | "processing" | "completed" | "partial_completed" | "failed" | "cancelled";

// 资源类型枚举
type ResourceTypeEnum = "m3u8" | "ts" | "mp4" | "image";

// 失败类型枚举
type FailureTypeEnum = "network_error" | "timeout" | "invalid_content" | "storage_error" | "permission_error";

// 失败状态枚举
type FailureStatusEnum = "pending" | "retrying" | "abandoned";

interface DownloadTaskCreate {
  resource_url: string;      // 必填，资源URL
  resource_type: string;     // "m3u8" | "mp4" | "image"
  video_id?: string;         // 关联的视频ID
  liveroom_id?: string;      // 关联的直播间ID
}

interface DownloadTask {
  id: string;
  user_id: string;
  video_id?: string;
  liveroom_id?: string;
  resource_url: string;
  resource_type: string;
  status: TaskStatus;
  progress: number;          // 0-100
  total_segments?: number;   // 总分片数
  downloaded_segments?: number; // 已下载分片数
  failed_segments?: number;  // 失败分片数
  storage_path?: string;     // 存储路径
  created_at: string;
  updated_at: string;
}

interface DownloadFailure {
  id: string;
  task_id: string;
  resource_url: string;
  resource_type: string;
  failure_type: FailureTypeEnum;
  error_message: string;
  retry_count: number;
  status: FailureStatusEnum;
  created_at: string;
}

interface DownloadedVideo {
  id: string;                // video_id
  liveroom_id?: string;
  video_type?: string;
  video_url: string;
  storage_path: string;
  file_size?: number;
  duration?: number;
  resolution?: string;
  format?: string;
  status: string;
  created_at: string;
}

interface CrawlAndImportRequest {
  source_url: string;        // 要爬取的页面URL
  // 其他配置参数...
}
```

### 11.3 前端页面实现

#### 页面A：下载任务管理

**路由建议**: `/admin/downloads` 或 `/downloads`

**页面功能**:
- 任务列表（分页），支持按状态筛选
- 每行显示：资源URL、类型、状态（带进度条）、已下载/失败分片数、操作
- 操作：启动、重试、删除、查看详情
- 顶部：新建任务、批量导入、爬取导入

**API调用流程**:
```
1. 加载 → GET /download/tasks?page=1&page_size=20&status=processing
2. 新建 → POST /download/tasks
3. 启动 → POST /download/tasks/{id}/start
4. 重试 → POST /download/tasks/{id}/retry
5. 删除 → DELETE /download/tasks/{id}
6. 批量导入 → 上传CSV → POST /download/tasks/batch-import
7. 爬取导入 → POST /download/tasks/crawl-and-import
8. 轮询状态 → GET /download/tasks/crawl-import-status （每5秒）
```

**进度轮询**:
```typescript
// 处理中的任务自动轮询进度
const pollProgress = setInterval(async () => {
  const { data } = await axios.get(`/api/v1/download/tasks/${taskId}`);
  updateProgressBar(data.progress);
  if (['completed', 'failed', 'cancelled'].includes(data.status)) {
    clearInterval(pollProgress);
  }
}, 3000);
```

#### 页面B：已下载视频库

**路由建议**: `/downloads/videos`

**API调用**:
```
GET /download/videos?page=1&page_size=20
```

**功能**: 视频列表、查看详情、播放预览

#### 页面C：失败记录管理

**路由建议**: `/downloads/failures`

**API调用**:
```
1. 加载 → GET /download/failures?page=1&page_size=20
2. 重试 → POST /download/failures/{id}/retry
3. 放弃 → POST /download/failures/{id}/abandon
```

---

## 十二、直播间与公众号关联（Official Accounts）

### 12.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/admin/official-accounts` | Admin | 获取所有公众号列表 |
| 2 | POST | `/admin/official-accounts` | Admin | 创建公众号 |
| 3 | GET | `/admin/official-accounts/{id}` | Admin | 获取公众号详情 |
| 4 | PATCH | `/admin/official-accounts/{id}` | Admin | 更新公众号 |
| 5 | DELETE | `/admin/official-accounts/{id}` | Admin | 删除公众号 |
| 6 | GET | `/rooms/{room_id}/official-accounts` | 公开 | 获取直播间关联的公众号 |
| 7 | POST | `/admin/rooms/{room_id}/official-accounts` | Admin | 批量设置直播间公众号 |
| 8 | DELETE | `/admin/rooms/{room_id}/official-accounts/{id}` | Admin | 解除关联 |
| 9 | GET | `/official-accounts/{id}/rooms` | Admin | 获取公众号关联的直播间 |

### 12.2 数据结构

```typescript
interface OfficialAccount {
  id: string;
  name: string;           // 公众号名称
  app_id?: string;        // 微信AppID
  description?: string;
  qrcode_url?: string;    // 二维码图片URL
  is_active: boolean;
  created_at: string;
}

interface LiveRoomOfficialAccountsSetRequest {
  account_ids: string[];  // 公众号ID列表
}
```

### 12.3 前端页面实现

#### 页面A：公众号管理（管理端）

**路由建议**: `/admin/official-accounts`

**API调用流程**:
```
1. 加载 → GET /admin/official-accounts
2. 新增 → POST /admin/official-accounts
3. 编辑 → PATCH /admin/official-accounts/{id}
4. 删除 → DELETE /admin/official-accounts/{id}
```

#### 页面B：直播间公众号关联（管理端直播间编辑页内嵌）

**API调用流程**:
```
1. 加载 → GET /rooms/{room_id}/official-accounts
2. 加载全部公众号 → GET /admin/official-accounts
3. 设置关联 → POST /admin/rooms/{room_id}/official-accounts  body: { account_ids: [...] }
4. 解除关联 → DELETE /admin/rooms/{room_id}/official-accounts/{id}
```

---

## 十三、搜索功能（Search）

### 13.1 后端API清单

| # | 方法 | 路径 | 权限 | 用途 |
|---|------|------|------|------|
| 1 | GET | `/search` | 公开 | 全局搜索 |
| 2 | GET | `/search/hot-keywords` | 公开 | 热门搜索词 |
| 3 | GET | `/search/suggestions` | 公开 | 搜索建议/自动补全 |
| 4 | GET | `/search/recommendations` | 公开 | 推荐内容 |
| 5 | GET | `/users/me/search-history` | 登录用户 | 获取搜索历史 |
| 6 | DELETE | `/users/me/search-history/{id}` | 登录用户 | 删除单条搜索历史 |
| 7 | DELETE | `/users/me/search-history` | 登录用户 | 清空搜索历史 |

### 13.2 前端页面实现

#### 页面：搜索页

**路由建议**: `/search?q=关键词`

**页面功能**:
- 搜索输入框（顶部固定）
- 热门搜索词（无输入时展示）
- 搜索建议/自动补全（输入时实时展示）
- 搜索结果列表（直播间、专家、专题混合）
- 搜索历史（已登录用户）

**API调用流程**:
```
1. 页面加载 → GET /search/hot-keywords
2. 输入时 → GET /search/suggestions?q=关键词 （防抖300ms）
3. 回车搜索 → GET /search?q=关键词&page=1&page_size=20
4. 搜索历史 → GET /users/me/search-history
5. 删除历史 → DELETE /users/me/search-history/{id}
6. 清空历史 → DELETE /users/me/search-history
7. 推荐内容 → GET /search/recommendations
```

---

## 十四、异常处理统一规范

### 14.1 后端异常结构

后端定义了统一的业务异常类，前端需要根据HTTP状态码和响应体进行处理。

```typescript
// 后端统一错误响应格式
interface ApiError {
  detail: string;        // 错误描述信息
  // 可能还有 code、errors 等字段
}

// 常见业务异常及前端处理建议
const ERROR_HANDLERS: Record<string, (msg: string) => void> = {
  // 直播间相关
  "RoomNotFound": (msg) => showToast(msg || "直播间不存在"),
  "RoomAlreadyExists": (msg) => showToast(msg || "直播间已存在"),
  "RoomAccessDenied": (msg) => { showToast(msg); navigate("/"); },

  // 场次相关
  "SessionNotFound": (msg) => showToast(msg || "直播场次不存在"),
  "SessionConflict": (msg) => showToast(msg || "场次时间冲突"),

  // 标签相关
  "TagNotFound": (msg) => showToast(msg || "标签不存在"),
  "TagAlreadyExists": (msg) => showToast(msg || "标签名已存在"),

  // 专家相关
  "ExpertNotFound": (msg) => showToast(msg || "专家不存在"),
  "ExpertAlreadyFollowed": (msg) => showToast(msg || "已关注该专家"),

  // 品牌相关
  "BrandNotFound": (msg) => showToast(msg || "品牌不存在"),

  // 用户相关
  "InvalidToken": (msg) => { localStorage.clear(); navigate("/login"); },
  "InvalidCredentials": (msg) => showToast(msg || "用户名或密码错误"),
  "ValidationError": (msg) => showToast(msg || "输入校验失败"),
};
```

### 14.2 Axios全局错误处理建议

```typescript
axios.interceptors.response.use(
  response => response,
  error => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    switch (status) {
      case 400: showToast(detail || "请求参数错误"); break;
      case 401: // Token过期，已在上方拦截器处理
        break;
      case 403: showToast("无权限执行此操作"); break;
      case 404: showToast(detail || "资源不存在"); break;
      case 409: showToast(detail || "资源冲突"); break;
      case 422: showToast(detail || "输入校验失败"); break;
      case 500: showToast("服务器内部错误，请稍后重试"); break;
      default:  showToast("网络错误，请检查网络连接");
    }
    return Promise.reject(error);
  }
);
```

---

## 附录：前端技术栈建议

| 类别 | 推荐方案 |
|------|---------|
| 框架 | Vue 3 + TypeScript |
| UI库 | Element Plus 或 Ant Design Vue |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| HTTP | Axios |
| 图片上传 | 封装统一的 Upload 组件，支持 multipart/form-data |
| 富文本 | WangEditor 或 TinyMCE（Tab内容编辑） |
| 轮播图 | Swiper（焦点图） |
| 图标 | @element-plus/icons-vue 或 iconify |

---

## 附录：API服务端口规划

| 服务 | 默认端口 | API前缀 |
|------|---------|---------|
| live_core_service | 8000 | `/api/v1` |
| media_download_service | 8001 | `/api/v1` |
| users | 8002 | `/api/v1` |

前端开发环境可通过 Vite proxy 统一代理到各服务：
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/v1/download': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
      },
      '/api/v1/auth': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
      },
      '/api/v1/users': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
      },
    },
  },
});
```
