<template>
  <view class="notify-page consumer-layout">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">推送通知</text>
      <text class="page-subtitle">向平台用户发送系统通知</text>
    </view>

    <!-- 通知表单 -->
    <view class="form-section">
      <view class="form-group">
        <text class="form-label">通知标题</text>
        <input
          v-model="form.title"
          class="form-input"
          placeholder="请输入通知标题"
          :maxlength="100"
        />
      </view>

      <view class="form-group">
        <text class="form-label">通知内容</text>
        <textarea
          v-model="form.content"
          class="form-textarea"
          placeholder="请输入通知内容"
          :maxlength="500"
        />
        <text class="form-counter">{{ form.content.length }}/500</text>
      </view>

      <view class="form-group">
        <text class="form-label">通知类型</text>
        <view class="type-selector">
          <view
            v-for="t in typeOptions"
            :key="t.value"
            class="type-option"
            :class="{ 'type-option--active': form.notification_type === t.value }"
            @click="form.notification_type = t.value"
          >
            <text>{{ t.label }}</text>
          </view>
        </view>
      </view>

      <view class="form-group">
        <text class="form-label">推送范围</text>
        <view class="scope-selector">
          <view
            class="scope-option"
            :class="{ 'scope-option--active': pushScope === 'all' }"
            @click="pushScope = 'all'"
          >
            <text>全站用户</text>
          </view>
          <view
            class="scope-option"
            :class="{ 'scope-option--active': pushScope === 'specific' }"
            @click="pushScope = 'specific'"
          >
            <text>指定用户</text>
          </view>
        </view>
      </view>

      <view v-if="pushScope === 'specific'" class="form-group">
        <text class="form-label">用户ID列表</text>
        <textarea
          v-model="specificUserIds"
          class="form-textarea form-textarea--compact"
          placeholder="一行一个用户ID"
          :maxlength="2000"
        />
        <text class="form-hint">每行输入一个用户ID，系统将仅向这些用户发送通知</text>
      </view>
    </view>

    <!-- 发送按钮 -->
    <view class="submit-area">
      <button
        class="submit-btn"
        :disabled="!canSubmit || submitting"
        @click="handleSubmit"
      >
        <text v-if="submitting">发送中...</text>
        <text v-else>发送通知</text>
      </button>
    </view>

    <!-- 推送历史 -->
    <view class="history-section">
      <view class="section-title">推送记录</view>
      <view v-if="historyLoading" class="history-empty">
        <text class="empty-text">加载中...</text>
      </view>
      <view v-else-if="history.length === 0" class="history-empty">
        <text class="empty-text">暂无推送记录</text>
      </view>
      <view v-else class="history-list">
        <view v-for="item in history" :key="item.id" class="history-item">
          <view class="history-row">
            <text class="history-title">{{ item.title }}</text>
            <text class="history-time">{{ formatTime(item.created_at) }}</text>
          </view>
          <view class="history-row">
            <text class="history-type">{{ typeLabel(item.notification_type) }}</text>
            <text class="history-status" :class="{ 'history-status--read': item.is_read }">
              {{ item.is_read ? '已读' : '未读' }}
            </text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useAdminGuard } from '@/composables/useAdminGuard';
import {
  createNotification,
  getAllNotifications,
} from '@/api/notification';
import type { CreateNotificationRequest, NotificationItem } from '@/types/notification';

const typeOptions = [
  { label: '系统通知', value: 'system' },
  { label: '订阅通知', value: 'subscription' },
  { label: '互动通知', value: 'interaction' },
] as const;

const form = reactive<CreateNotificationRequest>({
  title: '',
  content: '',
  notification_type: 'system',
});

const pushScope = ref<'all' | 'specific'>('all');
const specificUserIds = ref('');
const submitting = ref(false);
const history = ref<NotificationItem[]>([]);
const historyLoading = ref(false);

const canSubmit = computed(() => {
  if (!form.title.trim()) return false;
  if (pushScope.value === 'specific' && !specificUserIds.value.trim()) return false;
  return true;
});

