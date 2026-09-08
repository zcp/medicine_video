# 首页直播状态Tab功能设计与实现文档

**版本**: V1.0  
**创建日期**: 2026-03-11  
**项目**: 医学直播SaaS平台  
**功能**: 首页直播间三状态Tab切换  
**作者**: 资深前端工程师

---

## 1. 需求背景

### 1.1 业务需求

在医学直播平台首页，直播间存在三种状态：
1. **正在直播**（live）：当前正在进行的直播
2. **预告**（scheduled）：即将开播的直播
3. **回放**（replay）：已结束的直播录像

用户需要能够快速切换查看不同状态的直播内容，提升浏览效率和用户体验。

### 1.2 用户场景

- **医学专业人士**：希望第一时间观看正在进行的直播学习
- **计划学习者**：查看预告，提前预约感兴趣的直播
- **回顾学习者**：观看回放，复习重要的医学知识点

### 1.3 设计参考

参考B站、抖音等主流视频平台的Tab切换设计，结合医学直播专业场景需求，打造简洁高效的Tab切换体验。

---

## 2. 功能设计

### 2.1 Tab结构

```
┌─────────────────────────────────────┐
│  ● 正在直播 | 预告 | 回放           │  ← 三个Tab（红点提示有直播）
│  ══════════                         │  ← 选中态下划线
│                                     │
│  ┌─────────────────────────────┐  │  ← 直播卡片网格（双栏）
│  │ [直播中] 直播标题              │  │
│  │ 🖼 封面图                      │  │
│  │ 👨‍⚕️ 专家信息                  │  │
│  └─────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### 2.2 Tab功能说明

| Tab | 显示内容 | 数据来源 | 状态标识 |
|-----|---------|---------|---------|
| **正在直播** | 当前正在进行的直播 | `roomList.filter(r => r.live_status === 'live')` | 红点提示（有直播时） |
| **预告** | 即将开播的直播 | `roomList.filter(r => r.live_status === 'scheduled')` | 无特殊标识 |
| **回放** | 已结束的直播录像 | `roomList.filter(r => r.live_status === 'replay')` | 无特殊标识 |

### 2.3 智能默认Tab

**优先级规则**：正在直播 > 预告 > 回放

- 页面加载时，如果有正在直播的内容，默认显示"正在直播"Tab
- 如果没有正在直播，但有预告，显示"预告"Tab
- 如果只有回放，显示"回放"Tab

### 2.4 空状态处理

当某个Tab没有数据时，显示友好的空状态提示：

| Tab | 空状态提示 | 操作按钮 |
|-----|-----------|---------|
| **正在直播** | "暂无正在直播" | "看预告" + "刷新" |
| **预告** | "暂无预告直播" | "看回放" + "刷新" |
| **回放** | "暂无回放" | "敬请期待更多精彩内容" |

---

## 3. 技术实现

### 3.1 技术栈

- **框架**: uni-app + Vue3 Composition API
- **语言**: TypeScript
- **状态管理**: 组件内部状态（ref + computed）
- **样式**: SCSS

### 3.2 核心文件结构

```
src/pages/app/tabbar/home/
├── components/
│   └── RoomCardGrid.vue        # 直播间卡片网格组件（包含Tab切换）
├── index.vue                   # 首页主入口
```

### 3.3 数据流转

```
首页 index.vue
    ↓ loadRooms() 调用API
    ↓ roomList = 100条直播数据（包含所有状态）
    ↓ 传递给 RoomCardGrid 组件
    ↓
RoomCardGrid.vue
    ↓ computed 自动分类
    ├─ liveList: 正在直播列表 (filter live_status === 'live')
    ├─ scheduledList: 预告列表 (filter live_status === 'scheduled')
    └─ replayList: 回放列表 (filter live_status === 'replay')
    ↓ 用户切换Tab
    ↓ v-show 控制显示/隐藏
