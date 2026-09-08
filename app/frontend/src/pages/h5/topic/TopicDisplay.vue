<template>
  <el-container class="venue-container">
    <el-main class="venue-main">
      <div class="venue-inner">
        <!-- 加载状态 -->
        <el-card v-if="loading" shadow="never" class="loading-card">
          <div class="loading-container">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在加载专题...</span>
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

        <!-- 专题内容 -->
        <template v-else-if="currentTopic">
          <!-- 顶部主视觉 Banner -->
          <el-card shadow="never" class="banner-card">
            <div class="banner-content">
              <img 
                class="banner-img" 
                :src="getBannerSrc(currentTopic.banner_url)" 
                :alt="currentTopic.title"
                @error="handleBannerError"
              />
              <div class="banner-overlay">
                <h1 class="banner-title">{{ currentTopic.title }}</h1>
                <p v-if="currentTopic.description" class="banner-desc">{{ currentTopic.description }}</p>
              </div>
            </div>
          </el-card>

          <!-- 分类标签页 -->
          <el-tabs v-model="activeTab" class="venue-tabs" v-if="categories.length > 0">
            <el-tab-pane 
              v-for="category in categories" 
              :key="category.id" 
              :label="category.name" 
              :name="category.id"
            >
              <el-space direction="vertical" :size="12" style="width:100%">
                <!-- 直播间卡片列表 -->
                <template v-if="getCategoryRooms(category.id).length > 0">
                  <el-row :gutter="10">
                    <el-col 
                      v-for="room in getCategoryRooms(category.id)" 
                      :key="room.id" 
                      :xs="24" 
                      :sm="24" 
                      :md="24" 
                      :lg="24"
                    >
                      <el-card shadow="hover" class="venue-card dense" @click="goLive(room.id)">
                        <div class="venue-card-inner">
                          <el-image class="venue-cover small" :src="getCoverSrc(room.cover_url)" fit="cover">
                            <template #error>
                              <div class="img-error">No Image</div>
                            </template>
                          </el-image>
                          <div class="venue-info">
                            <div class="venue-title one-line" :title="room.title">{{ room.title }}</div>
                            <div class="venue-meta one-line">
                              <span>开始时间：{{ formatTime(room.start_time) }}</span>
                              <span class="meta-split">·</span>
                              <span>热度：{{ room.heat || 0 }}</span>
                            </div>
                          </div>
                          <el-tag 
                            class="status-badge" 
                            size="small" 
                            :type="statusType(room.live_status)"
                          >
                            {{ statusText(room.live_status) }}
                          </el-tag>
                        </div>
                      </el-card>
                    </el-col>
                  </el-row>
                </template>
                <el-empty v-else description="该分类下暂无直播间"></el-empty>
              </el-space>
            </el-tab-pane>
          </el-tabs>

          <!-- 无分类时的提示 -->
          <el-card v-else shadow="never" class="empty-categories-card">
            <el-empty description="该专题暂无分类">
              <el-button type="primary" @click="goToManage">管理专题</el-button>
            </el-empty>
          </el-card>
        </template>

        <!-- 专题不存在 -->
        <el-card v-else shadow="never" class="not-found-card">
          <el-empty description="专题不存在或已被删除">
            <el-button type="primary" @click="goBack">返回</el-button>
          </el-empty>
        </el-card>
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ElMessage } from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import { useTopicStore } from '@/store/topic'
import { storeToRefs } from 'pinia'
import type { RoomInCategory } from '@/types/topic'
import { BASE_API_URL } from '@/constants/api'
import topicApi from '@/api/topic'
import { useAuthStore } from '@/store/auth'

// Store
const topicStore = useTopicStore()
const { currentTopic, categories, loading, error } = storeToRefs(topicStore)

// 响应式数据
const activeTab = ref('')
const topicId = ref('')
const defaultCover = '/public/logo.png'
const defaultBanner = '/public/logo.png'

// UUID 基本校验，避免向后端发送无效 ID 导致 422
const isValidUuid = (v?: string) => {
  const s = (v || '').toString().trim()
  return /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/.test(s)
}

// 计算属性
const getCategoryRooms = (categoryId: string): RoomInCategory[] => {
  const category = categories.value.find(cat => cat.id === categoryId)
  return category?.rooms || []
}

// 方法
const getBannerSrc = (url?: string | null) => {
  if (!url) return defaultBanner
  if (/^https?:\/\//.test(url)) return url
  const base = BASE_API_URL.replace(/\/+$/, '')
  const origin = base.replace(/\/api\/.*/, '')
  return origin + (url.startsWith('/') ? url : '/' + url)
}

const getCoverSrc = (url?: string | null) => {
  if (!url) return defaultCover
  if (/^https?:\/\//.test(url)) return url
  const base = BASE_API_URL.replace(/\/+$/, '')
  const origin = base.replace(/\/api\/.*/, '')
  return origin + (url.startsWith('/') ? url : '/' + url)
}

const handleBannerError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = defaultBanner
}

const goLive = (roomId: string) => {
  uni.navigateTo({ 
    url: `/pages/live/new/LiveView?room_id=${roomId}` 
  })
}

const goToManage = () => {
  if (topicId.value) {
    uni.navigateTo({
      url: `/pages/topic/TopicManage?topic_id=${topicId.value}`
    })
  }
}

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
    
    // 设置默认激活的标签页
    if (categories.value.length > 0) {
      activeTab.value = categories.value[0].id
    }
    console.info('[TopicDisplay] loadTopic success:', {
      topicId: topicId.value,
      hasTopic: !!currentTopic.value,
      categoriesCount: categories.value.length,
    })
  } catch (error: any) {
    console.error('[TopicDisplay] 加载专题失败:', { topicId: topicId.value, error })
    ElMessage.error(error.message || '加载专题失败')
  }
}

