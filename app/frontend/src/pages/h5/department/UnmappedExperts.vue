<template>
  <AdminLayout>
    <div class="unmapped-container">
      <el-card class="table-section">
        <div class="table-header">
          <h3 class="table-title">
            未映射科室的专家
            <el-tag size="small" type="warning" style="margin-left: 8px">共 {{ pagination.total }} 人</el-tag>
          </h3>
          <el-button size="small" @click="loadUnmapped">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-alert title="以下专家的 department_id 为空，需管理员手动分配科室" type="info" :closable="false" show-icon style="margin-bottom: 16px" />

        <el-table v-loading="loading" :data="experts" stripe style="width: 100%">
          <el-table-column label="专家姓名" prop="name" min-width="180" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleAssign(row)">分配科室</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { getUnmappedExperts } from '@/api/department'
import type { UnmappedExpert } from '@/types/department'

const loading = ref(false)
const experts = ref<UnmappedExpert[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const loadUnmapped = async () => {
  loading.value = true
  try {
    const res = await getUnmappedExperts({ page: pagination.page, size: pagination.pageSize })
    experts.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (err: any) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadUnmapped()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadUnmapped()
}

const handleAssign = (row: UnmappedExpert) => {
  ElMessage.info('分配科室功能将在后续版本中集成到专家编辑页面')
}

onMounted(() => {
  loadUnmapped()
})
</script>

<style lang="scss" scoped>
.unmapped-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.table-section {
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 0 16px 0;
    .table-title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
