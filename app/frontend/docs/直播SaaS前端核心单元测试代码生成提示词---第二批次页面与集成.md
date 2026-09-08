# 直播SaaS前端核心单元测试代码生成提示词---第二批次页面与集成

---

## 1. 角色定义 (Role Definition)

你是一名资深前端工程师，精通 Vue3、TypeScript、Pinia、uni-app 生态，擅长页面级集成测试和组件交互测试。你将为 frontend_live/src/pages/ 下的核心页面编写高质量、可维护的集成测试代码，采用 Vitest + @vue/test-utils + TypeScript，重点测试页面与 store、API、组件之间的集成交互，所有测试严格遵循 AAA（Arrange-Act-Assert）模式，保证每个测试用例独立、隔离。

---

## 2. 任务目标 (Task Objective)

你的目标是为以下页面生成完整的集成测试代码：
- `src/pages/room/RoomList.vue` - 房间列表页面
- `src/pages/room/RoomDetail.vue` - 房间详情页面  
- `src/pages/live/LiveView.vue` - 直播观看页面
- `src/pages/common/NotFound.vue` - 404页面

每个测试文件需覆盖页面渲染、用户交互、store集成、API调用、路由跳转、生命周期钩子等核心功能，所有测试用例需独立、mock 所有外部依赖。

---

## 3. 核心上下文信息 (Core Context Information)

### 3.1. Testing Strategy
- **页面渲染**：测试页面正常渲染、加载状态、错误状态、空状态
- **用户交互**：测试按钮点击、表单提交、模态框操作、列表操作
- **Store 集成**：测试页面与 Pinia store 的数据绑定和状态管理
- **API 集成**：测试页面触发的 API 调用和响应处理
- **路由跳转**：测试页面间的导航和参数传递
- **生命周期**：测试 onLoad、onPullDownRefresh、onReachBottom 等钩子
- **组件集成**：测试页面内组件的交互和事件传递
- 所有测试用例必须严格遵循 AAA（Arrange-Act-Assert）三段式结构
- 每个测试用例必须独立，不能依赖其它测试副作用
- 所有 mock、全局变量、定时器等必须在每个测试后清理，保证隔离

### 3.2. Testing Environment Setup
- 使用 Vitest 作为测试运行器，@vue/test-utils 进行组件挂载
- 使用 createTestingPinia 进行 store 测试
- 所有 API 请求、uni-app API、路由跳转需用 vi.mock/vi.fn mock 掉
- 测试文件命名为 xxx.spec.ts，与被测页面同名，存放于 tests/pages/ 目录下

### 3.3. Project Structure
```
frontend_live/
├── src/
│   ├── pages/
│   │   ├── room/
│   │   │   ├── RoomList.vue
│   │   │   └── RoomDetail.vue
│   │   ├── live/
│   │   │   └── LiveView.vue
│   │   ├── common/
│   │       └── NotFound.vue
│   ├── components/
│   │   ├── AppButton.vue
│   │   ├── ModalDialog.vue
│   │   ├── RoomCard.vue
│   │   └── VideoPlayer.vue
│   ├── store/
│   │   ├── room.ts
│   │   └── session.ts
│   └── api/
│       ├── room.ts
│       └── session.ts
└── tests/
    └── pages/  # 页面测试文件存放目录
```
**已存在的代码全文 (Full Text of Existing Code)**
*You must generate tests based on the logic within the following application code.*

* **已存在的代码**:
    * `/src/pages/room/RoomList.vue`
    * `/src/pages/room/RoomDetail.vue`
    * `/src/pages/room/live/LiveView.vue`
    * `/src/pages/room/common/NotFound.vue`     

# 3.4. 页面功能概览

#### 3.4.1. RoomList.vue (房间列表页)
**核心功能**：
- 房间列表展示和分页加载
- 房间创建、编辑、删除操作
- 场次创建功能
- 下拉刷新和上拉加载更多
- 路由跳转到房间详情页