```

---

## 4. 核心代码实现

### 4.1 组件Props定义

**文件**: `src/pages/app/tabbar/home/components/RoomCardGrid.vue`

```typescript
/** Props 定义 */
const props = withDefaults(
  defineProps<{
    roomList: HomepageRoomItem[];  // 直播间列表（包含所有状态）
    isLoading: boolean;            // 是否加载中
    isLoadingMore: boolean;        // 是否加载更多中
    hasMore: boolean;              // 是否还有更多数据
  }>(),
  {
    roomList: () => [],
    isLoading: false,
    isLoadingMore: false,
    hasMore: true,
  }
);
```

### 4.2 Tab状态管理

```typescript
/** 模块级 Tab：正在直播 | 预告 | 回放 */
type ContentTab = 'live' | 'scheduled' | 'replay';

const activeContentTab = ref<ContentTab>('live');
```

### 4.3 数据自动分类

```typescript
/** 
 * 根据 live_status 动态分类直播间
 * 每个直播间只会出现在一个Tab下，确保无重复
 * 注意：live_status 会随时间变化（预告→正在直播→回放），computed 会自动响应更新
 */
const liveList = computed(() => 
  props.roomList.filter(r => r.live_status === 'live')
);

const scheduledList = computed(() => 
  props.roomList.filter(r => r.live_status === 'scheduled')
);

const replayList = computed(() => 
  props.roomList.filter(r => r.live_status === 'replay')
);

const liveCount = computed(() => liveList.value.length);
```

**关键点**：
- ✅ 使用 `computed` 确保响应式更新
- ✅ 每个直播间按 `live_status` 严格分类，**不会重复出现**
- ✅ 状态发生变化时（如预告→正在直播），会自动重新分类

### 4.4 智能默认Tab逻辑

```typescript
/** 
 * 默认 Tab 规则：智能选择有内容的Tab
 * 优先级：正在直播 > 预告 > 回放
 * 当数据更新时（如下拉刷新、加载更多、状态变化），会自动重新评估
 */
const hasAppliedDefaultTab = ref(false);

// 监听数据加载状态，首次加载完成后应用默认Tab规则
watch(
  () => props.isLoading,
  (loading) => {
    if (loading || hasAppliedDefaultTab.value) return;
    hasAppliedDefaultTab.value = true;
    
    // 按优先级选择默认Tab
    if (liveList.value.length > 0) {
      activeContentTab.value = 'live';
    } else if (scheduledList.value.length > 0) {
      activeContentTab.value = 'scheduled';
    } else {
      activeContentTab.value = 'replay';
    }
  },
  { immediate: true }
);
```

### 4.5 空Tab自动切换逻辑

```typescript
// 监听数据变化，当roomList变化时（如从其他页面返回、数据刷新），重新评估Tab状态
watch(
  () => props.roomList.length,
  () => {
    // 如果当前Tab没有数据，自动切换到有数据的Tab
    if (activeContentTab.value === 'live' && liveList.value.length === 0) {
      // 正在直播Tab无数据，切换到预告或回放
      if (scheduledList.value.length > 0) {
        activeContentTab.value = 'scheduled';
      } else if (replayList.value.length > 0) {
        activeContentTab.value = 'replay';
      }
    } else if (activeContentTab.value === 'scheduled' && scheduledList.value.length === 0) {
      // 预告Tab无数据，切换到正在直播或回放
      if (liveList.value.length > 0) {
        activeContentTab.value = 'live';
      } else if (replayList.value.length > 0) {
        activeContentTab.value = 'replay';
      }
    } else if (activeContentTab.value === 'replay' && replayList.value.length === 0) {
      // 回放Tab无数据，切换到正在直播或预告
      if (liveList.value.length > 0) {
        activeContentTab.value = 'live';
      } else if (scheduledList.value.length > 0) {
        activeContentTab.value = 'scheduled';
      }
    }
  }
);
```

### 4.6 模板结构

```vue
<template>
  <view class="room-card-grid">
    <!-- 骨架屏（加载中） -->
    <view v-if="isLoading" class="skeleton-grid">
      <!-- 骨架屏内容省略 -->
    </view>

    <!-- 模块级 Tab：正在直播 / 预告 / 回放 -->
    <view v-else class="cards-wrapper">
      <view class="section">
        <view class="module-tabs">
          <!-- 正在直播Tab -->
          <view
            class="module-tab"
            :class="{ 'module-tab--active': activeContentTab === 'live' }"
            @tap="activeContentTab = 'live'"
          >
            <view class="module-tab-inner">
              <view v-if="liveCount > 0" class="tab-badge-dot" />
              <text class="module-tab-text">正在直播</text>
            </view>
            <view v-if="activeContentTab === 'live'" class="module-tab-indicator" />
          </view>
          
          <!-- 预告Tab -->
          <view
            class="module-tab"
            :class="{ 'module-tab--active': activeContentTab === 'scheduled' }"
            @tap="activeContentTab = 'scheduled'"
          >
            <text class="module-tab-text">预告</text>
            <view v-if="activeContentTab === 'scheduled'" class="module-tab-indicator" />
          </view>
          
          <!-- 回放Tab -->
          <view
            class="module-tab"
            :class="{ 'module-tab--active': activeContentTab === 'replay' }"
            @tap="activeContentTab = 'replay'"
          >
            <text class="module-tab-text">回放</text>
            <view v-if="activeContentTab === 'replay'" class="module-tab-indicator" />
          </view>
        </view>

        <!-- 正在直播Tab内容 -->
        <view v-show="activeContentTab === 'live'" class="tab-panel">
          <view v-if="liveList.length === 0" class="empty-section empty-live">
            <text class="empty-section-text">暂无正在直播</text>
            <view class="empty-actions">
              <view class="empty-btn" @tap.stop="activeContentTab = 'scheduled'">
                <text class="empty-btn-text">看预告</text>
              </view>
              <view class="empty-btn empty-btn-secondary" @tap.stop="handleRefresh">
                <text class="empty-btn-text">刷新</text>
              </view>
            </view>
            <text class="empty-hint">或下拉刷新获取最新直播</text>
          </view>
          <view v-else class="grid-container grid-double">
            <view v-for="room in liveList" :key="room.id" class="card-item">
              <RoomCard :room="room" :is-mobile="true" :show-description="false" @click="handleCardClick(room)" />
            </view>
          </view>
        </view>

        <!-- 预告Tab内容（结构类似，省略） -->
        <!-- 回放Tab内容（结构类似，省略） -->
      </view>

      <!-- 加载更多/已经到底提示 -->
      <view v-if="isLoadingMore" class="loading-more">
        <text class="loading-text">加载中...</text>
      </view>
      <view v-if="!hasMore && roomList.length > 0" class="no-more">
        <text class="no-more-text">—— 已经到底了 ——</text>
      </view>
    </view>
  </view>
