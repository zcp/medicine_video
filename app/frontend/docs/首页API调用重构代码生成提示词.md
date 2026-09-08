# 首页API调用重构代码生成提示词（Element Plus版）

## 角色与目标

你是一名资深前端重构工程师，**精通 Element Plus** 并对UI细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API请求、状态管理、数据处理）已经全部实现。

你的核心任务是**"API调用升级与首页重构"**，即根据我提供的最新后端设计文档（`@直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md`），将首页从旧的Mock数据和通用API升级为专用的首页API，实现真实的后端数据调用。**注意：这是对现有首页的升级改造，需要保持现有业务逻辑和UI风格**。

---

## 背景说明

### 当前实现状态
- **首页主组件**: `src/pages/app/tabbar/home/index.vue` - 使用旧API `getRoomList()`
- **首页子组件**:
  - `SearchBar.vue` - 搜索栏组件
  - `CategoryTabs.vue` - 分类筛选（**当前使用Mock数据**）
  - `FeaturedCarousel.vue` - 焦点图轮播（**当前使用Mock数据**）
  - `RoomCardGrid.vue` - 直播卡片网格
- **直播卡片组件**: `src/components/shared/RoomCard.vue` - 显示直播间卡片

### 升级目标
将首页升级为调用以下**三个真实API**：
1. **首页直播间列表API**: `GET /api/v1/homepage/rooms` - 替代旧的 `getRoomList()`
2. **焦点图轮播API**: `GET /api/v1/featured-content` - 替代Mock数据
3. **分类筛选API**: `GET /api/v1/categories` - 替代Mock数据

---

## API接口详细说明

### API 1: 首页直播间列表

**接口路径**: `GET /api/v1/homepage/rooms`

**认证要求**: 公开访问，无需JWT Token

**请求参数** (Query Parameters):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `page` | number | 否 | 1 | 页码 |
| `size` | number | 否 | 10 | 每页数量（**建议10-15条**，最大100）|
| `sort` | string | 否 | `heat:desc` | 排序规则：`heat:desc`（按热度降序）、`start_time:asc`（按开播时间升序）、`created_at:desc`（按创建时间降序） |
| `category_id` | string | 否 | - | 按分类ID筛选（UUID格式） |

**响应数据结构**:
```typescript
interface HomepageRoomsResponse {
  total: number;      // 总数
  page: number;       // 当前页码
  size: number;       // 每页数量
  items: HomepageRoomItem[];  // 直播间列表
}

interface HomepageRoomItem {
  id: string;                    // 直播间UUID
  title: string;                 // 直播间标题
  cover_url: string | null;      // 封面图URL
  summary: string | null;        // 直播间简介摘要
  live_status: 'live' | 'scheduled' | 'replay';  // 直播状态
  host: HomepageHost | null;     // 主讲人信息
  status_data: HomepageStatusData;  // 状态相关数据
  heat: number | null;           // 热度值（用于排序）
}

interface HomepageHost {
  expert_id: string | null;      // 专家ID（如果是专家）
  user_id: string | null;        // 用户ID（如果是普通用户）
  name: string;                  // 主讲人姓名
  title: string | null;          // 职称（如：主任医师、教授）
  hospital: string | null;       // 所在医院
}

interface HomepageStatusData {
  viewer_count: number | null;      // 当前观看人数（直播中时有值）
  start_time: string | null;        // 计划开始时间（预告时有值，ISO 8601格式）
  duration_seconds: number | null;  // 回放时长（秒）（回放时有值）
  play_count: number | null;        // 回放播放次数（回放时有值）
}
```

**重要说明**:
- **Host选择逻辑**（后端已处理）: 优先级为 `场次的featured_expert > 房主专家 > 房主用户`
- **live_status映射**: 
  - `live`: 正在直播，`status_data.viewer_count` 有值
  - `scheduled`: 预告/待开播，`status_data.start_time` 有值
  - `replay`: 回放，`status_data.duration_seconds` 和 `play_count` 有值
- **热度计算**（后端已处理）: `heat = current_viewer_count * 10 + peak_viewer_count * 5 + play_count`
- **性能优化建议**:
  - 推荐Tab（不传category_id）返回多科室热门直播间，建议每页10-15条
  - 使用上拉加载更多，避免一次性加载大量数据
  - 后端已做好热度排序和分页，前端直接使用即可

**前端调用示例**:
```typescript
import { getHomepageRooms } from '@/api/homepage';

// 获取第一页，按热度排序
const res = await getHomepageRooms({ 
  page: 1, 
  size: 10, 
  sort: 'heat:desc' 
});
const rooms = res.data.items;

// 按分类筛选
const res2 = await getHomepageRooms({ 
  page: 1, 
  size: 10, 
  category_id: '550e8400-e29b-41d4-a716-446655440001' 
});
```

---

### API 2: 焦点图轮播

**接口路径**: `GET /api/v1/featured-content`

**认证要求**: 公开访问，无需JWT Token

**请求参数**: 无

**响应数据结构**:
```typescript
interface FeaturedContent {
  id: string;                    // 焦点图UUID
  title: string;                 // 焦点图标题
  image_url: string;             // 焦点图图片URL
  target_type: string | null;    // 目标类型：'session'（跳转到场次）、'topic'（跳转到专题）、'external'（外部链接）
  target_id: string | null;      // 目标ID（当target_type为session/topic时使用）
  target_url: string | null;     // 外部链接URL（当target_type为external时使用）
  cta_text: string | null;       // 行动召唤文本（如"立即观看"、"了解详情"）
  sort_order: number;            // 排序权重，数字越小越靠前
}

// API返回: FeaturedContent[]（数组）
```

