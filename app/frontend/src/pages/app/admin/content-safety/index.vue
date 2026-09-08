<template>
  <view class="admin-page consumer-layout">
    <view class="top-bar">
      <view class="tab-bar">
        <view
          v-for="(t, idx) in tabs"
          :key="t.key"
          class="tab-item"
          :class="{ 'tab-item--active': activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text class="tab-label">{{ t.label }}</text>
          <view v-if="activeIndex === idx" class="tab-indicator" />
        </view>
      </view>
      <view v-if="activeTab === 'rules'" class="header-actions">
        <view class="header-btn header-btn--primary" @tap="openCreateDialog">
          <text>＋ 新建</text>
        </view>
      </view>
    </view>

    <!-- 规则 Tab -->
    <view v-if="activeTab === 'rules'" class="filter-bar">
      <wd-picker
        v-model="sceneFilterIndex"
        :columns="sceneFilterCols"
        title="选择应用位置"
        :z-index="3000"
        @confirm="onSceneFilterChange"
      >
        <view class="filter-tag">{{ sceneFilterLabel }}</view>
      </wd-picker>
    </view>
    <view v-else class="filter-bar">
      <wd-picker
        v-model="sceneFilterIndex"
        :columns="sceneFilterCols"
        title="选择应用位置"
        :z-index="3000"
        @confirm="onSceneFilterChange"
      >
        <view class="filter-tag">{{ sceneFilterLabel }}</view>
      </wd-picker>
      <wd-picker
        v-model="decisionFilterIndex"
        :columns="decisionFilterCols"
        title="选择判定结果"
        :z-index="3000"
        @confirm="onDecisionFilterChange"
      >
        <view class="filter-tag">{{ decisionFilterLabel }}</view>
      </wd-picker>
    </view>

    <scroll-view
      v-if="activeTab === 'rules'"
      class="list"
      scroll-y
      :lower-threshold="120"
      @scrolltolower="loadMoreRules"
      @refresherrefresh="onRefreshRules"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
    >
      <view v-if="rulesLoading && rules.length === 0" class="state-box">
        <view v-for="i in 4" :key="i" class="skeleton-card" />
      </view>
      <view v-else-if="rules.length === 0" class="state-box placeholder-block">
        <text class="placeholder-title">{{ sceneFilter ? '该位置暂无规则' : '暂无内容安全规则' }}</text>
        <text class="placeholder-desc">点击右上角新建规则</text>
      </view>
      <view v-else class="rule-list">
        <view v-for="rule in rules" :key="rule.id" class="rule-card">
          <view class="rule-card__head">
            <text class="rule-card__name">{{ rule.rule_name }}</text>
            <switch
              :checked="rule.enabled"
              color="#0F766E"
              :disabled="ruleUpdatingId === rule.id"
              @change="toggleRuleEnabled(rule)"
            />
          </view>
          <view class="rule-card__tags">
            <text class="tag">{{ formatSceneLabel(rule.scene) }}</text>
            <text class="tag" :class="rule.action === 'block' ? 'tag--danger' : ''">
              {{ formatActionLabel(rule.action) }}
            </text>
            <text class="tag">{{ formatSeverityLabel(rule.severity) }}</text>
            <text class="tag" :class="rule.binding_level === 'statutory' ? 'tag--sys' : 'tag--custom'">
              {{ formatBindingLabel(rule.binding_level) }}
            </text>
          </view>
          <view class="rule-card__meta">
            <text class="meta-text">{{ rule.pattern }}</text>
          </view>
          <view class="rule-card__edit" @tap="openEditDialog(rule)">
            <text>编辑</text>
          </view>
        </view>
        <view v-if="!rulesHasMore && rules.length > 0" class="no-more"><text>没有更多了</text></view>
      </view>
    </scroll-view>

    <!-- 处理记录 Tab 列表 -->
    <scroll-view
      v-else
      class="list"
      scroll-y
      :lower-threshold="120"
      @scrolltolower="loadMoreLogs"
      @refresherrefresh="onRefreshLogs"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
    >
      <view v-if="logsLoading && logs.length === 0" class="state-box">
        <view v-for="i in 4" :key="i" class="skeleton-card" />
      </view>
      <view v-else-if="logs.length === 0" class="state-box placeholder-block">
        <text class="placeholder-title">暂无处理记录</text>
        <text class="placeholder-desc">内容安全检查命中后将在此显示</text>
      </view>
      <view v-else class="log-list">
        <view v-for="log in logs" :key="log.id" class="log-card">
          <view class="log-card__head">
            <text class="log-card__scene">{{ formatSceneLabel(log.scene) }}</text>
            <text class="log-card__decision" :class="decisionClass(log.decision)">
              {{ formatDecisionLabel(log.decision) }}
            </text>
            <text class="log-card__time">{{ formatTime(log.created_at) }}</text>
          </view>
          <view class="log-card__content">
            <text class="log-card__excerpt">{{ log.input_excerpt || log.normalized_excerpt || '—' }}</text>
          </view>
          <view class="log-card__meta">
            <text class="meta-text">{{ log.user_nickname || log.username || (log.user_id ? `用户 ${log.user_id.slice(0, 8)}` : '匿名') }}</text>
            <text v-if="log.matched_rule_names && log.matched_rule_names.length" class="meta-text">命中：{{ log.matched_rule_names.slice(0, 2).join('、') }}</text>
          </view>
        </view>
        <view v-if="!logsHasMore && logs.length > 0" class="no-more"><text>没有更多了</text></view>
      </view>
    </scroll-view>

    <!-- 新建/编辑规则弹窗 -->
    <ModalDialog
      :visible="dialogVisible"
      :title="dialogMode === 'create' ? '新建规则' : '编辑规则'"
      confirmText="保存"
      :confirmLoading="dialogSubmitting"
      @update:visible="dialogVisible = $event"
      @confirm="handleDialogConfirm"
      @cancel="closeDialog"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">规则名称</text>
          <input class="form-input" v-model="ruleForm.rule_name" placeholder="如：绝对化用语" />
        </view>
        <view class="form-group">
          <text class="form-label">应用位置</text>
          <wd-picker
            v-model="formSceneIdx"
            :columns="formSceneCols"
            title="选择应用位置"
            :z-index="3000"
            @confirm="onSceneFormChange"
          >
            <view class="form-picker">{{ sceneFormLabel }}</view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">目标字段</text>
          <input class="form-input" v-model="ruleForm.target_field" placeholder="如：content" />
        </view>
        <view class="form-group">
          <text class="form-label">匹配方式</text>
          <input class="form-input" v-model="ruleForm.match_type" placeholder="如：contains / regex" />
        </view>
        <view class="form-group">
          <text class="form-label">匹配内容（pattern）</text>
          <input class="form-input" v-model="ruleForm.pattern" placeholder="关键词或正则" />
        </view>
        <view class="form-group">
          <text class="form-label">动作</text>
          <wd-picker
            v-model="formActionIdx"
            :columns="formActionCols"
            title="选择动作"
            :z-index="3000"
            @confirm="onActionFormChange"
          >
            <view class="form-picker">{{ actionFormLabel }}</view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">严重级别</text>
          <wd-picker
            v-model="formSeverityIdx"
            :columns="formSeverityCols"
            title="选择严重级别"
            :z-index="3000"
            @confirm="onSeverityFormChange"
          >
            <view class="form-picker">{{ severityFormLabel }}</view>
          </wd-picker>
        </view>
        <view class="form-group">
          <text class="form-label">优先级（数字越小越先）</text>
          <input class="form-input" v-model="ruleForm.priority" type="number" placeholder="如：100" />
        </view>
        <view v-if="dialogMode === 'edit'" class="form-group form-group--switch">
          <text class="form-label">启用规则</text>
          <switch :checked="ruleForm.enabled" @change="ruleForm.enabled = $event.detail.value" color="#0F766E" />
        </view>
        <view class="form-group">
          <text class="form-label">备注</text>
          <input class="form-input" v-model="ruleForm.remark" placeholder="备注（可选）" />
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useAdminGuard } from '@/composables/useAdminGuard';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import { getContentSafetyRules, createContentSafetyRule, updateContentSafetyRule, getContentSafetyLogs } from '@/api/contentSafety';
import {
  ADMIN_SCENE_OPTIONS,
  ADMIN_SCENE_FORM_OPTIONS,
  ADMIN_ACTION_FORM_OPTIONS,
  ADMIN_DECISION_FILTER_OPTIONS,
  SCENE_DEFAULT_TARGET_FIELD,
  formatSceneLabel,
  formatActionLabel,
  formatDecisionLabel,
  formatSeverityLabel,
  formatBindingLabel,
} from '@/utils/contentSafetyDisplay';
import type { ContentSafetyRule, ContentSafetyLog } from '@/types/contentSafety';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import WdPicker from 'wot-design-uni/components/wd-picker/wd-picker.vue';