**/src/pages/room/RoomList.vue**参考代码示例
```python
<template>
  <view class="room-list-page">
    <view class="page-title fade-in">直播房间列表</view>
    <view class="content-container">
      <view class="accordion-list">
        <view v-for="room in mainRooms" :key="room.id" class="room-item">
          <!-- 房间行 - 可点击跳转到详情页 -->
          <view class="room-header" @click="goToRoomDetail(room.id)">
            <span class="room-title" v-html="safeRoomTitle(room)"></span>
            <view class="room-actions" @click.stop>
              <AppButton type="default" size="small" @click="openEditModal(room)">编辑</AppButton>
              <AppButton type="danger" size="small" @click="confirmDelete(room)">删除</AppButton>
              <AppButton type="primary" size="small" @click="goToRoomDetail(room.id)">查看详情</AppButton>
            </view>
          </view>
          <!-- 房间简介（如有） -->
          <view v-if="room.description" style="margin-left: 32px; margin-bottom: 8px;">
            <span style="color: #888; font-size: 14px;" v-html="safeRoomDescription(room)"></span>
          </view>
        </view>
      </view>
    </view>
    <view class="fab-container">
      <AppButton type="primary" size="large" @click="openCreateModal">+</AppButton>
    </view>
    <ModalDialog
      :visible="isModalVisible"
      :title="modalTitle"
      :confirmText="modalConfirmText"
      :confirmLoading="isSubmitting"
      @update:visible="isModalVisible = $event"
      @confirm="handleConfirm"
      @cancel="closeModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">房间标题 <text class="required">*</text></text>
          <input 
            class="form-input" 
            v-model="formModel.title" 
            placeholder="请输入房间标题" 
            :class="{ 'input-error': titleError }"
          />
          <text v-if="titleError" class="form-error">{{ titleError }}</text>
        </view>
        <view class="form-group">
          <text class="form-label">房间简介</text>
          <textarea 
            class="form-textarea" 
            v-model="formModel.description" 
            placeholder="请输入房间简介（选填）" 
            :class="{ 'input-error': descriptionError }"
          />
          <text v-if="descriptionError" class="form-error">{{ descriptionError }}</text>
        </view>
      </view>
    </ModalDialog>
    <ModalDialog
      :visible="isSessionModalVisible"
      title="新增场次"
      confirmText="立即创建"
      :confirmLoading="isSessionSubmitting"
      @update:visible="isSessionModalVisible = $event"
      @confirm="handleCreateSession"
      @cancel="closeSessionModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">开始时间 <text class="required">*</text></text>
          <input 
            class="form-input" 
            v-model="sessionFormModel.start_time" 
            placeholder="请输入开始时间，如 2025-07-23 10:00" 
            :class="{ 'input-error': startTimeError }"
          />
          <text v-if="startTimeError" class="form-error">{{ startTimeError }}</text>
        </view>
        <view class="form-group">
          <text class="form-label">结束时间</text>
          <input 
            class="form-input" 
            v-model="sessionFormModel.end_time" 
            placeholder="请输入结束时间，如 2025-07-23 12:00" 
            :class="{ 'input-error': endTimeError }"
          />
          <text v-if="endTimeError" class="form-error">{{ endTimeError }}</text>
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useRoomStore } from '../../store/room';
import RoomCard from '../../components/RoomCard.vue';
import AppButton from '../../components/AppButton.vue';
import ModalDialog from '../../components/ModalDialog.vue';
import { ref, reactive, computed } from 'vue';
import type{ Room } from '../../types/room';
import { escapeHtml } from '@/utils/xss';


// 计算属性：只显示主会场（没有 parent_room_id 的房间）
const mainRooms = computed(() => {
  return rooms.value.filter(room => !room.parent_room_id);
});
// XSS防护：安全渲染房间标题和简介
const safeRoomTitle = (room: Room) => escapeHtml(room.title);
const safeRoomDescription = (room: Room) => escapeHtml(room.description || '');

// 1. Store 和数据
const roomStore = useRoomStore();
const { rooms, loading, error, pagination } = storeToRefs(roomStore);

// 跳转到房间详情页
const goToRoomDetail = (roomId: string) => {
  uni.navigateTo({ url: `/pages/room/RoomDetail?id=${roomId}` });
};

const retryFetch = () => {
  roomStore.fetchRooms({ refresh: true });
};


// 模态框与表单逻辑 (重构以支持创建和编辑)
const isModalVisible = ref(false);
const isSubmitting = ref(false); // 通用的提交状态
const isEditMode = ref(false);

// 错误状态管理
const titleError = ref('');
const descriptionError = ref('');

const formModel = reactive({
  id: null as string | null,
  title: '',
  description: ''
});

// 用于比较，判断哪些字段被修改了
const originalRoomData = reactive({
  title: '',
  description: ''
});

// 计算属性动态改变模态框
const modalTitle = computed(() => isEditMode.value ? '编辑房间' : '创建新房间');
const modalConfirmText = computed(() => isEditMode.value ? '保存更改' : '立即创建');

// 清除错误状态
const clearErrors = () => {
  titleError.value = '';
  descriptionError.value = '';
};

// 表单验证
const validateForm = () => {
  clearErrors();
  let isValid = true;

  // 验证标题
  if (!formModel.title.trim()) {
    titleError.value = '房间标题不能为空';
    isValid = false;
  } else if (formModel.title.trim().length < 2) {
    titleError.value = '房间标题至少需要2个字符';
    isValid = false;
  } else if (formModel.title.trim().length > 50) {
    titleError.value = '房间标题不能超过50个字符';
    isValid = false;
  }

  // 验证简介（可选）
  if (formModel.description && formModel.description.length > 200) {
    descriptionError.value = '房间简介不能超过200个字符';
    isValid = false;
  }

  return isValid;
};

const openCreateModal = () => {
  isEditMode.value = false;
  // 重置表单
  formModel.id = null;
  formModel.title = '';
  formModel.description = '';
  clearErrors();
  isModalVisible.value = true;
};

const openEditModal = async (room: Room) => {
  uni.showLoading({ title: '加载中...', mask: true });
  try {
    await roomStore.fetchRoomById(room.id);
    if (roomStore.currentRoom) {
      isEditMode.value = true;
      // 填充表单模型和原始数据模型
      formModel.id = roomStore.currentRoom.id;
      formModel.title = roomStore.currentRoom.title;
      formModel.description = roomStore.currentRoom.description || '';
      
      originalRoomData.title = roomStore.currentRoom.title;
      originalRoomData.description = roomStore.currentRoom.description || '';
      
      clearErrors();
      isModalVisible.value = true;
    } else {
      throw new Error('未能获取房间详情');
    }
  } catch (e: any) {
    uni.showToast({ title: `获取房间信息失败: ${e.message || '请重试'}`, icon: 'none' });
  } finally {
    uni.hideLoading();
  }
};

const closeModal = () => {
  isModalVisible.value = false;
  clearErrors();
};

const handleConfirm = () => {
  if (isEditMode.value) {
    handleUpdateRoom();
  } else {
    handleCreateRoom();
  }
};

// 3. CRUD 操作
const handleCreateRoom = async () => {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  try {
    await roomStore.addNewRoom({
      title: formModel.title.trim(),
      description: formModel.description.trim(),
      // 确保创建的是主会场（不设置 parent_room_id）
    });
    await roomStore.fetchRooms({ refresh: true });
    uni.showToast({ title: '创建成功', icon: 'success' });
    closeModal();
  } catch (e: any) {
    uni.showToast({ title: `创建失败: ${e.message || '请重试'}`, icon: 'none' });
  } finally {
    isSubmitting.value = false;
  }
};

const handleUpdateRoom = async () => {
  if (!validateForm()) {
    return;
  }
  
  if (!formModel.id) return;

  // 1. 构建只包含已修改字段的 payload
  const payload: Partial<Room> = {};
  if (formModel.title.trim() !== originalRoomData.title) {
    payload.title = formModel.title.trim();
  }
  if (formModel.description.trim() !== originalRoomData.description) {
    payload.description = formModel.description.trim();
  }

  // 2. 如果没有任何修改，则直接提示成功并关闭
  if (Object.keys(payload).length === 0) {
    closeModal();
    uni.showToast({ title: '没有检测到任何更改', icon: 'none' });
    return;
  }

  isSubmitting.value = true;
  try {
    await roomStore.updateRoom(formModel.id, payload);
    // 操作成功后，先关闭模态框，再刷新列表
    closeModal();
    await roomStore.fetchRooms({ refresh: true });
    uni.showToast({ title: '更新成功', icon: 'success' });
  } catch (e: any) {
    uni.showToast({ title: `更新失败: ${e.message || '请重试'}`, icon: 'none' });
  } finally {
    isSubmitting.value = false;
  }
};

const confirmDelete = async (room: Room) => {
  console.log("a")
  uni.showLoading({ title: '检查中...', mask: true });
  console.log("aa")
  try {
    console.log("aaa")
    const hasSessions = await roomStore.checkRoomHasSessions(room.id);
    console.log("aaaa")
    uni.hideLoading();

    if (hasSessions) {
      console.log("11")
      uni.showModal({
        title: '无法删除',
        content: '该房间下仍有关联的直播场次，请先清空场次后再尝试删除。',
        showCancel: false,
      });
    } else {
      console.log("12")
      uni.showModal({
        title: '确认删除',
        content: `您确定要删除房间"${room.title}"吗？此操作无法撤销。`,
        success: (res) => {
          if (res.confirm) {
            handleDeleteRoom(room.id);
          }
        },
      });
    }
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: '检查失败，请重试', icon: 'none' });
  }
};

const handleDeleteRoom = async (roomId: string) => {
  uni.showLoading({ title: '删除中...' });
  try {
    await roomStore.deleteRoom(roomId);
    await roomStore.fetchRooms({ refresh: true });
    uni.hideLoading(); // 确保 hideLoading 在 fetchRooms 之后
    uni.showToast({ title: '删除成功', icon: 'success' });
  } catch (e: any) {
    uni.hideLoading(); // 确保在 catch 分支也能 hideLoading
    uni.showToast({ title: `删除失败: ${e.message || '请重试'}`, icon: 'none' });
  }
};

// 新增场次模态框逻辑
const isSessionModalVisible = ref(false);
const isSessionSubmitting = ref(false);
const currentRoomIdForSession = ref<string | null>(null);
const sessionFormModel = reactive({
  start_time: '',
  end_time: '',
});

// 场次表单错误状态
const startTimeError = ref('');
const endTimeError = ref('');

// 清除场次表单错误
const clearSessionErrors = () => {
  startTimeError.value = '';
  endTimeError.value = '';
};

// 场次表单验证
const validateSessionForm = () => {
  clearSessionErrors();
  let isValid = true;

  // 验证开始时间
  if (!sessionFormModel.start_time.trim()) {
    startTimeError.value = '开始时间不能为空';
    isValid = false;
  } else {
    // 验证时间格式
    const startTime = new Date(sessionFormModel.start_time);
    if (isNaN(startTime.getTime())) {
      startTimeError.value = '请输入有效的时间格式';
      isValid = false;
    } else if (startTime < new Date()) {
      startTimeError.value = '开始时间不能早于当前时间';
      isValid = false;
    }
  }

  // 验证结束时间（如果填写了）
  if (sessionFormModel.end_time.trim()) {
    const endTime = new Date(sessionFormModel.end_time);
    if (isNaN(endTime.getTime())) {
      endTimeError.value = '请输入有效的时间格式';
      isValid = false;
    } else if (sessionFormModel.start_time && new Date(sessionFormModel.start_time) >= endTime) {
      endTimeError.value = '结束时间必须晚于开始时间';
      isValid = false;
    }
  }

  return isValid;
};

const openCreateSessionModal = (roomId: string) => {
  currentRoomIdForSession.value = roomId;
  sessionFormModel.start_time = '';
  sessionFormModel.end_time = '';
  clearSessionErrors();
  isSessionModalVisible.value = true;
};

const closeSessionModal = () => {
  isSessionModalVisible.value = false;
  sessionFormModel.start_time = '';
  sessionFormModel.end_time = '';
  clearSessionErrors();
};

const handleCreateSession = async () => {
  if (!validateSessionForm()) {
    return;
  }
  
  if (!currentRoomIdForSession.value) return;
  isSessionSubmitting.value = true;
  try {
    await sessionStore.createSession(currentRoomIdForSession.value, {
      start_time: sessionFormModel.start_time.trim(),
      end_time: sessionFormModel.end_time.trim() || undefined,
    });
    closeSessionModal();
    uni.showToast({ title: '创建成功', icon: 'success' });
    // 可选：刷新 SessionList
  } catch (e: any) {
    uni.showToast({ title: `创建失败: ${e.message || '请重试'}`, icon: 'none' });
  } finally {
    isSessionSubmitting.value = false;
  }
};

// 4. 页面生命周期
onLoad(() => {
  roomStore.fetchRooms({ refresh: true });
});

onPullDownRefresh(async () => {
  await roomStore.fetchRooms({ refresh: true });
  uni.stopPullDownRefresh();
});

onReachBottom(() => {
  if (pagination.value.hasMore && !loading.value) {
    roomStore.fetchRooms();
  }
});

const jumpPage = ref(1);
// 计算最大页数
const maxPage = computed(() => {
  if (pagination.value.total && pagination.value.size) {
    return Math.ceil(pagination.value.total / pagination.value.size);
  }
  return 1;
});

const goPrevPage = () => {
  if (pagination.value.page > 2) {
    roomStore.fetchRooms({ refresh: true, page: pagination.value.page - 2 });
  }
};
const goNextPage = () => {
  if (pagination.value.hasMore) {
    roomStore.fetchRooms();
  }
};
const jumpToPage = () => {
  if (jumpPage.value >= 1 && jumpPage.value <= maxPage.value) {
    roomStore.fetchRooms({ refresh: true, page: jumpPage.value });
  }
};
</script>

<style lang="scss" scoped>
.room-list-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eaf0f7 100%);
  font-family: var(--font-family-sans-serif);
}
.page-title {
  font-size: 22px;
  font-weight: bold;
  text-align: center;
  margin: 24px 0 12px 0;
  color: #222;
  animation: fadeInTitle 0.6s;
}
.content-container {
  max-width: 1150px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(74,144,226,0.06);
  padding-bottom: 32px;
}
.accordion-list {
  width: 100%;
  padding: 0 0 24px 0;
}
.room-item {
  border-radius: 10px;
  box-shadow: 0 1px 6px rgba(74,144,226,0.04);
  margin: 18px 24px 0 24px;
  background: #f8fafc;
  transition: box-shadow 0.2s;
}
.room-header {
  display: flex;
  align-items: center;
  padding: 18px 24px;
  cursor: pointer;
  user-select: none;
  border-radius: 10px;
  background: #f8fafc;
  transition: background 0.2s;
  
  &:hover {
    background: #f0f6ff;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(74,144,226,0.1);
  }
  
  &:active {
    transform: translateY(0);
  }
}
.room-title {
  font-size: 18px;
  font-weight: 600;
  color: #222;
  margin-right: 24px;
  flex: 1;
  min-width: 0;
  word-break: break-word;
  white-space: normal;
  line-height: 1.4;
}
.room-actions {
  display: flex;
  gap: 12px;
}
@keyframes fadeInTitle {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.accordion-enter-active, .accordion-leave-active {
  transition: all 0.3s cubic-bezier(.25,.8,.25,1);
}
.accordion-enter-from, .accordion-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.fab-container {
  position: fixed;
  right: 40px;
  bottom: 48px;
  z-index: 100;
  .app-button {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    padding: 0;
    font-size: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 16px rgba(74,144,226,0.18);
  }
}
@media (max-width: 900px) {
  .content-container {
    max-width: 100vw;
    padding-left: 0;
    padding-right: 0;
  }
  .accordion-item {
    margin: 12px 4px 0 4px;
  }
  .accordion-header, .accordion-panel {
    padding-left: 8px;
    padding-right: 8px;
  }
}
@media (max-width: 600px) {
  .content-container {
    max-width: 100vw;
    padding-left: 0;
    padding-right: 0;
  }
  .accordion-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .accordion-title, .accordion-desc {
    margin-right: 0;
    max-width: 100%;
    white-space: normal;
  }
  .accordion-actions {
    justify-content: flex-start;
    gap: 8px;
    margin-top: 8px;
  }
  .fab-container {
    right: 16px;
    bottom: 16px;
  }
}
</style> 
```

