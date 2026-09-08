<template>
  <AdminLayout>
    <div class="expert-create-container">
      <el-card class="main-card">
        <h3 class="page-title">创建专家</h3>

        <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" style="max-width: 700px">
          <el-form-item label="专家姓名" prop="name">
            <el-input v-model="formData.name" placeholder="请输入专家姓名" maxlength="120" />
          </el-form-item>

          <el-form-item label="职称">
            <el-input v-model="formData.title" placeholder="如：主任医师、教授" maxlength="120" />
          </el-form-item>

          <el-form-item label="所在医院">
            <el-input v-model="formData.hospital" placeholder="请输入医院名称" maxlength="200" />
          </el-form-item>

          <el-form-item label="所属科室" prop="department_name">
            <el-select v-model="formData.department_name" filterable allow-create placeholder="搜索或选择科室" style="width: 100%">
              <el-option v-for="d in departments" :key="d.id" :label="`${d.name} / ${d.category_name || '未分类'}`" :value="d.name" />
            </el-select>
            <div class="form-tip">从受控词表选择，若输入新名称系统将自动创建待审核科室</div>
          </el-form-item>

          <el-form-item label="主分类">
            <el-select v-model="formData.category_id" filterable placeholder="可选，留空则根据科室自动归类" clearable style="width: 100%">
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
            <div class="form-tip">管理员可手动指定分类，优先级高于科室的自动归类</div>
          </el-form-item>

          <el-form-item label="擅长领域">
            <el-input v-model="formData.expertise_areas" type="textarea" :rows="2" placeholder="用逗号分隔多个领域" maxlength="500" show-word-limit />
          </el-form-item>

          <el-form-item label="个人简介">
            <el-input v-model="formData.bio" type="textarea" :rows="3" placeholder="专家简介" maxlength="10000" />
          </el-form-item>

          <el-form-item label="头像URL">
            <el-input v-model="formData.avatar_url" placeholder="可选，输入头像图片URL" />
          </el-form-item>

          <el-form-item label="首页推荐">
            <el-switch v-model="formData.is_featured" />
          </el-form-item>

          <el-form-item>
            <el-space>
              <el-button type="primary" :loading="submitting" @click="handleSubmit">创建专家</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-space>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { createExpert } from '@/api/expert'
import { getDepartments } from '@/api/department'
import { getCategories } from '@/api/category'
import type { ExpertCreatePayload } from '@/types/expert'
import type { ExpertDepartmentBrief } from '@/types/department'
import type { Category } from '@/types/category'

const formRef = ref<any>(null)
const submitting = ref(false)
const departments = ref<ExpertDepartmentBrief[]>([])
const categories = ref<Category[]>([])

const formData = reactive<{
  name: string
  title: string
  hospital: string
  department_name: string
  category_id: string
  expertise_areas: string
  bio: string
  avatar_url: string
  is_featured: boolean
}>({
  name: '',
  title: '',
  hospital: '',
  department_name: '',
  category_id: '',
  expertise_areas: '',
  bio: '',
  avatar_url: '',
  is_featured: false,
})

const formRules = {
  name: [{ required: true, message: '请输入专家姓名', trigger: 'blur' }],
  department_name: [{ required: true, message: '请选择或输入科室', trigger: 'change' }],
}

const loadDepartments = async () => {
  try {
    const res = await getDepartments({ is_active: true, size: 200 })
    departments.value = (res.data?.items || []).map(d => ({
      id: d.id,
      name: d.name,
      category_id: d.category_id,
      category_name: d.category_name,
    }))
  } catch {
    console.warn('科室列表加载失败')
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

const handleSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload: ExpertCreatePayload = {
      name: formData.name,
      title: formData.title || undefined,
      hospital: formData.hospital || undefined,
      department_name: formData.department_name,
      category_id: formData.category_id || undefined,
      expertise_areas: formData.expertise_areas || undefined,
      bio: formData.bio || undefined,
      avatar_url: formData.avatar_url || undefined,
      is_featured: formData.is_featured,
    }
    await createExpert(payload)
    ElMessage.success('专家创建成功')
    handleReset()
  } catch (err: any) {
    ElMessage.error(err.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  formData.name = ''
  formData.title = ''
  formData.hospital = ''
  formData.department_name = ''
  formData.category_id = ''
  formData.expertise_areas = ''
  formData.bio = ''
  formData.avatar_url = ''
  formData.is_featured = false
}

onMounted(() => {
  loadDepartments()
  loadCategories()
})
</script>

<style lang="scss" scoped>
.expert-create-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}
.main-card {
  max-width: 800px;
}
.page-title {
  margin: 0 0 24px 0;
  font-size: 20px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
