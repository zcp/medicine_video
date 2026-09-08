<template>
  <view class="chat-tab">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="messages.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无聊天消息</text>
      <text class="empty-hint">快来发送第一条消息吧！</text>
    </view>
    
    <!-- 消息列表（v2.0 微信式：后端契约=DESC 窗口+页内 ASC，列表直渲=最早在上、最新在底）：
         进入/发送/回底 经 scroll-into-view 锚定末条（=最新，底部）；
         上滑触顶加载更早历史（scrolltoupper → page++ 更早窗口插头部）；更早尽头继续上滑 → 弹「没有更多消息了」轻提示；
         @scroll 同步近底状态（近底跟随 / 阅读态暂停替换判定）；触底（scrolltolower）触发回底补拉；
         触摸中不替换列表防手势竞态 -->
    <scroll-view 
      v-else
      scroll-y 
      :scroll-into-view="scrollIntoViewId"
      class="message-list"
      @scrolltoupper="handleReachTop"
      @scroll="handleScroll"
      @scrolltolower="handleScrollToLower"
      @touchstart="isTouching = true"
      @touchend="isTouching = false"
      @touchmove.stop.prevent
    >
      <!-- 顶部：向上翻更早历史时的就地加载反馈（更早方向=列表头部） -->
      <view v-if="isLoadingMore" class="loading-more">
        <text>加载中...</text>
      </view>

      <!-- 消息列表：微信式气泡。他人=头像左+气泡左；自己=头像右+气泡右（row-reverse）。
           昵称/时间位于气泡外上方，气泡仅包裹文字内容、宽度随内容自适应（上限由 .message-body max-width 约束） -->
      <view 
        v-for="msg in messages" 
        :key="msg.id"
        :id="`msg-${msg.id}`"
        class="message-item"
        :class="{ self: isSelf(msg) }"
        @longpress="canDelete(msg) && handleDeleteMessage(msg)"
      >
        <image 
          :src="msg.user?.avatar_url ? resolveMediaUrl(msg.user.avatar_url) : '/static/default-avatar.png'" 
          @error="handleAvatarError"
          lazy-load
          class="user-avatar"
        />
        <view class="message-body">
          <view class="message-meta">
            <text v-if="!isSelf(msg)" class="user-name">{{ msg.user_display_name || msg.user?.nickname || '匿名用户' }}</text>
            <text class="message-time">{{ formatTime(msg.created_at) }}</text>
          </view>
          <view class="message-bubble">
            <text class="message-text">{{ sanitizeContent(msg.content) }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- C1/C2（v2.0）：阅读态（滚离底部）存在未读新留言时的回底浮条（贴输入条上沿）。
         点击=先强制刷新（绕过阅读态暂停）→ 锚定末条（底部）→ 清计数（铁律：刷新成功才清，失败保留）；
         滚回底部（isNearBottom）后浮条自动消失。定位相对 .chat-tab（absolute，不随消息滚动） -->
    <view
      v-if="!isNearBottom && unreadCount > 0 && messages.length > 0"
      class="new-messages-tip"
      @tap="handleJumpToBottom"
    >
      <text>{{ unreadCount }} 条新留言</text>
      <text class="iconfont icon-arrow-down tip-arrow"></text>
    </view>

    <!-- FE-8（v2.0）：最早尽头轻提示——仅触顶且无更早时短暂弹出（方案 A：深色半透明胶囊），
         淡入后 1s 开始 300ms 淡出，2s 防抖不连弹 -->
    <view
      v-if="noMoreTipVisible"
      class="no-more-tip"
      :class="{ fading: noMoreTipFading }"
    >
      <text>没有更多消息了</text>
    </view>
    
    <!-- 输入栏 - 固定在底部 -->
    <view class="input-bar">
      <view class="input-wrapper">
        <input 
          v-model="inputText"
          class="message-input"
          placeholder="一起聊聊吧~"
          placeholder-class="input-placeholder"
          :maxlength="500"
          confirm-type="send"
          @confirm="handleSendMessage"
          @focus="handleInputFocus"
          @blur="handleInputBlur"
        />
        <button 
          class="send-btn"
          :disabled="!inputText.trim()"
          @tap="handleSendMessage"
        >
          发送
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
// ============================================================
// 互动讨论留言列表 —— 交互规则定案（实施文档《播放页互动讨论留言区-展示顺序与智能跟随-实施规划文档》v2.0）
// 契约（后端 v2.0 已上线）：GET /rooms/{id}/messages = DESC 分页窗口 + 页内 ASC（旧→新）；
//   page1=最新窗口、page 递增向更早；列表直渲 = 最早在上、最新在底（微信式，禁止 reverse）
// 1) 进入/切回：加载后自动锚定末条（最新，底部）——scroll-into-view 锚点，跨帧先清再设
// 2) 新留言跟随（5s 轮询按位置分级）：
//    近底（scrollTop 距底 ≤ 阈值且非触摸/非聚焦）→ 末条 id+条数浅比较：无变化不赋值（防空转重渲染）；
//                                    有变化 → 整体替换并锚定末条（新留言出现在底部）
//    阅读态（滚离底部，向上翻更早）→ 不替换仅计数（本地末条在 page1 响应中的位置差 = 新留言数）
// 3) 滚回底部：触底（scrolltolower）即时补拉 / 轮询（≤5s）兜底强制刷新并清计数（回底闭环）
// 4) 发送成功：刷新并锚底看自己刚发的新留言，清计数
// 5) 翻更早历史：上滑触顶（scrolltoupper）加载 pageN+1 更早窗口**插到列表头部**；
//                更早尽头继续上滑 → 弹「没有更多消息了」轻提示（1.3s 自动淡出，2s 防抖）
// 6) 浮条：阅读态且有未读 → 输入条上沿胶囊「X 条新留言」；点击 = 先强制刷新 → 锚底 → 清计数；
//          滚回底部自动消失；断网失败保留计数与浮条
// 7) 键盘：聚焦期间暂停轮询跟随与回底补拉（键盘顶起改可视高度防误判），失焦后近底则补拉一次
// ============================================================
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getRoomMessages, sendRoomMessage, deleteRoomMessage } from '@/api/message'
import { resolveMediaUrl } from '@/utils/url'
import { useAuthStore } from '@/store/auth'
import type { Message } from '@/types/message'

