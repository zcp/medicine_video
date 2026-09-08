<template>
  <RoomManageLayout>
    <div class="basic-settings-content">
      <el-card class="settings-card">
        <!-- 页面标题 -->
        <el-page-header @back="goBack" content="基本设置">
          <template #extra>
            <el-space>
              <el-button @click="goBack">取消</el-button>
              <el-button 
                type="primary" 
                :loading="saving"
                @click="handleSave"
              >
                保存
              </el-button>
            </el-space>
          </template>
        </el-page-header>

        <!-- 表单区域 -->
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-position="top"
          class="settings-form"
        >
          <el-row :gutter="24">
            <el-col :span="12">
              <!-- 直播名称 -->
              <el-form-item label="直播名称" prop="title" required>
                <el-input
                  v-model="formData.title"
                  placeholder="请输入直播名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <!-- 观看方式 -->
              <el-form-item label="观看方式" prop="is_private">
                <el-radio-group v-model="formData.is_private">
                  <el-radio :label="false">公开</el-radio>
                  <el-radio :label="true">加密</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <!-- 直播封面 -->
              <el-form-item label="直播封面" prop="cover_url">
                <el-upload
                  class="cover-uploader"
                  :action="uploadAction"
                  :headers="uploadHeaders"
                  :show-file-list="false"
                  :on-success="handleUploadSuccess"
                  :on-error="handleUploadError"
                  :before-upload="beforeUpload"
                  accept="image/*"
                >
                  <el-image
                    v-if="formData.cover_url"
                    :src="formData.cover_url"
                    class="cover-image"
                    fit="cover"
                  />
                  <el-icon v-else class="cover-uploader-icon">
                    <Plus />
                  </el-icon>
                </el-upload>
                <div class="upload-tips">
                  <el-text type="info" size="small">
                    支持JPG、PNG格式，建议尺寸16:9，大小不超过2MB
                  </el-text>
                </div>
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <!-- 直播描述 -->
              <el-form-item label="直播描述" prop="description">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="6"
                  placeholder="请输入直播描述（选填）"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <!-- 开始时间 -->
              <el-form-item label="开始时间" prop="start_time">
                <el-date-picker
                  v-model="formData.start_time"
                  type="datetime"
                  placeholder="选择开始时间"
                  format="YYYY-MM-DD HH:mm"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <!-- 直播类型 -->
              <el-form-item label="直播类型">
                <el-select v-model="formData.live_type" placeholder="选择直播类型" style="width: 100%">
                  <el-option label="视频直播" value="video" />
                  <el-option label="图文直播" value="image" />
                  <el-option label="VR直播" value="vr" />
                  <el-option label="语音直播" value="audio" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- Stream Key 展示（只读） -->
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="Stream Key" prop="stream_key">
                <el-input v-model="formData.stream_key" readonly>
                  <template #append>
                    <el-button @click="copyStreamKey" :disabled="!formData.stream_key">复制</el-button>
                  </template>
                </el-input>
                <div v-if="formData.stream_key" class="upload-tips">
                  <el-text type="info" size="small">后端返回的推流密钥（stream_key），用于拼接播放/推流地址</el-text>
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <!-- 显示模式 -->
              <el-form-item label="显示模式">
                <el-radio-group v-model="formData.display_mode">
                  <el-radio label="landscape">横屏</el-radio>
                  <el-radio label="portrait">竖屏</el-radio>
                  <el-radio label="split">三分屏</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <!-- 直播形式 -->
              <el-form-item label="直播形式">
                <el-radio-group v-model="formData.live_format">
                  <el-radio label="live">直播</el-radio>
                  <el-radio label="vod">点播/录播</el-radio>
                  <el-radio label="fake">伪直播</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </div>
  </RoomManageLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import RoomManageLayout from '@/layouts/RoomManageLayout.vue'
import { getRoomDetail, updateRoom } from '@/api/room'
import type { Room } from '@/types/room'
import { getToken } from '@/store/auth'
import dayjs from 'dayjs'

// 响应式数据
const formRef = ref()
const saving = ref(false)
const roomDetail = ref<Room | null>(null)