const tabs = [
  { key: 'rules', label: '规则' },
  { key: 'logs', label: '处理记录' },
];
const activeTab = ref('rules');
function onTabActivated(idx: number): void {
  const t = tabs[idx];
  if (!t) return;
  if (activeTab.value === t.key) return;
  activeTab.value = t.key;
}
const { activeIndex, handleTabTap } = useSwiperTabs(tabs.length, onTabActivated, 0);

// ===== 规则列表 =====
const rules = ref<ContentSafetyRule[]>([]);
const rulesLoading = ref(false);
const rulesPage = ref(1);
const rulesHasMore = ref(true);
const refreshing = ref(false);
const ruleUpdatingId = ref<string | null>(null);
const sceneFilter = ref('');
const sceneFilterIndex = ref(0);
const sceneFilterLabels = computed(() => ADMIN_SCENE_OPTIONS.map(o => o.label));
const sceneFilterLabel = computed(() => ADMIN_SCENE_OPTIONS[sceneFilterIndex.value]?.label || '全部位置');
// —— P2 短枚举迁移：wd-picker 列（value=index）——
const sceneFilterCols = computed(() => sceneFilterLabels.value.map((label, i) => ({ value: i, label })));

function onSceneFilterChange(e: any) {
  const idx = Number(e?.value ?? e?.detail?.value);
  sceneFilterIndex.value = idx;
  sceneFilter.value = ADMIN_SCENE_OPTIONS[idx]?.value || '';
  loadRules(true);
}