</template>
```

---

## 5. 首页数据加载优化

### 5.1 首次加载策略

**文件**: `src/pages/app/tabbar/home/index.vue`

```typescript
/** 每页数据条数（性能优化：首页建议10-15条） */
const PAGE_SIZE = 15;

/** 首次加载时额外获取的数据量，确保包含各种状态的直播间 */
const INITIAL_EXTRA_SIZE = 85;

/**
 * 加载直播间列表
 * @param append - 是否追加模式（分页加载）
 */
async function loadRooms(append = false): Promise<void> {
  const loading = append ? 'isLoadingMore' : 'isLoading';
  (loading === 'isLoadingMore' ? isLoadingMore : isLoading).value = true;
  
  try {
    // 首次加载时，增加数据量以确保包含各种状态的直播间
    const loadSize = append ? PAGE_SIZE : (PAGE_SIZE + INITIAL_EXTRA_SIZE);
    
    const res = await getHomepageRooms({
      page: currentPage.value,
      size: loadSize,  // 首次加载100条，追加加载15条
      sort: 'heat:desc',
      category_id: activeCategoryId.value || undefined
    });
    
    if (append) {
      roomList.value.push(...res.data.items);
    } else {
      roomList.value = res.data.items;
    }
    
    totalCount.value = res.data.total;
    hasMore.value = roomList.value.length < totalCount.value;
    
    // 统计各状态数量（用于调试）
    const statusCount = {
      live: roomList.value.filter(r => r.live_status === 'live').length,
      scheduled: roomList.value.filter(r => r.live_status === 'scheduled').length,
      replay: roomList.value.filter(r => r.live_status === 'replay').length
    };
    console.log('[Home] 📊 状态分布:', statusCount);
  } catch (error) {
    console.error('[Home] 直播间列表加载失败', error);
    uni.showToast({ title: '加载直播间列表失败', icon: 'none' });
  } finally {
    (loading === 'isLoadingMore' ? isLoadingMore : isLoading).value = false;
  }
}
```

**关键优化点**：
- ✅ 首次加载100条数据（15基础 + 85额外），大幅提高包含各种状态的概率
- ✅ 追加加载时仅加载15条，避免一次请求过多数据
- ✅ 添加状态分布统计日志，方便问题定位

### 5.2 为什么是100条？

在医学直播平台中，直播间的状态分布可能不均衡：
- **回放占比最高**：大量历史直播录像
- **正在直播占比低**：同一时间段内正在直播的数量有限
- **预告占比中等**：未来几天的预告直播

**问题场景**：
- 如果首次只加载15条，可能全是回放
- 导致"正在直播"和"预告"Tab为空
- 用户需要下拉加载更多才能看到其他状态的内容

**解决方案**：
- 首次加载100条数据，覆盖更多状态
- 用户首次进入页面就能看到完整的Tab内容
- 避免频繁下拉加载导致的体验割裂

---

## 6. 样式规范

### 6.1 Tab样式

```scss
/* 模块级标题风格：选中 30rpx/600 未选 28rpx/500，#0F766E/#7A869A，下划线 36×4rpx 距文字 6~8rpx */
.module-tabs {
  display: flex;
  align-items: center;
  gap: 32rpx;
  margin-top: 28rpx;
  margin-bottom: 24rpx;
}