**关键交互**：
- 与 useRoomStore 的集成（fetchRooms, addNewRoom, updateRoom, deleteRoom）
- 与 useSessionStore 的集成（createSession）
- ModalDialog 组件的交互
- AppButton 组件的交互
- 表单验证和错误处理
- uni-app 生命周期钩子（onLoad, onPullDownRefresh, onReachBottom）

#### 3.4.2. RoomDetail.vue (房间详情页)
**/src/pages/room/RoomDetail.vue**参考代码示例
```python
<template>
  <view class="room-detail-page">
    <!-- 固定页面标题 -->
    <view class="fixed-header">
      <view class="header-left">
        <AppButton type="primary" size="small" @click="goBackToList">返回直播列表页</AppButton>
      </view>
      <text class="page-title">房间详情</text>
      <view class="header-right">
        <!-- 预留右侧按钮位置 -->
      </view>
    </view>
    
    <!-- 1. 加载状态 -->
    <view v-if="loading" class="loading-container">
      <view class="spinner"></view>
      <text>加载中...</text>
    </view>

    <!-- 2. 错误状态 -->
    <view v-else-if="error" class="status-container">
      <text class="status-text">加载失败：{{ error.message }}</text>
      <AppButton type="primary" size="small" @click="goBack">返回</AppButton>
    </view>

    <!-- 3. 内容渲染 -->
    <view v-else-if="currentRoom" class="content-wrapper">
      <view class="info-card">
        <view class="room-info-table">
          <view class="info-row">
            <view class="info-cell">
              <text class="info-label">房间名称</text>
              <text class="info-value" v-html="safeRoomTitle"></text>
            </view>
            <view class="info-cell">
              <text class="info-label">简介</text>
              <text class="info-value" v-html="safeRoomDescription"></text>
            </view>
            <view class="info-cell">
              <text class="info-label">状态</text>
              <text class="info-value">
                <text class="status-icon">{{ currentRoom.is_private ? '🔒' : '🌍' }}</text>
                {{ currentRoom.is_private ? '私密房间' : '公开房间' }}
              </text>
            </view>
            <view class="info-cell">
              <text class="info-label">房间ID</text>
              <text class="info-value id-text">{{ currentRoom.id }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 场次列表卡片 -->
      <view class="sessions-card">
        <view class="sessions-header">
          <text class="sessions-title">直播场次</text>
          <AppButton type="primary" size="small" @click="openCreateSessionModal">创建新场次</AppButton>
        </view>
        <!-- 场次列表 -->
        <view v-if="sessionsLoading && sessions.length === 0" class="loading-container">
          <view class="spinner"></view>
          <text>正在加载场次...</text>
        </view>
        <view v-else-if="sessionsError" class="status-container">
          <text class="status-text">加载失败：{{ sessionsError.message }}</text>
          <AppButton type="primary" size="small" @click="retryFetchSessions">点击重试</AppButton>
        </view>
        <view v-else-if="sessions.length === 0" class="status-container empty-state">
          <text class="status-text">暂无场次信息</text>
        </view>
        <view v-else class="sessions-table">
          <!-- 表格头部 -->
          <view class="table-header">
            <view class="table-cell header-cell">场次ID</view>
            <view class="table-cell header-cell">状态</view>
            <view class="table-cell header-cell">开始时间</view>
            <view class="table-cell header-cell">结束时间</view>
            <view class="table-cell header-cell">视频ID</view>
            <view class="table-cell header-cell">创建时间</view>
            <view class="table-cell header-cell">更新时间</view>
            <view class="table-cell header-cell">操作</view>
          </view>
          
          <!-- 表格内容 -->
          <view 
            v-for="session in sessions" 
            :key="session.id" 
            class="table-row"
            @click="goToSessionDetail(session.id)"
          >
            <view class="table-cell">{{ session.id }}</view>
            <view class="table-cell">
              <view class="status-badge" :class="getStatusClass(session.status)">
                {{ getStatusText(session.status) }}
              </view>
            </view>
            <view class="table-cell">{{ formatTime(session.start_time) }}</view>
            <view class="table-cell">{{ formatTime(session.end_time) }}</view>
            <view class="table-cell">{{ session.video_id || '无' }}</view>
            <view class="table-cell">{{ formatTime(session.created_at) }}</view>
            <view class="table-cell">{{ formatTime(session.updated_at) }}</view>
            <view class="table-cell actions-cell" @click.stop>
              <AppButton type="default" size="small" @click="openEditModal(session)">编辑</AppButton>
              <AppButton type="danger" size="small" @click="handleDeleteSession(session)">删除</AppButton>
              <AppButton type="primary" size="small" @click="goToLiveView(session.id)">播放</AppButton>
            </view>
          </view>
        </view>
      </view>

      <!-- 分会场列表卡片 - 只在主会场显示 -->
      <view v-if="!currentRoom.parent_room_id" class="sub-venues-card">
        <view class="sub-venues-header">
          <text class="sub-venues-title">分会场</text>
          <AppButton type="primary" size="small" @click="openCreateSubVenueModal">创建分会场</AppButton>
        </view>
        
        <!-- 分会场列表 -->
        <view v-if="subVenuesLoading && subVenues.length === 0" class="loading-container">
          <view class="spinner"></view>
          <text>正在加载分会场...</text>
        </view>
        <view v-else-if="subVenuesError" class="status-container">
          <text class="status-text">加载失败：{{ subVenuesError.message }}</text>
          <AppButton type="primary" size="small" @click="retryFetchSubVenues">点击重试</AppButton>
        </view>
        <view v-else-if="subVenues.length === 0" class="status-container empty-state">
          <text class="status-text">暂无分会场信息</text>
        </view>
        <view v-else class="sub-venues-table">
          <!-- 表格头部 -->
          <view class="table-header">
            <view class="table-cell header-cell">分会场ID</view>
            <view class="table-cell header-cell">名称</view>
            <view class="table-cell header-cell">简介</view>
            <view class="table-cell header-cell">操作</view>
          </view>
          
          <!-- 表格内容 -->
          <view 
            v-for="subVenue in subVenues" 
            :key="subVenue.id" 
            class="table-row"
            @click="goToSubVenueDetail(subVenue.id)"
          >
            <view class="table-cell">{{ subVenue.id }}</view>
            <view class="table-cell" v-html="safeSubVenueTitle(subVenue)"></view>
            <view class="table-cell" v-html="safeSubVenueDescription(subVenue)"></view>
            <view class="table-cell actions-cell" @click.stop>
              <AppButton type="default" size="small" @click="openEditSubVenueModal(subVenue)">编辑</AppButton>
              <AppButton type="danger" size="small" @click="handleDeleteSubVenue(subVenue)">删除</AppButton>
              <AppButton type="primary" size="small" @click="goToSubVenueDetail(subVenue.id)">查看详情</AppButton>
            </view>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 创建新场次的模态框 -->
    <ModalDialog
      :visible="isSessionModalVisible"
      title="创建新场次"
      confirmText="立即创建"
      :confirmLoading="isCreatingSession"
      @update:visible="isSessionModalVisible = $event"
      @confirm="handleCreateSession"
      @cancel="closeCreateSessionModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">场次标题</text>
          <input class="form-input" v-model="newSession.title" placeholder="请输入场次标题" placeholder-class="placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">计划开始时间</text>
          <input class="form-input" type="datetime-local" v-model="newSession.start_time" placeholder="格式: YYYY-MM-DD HH:mm:ss" placeholder-class="placeholder" />
        </view>
      </view>
    </ModalDialog>

    <!-- 编辑场次的模态框 -->
    <ModalDialog
      :visible="isEditModalVisible"
      title="编辑场次"
      confirmText="保存更改"
      :confirmLoading="isUpdatingSession"
      @update:visible="isEditModalVisible = $event"
      @confirm="handleUpdateSession"
      @cancel="closeEditModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">开始时间</text>
          <input class="form-input" type="datetime-local" v-model="editSession.start_time" placeholder="格式: YYYY-MM-DD HH:mm:ss" placeholder-class="placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">结束时间</text>
          <input class="form-input" type="datetime-local" v-model="editSession.end_time" placeholder="格式: YYYY-MM-DD HH:mm:ss" placeholder-class="placeholder" />
        </view>
      </view>
    </ModalDialog>

    <!-- 创建分会场的模态框 -->
    <ModalDialog
      :visible="isSubVenueModalVisible"
      title="创建分会场"
      confirmText="立即创建"
      :confirmLoading="isCreatingSubVenue"
      @update:visible="isSubVenueModalVisible = $event"
      @confirm="handleCreateSubVenue"
      @cancel="closeCreateSubVenueModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">分会场标题</text>
          <input class="form-input" v-model="newSubVenue.title" placeholder="请输入分会场标题" placeholder-class="placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">分会场简介</text>
          <textarea class="form-textarea" v-model="newSubVenue.description" placeholder="请输入分会场简介（选填）" placeholder-class="placeholder" />
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useRoomStore } from '../../store/room';
import { useSessionStore } from '../../store/session';
import AppButton from '../../components/AppButton.vue';
import ModalDialog from '../../components/ModalDialog.vue';
import { escapeHtml } from '@/utils/xss';

const roomStore = useRoomStore();
const sessionStore = useSessionStore();
const { currentRoom, loading, error } = storeToRefs(roomStore);
const { sessions, loading: sessionsLoading, error: sessionsError } = storeToRefs(sessionStore);
const { subVenues, subVenuesLoading, subVenuesError } = storeToRefs(roomStore);

// 创建场次的模态框逻辑
const isSessionModalVisible = ref(false);
const isCreatingSession = ref(false);
const newSession = reactive({
  title: '',
  start_time: '',
});

// 编辑场次的模态框逻辑
const isEditModalVisible = ref(false);
const isUpdatingSession = ref(false);
const editSession = reactive({
  id: '',
  start_time: '',
  end_time: '',
});

// 创建分会场的模态框逻辑
const isSubVenueModalVisible = ref(false);
const isCreatingSubVenue = ref(false);
const newSubVenue = reactive({
  title: '',
  description: '',
});

// 时间格式转换
const toISOString = (datetimeLocal: string) => {
  if (!datetimeLocal) return '';
  return new Date(datetimeLocal).toISOString();
};

// 格式化时间显示
const formatTime = (timeStr: string) => {
  if (!timeStr) return '---';
  let fixed = timeStr.replace('+00:00Z', 'Z').replace(/\+00:00$/, 'Z');
  const date = new Date(fixed);
  if (isNaN(date.getTime())) return '---';
  return date.toLocaleString();
};

// 转换为datetime-local格式
const toDatetimeLocal = (isoString: string) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

const openCreateSessionModal = () => {
  newSession.title = '';
  newSession.start_time = '';
  isSessionModalVisible.value = true;
};

//创建分会场
const openCreateSubVenueModal = () => {
  newSubVenue.title = '';
  newSubVenue.description = '';
  isSubVenueModalVisible.value = true;
};

const closeCreateSubVenueModal = () => {
  isSubVenueModalVisible.value = false;
  newSubVenue.title = '';
  newSubVenue.description = '';
};

//创建场次
const closeCreateSessionModal = () => {
  isSessionModalVisible.value = false;
  newSession.title = '';
  newSession.start_time = '';
};

const openEditModal = (session: any) => {
  editSession.id = session.id;
  editSession.start_time = toDatetimeLocal(session.start_time);
  editSession.end_time = toDatetimeLocal(session.end_time);
  isEditModalVisible.value = true;
};

const closeEditModal = () => {
  isEditModalVisible.value = false;
  editSession.id = '';
  editSession.start_time = '';
  editSession.end_time = '';
};

const handleCreateSession = async () => {
  if (!currentRoom.value) {
    uni.showToast({ title: '未能获取当前房间ID', icon: 'none' });
    return;
  }
  if (!newSession.title || !newSession.start_time) {
    uni.showToast({ title: '标题和开始时间均不能为空', icon: 'none' });
    return;
  }
  isCreatingSession.value = true;
  try {
    await sessionStore.createSession(currentRoom.value.id, {
      title: newSession.title,
      start_time: toISOString(newSession.start_time),
    });
    uni.showToast({ title: '创建成功', icon: 'success' });
    closeCreateSessionModal();
    fetchSessions();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '创建失败', icon: 'none' });
    console.error('创建场次失败:', e);
  } finally {
    isCreatingSession.value = false;
  }
};

const handleUpdateSession = async () => {
  if (!editSession.start_time) {
    uni.showToast({ title: '开始时间不能为空', icon: 'none' });
    return;
  }
  isUpdatingSession.value = true;
  try {
    await sessionStore.updateSession(editSession.id, {
      start_time: toISOString(editSession.start_time),
      end_time: toISOString(editSession.end_time),
    });
    uni.showToast({ title: '更新成功', icon: 'success' });
    closeEditModal();
    fetchSessions();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '更新失败', icon: 'none' });
  } finally {
    isUpdatingSession.value = false;
  }
};

const handleDeleteSession = async (session: any) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个场次吗？',
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '删除中...' });
        try {
          await sessionStore.deleteSession(session.id, currentRoom.value?.id);
          await fetchSessions();
          uni.hideLoading();
          uni.showToast({ title: '删除成功', icon: 'success' });
        } catch (e: any) {
          uni.hideLoading();
          uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
        }
      }
    }
  });
};

// 跳转到场次详情页
const goToSessionDetail = (sessionId: string) => {
  if (!sessionId) {
    uni.showToast({ title: '无效的场次ID', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: `/pages/session/SessionDetail?id=${sessionId}` });
};

// 跳转到直播页面
const goToLiveView = (sessionId: string) => {
  if (!sessionId) {
    uni.showToast({ title: '无效的场次ID', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: `/pages/live/LiveView?id=${sessionId}` });
};

// 获取场次列表
const fetchSessions = () => {
  if (currentRoom.value?.id) {
    sessionStore.fetchSessionsByRoomId(currentRoom.value.id, { refresh: true });
  }
};

const retryFetchSessions = () => {
  fetchSessions();
};

// 获取状态样式类
const getStatusClass = (status: string) => {
  switch (status) {
    case 'scheduled':
      return 'status-scheduled';
    case 'live':
      return 'status-live';
    case 'ended':
      return 'status-ended';
    case 'archived':
      return 'status-archived';
    case 'finished':
      return 'status-ended';
    case 'ready':
      return 'status-scheduled';
    default:
      return 'status-default';
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  return status;
};

// 获取分会场状态样式类
const getSubVenueStatusClass = (subVenue: any) => {
  if (subVenue.live_status === 'live') {
    return 'status-live';
  } else if (subVenue.current_session_id) {
    return 'status-scheduled';
  } else {
    return 'status-default';
  }
};

// 获取分会场状态文本
const getSubVenueStatusText = (subVenue: any) => {
  if (subVenue.live_status === 'live') {
    return '直播中';
  } else if (subVenue.current_session_id) {
    return '有场次';
  } else {
    return '空闲';
  }
};

// 获取分会场列表
const fetchSubVenues = () => {
  if (currentRoom.value?.id) {
    roomStore.fetchSubVenues(currentRoom.value.id);
  }
};

const retryFetchSubVenues = () => {
  fetchSubVenues();
};

// 创建分会场
const handleCreateSubVenue = async () => {
  if (!currentRoom.value) {
    uni.showToast({ title: '未能获取当前房间ID', icon: 'none' });
    return;
  }
  // 检查是否为分会场
  if (currentRoom.value.parent_room_id) {
    uni.showToast({ title: '分会场不能创建子分会场', icon: 'none' });
    return;
  }
  if (!newSubVenue.title) {
    uni.showToast({ title: '分会场标题不能为空', icon: 'none' });
    return;
  }
  isCreatingSubVenue.value = true;
  try {
    await roomStore.createSubVenue({
      title: newSubVenue.title,
      description: newSubVenue.description,
      parent_room_id: currentRoom.value.id
    });
    uni.showToast({ title: '创建成功', icon: 'success' });
    closeCreateSubVenueModal();
    fetchSubVenues();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '创建失败', icon: 'none' });
    console.error('创建分会场失败:', e);
  } finally {
    isCreatingSubVenue.value = false;
  }
};

// 编辑分会场
const openEditSubVenueModal = (subVenue: any) => {
  // 这里可以添加编辑分会场的逻辑
  uni.showToast({ title: '编辑功能开发中', icon: 'none' });
};

// 删除分会场
const handleDeleteSubVenue = async (subVenue: any) => {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除分会场"${subVenue.title}"吗？`,
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '删除中...' });
        try {
          await roomStore.deleteSubVenue(subVenue.id, currentRoom.value?.id);
          await fetchSubVenues();
          uni.hideLoading();
          uni.showToast({ title: '删除成功', icon: 'success' });
        } catch (e: any) {
          uni.hideLoading();
          uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
        }
      }
    }
  });
};

