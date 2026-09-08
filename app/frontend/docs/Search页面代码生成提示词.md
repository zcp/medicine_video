h# 搜索页面代码生成提示词（uni-app移动端版 V1.0）

**版本**: V1.0  
**创建日期**: 2026-03-06  
**适用平台**: uni-app（H5/Android/iOS/微信小程序）  
**技术栈**: Vue 3 Composition API + TypeScript  
**参考文档**: 搜索页面设计文档（V3.0 - 移动端规范版）

---

## 📚 必读文档清单（Mandatory Reading）

在开始开发前，你必须先阅读以下文档：

### 设计文档（最高优先级）
- **📖 `docs/搜索页面设计文档.md`**（V3.0 - 移动端规范版）- 完整的UI设计、技术实现、后端方案
- **📖 `docs/后端设计文档/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API-统一版.md`** - 搜索API完整设计
- **📖 `docs/直播SaaS平台移动端前端设计文档.md`**（第6章 - 核心数据模型、第8章 - API接口映射）

### 规范文档
- **📖 移动端开发规范**（搜索页面设计文档第3章）
- **📖 移动端安全规范**（搜索页面设计文档第8章）
- **📖 移动端异常处理规范**（搜索页面设计文档第9章）
- **📖 移动端性能优化规范**（搜索页面设计文档第10章）
- **📖 Design System规范**（搜索页面设计文档第11章）

---

## 第0章：强制性前置检查 ⚡（必须先执行）

### 0.1 检查目的

在生成任何代码之前，必须全面了解项目现状，避免：
- ❌ 覆盖已有的完善代码
- ❌ 与现有类型定义冲突
- ❌ 创建重复的工具函数
- ❌ 破坏现有的导入依赖关系

### 0.2 必须执行的检查步骤

#### 步骤1：读取现有核心文件（强制）

你必须先读取以下文件，了解现有实现：

```bash
必须读取的文件清单：
✅ src/api/homepage.ts - 首页API封装（参考数据结构）
✅ src/api/room.ts - 房间API封装（房间详情获取）
✅ src/api/expert.ts - 专家API封装（专家详情、关注功能）
✅ src/api/brand.ts - 品牌API封装（品牌详情）
✅ src/store/auth.ts - 认证状态管理（User接口、登录状态）
✅ src/config/env.ts - 环境配置（VITE_USE_MOCK开关、BASE_URL）
✅ src/types/room.ts - 房间类型定义
✅ src/types/expert.ts - 专家类型定义
✅ src/types/brand.ts - 品牌类型定义
✅ src/types/common.ts - 通用类型定义（PaginatedData等）
✅ src/utils/time.ts - 时间格式化工具
✅ src/utils/storage.ts - 本地存储封装
✅ src/pages.json - 路由配置
✅ src/static/fonts/iconfont.css - 可用图标列表
✅ package.json - 项目依赖（检查lodash-es是否已安装）

【重点检查】现有业务组件（用于复用）：
✅ src/components/business/RoomCard.vue - 直播间卡片（收藏页面使用）
✅ src/components/business/ExpertCard.vue - 专家卡片（专家专题页面使用）
✅ src/components/business/BrandCard.vue - 品牌卡片（品牌列表页面使用）
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/pages/app/search/ - 确认搜索页面目录（可能不存在）
✅ src/api/ - 列出所有.ts文件
✅ src/store/ - 列出所有.ts文件
✅ src/components/app/ - 列出可复用移动端组件
✅ src/components/business/ - 列出业务组件（重点：卡片组件）
✅ src/utils/ - 列出现有工具函数
```

**执行命令**：使用 `list_dir` 工具扫描目录。

#### 步骤3：在聊天窗口输出项目现状分析（强制）

⚠️ **重要**：不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

基于步骤1和步骤2的检查结果，在聊天窗口中输出以下结构化分析：

---

**📊 搜索页面开发现状分析**

**一、已存在且可直接复用的文件（✅ 直接使用）**
- 列出所有可复用的API、Store、组件、工具函数
- 注明文件路径、核心功能
- 给出"直接导入使用"的结论

**二、已存在但需要扩展的文件（🔧 需要补充）**
- 列出需要补充的文件
- 明确列出现有字段清单
- 明确列出缺失字段
- 说明操作方式（保留现有字段）

**三、需要新建的文件（➕ 需新建）**
- 列出所有需要新建的页面文件
- 列出需要新建的组件文件（优先考虑复用现有组件）
- 列出需要新建的类型定义文件
- 列出需要新建的API封装文件
- 列出需要新建的Store文件

**四、卡片组件复用评估（🔍 重点分析）**
- 评估现有RoomCard是否可复用于搜索结果
- 评估现有ExpertCard是否可复用于搜索结果
- 评估现有BrandCard是否可复用于搜索结果
- 如果可以复用，说明需要适配的props
- 如果不能复用，说明需要新建的理由

**五、路由配置检查（📍 pages.json）**
- 检查现有搜索相关路由
- 列出需要新增的路由

**六、API支持情况检查（🔌 后端接口）**
- 检查后端是否支持推荐API（/search/suggestions、/experts?is_featured=true等）
- 如果不支持，说明使用列表API的降级方案（如：用/experts + limit参数替代）

**七、安全性分析**
- ⚠️ 列出潜在风险点
- ✅ 给出安全操作策略

---

#### 步骤4：等待用户确认（强制）

在聊天窗口输出分析结果后，**必须等待用户确认**才能继续生成代码。

向用户提问：
```
📋 以上是搜索页面开发现状分析结果。

请确认：
1. 分析结果是否准确？
2. 是否有遗漏或需要调整的地方？
3. 如果确认无误，请输入"确认继续"开始代码生成。
```

**禁止**在用户确认前开始生成任何代码！

---

## 第1章：角色定义（Role Definition）

你是一名**资深移动端前端工程师**，具备以下专业技能：

- **精通技术栈**：uni-app、Vue 3 Composition API、TypeScript、移动端H5、小程序等多端开发
- **搜索功能专家**：熟悉搜索交互设计、防抖节流、虚拟滚动、结果缓存等性能优化技术
- **跨平台适配**：精通uni-app的平台差异处理和条件编译
- **Design System实践者**：严格遵循全站设计语言（色彩、字体、间距、动效）
- **增量开发能力**：能够在现有项目基础上进行安全的增量开发，不破坏现有功能

**你的任务是根据详细设计文档和现有代码基础，编写高质量、功能完整、可直接运行的搜索页面代码。**

---

## 第2章：任务目标（Task Objective）

### 2.1 核心目标

开发移动端搜索功能，包括两个核心页面：

1. **搜索前页面（index.vue）**：热门搜索 + 搜索历史（**不包含推荐内容**）
2. **搜索结果页（results.vue）**：三个Tab（直播间/专家/品牌）+ 搜索结果列表
3. **空结果页**：搜索结果页的一种状态，显示推荐内容

### 2.2 页面布局设计

#### 2.2.1 搜索前页面（index.vue）