async function loadRules(refresh = false) {
  if (rulesLoading.value) return;
  rulesLoading.value = true;
  try {
    const page = refresh ? 1 : rulesPage.value;
    const params: Record<string, any> = { page, page_size: 20 };
    if (sceneFilter.value) params.scene = sceneFilter.value;
    const res = await getContentSafetyRules(params);
    if (res.code === 200) {
      const items = res.data?.items || [];
      rules.value = refresh ? items : [...rules.value, ...items];
      rulesPage.value = page + 1;
      rulesHasMore.value = (res.data?.total || 0) > (refresh ? items.length : rules.value.length);
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '加载失败', icon: 'none' });
  } finally {
    rulesLoading.value = false;
  }
}

function loadMoreRules() {
  if (rulesHasMore.value) loadRules(false);
}

async function onRefreshRules() {
  refreshing.value = true;
  await loadRules(true);
  refreshing.value = false;
}

// 启用/关闭（列表快捷开关）
async function toggleRuleEnabled(rule: ContentSafetyRule) {
  ruleUpdatingId.value = rule.id;
  try {
    await updateContentSafetyRule(rule.id, { enabled: !rule.enabled });
    rule.enabled = !rule.enabled;
    uni.showToast({ title: rule.enabled ? '已启用' : '已停用', icon: 'success' });
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    ruleUpdatingId.value = null;
  }
}

// ===== 新建/编辑弹窗 =====
const dialogVisible = ref(false);
const dialogMode = ref<'create' | 'edit'>('create');
const dialogSubmitting = ref(false);
const editingRuleId = ref<string | null>(null);
const ruleForm = ref({
  rule_name: '',
  scene: 'message' as string,
  target_field: 'content',
  match_type: 'contains',
  pattern: '',
  action: 'block' as string,
  severity: 'high' as string,
  priority: 100,
  enabled: true,
  remark: '',
});