interface Props {
  roomId: string
}

const props = defineProps<Props>()

const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(true)
const scrollIntoViewId = ref('') // 滚底锚点（末条消息 id；id 每次变化必触发）
const isOnline = ref(true)
const currentPage = ref(1)
const hasMore = ref(true)
const isLoadingMore = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | null = null

// === v2.0：正序（底部锚定）智能跟随状态 ===
const NEAR_BOTTOM_THRESHOLD = 100 // 距底判定阈值(px)，真机调参
const isNearBottom = ref(true)      // 默认在底部（进入后锚定末条=最新区）
const containerHeightPx = ref(0)    // 消息滚动容器可视高（.message-list 测量缓存，用于距底计算）
const isTouching = ref(false)       // 手指触摸中不替换列表（防手势竞态）
const isInputFocused = ref(false)   // 键盘弹出期间暂停跟随（可视高度变化防误判）
const unreadCount = ref(0)          // 阅读态期间累计的新留言数（浮条展示用）
// no-more 轻提示（FE-8）
const noMoreTipVisible = ref(false)
const noMoreTipFading = ref(false)
let noMoreTipTimer: ReturnType<typeof setTimeout> | null = null
let noMoreTipTimer2: ReturnType<typeof setTimeout> | null = null
let lastNoMoreTipAt = 0

onMounted(async () => {
  await loadMessages()
  
  // 首载完成：测量滚动容器可视高（距底判定用）并锚定末条=最新（微信式：进入即最新消息处）
  nextTick(() => {
    measureContainer()
  })
  scrollToLatest()

  // 启动定时刷新
  startRefreshTimer()
  
  // 监听网络状态
  uni.onNetworkStatusChange((res) => {
    isOnline.value = res.isConnected
    
    if (res.isConnected) {
      // 网络恢复：按当前滚动位置刷新并启动定时器
      refreshByPosition()
      startRefreshTimer()
    } else {
      // 网络断开，停止定时器
      stopRefreshTimer()
      uni.showToast({
        title: '网络已断开',
        icon: 'none'
      })
    }
  })
})