```
┌─────────────────────────────────────┐
│  ← [搜索框：搜索直播间...]      🔍 │  ← 顶部搜索框（自定义导航栏）
├─────────────────────────────────────┤
│                                     │
│  🔥 热门搜索                        │  ← 热门搜索词（Mock数据）
│  ┌──────┬──────┬──────┬──────┐    │
│  │ 心脏病 │ 骨科手术 │ 糖尿病 │ 肿瘤 │    │
│  │ 儿科  │ 神经外科 │ 妇科  │ 康复  │    │
│  └──────┴──────┴──────┴──────┘    │
│                                     │
│  ⏱ 搜索历史                  清空 │  ← 用户搜索历史
│  ┌─────────────────────────────┐  │
│  │ 📍 心脏病手术演示              │  │
│  │ 📍 李四教授                   │  │
│  │ 📍 骨科病例讨论               │  │
│  └─────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

> **注意**：实际实现中，搜索前页面**不包含推荐内容区域**。推荐内容仅在搜索结果为空时显示。

#### 2.2.2 搜索结果页（results.vue）

```
┌─────────────────────────────────────┐
│  ← [骨科]                        🔍 │  ← 搜索框（SearchNavBar）
├─────────────────────────────────────┤
│  直播间 | 专家 | 品牌               │  ← Tab切换（仅3个Tab）
│  ═════                              │
│                                     │
│  ┌─────────────────────────────┐  │  ← 搜索结果列表
│  │ 共找到 15 个结果               │  │  ← 结果数量提示
│  ├─────────────────────────────┤  │
│  │ [直播中] 骨科手术演示          │  │  ← 直播间卡片
│  │ 🖼 [封面图]                    │  │    （SearchResultCard）
│  │ 演示最新的微创技术...           │  │
│  │ 👨‍⚕️ 李四 教授 | 主任医师 | XX医院 │  │
│  │ 👁 1250人观看                 │  │
│  ├─────────────────────────────┤  │
│  │ 👨‍⚕️  李四 教授  副主任医师   ➕ │  │  ← 专家卡片
│  │ [头像] 中山大学第一附属医院     │  │    （ExpertCard复用）
│  │       神经外科                 │  │
│  ├─────────────────────────────┤  │
│  │ 🏢  Medtronic 中国        ➕  │  │  ← 品牌卡片
│  │ [Logo] 官方品牌                │  │    （SearchResultCard）
│  │       为生命赋能                │  │
│  └─────────────────────────────┘  │
│                                     │
│  上拉加载更多...                    │  ← 加载更多提示
│                                     │
└─────────────────────────────────────┘
```

> **Tab说明**：实际实现中，**移除了"综合"Tab**，仅保留：直播间、专家、品牌。每个Tab独立显示对应类型的搜索结果。
│  ═════                              │
│                                     │
│         📭                          │
│     暂无搜索结果                    │
│                                     │
│  ──────────────────────────────    │
│                                     │
│  💡 为你推荐优质直播                │  ← 推荐分割线
│  ┌─────────────────────────────┐  │
│  │ [直播中] 肝胆胰外科手术直播    │  │  ← 推荐直播间
│  │ 🖼 [封面图]                    │  │
│  │ 李四 · 教授 · XX医院           │  │
│  └─────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### 2.3 功能模块清单

| 功能模块 | 优先级 | 实现复杂度 | 说明 |
|---------|-------|-----------|------|
| **搜索框组件** | P0 | ⭐⭐ | 防抖输入、清空按钮、自定义导航栏 |
| **热门搜索** | P0 | ⭐ | Mock数据、胶囊按钮、点击跳转 |
| **搜索历史** | P0 | ⭐ | 本地存储、单条删除、全部清空 |
| **直播间Tab** | P0 | ⭐⭐ | 直播间卡片列表、分页、标题解析 |
| **专家Tab** | P0 | ⭐⭐ | 专家卡片（复用）、关注功能 |
| **品牌Tab** | P0 | ⭐⭐ | 品牌卡片、关注功能 |
| **空结果推荐** | P0 | ⭐⭐ | 空状态提示、根据Tab显示对应推荐 |
| **搜索防抖** | P0 | ⭐ | 300ms防抖优化 |
| **结果缓存** | P1 | ⭐⭐ | 5分钟缓存、减少请求 |
| **虚拟滚动** | P2 | ⭐⭐⭐ | 超过50项启用 |

---

## 第3章：技术架构与规范（Architecture & Specs）

### 3.1 技术栈选择

```
前端框架：uni-app
组件规范：Vue 3 Composition API
类型系统：TypeScript
状态管理：Pinia
网络请求：uni.request（基于 @/api/request.ts 封装）
本地存储：uni.setStorageSync / uni.getStorageSync
样式方案：SCSS + rpx单位
```

### 3.2 目录结构

```plaintext
src/
├── pages/
│   └── app/
│       └── search/
│           ├── index.vue            # 搜索前页面
│           └── results.vue          # 搜索结果页
│
├── components/
│   └── app/                         # 搜索相关的全局组件
│       ├── SearchBar.vue            # 搜索框
│       ├── SearchNavBar.vue         # 搜索结果页导航栏
│       ├── HotSearches.vue          # 热门搜索
│       ├── SearchHistory.vue        # 搜索历史
│       └── SearchResultCard.vue     # 搜索结果卡片
│   └── expert/
│       └── ExpertCard.vue           # 专家卡片（复用）
│
├── api/
│   └── search.ts                    # 搜索API封装
│
├── store/
│   └── search.ts                    # 搜索状态管理（Pinia）
│
├── types/
│   └── search.ts                    # 搜索相关类型定义
│
└── utils/
    └── search-history.ts            # 搜索历史管理
```

### 3.3 代码注释规范

为了保证代码可维护性和团队协作效率，必须遵循以下注释规范：

#### 3.3.1 JSDoc注释规范

**所有导出的函数、类、接口必须添加JSDoc注释**：

```typescript
/**
 * 执行全局搜索
 * @param keyword 搜索关键词
 * @param page 页码，从1开始
 * @param size 每页数量，默认20
 * @returns 搜索结果的Promise对象
 * @throws {Error} 如果关键词为空或网络请求失败
 * @example
 * const result = await globalSearch('肝胆外科', 1, 20);
 * console.log(result.data.items);
 */
export const globalSearch = (
  keyword: string, 
  page: number = 1, 
  size: number = 20
) => {
  // 实现代码...
};
```

#### 3.3.2 行内注释规范

**复杂逻辑（嵌套3层以上或关键算法）必须添加行内注释**：

```typescript
// ✅ 好的注释：说明为什么这样做
const loadRecommendations = async () => {
  // 综合Tab需要混合直播间和专家，按照"直播-专家-直播"顺序排列
  // 这样可以提供更丰富的内容多样性
  if (currentTab.value === 'all') {
    const [roomsRes, expertsRes] = await Promise.all([...]);
    
    // 混合排列：直播-专家-直播-专家-直播
    recommendations.value = [
      { ...roomsRes.data.items[0], type: 'room' },
      { ...expertsRes.data.items[0], type: 'expert' },
      // ...
    ].filter(item => item.id); // 过滤掉可能的undefined项
  }
};

// ❌ 差的注释：重复代码内容
const page = ref(1); // 定义page变量为1
```

#### 3.3.3 TODO/FIXME标记规范

**临时方案使用TODO标记，遗留问题使用FIXME标记**：

```typescript
// TODO: 后端实现推荐API后，改为getExperts({ is_featured: true, size: 5 })
const res = await getExperts({ page: 1, size: 5 });

// FIXME: 当搜索结果超过1000条时，分页加载会很慢，需要优化
if (total.value > 1000) {
  // 临时限制最大页数
}
```

#### 3.3.4 注释最佳实践

1. **用中文注释**：团队主要使用中文，中文注释更易理解
2. **注释说明"为什么"而非"是什么"**：代码本身已经说明"是什么"
3. **关键业务逻辑必须注释**：如数据转换、特殊处理、兼容性处理
4. **注释要与代码同步更新**：修改代码时必须更新相关注释
5. **避免过度注释**：简单的代码不需要注释

### 3.4 核心组件设计

#### 3.3.1 SearchBar 组件

**功能要求**：
- 输入防抖（300ms）
- 清空按钮
- 搜索图标
- 支持回车搜索
- 支持历史记录联想（可选）

**关键代码**：
```vue
<template>
  <view class="search-bar">
    <view class="search-input-wrapper">
      <text class="icon-search"></text>
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="搜索直播间、专家、品牌..."
        confirm-type="search"
        @input="handleInput"
        @confirm="handleSearch"
      />
      <text
        v-if="searchKeyword"
        class="icon-close"
        @click="handleClear"
      ></text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { debounce } from 'lodash-es';

// ✅ 添加props定义，支持外部传入value
const props = defineProps<{
  value?: string;
  placeholder?: string;
}>();

const emit = defineEmits<{
  (e: 'search', keyword: string): void;
  (e: 'input', keyword: string): void;
}>();

const searchKeyword = ref(props.value || '');

// ✅ 监听外部value变化（用于搜索结果页）
watch(() => props.value, (newValue) => {
  if (newValue !== searchKeyword.value) {
    searchKeyword.value = newValue || '';
  }
});

// 防抖搜索（300ms）
const debouncedSearch = debounce((keyword: string) => {
  if (keyword.trim().length >= 2) {
    emit('input', keyword);
  }
}, 300);

const handleInput = () => {
  debouncedSearch(searchKeyword.value);
};

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    emit('search', searchKeyword.value.trim());
  }
};

const handleClear = () => {
  searchKeyword.value = '';
  emit('input', '');
};
</script>
```

#### 3.3.2 HotSearches 组件

**功能要求**：
- 获取热门搜索词（**使用Store中的Mock数据**）
- Pill按钮样式（圆角胶囊）
- 点击填充搜索框并执行搜索
- 支持2列/3列响应式布局

**数据来源**：`src/store/search.ts` 中的 `hotSearches` 字段（硬编码Mock数据）

**实际实现说明**：
- 热门搜索数据存储在Pinia store中，格式为 `{ keyword: string, heat: number, isNew?: boolean }`
- 组件从store读取数据并展示
- 后端未实现热门搜索API，暂时使用硬编码数据

**完整代码**：

```vue
<template>
  <view class="hot-searches">
    <view class="header">
      <text class="icon">🔥</text>
      <text class="title">热门搜索</text>
    </view>
    <view class="keywords">
      <text
        v-for="(keyword, index) in keywords"
        :key="index"
        class="keyword-pill"
        @click="handleClick(keyword)"
      >
        {{ keyword }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getHotSearches } from '@/api/search';

const emit = defineEmits<{
  (e: 'click', keyword: string): void;
}>();

const keywords = ref<string[]>([]);
const loading = ref(false);

// ⚙️ 配置：是否使用真实API（后端实现后改为true）
const USE_REAL_API = false;

// 📋 Mock数据：热门搜索词配置
const MOCK_HOT_SEARCHES = [
  '肝胆外科',
  '内镜手术',
  '骨科培训',
  '微创手术',
  '病例讨论',
  '王教授'
];

// 加载热门搜索
const loadHotSearches = async () => {
  try {
    loading.value = true;
    
    if (USE_REAL_API) {
      // 方案1：真实API（后端实现后使用）
      try {
        const res = await getHotSearches('', 6); // 尝试传入空字符串
        keywords.value = res.data.suggestions || [];
        console.log('[热门搜索] API获取成功:', keywords.value.length);
      } catch (apiError) {
        console.warn('[热门搜索] API调用失败，回退到Mock数据:', apiError);
        keywords.value = MOCK_HOT_SEARCHES;
      }
    } else {
      // 方案2：Mock数据（当前方案）
      keywords.value = MOCK_HOT_SEARCHES;
      console.log('[热门搜索] 使用Mock数据');
    }
    
  } catch (error) {
    console.error('[热门搜索] 加载失败:', error);
    // 确保至少显示Mock数据
    keywords.value = MOCK_HOT_SEARCHES;
  } finally {
    loading.value = false;
  }
};

const handleClick = (keyword: string) => {
  emit('click', keyword);
};

onMounted(() => {
  loadHotSearches();
});
</script>