// 跳转到分会场详情页
const goToSubVenueDetail = (subVenueId: string) => {
  if (!subVenueId) {
    uni.showToast({ title: '无效的分会场ID', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: `/pages/room/RoomDetail?id=${subVenueId}` });
};

// 获取参数与数据
onLoad((options) => {
  if (options && typeof options.id === 'string' && options.id) {
    roomStore.fetchRoomById(options.id);
  } else {
    error.value = new Error('无效的房间ID');
  }
});

// 监听房间数据变化，自动加载场次和分会场
watch(
  () => currentRoom.value?.id,
  (newRoomId) => {
    if (newRoomId) {
      fetchSessions();
      // 只有主会场才加载分会场数据
      if (!currentRoom.value?.parent_room_id) {
        fetchSubVenues();
      }
    }
  }
);

const goBack = () => {
  uni.navigateBack();
};

// 返回直播列表页
const goBackToList = () => {
  uni.navigateTo({ url: '/pages/room/RoomList' });
};

const safeRoomTitle = computed(() => escapeHtml(currentRoom.value?.title || ''));
const safeRoomDescription = computed(() => escapeHtml(currentRoom.value?.description || '暂无简介'));
const safeSubVenueTitle = (subVenue: any) => escapeHtml(subVenue.title);
const safeSubVenueDescription = (subVenue: any) => escapeHtml(subVenue.description || '暂无简介');
</script>

<style lang="scss" scoped>
.room-detail-page {
  background-color: #f7f8fa;
  min-height: 100vh;
  padding-top: 60px; /* 为固定标题留出空间 */
}

.fixed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 2;
}