async function handleSubmit() {
  if (!canSubmit.value) return;
  submitting.value = true;

  try {
    if (pushScope.value === 'specific') {
      const ids = specificUserIds.value
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean);
      if (ids.length > 0) {
        // 后端 POST /admin/notifications 原生支持 user_ids 数组批量创建
        await createNotification({ user_ids: ids, title: form.title, content: form.content, notification_type: form.notification_type });
      }
    } else {
      // 后端不支持"全站推送"（user_ids 必填，空列表 400）——明确提示而非静默失败
      uni.showToast({ title: '全站推送暂未开放，请使用指定用户推送', icon: 'none' });
      return;
    }
    uni.showToast({ title: '通知已发送', icon: 'success' });
    form.title = '';
    form.content = '';
    await loadHistory();
  } catch (e: any) {
    if (!e?.__toasted) {
      uni.showToast({ title: e?.message || '发送失败', icon: 'none' });
    }
  } finally {
    submitting.value = false;
  }
}

async function loadHistory() {
  historyLoading.value = true;
  try {
    const res = await getAllNotifications({ page: 1, size: 20 });
    if (res.code === 200) {
      history.value = res.data?.items ?? [];
    }
  } catch {
    // 静默失败
  } finally {
    historyLoading.value = false;
  }
}

function formatTime(iso: string): string {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return iso;
  }
}

function typeLabel(t: string): string {
  const m: Record<string, string> = { system: '系统', subscription: '订阅', interaction: '互动' };
  return m[t] || t;
}

onMounted(() => {
  if (!useAdminGuard()) return;
  loadHistory();
});
</script>

<style lang="scss" scoped>
.notify-page.consumer-layout {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding: 24rpx 32rpx 140rpx;
}

.page-header {
  padding: 16rpx 0 28rpx;
}

.page-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #111827;
  display: block;
}

.page-subtitle {
  font-size: 24rpx;
  color: #6b7280;
  margin-top: 6rpx;
  display: block;
}

/* 表单区 */
.form-section {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.form-group {
  margin-bottom: 28rpx;
}

.form-label {
  font-size: 28rpx;
  font-weight: 500;
  color: #374151;
  margin-bottom: 12rpx;
  display: block;
}

.form-input {
  width: 100%;
  height: 80rpx;
  border: 2rpx solid #e5e7eb;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  color: #111827;
  background: #f9fafb;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  min-height: 160rpx;
  border: 2rpx solid #e5e7eb;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
  color: #111827;
  background: #f9fafb;
  box-sizing: border-box;
}

.form-textarea--compact {
  min-height: 120rpx;
}

.form-counter {
  font-size: 22rpx;
  color: #9ca3af;
  text-align: right;
  display: block;
  margin-top: 6rpx;
}

.form-hint {
  font-size: 22rpx;
  color: #9ca3af;
  margin-top: 6rpx;
  display: block;
}

/* 类型选择器 */
.type-selector {
  display: flex;
  gap: 12rpx;
}

.type-option {
  flex: 1;
  padding: 20rpx 0;
  border-radius: 12rpx;
  text-align: center;
  font-size: 26rpx;
  color: #6b7280;
  background: #f3f4f6;
  border: 2rpx solid transparent;
}

.type-option--active {
  background: rgba(15, 118, 110, 0.08);
  border-color: #0F766E;
  color: #0F766E;
  font-weight: 500;
}

/* 范围选择器 */
.scope-selector {
  display: flex;
  gap: 12rpx;
}

.scope-option {
  flex: 1;
  padding: 20rpx 0;
  border-radius: 12rpx;
  text-align: center;
  font-size: 26rpx;
  color: #6b7280;
  background: #f3f4f6;
  border: 2rpx solid transparent;
}

.scope-option--active {
  background: rgba(15, 118, 110, 0.08);
  border-color: #0F766E;
  color: #0F766E;
  font-weight: 500;
}

/* 提交按钮 */
.submit-area {
  margin-top: 32rpx;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  background: #0F766E;
  color: #ffffff;
  border-radius: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.submit-btn[disabled] {
  background: #9ca3af;
}

/* 推送历史 */
.history-section {
  margin-top: 48rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16rpx;
}

.history-empty {
  padding: 60rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: #9ca3af;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.history-item {
  background: #ffffff;
  border-radius: 12rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.03);
}

.history-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-row + .history-row {
  margin-top: 10rpx;
}

.history-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #111827;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 22rpx;
  color: #9ca3af;
  margin-left: 16rpx;
  flex-shrink: 0;
}

.history-type {
  font-size: 22rpx;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}

.history-status {
  font-size: 22rpx;
  color: #f59e0b;
}

.history-status--read {
  color: #6b7280;
}
</style>