<style lang="scss" scoped>
.hot-searches {
  .header {
    display: flex;
    align-items: center;
    margin-bottom: 24rpx;
    
    .icon {
      font-size: 36rpx;
      margin-right: 12rpx;
    }
    
    .title {
      font-size: 32rpx;
      font-weight: 600;
      color: #1F2937;
    }
  }
  
  .keywords {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
    
    .keyword-pill {
      padding: 12rpx 32rpx;
      background: #F3F4F6;
      border-radius: 40rpx;
      font-size: 28rpx;
      color: #6B7280;
      transition: all 0.3s;
      
      &:active {
        background: #E5E7EB;
        transform: scale(0.95);
      }
    }
  }
}
</style>
```

**⚠️ 重要说明**：

1. **当前使用Mock数据**：由于后端暂未实现 `/api/v1/search/suggestions` 接口，组件使用配置数据作为热门搜索词
2. **快速切换到真实API**：后端实现后，只需修改 `USE_REAL_API` 为 `true`
3. **降级保证**：即使真实API调用失败，也会自动回退到Mock数据，确保功能可用
4. **Mock数据维护**：可根据运营需求定期更新 `MOCK_HOT_SEARCHES` 数组
5. **未来升级路径**：建议后端新增独立的 `GET /api/v1/search/hot` API（无需q参数）

#### 3.3.3 SearchHistory 组件

**功能要求**：
- 本地存储管理（uni.setStorageSync）
- 最多保存10条历史记录
- 显示清空按钮
- 点击历史项填充搜索框并执行搜索

**存储Key**：`search_history`

**完整代码**：

```vue
<template>
  <view class="search-history">
    <view class="header">
      <view class="title-row">
        <text class="icon">⏱</text>
        <text class="title">搜索历史</text>
      </view>
      <text 
        v-if="history.length > 0"
        class="clear-btn" 
        @click="handleClear"
      >
        清空
      </text>
    </view>
    
    <view v-if="history.length === 0" class="empty">
      <text class="empty-text">暂无搜索历史</text>
    </view>
    
    <view v-else class="history-list">
      <view
        v-for="(item, index) in history"
        :key="index"
        class="history-item"
        @click="handleClick(item)"
      >
        <text class="icon-history">📍</text>
        <text class="text">{{ item }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { 
  getSearchHistory, 
  clearSearchHistory 
} from '@/utils/search-history';

const emit = defineEmits<{
  (e: 'click', keyword: string): void;
  (e: 'clear'): void;
}>();

const history = ref<string[]>([]);

// 加载搜索历史
const loadHistory = () => {
  history.value = getSearchHistory();
};

// 处理点击历史项
const handleClick = (keyword: string) => {
  emit('click', keyword);
};

// 处理清空历史
const handleClear = () => {
  uni.showModal({
    title: '确认清空',
    content: '确定要清空所有搜索历史吗？',
    success: (res) => {
      if (res.confirm) {
        clearSearchHistory();
        history.value = [];
        emit('clear');
        
        uni.showToast({
          title: '已清空',
          icon: 'success',
          duration: 1500
        });
      }
    }
  });
};

onMounted(() => {
  loadHistory();
});

// 暴露方法供父组件调用
defineExpose({
  loadHistory
});
</script>

<style lang="scss" scoped>
.search-history {
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24rpx;
    
    .title-row {
      display: flex;
      align-items: center;
      
      .icon {
        font-size: 36rpx;
        margin-right: 12rpx;
      }
      
      .title {
        font-size: 32rpx;
        font-weight: 600;
        color: #1F2937;
      }
    }
    
    .clear-btn {
      font-size: 28rpx;
      color: #9CA3AF;
      padding: 8rpx 16rpx;
      
      &:active {
        opacity: 0.6;
      }
    }
  }
  
  .empty {
    padding: 60rpx 0;
    text-align: center;
    
    .empty-text {
      font-size: 28rpx;
      color: #9CA3AF;
    }
  }
  
  .history-list {
    display: flex;
    flex-direction: column;
    gap: 12rpx;
    
    .history-item {
      display: flex;
      align-items: center;
      padding: 20rpx 24rpx;
      background: #F9FAFB;
      border-radius: 12rpx;
      transition: all 0.3s;
      
      .icon-history {
        font-size: 32rpx;
        margin-right: 16rpx;
      }
      
      .text {
        flex: 1;
        font-size: 28rpx;
        color: #374151;
      }
      
      &:active {
        background: #F3F4F6;
        transform: scale(0.98);
      }
    }
  }
}
</style>
```

**组件使用示例**：

```vue
<script setup>
import { ref } from 'vue';
import SearchHistory from './components/SearchHistory.vue';
import { addSearchHistory } from '@/utils/search-history';

const searchHistoryRef = ref();

// 执行搜索时添加历史
const handleSearch = (keyword: string) => {
  addSearchHistory(keyword);
  // 刷新历史列表
  searchHistoryRef.value?.loadHistory();
  // 执行搜索...
};

// 点击历史项
const handleHistoryClick = (keyword: string) => {
  handleSearch(keyword);
};
</script>

<template>
  <SearchHistory
    ref="searchHistoryRef"
    @click="handleHistoryClick"
    @clear="() => console.log('历史已清空')"
  />
</template>
```

### 3.5 卡片组件设计（优先复用现有组件）

⚠️ **重要原则**：搜索页面的卡片组件应该**优先复用**现有的业务组件，而不是重新创建。

#### 3.5.1 直播间卡片 - 复用策略

**组件来源**：复用 `src/components/business/RoomCard.vue`（收藏页面使用的组件）

**复用评估**：
- ✅ 现有RoomCard已包含：封面图、标题、专家信息、时长、状态标签
- ✅ 布局为横向卡片，适合搜索结果列表
- ✅ 已支持直播状态显示（直播中/预告/回放）

**数据适配**（需要在搜索结果页中转换数据格式）：
```typescript
// 搜索API返回的数据结构
interface SearchRoomResult {
  type: 'room';
  id: string;
  title: string;
  summary: string;
  cover_url: string;
  metadata: {
    live_status: 'live' | 'upcoming' | 'replay';
    viewer_count: number;
    host_expert?: {
      expert_id: string;
      name: string;
      title: string;
      hospital: string;
    };
  };
}

// 转换为RoomCard组件所需的props格式
const adaptRoomData = (searchResult: SearchRoomResult) => {
  return {
    id: searchResult.id,
    title: searchResult.title,
    cover_url: searchResult.cover_url,
    live_status: searchResult.metadata.live_status,
    viewer_count: searchResult.metadata.viewer_count,
    expert_name: searchResult.metadata.host_expert?.name,
    expert_title: searchResult.metadata.host_expert?.title,
    hospital: searchResult.metadata.host_expert?.hospital
  };
};
```

**使用示例**：
```vue
<RoomCard
  v-if="item.type === 'room'"
  :data="adaptRoomData(item)"
  @click="handleRoomClick(item)"
/>
```

#### 3.5.2 专家卡片 - 复用策略

**组件来源**：复用 `src/components/business/ExpertCard.vue`（专家专题页面使用的组件）

**复用评估**：
- ✅ 现有ExpertCard已包含：姓名、职称、医院、关注按钮、统计数据
- ✅ 适合搜索结果展示

**数据适配**：
```typescript
interface SearchExpertResult {
  type: 'expert';
  id: string;
  title: string; // 专家姓名
  summary: string; // 简介
  cover_url: string; // 头像
  metadata: {
    hospital: string;
    title: string; // 职称
    is_followed?: boolean;
  };
}

const adaptExpertData = (searchResult: SearchExpertResult) => {
  return {
    id: searchResult.id,
    name: searchResult.title,
    avatar_url: searchResult.cover_url,
    title: searchResult.metadata.title,
    hospital: searchResult.metadata.hospital,
    is_followed: searchResult.metadata.is_followed || false
  };
};
```

**使用示例**：
```vue
<ExpertCard
  v-else-if="item.type === 'expert'"
  :data="adaptExpertData(item)"
  @click="handleExpertClick(item)"
/>
```

#### 3.5.3 品牌卡片 - 复用策略

**组件来源**：复用 `src/components/business/BrandCard.vue`（品牌列表页面使用的组件）

**复用评估**：
- ✅ 现有BrandCard已包含：Logo、品牌名、简介、关注按钮
- ✅ 布局简洁，适合搜索结果

**数据适配**：
```typescript
interface SearchBrandResult {
  type: 'brand';
  id: string;
  title: string; // 品牌名称
  summary: string; // 品牌简介
  cover_url: string; // 品牌Logo
  metadata: {
    is_official?: boolean;
  };
}

const adaptBrandData = (searchResult: SearchBrandResult) => {
  return {
    id: searchResult.id,
    name: searchResult.title,
    logo_url: searchResult.cover_url,
    description: searchResult.summary,
    is_official: searchResult.metadata.is_official || false
  };
};
```

**使用示例**：
```vue
<BrandCard
  v-else-if="item.type === 'brand'"
  :data="adaptBrandData(item)"
  @click="handleBrandClick(item)"
/>
```

#### 3.5.4 如果需要新建组件

⚠️ **仅在以下情况新建组件**：
1. 现有组件完全不适合搜索场景（需要详细说明理由）
2. 现有组件缺少关键字段且无法扩展
3. 搜索结果需要特殊的高亮显示（如关键词高亮）

如果需要新建，请参考现有组件的样式规范，保持设计一致性。

---

## 第4章：API依赖与数据流（API & Data Flow）

### 4.1 搜索API接口（需要新建 `src/api/search.ts`）

#### 4.1.1 热门搜索词API

```typescript
/**
 * 获取热门搜索词
 * @param limit 返回数量，默认6个
 */