.header-right {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 2;
}

.loading-container, .status-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding-top: 100px;
  text-align: center;
  color: var(--color-text-secondary);
}

.status-text {
  margin-bottom: var(--spacing-medium);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-primary-light-1);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-medium);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.content-wrapper {
  padding: 30px 112px
}

.cover-section {
  width: 100%;
  height: 200px;
}

.cover-image {
  width: 100%;
  height: 100%;
  background-color: #e0e0e0;
}

.info-card, .sessions-card {
  background-color: var(--color-background);
  margin: 0 var(--spacing-medium);
  border-radius: var(--radius-large);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.info-card {
  margin-top: -30px;
  position: relative;
  z-index: 1;
  padding: var(--spacing-large);
  margin-bottom: var(--spacing-medium);
}

.room-info-table {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  overflow: hidden;
  background: #fff;
}

.info-row {
  display: flex;
  width: 100%;
}

.info-cell {
  flex: 1;
  padding: var(--spacing-medium);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  
  &:last-child {
    border-right: none;
  }
}

.info-label {
  font-size: var(--font-size-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-medium);
  font-weight: 500;
}

.info-value {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-weight: 500;
  word-break: break-word;
  line-height: 1.4;
}

.status-icon {
  margin-right: var(--spacing-small);
  font-size: 16px;
}

.id-text {
  color: var(--color-text-secondary);
  font-family: monospace;
  font-size: var(--font-size-medium);
  word-break: break-all;
}

.sessions-card, .sub-venues-card {
  background-color: var(--color-background);
  margin: 0 var(--spacing-medium);
  border-radius: var(--radius-large);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: var(--spacing-large);
  margin-bottom: var(--spacing-large);
}

.sub-venues-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-large);
}

.sub-venues-title {
  font-size: var(--font-size-large);
  font-weight: bold;
  color: var(--color-text-primary);
}

.sub-venues-table {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  overflow: hidden;
  background: #fff;
  table-layout: fixed;
  
  .table-header {
    display: grid;
    grid-template-columns: 2fr 2fr 2fr 1.8fr;
    background: #f8f9fa;
    border-bottom: 2px solid var(--color-border);
  }
  
  .table-row {
    display: grid;
    grid-template-columns: 2fr 2fr 2fr 1.8fr;
    border-bottom: 1px solid var(--color-border);
    transition: background-color 0.2s;
    
    /* 斑马纹效果：奇数行为白色，偶数行为浅灰色 */
    &:nth-child(odd) {
      background-color: #ffffff;
    }
    
    &:nth-child(even) {
      background-color: #f8f9fa;
    }

    &:hover {
      background-color: #e3f2fd !important;
    }
    
    &:last-child {
      border-bottom: none;
    }
  }
}



.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-large);
}

.sessions-title {
  font-size: var(--font-size-large);
  font-weight: bold;
  color: var(--color-text-primary);
}