onUnmounted(() => {
  stopRefreshTimer()
  if (noMoreTipTimer) {
    clearTimeout(noMoreTipTimer)
    noMoreTipTimer = null
  }
  if (noMoreTipTimer2) {
    clearTimeout(noMoreTipTimer2)
    noMoreTipTimer2 = null
  }
})

// 启动定时器（5s 轮询：按当前滚动位置刷新——近顶替换 / 阅读态计数 / 聚焦暂停）
const startRefreshTimer = () => {
  if (refreshTimer) return
  refreshTimer = setInterval(() => {
    if (isOnline.value) {
      refreshByPosition()
    }
  }, 5000)
}

// 停止定时器
const stopRefreshTimer = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 按当前滚动位置刷新（轮询/网络恢复共用）：
// - 近底态（且非触摸/非聚焦）：有未读则强制补拉并锚底（回底闭环）；否则浅比较无新消息不赋值（防空转重渲染）
// - 阅读态（滚离底部，向上翻更早）：不替换，仅累计新留言数（防阅读位置漂移）
const refreshByPosition = async () => {
  if (isInputFocused.value) return
  if (isNearBottom.value && !isTouching.value) {
    if (unreadCount.value > 0) {
      const ok = await loadMessages({ anchorToLatest: true })
      if (ok) unreadCount.value = 0
      return
    }
    await loadMessages({ skipIfUnchanged: true, anchorToLatest: true })
  } else {
    const n = await countNewMessages()
    if (n > 0) unreadCount.value += n
  }
}

// 加载最新一页（契约 v2.0：page1=最新窗口、页内 ASC，整体替换）
// skipIfUnchanged：末条（最新）id 与条数一致则跳过赋值（防 5s 空转重渲染/闪烁）
// anchorToLatest：赋值成功后锚定末条（滚到底部看最新）
// @returns 是否成功（供调用方决定是否清未读计数）
const loadMessages = async (opts: { skipIfUnchanged?: boolean; anchorToLatest?: boolean } = {}): Promise<boolean> => {
  try {
    const { data } = await getRoomMessages(props.roomId, {
      page: 1,
      size: 50
    })
    const items: Message[] = data.items || []
    if (opts.skipIfUnchanged && messages.value.length > 0) {
      const curLastId = messages.value[messages.value.length - 1]?.id
      const newLastId = items[items.length - 1]?.id
      if (curLastId === newLastId && messages.value.length === items.length) return true
    }
    messages.value = items
    currentPage.value = 1

    // 适配后端返回格式：使用total和size计算total_pages
    const totalPages = data.pagination?.total_pages || Math.ceil((data.total || 0) / (data.size || 50))
    hasMore.value = totalPages > 1
    if (opts.anchorToLatest) {
      scrollToLatest()
    }
    return true
  } catch (error: any) {
    console.error('获取消息失败:', error)
    // 首次加载失败才显示错误，刷新失败静默失败
    if (loading.value) {
      uni.showToast({
        title: error.message || '获取消息失败',
        icon: 'none',
        duration: 2000
      })
    }
    return false
  } finally {
    loading.value = false
  }
}

// 锚定末条（最新）：scroll-into-view 需子节点 id 匹配；同 id 不触发 → 跨帧先清空再设
const scrollToLatest = () => {
  const last = messages.value[messages.value.length - 1]
  if (!last) return
  const anchor = `msg-${last.id}`
  nextTick(() => {
    scrollIntoViewId.value = ''
    setTimeout(() => {
      scrollIntoViewId.value = anchor
    }, 120)
  })
}

// 测量消息滚动容器可视高（距底判定 = scrollHeight - scrollTop - 容器高；面板高 px 固定，缓存安全）
const measureContainer = () => {
  const query = uni.createSelectorQuery()
  query.select('.message-list').boundingClientRect((rect: any) => {
    if (rect && rect.height) {
      containerHeightPx.value = rect.height
    }
  })
  query.exec()
}