export const getHotSearches = (limit: number = 6) => {
  return request<{ suggestions: string[] }>({
    url: '/search/suggestions',
    method: 'GET',
    params: { limit }
  });
};
```

**API文档**：`GET /api/v1/search/suggestions?limit=6`

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "suggestions": ["肝胆外科", "内镜手术", "骨科培训", "微创手术", "病例讨论", "王教授"]
  },
  "timestamp": "2026-03-06T10:00:00Z"
}
```

#### 4.1.2 综合搜索API

```typescript
/**
 * 综合搜索（不指定type，混合返回所有类型）
 * @param keyword 搜索关键词
 * @param page 页码
 * @param size 每页数量
 */
export const globalSearch = (keyword: string, page: number = 1, size: number = 20) => {
  return request<PaginatedData<SearchResultItem>>({
    url: '/search',
    method: 'GET',
    params: { q: keyword, page, size }
  });
};
```

**API文档**：`GET /api/v1/search?q=关键词&page=1&size=20`

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "page": 1,
    "size": 20,
    "items": [
      {
        "type": "room",
        "id": "room-uuid-123",
        "title": "肝胆胰外科手术直播",
        "summary": "演示最新的微创技术...",
        "cover_url": "/media/rooms/xxx/cover.jpg",
        "match_score": 0.9,
        "metadata": {
          "live_status": "live",
          "viewer_count": 1250,
          "host_expert": {
            "expert_id": "expert-uuid-456",
            "name": "李四",
            "avatar_url": "/media/experts/xxx/avatar.jpg",
            "title": "教授",
            "hospital": "中山大学附属第一医院"
          }
        }
      },
      {
        "type": "expert",
        "id": "expert-uuid-789",
        "title": "李四",
        "summary": "肝胆胰外科专家...",
        "cover_url": "/media/experts/xxx/avatar.jpg",
        "match_score": 0.85,
        "metadata": {
          "hospital": "中山大学附属第一医院",
          "title": "教授",
          "is_followed": false
        }
      }
    ]
  },
  "timestamp": "2026-03-06T10:00:00Z"
}
```

#### 4.1.3 分类搜索API

```typescript
/**
 * 分类搜索（指定type）
 * @param keyword 搜索关键词
 * @param type 搜索类型（room/expert/brand）
 * @param page 页码
 * @param size 每页数量
 */
export const searchByType = (
  keyword: string,
  type: 'room' | 'expert' | 'brand',
  page: number = 1,
  size: number = 10
) => {
  return request<PaginatedData<SearchResultItem>>({
    url: '/search',
    method: 'GET',
    params: { q: keyword, type, page, size }
  });
};
```

**API文档**：`GET /api/v1/search?q=关键词&type=room&page=1&size=10`

#### 4.1.4 推荐内容API（复用现有API）

**直播间推荐**：复用 `GET /api/v1/homepage/rooms?sort=heat:desc&size=5`

**专家推荐**：复用 `GET /api/v1/experts?is_featured=true&size=5`

**品牌推荐**：复用 `GET /api/v1/brands?sort=sort_order:asc&size=5`

### 4.2 搜索历史管理（需要新建 `src/utils/search-history.ts`）

```typescript
const SEARCH_HISTORY_KEY = 'search_history';
const MAX_HISTORY_COUNT = 10;

/**
 * 获取搜索历史
 */
export const getSearchHistory = (): string[] => {
  try {
    const history = uni.getStorageSync(SEARCH_HISTORY_KEY);
    return Array.isArray(history) ? history : [];
  } catch (error) {
    console.error('[搜索历史] 获取失败:', error);
    return [];
  }
};

/**
 * 添加搜索历史
 */
export const addSearchHistory = (keyword: string) => {
  try {
    let history = getSearchHistory();
    
    // 去重（如果已存在，移动到最前面）
    history = history.filter(item => item !== keyword);
    history.unshift(keyword);
    
    // 限制数量
    if (history.length > MAX_HISTORY_COUNT) {
      history = history.slice(0, MAX_HISTORY_COUNT);
    }
    
    uni.setStorageSync(SEARCH_HISTORY_KEY, history);
  } catch (error) {
    console.error('[搜索历史] 添加失败:', error);
  }
};

/**
 * 清空搜索历史
 */
export const clearSearchHistory = () => {
  try {
    uni.removeStorageSync(SEARCH_HISTORY_KEY);
  } catch (error) {
    console.error('[搜索历史] 清空失败:', error);
  }
};
```

### 4.3 搜索状态管理（需要新建 `src/store/modules/search.ts`）

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SearchResultItem } from '@/types/search';
import { globalSearch, searchByType, getHotSearches } from '@/api/search';
// ✅ 导入推荐API（用于空结果推荐）
import { getHomepageRooms } from '@/api/homepage';
import { getExperts } from '@/api/expert';
import { getBrands } from '@/api/brand';

export const useSearchStore = defineStore('search', () => {
  // 状态
  const searchKeyword = ref('');
  const currentTab = ref<'all' | 'room' | 'expert' | 'brand'>('all');
  const searchResults = ref<SearchResultItem[]>([]);
  const total = ref(0);
  const page = ref(1);
  const size = ref(20);
  const loading = ref(false);
  const error = ref<string | null>(null);
  
  // 热门搜索词
  const hotSearches = ref<string[]>([]);
  
  // 推荐内容
  const recommendations = ref<any[]>([]);
  
  // 搜索结果缓存（5分钟）
  const searchCache = new Map<string, {
    data: SearchResultItem[];
    total: number;
    timestamp: number;
  }>();
  const CACHE_EXPIRE_TIME = 5 * 60 * 1000; // 5分钟
  
  // 计算属性
  const hasMore = computed(() => {
    return searchResults.value.length < total.value;
  });
  
  const isEmpty = computed(() => {
    return !loading.value && searchResults.value.length === 0;
  });
  
  // 获取热门搜索词
  const fetchHotSearches = async () => {
    try {
      const res = await getHotSearches(6);
      hotSearches.value = res.data.suggestions;
    } catch (err) {
      console.error('[搜索Store] 获取热门搜索失败:', err);
    }
  };
  
  // 执行搜索
  const performSearch = async (keyword: string, tabType?: 'all' | 'room' | 'expert' | 'brand') => {
    if (!keyword.trim()) {
      uni.showToast({
        title: '请输入搜索关键词',
        icon: 'none'
      });
      return;
    }
    
    searchKeyword.value = keyword;
    if (tabType) {
      currentTab.value = tabType;
    }
    page.value = 1;
    searchResults.value = [];
    total.value = 0;
    error.value = null;
    
    // 检查缓存
    const cacheKey = `${keyword}_${currentTab.value}_${page.value}`;
    const cached = searchCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_EXPIRE_TIME) {
      searchResults.value = cached.data;
      total.value = cached.total;
      return;
    }
    
    loading.value = true;
    
    try {
      let res;
      if (currentTab.value === 'all') {
        res = await globalSearch(keyword, page.value, size.value);
      } else {
        res = await searchByType(keyword, currentTab.value, page.value, 10);
      }
      
      searchResults.value = res.data.items;
      total.value = res.data.total;
      
      // 更新缓存
      searchCache.set(cacheKey, {
        data: res.data.items,
        total: res.data.total,
        timestamp: Date.now()
      });
      
      // 限制缓存数量
      if (searchCache.size > 10) {
        const firstKey = searchCache.keys().next().value;
        searchCache.delete(firstKey);
      }
      
      // 如果无结果，加载推荐内容
      if (total.value === 0) {
        await loadRecommendations();
      }
    } catch (err: any) {
      error.value = err.message || '搜索失败';
      uni.showToast({
        title: '搜索失败，请重试',
        icon: 'none'
      });
    } finally {
      loading.value = false;
    }
  };
  
  // 加载更多
  const loadMore = async () => {
    if (!hasMore.value || loading.value) return;
    
    page.value += 1;
    loading.value = true;
    
    try {
      let res;
      if (currentTab.value === 'all') {
        res = await globalSearch(searchKeyword.value, page.value, size.value);
      } else {
        res = await searchByType(searchKeyword.value, currentTab.value, page.value, 10);
      }
      
      searchResults.value.push(...res.data.items);
      total.value = res.data.total;
    } catch (err: any) {
      error.value = err.message || '加载失败';
      page.value -= 1; // 回退页码
    } finally {
      loading.value = false;
    }
  };
  
  // 加载推荐内容
  const loadRecommendations = async () => {
    try {
      // ✅ 导入正确的API函数（在文件开头添加）
      // import { getHomepageRooms } from '@/api/homepage';
      // import { getExperts } from '@/api/expert';
      // import { getBrands } from '@/api/brand';
      
      if (currentTab.value === 'all') {
        // 综合Tab：混合推荐（直播间 + 专家）
        // 注意：如果后端不支持is_featured参数，则使用普通列表API，通过limit限制数量
        const [roomsRes, expertsRes] = await Promise.all([
          getHomepageRooms({ sort: 'heat:desc', page: 1, size: 3 }),
          // 如果后端支持推荐API：getExperts({ is_featured: true, size: 2 })
          // 如果不支持，使用列表API：getExperts({ page: 1, size: 2 })
          getExperts({ page: 1, size: 2 })  // 降级方案：显示前2个专家
        ]);
        
        // 混合排列：直播-专家-直播-专家-直播
        recommendations.value = [
          { ...roomsRes.data.items[0], type: 'room' },
          { ...expertsRes.data.items[0], type: 'expert' },
          { ...roomsRes.data.items[1], type: 'room' },
          { ...expertsRes.data.items[1], type: 'expert' },
          { ...roomsRes.data.items[2], type: 'room' }
        ].filter(item => item.id); // 过滤掉undefined项
        
      } else if (currentTab.value === 'room') {
        // 直播间Tab推荐
        const res = await getHomepageRooms({ sort: 'heat:desc', page: 1, size: 5 });
        recommendations.value = res.data.items.map(item => ({ ...item, type: 'room' }));
        
      } else if (currentTab.value === 'expert') {
        // 专家Tab推荐
        // 降级方案：如果后端不支持推荐，显示前5个专家
        const res = await getExperts({ page: 1, size: 5 });
        recommendations.value = res.data.items.map(item => ({ ...item, type: 'expert' }));
        
      } else if (currentTab.value === 'brand') {
        // 品牌Tab推荐
        const res = await getBrands({ sort: 'sort_order:asc', page: 1, size: 5 });
        recommendations.value = res.data.items.map(item => ({ ...item, type: 'brand' }));
      }
    } catch (err) {
      console.error('[搜索Store] 加载推荐失败:', err);
      recommendations.value = []; // 失败时清空推荐
    }
  };
  
  // 切换Tab
  const switchTab = (tabType: 'all' | 'room' | 'expert' | 'brand') => {
    if (currentTab.value === tabType) return;
    
    currentTab.value = tabType;
    if (searchKeyword.value) {
      performSearch(searchKeyword.value);
    }
  };
  
  // 重置状态
  const resetState = () => {
    searchKeyword.value = '';
    currentTab.value = 'all';
    searchResults.value = [];
    total.value = 0;
    page.value = 1;
    loading.value = false;
    error.value = null;
    recommendations.value = [];
  };
  
  return {
    // 状态
    searchKeyword,
    currentTab,
    searchResults,
    total,
    page,
    size,
    loading,
    error,
    hotSearches,
    recommendations,
    
    // 计算属性
    hasMore,
    isEmpty,
    
    // 方法
    fetchHotSearches,
    performSearch,
    loadMore,
    loadRecommendations,
    switchTab,
    resetState
  };
});
```