**重要说明**:
- **后端自动筛选**: 只返回 `is_active=true` 且在有效时间范围内的焦点图
- **排序规则**: 后端已按 `sort_order ASC` 排序，前端直接使用即可
- **跳转逻辑**: 
  - `target_type === 'session'`: 跳转到 `/pages/app/live/LiveView?session_id={target_id}`
  - `target_type === 'topic'`: 跳转到 `/pages/h5/topic/TopicDisplay?topic_id={target_id}`
  - `target_type === 'external'`: 使用 `target_url` 跳转（需处理内部/外部链接）

**前端调用示例**:
```typescript
import { getFeaturedContent } from '@/api/featured';

const res = await getFeaturedContent();
const banners = res.data;  // 注意：直接是数组，不是分页结构
```

---

### API 3: 分类筛选

**接口路径**: `GET /api/v1/categories`

**认证要求**: 公开访问，无需JWT Token

**请求参数**: ~~无~~ **（注意：当前前端API封装有QueryParams参数，需优化移除）**

**响应数据结构**:
```typescript
interface Category {
  id: string;                    // 分类UUID
  name: string;                  // 分类名称（如：肝胆外科、胃肠外科）
  slug: string | null;           // URL友好的标识符
  icon: string | null;           // 分类图标名称或URL
  description: string | null;    // 分类描述
  sort_order: number;            // 排序权重，数字越小越靠前
  is_active: boolean;            // 是否启用（前端只会收到true的数据）
  created_at: string;            // 创建时间（ISO 8601格式）
  updated_at: string;            // 更新时间（ISO 8601格式）
}

// API返回: Category[]（数组）
```

**重要说明**:
- **后端自动筛选**: 只返回 `is_active=true` 的分类
- **排序规则**: 后端已按 `sort_order ASC` 排序，前端直接使用即可
- **⚠️ API封装优化**: 当前 `src/api/category.ts` 的 `getCategories()` 函数接受 `QueryParams` 参数，但后端API不支持，需移除此参数

**前端调用示例**:
```typescript
import { getCategories } from '@/api/category';

const res = await getCategories();
const categories = res.data;  // 注意：直接是数组，不是分页结构
```

---

## 核心原则

1. **[最高准则] UI组件库**: **所有UI元素必须使用 Element Plus 组件库进行构建**。禁止使用原生的HTML标签（如 `<table>`, `<button>`）来模拟复杂组件。
2. **逻辑复用，视图替换**: 保留现有的业务逻辑和UI结构，只升级API调用部分。
3. **保持UI风格**: 首页现有的UI风格、布局、动画效果必须完全保留。
4. **数据适配**: 将旧数据结构适配到新的首页API数据结构。

---

## 任务一：优化API封装与类型定义

### 1.1 优化分类API封装

**文件路径**: `src/api/category.ts`

**优化内容**: 移除 `getCategories()` 函数的 `QueryParams` 参数，因为后端API不支持查询参数。

**修改前**:
```typescript
export const getCategories = (params: QueryParams = {}): Promise<ApiResponse<Category[]>> => {
  return get<ApiResponse<Category[]>>('/categories', params);
};
```

**修改后**:
```typescript
/**
 * 获取分类列表（公开接口）
 * @description GET /api/v1/categories - 无需认证，后端自动筛选is_active=true的分类
 * @returns Promise<ApiResponse<Category[]>>
 * @example
 * const response = await getCategories();
 * const categories = response.data;  // 直接是数组
 */
export const getCategories = (): Promise<ApiResponse<Category[]>> => {
  return get<ApiResponse<Category[]>>('/categories');
};
```

### 1.2 确认焦点图类型定义（已修复）

**文件路径**: `src/types/featured.ts`

**确认内容**: `FeaturedContent` 接口已包含 `cta_text` 字段，并移除了多余字段（`subtitle`, `is_active`, `start_at`, `end_at`, `created_at`, `updated_at`）。

**当前正确定义**:
```typescript
export interface FeaturedContent {
  id: string;
  title: string;
  image_url: string;
  target_type: string | null;
  target_id: string | null;
  target_url: string | null;
  cta_text: string | null;       // ✅ 已添加
  sort_order: number;
}
```

### 1.3 确认首页类型定义（已正确）

**文件路径**: `src/types/homepage.ts`

**确认内容**: 所有类型定义与后端Schema完全匹配，无需修改。

---

## 任务二：升级首页主组件

**文件路径**: `src/pages/app/tabbar/home/index.vue`

### 2.1 页面布局 (`<template>`)

保持现有的布局结构不变：
1. **顶部搜索栏**: `<SearchBar />` 组件
2. **分类筛选**: `<CategoryTabs />` 组件（需升级数据源）
3. **焦点图轮播**: `<FeaturedCarousel />` 组件（需升级数据源）
4. **直播卡片网格**: `<RoomCardGrid />` 组件（需升级数据源和卡片组件）

### 2.2 逻辑绑定 (`<script setup>`)

**需要修改的部分**:

1. **API导入**: 将旧的 `getRoomList` 改为 `getHomepageRooms`
```typescript
// 修改前
import { getRoomList } from '@/api/room';

// 修改后
import { getHomepageRooms } from '@/api/homepage';
```

2. **数据获取**: 将 `getRoomList()` 调用改为 `getHomepageRooms()`
```typescript
// 修改前
const loadRooms = async () => {
  const res = await getRoomList({ page: 1, size: 10 });
  // ...
};

// 修改后
const loadRooms = async () => {
  const res = await getHomepageRooms({ 
    page: 1, 
    size: 10, 
    sort: 'heat:desc' 
  });
  // ...
};
```

3. **分类筛选逻辑**: 添加 `category_id` 参数支持
```typescript
// 新增分类筛选处理
const handleCategoryChange = (categoryId: string | null) => {
  loadRooms({ category_id: categoryId });
};
```

4. **数据传递**: 将 `HomepageRoomItem[]` 传递给 `<RoomCardGrid>` 组件

---

## 任务三：升级分类筛选组件

**文件路径**: `src/pages/app/tabbar/home/components/CategoryTabs.vue`

### 3.1 数据源升级

**修改前**: 使用本地Mock数据
```typescript
const categories = ref([
  { id: '1', name: '全部' },
  { id: '2', name: '肝胆外科' },
  // ...
]);
```

**修改后**: 调用真实API（参考设计文档V1.3的分类筛选器设计）
```typescript
import { getCategories } from '@/api/category';
import type { Category } from '@/types/category';

const categories = ref<Category[]>([]);
const displayCategories = ref<Category[]>([]);  // 显示在Tab栏的分类（推荐+星标+热门前几个）

const loadCategories = async () => {
  try {
    const res = await getCategories();
    categories.value = res.data;  // 全部分类
    
    // 显示在Tab栏的分类（参考设计文档）
    // 1. "推荐" Tab（固定第一位，id为null）
    //    - id为null时，调用首页API不传category_id参数
    //    - 后端返回多科室的热度推荐内容（跨科室的热门直播间）
    //    - 这是默认首页，用户每次打开App都停留在此Tab
    // 2. 用户星标的科室（最多5个，从本地存储获取，可通过≡图标页面编辑）
    // 3. 平台热门科室（取前几个，补充显示）
    displayCategories.value = [
      { id: null, name: '推荐', slug: 'recommended', ... },  // 推荐Tab（id必须为null）
      // ...用户星标的科室（从LocalStorage获取）
      // ...热门科室（取前几个）
    ];
  } catch (error) {
    console.error('[分类加载失败]', error);
    uni.showToast({ title: '获取分类列表失败', icon: 'none' });
  }
};

onMounted(() => {
  loadCategories();
});
```

**重要设计说明**（参考移动端设计文档V1.3）:
- **"推荐"Tab（固定第一位）**：
  - 功能：显示跨科室的热门推荐直播间（包含多个科室的高热度内容）
  - 实现：id为null，调用API时不传category_id参数，后端返回推荐内容
  - 特点：默认首页，用户每次打开App都停留在此Tab
  
- **"全部科室"页面（≡图标进入）**：
  - 功能：管理所有科室、搜索科室、编辑星标科室（最多5个）
  - 实现：点击筛选栏右侧≡图标，跳转到独立的全部科室管理页面
  - 特点：可以搜索科室并点击，点击后首页显示该科室的直播间；可以编辑星标科室，固定在Tab栏前面
  
- **区别总结**：
  - 推荐Tab = 多科室混合的热门内容（默认首页）
  - 全部科室 = 科室管理页面（搜索、查看、编辑星标）
  
- **Tab栏布局示例**：`[推荐] [⭐眼科] [⭐胃肠外科] [肝胆胰] [心血管] ... [≡]`
  - 第1位固定：推荐（id=null）
  - 第2-6位：用户星标的科室（最多5个，可通过≡页面编辑）
  - 第7位起：平台热门科室（补充显示）
  - 最右侧：≡图标（进入全部科室管理页面）

### 3.2 事件处理

**保持现有事件**: `emit('change', categoryId)`，父组件接收后调用首页API时传入 `category_id` 参数。

---

## 任务四：升级焦点图轮播组件

**文件路径**: `src/pages/app/tabbar/home/components/FeaturedCarousel.vue`

### 4.1 数据源升级

**修改前**: 使用本地Mock数据
```typescript
const banners = ref([
  { id: '1', title: '精彩直播1', image: '...' },
  // ...
]);
```

**修改后**: 调用真实API
```typescript
import { getFeaturedContent } from '@/api/featured';
import type { FeaturedContent } from '@/types/featured';

const banners = ref<FeaturedContent[]>([]);

const loadBanners = async () => {
  try {
    const res = await getFeaturedContent();
    banners.value = res.data;  // 直接是数组
  } catch (error) {
    console.error('[焦点图加载失败]', error);
    uni.showToast({ title: '获取焦点图失败', icon: 'none' });
  }
};

onMounted(() => {
  loadBanners();
});
```

### 4.2 轮播图渲染

**使用 Element Plus 轮播图组件**:
```vue
<el-carousel height="200px" indicator-position="outside">
  <el-carousel-item v-for="banner in banners" :key="banner.id">
    <div class="banner-item" @click="handleBannerClick(banner)">
      <el-image 
        :src="banner.image_url" 
        fit="cover"
        style="width: 100%; height: 200px;"
      />
      <div class="banner-overlay">
        <div class="banner-title">{{ banner.title }}</div>
        <el-button 
          v-if="banner.cta_text" 
          type="primary" 
          size="small"
        >
          {{ banner.cta_text }}
        </el-button>
      </div>
    </div>
  </el-carousel-item>
</el-carousel>
```