// 阅读态轮询：拉 page1 但不替换，按"本地末条（最新）在响应中的位置"累计新留言数
const countNewMessages = async (): Promise<number> => {
  const localLast = messages.value[messages.value.length - 1]
  const localLastId = localLast?.id
  if (!localLastId) return 0
  try {
    const { data } = await getRoomMessages(props.roomId, {
      page: 1,
      size: 50
    })
    const items: Message[] = data.items || []
    const idx = items.findIndex(m => m.id === localLastId)
    if (idx < 0) return 0 // 本地末条不在最新窗口（兜底不计）
    const newCount = items.length - (idx + 1) // 响应中比本地末条更新的条数
    return newCount > 0 ? newCount : 0
  } catch (error: any) {
    console.error('统计新留言失败:', error)
    return 0
  }
}

// 加载更早历史（契约 v2.0：page 递增=更早窗口、页内 ASC → 插到列表头部；列表触顶触发）
// ⚠️ 页大小必须与 loadMessages 一致（size=50）：否则 OFFSET 粒度错位 → 翻页滑窗重叠/永远翻不到更早页
const loadMore = async () => {
  if (!hasMore.value || isLoadingMore.value) return

  isLoadingMore.value = true
  currentPage.value++

  try {
    const { data } = await getRoomMessages(props.roomId, {
      page: currentPage.value,
      size: 50
    })

    // 更早消息插到列表头部（正序渲染：头部=更早方向；页内 ASC 使跨页顺序连续无锯齿）
    messages.value = [...(data.items || []), ...messages.value]

    // 适配后端返回格式：使用total和size计算total_pages
    const totalPages = data.pagination?.total_pages || Math.ceil((data.total || 0) / (data.size || 50))
    hasMore.value = currentPage.value < totalPages
  } catch (error: any) {
    console.error('加载更多消息失败:', error)
    currentPage.value-- // 回退页码
  } finally {
    isLoadingMore.value = false
  }
}

// 触顶处理：有更早 → 加载插头；已到更早尽头 → 弹「没有更多消息了」轻提示（2s 防抖）
const handleReachTop = () => {
  if (isLoadingMore.value) return
  if (hasMore.value) {
    loadMore()
  } else {
    flashNoMoreTip()
  }
}

// FE-8：轻提示闪显——淡入（150ms 级）→ 1s 后淡出(300ms) → 1.3s 隐藏；2s 防抖
const flashNoMoreTip = () => {
  const now = Date.now()
  if (now - lastNoMoreTipAt < 2000) return
  lastNoMoreTipAt = now
  noMoreTipVisible.value = true
  noMoreTipFading.value = true
  nextTick(() => {
    noMoreTipFading.value = false
  })
  if (noMoreTipTimer) clearTimeout(noMoreTipTimer)
  if (noMoreTipTimer2) clearTimeout(noMoreTipTimer2)
  noMoreTipTimer = setTimeout(() => {
    noMoreTipFading.value = true
  }, 1000)
  noMoreTipTimer2 = setTimeout(() => {
    noMoreTipVisible.value = false
    noMoreTipFading.value = false
  }, 1300)
}

// 滚动事件：距底判定（scrollHeight - scrollTop - 容器高 ≤ 阈值 → 近底）
// 容器高未测得（scroll-view 未渲染等）时：滚到顶部（st≤5）= 在最早区 → 非近底；其余维持现状
function handleScroll(e: any) {
  const d = e?.detail || {}
  const st = typeof d.scrollTop === 'number' ? d.scrollTop : 0
  const sh = typeof d.scrollHeight === 'number' ? d.scrollHeight : 0
  if (containerHeightPx.value > 0 && sh > 0) {
    isNearBottom.value = sh - st - containerHeightPx.value <= NEAR_BOTTOM_THRESHOLD
  } else if (st <= 5) {
    isNearBottom.value = false
  }
}

// 触底（滚回底部）：标记近底并即时触发回底补拉（若有未读；铁律：刷新成功才清计数）
const handleScrollToLower = () => {
  isNearBottom.value = true
  if (isOnline.value && !isInputFocused.value && unreadCount.value > 0) {
    loadMessages({ anchorToLatest: true }).then((ok) => {
      if (ok) unreadCount.value = 0
    })
  }
}

// C2（v2.0）：浮条点击回底 —— 铁律：先强制刷新（绕过阅读态暂停守卫，loadMessages 内锚底）
// 刷新成功后才清计数（浮条随 isNearBottom 状态消失）；失败（断网等）保留计数与浮条，下轮轮询重试
const handleJumpToBottom = async () => {
  if (!isOnline.value) return
  const ok = await loadMessages({ anchorToLatest: true })
  if (ok) unreadCount.value = 0
}