### 4.4 类型定义（需要新建 `src/types/search.ts`）

```typescript
/**
 * 搜索结果类型枚举
 */
export enum SearchResultType {
  ROOM = 'room',
  EXPERT = 'expert',
  TOPIC = 'topic',
  BRAND = 'brand'
}

/**
 * 直播状态枚举
 */
export enum LiveStatus {
  LIVE = 'live',
  UPCOMING = 'upcoming',
  REPLAY = 'replay'
}

/**
 * 主讲专家信息
 */
export interface HostExpertInfo {
  expert_id: string;
  name: string;
  avatar_url: string;
  title: string;
  hospital: string;
}

/**
 * 直播间搜索结果元数据
 */
export interface RoomSearchMetadata {
  live_status: LiveStatus;
  viewer_count: number;
  host_expert?: HostExpertInfo;
}

/**
 * 专家搜索结果元数据
 */
export interface ExpertSearchMetadata {
  hospital: string;
  title: string;
  is_followed?: boolean;
}

/**
 * 品牌搜索结果元数据
 */
export interface BrandSearchMetadata {
  website_url?: string;
  is_official?: boolean;
}

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  type: SearchResultType;
  id: string;
  title: string;
  summary?: string;
  cover_url?: string;
  match_score?: number;
  highlight?: string;
  metadata?: RoomSearchMetadata | ExpertSearchMetadata | BrandSearchMetadata;
}

/**
 * 热门搜索响应
 */
export interface HotSearchesResponse {
  suggestions: string[];
}
```

---

## 第5章：页面开发详细说明（Page Development）

### 5.1 搜索前页面（index.vue）

**文件路径**：`src/pages/app/search/index.vue`

**功能清单**：
- ✅ 自定义导航栏（返回按钮 + 搜索框）
- ✅ 搜索框组件（SearchBar）
- ✅ 热门搜索词（HotSearches，从Store读取）
- ✅ 搜索历史（SearchHistory，本地存储管理）

**页面结构**：

```vue
<template>
  <view class="search-landing-page">
    <!-- 顶部搜索框 -->
    <view class="search-bar-container">
      <SearchBar
        @search="handleSearch"
        placeholder="搜索直播间、专家、品牌..."
      />
    </view>
    
    <!-- 热门搜索 -->
    <view class="hot-searches-section">
      <view class="section-title">
        <text class="icon">🔥</text>
        <text class="title-text">热门搜索</text>
      </view>
      <HotSearches @select="handleHotSearchClick" />
    </view>
    
    <!-- 搜索历史 -->
    <view v-if="searchHistory.length > 0" class="search-history-section">
      <view class="section-title">
        <text class="icon">⏱</text>
        <text class="title-text">搜索历史</text>
        <text class="clear-btn" @click="handleClearHistory">清空</text>
      </view>
      <SearchHistory
        :history="searchHistory"
        @select="handleHistoryClick"
      />
    </view>
    
    <!-- 推荐内容 -->
    <view class="recommendations-section">
      <view class="section-title">
        <text class="icon">💡</text>
        <text class="title-text">为你推荐</text>
      </view>
      <scroll-view
        scroll-y
        class="recommendations-list"
        @scrolltolower="loadMoreRecommendations"
      >
        <!-- ✅ 使用复用的RoomCard组件 -->
        <RoomCard
          v-for="room in recommendations"
          :key="room.id"
          :data="room"
          @click="handleRoomClick(room)"
        />
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import SearchBar from './components/SearchBar.vue';
import HotSearches from './components/HotSearches.vue';
import SearchHistory from './components/SearchHistory.vue';
// ✅ 复用现有的RoomCard组件
import RoomCard from '@/components/business/RoomCard.vue';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '@/utils/search-history';
import { useSearchStore } from '@/store/modules/search';
import { getHomepageRooms } from '@/api/homepage';

const searchStore = useSearchStore();

// 搜索历史
const searchHistory = ref<string[]>([]);

// 推荐内容
const recommendations = ref<any[]>([]);
const recommendPage = ref(1);
const recommendSize = ref(10);
const hasMoreRecommend = ref(true);

// 加载搜索历史
const loadSearchHistory = () => {
  searchHistory.value = getSearchHistory();
};

// 加载推荐内容
const loadRecommendations = async () => {
  try {
    const res = await getHomepageRooms({
      page: recommendPage.value,
      size: recommendSize.value,
      sort: 'heat:desc'
    });
    
    if (recommendPage.value === 1) {
      recommendations.value = res.data.items;
    } else {
      recommendations.value.push(...res.data.items);
    }
    
    hasMoreRecommend.value = recommendations.value.length < res.data.total;
  } catch (error) {
    console.error('[搜索前页] 加载推荐失败:', error);
    uni.showToast({
      title: '加载失败',
      icon: 'none'
    });
  }
};

// 加载更多推荐
const loadMoreRecommendations = () => {
  if (!hasMoreRecommend.value) return;
  recommendPage.value += 1;
  loadRecommendations();
};

// 处理搜索
const handleSearch = (keyword: string) => {
  if (!keyword.trim()) {
    uni.showToast({
      title: '请输入搜索关键词',
      icon: 'none'
    });
    return;
  }
  
  // 添加到搜索历史
  addSearchHistory(keyword);
  
  // ✅ uni-app路由跳转（不是vue-router）
  uni.navigateTo({
    url: `/pages/app/search/results?q=${encodeURIComponent(keyword)}`
  });
};

// 处理热门搜索点击
const handleHotSearchClick = (keyword: string) => {
  handleSearch(keyword);
};

// 处理历史记录点击
const handleHistoryClick = (keyword: string) => {
  handleSearch(keyword);
};

// 清空搜索历史
const handleClearHistory = () => {
  uni.showModal({
    title: '确认清空',
    content: '确定要清空所有搜索历史吗？',
    success: (res) => {
      if (res.confirm) {
        clearSearchHistory();
        searchHistory.value = [];
        uni.showToast({
          title: '已清空',
          icon: 'success'
        });
      }
    }
  });
};

// 处理直播间点击
const handleRoomClick = (room: any) => {
  router.push({
    path: '/pages/app/live/detail',
    query: { id: room.id }
  });
};

onMounted(() => {
  loadSearchHistory();
  loadRecommendations();
  searchStore.fetchHotSearches();
});
</script>

<style lang="scss" scoped>
.search-landing-page {
  min-height: 100vh;
  background: #FFFFFF;
  
  .search-bar-container {
    padding: 24rpx 32rpx;
    background: #FFFFFF;
    position: sticky;
    top: 0;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  
  .hot-searches-section,
  .search-history-section,
  .recommendations-section {
    padding: 32rpx;
    
    .section-title {
      display: flex;
      align-items: center;
      margin-bottom: 24rpx;
      
      .icon {
        font-size: 32rpx;
        margin-right: 12rpx;
      }
      
      .title-text {
        flex: 1;
        font-size: 30rpx;
        font-weight: 600;
        color: #1F2937;
      }
      
      .clear-btn {
        font-size: 26rpx;
        color: #6B7280;
        padding: 8rpx 16rpx;
        
        &:active {
          opacity: 0.7;
        }
      }
    }
  }
  
  .recommendations-list {
    max-height: 1000rpx;
  }
}
</style>
```

### 5.2 搜索结果页（results.vue）

**文件路径**：`src/pages/app/search/results.vue`