### 4.3 跳转逻辑（含XSS安全防护）

**实现焦点图点击跳转**:
```typescript
/**
 * 验证UUID格式
 * @param id - 待验证的UUID字符串
 * @returns 是否为有效UUID
 */
const isValidUUID = (id: string | null): boolean => {
  if (!id) return false;
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidPattern.test(id);
};

/**
 * 验证URL安全性（防止XSS攻击）
 * @param url - 待验证的URL
 * @returns 是否安全
 */
const isUrlSafe = (url: string): boolean => {
  if (!url) return false;
  
  // 禁止危险协议
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'blob:'];
  const lowerUrl = url.toLowerCase().trim();
  
  for (const protocol of dangerousProtocols) {
    if (lowerUrl.startsWith(protocol)) {
      console.error('[安全风险] 检测到危险URL协议:', url);
      return false;
    }
  }
  
  return true;
};

const handleBannerClick = (banner: FeaturedContent) => {
  if (!banner.target_type) return;

  try {
    if (banner.target_type === 'session') {
      // 验证session_id的UUID格式
      if (!isValidUUID(banner.target_id)) {
        console.error('[安全风险] 无效的session_id格式:', banner.target_id);
        uni.showToast({ title: '链接格式错误', icon: 'none' });
        return;
      }
      // 跳转到直播播放页
      uni.navigateTo({
        url: `/pages/app/live/LiveView?session_id=${banner.target_id}`
      });
    } else if (banner.target_type === 'topic') {
      // 验证topic_id的UUID格式
      if (!isValidUUID(banner.target_id)) {
        console.error('[安全风险] 无效的topic_id格式:', banner.target_id);
        uni.showToast({ title: '链接格式错误', icon: 'none' });
        return;
      }
      // 跳转到专题展示页
      uni.navigateTo({
        url: `/pages/h5/topic/TopicDisplay?topic_id=${banner.target_id}`
      });
    } else if (banner.target_type === 'external' && banner.target_url) {
      // 外部链接处理 - 必须先验证安全性
      if (!isUrlSafe(banner.target_url)) {
        uni.showToast({ title: '链接不安全，无法跳转', icon: 'none' });
        return;
      }
      
      if (banner.target_url.startsWith('http://') || banner.target_url.startsWith('https://')) {
        // 外部链接，使用webview打开
        uni.navigateTo({
          url: `/pages/shared/webview/index?url=${encodeURIComponent(banner.target_url)}`
        });
      } else if (banner.target_url.startsWith('/')) {
        // 内部路径，直接跳转
        uni.navigateTo({
          url: banner.target_url
        });
      } else {
        console.error('[跳转错误] 无效的URL格式:', banner.target_url);
        uni.showToast({ title: '链接格式错误', icon: 'none' });
      }
    }
  } catch (error) {
    console.error('[跳转异常]', error);
    uni.showToast({ title: '跳转失败，请稍后重试', icon: 'none' });
  }
};
```

**安全说明**:
- ✅ 禁止 `javascript:`、`data:`、`vbscript:` 等恶意协议
- ✅ 使用 `try-catch` 捕获异常，防止跳转失败导致应用崩溃
- ✅ 只允许 `http://`、`https://` 或以 `/` 开头的内部路径
- ✅ 使用 `encodeURIComponent` 编码URL参数，防止注入攻击
```

---

## 任务五：升级直播卡片组件

**文件路径**: `src/components/shared/RoomCard.vue`

### 5.1 Props类型升级

**修改前**: 接受通用的 `LiveRoom` 类型
```typescript
interface Props {
  room: LiveRoom;
}
```

**修改后**: 接受首页专用的 `HomepageRoomItem` 类型
```typescript
import type { HomepageRoomItem } from '@/types/homepage';

interface Props {
  room: HomepageRoomItem;
}
```

### 5.2 卡片布局设计（参考Bilibili风格）

**布局结构**（完全参考Bilibili移动端视频卡片）:
```
┌─────────────────────────────────┐
│  [封面图 180px高]               │
│  [直播中]              ← 左上角  │  ← 状态角标（覆盖在封面上）
│                                 │
│  🔥 8.5K  👁 1.2K  ← 左下角     │  ← 底部统计（覆盖在封面上，带半透明背景）
├─────────────────────────────────┤
│  肝胆胰外科手术直播演示           │  ← 标题（最多2行）
├─────────────────────────────────┤
│  👤 李四 教授 · 主任医师         │  ← 第1行：头像+姓名+职称
│     XX 医院                      │  ← 第2行：医院（缩进对齐）
└─────────────────────────────────┘
```

**完整代码实现**:
```vue
<script setup lang="ts">
import { ref } from 'vue';
import type { HomepageRoomItem, HomepageHost } from '@/types/homepage';

// 卡片点击态
const isPressing = ref(false);

// ... 其他代码
</script>