const statusText = (status?: string) => {
  const map: Record<string, string> = {
    'live': '直播中',
    'scheduled': '计划中',
    'ended': '已结束',
    'archived': '已归档'
  }
  return map[status || 'scheduled'] || '计划中'
}

const statusType = (status?: string) => {
  const map: Record<string, string> = {
    'live': 'success',
    'scheduled': 'primary',
    'ended': 'info',
    'archived': 'warning'
  }
  return map[status || 'scheduled'] || 'primary'
}

const formatTime = (timeStr?: string) => {
  if (!timeStr) return '未设置'
  
  // 预清理：移除微秒和时区，统一形态
  let s = String(timeStr).trim()
  s = s.replace(/\s+/g, 'T') // 空格转T
  s = s.replace(/\.(\d{1,6})/, '') // 去掉小数秒
  s = s.replace(/Z$/i, '') // 去掉Z
  if (s.includes('+')) s = s.split('+')[0] // 去掉+时区
  if (s.includes('-')) {
    // 有些浏览器更易解析 2025/08/02 形式
    s = s.replace('T', ' ')
  }

  const candidates = [
    s,
    s.replace(/-/g, '/'), // 兜底
  ]

  for (const v of candidates) {
    const d = new Date(v)
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hh = String(d.getHours()).padStart(2, '0')
      const mm = String(d.getMinutes()).padStart(2, '0')
      const ss = String(d.getSeconds()).padStart(2, '0')
      return `${y}-${m}-${day} ${hh}:${mm}:${ss}`
    }
  }
  // 解析失败则输出去噪后的日期部分
  const dateOnly = s.split('T')[0] || s.split(' ')[0] || s
  return dateOnly
}

// 页面加载
onLoad(async (options) => {
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated) {
    ElMessage.error('请先登录')
    uni.navigateTo({ url: '/pages/auth/callback' })
    return
  }

  const topicParam = (options?.topic_id || '').toString()
  const roomParam = (options?.room_id || '').toString()
  topicId.value = topicParam
  console.info('[TopicDisplay] onLoad topic_id =', topicId.value, 'room_id =', roomParam)

  if (!topicId.value) {
    // 尝试通过 room_id 获取唯一关联专题
    if (!roomParam) {
      ElMessage.error('缺少专题ID或房间ID')
      uni.navigateBack()
      return
    }
    try {
      const resp = await topicApi.getRoomTopics(roomParam)
      const list = resp?.data || []
      // 优先选择已发布；否则取第一个
      const published = list.find((t: any) => (t.topic_status || t.status) === 'published' || t.is_published)
      const tid = published?.topic_id || published?.id || list?.[0]?.topic_id || list?.[0]?.id
      if (tid && isValidUuid(tid)) {
        topicId.value = tid
      } else {
        throw new Error('未找到有效的专题ID')
      }
    } catch (e: any) {
      console.error('[TopicDisplay] 通过房间获取专题失败:', e)
      ElMessage.error(e?.message || '获取专题失败')
      uni.navigateBack()
      return
    }
  }

  // 非法 ID 直接提示并返回，避免触发后端 422
  if (!isValidUuid(topicId.value)) {
    console.error('[TopicDisplay] Invalid topic_id format:', topicId.value)
    ElMessage.error(`专题ID格式无效：${topicId.value}`)
    uni.navigateBack()
    return
  }

  await loadTopic()
})

// 组件挂载
onMounted(() => {
  // 可以在这里添加一些初始化逻辑
})
</script>

<style scoped>
/* 完全复用 VenueDisplayPage.vue 的样式 */
.venue-container {
  background: #f5f7fa;
  min-height: 100vh;
}
.venue-main {
  padding: 16px;
  display: flex;
  justify-content: center;
}
.venue-inner {
  width: 450px;      /* 收窄整体内容宽度 */
  margin: 0 auto;    /* 居中 */
}
.banner-card {
  margin-bottom: 12px;
}
.banner-content {
  width: 100%;
  height: 200px;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}
.banner-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.banner-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  color: white;
  padding: 20px;
  text-align: center;
}
.banner-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}
.banner-desc {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
.venue-tabs :deep(.el-tabs__header) {
  display: flex;
  justify-content: center;
}
.parent-card {
  border: 1px solid #eef1f6;
}
.parent-inner {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.parent-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.parent-desc {
  color: #606266;
}

.venue-card {
  cursor: pointer;
  padding: 10px;
}
.venue-card + .venue-card { margin-top: 8px; }
.venue-card-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}
.venue-card.dense { padding: 6px; }
.venue-cover {
  width: 200px;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  background: #fafafa;
}
.venue-cover.small { width: 140px; height: 84px; }
.img-error { 
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #bbb; font-size: 12px;
}
.venue-info {
  flex: 1;
  min-width: 0;
}
.venue-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.venue-title.one-line {
  -webkit-line-clamp: 1;
}
.venue-meta {
  margin-top: 6px;
  color: #909399;
  font-size: 13px;
}
.venue-meta.one-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.meta-item { margin-right: 6px; }
.meta-split { margin: 0 6px; color: #d0d3d6; }
.status-badge { position: absolute; left: 8px; top: 8px; }

/* 新增样式 */
.loading-card,
.error-card,
.empty-categories-card,
.not-found-card {
  margin-bottom: 12px;
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

@media (max-width: 767px) {
  .venue-card-inner { flex-direction: column; align-items: flex-start; }
  .venue-cover { width: 100%; height: 180px; }
  .status-badge { left: 12px; top: 12px; }
  
  .banner-title {
    font-size: 20px;
  }
  
  .banner-desc {
    font-size: 12px;
  }
}
</style>