.sessions-table {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  overflow: hidden;
  background: #fff;
  table-layout: fixed;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1.8fr;
  background: #f8f9fa;
  border-bottom: 2px solid var(--color-border);
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1.8fr;
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.2s;
  
    /* 斑马纹效果：奇数行为白色，偶数行为浅灰色 */
  &:nth-child(odd) {
    background-color: #ffffff;
  }
  
  &:nth-child(even) {
    background-color: #f8f9fa;
  }

  &:hover {
    background-color: #e3f2fd !important;
  }
  
  &:last-child {
    border-bottom: none;
  }
}

.table-cell {
  padding: var(--spacing-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-small);
  color: var(--color-text-primary);
  border-right: 1px solid var(--color-border);
  word-break: break-word;
  overflow: hidden;
  
  &:last-child {
    border-right: none;
  }
}

.header-cell {
  font-weight: bold;
  background: #f8f9fa;
  color: var(--color-text-secondary);
}

.actions-cell {
  justify-content: flex-start;
  gap: var(--spacing-small);
  position: relative;
  z-index: 10;
  
  .app-button {
    position: relative;
    z-index: 11;
  }
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: var(--font-size-small);
  font-weight: 500;
  color: white;
  text-align: center;
  min-width: 60px;
}

.status-scheduled {
  background-color:rgb(239, 193, 8);
}

.status-live {
  background-color:rgb(47, 173, 77);
}

.status-ended {
  background-color:rgb(152, 152, 3);
}

.status-archived {
  background-color: #17a2b8;
}

.status-default {
  background-color: #6c757d;
}

.session-item {
  background: #f4f8ff;
  border-radius: 8px;
  border-left: 3px solid #a0c4ff;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #e8f2ff;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.session-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-medium);
}

.session-info {
  flex: 1;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-large);
}

.session-status {
  font-size: var(--font-size-base);
  font-weight: bold;
  color: var(--color-primary);
  flex: 1;
  text-align: center;
}

.session-time-start {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  flex: 1;
  text-align: left;
}

.session-time-end {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  flex: 1;
  text-align: left;
}

.session-time {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.session-actions {
  display: flex;
  gap: var(--spacing-small);
}

.title {
  font-size: var(--font-size-xlarge);
  font-weight: bold;
  color: black;
  margin-bottom: var(--spacing-medium);
}

.description {
  font-size: var(--font-size-base);
  color: black;
  line-height: 1.7;
  margin-bottom: var(--spacing-xlarge);
  word-break: break-word;
}

.meta-list {
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-medium);
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  
  &:not(:last-child) {
    margin-bottom: var(--spacing-medium);
  }
}

.meta-icon {
  margin-right: var(--spacing-medium);
  font-size: 18px;
}

.id-text {
  color: var(--color-text-secondary);
  font-family: monospace;
  word-break: break-all;
}

.empty-state {
  min-height: 120px;
}

.form {
  padding: var(--spacing-medium) 0;
}

.form-group {
  margin-bottom: var(--spacing-large);
}

.form-label {
  display: block;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-small);
  font-weight: bold;
}

.form-input {
  width: 100%;
  padding: var(--spacing-medium);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  background-color: var(--color-background-light);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  box-sizing: border-box;
}

.placeholder {
  color: var(--color-text-secondary);
}

@media (max-width: 600px) {
  .session-content, .sub-venue-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-small);
  }
  
  .session-actions, .sub-venue-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
```

**核心功能**：
- 房间详情信息展示
- 场次列表展示和管理
- 场次创建、编辑、删除操作
- 直播跳转功能

**关键交互**：
- 与 useRoomStore 的集成（fetchRoomById）
- 与 useSessionStore 的集成（fetchSessionsByRoomId, createSession, updateSession, deleteSession）
- 路由参数获取和处理
- 场次状态管理和显示
- 时间格式化和显示

#### 3.4.3. LiveView.vue (直播观看页)
**src/pages/live/LiveView.vue**源代码
```python
<template>
  <view class="live-view-page">
    <!-- 固定页面标题 -->
    <view class="fixed-header">
      <view class="header-left">
        <AppButton type="primary" size="small" @click="goBackToList">返回直播列表页</AppButton>
        <AppButton type="primary" size="small" @click="goBackToRoom">返回房间详情页</AppButton>
      </view>
      <text class="page-title">正在直播</text>
      <view class="header-right">
        <!-- 预留右侧按钮位置 -->
      </view>
    </view>
    
    <!-- 1. 加载状态 -->
    <view v-if="loading" class="loading-container">
      <view class="spinner"></view>
      <text>正在进入直播间...</text>
    </view>

    <!-- 2. 错误状态 -->
    <view v-else-if="error" class="status-container">
      <text class="status-text">进入失败：{{ error.message }}</text>
      <AppButton type="primary" size="small" @click="goBack">返回</AppButton>
    </view>

    <!-- 3. 内容渲染 -->
    <view v-else-if="currentSession" class="content-container">
      <!-- 左侧视频和评论区区域 -->
      <view class="left-section">
        <!-- 视频播放区域 -->
        <view class="video-container">
          <iframe
            v-if="isH5 && play_url"
            :src="h5PlayerUrl"
            style="width:100%;height:500px;border:none;border-radius:0;"
            allowfullscreen
          ></iframe>
          <VideoPlayer
            v-else-if="play_url"
            :src="play_url"
          />
          <text v-if="play_url" style="color:rgb(255, 255, 255); font-size: 12px; word-break: break-all;">
            播放地址: {{ play_url }}
          </text>
          <!-- 如果没有播放地址，显示提示 -->
          <view v-else class="status-container placeholder-video">
            <text class="status-text">暂无有效的播放地址</text>
            <text style="color: #ffffff; font-size: 12px; word-break: break-all;">
              play_url: {{ play_url }}
            </text>
          </view>
        </view>
        
        <!-- 评论区区域 -->
        <view class="comments-section">
          <!-- 房间简介 -->
          <view v-if="roomDetail && roomDetail.description" class="room-description-card">
            <view class="description-header">
              <text class="description-icon">📝</text>
              <text class="description-label">房间简介</text>
            </view>
            <text class="description-content">{{ roomDetail.description }}</text>
          </view>
          <view v-else class="room-description-card">
            <view class="description-header">
              <text class="description-icon">📝</text>
              <text class="description-label">房间简介</text>
            </view>
            <text class="description-content no-description">暂无简介</text>
          </view>
          <!-- 仿真评论 -->
          <text class="section-title">评论区</text>
          <view class="mock-comments">
            <view v-for="(comment, idx) in mockComments" :key="idx" class="comment-card">
              <text class="comment-user">{{ comment.user }}：</text>
              <text class="comment-content">{{ comment.content }}</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 右侧推荐区域 -->
      <view class="recommendations-section">
        <text class="section-title">推荐直播间</text>
        <view v-if="recommendedRooms.length > 0" class="room-cards-container">
                     <view 
             v-for="room in recommendedRooms" 
             :key="room.id" 
             class="room-card"
             @click="goToRoomDetail(room.id)"
           >
             <view class="room-card-header">
               <text class="room-title">{{ room.title }}</text>
             </view>
             <view class="room-card-content">
               <text class="room-description">{{ room.description || '暂无简介' }}</text>
             </view>
           </view>
        </view>
        <view v-else class="no-recommendations">
          <text class="placeholder-text">暂无推荐直播间</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useSessionStore } from '../../store/session';
import { useRoomStore } from '../../store/room';
import { getRoomDetail } from '../../api/room';
import type { SessionStatus } from '../../types/session';
import AppButton from '../../components/AppButton.vue';
import VideoPlayer from '../../components/VideoPlayer.vue';

const sessionStore = useSessionStore();
const { currentSession, loading, error } = storeToRefs(sessionStore);

const roomStore = useRoomStore();
const { rooms } = storeToRefs(roomStore);

const isH5 = process.env.UNI_PLATFORM === 'h5';

// 新增：房间详情和仿真评论
const roomDetail = ref<any>(null);
const mockComments = ref([
  { user: '用户小白', content: '直播间讲解很棒，支持！' },
  { user: '路人甲', content: '视频很清晰，主播加油！' },
  { user: '路人乙', content: '有回放吗？错过了前面部分。' }
]);

// 推荐直播间计算属性
const recommendedRooms = computed(() => {
  // 获取最新创建的5个房间，排除当前房间
  const currentRoomId = currentSession.value?.room_id;
  return rooms.value
    .filter(room => room.id !== currentRoomId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);
});