<template>
  <el-card 
    class="room-card" 
    :class="{ 'card-pressing': isPressing }"
    @touchstart="isPressing = true" 
    @touchend="isPressing = false"
    @touchcancel="isPressing = false"  
    @click="handleCardClick"
  >
    <!-- 封面图区域（相对定位，容纳绝对定位的子元素） -->
    <div class="cover-wrapper">
      <el-image 
        :src="room.cover_url || defaultCover" 
        fit="cover"
        style="width: 100%; height: 180px;"
      />
      
      <!-- 状态角标（左上角，绝对定位） -->
      <div 
        class="status-tag" 
        :class="`status-${room.live_status}`"
      >
        {{ getStatusText(room.live_status) }}
      </div>

      <!-- 底部统计信息（左下角，绝对定位，带半透明背景） -->
      <div class="cover-stats">
        <!-- 热度（如果有值） -->
        <span v-if="room.heat" class="stat-item">
          🔥 {{ formatNumber(room.heat) }}
        </span>

        <!-- 根据live_status显示不同的统计信息 -->
        <template v-if="room.live_status === 'live'">
          <span class="stat-item">
            👁 {{ formatNumber(room.status_data.viewer_count) }}人在看
          </span>
        </template>
        
        <!-- 预告状态暂不显示时间信息 -->
        
        <template v-else-if="room.live_status === 'replay'">
          <span class="stat-item">
            ▶️ {{ formatNumber(room.status_data.play_count) }}次播放
          </span>
          <span class="stat-item">
            ⏱ {{ formatDuration(room.status_data.duration_seconds) }}
          </span>
        </template>
      </div>
    </div>

    <!-- 直播间信息区域 -->
    <div class="room-info">
      <!-- 标题（最多2行） -->
      <el-tooltip :content="room.title" placement="top">
        <div class="room-title">{{ room.title }}</div>
      </el-tooltip>

      <!-- 主讲人信息（参考Bilibili UP主卡片） -->
      <div v-if="room.host" class="host-info">
        <!-- 头像（左侧） -->
        <el-avatar 
          :size="32" 
          :src="getHostAvatar(room.host)"
          class="host-avatar"
        />
        
        <!-- 文字信息（右侧，两行） -->
        <div class="host-text">
          <!-- 第1行：姓名 + 职称 -->
          <div class="host-line1">
            {{ room.host.name }}
            <template v-if="room.host.title">
              · {{ room.host.title }}
            </template>
          </div>
          
          <!-- 第2行：医院 -->
          <div v-if="room.host.hospital" class="host-line2">
            {{ room.host.hospital }}
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
/* 注意：uni-app移动端样式兼容性 */
.room-card {
  /* 移除cursor:pointer（移动端无意义） */
  transition: transform 0.2s, opacity 0.2s;
  
  /* uni-app中:active兼容性不佳，改为动态class */
  &.card-pressing {
    transform: scale(0.98);  /* 点击时轻微缩小 */
    opacity: 0.9;  /* 点击时轻微透明 */
  }
}

.cover-wrapper {
  position: relative;  /* 关键：让子元素可以绝对定位 */
  width: 100%;
  height: 180px;
  overflow: hidden;
  border-radius: 8px 8px 0 0;
}

/* 状态角标（左上角） */
.status-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 6px;
  font-size: 11px;
  border-radius: 4px;
  color: #fff;
  font-weight: 500;
  z-index: 2;
  
  &.status-live {
    background-color: #ff4d4f;
    animation: breathe 2s infinite;  /* 呼吸灯动画 */
  }
  
  &.status-scheduled {
    background-color: #1890ff;
  }
  
  &.status-replay {
    background-color: #8c8c8c;
  }
}

@keyframes breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 底部统计信息（左下角，覆盖在封面上） */
.cover-stats {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 8px;
  /* 小程序中linear-gradient兼容性差，改为纯色半透明 */
  background: rgba(0, 0, 0, 0.6);  /* 纯色半透明背景 */
  font-size: 11px;
  color: #fff;
  z-index: 2;
  
  .stat-item {
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
  }
}

/* 直播间信息区域 */
.room-info {
  padding: 8px 12px 12px;
}

/* 标题样式 */
.room-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  line-height: 1.4;
  margin-bottom: 8px;
  
  /* 最多显示2行，超出省略 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 主讲人信息区域（参考Bilibili UP主样式） */
