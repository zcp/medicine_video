<template>
  <el-container class="topic-manage-container">
    <!-- 页面头部 -->
    <el-page-header @back="goBack" :title="currentTopic?.title || '专题管理'">
      <template #extra>
        <el-button @click="handleSave" :loading="saving">保存</el-button>
        <el-button 
          v-if="currentTopic?.status === 'draft'" 
          type="primary" 
          @click="handlePublish"
          :loading="saving"
        >
          发布
        </el-button>
        <el-button 
          v-if="currentTopic?.status === 'published'" 
          type="warning" 
          @click="handleArchive"
          :loading="saving"
        >
          归档
        </el-button>
      </template>
    </el-page-header>

    <!-- 加载状态 -->
    <el-card v-if="loading" shadow="never" class="loading-card">
      <div class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在加载专题信息...</span>
      </div>
    </el-card>

    <!-- 错误状态 -->
    <el-card v-else-if="error" shadow="never" class="error-card">
      <div class="error-container">
        <el-icon><Warning /></el-icon>
        <span>{{ error }}</span>
        <el-button type="primary" size="small" @click="retryLoad">重试</el-button>
      </div>
    </el-card>

    <!-- 专题管理内容 -->
    <template v-else-if="currentTopic">
      <el-form 
        :model="formData" 
        :rules="formRules" 
        ref="formRef"
        label-width="100px"
        class="topic-form"
      >
        <!-- 基本信息编辑 -->
        <el-card class="basic-info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <el-tag :type="getStatusType(currentTopic.status)" size="small">
                {{ getStatusText(currentTopic.status) }}
              </el-tag>
            </div>
          </template>
          
          <el-form-item label="专题标题" prop="title">
            <el-input 
              v-model="formData.title" 
              placeholder="请输入专题标题"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="专题描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="4"
              placeholder="请输入专题描述"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="Banner图片">
            <div class="banner-upload-section">
              <el-upload
                class="banner-uploader"
                :show-file-list="false"
                :before-upload="beforeUpload"
                :http-request="handleUpload"
                accept="image/*"
                drag
              >
                <img v-if="formData.banner_url" :src="formData.banner_url" class="banner-preview" />
                <div v-else class="upload-placeholder">
                  <el-icon class="upload-icon"><Plus /></el-icon>
                  <div class="upload-text">点击或拖拽上传Banner图片</div>
                  <div class="upload-hint">支持 JPG、PNG 格式，大小不超过 5MB</div>
                </div>
              </el-upload>
              <div v-if="formData.banner_url" class="upload-actions">
                <el-button size="small" @click="removeBanner">删除图片</el-button>
                <el-button size="small" type="primary" @click="reuploadBanner">重新上传</el-button>
              </div>
            </div>
          </el-form-item>
        </el-card>

        <!-- 分类管理 -->
        <el-card class="categories-card">
          <template #header>
            <div class="card-header">
              <span>分类管理</span>
              <el-button type="primary" size="small" @click="addCategory">
                <el-icon><Plus /></el-icon>
                添加分类
              </el-button>
            </div>
          </template>
          
          <div v-if="categories.length === 0" class="empty-categories">
            <el-empty description="暂无分类">
              <el-button type="primary" @click="addCategory">添加第一个分类</el-button>
            </el-empty>
          </div>
          
          <div v-else class="categories-list">
            <el-card
              v-for="(category, index) in categories"
              :key="category.id || index"
              class="category-card"
              shadow="hover"
            >
              <div class="category-content">
                <div class="category-header">
                  <el-input
                    v-model="category.name"
                    placeholder="请输入分类名称"
                    class="category-name-input"
                    maxlength="20"
                    show-word-limit
                  />
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click="removeCategory(index)"
                    :disabled="categories.length === 1"
                  >
                    删除
                  </el-button>
                </div>
                
                <div class="category-info">
                  <div class="room-count">
                    <el-icon><VideoPlay /></el-icon>
                    <span>已选择 {{ category.rooms?.length || 0 }} 个直播间</span>
                  </div>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="openRoomSelection(index)"
                  >
                    选择直播间
                  </el-button>
                </div>
                
                <!-- 已选择的直播间预览 -->
                <div v-if="category.rooms && category.rooms.length > 0" class="selected-rooms-preview">
                  <div class="preview-header">
                    <span>已选择的直播间</span>
                  </div>
                  <div class="rooms-list">
                    <div
                      v-for="room in category.rooms.slice(0, 3)"
                      :key="room.id"
                      class="room-item"
                    >
                      <el-image
                        :src="getCoverSrc(room.cover_url)"
                        fit="cover"
                        class="room-cover"
                      >
                        <template #error>
                          <div class="image-error">无图片</div>
                        </template>
                      </el-image>
                      <div class="room-info">
                        <div class="room-title">{{ room.title }}</div>
                        <el-tag :type="getStatusType(room.live_status)" size="small">
                          {{ getStatusText(room.live_status) }}
                        </el-tag>
                      </div>
                      <el-button
                        size="small"
                        type="danger"
                        text
                        @click="removeRoomFromCategory(index, room.id)"
                      >
                        <el-icon><Close /></el-icon>
                      </el-button>
                    </div>
                    <div v-if="category.rooms.length > 3" class="more-rooms">
                      +{{ category.rooms.length - 3 }} 个直播间
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-form>
    </template>

    <!-- 专题不存在 -->
    <el-card v-else shadow="never" class="not-found-card">
      <el-empty description="专题不存在或已被删除">
        <el-button type="primary" @click="goBack">返回</el-button>
      </el-empty>
    </el-card>

    <!-- 直播间选择弹窗 -->
    <RoomSelectionDialog
      v-model:visible="roomSelectionVisible"
      :selected-rooms="currentCategoryRooms"
      :exclude-room-ids="getExcludedRoomIds()"
      @confirm="handleRoomSelection"
    />
  </el-container>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  VideoPlay, 
  Close, 
  Loading, 
  Warning 
} from '@element-plus/icons-vue'
import { useTopicStore } from '@/store/topic'
import { useAuthStore } from '@/store/auth'
import { storeToRefs } from 'pinia'
import RoomSelectionDialog from '@/components/h5/RoomSelectionDialog.vue'
import type { TopicEditForm, TopicCategory, RoomInCategory } from '@/types/topic'
// 与 RoomCreate.vue 保持一致：本地预览，必要时在保存/发布时统一上传
import { BASE_API_URL } from '@/constants/api'

