<template>
  <AdminLayout>
    <div class="topic-management-container">
      <!-- 顶部搜索筛选区域 -->
      <div class="search-section">
        <el-form :model="filterForm" inline class="search-form">
          <el-form-item label="页面标题">
            <el-input
              v-model="filterForm.title"
              placeholder="请输入标题"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="页面ID">
            <el-input
              v-model="filterForm.topic_id"
              placeholder="请输入页面ID"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="草稿" value="draft" />
              <el-option label="已发布" value="published" />
              <el-option label="已归档" value="archived" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="goToCreate">
              <el-icon><Plus /></el-icon>
              新建页面
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 数据表格区域 -->
      <div class="table-section">
        <div class="table-header">
          <h3 class="table-title">专题列表</h3>
          <el-button size="small" @click="refreshList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在加载专题列表...</span>
        </div>

        <!-- 专题表格 -->
        <el-table
          v-else
          :data="topics"
          v-loading="loading"
          class="topic-table"
          stripe
        >
          <el-table-column label="ID" prop="id" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="topic-id">{{ row.id.substring(0, 8) }}...</span>
            </template>
          </el-table-column>
          <el-table-column label="页面标题" prop="title" min-width="200" show-overflow-tooltip />
          <el-table-column label="封面" width="120">
            <template #default="{ row }">
              <el-image
                :src="getBannerSrc(row.banner_url)"
                fit="cover"
                class="banner-image"
                :preview-src-list="[getBannerSrc(row.banner_url)]"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </template>
          </el-table-column>
          <el-table-column label="包含子页面" width="120">
            <template #default="{ row }">
              <span class="stat-number">
                {{ getSubPagesCount(row) }}
                <el-tooltip content="包含的子页面数量" placement="top">
                  <el-icon class="question-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="总浏览量" width="120">
            <template #default="{ row }">
              <span class="stat-number">
                {{ getTotalViews(row) }}
                <el-tooltip content="专题总浏览量" placement="top">
                  <el-icon class="question-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div class="action-links">
                <div class="action-row">
                  <a href="javascript:void(0)" @click="handleAction('edit', row)" class="action-link">编辑</a>
                  <a href="javascript:void(0)" @click="handleAction('disable', row)" class="action-link">停用</a>
                  <a href="javascript:void(0)" @click="handleAction('share', row)" class="action-link">分享</a>
                </div>
                <div class="action-row">
                  <a href="javascript:void(0)" @click="handleAction('copy', row)" class="action-link">复制</a>
                  <a href="javascript:void(0)" @click="handleAction('tag', row)" class="action-link">打标签</a>
                  <a href="javascript:void(0)" @click="handleAction('data', row)" class="action-link">数据</a>
                </div>
                <div class="action-row">
                  <a href="javascript:void(0)" @click="handleAction('delete', row)" class="action-link delete-link">删除</a>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
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
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Refresh, 
  Loading, 
  Picture, 
  QuestionFilled
} from '@element-plus/icons-vue'
import { useTopicStore } from '@/store/topic'
import { storeToRefs } from 'pinia'
import AdminLayout from '@/layouts/AdminLayout.vue'
import type { Topic, TopicStatus, TopicListParams } from '@/types/topic'
import { BASE_API_URL } from '@/constants/api'

// Store
const topicStore = useTopicStore()
const { topics, loading, error } = storeToRefs(topicStore)

// 响应式数据
const filterForm = reactive({
  title: '',
  topic_id: '',
  status: '' as TopicStatus | ''
})

// 分页数据
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 计算属性 - 统计信息（暂时使用静态数据）
const getSubPagesCount = (topic: Topic) => {
  return topic.sub_pages_count || 0
}

const getTotalViews = (topic: Topic) => {
  return topic.total_views || 0
}

const getTotalVisitors = (topic: Topic) => {
  return topic.total_visitors || 0
}

// 方法
const goToCreate = () => {
  uni.navigateTo({
    url: '/pages/topic/TopicCreate'
  })
}

const handleViewTutorial = () => {
  ElMessage.info('查看教程功能待开发，敬请期待')
}

const handleSearch = () => {
  ElMessage.info('搜索功能待开发，敬请期待')
}