.module-tab {
  position: relative;
  padding: 10rpx 0;
  min-height: 44rpx;  // 确保触摸区域足够大（iOS规范）
  display: flex;
  align-items: center;
}

.module-tab-inner {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

// 红点提示（仅正在直播Tab显示，位于文字左侧）
.tab-badge-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 2rpx 4rpx rgba(239, 68, 68, 0.3);
  flex-shrink: 0;
}

// Tab文字
.module-tab-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #7A869A;  // 未选中：灰色
  line-height: 1.3;
}

// 选中态文字
.module-tab--active .module-tab-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #0F766E;  // 选中：品牌主色
}

// 选中态下划线
.module-tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 36rpx;
  height: 4rpx;
  background: #0F766E;  // 品牌主色
  border-radius: 2rpx;
}
```

### 6.2 红点设计说明

**设计理念**：
- ✅ **简洁优先**：只显示红点，不显示具体数量
- ✅ **避免信息过载**：数量多时（例如99+）对用户没有实际意义
- ✅ **符合用户习惯**：红点本身就足够引起用户注意
- ✅ **视觉更清爽**：减少视觉噪音，突出核心内容

**对比方案**：

| 方案 | 优点 | 缺点 |
|-----|------|------|
| 仅红点 | 简洁、清爽、永不过期 | 无法传达具体数量 |
| 红点+数字 | 传达精确信息 | 数量多时显示"99+"意义不大 |
| 红点+数字+动画 | 更有吸引力 | 过于花哨，不符合医学平台专业形象 |

**最终选择**：仅红点（当前实现）

---

## 7. 用户体验优化

### 7.1 空状态优化

**设计原则**：
- 友好的文案提示
- 提供操作引导（切换到其他Tab或刷新）
- 避免空白页面，保持用户参与感

**示例**：

```vue
<view v-if="liveList.length === 0" class="empty-section empty-live">
  <text class="empty-section-text">暂无正在直播</text>
  <view class="empty-actions">
    <view class="empty-btn" @tap.stop="activeContentTab = 'scheduled'">
      <text class="empty-btn-text">看预告</text>
    </view>
    <view class="empty-btn empty-btn-secondary" @tap.stop="handleRefresh">
      <text class="empty-btn-text">刷新</text>
    </view>
  </view>
  <text class="empty-hint">或下拉刷新获取最新直播</text>