const sceneFormLabels = computed(() => ADMIN_SCENE_FORM_OPTIONS.map(o => o.label));
const sceneFormLabel = computed(() => {
  const o = ADMIN_SCENE_FORM_OPTIONS.find(x => x.value === ruleForm.value.scene);
  return o?.label || '留言';
});
const actionFormLabels = computed(() => ADMIN_ACTION_FORM_OPTIONS.map(o => o.label));
const actionFormLabel = computed(() => {
  const o = ADMIN_ACTION_FORM_OPTIONS.find(x => x.value === ruleForm.value.action);
  return o?.label || '拦截';
});
const severityFormLabels = ['低', '中', '高', '严重'];
const severityFormLabel = computed(() => {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '严重' };
  return map[ruleForm.value.severity] || '高';
});

// —— P2 短枚举迁移：表单三列 wd-picker（value=index）+ 受控 index ——
const formSceneCols = computed(() => sceneFormLabels.value.map((label, i) => ({ value: i, label })));
const formActionCols = computed(() => actionFormLabels.value.map((label, i) => ({ value: i, label })));
const formSeverityCols = computed(() => severityFormLabels.map((label, i) => ({ value: i, label })));
const formSceneIdx = ref(0);
const formActionIdx = ref(0);
const formSeverityIdx = ref(0);

// 回填定位：按 ruleForm 值推导三列 index（options 无占位，index=下标）
function syncFormPickerIndexes() {
  const si = ADMIN_SCENE_FORM_OPTIONS.findIndex(o => o.value === ruleForm.value.scene);
  formSceneIdx.value = si >= 0 ? si : 0;
  const ai = ADMIN_ACTION_FORM_OPTIONS.findIndex(o => o.value === ruleForm.value.action);
  formActionIdx.value = ai >= 0 ? ai : 0;
  const sevMap = ['low', 'medium', 'high', 'critical'];
  const sei = sevMap.indexOf(ruleForm.value.severity);
  formSeverityIdx.value = sei >= 0 ? sei : 2;
}

function onSceneFormChange(e: any) {
  const o = ADMIN_SCENE_FORM_OPTIONS[Number(e?.value ?? e?.detail?.value)];
  if (!o) return;
  ruleForm.value.scene = o.value;
  ruleForm.value.target_field = SCENE_DEFAULT_TARGET_FIELD[o.value] || ruleForm.value.target_field;
}
function onActionFormChange(e: any) {
  const o = ADMIN_ACTION_FORM_OPTIONS[Number(e?.value ?? e?.detail?.value)];
  if (o) ruleForm.value.action = o.value;
}
function onSeverityFormChange(e: any) {
  const map = ['low', 'medium', 'high', 'critical'];
  ruleForm.value.severity = map[Number(e?.value ?? e?.detail?.value)] || 'high';
}

function openCreateDialog() {
  dialogMode.value = 'create';
  editingRuleId.value = null;
  ruleForm.value = {
    rule_name: '',
    scene: 'message',
    target_field: 'content',
    match_type: 'contains',
    pattern: '',
    action: 'block',
    severity: 'high',
    priority: 100,
    enabled: true,
    remark: '',
  };
  dialogVisible.value = true;
  syncFormPickerIndexes();
}

function openEditDialog(rule: ContentSafetyRule) {
  dialogMode.value = 'edit';
  editingRuleId.value = rule.id;
  ruleForm.value = {
    rule_name: rule.rule_name || '',
    scene: rule.scene || 'message',
    target_field: rule.target_field || '',
    match_type: rule.match_type || 'contains',
    pattern: rule.pattern || '',
    action: rule.action || 'block',
    severity: rule.severity || 'high',
    priority: rule.priority ?? 100,
    enabled: rule.enabled,
    remark: rule.remark || '',
  };
  syncFormPickerIndexes();
  dialogVisible.value = true;
}

function closeDialog() {
  dialogVisible.value = false;
}