// Store
const topicStore = useTopicStore()
const authStore = useAuthStore()
const { currentTopic, categories, loading, error } = storeToRefs(topicStore)

// 响应式数据
const formRef = ref()
const saving = ref(false)
const roomSelectionVisible = ref(false)
const currentCategoryIndex = ref(-1)
const topicId = ref('')

// 表单数据
const formData = reactive<TopicEditForm>({
  title: '',
  description: '',
  banner_url: '',
  status: 'draft'
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入专题标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述长度不能超过 500 个字符', trigger: 'blur' }
  ]
}

// 计算属性
const currentCategoryRooms = computed(() => {
  if (currentCategoryIndex.value >= 0 && currentCategoryIndex.value < categories.value.length) {
    return categories.value[currentCategoryIndex.value].rooms || []
  }
  return []
})

// 方法
const goBack = () => {
  uni.navigateBack()
}

const retryLoad = async () => {
  if (topicId.value) {
    await loadTopic()
  }
}

const loadTopic = async () => {
  try {
    await topicStore.fetchTopicById(topicId.value)
    
    // 更新表单数据
    if (currentTopic.value) {
      formData.title = currentTopic.value.title
      formData.description = currentTopic.value.description || ''
      formData.banner_url = currentTopic.value.banner_url || ''
      formData.status = currentTopic.value.status
    }
  } catch (error: any) {
    console.error('加载专题失败:', error)
    ElMessage.error(error.message || '加载专题失败')
  }
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'draft': 'info',
    'published': 'success',
    'archived': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'draft': '草稿',
    'published': '已发布',
    'archived': '已归档'
  }
  return statusMap[status] || '未知'
}