**功能清单**：
- ✅ SearchNavBar（可修改关键词、返回按钮）
- ✅ Tab切换（直播间/专家/品牌，**仅3个Tab**）
- ✅ 搜索结果列表（SearchResultCard + ExpertCard复用）
- ✅ 空结果推荐（根据Tab类型显示对应推荐）
- ✅ 分页加载（上拉加载更多）
- ✅ 标题解析器（提取专家信息的降级策略）

**页面结构**：

```vue
<template>
  <view class="search-results-page">
    <!-- 顶部搜索框 -->
    <view class="search-bar-container">
      <text class="back-btn" @click="handleBack">←</text>
      <SearchBar
        :value="searchStore.searchKeyword"
        @search="handleSearch"
        placeholder="搜索直播间、专家、品牌..."
      />
    </view>
    
    <!-- Sticky Tab栏 -->
    <view class="sticky-tabs" :class="{ 'stuck': tabsStuck }">
      <scroll-view scroll-x class="tabs-container">
        <view
          v-for="tab in tabs"
          :key="tab.value"
          class="tab-item"
          :class="{ 'active': searchStore.currentTab === tab.value }"
          @click="handleTabChange(tab.value)"
        >
          <text class="tab-text">{{ tab.label }}</text>
          <view v-if="searchStore.currentTab === tab.value" class="tab-indicator"></view>
        </view>
      </scroll-view>
    </view>
    
    <!-- 搜索结果列表 -->
    <scroll-view
      v-if="!searchStore.isEmpty"
      scroll-y
      class="results-list"
      @scrolltolower="handleLoadMore"
    >
      <!-- 动态渲染不同类型的卡片 -->
      <!-- ✅ 使用复用的卡片组件，注意需要适配数据格式 -->
      <view
        v-for="item in searchStore.searchResults"
        :key="item.id"
        class="result-item"
      >
        <RoomCard
          v-if="item.type === 'room'"
          :data="adaptRoomData(item)"
          @click="handleRoomClick(item)"
        />
        <ExpertCard
          v-else-if="item.type === 'expert'"
          :data="adaptExpertData(item)"
          @click="handleExpertClick(item)"
        />
        <BrandCard
          v-else-if="item.type === 'brand'"
          :data="adaptBrandData(item)"
          @click="handleBrandClick(item)"
        />
      </view>
      
      <!-- 加载更多 -->
      <view v-if="searchStore.loading" class="loading-more">
        <text class="loading-text">加载中...</text>
      </view>
      
      <!-- 没有更多 -->
      <view v-if="!searchStore.hasMore && searchStore.searchResults.length > 0" class="no-more">
        <text class="no-more-text">没有更多了</text>
      </view>
    </scroll-view>
    
    <!-- 空结果推荐 -->
    <view v-if="searchStore.isEmpty" class="empty-results">
      <view class="empty-icon">📭</view>
      <text class="empty-text">暂无搜索结果</text>
      
      <!-- 分割线 -->
      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">为你推荐优质内容</text>
        <view class="divider-line"></view>
      </view>
      
      <!-- 推荐内容 -->
      <scroll-view scroll-y class="recommendations-list">
        <view
          v-for="item in searchStore.recommendations"
          :key="item.id"
          class="recommendation-item"
        >
          <RoomCard
            v-if="item.type === 'room'"
            :data="adaptRoomData(item)"
            @click="handleRoomClick(item)"
          />
          <ExpertCard
            v-else-if="item.type === 'expert'"
            :data="adaptExpertData(item)"
            @click="handleExpertClick(item)"
          />
          <BrandCard
            v-else-if="item.type === 'brand'"
            :data="adaptBrandData(item)"
            @click="handleBrandClick(item)"
          />
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { onPageScroll } from '@dcloudio/uni-app';
import SearchBar from './components/SearchBar.vue';
// ✅ 复用现有的卡片组件
import RoomCard from '@/components/business/RoomCard.vue';
import ExpertCard from '@/components/business/ExpertCard.vue';
import BrandCard from '@/components/business/BrandCard.vue';
import { useSearchStore } from '@/store/modules/search';
import { addSearchHistory } from '@/utils/search-history';

const searchStore = useSearchStore();

// ✅ uni-app获取页面参数（onLoad生命周期）
const pageQuery = ref<{q?: string}>({});

// Tab配置
const tabs = [
  { label: '综合', value: 'all' },
  { label: '直播间', value: 'room' },
  { label: '专家', value: 'expert' },
  { label: '品牌', value: 'brand' }
];

// Tab栏吸顶状态
const tabsStuck = ref(false);

// 处理页面滚动（Tab栏吸顶）
onPageScroll((e) => {
  tabsStuck.value = e.scrollTop > 100;
});

// 处理搜索
const handleSearch = (keyword: string) => {
  if (!keyword.trim()) {
    uni.showToast({
      title: '请输入搜索关键词',
      icon: 'none'
    });
    return;
  }
  
  // 添加到搜索历史
  addSearchHistory(keyword);
  
  // 执行搜索
  searchStore.performSearch(keyword);
};

// 处理Tab切换
const handleTabChange = (tabValue: 'all' | 'room' | 'expert' | 'brand') => {
  searchStore.switchTab(tabValue);
};

// 处理加载更多
const handleLoadMore = () => {
  if (searchStore.hasMore && !searchStore.loading) {
    searchStore.loadMore();
  }
};

// ✅ uni-app生命周期：页面加载时获取参数
onMounted(() => {
  // @ts-ignore uni-app全局方法
  const pages = getCurrentPages();
  const currentPage = pages[pages.length - 1];
  pageQuery.value = currentPage.$page?.options || {};
  
  const keyword = pageQuery.value.q;
  if (keyword) {
    searchStore.performSearch(keyword);
  }
});

// 处理返回
const handleBack = () => {
  uni.navigateBack();
};

// 处理直播间点击
const handleRoomClick = (room: any) => {
  uni.navigateTo({
    url: `/pages/app/live/detail?id=${room.id}`
  });
};

// 处理专家点击
const handleExpertClick = (expert: any) => {
  uni.navigateTo({
    url: `/pages/app/expert/detail?id=${expert.id}`
  });
};

// 处理品牌点击
const handleBrandClick = (brand: any) => {
  uni.navigateTo({
    url: `/pages/app/brand/detail?id=${brand.id}`
  });
};

// ✅ 数据适配函数（将搜索结果适配为卡片组件所需格式）
/**
 * 适配直播间搜索结果为RoomCard组件数据格式
 * @param searchResult 搜索结果项
 * @returns RoomCard组件所需数据
 */
const adaptRoomData = (searchResult: any) => {
  return {
    id: searchResult.id,
    title: searchResult.title,
    cover_url: searchResult.cover_url,
    live_status: searchResult.metadata?.live_status || 'replay',
    viewer_count: searchResult.metadata?.viewer_count || 0,
    expert_name: searchResult.metadata?.host_expert?.name || '',
    expert_title: searchResult.metadata?.host_expert?.title || '',
    hospital: searchResult.metadata?.host_expert?.hospital || ''
  };
};

/**
 * 适配专家搜索结果为ExpertCard组件数据格式
 * @param searchResult 搜索结果项
 * @returns ExpertCard组件所需数据
 */
const adaptExpertData = (searchResult: any) => {
  return {
    id: searchResult.id,
    name: searchResult.title,
    avatar_url: searchResult.cover_url,
    title: searchResult.metadata?.title || '',
    hospital: searchResult.metadata?.hospital || '',
    is_followed: searchResult.metadata?.is_followed || false
  };
};

/**
 * 适配品牌搜索结果为BrandCard组件数据格式
 * @param searchResult 搜索结果项
 * @returns BrandCard组件所需数据
 */
const adaptBrandData = (searchResult: any) => {
  return {
    id: searchResult.id,
    name: searchResult.title,
    logo_url: searchResult.cover_url,
    description: searchResult.summary || '',
    is_official: searchResult.metadata?.is_official || false
  };
};
</script>

<style lang="scss" scoped>
.search-results-page {
  min-height: 100vh;
  background: #FFFFFF;
  
  .search-bar-container {
    display: flex;
    align-items: center;
    padding: 24rpx 32rpx;
    background: #FFFFFF;
    position: sticky;
    top: 0;
    z-index: 20;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    
    .back-btn {
      font-size: 40rpx;
      color: #1F2937;
      margin-right: 16rpx;
      padding: 8rpx;
      
      &:active {
        opacity: 0.7;
      }
    }
  }
  
  .sticky-tabs {
    position: sticky;
    top: 140rpx; // 搜索框高度 + padding
    z-index: 15;
    background: #FFFFFF;
    border-bottom: 1px solid #F3F4F6;
    transition: box-shadow 180ms ease-out;
    
    &.stuck {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .tabs-container {
      display: flex;
      white-space: nowrap;
      
      .tab-item {
        position: relative;
        flex-shrink: 0;
        padding: 24rpx 32rpx;
        color: #6B7280;
        font-size: 28rpx;
        transition: color 180ms ease-out;
        
        &.active {
          color: #0F766E;
          font-weight: 600;
          
          .tab-indicator {
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 40rpx;
            height: 4rpx;
            background: #0F766E;
            border-radius: 2rpx;
          }
        }
        
        &:active {
          opacity: 0.7;
        }
      }
    }
  }
  
  .results-list {
    padding: 32rpx;
    
    .result-item {
      margin-bottom: 24rpx;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    .loading-more,
    .no-more {
      padding: 32rpx 0;
      text-align: center;
      
      .loading-text,
      .no-more-text {
        font-size: 26rpx;
        color: #9CA3AF;
      }
    }
  }
  
  .empty-results {
    padding: 80rpx 32rpx;
    text-align: center;
    
    .empty-icon {
      font-size: 120rpx;
      margin-bottom: 24rpx;
    }
    
    .empty-text {
      display: block;
      font-size: 30rpx;
      color: #6B7280;
      margin-bottom: 64rpx;
    }
    
    .divider {
      display: flex;
      align-items: center;
      margin: 48rpx 0;
      
      .divider-line {
        flex: 1;
        height: 1px;
        background: #F3F4F6;
      }
      
      .divider-text {
        padding: 0 24rpx;
        font-size: 24rpx;
        color: #9CA3AF;
      }
    }
    
    .recommendations-list {
      max-height: 1000rpx;
      
      .recommendation-item {
        margin-bottom: 24rpx;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}
</style>
```