.host-info {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  
  .host-avatar {
    flex-shrink: 0;
  }
  
  .host-text {
    flex: 1;
    min-width: 0;  /* 允许文字省略 */
  }
  
  .host-line1 {
    font-size: 12px;
    color: #595959;
    line-height: 1.4;
    
    /* 最多1行，超出省略 */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .host-line2 {
    font-size: 11px;
    color: #8c8c8c;
    line-height: 1.4;
    margin-top: 2px;
    
    /* 最多1行，超出省略 */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
```

### 5.3 卡片点击跳转逻辑

**跳转规则**:
- **所有状态**（`live`/`scheduled`/`replay`）: 统一跳转到播放页 `/pages/app/live/LiveView?roomId=${room.id}`
- **LiveView页面职责**: 根据房间当前状态自动处理：
  - 有roomId时，会自动查询房间的当前活跃session（live > scheduled > replay）
  - 直播中：显示直播流
  - 预告：显示倒计时和预告信息
  - 回放：显示回放列表

**实现说明**:
```typescript
// 卡片点击事件处理
const handleCardClick = () => {
  // 直接使用房间ID跳转，LiveView页面会根据roomId自动查询当前活跃session
  // 参数名使用roomId（首字母小写），与LiveView页面的options.roomId保持一致
  uni.navigateTo({
    url: `/pages/app/live/LiveView?roomId=${room.id}`
  });
};
```

**重要说明**:
- ✅ 首页API返回的 `room.id` 就是房间UUID，可以直接用于跳转
- ✅ LiveView页面会根据room_id查询房间当前的活跃场次，自动处理不同状态
- ✅ LiveView调用`GET /api/v1/sessions/{session_id}`获取场次详情，**后端返回`playback_url`字段**
- ✅ `playback_url`包含直播流或回放视频的播放地址（HLS/RTMP格式）
- ✅ 这样设计避免了前端需要额外调用API获取session_id和播放地址的复杂度

### 5.4 工具函数

**新增数据格式化函数**:
```typescript
import dayjs from 'dayjs';

// 格式化数字（如：1250 -> 1.2K）
const formatNumber = (num: number | null): string => {
  if (!num) return '0';
  if (num >= 10000) return (num / 10000).toFixed(1) + 'W';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};

// 注意：首页直播卡片暂时不需要显示日期，移除formatScheduleTime函数

// 格式化回放时长（秒 -> HH:mm:ss 或 mm:ss）
const formatDuration = (seconds: number | null): string => {
  if (!seconds) return '00:00';
  
  // 确保seconds是整数，防止后端返回小数导致显示错误
  const totalSeconds = Math.floor(seconds);
  
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs = Math.floor(totalSeconds % 60);  // 添加Math.floor防止小数
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};

// 获取状态类型
const getStatusType = (status: string): string => {
  const map = {
    live: 'danger',
    scheduled: 'warning',
    replay: 'info'
  };
  return map[status] || 'info';
};

// 获取状态文本
const getStatusText = (status: string): string => {
  const map = {
    live: '直播中',
    scheduled: '预告',
    replay: '回放'
  };
  return map[status] || '未知';
};

// 获取主讲人头像（后端暂未实现avatar_url字段，使用Mock头像）
const getHostAvatar = (host: HomepageHost): string => {
  // 暂时使用mock医生头像图片
  // 路径：项目中已有的mock头像资源 /static/医生头像mock.jpg
  // 注意：这是新增功能，当前首页卡片未显示医生信息
  // TODO: 等待后端HomepageHost添加avatar_url字段后替换为真实头像
  return '/static/医生头像mock.jpg';
};

// 注意：需要确保该图片资源存在于 /static/images/ 目录下
```

---

## 任务六：数据流与状态管理

### 6.1 数据加载流程

1. **页面初始化**: 
   - 并行加载：分类列表、焦点图、首页直播间列表（第一页）
   - 默认显示"推荐"Tab（id=null，不传category_id参数）
   
2. **分类筛选**: 
   - 用户点击分类Tab → 传递对应的 `category_id`（推荐Tab传undefined） → 重置页码为1 → 重新加载直播间列表
   - 示例：点击"推荐" → category_id=undefined；点击"肝胆外科" → category_id='uuid_123'
   
3. **上拉加载更多**（移动端无限滚动模式）: 
   - 用户上滑到底部 → 触发`@scrolltolower`事件 → 调用`loadMore()`函数
   - 自动加载下一页：`page` 参数+1 → 追加到列表
   - 直到当前Tab下的直播间全部加载完毕（`hasMore` 为 `false`）
   - **注意**：这是移动端标准的无限滚动模式，不是传统的点击"下一页"分页

### 6.2 错误处理

**分级错误处理机制**（uni-app版本）:
```typescript
/**
 * 统一的API错误处理（uni-app专用）
 * @param error - 错误对象
 * @param context - 错误上下文（如"加载焦点图"）
 */
const handleApiError = (error: any, context: string) => {
  console.error(`[${context}失败]`, error);
  
  // 根据错误类型显示不同提示
  if (error.response) {
    const status = error.response.status;
    
    switch (status) {
      case 401:
        uni.showToast({ title: '登录已过期，请重新登录', icon: 'none', duration: 2000 });
        // 可选：跳转到登录页
        // setTimeout(() => {
        //   uni.navigateTo({ url: '/pages/auth/login' });
        // }, 2000);
        break;
      
      case 403:
        uni.showToast({ title: '您没有访问权限', icon: 'none' });
        break;
      
      case 404:
        uni.showToast({ title: `${context}：内容不存在`, icon: 'none' });
        break;
      
      case 429:
        uni.showToast({ title: '操作过于频繁，请稍后重试', icon: 'none' });
        break;
      
      case 500:
      case 502:
      case 503:
        uni.showToast({ title: `${context}：服务异常，请稍后重试`, icon: 'none' });
        break;
      
      default:
        uni.showToast({ title: `${context}失败，请稍后重试`, icon: 'none' });
    }
  } else if (error.errMsg) {
    // uni-app特有的错误格式
    if (error.errMsg.includes('timeout')) {
      uni.showToast({ title: '请求超时，请检查网络', icon: 'none' });
    } else if (error.errMsg.includes('fail')) {
      uni.showToast({ title: '网络连接失败，请检查网络', icon: 'none' });
    } else {
      uni.showToast({ title: `${context}失败`, icon: 'none' });
    }
  } else {
    // 其他错误
    uni.showToast({ title: `${context}失败`, icon: 'none' });
  }
};

// 使用示例
try {
  const res = await getHomepageRooms({ page: 1 });
  rooms.value = res.data.items;
} catch (error) {
  handleApiError(error, '加载直播间列表');
}
```

**错误处理要点**:
- ✅ 区分不同HTTP状态码，提供针对性提示
- ✅ 网络错误单独处理
- ✅ 记录详细日志便于排查问题
- ✅ 用户友好的错误提示

### 6.3 数据加载状态管理

**完整的加载状态实现**:
```vue
<template>
  <view class="homepage">
    <!-- 焦点图轮播 -->
    <el-skeleton v-if="bannersLoading" :rows="2" animated />
    <FeaturedCarousel v-else :banners="banners" />
    
    <!-- 分类筛选 -->
    <el-skeleton v-if="categoriesLoading" :rows="1" animated />
    <CategoryTabs v-else :categories="displayCategories" @change="handleCategoryChange" />
    
    <!-- 直播间列表 -->
    <el-skeleton v-if="roomsLoading && rooms.length === 0" :rows="5" animated />
    <RoomCardGrid v-else :rooms="rooms" />
    
    <!-- 分页加载指示器 -->
    <view v-if="roomsLoading && rooms.length > 0" class="loading-more">
      <el-loading />
      <text>加载中...</text>
    </view>
    
    <!-- 无更多数据提示 -->
    <view v-if="!hasMore && rooms.length > 0" class="no-more">
      没有更多了~
    </view>
    
    <!-- 空状态 -->
    <el-empty v-if="!roomsLoading && rooms.length === 0" description="暂无直播内容" />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';

// 数据状态
const banners = ref<FeaturedContent[]>([]);
const categories = ref<Category[]>([]);
const displayCategories = ref<Category[]>([]);
const rooms = ref<HomepageRoomItem[]>([]);

// 加载状态
const bannersLoading = ref(false);
const categoriesLoading = ref(false);
const roomsLoading = ref(false);

// 分页状态
const currentPage = ref(1);
const pageSize = ref(15);  // 建议10-15条，优化首次加载性能
const totalCount = ref(0);
const hasMore = computed(() => rooms.value.length < totalCount.value);

// 筛选状态
const currentCategoryId = ref<string | null>(null);

// 加载焦点图
const loadBanners = async () => {
  bannersLoading.value = true;
  try {
    const res = await getFeaturedContent();
    banners.value = res.data;
  } catch (error) {
    console.error('[焦点图加载失败]', error);
    ElMessage.error('焦点图加载失败');
  } finally {
    bannersLoading.value = false;
  }
};

// 加载分类列表
const loadCategories = async () => {
  categoriesLoading.value = true;
  try {
    const res = await getCategories();
    categories.value = res.data;
    
    // 构建显示在Tab栏的分类
    displayCategories.value = [
      { id: '', name: '推荐', slug: 'recommended', ... },
      // TODO: 从LocalStorage获取用户星标的科室
      // TODO: 取前几个热门科室
    ];
  } catch (error) {
    console.error('[分类加载失败]', error);
    ElMessage.error('分类加载失败');
  } finally {
    categoriesLoading.value = false;
  }
};

// 加载直播间列表
const loadRooms = async (append = false) => {
  roomsLoading.value = true;
  try {
    const res = await getHomepageRooms({
      page: currentPage.value,
      size: pageSize.value,
      sort: 'heat:desc',
      category_id: currentCategoryId.value || undefined
    });
    
    if (append) {
      // 追加模式（分页加载）
      rooms.value.push(...res.data.items);
    } else {
      // 覆盖模式（首次加载或筛选）
      rooms.value = res.data.items;
    }
    
    totalCount.value = res.data.total;
  } catch (error) {
    console.error('[直播间列表加载失败]', error);
    ElMessage.error('直播间列表加载失败，请稍后重试');
  } finally {
    roomsLoading.value = false;
  }
};

// 分类切换处理
const handleCategoryChange = (categoryId: string | null) => {
  currentCategoryId.value = categoryId;
  currentPage.value = 1;  // 重置页码
  loadRooms(false);  // 重新加载列表（覆盖模式）
  
  // 说明：
  // - categoryId=null 时：调用API不传category_id参数，后端返回多科室推荐内容
  // - categoryId='uuid_123' 时：调用API传category_id='uuid_123'，后端返回该科室的直播间
};

// 加载更多（上拉加载，移动端无限滚动）
const loadMore = async () => {
  if (!hasMore.value || roomsLoading.value) return;
  
  currentPage.value += 1;
  await loadRooms(true);  // 追加模式
};

// 滚动到底部触发（需要在scroll-view上绑定@scrolltolower事件）
// <scroll-view @scrolltolower="loadMore">...</scroll-view>

// 页面初始化
onMounted(() => {
  // 独立加载各个模块，即使部分失败也不影响其他内容显示
  // 注意：不使用Promise.all([loadBanners(), loadCategories(), loadRooms()])，
  // 因为Promise.all会在任一失败时全部阻塞，导致整个首页无法加载
  loadBanners();      // 焦点图加载失败不影响列表
  loadCategories();   // 分类加载失败不影响列表
  loadRooms(false);   // 列表加载失败不影响焦点图和分类
});
</script>
```

**状态管理要点**:
- ✅ 三个独立的loading状态：`bannersLoading`、`categoriesLoading`、`roomsLoading`
- ✅ 分页状态：`currentPage`、`pageSize`、`totalCount`、`hasMore`
- ✅ 筛选状态：`currentCategoryId`
- ✅ 加载模式：`append`参数区分覆盖/追加模式
- ✅ 空状态处理：使用 `<el-empty>` 组件

---

## 关键实现要点

### 1. API调用一致性
- ✅ **首页直播间列表**: 使用 `getHomepageRooms()` 替代 `getRoomList()`
- ✅ **焦点图**: 调用 `getFeaturedContent()`，返回直接是数组
- ✅ **分类**: 调用 `getCategories()`，返回直接是数组，需优化移除 `QueryParams` 参数

### 2. 类型定义一致性
- ✅ **FeaturedContent**: 已包含 `cta_text` 字段，已移除多余字段
- ✅ **HomepageRoomItem**: 包含 `host`、`status_data`、`heat` 字段
- ✅ **Category**: 包含 `sort_order`、`is_active` 字段

### 3. UI组件要求
- 使用 Element Plus 的 `<el-carousel>`、`<el-card>`、`<el-tag>`、`<el-avatar>`、`<el-skeleton>` 等组件
- 保持现有的首页布局和UI风格
- 确保响应式设计和移动端适配

### 4. 数据适配
- **Host信息**: 优先显示专家信息，其次显示用户信息
- **状态数据**: 根据 `live_status` 显示不同的统计数据
- **时间格式化**: 使用 `dayjs` 格式化时间
- **数字格式化**: 大数字使用K/W单位

### 5. 交互逻辑
- **分类筛选**: 点击分类后重新加载列表，传入 `category_id` 参数
- **焦点图跳转**: 根据 `target_type` 跳转到不同页面
- **卡片点击**: 跳转到直播播放页（传递 `room_id` 或 `session_id`）

---

## 测试验证清单

### 功能测试
- [ ] 首页直播间列表正确加载（包含host、status_data、heat字段）
- [ ] 首页每页加载10-15条数据（性能优化）
- [ ] "推荐"Tab正常工作（不传category_id，显示多科室推荐内容）
- [ ] 分类筛选正常工作（点击分类后列表更新，传递正确的category_id）
- [ ] 右侧菜单图标（≡）正确显示，点击进入全部科室页面
- [ ] 焦点图轮播正常显示（包含cta_text按钮）
- [ ] 焦点图点击跳转正确（session/topic/external三种类型）
- [ ] 焦点图外部链接XSS防护正常工作（拒绝javascript:等恶意协议，验证UUID格式）
- [ ] 直播卡片显示完整信息（封面、标题、主讲人mock头像、统计数据）
- [ ] 卡片点击跳转到播放页（使用roomId参数，所有状态统一跳转）
- [ ] 播放页面正确加载（接收roomId，查询session，获取playback_url）
- [ ] **视频播放功能正常**（直播中可观看直播流，回放可观看回放视频）
- [ ] 卡片点击视觉反馈正常（点击时轻微缩小+透明）
- [ ] 上拉加载更多功能正常（滚动到底部自动加载下一页）
- [ ] 加载状态正确显示（骨架屏/加载指示器/无更多提示）
- [ ] 错误提示使用uni.showToast，显示正确
- [ ] 样式在小程序中正常显示（无渐变背景问题）

### 数据验证
- [ ] API返回数据结构符合类型定义
- [ ] Host信息优先级正确（featured_expert > 房主专家 > 房主用户）
- [ ] 状态数据根据live_status正确显示
- [ ] 时间格式化正确（ISO 8601 -> MM-DD HH:mm）
- [ ] 数字格式化正确（1250 -> 1.2K）

### 边界情况
- [ ] 无焦点图时的处理（不显示轮播图）
- [ ] 无分类时的处理（只显示"全部"选项）
- [ ] 无直播间时的处理（显示空状态）
- [ ] API失败时的错误提示
- [ ] 加载状态的骨架屏显示

### 性能测试
- [ ] 首页加载速度（三个API并行请求）
- [ ] 分页加载流畅度
- [ ] 图片懒加载正常工作

---

## 执行建议

1. **先优化API封装**（15分钟）:
   - 修复 `src/api/category.ts` 的 `getCategories()` 函数
   - 确认 `src/types/featured.ts` 的 `FeaturedContent` 接口

2. **升级分类筛选组件**（30分钟）:
   - 替换Mock数据为真实API调用
   - 测试分类筛选功能

3. **升级焦点图轮播组件**（45分钟）:
   - 替换Mock数据为真实API调用
   - 实现跳转逻辑（三种target_type）
   - 测试轮播图点击跳转

4. **升级首页主组件**（30分钟）:
   - 替换 `getRoomList()` 为 `getHomepageRooms()`
   - 实现分类筛选参数传递
   - 测试列表加载和筛选

5. **升级直播卡片组件**（45分钟）:
   - 修改Props类型为 `HomepageRoomItem`
   - 新增主讲人信息显示
   - 新增统计数据显示
   - 添加数据格式化工具函数
   - 测试卡片显示和点击

6. **完整测试与优化**（45分钟）:
   - 执行测试验证清单
   - 优化加载状态和错误处理
   - 优化UI细节和动画效果

**总计时间**: 约3-4小时

---

请根据以上详细要求，依次优化和重构首页相关组件的代码。优先级：**API封装优化 > 分类筛选 > 焦点图轮播 > 首页主组件 > 直播卡片**。