async function handleDialogConfirm() {
  if (!ruleForm.value.rule_name.trim()) {
    uni.showToast({ title: '请输入规则名称', icon: 'none' });
    return;
  }
  if (!ruleForm.value.pattern.trim()) {
    uni.showToast({ title: '请输入匹配内容', icon: 'none' });
    return;
  }
  dialogSubmitting.value = true;
  try {
    if (dialogMode.value === 'create') {
      await createContentSafetyRule({
        rule_name: ruleForm.value.rule_name.trim(),
        scene: ruleForm.value.scene as any,
        target_field: ruleForm.value.target_field.trim(),
        match_type: ruleForm.value.match_type.trim(),
        pattern: ruleForm.value.pattern.trim(),
        action: ruleForm.value.action as any,
        severity: ruleForm.value.severity as any,
        priority: Number(ruleForm.value.priority) || 100,
        enabled: ruleForm.value.enabled,
        remark: ruleForm.value.remark.trim() || undefined,
      });
      uni.showToast({ title: '规则已创建', icon: 'success' });
    } else {
      if (!editingRuleId.value) return;
      await updateContentSafetyRule(editingRuleId.value, {
        pattern: ruleForm.value.pattern.trim(),
        action: ruleForm.value.action as any,
        severity: ruleForm.value.severity as any,
        priority: Number(ruleForm.value.priority) || 100,
        enabled: ruleForm.value.enabled,
        remark: ruleForm.value.remark.trim() || undefined,
      });
      uni.showToast({ title: '规则已保存', icon: 'success' });
    }
    closeDialog();
    loadRules(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    dialogSubmitting.value = false;
  }
}

// ===== 处理记录（日志） =====
const logs = ref<ContentSafetyLog[]>([]);
const logsLoading = ref(false);
const logsPage = ref(1);
const logsHasMore = ref(true);
const decisionFilter = ref('');
const decisionFilterIndex = ref(0);
const decisionFilterLabels = computed(() => ADMIN_DECISION_FILTER_OPTIONS.map(o => o.label));
const decisionFilterLabel = computed(() => ADMIN_DECISION_FILTER_OPTIONS[decisionFilterIndex.value]?.label || '全部结果');
// —— P2 短枚举迁移：wd-picker 列（value=index）——
const decisionFilterCols = computed(() => decisionFilterLabels.value.map((label, i) => ({ value: i, label })));

function onDecisionFilterChange(e: any) {
  const idx = Number(e?.value ?? e?.detail?.value);
  decisionFilterIndex.value = idx;
  decisionFilter.value = ADMIN_DECISION_FILTER_OPTIONS[idx]?.value || '';
  loadLogs(true);
}

async function loadLogs(refresh = false) {
  if (logsLoading.value) return;
  logsLoading.value = true;
  try {
    const page = refresh ? 1 : logsPage.value;
    const params: Record<string, any> = { page, page_size: 20 };
    if (sceneFilter.value) params.scene = sceneFilter.value;
    if (decisionFilter.value) params.decision = decisionFilter.value;
    const res = await getContentSafetyLogs(params);
    if (res.code === 200) {
      const items = res.data?.items || [];
      logs.value = refresh ? items : [...logs.value, ...items];
      logsPage.value = page + 1;
      logsHasMore.value = (res.data?.total || 0) > (refresh ? items.length : logs.value.length);
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '加载失败', icon: 'none' });
  } finally {
    logsLoading.value = false;
  }
}

function loadMoreLogs() {
  if (logsHasMore.value) loadLogs(false);
}

async function onRefreshLogs() {
  refreshing.value = true;
  await loadLogs(true);
  refreshing.value = false;
}

function decisionClass(decision: string): string {
  if (decision === 'block') return 'log-card__decision--block';
  if (decision === 'warn') return 'log-card__decision--warn';
  return 'log-card__decision--allow';
}