// 拼接 play_url（前端生成）
const play_url = computed(() => {
  const session = currentSession.value;
  if (true){
    const room = rooms.value.find(r => r.id === session.room_id);
    if (true) {
      return `http://124.220.235.226:8080/live/streamkey_6bdfdfcf990672e1a2c8c222826e030b.m3u8?hls_ctx=y583930p`;
    }
  }
  return null;
});

const h5PlayerUrl = computed(() =>
  play_url.value ? `/static/hls-player.html?url=${encodeURIComponent(play_url.value)}` : ''
);

// 跳转到房间详情页
const goToRoomDetail = (roomId: string) => {
  uni.navigateTo({ url: `/pages/room/RoomDetail?id=${roomId}` });
};

// 获取房间状态样式类
const getStatusClass = (status: string) => {
  const statusMap: Record<string, string> = {
    'live': 'status-live',
    'scheduled': 'status-scheduled',
    'ended': 'status-ended',
    'archived': 'status-archived'
  };
  return statusMap[status] || 'status-default';
};

// 获取房间状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'live': '直播中',
    'scheduled': '计划中',
    'ended': '已结束',
    'archived': '已归档'
  };
  return statusMap[status] || '未知';
};

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

// 修改 onLoad，获取房间详情
onLoad(async (options) => {
  if (options && typeof options.id === 'string' && options.id) {
    await sessionStore.fetchSessionById(options.id);
    // 获取房间详情
    const { currentSession } = storeToRefs(sessionStore);
    const session = currentSession.value;
    if (session && session.room_id) {
      try {
        console.log('正在获取房间详情，room_id:', session.room_id);
        const detailResp = await getRoomDetail(session.room_id);
        roomDetail.value = detailResp.data; // 只存 data 字段
        console.log('直播简介:', roomDetail.value.description);
      } catch (e) {
        console.error('获取房间详情失败:', e);
        roomDetail.value = null;
      }
    }
  } else {
    console.log("xx")
    error.value = new Error('无效的场次ID');
  }
});

// 页面加载时获取房间列表
onMounted(async () => {
  await roomStore.fetchRooms();
});

const goBack = () => {
  uni.navigateBack();
};

// 返回直播列表
const goBackToList = () => {
  uni.navigateTo({ url: '/pages/room/RoomList' });
};

// 返回房间详情页
const goBackToRoom = () => {
  if (currentSession.value?.room_id) {
    uni.navigateTo({ url: `/pages/room/RoomDetail?id=${currentSession.value.room_id}` });
  } else {
    uni.showToast({
      title: '无法获取房间信息',
      icon: 'none'
    });
  }
};

const sessionStatusText = (status: SessionStatus) => {
  const map: Record<SessionStatus, string> = {
    scheduled: '计划中',
    live: '直播中',
    ended: '已结束',
    archived: '已归档',
  };
  return map[status] || '未知状态';
};
</script>

<style lang="scss" scoped>
.live-view-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f8fa; /* 改为浅灰色背景 */
  color: #333; /* 改为深色文字 */
  padding-top: 60px; /* 为固定标题留出空间 */
}

.fixed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.header-left {
  display: flex;
  gap: 30px;
  align-items: center;
  position: relative;
  z-index: 2;
}

.header-right {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 2;
}

.loading-container,
.status-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  flex-grow: 1;
  padding: var(--spacing-large);
  text-align: center;
}

.status-text {
  margin-bottom: var(--spacing-medium);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-medium);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.content-container {
  display: flex;
  flex-direction: row;
  flex-grow: 1;
  height: calc(100vh - 60px); /* 减去固定标题的高度 */
  background-color:#ffffff;
}

/* 左侧区域：视频 + 评论区 */
.left-section {
  
  flex: 2;
  display: flex;
  flex-direction: column;
  margin: 10px;
  border-radius: 8px;
}

/* 视频容器 */
.video-container {
  flex: 2; /* 增加视频区域的比例 */
  margin: 10px;
  border-radius: 8px;
  overflow: hidden;
  min-height: 500px; /* 设置最小高度 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); /* 添加阴影 */
}

.placeholder-video {
  height: 225px;
  background-color: #ffffff; /* 白色背景 */
}

/* 评论区 */
.comments-section {
  flex: 1; /* 保持评论区比例较小 */
  margin: 10px;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 200px; /* 设置评论区最小高度 */
}
.room-description-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); /* 更新阴影 */
  border: 1px solid #e0e0e0;
}

.description-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.description-icon {
  font-size: 16px;
  margin-right: 8px;
}

.description-label {
  font-size: 14px;
  font-weight: bold;
  color: #333;
}

.description-content {
  font-size: 14px;
  color: #444;
  line-height: 1.5;
}

.no-description {
  color: #aaa;
  font-style: italic;
}
.mock-comments {
  margin-top: 16px;
}

.comment-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 5px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  border-left: 5px solid rgb(109, 184, 246);
  border: 1px solid #e0e0e0;
  border-left: 5px solid rgb(109, 184, 246);
}

.comment-user {
  font-size: 14px;
  font-weight: bold;
  color: rgb(24, 132, 221);
  margin-right: 4px;
}

.comment-content {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
}

/* 右侧推荐区域 */
.recommendations-section {
  flex: 1;
  margin: 10px;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保高度填满父容器 */
  min-height: 0; /* 允许flex子元素收缩 */
}

/* 区域标题 */
.section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 16px;
  color: #333;
}

.placeholder-text {
  color: #666;
  font-size: 14px;
}

/* 房间卡片容器 */
.room-cards-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

/* 房间卡片样式 */
.room-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 12px;
}

.room-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.room-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.room-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  flex: 1;
  margin-right: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

.status-live {
  background-color: #ff4444;
  color: white;
}

.status-scheduled {
  background-color: #2196f3;
  color: white;
}

.status-ended {
  background-color: #666;
  color: white;
}

.status-archived {
  background-color: #9c27b0;
  color: white;
}

.status-default {
  background-color: #ccc;
  color: #333;
}

.room-card-content {
  margin-bottom: 8px;
}

.room-description {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.room-card-footer {
  display: flex;
  justify-content: flex-end;
}

.room-time {
  font-size: 12px;
  color: #999;
}

.no-recommendations {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}
</style>
```
**核心功能**：
- 直播视频播放
- 房间信息展示
- 推荐房间展示
- 评论区模拟

**关键交互**：
- 与 useSessionStore 的集成（fetchSessionById）
- 与 useRoomStore 的集成（fetchRooms）
- VideoPlayer 组件集成
- 路由参数处理
- 平台检测（H5/App）

#### 3.4.4. NotFound.vue (404页面)
**/src/pages/room/common/NotFound.vue**源代码
```python
<template>
  <view class="not-found-page">
    <view class="container">
      <image src="/static/404-illustration.svg" class="illustration" mode="widthFix" />
      <text class="title">页面未找到</text>
      <text class="message">抱歉，您访问的页面不存在或已被移动。</text>
      <AppButton type="primary" @click="goHome">返回首页</AppButton>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppButton from '../../components/AppButton.vue';

const goHome = () => {
  // 使用 reLaunch 跳转到 TabBar 页面或首页，清空页面栈
  uni.reLaunch({
    url: '/pages/room/RoomList'
  });
};
</script>

<style lang="scss" scoped>
.not-found-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: var(--color-background);
  text-align: center;
  padding: var(--spacing-large);
}

.container {
  max-width: 320px;
}

.illustration {
  width: 200px;
  margin-bottom: var(--spacing-large);
}

.title {
  display: block;
  font-size: var(--font-size-xlarge);
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-small);
}

