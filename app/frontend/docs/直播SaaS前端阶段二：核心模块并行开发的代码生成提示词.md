# 直播SaaS前端阶段二：核心模块并行开发的代码生成提示词 (V3 - 动态逻辑增强版)

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通uni-app、Vue3、TypeScript和Pinia，你的任务是根据详细设计文档和上下文，编写**高质量、功能完整、可直接运行**的核心模块代码，特别是实现带有**完整数据请求、状态更新和错误处理逻辑**的状态管理模块。

---

## 2. 任务目标（Task Objective）
本次任务为直播SaaS平台前端项目的**阶段二：核心模块并行开发**。目标是并行构建项目的两大核心支柱：
1.  一套完全独立、可复用的**哑（Dumb）基础UI组件**。
2.  一套包含**完整动态业务逻辑**的**智能（Smart）状态管理模块**。

**为确保任务明确、无歧义，本次需具体生成以下文件：**

-   **在 `src/components/` 目录下新建基础UI组件：**
    -   `AppButton.vue`
    -   `ModalDialog.vue`
    -   `RoomCard.vue`
-   **在 `src/store/` 目录下创建状态管理模块：**
    -   `index.ts` (Pinia 入口文件)
    -   `room.ts`
    -   `session.ts`

---

## 3. 核心上下文信息（Core Context Information）
-   **唯一事实来源**: 《直播SaaS平台前端设计文档.md》是所有代码生成工作的唯一且最高的设计依据。
-   **阶段一产出**: 你必须依赖阶段一已生成的以下模块：
    -   `src/api/room.ts`: 用于发起所有与“房间”相关的API请求。
    -   `src/api/session.ts`: 用于发起所有与“场次”相关的API请求。
    -   `src/types/*.ts`: 包含了所有核心数据结构的TypeScript类型定义。
    -   `src/common/uni.scss`: 包含了所有设计令牌的CSS变量。

---

## 4. 全局强制性约束与最高准则
-   **功能完整性**:
    -   **UI组件**: 必须是纯粹的展示性组件，通过 `props` 接收数据，通过 `emits` 发出事件，**内部绝不允许直接调用API或Store**。
    -   **状态管理**: **必须是功能完整的**。`actions` 必须包含实际的API调用、数据处理、状态更新和错误捕获逻辑，**绝不能只是一个空的框架或简单的 `setter`**。
-   **命名与结构**: 严格遵循《直播SaaS平台前端设计文档.md》**第 3.2 节**中的命名规范。

---

## 5. 分步生成与交叉验证流程

### 步骤1：基础UI组件生成 (`src/components/`)
-   **目标**: 创建一套可复用的、独立的“哑”组件。
-   **验证点**:
    -   [ ] `AppButton.vue`, `ModalDialog.vue`, `RoomCard.vue` 是否已创建？
    -   [ ] 所有组件的样式是否都严格使用了 `uni.scss` 中定义的CSS变量？

### 步骤2：状态管理模块生成 (`src/store/`)
-   **目标**: 创建包含完整业务逻辑的Pinia Store。
-   **要求 (强指令)**: 生成的`actions`不仅是方法的定义，更是**完整工作流的实现**。它们是连接UI和API的桥梁，后续将在页面组件的生命周期钩子（如 `onMounted`）或用户交互事件中被调用。
-   **验证点**:
    -   [ ] `index.ts`, `room.ts`, `session.ts` 文件是否已创建？
    -   [ ] `actions` 内部是否**真实地调用**了 `src/api/` 中对应的函数？
    -   [ ] 每个API调用是否都被 `try...catch` 块包裹，并在 `catch` 中**处理了错误状态**？
    -   [ ] 分页加载的逻辑是否**正确地追加（append）数据**而不是替换？

---

## 6. 模块生成指令 (Module Generation Instructions)