---

## 第6章：安全与性能（Security & Performance）

### 6.1 安全规范（严格遵守）

#### 6.1.1 XSS防护
```vue
<!-- ✅ 正确：使用文本插值 -->
<text>{{ userInput }}</text>

<!-- ❌ 禁止：使用v-html -->
<view v-html="userInput"></view>
```

#### 6.1.2 敏感信息脱敏
```typescript
// 搜索关键词不上报原文
logger.info('搜索功能使用', {
  // ❌ keyword: keyword, // 禁止上报原文
  hasKeyword: !!keyword,   // ✅ 仅上报是否有关键词
  resultCount: total        // ✅ 仅上报结果数量
});
```

#### 6.1.3 统一错误处理

为了保持代码一致性和用户体验，建议创建统一的错误处理工具函数。

**创建错误处理工具**（`src/utils/error-handler.ts`）：

```typescript
/**
 * 统一错误提示
 * @param error 错误对象
 * @param defaultMessage 默认错误消息
 */
export const showErrorToast = (
  error: any, 
  defaultMessage: string = '操作失败'
) => {
  const message = error?.message || error?.msg || error?.data?.message || defaultMessage;
  
  uni.showToast({
    title: message,
    icon: 'none',
    duration: 2000
  });
  
  // 上报错误（不包含敏感信息）
  console.error('[错误]', {
    message,
    code: error?.code || error?.status,
    timestamp: new Date().toISOString()
  });
};

/**
 * 统一加载提示
 * @param title 加载文字
 */
export const showLoading = (title: string = '加载中...') => {
  uni.showLoading({ 
    title, 
    mask: true 
  });
};

/**
 * 隐藏加载提示
 */
export const hideLoading = () => {
  uni.hideLoading();
};

/**
 * 统一成功提示
 * @param message 成功消息
 */
export const showSuccessToast = (message: string = '操作成功') => {
  uni.showToast({
    title: message,
    icon: 'success',
    duration: 1500
  });
};
```

**在Store和页面中使用**：

```typescript
import { 
  showErrorToast, 
  showLoading, 
  hideLoading,
  showSuccessToast 
} from '@/utils/error-handler';

// Store中使用
const performSearch = async (keyword: string) => {
  try {
    showLoading('搜索中...');
    const res = await globalSearch(keyword);
    searchResults.value = res.data.items;
    // 搜索成功不需要提示，直接显示结果
  } catch (error) {
    showErrorToast(error, '搜索失败，请重试');
  } finally {
    hideLoading();
  }
};

// 页面中使用
const handleClearHistory = () => {
  uni.showModal({
    title: '确认清空',
    content: '确定要清空所有搜索历史吗？',
    success: (res) => {
      if (res.confirm) {
        try {
          clearSearchHistory();
          showSuccessToast('已清空');
        } catch (error) {
          showErrorToast(error, '清空失败');
        }
      }
    }
  });
};
```

**错误处理最佳实践**：

1. **不要向用户暴露技术细节**：只显示友好的错误消息
2. **统一错误码映射**：将后端错误码映射为用户友好的提示
3. **区分网络错误和业务错误**：网络错误提示"网络异常，请检查网络连接"
4. **提供重试机制**：关键操作失败时提供重试按钮
5. **记录但不显示敏感信息**：在console.error中记录详细错误，但不显示给用户

#### 6.1.4 权限校验

**涉及用户操作的功能必须检查登录状态**：

```typescript
import { useAuthStore } from '@/store/modules/auth';

const authStore = useAuthStore();

// 处理关注专家
const handleFollowExpert = async (expertId: string) => {
  // ✅ 检查登录状态
  if (!authStore.isLoggedIn) {
    uni.showModal({
      title: '登录提示',
      content: '关注功能需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({
            url: '/pages/app/user/login'
          });
        }
      }
    });
    return;
  }
  
  // 执行关注逻辑
  try {
    await followExpert(expertId);
    uni.showToast({
      title: '关注成功',
      icon: 'success'
    });
  } catch (error) {
    showErrorToast(error, '关注失败');
  }
};

// 处理收藏直播间
const handleFavoriteRoom = async (roomId: string) => {
  // ✅ 检查登录状态
  if (!authStore.isLoggedIn) {
    uni.showModal({
      title: '登录提示',
      content: '收藏功能需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({
            url: '/pages/app/user/login'
          });
        }
      }
    });
    return;
  }
  
  // 执行收藏逻辑
  try {
    await favoriteRoom(roomId);
    uni.showToast({
      title: '收藏成功',
      icon: 'success'
    });
  } catch (error) {
    showErrorToast(error, '收藏失败');
  }
};
```

**需要登录的功能清单**：
- ✅ 关注/取消关注专家
- ✅ 关注/取消关注品牌
- ✅ 收藏/取消收藏直播间
- ✅ 订阅直播通知
- ✅ 发布评论/聊天消息

**无需登录的功能清单**：
- ✅ 浏览搜索结果
- ✅ 查看直播间/专家/品牌详情
- ✅ 观看直播（取决于业务规则）
- ✅ 搜索历史记录（本地存储）

#### 6.1.5 CSRF防护

**本项目使用JWT认证，天然防护CSRF攻击**：

1. **JWT Token存储位置**：
   - 存储在uni-app本地存储中（`uni.getStorageSync('token')`）
   - 不使用Cookie，避免CSRF攻击

2. **Token自动添加到请求头**：
   - 在`src/api/request.ts`中，所有请求自动添加Authorization头
   ```typescript
   // src/api/request.ts
   const token = uni.getStorageSync('token');
   if (token) {
     header['Authorization'] = `Bearer ${token}`;
   }
   ```

3. **后端验证JWT**：
   - 后端通过验证JWT签名和过期时间来确认用户身份
   - 即使攻击者诱导用户点击恶意链接，也无法获取JWT Token
   - 因此无需额外的CSRF Token机制

4. **安全最佳实践**：
   - ✅ JWT Token设置合理的过期时间（如7天）
   - ✅ 敏感操作（如删除数据）需要二次确认
   - ✅ Token过期后自动跳转到登录页
   - ✅ 不在URL中传递Token（使用请求头）

**CSRF防护验证清单**：
- [x] Token存储在本地存储而非Cookie
- [x] 所有API请求自动添加Authorization头
- [x] 后端验证JWT签名和过期时间
- [x] 敏感操作有二次确认机制
- [x] Token过期处理逻辑完善

### 6.2 性能优化

#### 6.2.1 搜索防抖（300ms）
```typescript
const debouncedSearch = debounce((keyword: string) => {
  performSearch(keyword);
}, 300);
```

#### 6.2.2 结果缓存（5分钟）
```typescript
const searchCache = new Map<string, {
  data: SearchResultItem[];
  timestamp: number;
}>();

const CACHE_EXPIRE_TIME = 5 * 60 * 1000;
```

#### 6.2.3 虚拟滚动（超过50项启用）
```vue
<recycle-list
  v-if="searchResults.length > 50"
  :data="searchResults"
  :item-height="200"
>
  <!-- 卡片内容 -->
</recycle-list>
```

#### 6.2.4 图片懒加载
```vue
<image
  :src="cover_url"
  mode="aspectFill"
  lazy-load
  class="cover"
/>
```

---

## 第7章：测试与验收（Testing & Acceptance）

### 7.1 功能测试清单

#### 7.1.1 搜索前页面
- [ ] 热门搜索词正确显示（6个）
- [ ] 点击热门搜索执行搜索
- [ ] 搜索历史正确显示（最多10条）
- [ ] 点击搜索历史执行搜索
- [ ] 清空搜索历史功能正常
- [ ] 推荐直播间列表正确显示
- [ ] 推荐内容分页加载正常

#### 7.1.2 搜索结果页
- [ ] 搜索框显示当前关键词
- [ ] 可修改关键词重新搜索
- [ ] Tab切换功能正常
- [ ] 综合Tab显示混合结果
- [ ] 直播间Tab显示直播间卡片
- [ ] 专家Tab显示专家卡片
- [ ] 品牌Tab显示品牌卡片
- [ ] 空结果显示推荐内容
- [ ] 分页加载功能正常
- [ ] 卡片点击跳转正常

#### 7.1.3 性能测试
- [ ] 搜索防抖生效（300ms）
- [ ] 结果缓存生效（5分钟）
- [ ] 列表滚动流畅（60fps）
- [ ] 图片懒加载生效
- [ ] 无内存泄漏

### 7.2 兼容性测试

#### 7.2.1 平台兼容
- [ ] H5端功能正常
- [ ] Android App功能正常
- [ ] iOS App功能正常
- [ ] 微信小程序功能正常

#### 7.2.2 设备兼容
- [ ] iPhone SE（小屏）显示正常
- [ ] iPhone 14 Pro Max（大屏）显示正常
- [ ] Android中低端机型流畅运行
- [ ] iPad横屏显示正常

### 7.3 验收标准

#### 7.3.1 功能完整性
- ✅ 所有P0功能实现完整
- ✅ 所有交互符合设计规范
- ✅ 所有异常场景有友好提示

