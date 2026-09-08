<template>
  <RoomManageLayout>
    <template #top-left>
      <div class="top-left-wrap">
        <div class="top-left-row">
          <span class="top-left-title">{{ parentRoomDetail?.title || '加载中…' }}</span>
        </div>
        <div class="top-left-row time">
          <el-tag class="top-left-status" :type="getStatusType(parentRoomDetail?.status)">
            {{ getStatusText(parentRoomDetail?.status) }}
          </el-tag>
          <span class="top-left-time">开始时间 {{ formatDateTime(parentRoomDetail?.start_time) }}</span>
        </div>
      </div>
    </template>
    <div class="multi-venue-manage-content">
      <el-space direction="vertical" size="large" style="width: 100%">
        
        <!-- 页面头部设置区 -->
        <el-card class="settings-card">
          <div class="card-header">
            <span class="card-title">多会场直播</span>
            <el-switch
              v-model="multiVenueEnabled"
              active-text="开启"
              inactive-text="关闭"
              style="margin-left: 20px;"
              @change="handleMultiVenueToggle"
            />
            <span class="example-text">示例</span>
            <el-button type="text" class="guide-button" @click="showComingSoon('使用指南')">使用指南</el-button>
          </div>
          <div class="card-body">
            <p class="description-text">关闭后,则播放页不显示会场信息,全部会场推流地址失效</p>
            <el-form label-width="100px" class="settings-form">
              <el-form-item label="菜单名称">
                <el-input 
                  v-model="menuName" 
                  placeholder="其他会场" 
                  maxlength="20" 
                  show-word-limit 
                  style="width: 240px;" 
                  @input="handleMenuNameChange"
                />
                <el-switch 
                  v-model="showMenuInfo" 
                  style="margin-left: 20px;" 
                  @change="handleMenuInfoToggle"
                />
              </el-form-item>
              <el-form-item label="主会场名称">
                <el-input 
                  v-model="mainVenueName" 
                  placeholder="主会场" 
                  maxlength="20" 
                  show-word-limit 
                  style="width: 240px;" 
                  disabled
                />
                <el-button type="primary" link style="margin-left: 20px;" @click="showComingSoon('修改主会场名称')">更改</el-button>
              </el-form-item>
              <el-form-item label="显示位置">
                <el-radio-group v-model="displayPosition" @change="handleDisplayPositionChange">
                  <el-radio label="below_video">视频下方示例</el-radio>
                  <el-radio label="right_of_video">视频右侧示例</el-radio>
                </el-radio-group>
                <p class="form-item-note">注:主会场不推流,分会场推流时,不统计用户直播停留时长;只有主会场推流时,才统计用户直播停留时长。</p>
              </el-form-item>
            </el-form>
          </div>
        </el-card>

        <!-- 列表操作栏 -->
        <el-card class="list-operations-card">
          <el-row justify="space-between" align="middle">
            <el-col :span="6">
              <el-button type="primary" @click="handleAddSubVenue">添加分会场</el-button>
            </el-col>
            <el-col :span="18" style="text-align: right;">
              <el-select 
                v-model="filterStatus" 
                placeholder="全部" 
                style="width: 120px; margin-right: 10px;" 
                @change="handleFilterChange"
              >
                <el-option label="全部" value="all"></el-option>
                <el-option label="未开始" value="scheduled"></el-option>
                <el-option label="直播中" value="live"></el-option>
                <el-option label="已结束" value="ended"></el-option>
              </el-select>
              <el-input
                v-model="searchKeyword"
                placeholder="请输入会场名称"
                style="width: 200px;"
                @input="handleSearchInput"
              >
                <template #append>
                  <el-button :icon="Search" @click="handleSearch" />
                </template>
              </el-input>
            </el-col>
          </el-row>
        </el-card>

        <!-- 分会场数据列表区 -->
        <el-card class="sub-venue-list-card">
          <el-table :data="subRooms" v-loading="loading" style="width: 100%">
            <el-table-column label="会场封面" width="120">
              <template #default="{ row }">
                <el-image
                  style="width: 80px; height: 45px; border-radius: 4px;"
                  :src="tempCoverUrls[row.id] || row.cover_url || '/logo.png'"
                  fit="cover"
                />
              </template>
            </el-table-column>
            <el-table-column prop="title" label="会场名称" width="180" />
            <el-table-column prop="id" label="会场ID" width="200" />
            <el-table-column label="直播时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(roomSessions[row.id]?.start_time) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getSessionStatusType(roomSessions[row.id]?.status)">
                  {{ getSessionStatusText(roomSessions[row.id]?.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="排序" width="80">
              <template #default="{ row, $index }">
                {{ $index + 1 }}
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="180">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="showComingSoon('下载回放视频')">下载回放视频</el-button>
                <el-button link type="primary" size="small" @click="handleEditSubVenue(row.id)">编辑</el-button>
                <el-button link type="primary" size="small" @click="showComingSoon('更多操作')">更多</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="subRooms.length === 0 && !loading" class="no-data-message">暂无数据</div>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :small="false"
              :disabled="loading"
              :background="true"
              layout="total, sizes, prev, pager, next, jumper"
              :total="pagination.total"
              @size-change="handlePageSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>

        <!-- 添加分会场弹窗 -->
        <el-dialog
          v-model="dialogVisible"
          title="添加多会场"
          width="600px"
          :before-close="handleDialogClose"
          destroy-on-close
        >
          <el-form
            :model="formModel"
            :rules="formRules"
            ref="subVenueFormRef"
            label-width="100px"
            v-loading="isSubmitting"
          >
            <el-form-item label="分会场名称" prop="title">
              <el-input 
                v-model="formModel.title" 
                maxlength="50" 
                show-word-limit 
                placeholder="请输入分会场名称" 
              />
            </el-form-item>
            <el-form-item label="分会场封面" prop="cover_url">
              <el-upload
                class="avatar-uploader"
                action="#"
                :show-file-list="false"
                :before-upload="handleCoverUploadClick"
                drag
              >
                <template v-if="formModel.cover_url">
                  <el-image
                    :src="formModel.cover_url"
                    fit="cover"
                    style="width: 100%; height: 100%; border-radius: 4px;"
                  />
                </template>
                <template v-else>
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">
                    拖拽文件到此处或 <em>点击上传</em>
                  </div>
                </template>
                <template #tip>
                  <div class="el-upload__tip">
                    推荐图片尺寸为: 1000*562, 不超过10M <br />
                    支持png、jpg、gif格式
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            <el-form-item label="直播时间" prop="start_time">
              <el-date-picker
                v-model="formModel.start_time"
                type="datetime"
                placeholder="选择日期时间"
                value-format="YYYY-MM-DDTHH:mm:ssZ"
                :prefix-icon="Clock"
                style="width: 100%;"
              />
            </el-form-item>
            <el-form-item label="回放设置">
              <el-radio-group v-model="formModel.playback_type" @change="handlePlaybackSettingChange">
                <el-radio :label="0">结束后回放</el-radio>
                <el-radio :label="1">实时回放</el-radio>
                <el-radio :label="2">结束后不回放</el-radio>
              </el-radio-group>
              <p class="form-item-note">结束会场直播后才生成回放视频,分会场同步话题设置的跑马灯信息</p>
            </el-form-item>
            <el-form-item label="回放有效期">
              <el-switch v-model="formModel.playback_enabled" @change="handlePlaybackEnabledChange" />
            </el-form-item>
          </el-form>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="handleDialogClose">取消</el-button>
              <el-button type="primary" @click="handleSubmit" :loading="isSubmitting">
                确定
              </el-button>
            </span>
          </template>
        </el-dialog>
      </el-space>
    </div>
  </RoomManageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  UploadFilled,
  Clock
} from '@element-plus/icons-vue'
import RoomManageLayout from '@/layouts/RoomManageLayout.vue'
import { useRoomStore } from '@/store/room'
import { useSessionStore } from '@/store/session'
import { getRoomDetail, getRoomList, createRoom, getSubVenues } from '@/api/room'
import { getSessionList, createSession } from '@/api/session'
import { getToken } from '@/store/auth'
import { BASE_API_URL } from '@/constants/api'
import type { Room, RoomCreatePayload } from '@/types/room'
import type { Session, SessionCreatePayload } from '@/types/session'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const roomStore = useRoomStore()
const sessionStore = useSessionStore()

const roomId = ref<string | null>(null)
const parentRoomDetail = ref<Room | null>(null)
const subRooms = ref<Room[]>([])
const roomSessions = ref<Record<string, Session | null>>({})
const loading = ref(false)
const dialogVisible = ref(false)
const isSubmitting = ref(false)

// 头部设置区数据
const multiVenueEnabled = ref(false)
const menuName = ref('其他会场')
const showMenuInfo = ref(true)
const mainVenueName = ref('主会场')
const displayPosition = ref('below_video')

// 搜索和筛选数据
const filterStatus = ref('all')
const searchKeyword = ref('')

// 表单数据模型
const formModel = ref<RoomCreatePayload & { start_time: string | null; playback_type: number; playback_enabled: boolean }>({
  title: '',
  description: '',
  cover_url: '',
  is_private: false,
  parent_room_id: '',
  start_time: null,
  playback_type: 0,
  playback_enabled: false,
})

// 表单验证规则
const formRules = ref({
  title: [
    { required: true, message: '请输入分会场名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' },
  ],
  start_time: [
    { required: true, message: '请选择直播时间', trigger: 'change' },
  ],
})

const pagination = ref({
  page: 1,
  size: 10,
  total: 0,
})

// 本地分页状态，用于控制分页器显示
const currentPage = ref(1)
const pageSize = ref(10)

// 本地选择的封面临时路径（用于提交后上传）
const selectedCoverTempPath = ref<string>('')
// 分会场ID -> 临时封面地址 的映射，用于在上传成功前先展示
const tempCoverUrls = ref<Record<string, string>>({})

// 获取房间ID
const getRoomId = (): string | null => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  return currentPage.options?.room_id || null
}

onMounted(() => {
  roomId.value = getRoomId()
  if (roomId.value) {
    loadParentRoomDetail()
    loadSubRooms()
  } else {
    ElMessage.error('缺少房间ID，无法管理多会场')
    router.back()
  }
})

// 移除 watch，改为在 loadSubRooms 中直接调用

// 获取主会场详情
const loadParentRoomDetail = async () => {
  if (!roomId.value) return
  loading.value = true
  try {
    const response = await getRoomDetail(roomId.value)
    if (response && response.code === 200) {
      parentRoomDetail.value = response.data
      formModel.value.parent_room_id = roomId.value
      mainVenueName.value = response.data?.title || '主会场'
    } else {
      ElMessage.error(response?.message || '获取主会场详情失败')
    }
  } catch (error: any) {
    ElMessage.error('获取主会场详情异常: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 获取分会场列表
const loadSubRooms = async () => {
  if (!roomId.value) return
  loading.value = true
  try {
    console.log('加载分会场列表，参数：', {
      roomId: roomId.value,
      page: pagination.value.page,
      size: pagination.value.size,
    })
    
    const response = await getSubVenues(roomId.value, {
      page: pagination.value.page,
      size: pagination.value.size,
    })
    
    console.log('分会场列表响应：', response)
    
    if (response && response.code === 200 && response.data) {
      // 根据API文档，数据结构是 response.data.items
      const roomsList = response.data.items || []
      subRooms.value = roomsList
      pagination.value.total = response.data.total || 0
      // 将后端返回的真实封面地址同步到临时映射，保证刷新后也能展示
      roomsList.forEach((r: any) => {
        if (r && r.id && r.cover_url) {
          tempCoverUrls.value[r.id] = r.cover_url
        }
      })
      console.log('分会场列表更新：', subRooms.value)
      console.log('原始响应数据结构：', response.data)
      
      // 如果有分会场，先补全封面，再获取场次信息
      if (subRooms.value.length > 0) {
        fetchCoverUrlsForRooms(subRooms.value)
        fetchLatestSessions(subRooms.value)
      }
    } else {
      ElMessage.error(response?.message || '获取分会场列表失败')
    }
  } catch (error: any) {
    console.error('获取分会场列表异常：', error)
    ElMessage.error('获取分会场列表异常: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 获取分会场的最新场次信息
const fetchLatestSessions = async (rooms: Room[]) => {
  const newRoomSessions: Record<string, Session | null> = {}
  for (const room of rooms) {
    try {
      const response = await getSessionList(room.id, { page: 1, size: 1 })
      console.log(`获取房间 ${room.id} 的场次响应：`, response)
      
      if (response && response.code === 200 && response.data) {
        // 检查数据结构，可能是 response.data.items 而不是 response.data.list
        const sessionsList = response.data.items || response.data.list || []
        console.log(`房间 ${room.id} 的场次列表：`, sessionsList)
        
        if (sessionsList.length > 0) {
          // 按开始时间排序，获取最新的场次
          const sortedSessions = sessionsList.sort((a, b) => {
            const timeA = new Date(a.start_time).getTime()
            const timeB = new Date(b.start_time).getTime()
            return timeB - timeA // 降序，最新的在前
          })
          const latestSession = sortedSessions[0]
          console.log(`房间 ${room.id} 的最新场次：`, latestSession)
          newRoomSessions[room.id] = latestSession
        } else {
          console.log(`房间 ${room.id} 没有场次数据`)
          newRoomSessions[room.id] = null
        }
      } else {
        console.log(`房间 ${room.id} 场次请求失败：`, response)
        newRoomSessions[room.id] = null
      }
    } catch (error) {
      console.error(`获取房间 ${room.id} 的场次信息失败:`, error)
      newRoomSessions[room.id] = null
    }
  }
  roomSessions.value = newRoomSessions
}

// 使用房间详情API补全封面地址
const fetchCoverUrlsForRooms = async (rooms: Room[]) => {
  // 并发请求详情以提升速度
  const tasks = rooms.map((room) => getRoomDetail(room.id).then((res: any) => ({ id: room.id, res })).catch(() => ({ id: room.id, res: null })))
  const results = await Promise.all(tasks)
  results.forEach(({ id, res }) => {
    if (res && (res as any).cover_url) {
      // 兼容 utils/request 直接返回数据对象的场景
      tempCoverUrls.value[id] = (res as any).cover_url
    } else if (res && (res as any).data?.cover_url) {
      // 兼容后端统一响应 { code, data } 的场景
      tempCoverUrls.value[id] = (res as any).data.cover_url
    }
  })
}

// 格式化日期时间
const formatDateTime = (dateTime: string | null | undefined) => {
  if (!dateTime) return 'N/A'
  try {
    let cleanTime = dateTime
    cleanTime = cleanTime.replace(/\.\d{6}/, '')
    cleanTime = cleanTime.replace(/\+00:00Z$/, 'Z')
    const date = dayjs(cleanTime)
    if (date.isValid()) {
      return date.format('YYYY-MM-DD HH:mm:ss')
    } else {
      console.warn('Invalid date format after cleaning:', cleanTime)
      return 'Invalid Date'
    }
  } catch (error) {
    console.error('Date formatting error:', error, 'for time:', dateTime)
    return 'Invalid Date'
  }
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

// 获取场次状态类型
const getSessionStatusType = (status: string | undefined) => {
  switch (status) {
    case 'scheduled':
      return 'info'
    case 'live':
      return 'success'
    case 'ended':
      return 'warning'
    case 'archived':
      return 'info'
    default:
      return 'info'
  }
}

// 获取场次状态文本
const getSessionStatusText = (status: string | undefined) => {
  switch (status) {
    case 'scheduled':
      return '未开始'
    case 'live':
      return '直播中'
    case 'ended':
      return '已结束'
    case 'archived':
      return '已归档'
    default:
      return '无场次'
  }
}

// 处理分页变化
const handlePageChange = (newPage: number) => {
  currentPage.value = newPage
  pagination.value.page = newPage
  loadSubRooms()
}

// 处理每页条数变化
const handlePageSizeChange = (newSize: number) => {
  pageSize.value = newSize
  pagination.value.size = newSize
  currentPage.value = 1
  pagination.value.page = 1
  loadSubRooms()
}

// 头部设置区事件处理
const handleMultiVenueToggle = () => {
  showComingSoon('多会场直播总开关')
}

const handleMenuNameChange = () => {
  showComingSoon('菜单名称修改')
}

const handleMenuInfoToggle = () => {
  showComingSoon('菜单信息显示开关')
}

const handleDisplayPositionChange = () => {
  showComingSoon('显示位置设置')
}

// 搜索和筛选事件处理
const handleFilterChange = () => {
  showComingSoon('状态筛选')
}

const handleSearchInput = () => {
  // 实时搜索可以在这里实现
}

const handleSearch = () => {
  showComingSoon('会场名称搜索')
}

// 打开添加分会场弹窗
const handleAddSubVenue = () => {
  dialogVisible.value = true
  formModel.value = {
    title: '',
    description: '',
    cover_url: '',
    is_private: false,
    parent_room_id: roomId.value || '',
    start_time: null,
    playback_type: 0,
    playback_enabled: false,
  }
}

// 关闭弹窗并重置表单
const handleDialogClose = () => {
  dialogVisible.value = false
  // 手动重置表单数据
  formModel.value = {
    title: '',
    description: '',
    cover_url: '',
    is_private: false,
    parent_room_id: roomId.value || '',
    start_time: null,
    playback_type: 0,
    playback_enabled: false,
  }
}

// 提交分会场创建表单
const handleSubmit = async () => {
  // 手动验证必填字段
  if (!formModel.value.title || formModel.value.title.trim() === '') {
    ElMessage.error('请输入分会场名称')
    return
  }
  
  if (!formModel.value.start_time) {
    ElMessage.error('请选择直播时间')
    return
  }

  if (formModel.value.title.length > 50) {
    ElMessage.error('分会场名称不能超过50个字符')
    return
  }

  isSubmitting.value = true
  try {
    ElMessage.info('正在创建分会场...')

    // 1. 创建房间 (分会场)
    const roomPayload: RoomCreatePayload = {
      title: formModel.value.title.trim(),
      description: formModel.value.description.trim() || '分会场',
      is_private: formModel.value.is_private,
      parent_room_id: formModel.value.parent_room_id,
    }
        console.log('创建分会场请求参数：', roomPayload)
        const roomResult = await createRoom(roomPayload)
        console.log('创建分会场响应：', roomResult)

        if (roomResult.code !== 200 || !roomResult.data?.id) {
          throw new Error(roomResult.message || '创建分会场失败')
        }
        const newRoomId = roomResult.data.id
        console.log('新创建的分会场ID：', newRoomId)

    // 2. 创建场次
    if (formModel.value.start_time) {
      ElMessage.info('正在设置直播时间...')
      const sessionPayload: SessionCreatePayload = {
        start_time: formModel.value.start_time,
      }
      const sessionResult = await createSession(newRoomId, sessionPayload)
      if (sessionResult.code !== 200) {
        ElMessage.warning('分会场创建成功，但设置直播时间失败，请稍后手动设置')
      }
    }

    // 3. 如果用户选择了本地封面，创建后上传到后端
    if (selectedCoverTempPath.value) {
      try {
        await uploadCoverToServer(newRoomId, selectedCoverTempPath.value)
        ElMessage.success('封面已上传')
      } catch (e: any) {
        ElMessage.warning(e?.message || '封面上传失败，可稍后在管理页重试')
      }
    }

    ElMessage.success('分会场创建成功')
    handleDialogClose()
    // 重置分页到第一页并刷新列表
    currentPage.value = 1
    pagination.value.page = 1
    // 立即在列表中用本地临时图占位显示
    if (selectedCoverTempPath.value) {
      tempCoverUrls.value[newRoomId] = selectedCoverTempPath.value
    }
    await loadSubRooms()
  } catch (error: any) {
    ElMessage.error(error.message || '创建失败，请重试')
  } finally {
    isSubmitting.value = false
  }
}

// 静态功能提示
const showComingSoon = (featureName: string) => {
  ElMessage.info(`${featureName}功能待开发，敬请期待`)
}

// 封面上传占位提示
const handleCoverUploadClick = () => {
  uni.chooseImage({
    count: 1,
    success: (chooseRes) => {
      const filePath = (chooseRes as any).tempFilePaths?.[0]
      if (!filePath) return
      // 预览：直接使用本地临时路径
      formModel.value.cover_url = filePath
      selectedCoverTempPath.value = filePath
    },
    fail: () => {
      ElMessage.error('选择图片失败')
    },
  })
  return false
}

// 回放设置占位提示
const handlePlaybackSettingChange = () => {
  showComingSoon('回放设置')
}

// 回放有效期占位提示
const handlePlaybackEnabledChange = () => {
  showComingSoon('回放有效期')
}

// 编辑分会场
const handleEditSubVenue = (subRoomId: string) => {
  router.push(`/pages/room/new/RoomCreate?room_id=${subRoomId}&mode=edit`)
}

// 上传封面到服务器
const uploadCoverToServer = (roomId: string, filePath: string) => {
  return new Promise<void>((resolve, reject) => {
    const token = getToken()
    const uploadUrl = `${BASE_API_URL.replace(/\/+$/, '')}/rooms/${roomId}/cover`
    uni.uploadFile({
      url: uploadUrl,
      filePath,
      name: 'file',
      header: {
        Authorization: `Bearer ${token || ''}`,
      },
      success: (res) => {
        try {
          const body = JSON.parse((res as any).data || '{}')
          if ((res as any).statusCode >= 200 && (res as any).statusCode < 300 && (body?.code === 0 || body?.code === 200)) {
            formModel.value.cover_url = body?.data?.cover_url || formModel.value.cover_url
            // 覆盖临时映射为正式URL
            if (body?.data?.cover_url) {
              tempCoverUrls.value[roomId] = body.data.cover_url
            }
            return resolve()
          }
          reject(new Error(body?.message || `上传失败(${(res as any).statusCode})`))
        } catch (e) {
          reject(new Error('响应解析失败'))
        }
      },
      fail: (err) => reject(err as any),
    })
  })
}
</script>

<style scoped>
.multi-venue-manage-content {
  padding: 12px 12px 10px;
  width: 100%;
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

.settings-card, .list-operations-card, .sub-venue-list-card {
  margin-bottom: 12px;
  border-radius: 8px;
  width: 95%;
  max-width: none;
}

.settings-card .card-header {
  display: flex;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 16px;
}

.settings-card .card-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.settings-card .example-text {
  margin-left: 10px;
  color: #909399;
  font-size: 14px;
}

.settings-card .guide-button {
  margin-left: auto;
}

.settings-card .description-text {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.settings-form .el-form-item {
  margin-bottom: 16px;
}

.settings-form .form-item-note {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 5px;
  display: block;
  width: 100%;
  clear: both;
}

.list-operations-card {
  padding: 16px;
}

.sub-venue-list-card {
  padding: 16px;
}

.no-data-message {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 16px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* Dialog specific styles */
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
  width: 100%;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader .el-icon--upload {
  font-size: 28px;
  color: #8c939d;
  text-align: center;
}

.el-upload__text {
  color: #8c939d;
  font-size: 14px;
  margin-top: 8px;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 5px;
}

.dialog-footer {
  text-align: right;
}

/* 确保卡片适应全宽 */
.multi-venue-manage-content :deep(.el-card) {
  width: 95%;
  max-width: none;
  box-sizing: border-box;
}

.multi-venue-manage-content :deep(.el-space) {
  width: 95%;
}

.multi-venue-manage-content :deep(.el-space__item) {
  width: 95%;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .multi-venue-manage-content {
    padding: 16px;
  }
}
</style>