const getBannerSrc = (url?: string | null) => {
  if (!url) return '/public/logo.png'
  if (/^https?:\/\//.test(url)) return url
  const base = BASE_API_URL.replace(/\/+$/, '')
  const origin = base.replace(/\/api\/.*/, '')
  return origin + (url.startsWith('/') ? url : '/' + url)
}

const getStatusType = (status: TopicStatus) => {
  const statusMap: Record<TopicStatus, string> = {
    'draft': 'info',
    'published': 'success',
    'archived': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: TopicStatus) => {
  const statusMap: Record<TopicStatus, string> = {
    'draft': '草稿',
    'published': '已发布',
    'archived': '已归档'
  }
  return statusMap[status] || '未知'
}

// 规范化后端返回的时间字符串：
// 兼容类似 "2025-10-20T13:36:10.223019+00:00Z"（重复时区标记、微秒过长）
const normalizeDateString = (raw?: string): string | null => {
  if (!raw || typeof raw !== 'string') return null
  let s = raw.trim()
  // 如果同时包含时区偏移(+08:00/+00:00等)并以Z结尾，去掉尾部Z
  if (/\+\d{2}:?\d{2}$/i.test(s.replace(/Z$/i, '')) && /Z$/i.test(s)) {
    s = s.replace(/Z$/i, '')
  }
  // 微秒位数过长时，仅保留3位毫秒
  s = s.replace(/\.(\d{3})\d+(?=(?:[+\-]\d{2}:?\d{2}|Z|$))/i, '.$1')
  // Safari 等对时区中的冒号兼容性差，移除时区中的冒号：+08:00 -> +0800
  s = s.replace(/([+\-]\d{2}):(\d{2})(?=$|Z)/, '$1$2')
  return s
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '--'
  try {
    const normalized = normalizeDateString(dateStr)
    const date = normalized ? new Date(normalized) : new Date(dateStr)
    if (isNaN(date.getTime())) {
      console.warn('无效的日期格式:', dateStr)
      return '--'
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    console.warn('日期格式化失败:', dateStr, error)
    return '--'
  }
}

const handleAction = async (action: string, topic: Topic) => {
  try {
    switch (action) {
      case 'edit':
        // 跳转到编辑页面
        uni.navigateTo({
          url: `/pages/topic/TopicCreate?topic_id=${topic.id}`
        })
        break
      case 'delete':
        await ElMessageBox.confirm(
          '确定要删除这个专题吗？此操作不可恢复！',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await topicStore.deleteTopic(topic.id)
        ElMessage.success('删除成功')
        await loadTopics() // 重新加载列表
        break
      default:
        ElMessage.info(`${action}功能待开发，敬请期待`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadTopics()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadTopics()
}

const refreshList = () => {
  loadTopics()
}

const loadTopics = async () => {
  try {
    const params: TopicListParams = {
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filterForm.status || undefined
    }
    
    await topicStore.fetchTopics(params)
    
    // 调试信息：打印获取到的专题数据
    console.log('获取到的专题数据:', topics.value)
    if (topics.value && topics.value.length > 0) {
      console.log('第一个专题的数据结构:', topics.value[0])
      console.log('第一个专题的创建时间:', topics.value[0].created_at)
    }
    
    // 更新分页信息 - 根据后端API响应结构设置total
    // 注意：这里需要根据实际API响应来设置，暂时使用topics长度
    pagination.total = topics.value?.length || 0
  } catch (error: any) {
    console.error('加载专题列表失败:', error)
    ElMessage.error(error.message || '加载专题列表失败')
  }
}

// 页面加载
onLoad(() => {
  loadTopics()
})

// 组件挂载
onMounted(() => {
  // 可以在这里添加一些初始化逻辑
})
</script>

<style lang="scss" scoped>
.topic-management-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.search-section {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  
  .search-form {
    width: 100%;
    
    .el-form-item {
      margin-bottom: 0;
    }
  }
}

.table-section {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    background-color: #fafafa;
    
    .table-title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  
  .el-icon {
    font-size: 32px;
    color: #409eff;
    margin-bottom: 12px;
  }
}

.topic-table {
  width: 100%;
  
  .topic-id {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: #606266;
  }
  
  .banner-image {
    width: 60px;
    height: 40px;
    border-radius: 4px;
    
    .image-error {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      background-color: #f5f7fa;
      color: #c0c4cc;
    }
  }
  
  .stat-number {
    display: flex;
    align-items: center;
    gap: 4px;
    
    .question-icon {
      font-size: 12px;
      color: #c0c4cc;
      cursor: help;
    }
  }
  
  .action-links {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .action-row {
      display: flex;
      gap: 12px;
      flex-wrap: nowrap;
    }
    
    .action-link {
      color: #409eff;
      text-decoration: none;
      font-size: 12px;
      padding: 0;
      cursor: pointer;
      transition: color 0.2s;
      
      &:hover {
        color: #66b1ff;
        text-decoration: underline;
      }
      
      &.delete-link {
        color: #f56c6c;
        
        &:hover {
          color: #f78989;
        }
      }
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

// 响应式设计
@media (max-width: 768px) {
  .topic-management-container {
    padding: 12px;
  }
  
  .search-section {
    .search-form {
      .el-form-item {
        margin-bottom: 12px;
      }
    }
  }
  
  .table-section {
    .table-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }
  }
  
  .topic-table {
    .banner-image {
      width: 50px;
      height: 30px;
    }
    
    .action-links {
      .action-row {
        gap: 8px;
      }
      .action-link {
        font-size: 11px;
      }
    }
  }
}
</style>