// 发送消息（包含权限验证）
const handleSendMessage = async () => {
  if (!inputText.value.trim()) return
  
  // 权限验证
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated) {
    uni.showToast({
      title: '请先登录',
      icon: 'none',
      duration: 2000
    })
    return
  }
  
  try {
    await sendRoomMessage(props.roomId, {
      content: inputText.value
    })
    inputText.value = ''
    // 发送后：刷新并锚定末条（自己刚发的新留言在底部=最新区），清未读计数（v2.0 正序契约）
    unreadCount.value = 0
    await loadMessages({ anchorToLatest: true })
    uni.showToast({ title: '发送成功', icon: 'success' })
  } catch (error: any) {
    console.error('发送消息失败:', error)
    // request 层已 toast（内容安全 2004/2005 等）时不重复提示
    if (!error?.__toasted) {
      uni.showToast({
        title: error.message || '发送失败，请重试',
        icon: 'none',
        duration: 2000
      })
    }
  }
}

// XSS防护：内容清理函数
const sanitizeContent = (content: string): string => {
  if (!content) return ''
  
  // 移除HTML标签
  let sanitized = content.replace(/<[^>]*>/g, '')
  
  // 转义特殊字符
  sanitized = sanitized
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
  
  return sanitized
}

// 图片加载失败处理
const handleAvatarError = (e: any) => {
  e.target.src = '/static/default-avatar.png'
}

// 时间格式化
const formatTime = (timeStr: string): string => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 超过24小时
  return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
}

// B6（v2.0）：输入聚焦/失焦（键盘顶起会改变可视高度，聚焦期间暂停轮询跟随与回底补拉，防 isNearBottom 误判）
const handleInputFocus = () => {
  isInputFocused.value = true
}

const handleInputBlur = () => {
  isInputFocused.value = false
  // 聚焦期间可能错过轮询：失焦后若在底部则立即补拉一次
  if (isNearBottom.value && isOnline.value) {
    refreshByPosition()
  }
}

// 是否为自己发送的消息（用于气泡 Primary tint）
const authStore = useAuthStore()
function isSelf(msg: Message): boolean {
  const uid = (authStore as any).user?.user_id ?? (authStore as any).user?.id
  return Boolean(uid && msg.user_id && String(msg.user_id) === String(uid))
}

// 删除权限：本人留言或管理员（后端同语义：管理员可删任意，普通用户仅本人）
function canDelete(msg: Message): boolean {
  if ((authStore as any).isAdmin) return true
  return isSelf(msg)
}

// 长按删除留言（本人/管理员）
async function handleDeleteMessage(msg: Message) {
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({
      title: '删除留言',
      content: '确定删除这条留言？此操作不可恢复。',
      confirmColor: '#dc2626',
      success: r => resolve(r),
    })
  })
  if (!confirm) return
  try {
    await deleteRoomMessage(props.roomId, msg.id)
    messages.value = messages.value.filter(m => m.id !== msg.id)
    uni.showToast({ title: '已删除', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败，请稍后再试', icon: 'none' })
  }
}
</script>

<style scoped>
.chat-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  max-width: 100vw;
  overflow-x: hidden;
  box-sizing: border-box;
  position: relative; /* 供回底浮条 / no-more 轻提示 absolute 定位（相对整个聊天面板，不随消息滚动） */
  background: #ffffff; /* 整个聊天区域白色背景 */
}

/* C1/C2（v2.0）：阅读态回底浮条——贴输入条上沿、居中胶囊，主色底白字 + 下箭头 */
.new-messages-tip {
  position: absolute;
  bottom: calc(152rpx + env(safe-area-inset-bottom)); /* 输入栏高(约128rpx)+安全区上方留白 */
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 28rpx;
  background-color: var(--home-primary);
  color: #ffffff;
  font-size: 24rpx;
  border-radius: 999rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.18);
  white-space: nowrap;
}

.new-messages-tip:active {
  opacity: 0.9;
}

.tip-arrow {
  font-size: 20rpx;
  color: #ffffff;
}