####7.3.2 性能指标
- ✅ 搜索响应时间 < 2秒
- ✅ 列表滚动帧率 ≥ 60fps
- ✅ 首屏加载时间 < 3秒
- ✅ 内存占用 < 200MB

#### 7.3.3 用户体验
- ✅ 所有文字清晰可读
- ✅ 所有按钮触控热区 ≥ 44x44px
- ✅ 所有加载状态有反馈
- ✅ 所有错误有友好提示

### 7.4 单元测试规范

#### 7.4.1 测试范围要求

**必须编写单元测试的代码**：

1. **所有工具函数**（`src/utils/`目录）
   - `search-history.ts`：getSearchHistory、addSearchHistory、clearSearchHistory
   - 覆盖率要求：≥ 90%

2. **Store的关键方法**（`src/store/modules/search.ts`）
   - `performSearch`：搜索执行逻辑
   - `loadMore`：分页加载逻辑
   - `switchTab`：Tab切换逻辑
   - 覆盖率要求：≥ 70%

3. **API封装函数**（`src/api/search.ts`）
   - 所有导出函数：globalSearch、searchByType、getHotSearches
   - 覆盖率要求：≥ 80%

#### 7.4.2 测试文件命名规范

```plaintext
src/
├── utils/
│   ├── search-history.ts
│   └── search-history.spec.ts       # 单元测试文件
├── store/
│   └── modules/
│       ├── search.ts
│       └── search.spec.ts           # Store测试文件
└── api/
    ├── search.ts
    └── search.spec.ts               # API测试文件
```

**命名规则**：
- 测试文件与源文件同目录
- 测试文件名：`{源文件名}.spec.ts` 或 `{源文件名}.test.ts`
- 推荐使用 `.spec.ts`（与Angular、NestJS等主流框架一致）

#### 7.4.3 测试示例

**工具函数测试示例**（`src/utils/search-history.spec.ts`）：

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from './search-history';

// Mock uni-app API
vi.mock('@dcloudio/uni-app', () => ({
  uni: {
    getStorageSync: vi.fn(),
    setStorageSync: vi.fn(),
    removeStorageSync: vi.fn()
  }
}));

describe('搜索历史管理', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  it('应该正确获取搜索历史', () => {
    const mockHistory = ['肝胆外科', '内镜手术'];
    uni.getStorageSync.mockReturnValue(mockHistory);
    
    const history = getSearchHistory();
    
    expect(history).toEqual(mockHistory);
    expect(uni.getStorageSync).toHaveBeenCalledWith('search_history');
  });
  
  it('应该正确添加搜索历史（去重）', () => {
    const existingHistory = ['内镜手术', '骨科培训'];
    uni.getStorageSync.mockReturnValue(existingHistory);
    
    addSearchHistory('内镜手术');
    
    // 应该将重复项移到最前面
    expect(uni.setStorageSync).toHaveBeenCalledWith(
      'search_history',
      ['内镜手术', '骨科培训']
    );
  });
  
  it('应该限制历史记录数量为10条', () => {
    const longHistory = Array.from({ length: 10 }, (_, i) => `关键词${i}`);
    uni.getStorageSync.mockReturnValue(longHistory);
    
    addSearchHistory('新关键词');
    
    const savedHistory = uni.setStorageSync.mock.calls[0][1];
    expect(savedHistory.length).toBe(10);
    expect(savedHistory[0]).toBe('新关键词');
  });
});
```

**Store测试示例**（`src/store/modules/search.spec.ts`）：

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useSearchStore } from './search';
import * as searchApi from '@/api/search';

// Mock API
vi.mock('@/api/search', () => ({
  globalSearch: vi.fn(),
  searchByType: vi.fn(),
  getHotSearches: vi.fn()
}));

describe('搜索Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });
  
  it('应该正确执行搜索', async () => {
    const store = useSearchStore();
    const mockResult = {
      data: {
        items: [{ id: '1', title: '测试直播间', type: 'room' }],
        total: 1
      }
    };
    
    vi.mocked(searchApi.globalSearch).mockResolvedValue(mockResult);
    
    await store.performSearch('测试关键词');
    
    expect(store.searchKeyword).toBe('测试关键词');
    expect(store.searchResults).toEqual(mockResult.data.items);
    expect(store.total).toBe(1);
  });
  
  it('应该正确处理搜索错误', async () => {
    const store = useSearchStore();
    const mockError = new Error('网络错误');
    
    vi.mocked(searchApi.globalSearch).mockRejectedValue(mockError);
    
    await store.performSearch('测试关键词');
    
    expect(store.error).toBe('网络错误');
    expect(store.searchResults).toEqual([]);
  });
});
```

#### 7.4.4 测试覆盖率要求

| 文件类型 | 最低覆盖率 | 推荐覆盖率 |
|---------|-----------|----------|
| 工具函数 | 90% | 95% |
| API封装 | 80% | 90% |
| Store | 70% | 80% |
| 组件 | 60% | 75% |

**检查命令**：
```bash
# 运行测试并生成覆盖率报告
pnpm test -- --coverage

# 查看覆盖率报告
open coverage/index.html
```

#### 7.4.5 测试最佳实践

1. **AAA模式**：Arrange（准备）、Act（执行）、Assert（断言）
2. **每个测试只测一个功能点**：测试用例职责单一
3. **使用描述性的测试名称**：`it('应该...', () => {})`
4. **Mock外部依赖**：uni-app API、网络请求等
5. **避免测试实现细节**：测试行为而非实现

---

## 第8章：开发检查清单（Development Checklist）

### 8.1 开发前检查
- [ ] 已读取所有必读文件
- [ ] 已扫描所有相关目录
- [ ] 已输出项目现状分析
- [ ] 已获得用户确认

### 8.2 开发中检查
- [ ] 严格遵循Design System规范
- [ ] 所有组件使用TypeScript
- [ ] 所有API调用有错误处理
- [ ] 所有状态变化有加载反馈
- [ ] 所有用户输入有校验

### 8.3 开发后检查
- [ ] 所有功能测试通过
- [ ] 所有兼容性测试通过
- [ ] 所有性能指标达标
- [ ] 代码已提交并通过Code Review
- [ ] 文档已更新

---

## 附录A：快速参考

### A.1 API速查表

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 热门搜索 | GET | `/api/v1/search/suggestions` | 获取热门搜索词 |
| 综合搜索 | GET | `/api/v1/search?q=关键词` | 混合搜索所有类型 |
| 分类搜索 | GET | `/api/v1/search?q=关键词&type=room` | 指定类型搜索 |
| 直播间推荐 | GET | `/api/v1/homepage/rooms` | 热门直播间 |
| 专家推荐 | GET | `/api/v1/experts` | 推荐专家 |
| 品牌推荐 | GET | `/api/v1/brands` | 推荐品牌 |

### A.2 图标引入方式

#### A.2.1 全局引入说明

图标字体已在 `App.vue` 中全局引入：

```vue
<style>
@import '@/static/fonts/iconfont.css';
</style>
```

#### A.2.2 使用方式

**方式1：使用class类名（推荐）**

```vue
<text class="iconfont icon-search"></text>
```

**方式2：使用Unicode编码**

```vue
<text class="iconfont">&#xe688;</text>
```

**方式3：使用font-family样式**

```vue
<text style="font-family: iconfont;">&#xe688;</text>
```

#### A.2.3 样式控制

```vue
<!-- 大小控制 -->
<text class="iconfont icon-search" style="font-size: 32rpx;"></text>

<!-- 颜色控制 -->
<text class="iconfont icon-search" style="color: #0F766E;"></text>

<!-- 组合使用 -->
<text class="iconfont icon-search" style="font-size: 32rpx; color: #667eea;"></text>
```

#### A.2.4 注意事项

- ✅ 所有图标类名统一前缀：`iconfont icon-`
- ✅ 图标大小通过 `font-size` 控制
- ✅ 图标颜色通过 `color` 控制
- ❌ 不要使用 `<i>` 标签（uni-app不支持）
- ❌ 不要在CSS中使用 `content` 属性插入图标

### A.3 图标速查表

| 图标类名 | 用途 | 图标类名 | 用途 |
|---------|------|---------|------|
| `icon-search` | 搜索 | `icon-close` | 关闭/清空 |
| `icon-star` | 收藏 | `icon-star-filled` | 已收藏 |
| `icon-heart` | 关注/喜欢 | `icon-heart-filled` | 已关注 |
| `icon-history` | 历史记录 | `icon-arrow-right` | 右箭头 |
| `icon-video` | 视频/直播 | `icon-eye` | 查看/观看 |

### A.4 颜色速查表

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 品牌主色 | `#0F766E` | Tab选中、关注按钮、焦点ring |
| 主文本 | `#1F2937` | 标题、正文 |
| 副文本 | `#6B7280` | 描述、职称 |
| 辅助文本 | `#9CA3AF` | 时间、医院 |
| 分割线 | `#F3F4F6` | 极浅，5-10%对比 |
| 直播中 | `#EF4444` | 红色状态标签 |
| 预告 | `#0F766E` | 品牌色状态标签 |
| 回放 | `#6B7280` | 灰色状态标签 |

---

## 结束语

本提示词文档提供了完整的搜索页面开发指导，涵盖了移动端开发的所有关键方面。请严格遵循文档中的规范和要求，确保代码质量和用户体验。

**记住三个核心原则**：
1. **移动优先**：所有设计从移动端场景出发
2. **性能优先**：防抖、缓存、懒加载、虚拟滚动
3. **安全第一**：XSS防护、数据脱敏、错误处理

祝开发顺利！🚀
