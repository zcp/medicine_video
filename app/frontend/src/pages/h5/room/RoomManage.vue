<template>
  <RoomManageLayout>
    <template #top-left>
      <div class="top-left-wrap">
        <div class="top-left-row">
          <span class="top-left-title">{{ roomDetail?.title || '加载中…' }}</span>
        </div>
        <div class="top-left-row time">
          <el-tag class="top-left-status" :type="getStatusType(roomDetail?.status)">
            {{ getStatusText(roomDetail?.status) }}
          </el-tag>
          <span class="top-left-time">开始时间 {{ formatDateTime(roomDetail?.start_time) }}</span>
        </div>
      </div>
    </template>
    <div class="room-manage-content">
      <el-space direction="vertical" size="large" style="width: 100%">
        
        <!-- 直播房间信息区（固定尺寸：对齐设计稿） -->
        <el-card class="room-info-card fixed-layout">
          <div class="room-hero">
            <div class="hero-left">
              <el-image
                class="hero-cover"
                :src="getCoverSrc(roomDetail?.cover_url)"
                fit="cover"
                @error="onHeroCoverError"
              />
            </div>
            <div class="hero-right">
              <el-tooltip :content="roomDetail?.title || '加载中...'" placement="top">
                <h2 class="room-title small">{{ roomDetail?.title || '加载中...' }}</h2>
              </el-tooltip>
              <!-- 一行：直播类型 -->
              <div class="meta-row">
                <span class="meta-label">直播类型：</span>
                <el-tag type="info" size="large">横屏直播</el-tag>
                <el-tag type="info" size="large">通用</el-tag>
              </div>
              <!-- 一行：观看限制 -->
              <div class="meta-row">
                <span class="meta-label">观看限制：</span>
                <el-tag :type="roomDetail?.is_private ? 'warning' : 'success'" size="large">
                  {{ roomDetail?.is_private ? '加密' : '公开' }}
                </el-tag>
              </div>
              <!-- 一行：开始时间 -->
              <div class="meta-row">
                <span class="meta-label">开始时间：</span>
                <span class="meta-text">{{ formatDateTime(roomDetail?.start_time) }}</span>
              </div>
            </div>
          </div>
          <!-- 右上操作按钮 -->
          <div class="hero-actions">
            <el-button size="large" @click="handleEnterLive">进入直播</el-button>
            <el-button type="primary" size="large" @click="handleOpenSettings">开播设置</el-button>
          </div>
        </el-card>

        <!-- 分组：基本设置 -->
        <h3 class="group-title">基本设置</h3>
        <el-row :gutter="12" class="grid-section">
          <!-- 基本设置区块 -->
          <el-col :span="6">
            <el-card class="function-card disabled" @click="goToBasicSettings">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399"><Setting /></el-icon>
                <div class="card-title">基本设置</div>
                <div class="card-desc">编辑直播基本信息</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="function-card disabled" @click="showComingSoon">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399"><View /></el-icon>
                <div class="card-title">观看页设置</div>
                <div class="card-desc">设置观看界面功能</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="function-card disabled" @click="showComingSoon">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399"><Promotion /></el-icon>
                <div class="card-title">广告设置</div>
                <div class="card-desc">直播界面插入广告</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="function-card disabled" @click="showComingSoon">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399"><Bell /></el-icon>
                <div class="card-title">订阅设置</div>
                <div class="card-desc">支持商家设置直播订阅通知</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="function-card disabled" @click="showComingSoon">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399"><Share /></el-icon>
                <div class="card-title">私域引流</div>
                <div class="card-desc">将用户引流到私域流量池</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="function-card" :class="{ 'clickable': true }" @click="goToTopicCreate">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#409eff"><Promotion /></el-icon>
                <div class="card-title">营销专题</div>
                <div class="card-desc">创建和管理营销专题活动</div>
                <el-button type="primary" size="small" class="enter-button">进入</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 分组：直播方式 -->
        <h3 class="group-title">直播方式</h3>
        <el-row :gutter="12" class="grid-section">
          <!-- 直播方式区块 -->
          <el-col :span="6">
            <el-card class="function-card" :class="{ 'clickable': true }"@click="goToMultiVenue">
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#409eff"><Platform /></el-icon>
                <div class="card-title">多会场直播</div>
                <div class="card-desc">设置多个直播会场</div>
                <el-button type="primary" size="small" class="enter-button">进入</el-button>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <Document />
                </el-icon>
                <div class="card-title">多语言直播</div>
                <div class="card-desc">设置不同语言的会场</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 分组：内容安全 -->
        <h3 class="group-title">内容安全</h3>
        <el-row :gutter="12" class="grid-section">
          <!-- 内容安全区块 -->
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <User />
                </el-icon>
                <div class="card-title">白名单</div>
                <div class="card-desc">设置观看白名单</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <ChatLineRound />
                </el-icon>
                <div class="card-title">跑马灯</div>
                <div class="card-desc">设置滚动文字</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 分组：其他 -->
        <h3 class="group-title">其他</h3>
        <el-row :gutter="12" class="grid-section">
          <!-- 其他区块 -->
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <FullScreen />
                </el-icon>
                <div class="card-title">进入弹窗</div>
                <div class="card-desc">设置进入弹窗</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <Link />
                </el-icon>
                <div class="card-title">页面跳转</div>
                <div class="card-desc">设置页面跳转</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <Document />
                </el-icon>
                <div class="card-title">智能字幕</div>
                <div class="card-desc">设置智能字幕</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card 
              class="function-card disabled" 
              @click="showComingSoon"
            >
              <div class="card-content">
                <el-icon class="card-icon" :size="32" color="#909399">
                  <UserFilled />
                </el-icon>
                <div class="card-title">管理员设置</div>
                <div class="card-desc">设置管理员权限</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-space>
    </div>
  </RoomManageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting,
  View,
  Promotion,
  Bell,
  Share,
  Platform,
  User,
  ChatLineRound,
  FullScreen,
  ChatDotSquare,
  Link,
  Document,
  UserFilled,
  Monitor,
  Connection
} from '@element-plus/icons-vue'
import RoomManageLayout from '@/layouts/RoomManageLayout.vue'
import { getRoomDetail } from '@/api/room'
import type { Room } from '@/types/room'
import dayjs from 'dayjs'
import { BASE_API_URL } from '@/constants/api'

