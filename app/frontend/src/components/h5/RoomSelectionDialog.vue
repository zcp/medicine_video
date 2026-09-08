<template>
  <el-dialog
    :model-value="props.visible"
    @update:modelValue="(val) => emit('update:visible', val)"
    title="选择直播间"
    width="90%"
    :before-close="handleClose"
    class="room-selection-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div class="search-section">
      <el-input v-model="searchKeyword" placeholder="搜索直播间标题" clearable @input="handleSearch" class="search-input">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="search-stats">共 {{ filteredRooms.length }} 个直播间，已选择 {{ selectedCount }} 个</div>
    </div>

    <el-table
      ref="tableRef"
      :data="paginatedRooms"
      height="400"
      class="room-table"
      :row-key="rowKeyFn"
      @selection-change="onSelectionChange"
    >
      <el-table-column type="selection" width="55" :reserve-selection="true" :selectable="() => true" />
      <el-table-column label="封面" width="120">
        <template #default="{ row }">
          <el-image :src="getCoverSrc(row.cover_url)" fit="cover" class="room-cover">
            <template #error>
              <div class="image-error"><el-icon><Picture /></el-icon><span>无图片</span></div>
            </template>
          </el-image>
        </template>
      </el-table-column>
      <el-table-column label="标题" prop="title" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.live_status)" size="small">{{ getStatusText(row.live_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="热度" width="80">
        <template #default="{ row }"><span class="heat-value">{{ row.heat || 0 }}</span></template>
      </el-table-column>
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <div class="pagination-section">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="filteredRooms.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :disabled="selectedCount === 0">确定选择 ({{ selectedCount }})</el-button>
      </div>
    </template>
  </el-dialog>
  
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Picture } from '@element-plus/icons-vue'
import { useRoomStore } from '@/store/room'
import { storeToRefs } from 'pinia'
import type { RoomInCategory, RoomSelectionItem } from '@/types/topic'
import { BASE_API_URL } from '@/constants/api'

// Props
interface Props {
  visible: boolean
  selectedRooms: RoomInCategory[]
  excludeRoomIds?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  excludeRoomIds: () => []
})

// Emits
interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'confirm', rooms: RoomInCategory[]): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const tableRef = ref<any>()
// 用 key 集合来保存所有页已选择项，避免分页切换丢失；key 始终为字符串
const selectedKeySet = ref<Set<string>>(new Set())

// Store
const roomStore = useRoomStore()
const { rooms } = storeToRefs(roomStore)

// 计算属性
// 归一化 rooms：补齐字段并构造稳定字符串 key
const normalizedRooms = computed(() => {
  return (rooms.value || []).map((r: any) => ({
    ...r,
    id: r.id,
    _key: String(r.id),
    live_status: r.live_status || r.status || 'scheduled',
    created_at: r.created_at || r.start_time || '',
    heat: r.heat || 0,
  }))
})

const filteredRooms = computed(() => {
  let list = normalizedRooms.value.filter((room: any) => !props.excludeRoomIds.includes(room.id))
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter((room: any) => String(room.title || '').toLowerCase().includes(kw))
  }
  return list
})

const paginatedRooms = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRooms.value.slice(start, end)
})

// 方法
const getCoverSrc = (url?: string | null) => {
  if (!url) return '/public/logo.png'
  if (/^https?:\/\//.test(url)) return url
  const base = BASE_API_URL.replace(/\/+$/, '')
  const origin = base.replace(/\/api\/.*/, '')
  return origin + (url.startsWith('/') ? url : '/' + url)
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'live': 'success',
    'scheduled': 'primary',
    'ended': 'info',
    'archived': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'live': '直播中',
    'scheduled': '计划中',
    'ended': '已结束',
    'archived': '已归档'
  }
  return statusMap[status] || '未知'
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleSearch = () => {
  currentPage.value = 1
}

function rowKeyFn(row: any) { return String(row._key) }

function onSelectionChange(selection: any[]) {
  const pageKeys = new Set(paginatedRooms.value.map((r: any) => String(r._key)))
  // 先把当前页相关的 key 从全局集合移除
  pageKeys.forEach(k => selectedKeySet.value.delete(k))
  // 再把当前选择加入
  selection.forEach((r: any) => selectedKeySet.value.add(String(r._key)))
}

function syncTableSelection() {
  nextTick(() => {
    if (!tableRef.value) return
    tableRef.value.clearSelection()
    paginatedRooms.value.forEach((row: any) => {
      const checked = selectedKeySet.value.has(String(row._key))
      if (checked) tableRef.value.toggleRowSelection(row, true)
    })
  })
}

const clearSelection = () => {
  selectedKeySet.value = new Set()
  syncTableSelection()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  syncTableSelection()
}

const handleClose = () => {
  emit('update:visible', false)
}

const selectedCount = computed(() => selectedKeySet.value.size)

const handleConfirm = () => {
  if (selectedKeySet.value.size === 0) {
    ElMessage.warning('请至少选择一个直播间')
    return
  }

  const selected = normalizedRooms.value
    .filter((r: any) => selectedKeySet.value.has(String(r._key)))
    .map((room: any) => ({
      id: room.id,
      title: room.title,
      cover_url: room.cover_url,
      live_status: room.live_status,
      start_time: room.created_at,
      heat: room.heat,
      sort_order: 0,
    }))

  emit('confirm', selected)
  handleClose()
}

// 监听 visible 变化，初始化数据
watch(() => props.visible, async (newVisible) => {
  if (newVisible) {
    // 初始化选中集合
    selectedKeySet.value = new Set((props.selectedRooms || []).map(r => String((r as any).id)))
    searchKeyword.value = ''
    currentPage.value = 1
    
    // 每次打开都强制刷新第一页，避免历史状态或分页导致为空
    try {
      await roomStore.fetchRooms({ refresh: true, page: 1 })
    } catch (e: any) {
      ElMessage.error(e?.message || '加载直播间失败')
    }
    
    // 恢复表格选中
    syncTableSelection()
  }
})

// 监听 selectedRooms 变化，更新表格选中状态
watch([currentPage, pageSize], () => {
  syncTableSelection()
})
</script>

<style lang="scss" scoped>
.room-selection-dialog {
  .search-section {
    margin-bottom: 16px;
    
    .search-input {
      margin-bottom: 8px;
    }
    
    .search-stats {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .room-table {
    margin-bottom: 16px;
    
    .room-cover {
      width: 80px;
      height: 60px;
      border-radius: 4px;
      
      .image-error {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        background-color: #f5f7fa;
        color: #c0c4cc;
        font-size: 12px;
        
        .el-icon {
          font-size: 16px;
          margin-bottom: 4px;
        }
      }
    }
    
    .heat-value {
      color: #f56c6c;
      font-weight: 500;
    }
  }
  
  .pagination-section {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
  }
  
  .selected-preview {
    background-color: #f5f7fa;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 16px;
    
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 14px;
      font-weight: 500;
      color: #303133;
    }
    
    .preview-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .room-tag {
        max-width: 200px;
        
        &.more-tag {
          background-color: #e4e7ed;
          color: #606266;
        }
      }
    }
  }
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .room-selection-dialog {
    .room-table {
      .room-cover {
        width: 60px;
        height: 45px;
      }
    }
    
    .selected-preview {
      .preview-list {
        .room-tag {
          max-width: 150px;
          font-size: 12px;
        }
      }
    }
  }
}
</style>