function formatTime(timeStr: string): string {
  if (!timeStr) return '';
  const d = new Date(timeStr);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

onMounted(() => {
  if (!useAdminGuard()) return;
  loadRules(true);
});

// 切换到日志 Tab 时首次加载
watch(activeTab, (v) => {
  if (v === 'logs' && logs.value.length === 0) loadLogs(true);
});

onUnmounted(() => {});
</script>

<style lang="scss" scoped>
.admin-page {
  min-height: 100vh;
  background: var(--home-bg, #f5f6f8);
}
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 24rpx;
  background: #fff;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
}
.tab-bar { display: flex; align-items: center; gap: 32rpx; }
.tab-item { position: relative; padding: 8rpx 4rpx; }
.tab-label { font-size: 28rpx; color: #666; }
.tab-item--active .tab-label { color: #0F766E; font-weight: 600; }
.tab-indicator {
  position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 32rpx; height: 4rpx; border-radius: 2rpx; background: #0F766E;
}
.header-actions { display: flex; align-items: center; gap: 16rpx; }
.header-btn { font-size: 26rpx; color: #666; padding: 8rpx 16rpx; }
.header-btn--primary { color: #fff; background: #0F766E; border-radius: 8rpx; }

.filter-bar {
  display: flex; align-items: center; gap: 16rpx; flex-wrap: wrap;
  padding: 16rpx 24rpx; background: #fff; border-bottom: 1rpx solid rgba(0,0,0,0.04);
}
.filter-tag {
  font-size: 26rpx; color: #333; background: #f5f5f5;
  padding: 10rpx 24rpx; border-radius: 8rpx;
}

.list { height: calc(100vh - 220rpx); }

.state-box { padding: 120rpx 24rpx; text-align: center; }
.skeleton-card { height: 140rpx; background: #f0f0f0; border-radius: 12rpx; margin-bottom: 16rpx; }
.placeholder-title { display: block; font-size: 28rpx; color: #333; margin-bottom: 8rpx; }
.placeholder-desc { font-size: 24rpx; color: #999; }

.rule-list, .log-list { padding: 16rpx 24rpx; }
.rule-card {
  position: relative;
  background: #fff; border-radius: 12rpx; padding: 24rpx; margin-bottom: 16rpx;
}
.rule-card__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.rule-card__name { font-size: 28rpx; font-weight: 600; color: #1a1a1a; flex: 1; margin-right: 16rpx; }
.rule-card__tags { display: flex; align-items: center; gap: 12rpx; flex-wrap: wrap; margin-bottom: 8rpx; }
.tag {
  font-size: 22rpx; color: #0F766E; background: rgba(15, 118, 110, 0.08);
  padding: 4rpx 14rpx; border-radius: 20rpx;
}
.tag--danger { color: #dc2626; background: rgba(220, 38, 38, 0.08); }
.tag--sys { color: #666; background: #f0f0f0; }
.tag--custom { color: #b45309; background: rgba(180, 83, 9, 0.08); }
.rule-card__meta { font-size: 22rpx; color: #999; word-break: break-all; }
.rule-card__edit {
  position: absolute; right: 24rpx; bottom: 24rpx;
  font-size: 24rpx; color: #0F766E;
}

.log-card { background: #fff; border-radius: 12rpx; padding: 24rpx; margin-bottom: 16rpx; }
.log-card__head { display: flex; align-items: center; gap: 16rpx; margin-bottom: 10rpx; }
.log-card__scene { font-size: 24rpx; color: #0F766E; background: rgba(15,118,110,0.08); padding: 4rpx 14rpx; border-radius: 20rpx; }
.log-card__decision { font-size: 24rpx; font-weight: 600; }
.log-card__decision--block { color: #dc2626; }
.log-card__decision--warn { color: #b45309; }
.log-card__decision--allow { color: #16a34a; }
.log-card__time { font-size: 22rpx; color: #999; margin-left: auto; }
.log-card__content { margin-bottom: 8rpx; }
.log-card__excerpt { font-size: 26rpx; color: #333; word-break: break-all; }
.log-card__meta { display: flex; gap: 24rpx; font-size: 22rpx; color: #999; }
.meta-text { font-size: 22rpx; color: #999; }
.no-more { text-align: center; padding: 24rpx; font-size: 24rpx; color: #999; }

.form { padding: 8rpx 0; }
.form-group { margin-bottom: 24rpx; }
.form-label { display: block; font-size: 26rpx; color: #666; margin-bottom: 10rpx; }
.form-input {
  height: 72rpx; background: #f5f5f5; border-radius: 10rpx;
  padding: 0 20rpx; font-size: 28rpx; color: #333;
}
.form-picker {
  height: 72rpx; background: #f5f5f5; border-radius: 10rpx;
  display: flex; align-items: center; padding: 0 20rpx; font-size: 28rpx; color: #333;
}
.form-group--switch {
  display: flex; align-items: center; justify-content: space-between;
}
</style>