// 响应式数据
const roomDetail = ref<Room | null>(null)
const loading = ref(false)
const broadcastTime = ref<Date | null>(null)
const heroCoverError = ref(false)

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

  loading.value = true
  try {
    const response = await getRoomDetail(roomId)
    if (response && response.code === 200) {
      roomDetail.value = response.data
    } else {
      throw new Error(response?.message || '获取房间详情失败')
    }
  } catch (error: any) {
    console.error('加载房间详情失败:', error)
    ElMessage.error(`加载失败: ${error.message || '请重试'}`)
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatDateTime = (dateTime: string | undefined): string => {
  if (!dateTime) return '未设置'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 封面规范化与兜底
const getCoverSrc = (url?: string) => {
  if (heroCoverError.value) return '/logo.png'
  if (!url) return '/logo.png'
  if (/^https?:\/\//.test(url)) return url
  const base = BASE_API_URL.replace(/\/+$/, '')
  const origin = base.replace(/\/api\/.*/, '')
  return origin + (url.startsWith('/') ? url : '/' + url)
}
const onHeroCoverError = () => {
  heroCoverError.value = true
}

// 获取状态类型
const getStatusType = (status: string | undefined): 'success' | 'warning' | 'info' => {
  if (!status) return 'info'
  const statusMap: Record<string, 'success' | 'warning' | 'info'> = {
    'scheduled': 'warning',
    'live': 'success',
    'finished': 'info'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string | undefined): string => {
  if (!status) return '未知'
  const statusMap: Record<string, string> = {
    'scheduled': '未开始',
    'live': '直播中',
    'finished': '已结束'
  }
  return statusMap[status] || status
}

// 跳转到基本设置
const goToBasicSettings = () => {
  const roomId = getRoomId()
  if (roomId) {
    uni.navigateTo({
      url: `/pages/room/new/RoomBasicSettings?room_id=${roomId}`
    })
  }
}

// 跳转到多会场管理
const goToMultiVenue = () => {
  const roomId = getRoomId()
  if (roomId) {
    uni.navigateTo({
      url: `/pages/room/new/MultiVenueManage?room_id=${roomId}`
    })
  }
}

// 跳转到专题创建页面
const goToTopicCreate = () => {
  const roomId = getRoomId()
  if (roomId) {
    uni.navigateTo({
      url: `/pages/topic/TopicCreate?room_id=${roomId}`
    })
  }
}

// 显示待开发提示
const showComingSoon = () => {
  ElMessage.info('功能待开发，敬请期待')
}

// 右侧操作按钮
const handleEnterLive = () => {
  const roomId = getRoomId()
  if (roomId) {
    // 跳转到新的LiveView页面
    uni.navigateTo({ 
      url: `/pages/live/new/LiveView?room_id=${roomId}` 
    })
  } else {
    ElMessage.error('无法获取房间ID')
  }
}

const handleOpenSettings = () => {
  const roomId = getRoomId()
  if (roomId) {
    uni.navigateTo({ url: `#` })
  }
}

// 页面加载
onMounted(() => {
  loadRoomDetail()
})
</script>

<style scoped>
.room-manage-content {
  padding: 12px 12px 10px; /* 收紧白色容器内边距，尤其是底部 */
}

.group-title {
  margin: 14px 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.top-left-wrap {
  display: flex;
  align-items: center;
  flex-direction: column;
}

.top-left-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.top-left-time {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.top-left-row {
  display: flex;
  align-items: center;
}

.top-left-row.time {
  width: 100%;
}

.top-left-status {
  margin-left: 12px;
}

.room-info-card {
  margin-bottom: 16px;
}

/* 顶部信息区固定布局（对齐设计稿） */
.room-info-card.fixed-layout {
  width: 1200px; /* 目标视觉宽度 */
  max-width: 100%; /* 小屏时不溢出 */
  margin: 0 auto 16px; /* 居中并留间距 */
  height: 220px; /* 固定高度 */
  overflow: hidden;
  flex: 0 0 auto; /* 避免在 el-space 的 flex 布局中被压缩 */
  position: relative; /* 使内部绝对定位基于卡片 */
}

.room-hero {
  height: 100%;
  display: grid;
  grid-template-columns: 380px 1fr; /* 左侧固定 380px，右侧自适应 */
  column-gap: 24px;
  align-items: center; /* 垂直居中 */
}

/* 右侧固定按钮区域（浮于卡片右上角） */
.hero-actions {
  position: absolute;
  top: 50%;
  right: calc(var(--el-card-padding, 20px) + 40px); /* 距离内容区右边 40px，可视对齐 */
  transform: translateY(-50%);
  display: flex;
  flex-direction: column; /* 垂直排列两个按钮 */
  gap: 12px;
}

.hero-actions :deep(.el-button) {
  width: 120px; /* 统一按钮宽度 */
  justify-content: center;
}

.hero-left {
  height: 100%;
  display: flex;
  align-items: center;
}

.hero-cover {
  width: 380px;
  height: 180px; /* 近似 16:9 内边距留白 */
  border-radius: 8px;
  background: #f2f3f5;
}

.hero-right {
  min-width: 0; /* 允许内部文本省略 */
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
}

.meta-label {
  color: #606266;
  font-size: 14px;
  flex: 0 0 auto;
}

.meta-text {
  color: #303133;
  font-size: 16px;
}

/* 让 Element Plus 的 el-space 容器把卡片居中且不压缩宽度 */
:deep(.room-manage-content > .el-space) {
  width: 100%;
}

:deep(.room-manage-content > .el-space > .el-space__item) {
  width: 100%;
  display: flex;
  justify-content: center; /* 居中 room-info-card */
}

.room-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}kuangua

.room-title.small {
  font-size: 16px;
  font-weight: 600;
}

.status-panel {
  width: 100%;
  height: 200px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.status-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.status-content {
  color: #c0c4cc;
  font-size: 24px;
  letter-spacing: 2px;
}

.preview-card {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #ffffff 100%);
  border: none;
  position: relative;
  overflow: hidden;
}

.preview-card::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120"><path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" fill="rgba(0,0,0,0.1)"/></svg>') no-repeat center bottom;
  background-size: cover;
}

.preview-content {
  position: relative;
  z-index: 1;
  padding: 24px;
  color: #333;
}

.preview-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.organization {
  margin-left: 12px;
  font-size: 14px;
  color: #666;
}

.preview-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.preview-time {
  font-size: 14px;
  color: #666;
}

.function-card {
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  height: 86px; /* 更紧凑高度 */
}

/* 强制覆盖Element Plus卡片body默认padding（20px）*/
.grid-section :deep(.el-card__body) {
  padding: 10px !important;
}

.function-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.function-card.clickable {
  border-color: #409eff;
}

.function-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.function-card.disabled:hover {
  transform: none;
  box-shadow: none;
}

.card-content {
  position: relative;
  padding: 10px 10px 10px 64px; /* 与更小图标匹配的左侧留白 */
  text-align: left;
}

.card-icon {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3a8bff 0%, #5cc2ff 100%);
  color: #fff;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 2px 0 4px 0;
}

.card-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.enter-button {
  position: absolute;
  top: 12px;
  right: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .room-manage-content {
    padding: 16px;
  }
  
  .function-card {
    margin-bottom: 12px;
  }
}
</style>