const getCoverSrc = (url?: string | null) => {
  if (!url) return '/public/logo.png'
  if (/^https?:\/\//.test(url)) return url
  const base = BASE_API_URL.replace(/\/+$/, '')
  const origin = base.replace(/\/api\/.*/, '')
  return origin + (url.startsWith('/') ? url : '/' + url)
}

const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }
  return true
}

const handleUpload = async (options: any) => {
  try {
    const file: File = options.file
    const objectUrl = URL.createObjectURL(file)
    formData.banner_url = objectUrl
    ElMessage.success('图片已选择（预览）')
  } catch (error: any) {
    console.error('处理图片失败:', error)
    ElMessage.error(error.message || '处理图片失败')
  }
}

const removeBanner = () => {
  formData.banner_url = ''
  ElMessage.success('已删除Banner图片')
}

const reuploadBanner = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e: any) => {
    const file = e.target.files[0]
    if (file && beforeUpload(file)) {
      handleUpload({ file })
    }
  }
  input.click()
}

const addCategory = () => {
  const newCategory: TopicCategory = {
    id: `temp_${Date.now()}`,
    topic_id: topicId.value,
    name: '',
    sort_order: categories.value.length,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    rooms: []
  }
  categories.value.push(newCategory)
}

const removeCategory = (index: number) => {
  if (categories.value.length <= 1) {
    ElMessage.warning('至少需要保留一个分类')
    return
  }
  
  ElMessageBox.confirm(
    '确定要删除这个分类吗？分类下的所有直播间将被移除。',
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    categories.value.splice(index, 1)
    ElMessage.success('分类已删除')
  }).catch(() => {
    // 用户取消
  })
}

const openRoomSelection = (index: number) => {
  currentCategoryIndex.value = index
  roomSelectionVisible.value = true
}

const handleRoomSelection = (rooms: RoomInCategory[]) => {
  if (currentCategoryIndex.value >= 0 && currentCategoryIndex.value < categories.value.length) {
    categories.value[currentCategoryIndex.value].rooms = rooms
    ElMessage.success(`已选择 ${rooms.length} 个直播间`)
  }
}

const removeRoomFromCategory = (categoryIndex: number, roomId: string) => {
  const category = categories.value[categoryIndex]
  if (category.rooms) {
    category.rooms = category.rooms.filter(room => room.id !== roomId)
    ElMessage.success('已移除直播间')
  }
}

const getExcludedRoomIds = () => {
  const excludedIds: string[] = []
  categories.value.forEach(category => {
    if (category.rooms) {
      category.rooms.forEach(room => {
        excludedIds.push(room.id)
      })
    }
  })
  return excludedIds
}

const validateForm = () => {
  return new Promise((resolve, reject) => {
    formRef.value.validate((valid: boolean) => {
      if (valid) {
        if (categories.value.length === 0) {
          ElMessage.error('请至少添加一个分类')
          reject(new Error('请至少添加一个分类'))
          return
        }
        
        for (let i = 0; i < categories.value.length; i++) {
          const category = categories.value[i]
          if (!category.name.trim()) {
            ElMessage.error(`第 ${i + 1} 个分类的名称不能为空`)
            reject(new Error(`第 ${i + 1} 个分类的名称不能为空`))
            return
          }
        }
        
        resolve(true)
      } else {
        reject(new Error('表单验证失败'))
      }
    })
  })
}

const handleSave = async () => {
  try {
    await validateForm()
    
    saving.value = true
    
    // 更新专题基本信息
    await topicStore.updateTopic(topicId.value, {
      title: formData.title,
      description: formData.description,
      banner_url: formData.banner_url
    })
    
    // 更新分类信息
    for (const category of categories.value) {
      if (category.id.startsWith('temp_')) {
        // 新建分类
        await topicStore.createCategory(topicId.value, {
          name: category.name,
          sort_order: category.sort_order
        })
      } else {
        // 更新分类
        await topicStore.updateCategory(category.id, {
          name: category.name,
          sort_order: category.sort_order
        })
      }
    }
    
    ElMessage.success('保存成功')
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handlePublish = async () => {
  try {
    await validateForm()
    
    saving.value = true
    
    await topicStore.updateTopic(topicId.value, {
      status: 'published'
    })
    
    ElMessage.success('发布成功')
    await loadTopic()
  } catch (error: any) {
    console.error('发布失败:', error)
    ElMessage.error(error.message || '发布失败')
  } finally {
    saving.value = false
  }
}

const handleArchive = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要归档这个专题吗？归档后用户将无法访问。',
      '确认归档',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    saving.value = true
    
    await topicStore.updateTopic(topicId.value, {
      status: 'archived'
    })
    
    ElMessage.success('归档成功')
    await loadTopic()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('归档失败:', error)
      ElMessage.error(error.message || '归档失败')
    }
  } finally {
    saving.value = false
  }
}