/* FE-8（v2.0）：最早尽头轻提示——底部居中深色半透明胶囊（方案 A + 产品裁定放底部）：
   淡入 150ms 级（fading=false 时 opacity 1）、淡出 300ms（fading=true）；
   高度置于"新留言回底浮条"之上，避免同帧重叠 */
.no-more-tip {
  position: absolute;
  bottom: calc(240rpx + env(safe-area-inset-bottom));
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  padding: 10rpx 28rpx;
  background-color: rgba(0, 0, 0, 0.55);
  color: #ffffff;
  font-size: 24rpx;
  border-radius: 999rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.18);
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.no-more-tip.fading {
  opacity: 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.empty-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: #ccc;
}

.message-list {
  flex: 1;
  padding: var(--home-spacing-module);
  padding-bottom: 160rpx;
  overflow-y: auto;
  width: 100%;
  max-width: 100vw;
  box-sizing: border-box;
  background: var(--home-bg);
}

.loading-more {
  text-align: center;
  padding: var(--home-spacing-inner);
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
}

/* 微信式消息气泡 */
.message-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 28rpx;
  max-width: 100%;
}

/* 自己：整行翻转 → 头像在右、气泡在右（row-reverse 只翻主轴顺序，交叉轴对齐不受影响） */
.message-item.self {
  flex-direction: row-reverse;
}

.user-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.message-item.self .user-avatar {
  margin-right: 0;
  margin-left: 16rpx;
}

/* 气泡列：宽度自适应内容；上限 72% 面板宽，超长消息在此约束内换行 */
.message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 72%;
  min-width: 0;
}

.message-item.self .message-body {
  align-items: flex-end;
}

/* 气泡外 meta：他人=昵称+时间同行；自己=仅时间（无昵称） */
.message-meta {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  margin-bottom: 6rpx;
  padding: 0 8rpx;
  max-width: 100%;
  box-sizing: border-box;
}

.user-name {
  font-size: 22rpx;
  color: var(--home-text2);
  flex-shrink: 0;
  max-width: 320rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-time {
  font-size: 20rpx;
  color: var(--home-text2);
  opacity: 0.65;
  flex-shrink: 0;
}

/* 气泡本体：仅文字，宽度随内容；他人浅色卡片、自己品牌浅底 */
.message-bubble {
  padding: 16rpx 24rpx;
  background-color: var(--home-card);
  border: 1rpx solid var(--home-border);
  border-radius: 20rpx;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.message-item.self .message-bubble {
  background-color: var(--home-tag-forecast-bg);
  border-color: transparent;
}

.message-text {
  display: block;
  font-size: var(--home-fs-meta);
  color: var(--home-text1);
  line-height: 1.5;
  /* 长串（无空格 URL/英文）强制折行，防止撑破气泡；中文按字折行不受影响 */
  overflow-wrap: break-word;
  word-break: break-all;
}

.input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  max-width: 100vw;
  background: var(--home-bg);
  border-top: 1rpx solid var(--home-border);
  padding: 20rpx 24rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  z-index: 100;
}

.input-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  gap: var(--home-spacing-inner);
}

.message-input {
  flex: 1;
  min-height: 88rpx;
  padding: 20rpx 32rpx;
  background-color: var(--home-card);
  border: 2rpx solid var(--home-border);
  border-radius: var(--home-r-md);
  font-size: var(--home-fs-meta);
  color: var(--home-text1);
  transition: var(--transition-base);
  box-sizing: border-box;
}

.message-input:focus {
  border-color: var(--home-primary);
}

.input-placeholder {
  color: var(--home-text2);
  opacity: 0.85;
  font-size: var(--home-fs-meta);
}

.send-btn {
  min-width: 120rpx;
  min-height: 88rpx;
  padding: 20rpx 40rpx;
  background-color: var(--home-primary);
  color: var(--color-text-on-primary);
  border: none;
  border-radius: var(--home-r-md);
  font-size: var(--home-fs-meta);
  font-weight: 500;
  transition: var(--transition-base);
}

.send-btn::after {
  border: none;
}

.send-btn:active:not([disabled]) {
  opacity: 0.9;
}

.send-btn[disabled] {
  background-color: var(--home-border);
  color: var(--home-text2);
  opacity: 0.7;
}
</style>
