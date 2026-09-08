<template>
  <AdminLayout>
    <div class="department-manage-container">
      <!-- 顶部筛选区域 -->
      <el-card class="search-section">
        <el-form :model="filterForm" inline class="search-form">
          <el-form-item label="审核状态">
            <el-select v-model="filterForm.verifiedTab" placeholder="全部" clearable style="width: 130px" @change="handleTabChange">
              <el-option label="全部科室" value="" />
              <el-option label="已审核" :value="true" />
              <el-option label="待审核" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item label="科室名称">
            <el-input v-model="filterForm.q" placeholder="搜索科室名称" clearable style="width: 200px" @keyup.enter="handleSearch" />
          </el-form-item>
          <el-form-item label="所属分类">
            <el-select v-model="filterForm.category_id" placeholder="全部" clearable style="width: 150px" @change="handleSearch">
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              新增科室
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 数据表格 -->
      <el-card class="table-section">
        <div class="table-header">
          <h3 class="table-title">
            科室列表
            <el-tag size="small" type="info" style="margin-left: 8px">共 {{ pagination.total }} 条</el-tag>
          </h3>
          <el-button size="small" @click="loadDepartments">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-table v-loading="loading" :data="departments" stripe style="width: 100%">
          <el-table-column label="科室名称" prop="name" min-width="160" />
          <el-table-column label="所属分类" prop="category_name" width="140" />
          <el-table-column label="同义词" width="200">
            <template #default="{ row }">
              <span v-if="row.synonyms?.length" class="synonyms-text">{{ row.synonyms.join(', ') }}</span>
              <span v-else class="no-data">--</span>
            </template>
          </el-table-column>
          <!-- expert_count 暂时隐藏：后端 get_departments_paginated 缺子查询计算，始终返回 0 -->
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_verified ? 'success' : 'warning'" size="small">
                {{ row.is_verified ? '已审核' : '待审核' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="启用" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-space>
                <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button v-if="!row.is_verified" link type="success" size="small" @click="handleApprove(row)">审核通过</el-button>
                <el-button link type="warning" size="small" @click="handleMerge(row)">合并</el-button>
                <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </el-space>
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

      <!-- 创建/编辑对话框 -->
      <el-dialog v-model="showCreateDialog" :title="isEditing ? '编辑科室' : '新增科室'" width="500px" @close="resetForm">
        <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
          <el-form-item label="科室名称" prop="name">
            <el-input v-model="formData.name" placeholder="请输入标准科室名称" maxlength="120" />
          </el-form-item>
          <el-form-item label="所属分类" prop="category_id">
            <el-select v-model="formData.category_id" placeholder="请选择所属分类" style="width: 100%">
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="同义词">
            <el-select v-model="formData.synonyms" multiple filterable allow-create default-first-option placeholder="输入同义词后回车" style="width: 100%">
              <el-option v-for="s in formData.synonyms" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="审核状态">
            <el-switch v-model="formData.is_verified" active-text="已审核" inactive-text="待审核" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { getDepartments, createDepartment, updateDepartment, deleteDepartment } from '@/api/department'
import { getCategories } from '@/api/category'
import type { ExpertDepartment, ExpertDepartmentCreatePayload, ExpertDepartmentUpdatePayload } from '@/types/department'
import type { Category } from '@/types/category'

const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const departments = ref<ExpertDepartment[]>([])
const categories = ref<Category[]>([])
const formRef = ref<any>(null)

const filterForm = reactive({
  verifiedTab: '' as boolean | '',
  q: '',
  category_id: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const formData = reactive<{
  name: string
  category_id: string
  synonyms: string[]
  is_verified: boolean
}>({
  name: '',
  category_id: '',
  synonyms: [],
  is_verified: false,
})

const formRules = {
  name: [{ required: true, message: '请输入科室名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择所属分类', trigger: 'change' }],
}

const loadDepartments = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, size: pagination.pageSize }
    if (filterForm.verifiedTab !== '') params.is_verified = filterForm.verifiedTab
    if (filterForm.q) params.q = filterForm.q
    if (filterForm.category_id) params.category_id = filterForm.category_id
    const res = await getDepartments(params)
    departments.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (err: any) {
    ElMessage.error(err.message || '加载科室列表失败')
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const res = await getCategories()
    categories.value = res.data || []
  } catch {
    console.warn('分类加载失败')
  }
}

const handleTabChange = () => {
  pagination.page = 1
  loadDepartments()
}

const handleSearch = () => {
  pagination.page = 1
  loadDepartments()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadDepartments()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadDepartments()
}

const resetForm = () => {
  formData.name = ''
  formData.category_id = ''
  formData.synonyms = []
  formData.is_verified = false
  isEditing.value = false
  editingId.value = null
}

const handleEdit = (row: ExpertDepartment) => {
  isEditing.value = true
  editingId.value = row.id
  formData.name = row.name
  formData.category_id = row.category_id
  formData.synonyms = row.synonyms || []
  formData.is_verified = row.is_verified
  showCreateDialog.value = true
}

const handleApprove = async (row: ExpertDepartment) => {
  try {
    await updateDepartment(row.id, { is_verified: true })
    ElMessage.success('审核通过')
    loadDepartments()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

const handleMerge = (row: ExpertDepartment) => {
  uni.navigateTo({ url: `/pages/h5/department/DepartmentMerge?sourceId=${row.id}&sourceName=${encodeURIComponent(row.name)}` })
}

const handleDelete = async (row: ExpertDepartment) => {
  try {
    await ElMessageBox.confirm(`确定要删除科室"${row.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteDepartment(row.id)
    ElMessage.success('删除成功')
    loadDepartments()
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '删除失败')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      const payload: ExpertDepartmentUpdatePayload = {
        name: formData.name,
        category_id: formData.category_id,
        synonyms: formData.synonyms,
        is_verified: formData.is_verified,
      }
      await updateDepartment(editingId.value, payload)
      ElMessage.success('更新成功')
    } else {
      const payload: ExpertDepartmentCreatePayload = {
        name: formData.name,
        category_id: formData.category_id,
        synonyms: formData.synonyms,
        is_verified: formData.is_verified,
      }
      await createDepartment(payload)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    loadDepartments()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '--'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return '--'
  }
}

onMounted(() => {
  loadCategories()
  loadDepartments()
})
</script>

<style lang="scss" scoped>
.department-manage-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.search-section {
  margin-bottom: 20px;
  .search-form {
    width: 100%;
    .el-form-item { margin-bottom: 0; }
  }
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

.synonyms-text {
  font-size: 12px;
  color: #606266;
}

.no-data {
  color: #c0c4cc;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