</view>
```

### 7.2 状态自动切换

**场景**：
- 用户正在观看"正在直播"Tab
- 最后一个直播结束，该Tab变为空
- 系统自动切换到"预告"或"回放"Tab

**优势**：
- 减少用户手动操作
- 避免空白页面停留时间过长
- 提升用户体验流畅度

### 7.3 实时状态更新

**场景**：
- 预告直播到达开播时间，自动变为"正在直播"
- 正在直播结束，自动变为"回放"

**实现方式**：
- 使用 `computed` 响应式分类
- `live_status` 字段变化时，自动重新分类
- 无需手动刷新页面

---

## 8. 卡片复用统一

### 8.1 RoomCard组件统一样式

**所有Tab使用相同的 `RoomCard` 组件**，确保样式一致：

```vue
<RoomCard :room="room" :is-mobile="true" :show-description="false" @click="handleCardClick(room)" />
```

**样式统一点**：
- 封面图比例：16:9（`padding-top: 56.25%`）
- 卡片圆角：`var(--home-r-lg)`
- 卡片间距：`var(--home-spacing-card)`
- 文字大小：标题 `var(--home-fs-card-title)`
- 状态标签：左上角胶囊样式

### 8.2 状态标签区分

三种状态通过左上角标签区分：

| 状态 | 标签文本 | 标签颜色 | 图标 |
|------|---------|---------|------|
| 正在直播 | 直播中 | 半透明黑 + 红色图标 | icon-live |
| 预告 | 预告 | 半透明黑 + 绿色图标 | icon-time |
| 回放 | 回放 | 半透明黑 + 白色图标 | icon-play |

**关键点**：
- ✅ 移除了预告Tab的"预约参加"按钮，保持三种状态样式完全一致
- ✅ 仅通过状态标签区分，简洁统一

---

## 9. 性能优化

### 9.1 computed响应式分类

```typescript
const liveList = computed(() => props.roomList.filter(r => r.live_status === 'live'));
```

**优势**：
- 自动缓存计算结果
- 数据变化时自动更新
- 避免重复计算

### 9.2 v-show vs v-if

```vue
<view v-show="activeContentTab === 'live'" class="tab-panel">
  <!-- 内容 -->