// 页面加载
onLoad(async (options) => {
  topicId.value = (options?.topic_id || '').toString()
  
  if (!topicId.value) {
    ElMessage.error('专题ID不能为空')
    uni.navigateBack()
    return
  }
  
  // 检查认证状态
  if (!authStore.isAuthenticated) {
    ElMessage.error('请先登录')
    uni.navigateTo({
      url: '/pages/auth/callback'
    })
    return
  }
  
  await loadTopic()
})

// 组件挂载
onMounted(() => {
  // 可以在这里添加一些初始化逻辑
})
</script>

<style lang="scss" scoped>
.topic-manage-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.topic-form {
  max-width: 1200px;
  margin: 0 auto;
}

.loading-card,
.error-card,
.not-found-card {
  margin-bottom: 20px;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.loading-container .el-icon {
  font-size: 32px;
  color: #409eff;
  margin-bottom: 12px;
}

.error-container .el-icon {
  font-size: 32px;
  color: #f56c6c;
  margin-bottom: 12px;
}

.error-container .el-button {
  margin-top: 12px;
}

.basic-info-card,
.categories-card {
  margin-bottom: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.banner-upload-section {
  .banner-uploader {
    width: 100%;
    
    .banner-preview {
      width: 100%;
      max-height: 300px;
      object-fit: cover;
      border-radius: 8px;
    }
    
    .upload-placeholder {
      width: 100%;
      height: 200px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      border: 2px dashed #d9d9d9;
      border-radius: 8px;
      background-color: #fafafa;
      transition: all 0.3s;
      
      &:hover {
        border-color: #409eff;
        background-color: #f0f9ff;
      }
      
      .upload-icon {
        font-size: 48px;
        color: #c0c4cc;
        margin-bottom: 16px;
      }
      
      .upload-text {
        font-size: 16px;
        color: #606266;
        margin-bottom: 8px;
      }
      
      .upload-hint {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .upload-actions {
    margin-top: 12px;
    display: flex;
    gap: 8px;
  }
}

.empty-categories {
  text-align: center;
  padding: 40px 0;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-card {
  .category-content {
    .category-header {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      
      .category-name-input {
        flex: 1;
      }
    }
    
    .category-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      .room-count {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #606266;
        font-size: 14px;
      }
    }
    
    .selected-rooms-preview {
      .preview-header {
        font-size: 14px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 8px;
      }
      
      .rooms-list {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        
        .room-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px;
          background-color: #f5f7fa;
          border-radius: 6px;
          border: 1px solid #e4e7ed;
          
          .room-cover {
            width: 40px;
            height: 30px;
            border-radius: 4px;
            
            .image-error {
              display: flex;
              align-items: center;
              justify-content: center;
              width: 100%;
              height: 100%;
              background-color: #f0f0f0;
              color: #c0c4cc;
              font-size: 12px;
            }
          }
          
          .room-info {
            flex: 1;
            min-width: 0;
            
            .room-title {
              font-size: 12px;
              color: #303133;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              margin-bottom: 4px;
            }
          }
        }
        
        .more-rooms {
          display: flex;
          align-items: center;
          padding: 8px 12px;
          background-color: #e4e7ed;
          color: #606266;
          border-radius: 6px;
          font-size: 12px;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .topic-manage-container {
    padding: 12px;
  }
  
  .category-card {
    .category-content {
      .category-header {
        flex-direction: column;
        gap: 8px;
      }
      
      .category-info {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
      
      .selected-rooms-preview {
        .rooms-list {
          .room-item {
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