### 6.1 `src/components/AppButton.vue`
-   **目标**: 定义一个高度可复用的通用按钮组件，其样式必须完全由 `uni.scss` 设计令牌驱动。
-   **实现示例**:
```vue
<template>
  <button
    class="app-button"
    :class="[
      `app-button--${type}`,
      `app-button--${size}`,
      { 'is-disabled': disabled, 'is-loading': loading }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <view v-if="loading" class="app-button__loading-indicator"></view>
    <view class="app-button__content">
      <slot />
    </view>
  </button>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  type?: 'primary' | 'secondary' | 'danger';
  size?: 'large' | 'medium' | 'small';
  loading?: boolean;
  disabled?: boolean;
}>(), {
  type: 'secondary',
  size: 'medium',
  loading: false,
  disabled: false,
});

const emit = defineEmits(['click']);

function handleClick(e: Event) {
  if (!props.disabled && !props.loading) {
    emit('click', e);
  }
}
</script>

<style scoped lang="scss">
/* 样式完全由 uni.scss 设计令牌驱动 */
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  transition: all var(--duration-fast) ease-in-out;
  font-family: var(--font-family-base);
  
  /* 默认样式 (等同于 secondary) */
  background-color: var(--bg-color);
  color: var(--text-color-primary);

  /* 主题 */
  &--primary {
    background-color: var(--primary-color);
    color: var(--text-color-inverse);
    border-color: var(--primary-color);
    &:hover {
      background-color: var(--primary-color-hover);
    }
  }
  &--danger {
    background-color: var(--danger-color);
    color: var(--text-color-inverse);
    border-color: var(--danger-color);
  }

  /* 尺寸 */
  &--medium {
    height: 40px;
    padding: 0 var(--spacing-md);
    font-size: var(--font-size-base);
    border-radius: var(--border-radius-base);
  }
  &--large {
    height: 48px;
    padding: 0 var(--spacing-lg);
    font-size: var(--font-size-lg);
    border-radius: var(--border-radius-lg);
  }
  &--small {
    height: 32px;
    padding: 0 var(--spacing-sm);
    font-size: var(--font-size-sm);
    border-radius: var(--border-radius-sm);
  }
  
  /* 状态 */
  &:hover {
    opacity: 0.9;
  }
  &.is-disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background-color: var(--primary-color-disabled);
  }
  
  &__loading-indicator {
    width: 16px;
    height: 16px;
    margin-right: var(--spacing-sm);
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
```

### 6.2 `src/components/ModalDialog.vue`
-   **目标**: 定义通用弹窗组件，依赖 `AppButton` (通过 `easycom` 自动引入)。
-   **实现示例**:
```vue
<template>
  <view v-if="visible" class="modal-mask" @click.self="handleClose">
    <view class="modal-dialog" role="dialog" aria-modal="true" :aria-labelledby="title">
      <view class="modal-dialog__header" v-if="title">
        <text :id="title" class="modal-dialog__title">{{ title }}</text>
      </view>
      <view class="modal-dialog__content">
        <slot />
      </view>
      <view class="modal-dialog__footer">
        <app-button size="medium" @click="handleCancel">{{ cancelText }}</app-button>
        <app-button type="primary" size="medium" @click="handleConfirm" :loading="confirmLoading">{{ confirmText }}</app-button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
// AppButton 组件通过 uni-app 的 easycom 机制自动引入，无需手动 import。

withDefaults(defineProps<{
  visible: boolean;
  title?: string;
  confirmText?: string;
  cancelText?: string;
  confirmLoading?: boolean;
}>(), {
  confirmText: '确定',
  cancelText: '取消',
  confirmLoading: false,
});

const emit = defineEmits(['update:visible', 'confirm', 'cancel']);

function handleClose() {
  emit('update:visible', false);
}
function handleConfirm() {
  emit('confirm');
}
function handleCancel() {
  emit('cancel');
  handleClose();
}
</script>

<style scoped lang="scss">
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}
.modal-dialog {
  width: 85vw;
  max-width: 400px;
  background-color: var(--nav-bg-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;

  &__header {
    margin-bottom: var(--spacing-base);
  }
  &__title {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--text-color-primary);
  }
  &__content {
    color: var(--text-color-secondary);
    font-size: var(--font-size-base);
    margin-bottom: var(--spacing-lg);
  }
  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-base);
  }
}
</style>
```

