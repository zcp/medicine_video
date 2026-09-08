<template>
  <el-container class="venue-container">
    <el-main class="venue-main">
      <div class="venue-inner">
      <!-- 顶部主视觉 Banner（静态占位） -->
      <el-card shadow="never" class="banner-card">
        <div class="banner-content">
          <img class="banner-img" :src="bannerSrc" alt="banner" />
        </div>
      </el-card>

      <!-- 分类标签（静态占位） -->
      <el-tabs v-model="activeTab" class="venue-tabs">
        <el-tab-pane label="云南省" name="yunnan">
          <!-- 重要：主会场与分会场都展示在“云南省”页签 -->
          <el-space direction="vertical" :size="12" style="width:100%">
            <!-- 分会场卡片列表（栅格布局：桌面两列，移动端一列） -->
            <template v-if="subVenueCards.length > 0">
              <el-row :gutter="10">
                <el-col v-for="room in subVenueCards" :key="room.id" :xs="24" :sm="24" :md="24" :lg="24">
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
                          <span>开始时间：{{ formatTime(room._latestStartTime) }}</span>
                          <span class="meta-split">·</span>
                          <p>热度：100</p>
                        </div>
                      </div>
                      <el-tag class="status-badge" size="small" :type="statusType(room._latestStatus)">{{ statusText(room._latestStatus) }}</el-tag>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </template>
            <el-empty v-else description="暂无分会场"></el-empty>
          </el-space>
        </el-tab-pane>
        <el-tab-pane label="湖南省" name="hunan">
          <div class="placeholder-pane"></div>
        </el-tab-pane>
      </el-tabs>
      </div>
    </el-main>
  </el-container>
  
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useRoomStore } from '@/store/room';
import { BASE_API_URL } from '@/constants/api';

const roomStore = useRoomStore();
const { rooms, currentRoom } = storeToRefs(roomStore);

const activeTab = ref('yunnan');
const bannerSrc = '/public/logo.png';
const defaultCover = '/public/logo.png';

const parentRoomId = ref<string>('');

onLoad(async (options) => {
  parentRoomId.value = (options?.venue_id || options?.id || '').toString();
  await roomStore.fetchRooms({ refresh: true });
  if (parentRoomId.value) {
    await roomStore.fetchRoomById(parentRoomId.value);
  }
});

const parentRoom = computed(() => currentRoom.value);

// 选择分会场：过滤 parent_room_id === venue_id
const subVenues = computed(() => {
  if (!parentRoomId.value) return [] as any[];
  return (rooms.value || []).filter((r: any) => r.parent_room_id === parentRoomId.value);
});

// 对每个分会场补充最近场次状态/时间（如果后端未合并，可在此处做二次扩展；当前先占位字段）
const subVenueCards = computed(() => {
  return subVenues.value.map((r: any) => ({
    ...r,
    _latestStatus: r.status || 'scheduled',
    _latestStartTime: r.start_time || r.created_at,
  }));
});

const getCoverSrc = (url?: string) => {
  if (!url) return defaultCover;
  if (/^https?:\/\//.test(url)) return url;
  const base = BASE_API_URL.replace(/\/+$/, '');
  const origin = base.replace(/\/api\/.*/, '');
  return origin + (url.startsWith('/') ? url : '/' + url);
}

const goLive = (roomId: string) => {
  // 跳转到房间管理页，携带 room_id 参数
  uni.navigateTo({ url: `/pages/room/new/RoomManage?room_id=${roomId}` });
};

const statusText = (s?: string) => {
  const map: Record<string, string> = {
    live: '直播中',
    scheduled: '未开始',
    ended: '已结束',
    archived: '回放中',
  };
  return map[s || 'scheduled'] || '未开始';
};

const statusType = (s?: string) => {
  const map: Record<string, string> = {
    live: 'success',
    scheduled: 'info',
    ended: 'warning',
    archived: 'primary',
  };
  return map[s || 'scheduled'] || 'info';
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return '';
  let s = String(timeStr).trim();
  s = s.replace(/\s+/g, 'T');
  s = s.replace(/\.(\d{1,6})/, '');
  s = s.replace(/Z$/i, '');
  if (s.includes('+')) s = s.split('+')[0];
  s = s.replace('T', ' ');
  const candidates = [s, s.replace(/-/g, '/')];
  for (const v of candidates) {
    const d = new Date(v);
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const ss = String(d.getSeconds()).padStart(2, '0');
      return `${y}-${m}-${day} ${hh}:${mm}:${ss}`;
    }
  }
  return s.split(' ')[0] || s;
};
</script>

<style scoped>
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
}
.banner-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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

@media (max-width: 767px) {
  .venue-card-inner { flex-direction: column; align-items: flex-start; }
  .venue-cover { width: 100%; height: 180px; }
  .status-badge { left: 12px; top: 12px; }
}
</style>