.message {
  display: block;
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xlarge);
}
</style> 
```
**核心功能**：
- 404错误页面展示
- 返回首页功能

**关键交互**：
- AppButton 组件交互
- 路由跳转（uni.reLaunch）

---

## 4. 代码生成具体要求 (Test Code Generation Requirements)

### 4.1. 页面渲染测试
- 测试页面正常渲染和基本结构
- 测试加载状态、错误状态、空状态的显示
- 测试条件渲染逻辑
- 测试数据绑定和响应式更新

### 4.2. 用户交互测试
- 测试按钮点击事件和回调
- 测试表单输入和验证
- 测试模态框的打开、关闭、确认、取消
- 测试列表项的点击和操作

### 4.3. Store 集成测试
- 测试页面与 store 的数据绑定
- 测试 store action 的调用和参数传递
- 测试 store 状态变化对页面的影响
- 测试错误状态的处理

### 4.4. API 集成测试
- 测试页面触发的 API 调用
- 测试 API 成功响应的处理
- 测试 API 错误响应的处理
- 测试加载状态的管理

### 4.5. 路由集成测试
- 测试页面间的导航跳转
- 测试路由参数的获取和处理
- 测试返回操作
- 测试路由守卫（如有）

### 4.6. 生命周期测试
- 测试 onLoad 钩子的执行
- 测试 onPullDownRefresh 的触发和处理
- 测试 onReachBottom 的触发和处理
- 测试页面卸载时的清理

### 4.7. 组件集成测试
- 测试页面内组件的渲染
- 测试组件事件的传递和处理
- 测试组件 props 的传递
- 测试组件 slot 的使用

### 4.8. 边界条件和异常测试
- 测试网络错误的处理
- 测试数据为空的情况
- 测试参数异常的处理
- 测试权限异常的处理

---

## 5. Mock 策略和依赖隔离

### 5.1. uni-app API Mock
```typescript
// 统一方案 Part 1：使用 global.uni 提供导航与 UI 能力（不与生命周期注册混用）
const createUniMock = () => ({
  navigateTo: vi.fn(),
  navigateBack: vi.fn(),
  reLaunch: vi.fn(),
  showToast: vi.fn(),
  showModal: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  stopPullDownRefresh: vi.fn(),
  getStorageSync: vi.fn(),
  setStorageSync: vi.fn()
})

beforeEach(() => {
  // @ts-ignore
  global.uni = createUniMock()
})

afterEach(() => {
  vi.clearAllMocks()
})
```

### 5.2. Store Mock
```typescript
import { createTestingPinia } from '@pinia/testing'

// 在 beforeEach 中创建测试 pinia
beforeEach(() => {
  const pinia = createTestingPinia({
    createSpy: vi.fn,
    stubActions: false
  })
  setActivePinia(pinia)
})
```

### 5.3. 路由参数 Mock
```typescript
// 统一方案 Part 2：用 vi.mock('@dcloudio/uni-app') 捕获生命周期注册，测试里手动触发
// 在测试文件头部或测试工具模块中：
const lifecycles = {
  onLoad: [] as Array<(options?: any) => void>,
  onPullDownRefresh: [] as Array<() => void>,
  onReachBottom: [] as Array<() => void>
}

vi.mock('@dcloudio/uni-app', () => ({
  onLoad: (cb: (options?: any) => void) => lifecycles.onLoad.push(cb),
  onPullDownRefresh: (cb: () => void) => lifecycles.onPullDownRefresh.push(cb),
  onReachBottom: (cb: () => void) => lifecycles.onReachBottom.push(cb)
}))

// 提供测试助手：在用例中导入/复制后使用
export const captureLifecycle = () => ({
  triggerOnLoad: (options?: any) => lifecycles.onLoad.forEach(cb => cb(options)),
  triggerOnPullDown: () => lifecycles.onPullDownRefresh.forEach(cb => cb()),
  triggerOnReachBottom: () => lifecycles.onReachBottom.forEach(cb => cb()),
  reset: () => {
    lifecycles.onLoad.length = 0
    lifecycles.onPullDownRefresh.length = 0
    lifecycles.onReachBottom.length = 0
  }
})
```

### 5.4. 组件 Mock
```typescript
// Mock 子组件
vi.mock('@/components/AppButton.vue', () => ({
  default: {
    name: 'AppButton',
    template: '<button @click="$emit(\'click\')"><slot /></button>'
  }
}))
```

---

## 6. 测试用例结构示例

### 6.1. RoomList.vue 测试结构
```typescript
describe('RoomList.vue', () => {
  describe('页面渲染', () => {
    it('正常渲染页面结构')
    it('显示加载状态')
    it('显示错误状态')
    it('显示空状态')
  })

  describe('房间列表', () => {
    it('正确显示房间列表')
    it('点击房间跳转到详情页')
    it('下拉刷新房间列表')
    it('上拉加载更多房间')
  })

  describe('房间操作', () => {
    it('打开创建房间模态框')
    it('成功创建房间')
    it('创建房间表单验证')
    it('打开编辑房间模态框')
    it('成功编辑房间')
    it('确认删除房间')
    it('删除有场次的房间时显示提示')
  })

  describe('Store 集成', () => {
    it('页面加载时调用 fetchRooms')
    it('创建房间时调用 addNewRoom')
    it('更新房间时调用 updateRoom')
    it('删除房间时调用 deleteRoom')
  })

  describe('生命周期', () => {
    it('onLoad 时获取房间列表')
    it('onPullDownRefresh 时刷新列表')
    it('onReachBottom 时加载更多')
  })
})
```

---

## 7. 高质量测试的细节要求

### 7.1. Mock 与依赖隔离
- 所有 uni-app API、store action、组件事件、路由跳转、网络请求必须用 `vi.mock` 或 `vi.fn` 进行 mock
- 使用 `createTestingPinia` 进行 store 测试，确保 store 状态隔离
- Mock 所有子组件，避免子组件逻辑干扰页面测试

### 7.2. 断言要具体
- 优先使用 `toBe`、`toEqual`、`toContain`、`toHaveBeenCalledWith` 等具体断言
- 验证 DOM 结构和内容的正确性
- 验证事件调用的参数和次数

### 7.3. 页面测试要覆盖完整用户流程
- 测试从页面加载到用户操作的完整流程
- 测试异常情况的用户体验
- 测试页面间的导航流程

### 7.4. Store 集成要验证数据流
- 验证页面正确调用 store action
- 验证 store 状态变化对页面的影响
- 验证错误状态的传递和显示

### 7.5. 组件集成要测试交互
- 验证父子组件间的数据传递
- 验证组件事件的正确触发
- 验证组件 slot 的正确使用

### 7.6. 生命周期要测试时机
- 验证生命周期钩子在正确时机执行
- 验证钩子函数的参数和调用次数
- 验证页面卸载时的清理工作

---

## 8. 测试文件命名和组织

### 8.1. 文件命名规范
- 页面测试文件：`tests/pages/[路径].spec.ts`
- 例如：`tests/pages/room/RoomList.spec.ts`

### 8.2. 测试分组策略
- 按功能模块分组（页面渲染、用户交互、Store集成等）
- 每个分组内按具体功能细分
- 使用描述性的测试用例名称

### 8.3. 测试数据管理
- 使用工厂函数创建测试数据
- 复用常用的 mock 数据
- 保持测试数据的一致性

---

## 9. 最终交付 (Final Deliverable)

请为 frontend_live/src/pages/ 下的所有页面文件，分别生成完整、可运行的 Vitest 集成测试文件（.spec.ts），每个测试文件需覆盖：

1. **页面渲染测试** - 正常渲染、加载状态、错误状态、空状态
2. **用户交互测试** - 按钮点击、表单操作、模态框交互
3. **Store 集成测试** - 数据绑定、action 调用、状态响应
4. **API 集成测试** - 请求触发、响应处理、错误处理
5. **路由集成测试** - 页面跳转、参数传递、导航操作
6. **生命周期测试** - 钩子执行、参数处理、清理工作
7. **组件集成测试** - 子组件交互、事件传递、props 传递
8. **边界条件测试** - 异常处理、空数据、网络错误

所有测试用例需独立、mock 所有外部依赖，严格遵循 AAA（Arrange-Act-Assert）模式。

每个测试文件请用清晰的代码块标注文件名和内容，便于直接落地。

---

## 10. 注意事项

### 10.1. uni-app 特殊性
- 注意 uni-app 的生命周期钩子与 Vue 的差异
- 正确 mock uni-app 的全局 API
- 处理 uni-app 的条件编译（如 H5/App 平台差异）

### 10.2. Pinia Store 测试
- 使用 `createTestingPinia` 而不是真实 store
- 正确设置 store 的初始状态
- 验证 store action 的调用和参数

### 10.3. 组件测试集成
- 正确 mock 子组件，避免深度渲染
- 验证组件间的事件传递
- 测试组件的条件渲染

### 10.4. 异步操作处理
- 正确处理异步的 store action
- 使用 `await` 等待异步操作完成
- 验证异步操作的加载状态

---

**本提示词适用范围**：第二批次页面与集成测试，专注于页面级功能和组件间交互的测试覆盖。