### 6.3 `src/components/RoomCard.vue`
-   **目标**: 定义房间卡片组件，用于展示一个 `Room` 对象的核心信息。
-   **实现示例**:
```vue
<template>
  <view class="room-card" @click="emit('click')">
    <image class="room-card__cover" :src="room.cover_url || defaultCover" mode="aspectFill" />
    <view class="room-card__info">
      <view class="room-card__title-line">
        <text class="room-card__title">{{ room.title }}</text>
        <view v-if="room.is_private" class="room-card__private-tag">私密</view>
      </view>
      <text class="room-card__description">{{ room.description || '暂无简介' }}</text>
    </view>
    <view v-if="$slots.actions" class="room-card__actions">
      <slot name="actions" />
    </view>
  </view>
</template>

<script setup lang="ts">
import type { Room } from '../types/room';

defineProps<{
  room: Room;
}>();

const emit = defineEmits(['click']);

const defaultCover = '/static/logo.png'; // 指向一个确切存在的默认图片
</script>

<style scoped lang="scss">
.room-card {
  background-color: var(--nav-bg-color);
  border-radius: var(--border-radius-lg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  &__cover {
    width: 100%;
    height: 180px;
    background-color: var(--bg-color-hover);
  }

  &__info {
    padding: var(--spacing-md);
  }

  &__title-line {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm);
  }
  
  &__title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--text-color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__private-tag {
    background-color: var(--warning-color);
    color: var(--text-color-inverse);
    font-size: var(--font-size-sm);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--border-radius-sm);
    flex-shrink: 0;
    margin-left: var(--spacing-sm);
  }

  &__description {
    font-size: var(--font-size-base);
    color: var(--text-color-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;  
    overflow: hidden;
    min-height: 2.8em; /* 保证两行的高度 */
  }
  
  &__actions {
    padding: 0 var(--spacing-md) var(--spacing-md);
    margin-top: auto;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
```

### 6.4 `src/store/index.ts`
-   **目标**: **创建**并**导出**一个全局唯一的 Pinia 实例。
-   **实现示例**:
```typescript
import { createPinia } from 'pinia';

const pinia = createPinia();

export default pinia;
```

### 6.5 `src/store/room.ts`
-   **目标**: **实现**包含完整数据获取、分页、状态更新和错误处理逻辑的房间状态管理模块。
-   **强指令**:
    1.  **定义** `state`，包含 `rooms: Room[]`、`currentRoom: Room | null`、`loading: boolean`、`error: Error | null` 以及一个用于分页的 `pagination` 对象 (`{ page, size, total, hasMore }`)。
    2.  **实现** `fetchRooms` action：
        -   **数据流**: **调用** `src/api/room.ts` 中的 `getRoomList` 函数。
        -   **状态变化**: 必须支持分页。首次加载或刷新时，**覆盖** `rooms` 数组；加载更多时，**必须将** API 返回的新数据 `items` **追加 (append)** 到 `rooms` 数组后面。同时，**更新** `pagination` 对象中的 `page`, `total`, `hasMore` 状态。
        -   **错误处理**: **必须使用** `try...catch` 包裹 API 调用。在 `catch` 块中，**设置** `error` 状态，并将 `loading` 置为 `false`。
        -   **加载状态**: 在 action 开始时**设置** `loading` 为 `true`，在 `finally` 块中**设置**为 `false`。
    3.  **实现** `fetchRoomById` action：
        -   **数据流**: **调用** `src/api/room.ts` 中的 `getRoomDetail` 函数。
        -   **状态变化**: 成功时，**设置** `currentRoom` 的值。
        -   **错误处理**: **使用** `try...catch`，失败时**设置** `error` 状态并将 `currentRoom` 置为 `null`。

### 6.6 `src/store/session.ts`
-   **目标**: **实现**包含完整动态逻辑的场次状态管理模块。
-   **强指令**:
    1.  **定义** `state`，结构与 `room` store 类似，包含 `sessions: Session[]`、`currentSession: Session | null`、`loading`、`error` 和 `pagination`。
    2.  **实现** `fetchSessionsByRoomId` action：
        -   **数据流**: **调用** `src/api/session.ts` 中的 `getSessionList` 函数。
        -   **状态变化**: **实现**与 `fetchRooms` 相同的分页追加逻辑，**更新** `sessions` 数组和 `pagination` 状态。
        -   **错误处理**: **必须使用** `try...catch`，并在 `catch` 中**设置** `error` 状态。
        -   **加载状态**: 必须管理 `loading` 状态。
    3.  **实现** `fetchSessionById` action：
        -   **数据流**: **调用** `src/api/session.ts` 中的 `getSessionDetail` 函数。
        -   **状态变化**: 成功时**设置** `currentSession` 的值。
        -   **错误处理**: **使用** `try...catch`，失败时**设置** `error` 状态。

---

## 7. 最终交付与质量保证协议
-   **输出格式**:
    -   你必须为每个需要生成的文件，单独输出一个完整、可直接运行的代码块。
    -   每个代码块前必须用Markdown语法标注清晰的文件路径。
    -   禁止在代码之外添加任何解释、道歉或不必要的寒暄。
-   **最终一致性断言**:
    ```
    [FINAL ASSERTION]
    All generated code has been cross-validated against the design documents.
    - Dumb Component Principle: Adhered
    - Smart Store Principle: Adhered (with full dynamic logic)
    - Data Flow & Error Handling: Implemented as specified.
    ```