// 表单数据
const formData = reactive({
  title: '',
  description: '',
  cover_url: '',
  is_private: false,
  start_time: '',
  live_type: 'video',
  display_mode: 'landscape',
  live_format: 'live',
  stream_key: ''
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入直播名称', trigger: 'blur' },
    { min: 1, max: 100, message: '直播名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '直播描述不能超过 500 个字符', trigger: 'blur' }
  ]
}

// 上传配置
const uploadAction = '/api/v1/upload/image'
const uploadHeaders = {
  'Authorization': `Bearer ${getToken()}`
}

// 获取房间ID
const getRoomId = (): string | null => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  return currentPage.options?.room_id || null
}

// 加载房间详情
const loadRoomDetail = async () => {
  const roomId = getRoomId()
  if (!roomId) {
    ElMessage.error('房间ID不存在')
    return
  }

  try {
    const response = await getRoomDetail(roomId)
    if (response && response.code === 200) {
      roomDetail.value = response.data
      
      // 填充表单数据
      formData.title = response.data.title || ''
      formData.description = response.data.description || ''
      formData.cover_url = response.data.cover_url || ''
      formData.is_private = response.data.is_private || false
      formData.start_time = response.data.start_time || ''
      // 后端返回的 stream_key（可选）
      formData.stream_key = (response.data as any).stream_key || ''
    } else {
      throw new Error(response?.message || '获取房间详情失败')
    }
  } catch (error: any) {
    console.error('加载房间详情失败:', error)
    ElMessage.error(`加载失败: ${error.message || '请重试'}`)
  }
}

// 上传前验证
const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

// 上传成功
const handleUploadSuccess = (response: any) => {
  if (response && response.code === 200) {
    formData.cover_url = response.data.url
    ElMessage.success('封面上传成功')
  } else {
    ElMessage.error(response?.message || '封面上传失败')
  }
}

// 上传失败
const handleUploadError = (error: any) => {
  console.error('上传失败:', error)
  ElMessage.error('封面上传失败，请重试')
}

// 保存设置
const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    saving.value = true
    
    const roomId = getRoomId()
    if (!roomId) {
      ElMessage.error('房间ID不存在')
      return
    }

    // 构建更新数据
    const updateData: Partial<Room> = {
      title: formData.title,
      description: formData.description,
      cover_url: formData.cover_url,
      is_private: formData.is_private
    }

    // 如果有开始时间，也更新
    if (formData.start_time) {
      updateData.start_time = formData.start_time
    }

    const response = await updateRoom(roomId, updateData)
    if (response && response.code === 200) {
      ElMessage.success('保存成功')
      // 可以选择返回上一页或刷新数据
      setTimeout(() => {
        goBack()
      }, 1000)
    } else {
      throw new Error(response?.message || '保存失败')
    }
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(`保存失败: ${error.message || '请重试'}`)
  } finally {
    saving.value = false
  }
}

// 返回上一页
const goBack = () => {
  uni.navigateBack()
}

// 复制 stream_key
const copyStreamKey = async () => {
  try {
    if (!formData.stream_key) return
    await navigator.clipboard.writeText(formData.stream_key)
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败，请手动选择复制')
  }
}

// 页面加载
onMounted(() => {
  loadRoomDetail()
})
</script>

<style scoped>
.basic-settings-content {
  padding: 24px;
}

.settings-card {
  max-width: 1200px;
  margin: 0 auto;
}

.settings-form {
  margin-top: 24px;
}

.cover-uploader {
  width: 100%;
}

.cover-uploader :deep(.el-upload) {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-uploader :deep(.el-upload:hover) {
  border-color: #409eff;
}

.cover-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 6px;
}

.cover-uploader-icon {
  font-size: 28px;
  color: #8c939d;
}

.upload-tips {
  margin-top: 8px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .basic-settings-content {
    padding: 16px;
  }
  
  .settings-form .el-col {
    margin-bottom: 16px;
  }
}

/* 表单样式优化 */
.settings-form .el-form-item {
  margin-bottom: 24px;
}

.settings-form .el-form-item__label {
  font-weight: 600;
  color: #303133;
}

.settings-form .el-input,
.settings-form .el-textarea,
.settings-form .el-select,
.settings-form .el-date-picker {
  width: 100%;
}

.settings-form .el-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.settings-form .el-radio {
  margin-right: 0;
}
</style>