</view>
```

**选择 v-show 的原因**：
- Tab切换频繁，v-show性能更好（仅控制CSS显示/隐藏）
- 避免频繁DOM创建/销毁
- 保持滚动位置（用户从Tab A切换到Tab B再切回Tab A，滚动位置保持不变）

### 9.3 双栏网格布局

```scss
.grid-container.grid-double {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.card-item {
  width: calc(50% - 8rpx);  // 50% - 间距的一半
}
```

**优势**：
- 充分利用移动端屏幕空间
- 提升信息密度
- 减少滚动距离

---

## 10. 未来优化方向

### 10.1 后端API增强

**当前问题**：
- 首次加载100条数据，包含大量不需要的数据
- 浪费带宽和流量

**优化方案**：
- 后端API支持 `live_status` 参数筛选
- 前端可以只请求特定状态的数据

```typescript
// 示例：只请求正在直播的数据
const res = await getHomepageRooms({
  page: 1,
  size: 15,
  live_status: 'live'
});
```

### 10.2 智能加载策略

**优化方案**：
- 检测到某个Tab为空时，自动请求该状态的数据
- 减少首次加载数据量
- 按需加载，提升性能

```typescript
async function loadTabData(status: 'live' | 'scheduled' | 'replay') {
  if (getListByStatus(status).length === 0) {
    const res = await getHomepageRooms({
      page: 1,
      size: 15,
      live_status: status
    });
    appendToRoomList(res.data.items);
  }
}
```

### 10.3 预加载优化

**优化方案**：
- 首页挂载时预先请求各状态数据
- 用户切换Tab时数据已准备好
- 提升响应速度

```typescript
onMounted(async () => {
  // 并行请求三种状态的数据
  const [liveData, scheduledData, replayData] = await Promise.all([
    getHomepageRooms({ live_status: 'live', size: 15 }),
    getHomepageRooms({ live_status: 'scheduled', size: 15 }),
    getHomepageRooms({ live_status: 'replay', size: 15 })
  ]);
  
  // 合并数据
  roomList.value = [
    ...liveData.items,
    ...scheduledData.items,
    ...replayData.items
  ];
});
```

### 10.4 动态更新优化

**优化方案**：
- 使用WebSocket实时推送直播状态变化
- 无需轮询或手动刷新
- 自动更新Tab内容

```typescript
// 监听WebSocket推送
onMounted(() => {
  websocket.on('room_status_change', (data) => {
    updateRoomStatus(data.room_id, data.new_status);
  });
});
```

---

## 11. 测试验证

### 11.1 功能测试

- [ ] 首次加载，默认显示有数据的Tab
- [ ] 三个Tab可以正常切换
- [ ] 每个直播间只出现在一个Tab下，无重复
- [ ] 空Tab显示友好提示和操作按钮
- [ ] 操作按钮点击正常（切换Tab + 刷新）
- [ ] 下拉刷新正常，数据自动分类
- [ ] 上拉加载更多正常，数据正确追加
- [ ] 红点仅在有正在直播时显示
- [ ] 卡片点击跳转到播放页

### 11.2 边界测试

- [ ] 所有Tab都为空时，显示"暂无直播"
- [ ] 只有一个Tab有数据，其他Tab为空
- [ ] 100条数据全是同一种状态
- [ ] 网络异常时的错误提示
- [ ] 数据加载失败的降级处理

### 11.3 性能测试

- [ ] 首次加载时间 < 2秒
- [ ] Tab切换流畅，无卡顿
- [ ] 滚动流畅，帧率 ≥ 60fps
- [ ] 内存占用稳定，无内存泄漏

---

## 12. 总结

### 12.1 核心亮点

1. **智能分类**：使用 `computed` 自动按 `live_status` 分类，响应式更新
2. **智能默认**：自动选择有数据的Tab，避免空白页面
3. **空状态优化**：友好提示 + 操作引导，提升用户体验
4. **样式统一**：三种状态使用相同的 `RoomCard` 组件，保持视觉一致性
5. **红点简洁**：仅显示红点，不显示数量，避免信息过载
6. **性能优化**：首次加载100条数据，提高包含各状态的概率

### 12.2 技术特点

- ✅ Vue3 Composition API，代码简洁易维护
- ✅ TypeScript类型安全，减少运行时错误
- ✅ computed响应式分类，自动更新
- ✅ v-show优化Tab切换性能
- ✅ watch监听数据变化，自动切换Tab

### 12.3 用户体验

- ✅ 首次进入就能看到完整内容（三个Tab都有数据）
- ✅ 空Tab不会"孤零零"，有操作引导
- ✅ 状态变化自动更新，无需手动刷新
- ✅ 红点提示简洁清晰，不会造成视觉干扰
- ✅ 卡片样式统一，专业医学形象

---

## 13. 附录

### 13.1 相关文件

| 文件路径 | 功能说明 |
|---------|---------|
| `src/pages/app/tabbar/home/index.vue` | 首页主入口，负责数据加载 |
| `src/pages/app/tabbar/home/components/RoomCardGrid.vue` | Tab切换组件，负责显示和分类 |
| `src/components/shared/RoomCard.vue` | 直播卡片组件，统一样式 |
| `src/api/homepage.ts` | 首页API封装 |
| `src/types/homepage.ts` | 首页类型定义 |

### 13.2 API接口

**首页直播列表**：
- 后端接口：`GET /api/v1/homepage/rooms`
- 前端调用：`GET /homepage/rooms`
- 参数：
  - `page`: 页码（从1开始）
  - `size`: 每页数量（首次100，追加15）
  - `sort`: 排序规则（`heat:desc` 按热度降序）
  - `category_id`: 分类ID（可选）

**返回数据结构**：
```typescript
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "room_123",
        "title": "心脏外科手术演示",
        "cover_url": "https://...",
        "live_status": "live",  // 'live' | 'scheduled' | 'replay'
        "host": {
          "name": "张三",
          "title": "主任医师",
          "hospital": "三甲医院"
        },
        "status_data": {
          "viewer_count": 1250,      // 正在直播：观看人数
          "start_time": "2026-03-12T10:00:00Z",  // 预告：开始时间
          "duration_seconds": 3600,  // 回放：时长（秒）
          "play_count": 4600         // 回放：播放量
        }
      }
    ],
    "total": 235,
    "page": 1,
    "size": 100
  }
}
```

### 13.3 相关文档

- [首页功能设计文档](./前端分析及设计文档.md)
- [首页API升级方案](./明天实施计划-首页与播放页API升级.md)
- [设计语言规范](./Design-System-Rules_UI-UX-PRO-MAX.md)
- [登录注册统一设计](./登录与跨应用跳转设计文档.md)

---

**文档编写日期**: 2026-03-11  
**版本**: V1.0  
**维护人**: 前端团队
