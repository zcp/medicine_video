<template>
  <AdminLayout>
    <div class="merge-container">
      <el-card>
        <h3 class="page-title">科室合并</h3>
        <p class="page-desc">将源科室合并到目标科室，源科室的所有专家将迁移到目标科室，源科室名将作为同义词吸入目标科室。</p>

        <el-form label-width="120px" style="max-width: 600px; margin-top: 24px">
          <el-form-item label="源科室">
            <el-select v-model="sourceId" filterable placeholder="请选择源科室（将被合并）" style="width: 100%">
              <el-option v-for="d in departments" :key="d.id" :label="`${d.name} (${d.category_name || '未分类'})`" :value="d.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="目标科室">
            <el-select v-model="targetId" filterable placeholder="请选择目标科室（保留）" style="width: 100%">
              <el-option v-for="d in departments" :key="d.id" :label="`${d.name} (${d.category_name || '未分类'})`" :value="d.id" />
            </el-select>
          </el-form-item>

          <el-form-item v-if="sourceInfo && targetInfo" label="合并预览">
            <el-alert type="info" :closable="false" show-icon>
              <template #title>
                <div>
                  <p><strong>{{ sourceInfo.name }}</strong> 的 {{ sourceInfo.expert_count }} 位专家 → <strong>{{ targetInfo.name }}</strong></p>
                  <p style="font-size: 12px; margin-top: 4px">
                    源科室名 "{{ sourceInfo.name }}" 将追加到目标科室的同义词列表
                    <span v-if="!sourceInfo.is_verified && targetInfo.is_verified">（源科室待审核，合并后自动纳入标准词）</span>
                  </p>
                </div>
              </template>
            </el-alert>
          </el-form-item>

          <el-form-item>
            <el-space>
              <el-button type="danger" :disabled="!canMerge" :loading="submitting" @click="handleMerge">确认合并</el-button>
              <el-button @click="goBack">取消</el-button>
            </el-space>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { getDepartments, mergeDepartments } from '@/api/department'
import type { ExpertDepartment } from '@/types/department'

const departments = ref<ExpertDepartment[]>([])
const sourceId = ref('')
const targetId = ref('')
const submitting = ref(false)

const sourceInfo = computed(() => departments.value.find(d => d.id === sourceId.value))
const targetInfo = computed(() => departments.value.find(d => d.id === targetId.value))
const canMerge = computed(() => sourceId.value && targetId.value && sourceId.value !== targetId.value)

const loadDepartments = async () => {
  try {
    const res = await getDepartments({ size: 200, is_active: true })
    departments.value = res.data?.items || []
  } catch {
    ElMessage.error('加载科室列表失败')
  }
}

const handleMerge = async () => {
  if (!canMerge.value) return
  try {
    await ElMessageBox.confirm(
      `确认将"${sourceInfo.value?.name}"合并到"${targetInfo.value?.name}"？此操作不可撤销。`,
      '确认合并',
      { confirmButtonText: '确认合并', cancelButtonText: '取消', type: 'warning' }
    )
    submitting.value = true
    await mergeDepartments(sourceId.value, targetId.value)
    ElMessage.success('合并成功')
    await loadDepartments()
    sourceId.value = ''
    targetId.value = ''
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '合并失败')
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  uni.navigateBack()
}

onMounted(() => {
  loadDepartments()
})
</script>

<style lang="scss" scoped>
.merge-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
  max-width: 800px;
}
.page-title {
  margin: 0 0 8px 0;
  font-size: 20px;
}
.page-desc {
  color: #909399;
  font-size: 14px;
  margin: 0;
}
</style>
