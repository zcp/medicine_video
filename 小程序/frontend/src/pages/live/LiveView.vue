<!--
 * LiveView - 直播观看页面
 * @description 提供直播/回放观看体验，支持视频播放、实时统计、互动功能
 * @author 直播SaaS团队
 -->
<template>
  <view class="live-view-page">
    <!-- 加载状态 -->
    <LoadingIndicator v-if="loading && !playUrl" text="加载中..." fullscreen />
    
    <!-- 错误状态：房间信息模式（测播无场次）不用红条 -->
    <ErrorBanner 
      v-if="error && !roomInfoOnly" 
      :message="error"
      @close="error = null"
    />
    
    <!-- 播放器固定；下方（信息+Tab+内容）一体滚动，看播与看留言可并行 -->
    <!-- 视频播放器区域（适配小程序：视频是原生层，覆盖控件需用 cover-view） -->
    <view class="player-section">
      <view class="player-container">
          <!-- #ifdef MP-WEIXIN -->
          <live-player
            v-if="playUrl && useLivePlayer && !isScheduled"
            id="live-live-player"
            :src="playUrl"
            mode="live"
            :autoplay="true"
            :muted="false"
            :orientation="'vertical'"
            :object-fit="'contain'"
            class="video-player"
            @statechange="handleLivePlayerStateChange"
            @error="handleLivePlayerError"
            @fullscreenchange="handleFullscreenChange"
          />

          <video
            v-else-if="playUrl && !isScheduled"
            id="live-video-player"
            :src="playUrl"
            :autoplay="true"
            :controls="true"
            :show-fullscreen-btn="true"
            :show-play-btn="true"
            :enable-progress-gesture="isReplay"
            :show-center-play-btn="true"
            :object-fit="'contain'"
            class="video-player"
            @play="handlePlay"
            @pause="handlePause"
            @timeupdate="handleTimeUpdate"
            @ended="handleEnded"
            @error="handleVideoError"
            @fullscreenchange="handleFullscreenChange"
          >
          </video>
          <!-- #endif -->

          <!-- #ifndef MP-WEIXIN -->
          <video
            v-if="playUrl && !isScheduled"
            id="live-video-player"
            :src="playUrl"
            :autoplay="true"
            :controls="true"
            :show-fullscreen-btn="true"
            :show-play-btn="true"
            :enable-progress-gesture="isReplay"
            :show-center-play-btn="true"
            :object-fit="'contain'"
            class="video-player"
            @play="handlePlay"
            @pause="handlePause"
            @timeupdate="handleTimeUpdate"
            @ended="handleEnded"
            @error="handleVideoError"
            @fullscreenchange="handleFullscreenChange"
          >
          </video>
          <!-- #endif -->

          <view v-if="playUrl && !useLivePlayer && !isScheduled" class="player-native-tools">
            <view class="player-native-tools__left">
              <text class="player-native-tools__label">画质</text>
              <text class="player-native-tools__value">{{ currentQuality }}</text>
            </view>
            <view class="player-native-tools__right">
              <view class="player-native-tools__btn" @tap.stop="handleQualityClick">切换画质</view>
            </view>
          </view>

          <view v-else class="player-placeholder">
            <image
              v-if="isScheduled && playerCoverUrl && !playerCoverBroken"
              class="player-cover"
              :src="playerCoverUrl"
              mode="aspectFill"
              @error="handlePlayerCoverError"
            />
            <view v-else class="placeholder-content">
              <uni-icons type="videocam" size="28" color="rgba(255,255,255,0.75)" />
              <text class="placeholder-text">
                {{ playerPlaceholderText }}
              </text>
            </view>
          </view>
        </view>
    </view>

    <scroll-view
      class="live-body-scroll"
      scroll-y
      :enable-flex="true"
      :show-scrollbar="false"
      :scroll-into-view="bodyScrollIntoView"
      scroll-with-animation
    >
      <!-- 直播信息区域 -->
      <view class="session-info">
        <view class="session-info__title-row" @tap="toggleTitle">
          <text v-if="isPrivateRoom" class="privacy-chip">连接测试</text>
          <text class="title">
            {{ titleExpanded || !truncatedTitle ? displayTitle : truncatedTitle }}
          </text>
          <uni-icons
            v-if="displayTitle && displayTitle.length > titleFoldThreshold"
            :type="titleExpanded ? 'up' : 'down'"
            size="16"
            :color="'var(--color-text-tertiary)'"
          />
        </view>

        <!-- 标签折叠（标题下方） -->
        <view
          v-if="sessionTags.length > 0"
          class="session-info__tags"
        >
          <view class="tags-row">
            <text
              v-for="tag in visibleTags"
              :key="tag.id"
              class="tag"
            >
              {{ tag.name }}
            </text>
            <view
              v-if="sessionTags.length > maxVisibleTags"
              class="tags-toggle"
              @tap.stop="toggleTags"
            >
              <text class="tags-toggle-text">
                {{ showAllTags ? '收起' : `+${sessionTags.length - maxVisibleTags}` }}
              </text>
            </view>
          </view>
        </view>

        <!-- 专家信息 + 关注专家（对齐 Expert Follow API）；无专家时头像/名称兜底，不常驻骨架屏 -->
        <view class="session-info__expert" :class="{ 'session-info__expert--placeholder': !hasExpertData }">
          <template v-if="expertSectionLoading">
            <view class="expert-avatar expert-avatar--placeholder skeleton-block" />
            <view class="expert-brief">
              <view class="skeleton-line skeleton-line--name" />
              <view class="skeleton-line skeleton-line--title" />
            </view>
          </template>
          <template v-else>
            <image
              :src="displayExpertAvatar"
              class="expert-avatar"
              mode="aspectFill"
              @error="onPrimaryExpertAvatarError"
            />
            <view class="expert-brief">
              <text class="expert-name">{{ displayExpertName }}</text>
              <text v-if="displayExpertTitle" class="expert-title">{{ displayExpertTitle }}</text>
              <text v-else class="expert-title expert-title--placeholder"> </text>
            </view>
          </template>

          <view
            class="follow-btn"
            :class="{ 'follow-btn--active': isExpertFollowed, 'follow-btn--disabled': !currentExpertIdForActions || isExpertFollowPending }"
            @tap.stop="toggleExpertFollow"
          >
            <text>{{ isExpertFollowed ? '已关注' : '关注' }}</text>
          </view>
        </view>

        <!-- 点赞 / 收藏 / 下载（预告：订阅） / 分享（保留操作；仅去掉上方人数等统计） -->
        <view class="session-info__actions">
          <view class="action-chip" @tap="handleLike">
            <view class="action-icon">
              <text
                class="iconfont action-icon__glyph icon-xihuan"
                :style="{ color: 'var(--color-danger)' }"
              />
            </view>
            <text class="action-text">点赞</text>
          </view>
          <view class="action-chip" :class="{ 'action-chip--active': isFavorited }" @tap="handleFavorite">
            <view class="action-icon">
              <text
                class="iconfont action-icon__glyph"
                :class="isFavorited ? 'icon-shoucang1' : 'icon-shoucang'"
                :style="{ color: 'var(--color-warning)' }"
              />
            </view>
            <text class="action-text" :class="{ 'action-text--active': isFavorited }">{{ isFavorited ? '已收藏' : '收藏' }}</text>
          </view>
          <view
            v-if="showSubscriptionAction"
            class="action-chip"
            :class="{ 'action-chip--active': isSubscribed }"
            @tap="toggleSubscription"
          >
            <view class="action-icon">
              <text
                class="iconfont action-icon__glyph"
                :class="isSubscribed ? 'icon-yigouxuan' : 'icon-weigouxuan'"
                :style="{ color: 'var(--color-primary)' }"
              />
            </view>
            <text class="action-text" :class="{ 'action-text--active': isSubscribed }">{{ isSubscribed ? '已订阅' : '订阅' }}</text>
          </view>
          <view v-else-if="showDownloadAction" class="action-chip" @tap="handleDownload">
            <view class="action-icon">
              <image class="action-icon__img" src="/static/images/icons/download.svg" mode="aspectFit" />
            </view>
            <text class="action-text">下载</text>
          </view>
          <view class="action-chip" @tap="handleShare">
            <view class="action-icon">
              <text class="iconfont action-icon__glyph icon-fenxiang" :style="{ color: 'var(--color-success)' }" />
            </view>
            <text class="action-text">分享</text>
          </view>
        </view>
      </view>

    <!-- 功能性 Tab：在下方滚动区内吸顶 -->
    <view class="live-tabs-section">
      <view v-if="functionalTabsLoading" class="section-empty tab-content">
        <text class="empty-text">功能性Tab加载中…</text>
      </view>
      <view v-else-if="functionalTabsError" class="section-empty tab-content">
        <text class="empty-text">功能性Tab加载失败：{{ functionalTabsError }}</text>
      </view>
      <view v-else-if="enableFunctionalTabs" class="live-tabs">
        <!-- 与首页同款 flow：点选 ↔ 左右滑；内容撑高，外层 scroll-view 竖滚（不定高 swiper） -->
        <StickyTabPager
          :tabs="functionalPagerTabs"
          :current="functionalSwiperIndex"
          :equal-width="true"
          flow
          @change="handleFunctionalPagerChange"
        >
          <template #pane="{ tab }">
            <view
              class="tab-content"
              :class="{ 'tab-content--message': functionalTabOf(tab.id)?.tab_key === MESSAGE_TAB_KEY }"
            >
              <view
                v-if="functionalTabOf(tab.id)?.tab_key === EXPERT_INTRO_TAB_KEY"
                class="tab-content-item"
              >
                <view class="intro-card">
                  <view v-if="sessionExpertsLoading" class="section-empty">
                    <text class="empty-text">专家信息加载中…</text>
                  </view>
                  <view v-else-if="expertIntroItems.length" class="expert-list">
                    <view
                      v-for="ex in expertIntroItems"
                      :key="ex.id"
                      class="expert-item"
                      @tap="openExpertDetailById(ex.id)"
                    >
                      <image
                        class="expert-avatar"
                        :src="expertListAvatarSrc(ex)"
                        mode="aspectFill"
                        @error="onExpertListAvatarError(ex.id, ex.avatar_url)"
                      />
                      <view class="expert-meta">
                        <text class="expert-name">{{ ex.name }}</text>
                        <text v-if="ex.title || ex.hospital || ex.role" class="expert-sub">
                          {{ [ex.role, ex.title, ex.hospital].filter(Boolean).join(' · ') }}
                        </text>
                      </view>
                      <view
                        class="follow-btn"
                        :class="{
                          'follow-btn--active': !!followingMap[ex.id],
                          'follow-btn--disabled': followPendingId === ex.id
                        }"
                        @tap.stop="onExpertListFollow(ex.id)"
                      >
                        <text>{{ followPendingId === ex.id ? '...' : (followingMap[ex.id] ? '已关注' : '关注') }}</text>
                      </view>
                    </view>
                  </view>
                  <view v-else class="section-empty">
                    <text class="empty-text">暂无关联专家</text>
                  </view>
                </view>
              </view>

              <view
                v-else-if="functionalTabOf(tab.id)?.tab_key === BRAND_INTRO_TAB_KEY"
                class="tab-content-item"
              >
                <view class="intro-card">
                  <view v-if="roomBrandsLoading" class="section-empty">
                    <text class="empty-text">品牌信息加载中…</text>
                  </view>
                  <view v-else-if="roomBrands.length" class="brand-list">
                    <view
                      v-for="b in roomBrands"
                      :key="b.id"
                      class="brand-item"
                      @tap="openBrandDetail(b.id)"
                    >
                      <image
                        class="brand-logo"
                        :src="brandLogoSrc(b)"
                        mode="aspectFill"
                        @error="onBrandLogoError(b.id, b.logo_url)"
                      />
                      <view class="brand-meta">
                        <text class="brand-name">{{ b.name }}</text>
                        <text v-if="b.website_url" class="brand-website">{{ b.website_url }}</text>
                      </view>
                    </view>
                  </view>
                  <view v-else class="section-empty">
                    <text class="empty-text">暂无关联品牌</text>
                  </view>
                </view>
              </view>

              <view
                v-else-if="functionalTabOf(tab.id)?.tab_key === ROOM_INTRO_TAB_KEY"
                class="tab-content-item"
              >
                <view class="intro-card">
                  <view class="intro-body">
                    <text
                      v-if="functionalTabOf(tab.id)?.text_content"
                      class="intro-text"
                      :class="{ 'is-collapsed': introCanToggle && !introExpanded }"
                    >
                      {{ functionalTabOf(tab.id)?.text_content }}
                    </text>

                    <view
                      v-if="introCanToggle && functionalTabOf(tab.id)?.text_content"
                      class="intro-toggle"
                      @tap.stop="toggleIntro"
                    >
                      <text class="intro-toggle__text">{{ introExpanded ? '收起' : '展开' }}</text>
                    </view>
                    <view v-if="functionalTabOf(tab.id)?.image_url" class="intro-images">
                      <image
                        :src="normalizeAnyImageUrl(functionalTabOf(tab.id)?.image_url) || ''"
                        mode="widthFix"
                        class="intro-image"
                        @error="handleFunctionalTabImageError"
                      />
                    </view>
                  </view>
                </view>
              </view>

              <view
                v-else-if="functionalTabOf(tab.id)?.tab_key === MESSAGE_TAB_KEY"
                class="tab-content-item message-board-tab"
              >
                <view class="message-list">
                  <view v-if="messagesLoading && !messages.length" class="msg-loading">
                    <text class="msg-loading-text">加载中...</text>
                  </view>
                  <view v-else-if="!messages.length" class="msg-empty">
                    <text class="msg-empty-text">{{ isLoggedIn ? '暂无讨论，在下方输入框发表第一条吧' : '暂无讨论，登录后即可参与' }}</text>
                  </view>
                  <template v-else>
                    <view v-if="isLoggedIn && hasOwnMessages" class="msg-tip">
                      <text class="msg-tip-text">长按自己的讨论可删除</text>
                    </view>
                    <view v-if="messagesHasMore" class="msg-load-more" @tap="handleLoadMoreMessages">
                      <text class="msg-load-more-text">{{ messagesLoadingMore ? '加载中...' : '↑ 加载更早讨论' }}</text>
                    </view>
                    <view
                      v-for="msg in messagesSorted"
                      :id="'msg-' + msg.id"
                      :key="msg.id"
                    >
                      <MessageItem
                        v-if="msg"
                        :message="msg"
                        :current-user-id="authStore.userInfo?.user_id"
                        :is-admin="isAdmin"
                        @delete="handleDeleteMessage"
                      />
                    </view>
                  </template>
                </view>
              </view>

              <view v-else class="tab-content-item">
                <view v-if="functionalTabOf(tab.id)?.content_type === 'text'" class="section-content">
                  <text v-if="functionalTabOf(tab.id)?.text_content">{{ functionalTabOf(tab.id)?.text_content }}</text>
                  <text v-else class="empty-text">暂无内容</text>
                </view>

                <view v-else-if="functionalTabOf(tab.id)?.content_type === 'image'" class="section-image">
                  <image
                    v-if="functionalTabOf(tab.id)?.image_url"
                    :src="normalizeAnyImageUrl(functionalTabOf(tab.id)?.image_url) || ''"
                    mode="widthFix"
                    class="tab-image"
                    @error="handleFunctionalTabImageError"
                  />
                  <text v-else class="empty-text">暂无图片</text>
                </view>

                <view v-else class="section-mixed">
                  <text v-if="functionalTabOf(tab.id)?.text_content" class="section-content">{{ functionalTabOf(tab.id)?.text_content }}</text>
                  <image
                    v-if="functionalTabOf(tab.id)?.image_url"
                    :src="normalizeAnyImageUrl(functionalTabOf(tab.id)?.image_url) || ''"
                    mode="widthFix"
                    class="tab-image"
                    @error="handleFunctionalTabImageError"
                  />
                  <text v-if="!functionalTabOf(tab.id)?.text_content && !functionalTabOf(tab.id)?.image_url" class="empty-text">暂无内容</text>
                </view>
              </view>
            </view>
          </template>
        </StickyTabPager>
      </view>
      <view v-else class="section-empty tab-content">
        <text class="empty-text">该直播间未配置功能性Tab</text>
      </view>
    </view>
      <!-- 给固定底栏留空 -->
      <view class="live-body-spacer" />
    </scroll-view>

    <!-- 留言底栏：挂在页面层，仅讨论 Tab 显示（避免 swiper 多 pane 固定层串显） -->
    <template v-if="isMessageTabActive">
      <view v-if="!isLoggedIn" class="msg-login-hint" @tap="redirectToLogin">
        <text class="msg-login-hint-text">登录后即可发表讨论，点击前往登录</text>
      </view>
      <view class="msg-input-bar">
        <view class="msg-input-wrap">
          <input
            v-model="messageInputContent"
            class="msg-input"
            :placeholder="isLoggedIn ? '说点什么...' : '登录后可讨论'"
            :disabled="!isLoggedIn"
            :maxlength="500"
            confirm-type="send"
            @confirm="handleSendMessage"
          />
          <view
            v-if="!isLoggedIn"
            class="msg-input-mask"
            @tap="redirectToLogin"
          />
        </view>
        <view
          class="msg-send-btn"
          :class="{ 'msg-send-disabled': !messageInputContent.trim() || messageSending }"
          @tap="handleSendMessage"
        >
          <text class="msg-send-text">{{ messageSending ? '...' : '发送' }}</text>
        </view>
      </view>
      <view v-if="isLoggedIn" class="msg-char-count">
        <text class="msg-char-count-text">{{ messageInputContent.length }}/500</text>
      </view>
    </template>

    <!-- 用户气泡菜单 -->
    <UserBubbleMenu
      :visible="showUserBubble"
      :user-info="authStore.userInfo"
      :is-logged-in="isLoggedIn"
      :is-admin="isAdmin"
      @close="handleBubbleClose"
      @navigate="handleBubbleNavigate"
      @logout="handleBubbleLogout"
    />

    <!-- 底部导航栏 -->
    <BottomNavBar
      :user-avatar="userAvatarUrl"
      @navigate="handleBottomNav"
      @avatar-tap="handleAvatarTap"
    />

    <!-- 分享面板：微信好友（系统分享卡片）+ 复制直播链接；对齐文档 §7.1 / §7.2 -->
    <view v-if="showSharePanel" class="share-sheet" @tap="closeSharePanel">
      <view class="share-sheet__panel" @tap.stop>
        <text class="share-sheet__title">分享</text>
        <view class="share-sheet__actions">
          <!-- #ifdef MP-WEIXIN -->
          <button class="share-sheet__btn share-sheet__btn--primary" open-type="share" @tap="closeSharePanel">
            微信好友
          </button>
          <!-- #endif -->
          <!-- #ifndef MP-WEIXIN -->
          <view class="share-sheet__btn share-sheet__btn--primary" @tap="handleShareViaSystemHint">
            微信好友
          </view>
          <!-- #endif -->
          <view class="share-sheet__btn" @tap="handleCopyLiveLink">复制直播链接</view>
        </view>
        <view class="share-sheet__cancel" @tap="closeSharePanel">取消</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onUnmounted, watch } from 'vue'
import { onLoad, onShow, onHide, onShareAppMessage } from '@dcloudio/uni-app'
import { useSessionStore } from '@/store/session'
import { useRoomStore } from '@/store/room'
import { useAuthStore } from '@/store/auth'
import { useUserFavoritesStore } from '@/store/userFavorites'
import { useUserSubscriptionsStore } from '@/store/userSubscriptions'
import { useExpertStore } from '@/store/expert'
import { useWatchHistoryStore } from '@/store/watchHistory'
import { storeToRefs } from 'pinia'
import { recordWatchHistory } from '@/api/history'
import { getRoomById, getRoomBrandsTab } from '@/api/room'
import { getRoomTabs } from '@/api/room-tabs'
import { getRoomSessions } from '@/api/session'
import { getExpertDetail, getSessionExperts } from '@/api/expert'
import type { SessionExpertItem } from '@/api/expert'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import MessageItem from '@/components/MessageItem.vue'
import BottomNavBar from '@/components/live/BottomNavBar.vue'
import UserBubbleMenu from '@/components/live/UserBubbleMenu.vue'
import StickyTabPager, { type StickyTabItem } from '@/components/common/StickyTabPager.vue'
import { getRoomMessages, sendRoomMessage, deleteMessage } from '@/api/roomMessage'
import { getRoomMessageErrorMessage, ROOM_MESSAGE_ERROR_CODES } from '@/types/roomMessage'
import type { RoomMessageItem } from '@/types/roomMessage'
import { normalizeRoomMessageItem, normalizeRoomMessageItems } from '@/utils/roomMessageNormalize'
import {
  handleContentSafetyError,
  extractBusinessCode
} from '@/utils/contentSafety'
import { logger } from '@/logs/logger'
import type { RoomTab } from '@/types/room'
import type { RoomBrandItem, RoomBrandsTabData } from '@/types/brands'
import { normalizeImageUrl, resolveMediaUrl, resolveAvatarUrl, resolveBrandLogoUrl, shouldMarkAvatarBroken, shouldMarkBrandLogoBroken } from '@/utils/url'
import { showGlobalLoading, hideGlobalLoading } from '@/utils/request'
import { getSessionTags } from '@/api/tags'
import type { Tag } from '@/types/tags'

function normalizeAnyImageUrl(url: unknown): string {
  if (typeof url !== 'string') return ''
  const trimmed = url.trim()
  if (!trimmed) return ''
  return normalizeImageUrl(resolveMediaUrl(trimmed)) || ''
}
 

// ...existing code...

// Store连接
const sessionStore = useSessionStore()
const roomStore = useRoomStore()
const { currentSession } = storeToRefs(sessionStore)

// 页面状态
const sessionId = ref('')
const roomId = ref('') // 房间ID（用于通过房间查找场次）
const playUrl = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
/** 测播/无场次：房间信息模式（不走红色 ErrorBanner） */
const roomInfoOnly = ref(false)
const pageLoaded = ref(false)
const roomFromHome = ref<any | null>(null)
const currentRoomDetail = ref<any | null>(null)
const sessionExperts = ref<SessionExpertItem[]>([])
const sessionExpertsLoading = ref(false)
const expertInfoLoading = ref(false)
const roomBrands = ref<RoomBrandItem[]>([])
const roomBrandsLoading = ref(false)
const expertInfo = ref<any | null>(null)
const sessionTags = ref<Tag[]>([])

const authStore = useAuthStore()
const userFavoritesStore = useUserFavoritesStore()
const userSubscriptionsStore = useUserSubscriptionsStore()
const expertStore = useExpertStore()
const watchHistoryStore = useWatchHistoryStore()
const { followingMap, followPendingId } = storeToRefs(expertStore)

function resolveWatchHistorySessionType() {
  if (isReplayForActions.value) return 'replay' as const
  if (isScheduled.value) return 'scheduled' as const
  return 'live' as const
}

function buildWatchHistoryPayload(progress: number, watchedAt: string = new Date().toISOString()) {
  const h: any = roomFromHome.value as any
  const r: any = currentRoomDetail.value as any
  const fallbackTitle =
    (typeof h?.title === 'string' && h.title.trim() ? h.title : '') ||
    (typeof r?.title === 'string' && r.title.trim() ? r.title : '')
  const fallbackCover =
    (typeof h?.coverUrl === 'string' && h.coverUrl ? h.coverUrl : '') ||
    (typeof h?.cover_url === 'string' && h.cover_url ? h.cover_url : '') ||
    (typeof r?.cover_url === 'string' && r.cover_url ? r.cover_url : '')

  return {
    session_id: sessionId.value,
    session_title: fallbackTitle || (displayTitle as any)?.value || '未命名直播间',
    room_cover_url: (shareImageUrl as any)?.value || fallbackCover || '',
    progress: Math.max(0, Math.floor(progress || 0)),
    watched_at: watchedAt,
    session_type: resolveWatchHistorySessionType()
  }
}

function buildWatchHistoryContext(reason: string, progress: number, watchedAt: string) {
  return {
    reason,
    sessionId: sessionId.value,
    roomId: roomId.value,
    sessionType: resolveWatchHistorySessionType(),
    isScheduled: isScheduled.value,
    isLive: isLive.value,
    isReplay: isReplayForActions.value,
    playUrlReady: !!playUrl.value,
    loadedSession: !!sessionDetail.value,
    progress: Math.max(0, Math.floor(progress || 0)),
    watchedAt,
    roomTitle: (roomFromHome.value as any)?.title || '',
    sessionTitle: (sessionDetail.value as any)?.title || '',
    roomIdFromSession: (sessionDetail.value as any)?.room_id || ''
  }
}

async function recordWatchHistorySnapshot(reason: string, progress: number, watchedAt?: string) {
  if (!authStore.isAuthenticated || !sessionId.value) return

  const finalWatchedAt = watchedAt || new Date().toISOString()
  const payload = buildWatchHistoryPayload(progress, finalWatchedAt)
  const context = buildWatchHistoryContext(reason, progress, finalWatchedAt)

  logger.info('system', 'watch_history_snapshot_prepare', {
    ...context,
    payloadSummary: {
      session_id: payload.session_id,
      session_type: payload.session_type,
      progress: payload.progress,
      room_cover_url_present: !!payload.room_cover_url,
      session_title: payload.session_title
    }
  })

  try {
    watchHistoryStore.upsertLocalRecord(payload)
    logger.info('system', 'watch_history_local_record_saved', {
      ...context,
      localProgress: payload.progress,
      localSessionType: payload.session_type
    })
  } catch {
    // ignore
  }

  // 预告场次先仅写本地，避免当前后端对 scheduled 上报返回 500 造成噪音
  if (payload.session_type === 'scheduled') {
    logger.info('system', 'watch_history_api_skipped', {
      ...context,
      reason: 'scheduled_session_local_only'
    })
    return
  }

  try {
    logger.info('system', 'watch_history_api_request', {
      ...context,
      api: 'recordWatchHistory',
      request: {
        session_id: payload.session_id,
        progress: payload.progress
      }
    })
    await recordWatchHistory({
      session_id: payload.session_id,
      progress: payload.progress
    })
    logger.info('user', 'watch_history_api_success', {
      ...context,
      sessionType: payload.session_type,
      progress: payload.progress
    })
  } catch (e: any) {
    logger.warn('system', 'watch_history_api_failed', {
      ...context,
      sessionType: payload.session_type,
      progress: payload.progress,
      error: e,
      statusCode: e?.statusCode ?? e?.status ?? null,
      rawMessage: e?.raw?.data?.message ?? e?.message ?? e?.errMsg ?? null
    })
  }
}

const favoriteBusy = ref(false)
const subscriptionBusy = ref(false)
const downloadBusy = ref(false)
const favoriteOverride = ref<boolean | null>(null)
const subscriptionOverride = ref<boolean | null>(null)

function normalizeSessionExpertItems(raw: any): SessionExpertItem[] {
  const data: any = raw && typeof raw === 'object' ? raw : {}
  const arr: any[] = Array.isArray(data) ? data : []
  const itemsArr: any[] = Array.isArray(data.items)
    ? data.items
    : (data.data && typeof data.data === 'object' && Array.isArray(data.data.items) ? data.data.items : [])
  const expertsArr: any[] = Array.isArray(data.experts) ? data.experts : []
  const sessionExpertsArr: any[] = Array.isArray(data.session_experts) ? data.session_experts : []
  const merged = arr.length > 0 ? arr : (itemsArr.length > 0 ? itemsArr : [...expertsArr, ...sessionExpertsArr])

  const out: SessionExpertItem[] = []
  const seen = new Set<string>()

  for (let idx = 0; idx < merged.length; idx += 1) {
    const it: any = merged[idx]
    if (!it || typeof it !== 'object') continue

    const expertObj: any = it.expert || it.expert_info || it.expertInfo || null
    const id = String(it.expert_id || it.expertId || expertObj?.id || it.id || '').trim()
    if (!id || seen.has(id)) continue
    seen.add(id)

    // 《16》P44：显式 is_active=false 丢弃（与品牌挂靠一致）
    const activeFlag =
      it.is_active ?? expertObj?.is_active ?? it.expert_is_active
    if (activeFlag === false) continue

    const name = String(expertObj?.name || it.name || it.expert_name || '').trim()
    const title = expertObj?.title ?? it.title ?? it.expert_title
    const hospital = expertObj?.hospital ?? it.hospital ?? it.expert_hospital
    const avatarUrl = expertObj?.avatar_url ?? it.avatar_url ?? it.avatarUrl ?? it.expert_avatar_url

    const role = (it.role || it.expert_role || '主讲') as any
    const sortOrderRaw = it.sort_order ?? it.sortOrder ?? idx
    const sort_order = Number.isFinite(Number(sortOrderRaw)) ? Number(sortOrderRaw) : idx

    out.push({
      id,
      name: name || id,
      title: typeof title === 'string' ? title : undefined,
      hospital: typeof hospital === 'string' ? hospital : undefined,
      avatar_url: typeof avatarUrl === 'string' ? avatarUrl : undefined,
      role,
      sort_order
    } as SessionExpertItem)
  }

  return out
}

function normalizeRoomBrandItems(raw: any): RoomBrandItem[] {
  const data: any = raw && typeof raw === 'object' ? raw : {}
  const arr: any[] = Array.isArray(data) ? data : []
  const itemsArr: any[] = Array.isArray(data.items)
    ? data.items
    : (data.data && typeof data.data === 'object' && Array.isArray(data.data.items) ? data.data.items : [])
  const roomArr: any[] = Array.isArray(data.room_brands) ? data.room_brands : []
  const topicArr: any[] = Array.isArray(data.topic_brands) ? data.topic_brands : []
  const merged = arr.length > 0 ? arr : (itemsArr.length > 0 ? itemsArr : [...roomArr, ...topicArr])

  const out: RoomBrandItem[] = []
  const seen = new Set<string>()

  for (const it of merged) {
    if (!it || typeof it !== 'object') continue
    const brandObj: any = (it as any).brand || (it as any).brand_info || (it as any).brandInfo || null
    // 16-D5：显式 is_active=false 丢弃；未回传字段时信任后端已过滤
    const activeFlag =
      (it as any).is_active ??
      brandObj?.is_active ??
      (it as any).brand_is_active
    if (activeFlag === false) continue

    const id = String(
      (it as any).brand_id ||
        (it as any).brandId ||
        brandObj?.id ||
        (it as any).id ||
        ''
    ).trim()
    if (!id || seen.has(id)) continue
    seen.add(id)

    const name = String((it as any).name || (it as any).brand_name || (it as any).brandName || brandObj?.name || '').trim()
    const sortOrderRaw = (it as any).sort_order ?? (it as any).sortOrder ?? brandObj?.sort_order ?? 0
    const sort_order = Number.isFinite(Number(sortOrderRaw)) ? Number(sortOrderRaw) : 0

    out.push({
      id,
      name: name || id,
      slug: (it as any).slug ?? brandObj?.slug ?? null,
      logo_url: (it as any).logo_url ?? (it as any).logoUrl ?? brandObj?.logo_url ?? null,
      website_url: (it as any).website_url ?? (it as any).websiteUrl ?? brandObj?.website_url ?? null,
      sort_order,
      is_active: activeFlag !== false
    } as any)
  }

  return out
}

function normalizeRoomBrandsTabData(raw: any): RoomBrandItem[] {
  return normalizeRoomBrandItems(raw)
}

function resolveTopicId(): string {
  const s: any = sessionDetail.value as any
  const r: any = currentRoomDetail.value as any
  const h: any = roomFromHome.value as any
  const candidates = [s?.topic_id, r?.topic_id, h?.topic_id]
  const found = candidates.find(v => typeof v === 'string' && v) as string | undefined
  return found || ''
}

function resolveExpertId(): string {
  const se0 = sessionExperts.value && sessionExperts.value.length > 0 ? sessionExperts.value[0] : null
  const s: any = sessionDetail.value as any
  const r: any = currentRoomDetail.value as any
  const h: any = roomFromHome.value as any

  const candidates: any[] = [
    se0?.id,
    (se0 as any)?.expert_id,
    s?.featured_expert_id,
    s?.featured_expert?.id,
    s?.expert_id,
    Array.isArray(s?.experts) && s.experts[0] ? s.experts[0]?.id : null,

    r?.featured_expert_id,
    r?.featured_expert?.id,
    r?.expert_id,
    r?.expertId,
    r?.expert_info?.id,
    r?.expertInfo?.id,
    r?.host_detail?.id,
    r?.hostDetail?.id,

    h?.expert_id,
    h?.expertId,
    h?.expertInfo?.id
  ]

  const found = candidates.find(v => typeof v === 'string' && v) as string | undefined
  return found || ''
}

const primaryExpert = computed<SessionExpertItem | null>(() => {
  if (!sessionExperts.value.length) return null
  const sorted = [...sessionExperts.value].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
  return sorted[0] || null
})

const sortedSessionExperts = computed<SessionExpertItem[]>(() => {
  if (!sessionExperts.value.length) return []
  return [...sessionExperts.value].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
})

const primaryExpertId = computed(() => {
  const id = primaryExpert.value?.id
  return typeof id === 'string' && id ? id : resolveExpertId()
})

const expertIntroItems = computed<SessionExpertItem[]>(() => {
  if (sortedSessionExperts.value.length) return sortedSessionExperts.value

  const api: any = expertInfo.value
  const id = String(api?.id || primaryExpertId.value || resolveExpertId() || '').trim()
  if (!id) return []

  const name = String(api?.name || displayExpertName.value || id).trim()
  const title = typeof api?.title === 'string' ? api.title : (displayExpertTitle.value ? String(displayExpertTitle.value) : undefined)
  const hospital = typeof api?.hospital === 'string' ? api.hospital : undefined
  const avatar_url = typeof api?.avatar_url === 'string'
    ? api.avatar_url
    : (displayExpertAvatar.value ? String(displayExpertAvatar.value) : undefined)

  return [
    {
      id,
      name: name || id,
      title: title || undefined,
      hospital,
      avatar_url: avatar_url || undefined,
      role: (api?.role || '主讲') as any,
      sort_order: 0
    } as SessionExpertItem
  ]
})

async function loadSessionExperts() {
  if (!sessionId.value) {
    sessionExperts.value = []
    sessionExpertsLoading.value = false
    return
  }
  try {
    sessionExpertsLoading.value = true
    const resp = await getSessionExperts(sessionId.value)
    const raw: any = (resp as any)?.data ?? resp
    sessionExperts.value = normalizeSessionExpertItems(raw)
    try {
      console.log('✅ [loadSessionExperts] loaded', {
        sessionId: sessionId.value,
        count: sessionExperts.value.length,
        sampleKeys: sessionExperts.value[0] ? Object.keys(sessionExperts.value[0] as any) : []
      })
    } catch {}
    // 同步关注状态，供专家 Tab 列表右侧「关注」展示
    if (authStore.isAuthenticated && sessionExperts.value.length) {
      const probeId = String(sessionExperts.value[0]?.id || '').trim()
      if (probeId) {
        try {
          await expertStore.checkFollow(probeId)
        } catch {
          // ignore
        }
      }
    }
  } catch (e) {
    sessionExperts.value = []
    logger.warn('system', 'load_session_experts_failed', {
      sessionId: sessionId.value,
      statusCode: (e as any)?.statusCode ?? (e as any)?.status ?? null,
      message: (e as any)?.message || (e as any)?.errMsg || null
    })
    console.warn('⚠️ 获取场次专家列表失败', e)
  } finally {
    sessionExpertsLoading.value = false
  }
}

async function loadRoomBrands() {
  const currentRoomId = roomId.value || sessionDetail.value?.room_id
  if (!currentRoomId) {
    roomBrands.value = []
    return
  }

  try {
    roomBrandsLoading.value = true
    const topicId = resolveTopicId()
    const params = topicId ? ({ include_topic_brands: true, topic_id: topicId } as any) : undefined
    const resp = await getRoomBrandsTab(currentRoomId, params)
    const raw: RoomBrandsTabData | any = (resp as any)?.data ?? resp
    roomBrands.value = normalizeRoomBrandsTabData(raw)
    try {
      console.log('✅ [loadRoomBrands] loaded', {
        roomId: currentRoomId,
        count: roomBrands.value.length,
        sampleKeys: roomBrands.value[0] ? Object.keys(roomBrands.value[0] as any) : []
      })
    } catch {}
  } catch (e) {
    // 品牌信息获取失败不阻断页面
    roomBrands.value = []
    logger.warn('system', 'load_room_brands_failed', {
      roomId: currentRoomId,
      sessionId: sessionId.value || null,
      statusCode: (e as any)?.statusCode ?? (e as any)?.status ?? null,
      message: (e as any)?.message || (e as any)?.errMsg || null
    })
    console.warn('⚠️ 获取房间品牌失败', e)
  } finally {
    roomBrandsLoading.value = false
  }
}

async function loadSessionTags() {
  if (!sessionId.value) {
    sessionTags.value = []
    return
  }
  try {
    const resp = await getSessionTags(sessionId.value)
    const raw: any = (resp as any)?.data ?? resp
    const arr: any[] = Array.isArray(raw) ? raw : (Array.isArray(raw?.items) ? raw.items : [])
    sessionTags.value = arr.filter((t: any) => t && typeof t === 'object') as Tag[]
  } catch {
    sessionTags.value = []
  }
}

function openBrandDetail(brandId: string) {
  const id = String(brandId || '')
  if (!id) return
  uni.navigateTo({ url: `/pages/brand/BrandDetail?id=${encodeURIComponent(id)}` })
}

function openExpertDetailById(expertId: string) {
  const id = String(expertId || '').trim()
  if (!id) return
  const listed = sessionExperts.value.find((ex) => String(ex.id) === id)
  // 列表里已过滤下架专家；若仍点到无效 id，友好提示
  if (!listed && sessionExperts.value.length > 0) {
    uni.showToast({ title: '专家已下架', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/expert/ExpertDetail?id=${encodeURIComponent(id)}` })
}

const currentExpertIdForActions = computed(() => String(expertInfo.value?.id || primaryExpertId.value || resolveExpertId() || ''))

const isExpertFollowed = computed(() => {
  const id = currentExpertIdForActions.value
  if (!id) return false
  return !!followingMap.value[id]
})

const isExpertFollowPending = computed(() => {
  const id = currentExpertIdForActions.value
  if (!id) return false
  return followPendingId.value === id
})

// 用户行为接口要求 room_id，优先使用场次详情中的标准 room_id，避免路由 roomId 非 UUID 触发 422
const currentRoomIdForActions = computed(() => sessionDetail.value?.room_id || roomId.value || '')

const isFavorited = computed(() => {
  const rid = String(currentRoomIdForActions.value || '').trim()
  if (!rid) return false
  if (favoriteOverride.value !== null) return favoriteOverride.value

  const cached = userFavoritesStore.favoriteStatus[rid]
  if (typeof cached === 'boolean') return cached

  // 兜底：未查询到状态时，尽量用已加载的收藏列表判断（可能因分页不完整而不准确）
  return userFavoritesStore.items.some(i => i.room_id === rid)
})

const isSubscribed = computed(() => {
  const rid = currentRoomIdForActions.value
  if (!rid) return false
  if (subscriptionOverride.value !== null) return subscriptionOverride.value
  if (userSubscriptionsStore.items.some(i => i.room_id === rid)) return true
  const cached = userSubscriptionsStore.subscriptionStatus?.[rid]
  if (typeof cached === 'boolean') return cached
  return false
})


function redirectToLogin() {
  const redirectUrl = roomId.value
    ? `/pages/live/LiveView?roomId=${encodeURIComponent(roomId.value)}`
    : sessionId.value
      ? `/pages/live/LiveView?sessionId=${encodeURIComponent(sessionId.value)}`
      : '/pages/live/LiveView'

  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

function ensureAuthed(): boolean {
  if (authStore.isAuthenticated) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  setTimeout(() => redirectToLogin(), 250)
  return false
}

async function toggleExpertFollow(expertId?: string) {
  const id = String((typeof expertId === 'string' ? expertId : '') || currentExpertIdForActions.value || '').trim()
  if (!id) return
  if (!ensureAuthed()) return
  if (followPendingId.value === id) return

  const wasFollowing = !!followingMap.value[id]
  logger.info('user', wasFollowing ? 'unfollow:start' : 'follow:start', { expertId: id })

  try {
    await expertStore.toggleFollow(id)
    uni.showToast({ title: wasFollowing ? '已取消关注' : '已关注', icon: wasFollowing ? 'none' : 'success' })
    logger.info('user', wasFollowing ? 'unfollow:success' : 'follow:success', { expertId: id })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
    logger.warn('user', 'follow:failed', { expertId: id, error: String(e?.message || e) })
  }
}

/** 列表关注：避免模板里直接传参被编译成事件缓存键串到其它绑定 */
function onExpertListFollow(expertId: string) {
  void toggleExpertFollow(String(expertId || '').trim())
}

async function ensureUserListsLoaded() {
  if (!authStore.isAuthenticated) return
  const rid = currentRoomIdForActions.value
  if (!rid) return

  try {
    if (!userFavoritesStore.loading && userFavoritesStore.items.length === 0 && userFavoritesStore.total === 0) {
      await userFavoritesStore.fetch({ page: 1, size: 20 }, false)
    }
  } catch {
    // ignore
  }

  // 收藏状态以 check 接口为准（避免仅靠分页列表导致状态错误）
  void userFavoritesStore.checkStatus(rid)

  try {
    if (!userSubscriptionsStore.loading && userSubscriptionsStore.items.length === 0 && userSubscriptionsStore.total === 0) {
      await userSubscriptionsStore.fetch({ page: 1, size: 20 }, false)
    }
  } catch {
    // ignore
  }
}


// 功能性 tabs：改为使用房间详情接口返回的 tabs（GET /api/v1/rooms/{room_id}）
// V1.1：使用 tab_key 匹配（后端 DDL 已支持 tab_key 字段）
const ROOM_INTRO_TAB_KEY = 'intro'
const EXPERT_INTRO_TAB_KEY = 'expert_intro'
const BRAND_INTRO_TAB_KEY = 'brand_intro'
const MESSAGE_TAB_KEY = 'message'

// ---- 留言区状态 ----
const messages = ref<RoomMessageItem[]>([])
const messagesLoading = ref(false)
const messagesLoadingMore = ref(false)
const messageSending = ref(false)
const messagesTotal = ref(0)
const messagesPage = ref(1)
const messagesPageSize = ref(20)
const messagesHasMore = ref(true)
const messageInputContent = ref('')
/** 拉列表请求序号：丢弃过期响应，避免快切 Tab / 换房串数据 */
let messagesFetchSeq = 0
const isLoggedIn = computed(() => !!authStore.isAuthenticated)
const isAdmin = computed(() => authStore.isAdmin)

// ---- 底部导航 & 用户气泡菜单 ----
const showUserBubble = ref(false)

const userAvatarUrl = computed(() =>
  isLoggedIn.value ? authStore.userInfo?.avatar_url || '' : ''
)

const primaryExpertAvatarBroken = ref(false)
const brokenExpertAvatarIds = ref<Record<string, true>>({})
const brokenBrandLogoIds = ref<Record<string, true>>({})

function pickExpertAvatarRaw(): string | null {
  const urlFromApi = expertInfo.value?.avatar_url
  if (typeof urlFromApi === 'string' && urlFromApi) return urlFromApi
  const urlFromSessionExperts = primaryExpert.value?.avatar_url
  if (typeof urlFromSessionExperts === 'string' && urlFromSessionExperts) return urlFromSessionExperts
  const url = (sessionDetail.value as any)?.featured_expert?.avatar_url
  if (typeof url === 'string' && url) return url
  const fallback = roomFromHome.value?.expertInfo?.avatar || roomFromHome.value?.expertInfo?.avatar_url
  if (typeof fallback === 'string' && fallback) return fallback
  return null
}

function onPrimaryExpertAvatarError() {
  const raw = pickExpertAvatarRaw()
  if (!shouldMarkAvatarBroken(raw, primaryExpertAvatarBroken.value)) return
  primaryExpertAvatarBroken.value = true
}

function expertListAvatarSrc(ex: { id: string; avatar_url?: string | null }) {
  return resolveAvatarUrl(ex.avatar_url, !!brokenExpertAvatarIds.value[ex.id])
}

function onExpertListAvatarError(expertId: string, raw?: string | null) {
  const id = String(expertId || '').trim()
  if (!id || brokenExpertAvatarIds.value[id]) return
  if (!shouldMarkAvatarBroken(raw, !!brokenExpertAvatarIds.value[id])) return
  brokenExpertAvatarIds.value = { ...brokenExpertAvatarIds.value, [id]: true }
}

function brandLogoSrc(b: { id: string; logo_url?: string | null }) {
  return resolveBrandLogoUrl(b.logo_url, !!brokenBrandLogoIds.value[b.id])
}

function onBrandLogoError(brandId: string, raw?: string | null) {
  const id = String(brandId || '').trim()
  if (!id || brokenBrandLogoIds.value[id]) return
  if (!shouldMarkBrandLogoBroken(raw, !!brokenBrandLogoIds.value[id])) return
  brokenBrandLogoIds.value = { ...brokenBrandLogoIds.value, [id]: true }
}

function handleBottomNav(tab: string) {
  switch (tab) {
    case 'home':
      uni.switchTab({ url: '/pages/home/Home' })
      break
    case 'search':
      uni.navigateTo({ url: '/subpackages/search/index' })
      break
    case 'messages':
      if (!isLoggedIn.value) {
        redirectToLogin()
        return
      }
      uni.navigateTo({ url: '/pages/profile/Notifications' })
      break
    case 'profile':
      uni.switchTab({ url: '/pages/profile/Profile' })
      break
  }
}

function handleAvatarTap() {
  showUserBubble.value = true
}

function handleBubbleClose() {
  showUserBubble.value = false
}

function handleBubbleNavigate(path: string) {
  showUserBubble.value = false
  if (path === '/pages/auth/OneTapLogin') {
    redirectToLogin()
    return
  }
  // tabBar 页面用 switchTab，其他用 navigateTo
  const tabBarPages = ['/pages/home/Home', '/pages/brand/BrandZone', '/pages/expert/ExpertList', '/pages/profile/Profile']
  if (tabBarPages.includes(path)) {
    uni.switchTab({ url: path })
  } else {
    uni.navigateTo({ url: path })
  }
}

async function handleBubbleLogout() {
  try {
    await authStore.logout()
    showUserBubble.value = false
    uni.showToast({ title: '已退出登录', icon: 'success' })
  } catch {
    // ignore
  }
}

// 展示层 ASC：旧上新低（聊天式），API 仍 DESC 分页
const messagesSorted = computed(() => {
  return messages.value
    .filter((m): m is RoomMessageItem => !!m && !!m.id)
    .slice()
    .sort((a, b) =>
      new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
    )
})

const bodyScrollIntoView = ref('')
let scrollToLatestTimer: ReturnType<typeof setTimeout> | null = null

function scrollToLatestMessage() {
  const list = messagesSorted.value
  const last = list[list.length - 1]
  if (!last) return
  // 等 flow pane 布局完成后再滚，避免切 Tab 瞬间高度未稳导致「下面一大片白」
  if (scrollToLatestTimer) clearTimeout(scrollToLatestTimer)
  bodyScrollIntoView.value = ''
  scrollToLatestTimer = setTimeout(() => {
    scrollToLatestTimer = null
    nextTick(() => {
      bodyScrollIntoView.value = `msg-${last.id}`
    })
  }, 48)
}

const hasOwnMessages = computed(() => {
  const uid = authStore.userInfo?.user_id
  if (!uid) return false
  return messages.value.some(m => String(m.user_id) === String(uid))
})

function messageAuthFallback() {
  // 列表归一化只传 user_id 判定「我的留言」；禁止用当前登录昵称/头像盖住服务端快照或 D3 占位
  return {
    user_id: authStore.userInfo?.user_id
  }
}

/** 刚发送成功：响应缺快照时可用本人资料兜底（作者此时未注销） */
function messageSendAuthFallback() {
  return {
    user_id: authStore.userInfo?.user_id,
    nickname: authStore.userInfo?.nickname,
    avatar_url: authStore.userInfo?.avatar_url
  }
}

function resetMessagesState() {
  messages.value = []
  messagesTotal.value = 0
  messagesPage.value = 1
  messagesHasMore.value = true
}

async function fetchMessages(append = false, opts?: { silent?: boolean }) {
  if (!roomId.value) return
  const seq = ++messagesFetchSeq
  const requestRoomId = roomId.value
  const silent = !!opts?.silent && !append && messages.value.length > 0
  if (append) messagesLoadingMore.value = true
  else if (!silent) messagesLoading.value = true

  try {
    const res = await getRoomMessages(requestRoomId, {
      page: messagesPage.value,
      size: messagesPageSize.value
    })
    // 过期请求或已换房：丢弃，避免盖住新房间数据
    if (seq !== messagesFetchSeq || roomId.value !== requestRoomId) return
    // request 工具会将响应包装为 { code, data, message }，需解包取 data 层
    const data: any = (res as any)?.data ?? res
    const fetchedItems = normalizeRoomMessageItems(
      Array.isArray(data?.items) ? data.items : [],
      messageAuthFallback()
    )
    if (append) {
      const exist = new Set(messages.value.map((m) => String(m.id)))
      messages.value.push(...fetchedItems.filter((m) => !exist.has(String(m.id))))
    } else {
      // 保留发送中的乐观气泡，避免历史拉回时把刚发的盖掉
      const pendingLocals = messages.value.filter((m) => String(m.id || '').startsWith('local_'))
      const serverIds = new Set(fetchedItems.map((m) => String(m.id)))
      messages.value = [
        ...fetchedItems,
        ...pendingLocals.filter((m) => !serverIds.has(String(m.id)))
      ]
    }
    messagesTotal.value = data?.total ?? messages.value.length
    messagesHasMore.value = fetchedItems.length > 0 && messages.value.filter((m) => !String(m.id).startsWith('local_')).length < messagesTotal.value
  } catch (e) {
    if (seq !== messagesFetchSeq || roomId.value !== requestRoomId) return
    const err = e as { code?: number; message?: string }
    uni.showToast({
      title: getRoomMessageErrorMessage(err?.code, err?.message) || '加载讨论失败',
      icon: 'none'
    })
  } finally {
    if (seq === messagesFetchSeq) {
      messagesLoading.value = false
      messagesLoadingMore.value = false
    }
    if (seq === messagesFetchSeq && !append && messages.value.length) {
      nextTick(() => scrollToLatestMessage())
    }
  }
}

function handleLoadMoreMessages() {
  if (messagesLoadingMore.value || !messagesHasMore.value) return
  messagesPage.value++
  fetchMessages(true)
}

function buildMessageTab(roomIdStr: string): RoomFunctionalTab {
  return {
    id: 'tab_message_board',
    room_id: roomIdStr,
    tab_key: MESSAGE_TAB_KEY,
    title: '讨论',
    content_type: 'text' as const,
    text_content: null,
    image_url: null,
    sort_order: Number.MAX_SAFE_INTEGER,
    is_active: true,
    created_at: '',
    updated_at: ''
  }
}

function injectMessageTab(tabs: RoomFunctionalTab[], roomIdStr: string): RoomFunctionalTab[] {
  if (tabs.some(t => t.tab_key === MESSAGE_TAB_KEY)) return tabs
  return [...tabs, buildMessageTab(roomIdStr)]
}

async function handleSendMessage() {
  if (!ensureAuthed()) return
  const content = messageInputContent.value.trim()
  if (!content) {
    uni.showToast({ title: '请输入讨论内容', icon: 'none' })
    return
  }
  if (messageSending.value || !roomId.value) return

  // 直播评论（抖音/B 站同思路）：先清输入、本地上屏，再后台落库；禁止等接口再显示
  const clientId = `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  const auth = messageSendAuthFallback()
  const optimistic: RoomMessageItem = {
    id: clientId,
    room_id: roomId.value,
    user_id: String(auth.user_id || ''),
    content,
    created_at: new Date().toISOString(),
    user_display_name: auth.nickname || null,
    user_role: null,
    user: {
      nickname: auth.nickname || null,
      avatar_url: auth.avatar_url || null
    }
  }

  messageSending.value = true
  messageInputContent.value = ''
  messages.value.push(optimistic)
  messagesTotal.value++
  nextTick(() => scrollToLatestMessage())

  try {
    const res = await sendRoomMessage(roomId.value, { content })
    let serverMsg = normalizeRoomMessageItem(
      (res as any)?.data ?? res,
      messageSendAuthFallback()
    )
    if (!String(serverMsg.created_at || '').trim()) {
      serverMsg = { ...serverMsg, created_at: optimistic.created_at }
    }

    const localIdx = messages.value.findIndex((m) => String(m.id) === clientId)
    if (serverMsg.id) {
      if (localIdx >= 0) {
        messages.value.splice(localIdx, 1, serverMsg)
      } else if (!messages.value.some((m) => String(m.id) === String(serverMsg.id))) {
        messages.value.push(serverMsg)
        messagesTotal.value++
      }
    } else {
      // 响应异常：去掉临时气泡，静默重拉
      if (localIdx >= 0) {
        messages.value.splice(localIdx, 1)
        messagesTotal.value = Math.max(0, messagesTotal.value - 1)
      }
      messagesPage.value = 1
      await fetchMessages(false, { silent: true })
    }
    nextTick(() => scrollToLatestMessage())
  } catch (e) {
    messages.value = messages.value.filter((m) => String(m.id) !== clientId)
    messagesTotal.value = Math.max(0, messagesTotal.value - 1)
    messageInputContent.value = content
    const err = e as { code?: number; message?: string }
    // 2004/2005：统一人话 Toast，保留输入框
    if (handleContentSafetyError(e)) return
    if (extractBusinessCode(e) === ROOM_MESSAGE_ERROR_CODES.UNAUTHORIZED) {
      redirectToLogin()
      return
    }
    uni.showToast({
      title: getRoomMessageErrorMessage(err?.code, err?.message),
      icon: 'none'
    })
  } finally {
    messageSending.value = false
  }
}

async function handleDeleteMessage(message: RoomMessageItem) {
  if (!roomId.value) return
  if (!ensureAuthed()) return
  uni.showModal({
    title: '确认删除',
    content: '确定删除这条讨论吗？',
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteMessage(roomId.value, message.id)
        messages.value = messages.value.filter(m => m.id !== message.id)
        messagesTotal.value = Math.max(0, messagesTotal.value - 1)
        uni.showToast({ title: '删除成功', icon: 'success' })
      } catch (e) {
        const err = e as { code?: number; message?: string }
        uni.showToast({
          title: getRoomMessageErrorMessage(err?.code, err?.message),
          icon: 'none'
        })
      }
    }
  })
}

type RoomFunctionalTab = RoomTab & { is_active?: boolean }

const roomFunctionalTabs = ref<RoomFunctionalTab[]>([])
const currentTabId = ref<string>('')  // 用 id 做唯一标识，允许多个相同 tab_key 的 Tab
const functionalTabsLoading = ref(false)
const functionalTabsError = ref<string | null>(null)

const enableFunctionalTabs = computed(() => roomFunctionalTabs.value.length > 0)

// 用 id 查找当前 Tab
const currentFunctionalTab = computed<RoomFunctionalTab | null>(() => {
  if (!currentTabId.value) return null
  return roomFunctionalTabs.value.find(t => String(t.id) === String(currentTabId.value)) || null
})

function functionalTabOf(id: string | number): RoomFunctionalTab | null {
  return roomFunctionalTabs.value.find((t) => String(t.id) === String(id)) || null
}

const functionalPagerTabs = computed<StickyTabItem[]>(() =>
  roomFunctionalTabs.value.map((t) => ({
    id: String(t.id),
    label: String(t.title || 'Tab')
  }))
)

const functionalSwiperIndex = computed(() => {
  const idx = roomFunctionalTabs.value.findIndex(
    (t) => String(t.id) === String(currentTabId.value)
  )
  return idx >= 0 ? idx : 0
})

function handleFunctionalPagerChange(index: number) {
  const tab = roomFunctionalTabs.value[index]
  if (tab) handleTabChange(String(tab.id))
}

const isMessageTabActive = computed(
  () => currentFunctionalTab.value?.tab_key === MESSAGE_TAB_KEY
)

/**
 * 讨论列表加载触发（须同时满足）：
 * 1) 讨论 Tab 激活  2) roomId 已就绪
 * 仅监听 isMessageTabActive 边沿不够：进 Tab 时可能尚无 roomId，
 * 或 onLoad 稍后覆盖 roomId 会清空列表却不再拉数。
 */
function pullMessagesWhenDiscussionReady(opts?: { silent?: boolean }) {
  if (!isMessageTabActive.value || !roomId.value) return
  messagesPage.value = 1
  fetchMessages(false, opts)
}

watch(isMessageTabActive, (active) => {
  if (!active) return
  if (!roomId.value) return
  pullMessagesWhenDiscussionReady({ silent: messages.value.length > 0 })
}, { immediate: true })

watch(roomId, (id, prev) => {
  if (!id) {
    resetMessagesState()
    return
  }
  if (id === prev) return
  resetMessagesState()
  // 已在讨论 Tab：换房 / 路由 roomId→详情 room_id 后必须补拉
  pullMessagesWhenDiscussionReady()
})

async function loadRoomFunctionalTabs() {
  const currentRoomId = roomId.value || sessionDetail.value?.room_id
  if (!currentRoomId) {
    roomFunctionalTabs.value = []
    currentTabId.value = ''
    return
  }

  try {
    functionalTabsLoading.value = true
    functionalTabsError.value = null
    // 优先用 roomStore 当前详情（若已加载且匹配 roomId），避免重复请求
    const cached = roomStore.currentRoom && (roomStore.currentRoom as any).id === currentRoomId ? roomStore.currentRoom : null
    const roomData = cached ? (cached as any) : ((await getRoomById(currentRoomId)) as any)
    const room = roomData?.data ?? roomData
    currentRoomDetail.value = room

    // 输出房间描述内容（便于排查后端返回字段）
    try {
      const rawDesc =
        typeof (room as any)?.description === 'string'
          ? (room as any).description
          : (room as any)?.data?.description
      const desc = typeof rawDesc === 'string' ? rawDesc : (rawDesc != null ? JSON.stringify(rawDesc) : '')
      logger.info('system', '房间描述', { roomId: currentRoomId, description: desc })
      console.log('📝 [room.description]', {
        roomId: currentRoomId,
        type: typeof rawDesc,
        length: desc ? desc.length : 0,
        content: desc
      })
    } catch {}

    // 优先使用房间详情中的 tabs（普通用户契约），若无再回退公开接口
    let effectiveTabs: RoomFunctionalTab[] = []
    const roomTabsFromDetail: any[] = Array.isArray((room as any)?.tabs) ? (room as any).tabs : []

    console.log('🔎 [room.tabs] from detail', {
      exist: roomTabsFromDetail.length > 0,
      count: roomTabsFromDetail.length,
      sampleKeys: roomTabsFromDetail[0] ? Object.keys(roomTabsFromDetail[0]) : []
    })
    if (roomTabsFromDetail.length > 0) {
      // V1.1：后端 Tab 字段为 tab_key/title/content_type/text_content/image_url
      effectiveTabs = roomTabsFromDetail.map((t: any) => {
        const rawKey = t.tab_key ?? t.tabKey ?? ''
        return {
        id: String(t.id),
        room_id: t.room_id || '',
        tab_key: rawKey,
        title: t.title ?? t.name ?? '',
        content_type: t.content_type ?? t.contentType ?? 'text',
        text_content: (t.text_content ?? t.textContent ?? t.content ?? t.text ?? t.body ?? null) as string | null,
        image_url: normalizeAnyImageUrl(t.image_url ?? t.imageUrl ?? t.img_url ?? null),
        sort_order: t.sort_order ?? t.sortOrder ?? 0,
        is_active: t.is_active !== false,
        created_at: t.created_at || '',
        updated_at: t.updated_at || ''
      }})
      console.log('✅ [room.tabs] mapped', { count: effectiveTabs.length })
    } else {
      // room.tabs 为空时，使用公开Tab接口回退（后端已修正，所有用户均可访问）
      try {
        console.log('📡 [public.tabs] request (fallback)', { roomId: currentRoomId })
        const publicResp = await getRoomTabs(currentRoomId)
        console.log('🧾 [public.tabs] raw response', publicResp)
        const raw = (publicResp as any)?.data ?? publicResp

        // 兼容不同返回结构：直接数组 / 分页对象(items) / 常见命名(list/results/records/rows) / 嵌套字段(tabs/data) / 单对象
        let publicTabsArr: any[] = []
        if (Array.isArray(raw)) {
          publicTabsArr = raw
        } else if (raw && typeof raw === 'object') {
          if (Array.isArray((raw as any).items)) {
            publicTabsArr = (raw as any).items
          } else if (Array.isArray((raw as any).tabs)) {
            publicTabsArr = (raw as any).tabs
          } else if (Array.isArray((raw as any).data)) {
            publicTabsArr = (raw as any).data
          } else if (Array.isArray((raw as any).list)) {
            publicTabsArr = (raw as any).list
          } else if (Array.isArray((raw as any).results)) {
            publicTabsArr = (raw as any).results
          } else if (Array.isArray((raw as any).records)) {
            publicTabsArr = (raw as any).records
          } else if (Array.isArray((raw as any).rows)) {
            publicTabsArr = (raw as any).rows
          } else if ((raw as any).id && (raw as any).title) {
            publicTabsArr = [raw]
          } else {
            // 兼容更深层嵌套：如 { data: { items: [...] , total: N } }
            const nested = (raw as any).data
            if (nested && typeof nested === 'object') {
              if (Array.isArray(nested.items)) {
                publicTabsArr = nested.items
              } else if (Array.isArray(nested.tabs)) {
                publicTabsArr = nested.tabs
              } else if (Array.isArray(nested.data)) {
                publicTabsArr = nested.data
              } else if (Array.isArray(nested.list)) {
                publicTabsArr = nested.list
              } else if (Array.isArray(nested.results)) {
                publicTabsArr = nested.results
              } else if (Array.isArray(nested.records)) {
                publicTabsArr = nested.records
              } else if (Array.isArray(nested.rows)) {
                publicTabsArr = nested.rows
              }
            }

            // 兜底：扫描对象（及 data 子对象）中所有数组值，挑出疑似 tab 列表（含 tab_key/id/title）
            if (!Array.isArray(publicTabsArr) || publicTabsArr.length === 0) {
              try {
                const scanArrays = (obj: any): any[] => {
                  if (!obj || typeof obj !== 'object') return []
                  return Object.values(obj).filter(v => Array.isArray(v)) as any[]
                }
                const arrays = [
                  ...scanArrays(raw),
                  ...scanArrays((raw as any).data)
                ]
                const pick = arrays.find(arr => arr.length > 0 && typeof arr[0] === 'object' && (
                  'title' in arr[0] || 'id' in arr[0]
                ))
                if (Array.isArray(pick)) publicTabsArr = pick
              } catch {}
            }
          }
        }

        // 若仍未提取到数组，尝试把”对象字典”形式转为数组（value 为单个 tab 对象）
        if ((!Array.isArray(publicTabsArr) || publicTabsArr.length === 0) && raw && typeof raw === 'object') {
          try {
            const values = Object.values(raw)
            const looksLikeTabObj = (o: any) => o && typeof o === 'object' && (
              'title' in o || 'id' in o
            )
            const objItems = values.filter(v => looksLikeTabObj(v))
            if (objItems.length > 0) {
              publicTabsArr = objItems as any[]
            }
          } catch {}
          // 同样尝试从 raw.data 的对象字典中提取
          if ((!Array.isArray(publicTabsArr) || publicTabsArr.length === 0) && (raw as any).data && typeof (raw as any).data === 'object') {
            try {
              const values = Object.values((raw as any).data)
              const looksLikeTabObj = (o: any) => o && typeof o === 'object' && (
                'title' in o || 'id' in o
              )
              const objItems = values.filter(v => looksLikeTabObj(v))
              if (objItems.length > 0) {
                publicTabsArr = objItems as any[]
              }
            } catch {}
          }
        }

        if (Array.isArray(publicTabsArr)) {
          console.log('🛠️ [public.tabs] loaded', {
            count: publicTabsArr.length,
            sampleKeys: publicTabsArr[0] ? Object.keys(publicTabsArr[0]) : [],
            rootKeys: raw && typeof raw === 'object' ? Object.keys(raw) : []
          })
          // V1.1：后端 Tab 字段为 tab_key/title/content_type/text_content/image_url
          effectiveTabs = publicTabsArr.map((t: any) => {
            const rawKey = t.tab_key ?? t.tabKey ?? ''
            return {
            id: String(t.id),
            room_id: t.room_id || '',
            tab_key: rawKey,
            title: t.title ?? t.name ?? '',
            content_type: t.content_type ?? t.contentType ?? 'text',
            text_content: (t.text_content ?? t.textContent ?? t.content ?? t.text ?? t.body ?? null) as string | null,
            image_url: normalizeAnyImageUrl(t.image_url ?? t.imageUrl ?? t.img_url ?? null),
            sort_order: t.sort_order ?? t.sortOrder ?? 0,
            is_active: t.is_active !== false,
            created_at: t.created_at || '',
            updated_at: t.updated_at || ''
          }})
          functionalTabsError.value = null
        } else {
          console.warn('⚠️ [public.tabs] not an array', {
            type: typeof raw,
            rootKeys: raw && typeof raw === 'object' ? Object.keys(raw) : [],
            value: raw
          })
          functionalTabsError.value = 'Tab接口返回结构异常'
        }
      } catch (e) {
        console.warn('⚠️ 公开Tab接口请求失败', e)
        functionalTabsError.value = 'Tab接口请求失败'
      }
    }

    if (effectiveTabs && effectiveTabs.length > 0) {
      functionalTabsError.value = null
    }
    const baseTabs = (effectiveTabs || [])
      .filter(t => (t as any).is_active !== false)
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))


    // 去重（使用 id 去重，允许多个同类 tab_key 的 Tab 同时显示），并保持简介置顶
    const seenId = new Set<string>()
    roomFunctionalTabs.value = baseTabs
      .filter(t => {
        const id = String(t?.id || '')
        if (!id) return false
        if (seenId.has(id)) return false
        seenId.add(id)
        return true
      })
      .sort((a, b) => {
        const ak = String(a?.tab_key || '')
        const bk = String(b?.tab_key || '')
        if (ak === ROOM_INTRO_TAB_KEY) return -1
        if (bk === ROOM_INTRO_TAB_KEY) return 1
        return (Number((a as any)?.sort_order ?? 0) - Number((b as any)?.sort_order ?? 0))
      })

    // 只要最终能渲染出 Tab（包括前端注入的专家/品牌 Tab），就不应因为公开 tabs 接口失败而阻断 UI
    if (roomFunctionalTabs.value.length > 0) {
      functionalTabsError.value = null
    }

    // 留言 Tab 始终注入到末尾，与其他功能性 Tab 统一管理
    roomFunctionalTabs.value = injectMessageTab(roomFunctionalTabs.value, currentRoomId)
    console.log('🧩 [tabs] ready to render', {
      count: roomFunctionalTabs.value.length,
      titles: roomFunctionalTabs.value.map((t) => t.title),
      enable: roomFunctionalTabs.value.length > 0
    })

    if (!roomFunctionalTabs.value.length) {
      currentTabId.value = ''
      return
    }

    // 如果当前 tab 不存在，则默认选中第一个
    const stillExists = roomFunctionalTabs.value.some(t => String(t.id) === String(currentTabId.value))
    if (!currentTabId.value || !stillExists) {
      const introTab = roomFunctionalTabs.value.find(t => t.tab_key === ROOM_INTRO_TAB_KEY)
      currentTabId.value = String(introTab?.id || roomFunctionalTabs.value[0].id)
    }
  } catch (err) {
    logger.warn('system', '加载功能性Tab失败', { error: err })
    // Tab 加载失败时仍保留留言 Tab，确保用户可操作留言功能
    roomFunctionalTabs.value = injectMessageTab([], currentRoomId)
    currentTabId.value = 'tab_message_board'
    functionalTabsError.value = null
  } finally {
    functionalTabsLoading.value = false
  }
}

function handleTabChange(tabId: string) {
  const normalizedId = String(tabId)
  const tabChanged = String(currentTabId.value) !== normalizedId
  currentTabId.value = normalizedId
  if (!tabChanged) return
  const currentTab = roomFunctionalTabs.value.find(t => String(t.id) === normalizedId) || null
  const tabKey = currentTab?.tab_key || ''

  // 切到留言 Tab：历史列表由 isMessageTabActive + roomId 联合 watch 拉取
  if (tabKey === MESSAGE_TAB_KEY) {
    if (/^e\d+_/.test(messageInputContent.value)) messageInputContent.value = ''
  }

  const roomIntroText = currentTab?.tab_key === ROOM_INTRO_TAB_KEY ? String(currentTab?.text_content || '').trim() : ''
  const roomIntroImage = currentTab?.tab_key === ROOM_INTRO_TAB_KEY ? String(currentTab?.image_url || '').trim() : ''

  const expertIntroLogItems = tabKey === EXPERT_INTRO_TAB_KEY
    ? expertIntroItems.value.map((item) => ({
        id: item.id,
        name: item.name,
        role: item.role || '',
        title: item.title || '',
        hospital: item.hospital || '',
        avatar_url: item.avatar_url || ''
      }))
    : []

  const brandIntroLogItems = tabKey === BRAND_INTRO_TAB_KEY
    ? roomBrands.value.map((item) => ({
        id: item.id,
        name: item.name,
        slug: item.slug || '',
        website_url: item.website_url || '',
        logo_url: item.logo_url || ''
      }))
    : []

  logger.info('user', '切换功能性Tab', {
    tabId,
    tabKey,
    tabTitle: currentTab?.title || '',
    roomId: roomId.value,
    sessionId: sessionId.value,
    tabDetail: currentTab
      ? {
          id: currentTab.id,
          title: currentTab.title,
          sort_order: currentTab.sort_order,
          is_active: currentTab.is_active !== false
        }
      : null,
    content: tabKey === ROOM_INTRO_TAB_KEY
      ? {
          text: roomIntroText,
          textLength: roomIntroText.length,
          imageUrl: roomIntroImage,
          imageCount: roomIntroImage ? 1 : 0
        }
      : tabKey === EXPERT_INTRO_TAB_KEY
        ? {
            count: expertIntroLogItems.length,
            items: expertIntroLogItems
          }
        : tabKey === BRAND_INTRO_TAB_KEY
          ? {
              count: brandIntroLogItems.length,
              items: brandIntroLogItems
            }
          : {
              text: currentTab?.text_content || '',
              textLength: String(currentTab?.text_content || '').length,
              imageUrl: currentTab?.image_url || ''
            }
  })

  logger.debug('system', '功能性Tab内容摘要', {
    tabId,
    tabKey,
    roomId: roomId.value,
    sessionId: sessionId.value,
    roomIntro: currentTab?.tab_key === ROOM_INTRO_TAB_KEY
      ? {
          text: roomIntroText,
          imageUrl: roomIntroImage,
          rawImagePresent: !!roomIntroImage
        }
      : null,
    expertIntro: tabKey === EXPERT_INTRO_TAB_KEY
      ? {
          count: expertIntroLogItems.length,
          items: expertIntroLogItems
        }
      : null,
    brandIntro: tabKey === BRAND_INTRO_TAB_KEY
      ? {
          count: brandIntroLogItems.length,
          items: brandIntroLogItems
        }
      : null
  })
}

// 第一阶段目标：仅实现“功能性Tab列表渲染 + 可切换 + 内容基础渲染”

// 画质相关（当前设计文档仅支持单一播放地址，画质切换功能暂不支持）
const currentQuality = ref('自动')
const availableQualities = ref<Array<{ quality: 'auto' | 'high' | 'medium' | 'low'; url: string; bitrate?: number }>>([])
const videoErrorRetryCount = ref(0)

// 统计数据
const stats = ref({
  liveViewerCount: 0,
  totalViewerCount: 0,
  likeCount: 0,
  commentCount: 0,
  shareCount: 0
})

// 定时器
let statsTimer: any = null

// 观看记录（用于“观看历史”）
const watchStartTimeMs = ref<number | null>(null)
const lastPositionSec = ref(0)
const mediaDurationSec = ref(0)
const lastFlushAtMs = ref(0)

function handleTimeUpdate(e: any) {
  const detail = e?.detail ?? e
  const currentTime = Number(detail?.currentTime)
  const duration = Number(detail?.duration)
  if (Number.isFinite(currentTime)) lastPositionSec.value = currentTime
  if (Number.isFinite(duration)) mediaDurationSec.value = duration
}

async function flushWatchRecord(reason: string) {
  if (!authStore.isAuthenticated) return
  if (!sessionId.value) return
  if (watchStartTimeMs.value === null) return

  const nowMs = Date.now()
  if (nowMs - lastFlushAtMs.value < 1200) return

  const startMs = watchStartTimeMs.value
  const durationSec = Math.max(0, Math.floor((nowMs - startMs) / 1000))
  const lastPos = Math.max(0, Math.floor(lastPositionSec.value || 0))

  // 若几乎没开始播放，也别强行写入
  if (durationSec <= 0 && lastPos <= 0) {
    watchStartTimeMs.value = null
    lastFlushAtMs.value = nowMs
    return
  }

  const endTime = new Date(nowMs).toISOString()
  try {
    await recordWatchHistorySnapshot(reason, lastPos, endTime)
  } catch (e: any) {
    logger.warn('system', '写入观看记录失败', { error: e, sessionId: sessionId.value, reason })
  } finally {
    watchStartTimeMs.value = null
    lastFlushAtMs.value = nowMs
  }
}

// 计算属性
const sessionDetail = computed(() => currentSession.value)

// 下载地址（用于“保存到相册”）：优先使用后端提供的 mp4 / download 字段，避免误用 m3u8 播放清单
const downloadUrl = computed(() => {
  const detail: any = sessionDetail.value as any
  if (!detail) return ''
  const candidates: any[] = [
    detail.download_url,
    detail.downloadUrl,
    detail.playback_mp4_url,
    detail.playbackMp4Url,
    detail.mp4_url,
    detail.mp4Url,
    detail.recording_url,
    detail.recordingUrl,
    detail.playback?.mp4_url,
    detail.playback?.mp4Url,
    detail.stream?.mp4_url,
    detail.stream?.mp4Url
  ]
  const found = candidates.find(v => typeof v === 'string' && v.trim().length > 0) as string | undefined
  return found ? found.trim() : ''
})
const sessionStatus = computed(() => {
  const raw: any = (sessionDetail.value as any)?.status
  return typeof raw === 'string' ? raw.toLowerCase() : ''
})
const sessionStartTime = computed(() => {
  const s: any = sessionDetail.value as any
  const raw: any = s?.start_time ?? s?.startTime ?? s?.start_at ?? s?.startAt ?? s?.scheduled_start_time
  return typeof raw === 'string' ? raw : ''
})

const isLive = computed(() => sessionStatus.value === 'live')
const isReplay = computed(() => {
  const s = sessionStatus.value
  return s === 'ended' || s === 'replay' || s === 'playback' || s === 'ready' || s === 'finished'
})

// 直播态：微信小程序优先使用 live-player（更适合低延迟直播）
const useLivePlayer = computed(() => isLive.value)

// 兜底：从首页列表带入的 liveStatus 判定回放（避免 session.status 未按预期返回导致动作区不显示下载）
const isReplayByHome = computed(() => {
  const h: any = roomFromHome.value as any
  const raw = typeof h?.liveStatus === 'string' ? h.liveStatus.toLowerCase() : ''
  return raw === 'replay' || raw === 'ended' || raw === 'playback'
})

const isReplayForActions = computed(() => isReplay.value || isReplayByHome.value)
const isScheduled = computed(() => {
  if (sessionStatus.value === 'scheduled') return true

  // 兜底：若后端 status 不一致，但 start_time 在未来，则视为预告
  const t = Date.parse(sessionStartTime.value)
  if (!Number.isFinite(t)) return false
  return t > Date.now()
})

const showSubscriptionAction = computed(() => {
  // 仅“预告”展示订阅；回放/直播不显示
  if (isLive.value) return false
  if (isReplayForActions.value) return false
  if (sessionStatus.value === 'cancelled') return false
  return isScheduled.value
})

const showDownloadAction = computed(() => {
  // 需求：直播中不显示下载；回放中显示下载；预告由订阅替代
  if (showSubscriptionAction.value) return false
  return isReplayForActions.value
})

const sessionTitle = computed(() => {
  const title = (sessionDetail.value as any)?.title
  return typeof title === 'string' ? title : ''
})

const displayTitle = computed(() => {
  const roomTitle =
    (currentRoomDetail.value as any)?.title ||
    (currentRoomDetail.value as any)?.room_title ||
    ''
  return sessionTitle.value || roomTitle || roomFromHome.value?.title || '直播间'
})

/** 不公开房弱提示（测播/私人房）；非门禁、非报错 */
const isPrivateRoom = computed(() => {
  const r: any = currentRoomDetail.value as any
  if (!r) return false
  if (r.is_private === true || r.isPrivate === true) return true
  if (r.is_private === 1 || r.is_private === 'true') return true
  // 测播间：有 source_room_id 或标题带「连接测试」
  if (r.source_room_id || r.sourceRoomId) return true
  const title = String(r.title || '')
  return title.includes('连接测试')
})

const playerPlaceholderText = computed(() => {
  if (isScheduled.value) return '预告直播，暂未开始'
  if (loading.value) return '加载视频中…'
  if (roomInfoOnly.value && isPrivateRoom.value) return '连接测试 · 暂无画面'
  if (roomInfoOnly.value) return '暂无场次'
  if (error.value) return '视频暂不可播放'
  return '暂无播放地址'
})

// 标题折叠
const titleExpanded = ref(false)
const titleFoldThreshold = 18
const truncatedTitle = computed(() => {
  const title = displayTitle.value
  if (!title) return ''
  if (title.length <= titleFoldThreshold) return ''
  return `${title.slice(0, titleFoldThreshold)}...`
})

const displayExpertAvatar = computed(() =>
  resolveAvatarUrl(pickExpertAvatarRaw(), primaryExpertAvatarBroken.value)
)

const displayExpertName = computed(() => {
  const nameFromApi = expertInfo.value?.name
  if (typeof nameFromApi === 'string' && nameFromApi) return nameFromApi
  const nameFromSessionExperts = primaryExpert.value?.name
  if (typeof nameFromSessionExperts === 'string' && nameFromSessionExperts) return nameFromSessionExperts
  const name = (sessionDetail.value as any)?.featured_expert?.name
  if (typeof name === 'string' && name) return name
  const fallback = roomFromHome.value?.expertInfo?.name
  return typeof fallback === 'string' && fallback ? fallback : '主播'
})

const displayExpertTitle = computed(() => {
  const titleFromApi = expertInfo.value?.title
  if (typeof titleFromApi === 'string' && titleFromApi) return titleFromApi
  const titleFromSessionExperts = primaryExpert.value?.title
  if (typeof titleFromSessionExperts === 'string' && titleFromSessionExperts) return titleFromSessionExperts
  const title = (sessionDetail.value as any)?.featured_expert?.title
  if (typeof title === 'string' && title) return title
  const fallback = roomFromHome.value?.expertInfo?.title
  return typeof fallback === 'string' ? fallback : ''
})

/** 是否有真实关联专家（用于样式/关注可用性）；无专家时仍展示头像与名称兜底 */
const hasExpertData = computed(() => {
  if (expertInfo.value && (expertInfo.value.name || expertInfo.value.avatar_url)) return true
  if (primaryExpert.value && (primaryExpert.value.name || primaryExpert.value.avatar_url)) return true
  const expert = (sessionDetail.value as any)?.featured_expert
  if (expert && (expert.name || expert.avatar_url)) return true
  const homeExpert: any = (roomFromHome.value as any)?.expertInfo
  if (homeExpert && (homeExpert.name || homeExpert.avatar || homeExpert.avatar_url || homeExpert.title)) return true
  return Boolean(resolveExpertId())
})

const expertSectionLoading = computed(() => sessionExpertsLoading.value || expertInfoLoading.value)

// 简介折叠（过长则默认收起；按房间简介 Tab 文本判断，避免多 pane 时跟当前 Tab 串）
const introExpanded = ref(false)
const introFoldThreshold = 160
const roomIntroTextContent = computed(() => {
  const t = roomFunctionalTabs.value.find((x) => x.tab_key === ROOM_INTRO_TAB_KEY)
  return String(t?.text_content || '')
})
const introCanToggle = computed(() => roomIntroTextContent.value.length > introFoldThreshold)

function toggleIntro() {
  introExpanded.value = !introExpanded.value
}

watch(roomIntroTextContent, () => {
  introExpanded.value = false
})

// 标签折叠
const maxVisibleTags = 3
const showAllTags = ref(false)
const visibleTags = computed(() => {
  if (!sessionTags.value.length) return []
  if (showAllTags.value) return sessionTags.value
  return sessionTags.value.slice(0, maxVisibleTags)
})

/**
 * 格式化数字
 */
function formatNumber(num: number): string {
  if (num < 1000) return String(num)
  if (num < 10000) return `${(num / 1000).toFixed(1)}k`
  return `${(num / 10000).toFixed(1)}w`
}

/**
 * 统一处理图片链接协议：
 * - dayilive 域名从 http 升级到 https
 * - 本地 loopback 保持 http，避免证书与协议错误
 * - 其他域名保持原状
 */
function ensureHttps(url: string): string {
  if (!url || typeof url !== 'string') return ''
  const trimmed = url.trim()
  if (!trimmed) return ''

  const isMpWeixin = (): boolean => {
    // #ifdef MP-WEIXIN
    return true
    // #endif
    return false
  }

  const isLoopbackHost = (hostname: string): boolean => {
    const normalized = String(hostname || '').trim().toLowerCase()
    return normalized === 'localhost' || normalized === '127.0.0.1' || normalized === '::1'
  }

  try {
    const parsed = new URL(trimmed)
    if (isLoopbackHost(parsed.hostname)) {
      if (isMpWeixin()) return ''
      return `http://${parsed.host}${parsed.pathname}${parsed.search}${parsed.hash}`
    }
    if (parsed.hostname === 'mp.dayilive.com' || parsed.hostname === 'dayilive.com') {
      parsed.protocol = 'https:'
      return parsed.toString()
    }
    return trimmed
  } catch {
    if (/^http:\/\/(mp\.dayilive\.com|dayilive\.com)/.test(trimmed)) {
      return trimmed.replace(/^http:\/\/(mp\.dayilive\.com|dayilive\.com)/, 'https://$1')
    }
    if (/^https:\/\/(localhost|127\.0\.0\.1|::1)/i.test(trimmed)) {
      if (isMpWeixin()) return ''
      return trimmed.replace(/^https:/i, 'http:')
    }
    return trimmed
  }
}

/**
 * 加载播放地址
 * 遵循设计文档：从 GET /api/v1/sessions/{session_id} 响应中的 playback_url 字段获取
 */
async function loadPlayUrl() {
  // 播放地址从 sessionDetail 中获取，所以不需要单独调用API
  // 这个函数主要用于从 sessionDetail 中提取 playback_url
  if (!sessionDetail.value) {
    console.warn('⚠️ loadPlayUrl: sessionDetail 为空，等待场次详情加载')
    return
  }

  // 预告场次不应播放视频：清空播放地址并直接返回，由播放器区域展示封面图
  if (isScheduled.value) {
    playUrl.value = ''
    if (error.value && error.value.includes('未获取到播放地址')) {
      error.value = null
    }
    return
  }
  
  try {
    const detail: any = sessionDetail.value as any

    const candidates: Array<any> = [
      detail.stream_url,
      detail.streamUrl,
      detail.playback_url,
      detail.playbackUrl,
      detail.play_url,
      detail.playUrl,
      detail.hls_url,
      detail.hlsUrl,
      detail.flv_url,
      detail.flvUrl,
      detail.rtmp_url,
      detail.rtmpUrl,
      detail.playback?.url,
      detail.stream?.url,
      detail.stream?.play_url,
      detail.stream?.playUrl
    ]

    const directUrl = candidates.find(v => typeof v === 'string' && v.trim().length > 0) as string | undefined

    if (directUrl) {
      const finalUrl = directUrl.trim()

      // #ifdef MP-WEIXIN
      // 小程序 <video> 对 http 资源/域名白名单限制非常严格：先给出明确提示，避免“看起来像没加载”
      if (finalUrl.startsWith('http://')) {
        playUrl.value = ''
        error.value = '播放地址必须为 https（请检查回放地址协议、证书与小程序业务域名配置）'
        logger.warn('system', '播放地址为 http（小程序可能无法播放）', { sessionId: sessionId.value, url: finalUrl })
        return
      }

      const lower = finalUrl.toLowerCase()
      const looksM3u8 = lower.includes('.m3u8') || lower.includes('m3u8')
      if (looksM3u8) {
        logger.warn('system', '播放地址疑似为 m3u8（小程序 video 可能不支持/或受域名限制）', {
          sessionId: sessionId.value,
          url: finalUrl
        })
      }
      // #endif

      playUrl.value = finalUrl
      console.log('🎬 [loadPlayUrl] 从 sessionDetail 提取到播放地址', {
        sessionId: sessionId.value,
        url: playUrl.value,
        isM3u8: /m3u8/i.test(playUrl.value),
        isMp4: /\.mp4(\?|$)/i.test(playUrl.value)
      })
    } else {
      // 设计文档仅保证 session 详情提供 playback_url（或等价字段）。
      // 后端未开放 /play-url 时，这里不做兜底请求，避免产生 404 噪音。
      playUrl.value = ''
    }

    if (!playUrl.value) {
      // 无播放地址属正常业务态：播放器区展示「暂无播放地址」，不弹顶部红色报错
      if (error.value && error.value.includes('未获取到播放地址')) {
        error.value = null
      }
      logger.warn('system', '未获取到播放地址', { sessionId: sessionId.value })
      return
    }

    // 基础校验：如果后端返回的是 rtmp/flv，微信小程序 video 可能无法播放
    if (playUrl.value) {
      const urlLower = playUrl.value.toLowerCase()
      const isRtmp = urlLower.startsWith('rtmp://')
      const isFlv = urlLower.endsWith('.flv') || urlLower.includes('.flv?')
      if (isRtmp || isFlv) {
        logger.warn('system', '播放地址可能不被 video 组件支持（建议使用 live-player）', {
          sessionId: sessionId.value,
          url: playUrl.value
        })
      }
    }
  } catch (err: any) {
    console.error('❌ 获取播放地址失败', err)
    logger.error('system', '获取播放地址失败', { error: err, sessionId: sessionId.value })
    playUrl.value = ''
  }
}

async function ensureQualityOptions(): Promise<boolean> {
  void sessionId
  return false
}

async function switchQuality(quality: 'auto' | 'high' | 'medium' | 'low') {
  void quality
}

/**
 * 加载场次详情
 */
async function loadSessionDetail() {
  if (!sessionId.value) {
    console.warn('⚠️ loadSessionDetail: sessionId 为空')
    return
  }
  
  try {
    console.log('📡 [loadSessionDetail] 开始获取场次详情', { 
      sessionId: sessionId.value,
      sessionIdType: typeof sessionId.value,
      sessionIdLength: sessionId.value.length
    })
    // 不使用缓存，确保每次进入不同直播间都拉最新专家信息
    await sessionStore.fetchSessionDetail(sessionId.value, false)
    console.log('✅ [loadSessionDetail] 场次详情获取成功', {
      sessionId: sessionId.value,
      featured_expert: sessionDetail.value?.featured_expert,
      room_id: sessionDetail.value?.room_id
    })
  } catch (err: any) {
    console.error('❌ 获取场次详情失败', err)
    error.value = err.message || '加载场次信息失败'
    logger.error('system', '加载场次详情失败', { error: err })
  }
}

/**
 * 加载专家详情（公开接口），取消依赖任何 mock 的专家数据
 */
async function loadExpertInfo() {
  expertInfoLoading.value = true
  try {
    expertInfo.value = null
    const expertId = primaryExpertId.value || resolveExpertId()
    if (!expertId) return
    // 《16》P44：已下架专家 404 不弹错、不刷 ERROR
    const res = await getExpertDetail(expertId, { showError: false, quiet: true })
    const data: any = (res as any)?.data ?? res
    if (data && typeof data === 'object') {
      expertInfo.value = data
      try {
        if (authStore.isAuthenticated) {
          await expertStore.checkFollow(expertId)
        }
      } catch {
        // ignore
      }
      try {
        console.log('✅ [loadExpertInfo] 已获取专家信息', {
          expertId,
          name: expertInfo.value?.name,
          title: expertInfo.value?.title,
          avatar_url: expertInfo.value?.avatar_url
        })
      } catch {}
    }
  } catch (e) {
    // 专家信息获取失败不阻断页面（含已下架）
    console.warn('⚠️ 获取专家信息失败', e)
  } finally {
    expertInfoLoading.value = false
  }
}

/**
 * 加载统计数据
 * 遵循设计文档：从 GET /api/v1/sessions/{session_id} 响应中的 statistics 字段获取
 */
async function loadStats() {
  // 统计数据从 sessionDetail 中获取，所以不需要单独调用API
  // 这个函数主要用于从 sessionDetail 中提取 statistics
  if (!sessionDetail.value) {
    console.warn('⚠️ loadStats: sessionDetail 为空，等待场次详情加载')
    return
  }

  try {
    // 注意：文档中使用 snake_case，需要根据实际返回格式调整
    const statistics = (sessionDetail.value as any).statistics
    
    if (statistics) {
      // 映射字段名（文档中使用 snake_case，前端使用 camelCase）
      stats.value = {
        liveViewerCount: statistics.current_viewer_count || statistics.currentViewerCount || 0,
        totalViewerCount: statistics.peak_viewer_count || statistics.peakViewerCount || 0,
        likeCount: statistics.total_like_count || statistics.totalLikeCount || 0,
        commentCount: statistics.comment_count || statistics.commentCount || 0,
        shareCount: statistics.share_count || statistics.shareCount || 0
      }
    }
  } catch (err) {
    // 统计数据加载失败不影响播放，只记录日志
    logger.warn('system', '加载统计数据失败', { error: err })
  }
}

/**
 * 定时更新统计数据（直播时）
 * 注意：统计数据从 sessionDetail.statistics 获取，所以需要重新加载 sessionDetail
 */
function startStatsTimer() {
  if (!isLive.value) return
  
  statsTimer = setInterval(async () => {
    // 重新加载场次详情以获取最新的统计数据
    try {
      await loadSessionDetail()
      loadStats() // 从更新后的 sessionDetail 中提取统计数据
    } catch (err) {
      // 定时器更新失败不影响播放，只记录日志
      logger.warn('system', '定时更新统计数据失败', { error: err })
    }
  }, 5000) // 每5秒更新一次
}

/**
 * 停止统计定时器
 */
function stopStatsTimer() {
  if (statsTimer) {
    clearInterval(statsTimer)
    statsTimer = null
  }
}


/**
 * 视频播放事件
 */
function handlePlay() {
  logger.info('user', '视频开始播放', { sessionId: sessionId.value })
  if (watchStartTimeMs.value === null) {
    watchStartTimeMs.value = Date.now()
  }
}

/**
 * 视频暂停事件
 */
function handlePause() {
  logger.info('user', '视频暂停', { sessionId: sessionId.value })
  void flushWatchRecord('pause')
}

/**
 * 视频结束事件
 */
function handleEnded() {
  logger.info('user', '视频播放结束', { sessionId: sessionId.value })
  void flushWatchRecord('ended')
  
  uni.showModal({
    title: '播放结束',
    content: '是否观看相关推荐？',
    success: (res) => {
      if (res.confirm) {
        // TODO: 跳转到相关推荐
        uni.showToast({
          title: '相关推荐功能开发中',
          icon: 'none'
        })
      }
    }
  })
}

function appendCacheBusting(url: string): string {
  try {
    const u = new URL(url)
    u.searchParams.set('ts', String(Date.now()))
    return u.toString()
  } catch {
    if (!url) return url
    return url.includes('?') ? `${url}&ts=${Date.now()}` : `${url}?ts=${Date.now()}`
  }
}

async function recoverPlayback(lastError?: any): Promise<boolean> {
  if (!sessionId.value) return false
  try {
    // 后端未开放 /play-url 时：仅对现有地址追加时间戳避缓存
    const finalUrl = playUrl.value ? appendCacheBusting(playUrl.value) : ''

    if (!finalUrl) return false

    // 应用并尝试播放
    playUrl.value = finalUrl
    setTimeout(() => {
      try {
        // #ifdef MP-WEIXIN
        if (useLivePlayer.value) {
          const ctx = uni.createLivePlayerContext('live-live-player') as any
          ctx?.play?.()
        } else {
          const ctx = uni.createVideoContext('live-video-player')
          ctx.play()
        }
        // #endif

        // #ifndef MP-WEIXIN
        const ctx = uni.createVideoContext('live-video-player')
        ctx.play()
        // #endif
      } catch {}
    }, 80)

    uni.showToast({ title: '已尝试切换播放源', icon: 'none' })
    logger.info('system', 'recoverPlayback: 已切换播放源', { sessionId: sessionId.value, finalUrl, lastError })
    return true
  } catch (e) {
    logger.warn('system', 'recoverPlayback: 获取备用播放地址失败', { error: e, sessionId: sessionId.value })
    return false
  }
}

function handleLivePlayerStateChange(e: any) {
  const code = Number(e?.detail?.code)
  // 微信小程序 live-player 状态码在不同版本可能略有差异；这里用宽松映射，保证基础埋点与观看计时。
  if (code === 2004 || code === 2005 || code === 2007) {
    handlePlay()
  }
  if (code === 2008) {
    handlePause()
  }
  if (code === 2009) {
    handleEnded()
  }
}

function handleLivePlayerError(e: any) {
  handleVideoError(e)
}

/**
 * 视频错误事件
 */
function handleVideoError(e: any) {
  logger.error('system', '视频播放错误', { error: e, sessionId: sessionId.value, url: playUrl.value })

  // 仅在有限次数内进行自动恢复尝试
  const detail = e?.detail || e
  const errMsg: string = typeof detail?.errMsg === 'string' ? detail.errMsg : ''
  const isHls404 = /HLS error.*manifestLoadError/i.test(errMsg) || /response:\s*\{\"code\":404/.test(errMsg || '')

  const tryRecover = async () => {
    if (videoErrorRetryCount.value >= 2) return false
    videoErrorRetryCount.value += 1
    // 先尝试后端兜底获取新地址，失败则对现地址加时间戳
    const ok = await recoverPlayback(e)
    return ok
  }

  ;(async () => {
    const recovered = await tryRecover()
    if (recovered) return

    // 若无法恢复或超过重试次数，给出明确提示
    const hint = isHls404
      ? '视频资源不存在或已失效（404）。请稍后再试或联系管理员检查播放地址。'
      : '视频加载失败，请检查网络或稍后重试'

    const debugSuffix = errMsg
      ? `\n\n错误信息：${errMsg}${playUrl.value ? `\nURL：${playUrl.value}` : ''}`
      : (playUrl.value ? `\n\nURL：${playUrl.value}` : '')

    uni.showModal({
      title: '播放错误',
      content: hint + debugSuffix,
      showCancel: true,
      cancelText: '留在此页',
      confirmText: '返回',
      success: (res) => {
        if (res.confirm) handleBack()
      }
    })
  })()
}

/**
 * 全屏变化事件
 */
function handleFullscreenChange(e: any) {
  const fullScreen = e.detail.fullScreen || e.detail.fullscreen || false
  logger.info('user', '全屏状态变化', { fullScreen })
  
  // 全屏时隐藏页面其他内容，退出全屏时恢复
  // 注意：uni-app的video组件全屏时会自动处理，这里主要用于状态追踪
}

/**
 * 画质切换点击
 * 注意：根据设计文档，播放地址只有一个 playback_url 字段，暂不支持画质切换
 * 此功能保留UI，但实际不执行切换操作
 */
function handleQualityClick() {
  logger.info('user', '点击画质切换', { sessionId: sessionId.value })
  if (!sessionId.value) {
    uni.showToast({ title: '缺少场次ID', icon: 'none' })
    return
  }

  uni.showToast({ title: '暂不支持切换画质', icon: 'none' })
  return

  const openSheet = async () => {
    if (!availableQualities.value.length) {
      const ok = await ensureQualityOptions()
      if (!ok) {
        uni.showToast({ title: '后端未提供多画质列表', icon: 'none' })
        return
      }
    }

    const label = (q: string) => (q === 'high' ? '高清' : q === 'medium' ? '标清' : q === 'low' ? '流畅' : '自动')
    const itemList = availableQualities.value.map(item => {
      const bitrate = typeof item.bitrate === 'number' && item.bitrate > 0 ? ` ${Math.round(item.bitrate / 1000)}kbps` : ''
      return `${label(item.quality)}${bitrate}`
    })

    uni.showActionSheet({
      itemList,
      success: async (res) => {
        const chosen = availableQualities.value[res.tapIndex]
        if (!chosen) return
        await switchQuality(chosen.quality)
      }
    })
  }

  openSheet()
}

/**
 * 标题展开/收起
 */
function toggleTitle() {
  if (!sessionTitle.value || sessionTitle.value.length <= titleFoldThreshold) return
  titleExpanded.value = !titleExpanded.value
}

/**
 * 标签展开/收起
 */
function toggleTags() {
  showAllTags.value = !showAllTags.value
}

/**
 * 关注/取消关注
 */
async function toggleSubscription() {
  const rid = currentRoomIdForActions.value
  if (!rid) {
    uni.showToast({ title: '缺少房间ID', icon: 'none' })
    return
  }
  if (!showSubscriptionAction.value) {
    uni.showToast({ title: '直播已开始或已结束，无法订阅', icon: 'none' })
    return
  }
  if (!ensureAuthed()) return
  if (subscriptionBusy.value) return

  subscriptionBusy.value = true
  const next = !isSubscribed.value
  subscriptionOverride.value = next

  logger.info('user', next ? 'subscribe:start' : 'unsubscribe:start', { roomId: rid })

  try {
    if (next) {
      await userSubscriptionsStore.add(rid)
      uni.showToast({ title: '已订阅', icon: 'success' })
      logger.info('user', 'subscribe:success', { roomId: rid })
      // add 不会直接影响列表，刷新一次让“我的订阅”立刻可见
      try {
        await userSubscriptionsStore.refresh()
      } catch {
        // ignore
      }
    } else {
      await userSubscriptionsStore.remove(rid)
      uni.showToast({ title: '已取消订阅', icon: 'none' })
      logger.info('user', 'unsubscribe:success', { roomId: rid })
    }
  } catch (e: any) {
    subscriptionOverride.value = null
      uni.showToast({ title: e?.message || '订阅操作失败', icon: 'none' })
      logger.warn('user', 'subscribe:failed', { roomId: rid, error: String(e?.message || e) })
  } finally {
    subscriptionBusy.value = false
    // 若 store 已更新到位，让 computed 回归真实数据
    subscriptionOverride.value = null
  }
}

/**
 * 点赞（当前后端未开放接口，避免触发 404）
 */
function handleLike() {
  logger.info('user', 'like:skipped', { reason: '功能暂未开放' })
  uni.showToast({ title: '点赞功能暂未开放', icon: 'none' })
}

/**
 * 下载：回放场次尝试保存到相册
 */
async function handleDownload() {
  if (downloadBusy.value) return

  if (!ensureAuthed()) return

  logger.info('user', 'download:start', { sessionId: sessionId.value, roomId: roomId.value })

  if (isLive.value) {
    uni.showToast({ title: '直播中暂不支持下载', icon: 'none' })
    return
  }

  if (!isReplayForActions.value) {
    uni.showToast({ title: '仅回放支持下载', icon: 'none' })
    return
  }
  if (!playUrl.value) {
    uni.showToast({ title: '暂无可下载地址', icon: 'none' })
    return
  }

  type MediaProbeResult = {
    statusCode?: number
    contentType?: string
    location?: string
    effectiveUrl?: string
  }

  async function probeMediaUrl(url: string): Promise<MediaProbeResult> {
    const out: MediaProbeResult = { effectiveUrl: url }

    const pickHeader = (h: any, key: string) => {
      if (!h || typeof h !== 'object') return ''
      return String(h[key] ?? h[key.toLowerCase()] ?? h[key.toUpperCase()] ?? '')
    }

    // 1) 优先 HEAD
    const headRes = await new Promise<any>((resolve) => {
      try {
        uni.request({
          url,
          method: 'HEAD' as any,
          timeout: 8000,
          success: (res) => resolve(res),
          fail: () => resolve(null)
        })
      } catch {
        resolve(null)
      }
    })

    if (headRes && typeof headRes === 'object') {
      out.statusCode = Number(headRes.statusCode)
      const header = headRes.header || {}
      out.contentType = pickHeader(header, 'content-type')
      out.location = pickHeader(header, 'location')
      if (out.location) out.effectiveUrl = out.location
      return out
    }

    // 2) HEAD 不支持时：轻量 GET（尽量只取一点点）
    const getRes = await new Promise<any>((resolve) => {
      try {
        uni.request({
          url,
          method: 'GET',
          timeout: 8000,
          header: {
            Range: 'bytes=0-1'
          } as any,
          responseType: 'arraybuffer' as any,
          success: (res) => resolve(res),
          fail: () => resolve(null)
        })
      } catch {
        resolve(null)
      }
    })

    if (getRes && typeof getRes === 'object') {
      out.statusCode = Number(getRes.statusCode)
      const header = getRes.header || {}
      out.contentType = pickHeader(header, 'content-type')
      out.location = pickHeader(header, 'location')
      if (out.location) out.effectiveUrl = out.location
    }

    return out
  }

  const originalUrl = String(downloadUrl.value || playUrl.value || '')
  if (!originalUrl) {
    uni.showToast({ title: '后端未提供可下载地址', icon: 'none' })
    return
  }
  let effectiveUrl = originalUrl
  let probe: MediaProbeResult | null = null
  // #ifdef MP-WEIXIN
  probe = await probeMediaUrl(originalUrl)
  effectiveUrl = String(probe?.effectiveUrl || originalUrl)
  try {
    console.log('🔎 [download-probe]', {
      originalUrl,
      effectiveUrl,
      statusCode: probe?.statusCode,
      contentType: probe?.contentType,
      location: probe?.location
    })
  } catch {}
  // #endif

  const urlLower = effectiveUrl.toLowerCase()
  const contentTypeLower = String(probe?.contentType || '').toLowerCase()

  const isMp4ByUrl = urlLower.endsWith('.mp4') || urlLower.includes('.mp4?')
  const isM3u8ByUrl = urlLower.endsWith('.m3u8') || urlLower.includes('.m3u8?') || urlLower.includes('m3u8')
  const isFlvByUrl = urlLower.endsWith('.flv') || urlLower.includes('.flv?')
  const isRtmpByUrl = urlLower.startsWith('rtmp://')

  const isMp4ByHeader = contentTypeLower.includes('video/mp4')
  const isM3u8ByHeader =
    contentTypeLower.includes('application/vnd.apple.mpegurl') ||
    contentTypeLower.includes('application/x-mpegurl') ||
    contentTypeLower.includes('application/mpegurl')

  // 明确是流式（URL 或 Content-Type 任一命中）就禁止保存
  if (!isMp4ByUrl && !isMp4ByHeader && (isM3u8ByUrl || isM3u8ByHeader || isFlvByUrl || isRtmpByUrl)) {
    uni.showToast({ title: '后端仅返回流式播放地址，无法保存', icon: 'none' })
    return
  }
  // 无法确认是 mp4 就提示不支持（避免保存失败造成误导）
  if (!isMp4ByUrl && !isMp4ByHeader) {
    uni.showToast({ title: '暂仅支持 MP4 回放下载', icon: 'none' })
    return
  }

  downloadBusy.value = true
  try {
    // #ifdef MP-WEIXIN
    const scopeKey = 'scope.writePhotosAlbum'
    const setting = await new Promise<any>((resolve) => {
      uni.getSetting({
        success: (res) => resolve(res),
        fail: () => resolve(null)
      })
    })
    const authSetting = setting?.authSetting || {}
    if (authSetting[scopeKey] === false) {
      const go = await new Promise<boolean>((resolve) => {
        uni.showModal({
          title: '需要相册权限',
          content: '保存回放视频到相册需要授权，请在设置中开启。',
          confirmText: '去设置',
          cancelText: '取消',
          success: (res) => resolve(!!res?.confirm),
          fail: () => resolve(false)
        })
      })
      if (go) {
        await new Promise<void>((resolve) => {
          uni.openSetting({
            success: () => resolve(),
            fail: () => resolve()
          })
        })
      }
      return
    }
    if (!authSetting[scopeKey]) {
      try {
        await new Promise<void>((resolve, reject) => {
          uni.authorize({
            scope: scopeKey,
            success: () => resolve(),
            fail: (err) => reject(err)
          })
        })
      } catch {
        uni.showToast({ title: '未授权，无法保存到相册', icon: 'none' })
        return
      }
    }

    showGlobalLoading('下载中...')
    const tempFilePath = await new Promise<string>((resolve, reject) => {
      uni.downloadFile({
        url: effectiveUrl,
        success: (res) => {
          if (res.statusCode === 200 && res.tempFilePath) resolve(res.tempFilePath)
          else reject(new Error('下载失败'))
        },
        fail: () => reject(new Error('下载失败'))
      })
    })

    await new Promise<void>((resolve, reject) => {
      uni.saveVideoToPhotosAlbum({
        filePath: tempFilePath,
        success: () => resolve(),
        fail: (err) => reject(err)
      })
    })

    uni.showToast({ title: '已保存到相册', icon: 'success' })
    logger.info('user', 'download:success', { sessionId: sessionId.value, url: effectiveUrl })
    // #endif

    // #ifndef MP-WEIXIN
    uni.showToast({ title: '当前平台暂不支持下载', icon: 'none' })
    // #endif
  } catch (e: any) {
    const msg = e?.errMsg || e?.message
    if (typeof msg === 'string' && (msg.includes('auth') || msg.includes('authorize') || msg.includes('permission'))) {
      uni.showToast({ title: '请授权保存到相册', icon: 'none' })
    } else {
      uni.showToast({ title: '下载失败', icon: 'none' })
    }
    logger.warn('user', 'download:failed', { sessionId: sessionId.value, error: String(msg || e) })
  } finally {
    // #ifdef MP-WEIXIN
    hideGlobalLoading()
    // #endif
    downloadBusy.value = false
  }
}

/**
 * 收藏
 */
async function handleFavorite() {
  const rid = currentRoomIdForActions.value
  if (!rid) {
    uni.showToast({ title: '缺少房间ID', icon: 'none' })
    return
  }
  if (!ensureAuthed()) return
  if (favoriteBusy.value) return

  favoriteBusy.value = true
  const next = !isFavorited.value
  favoriteOverride.value = next

  logger.info('user', next ? 'favorite:start' : 'unfavorite:start', { roomId: rid })

  try {
    if (next) {
      await userFavoritesStore.add(rid)
      uni.showToast({ title: '已收藏', icon: 'success' })
      logger.info('user', 'favorite:success', { roomId: rid })
      try {
        await userFavoritesStore.refresh()
      } catch {
        // ignore
      }
    } else {
      await userFavoritesStore.remove(rid)
      uni.showToast({ title: '已取消收藏', icon: 'none' })
      logger.info('user', 'unfavorite:success', { roomId: rid })
    }
  } catch (e: any) {
    favoriteOverride.value = null
    uni.showToast({ title: e?.message || '收藏操作失败', icon: 'none' })
    logger.warn('user', 'favorite:failed', { roomId: rid, error: String(e?.message || e) })
  } finally {
    favoriteBusy.value = false
    favoriteOverride.value = null
  }
}

onShow(async () => {
  await ensureUserListsLoaded()
})

watch(
  () => currentRoomIdForActions.value,
  async (rid) => {
    if (!rid) return
    await ensureUserListsLoaded()
  }
)


/**
 * 返回上一页
 */
function handleBack() {
  uni.navigateBack()
}

/**
 * 分享：对齐 docs/19-分享功能（前端功能；复用 onShareAppMessage；path 仅 roomId）
 */
const showSharePanel = ref(false)

function handleShare() {
  logger.info('user', '分享操作', { roomId: roomId.value })
  if (!roomId.value) {
    uni.showToast({ title: '暂无可分享的直播间', icon: 'none' })
    return
  }
  showSharePanel.value = true
}

function closeSharePanel() {
  showSharePanel.value = false
}

function handleShareViaSystemHint() {
  closeSharePanel()
  uni.showToast({ title: '请使用系统分享', icon: 'none' })
}

function handleCopyLiveLink() {
  if (!sharePath.value || !roomId.value) {
    uni.showToast({ title: '暂无可复制的直播链接', icon: 'none' })
    return
  }
  uni.setClipboardData({
    data: sharePath.value,
    success: () => {
      closeSharePanel()
      uni.showToast({ title: '已复制直播链接', icon: 'success' })
    }
  })
}

const shareTitle = computed(() => displayTitle.value || '直播间')

/** 正式/测播均用当前页 roomId；禁止改写为正式间或其它场次 */
const sharePath = computed(() => {
  if (!roomId.value) return ''
  return `/pages/live/LiveView?roomId=${encodeURIComponent(roomId.value)}`
})

const shareImageUrl = computed(() => {
  const s: any = sessionDetail.value as any
  const r: any = currentRoomDetail.value as any
  const h: any = roomFromHome.value as any
  const raw = h?.cover_url || h?.coverUrl || s?.cover_url || r?.cover_url
  if (typeof raw !== 'string' || !raw) return ''
  return ensureHttps(resolveMediaUrl(raw))
})

// 预告播放器占位封面：优先保证可见，不走 ensureHttps 的 loopback 清空逻辑
const playerCoverUrl = computed(() => {
  const s: any = sessionDetail.value as any
  const r: any = currentRoomDetail.value as any
  const h: any = roomFromHome.value as any
  const raw = h?.cover_url || h?.coverUrl || s?.cover_url || r?.cover_url
  if (typeof raw !== 'string' || !raw) return ''
  const resolved = resolveMediaUrl(raw)
  if (resolved) return resolved
  // resolveMediaUrl 为空时兜底原始值（例如已是 /static/...）
  return raw
})

const playerCoverBroken = ref(false)

// 最小诊断增强：打印三个候选封面 URL（fromHome / roomDetail / sessionDetail）以及最终选中的 `playerCoverUrl`
function dumpCoverCandidates(source = 'auto') {
  try {
    const s: any = sessionDetail.value as any
    const r: any = currentRoomDetail.value as any
    const h: any = roomFromHome.value as any
    const fromHome = typeof (h?.cover_url === 'string' ? h.cover_url : (h?.coverUrl || '')) === 'string' ? (h?.cover_url || h.coverUrl || '') : ''
    const sessionDetailUrl = typeof s?.cover_url === 'string' ? s.cover_url : (typeof s?.coverUrl === 'string' ? s.coverUrl : '')
    const roomDetailUrl = typeof r?.cover_url === 'string' ? r.cover_url : (typeof r?.coverUrl === 'string' ? r.coverUrl : '')
    const selectedRaw = fromHome || sessionDetailUrl || roomDetailUrl || ''
    const selectedResolved = selectedRaw ? resolveMediaUrl(selectedRaw) || selectedRaw : ''
    const finalResolved = playerCoverUrl.value || ''
    console.log('🔍 [cover-diagnostics]', { source, fromHome, sessionDetailUrl, roomDetailUrl, selectedRaw, selectedResolved, finalResolved })
  } catch {}
}

// 监听数据来源变化并立即打印（便于快速锁定是哪个源把封面切坏）
watch([
  () => roomFromHome.value,
  () => currentRoomDetail.value,
  () => sessionDetail.value
], () => {
  dumpCoverCandidates('sources-changed')
}, { immediate: true, deep: true })

// 监听最终值变化，单独打印新旧值
watch(() => playerCoverUrl.value, (v, old) => {
  try { console.log('🔍 [cover-diagnostics] playerCoverUrl changed', { new: v || '', old: old || '' }) } catch {}
  if (v && v !== old) {
    playerCoverBroken.value = false
  }
})

function handlePlayerCoverError() {
  const h: any = roomFromHome.value as any
  const s: any = sessionDetail.value as any
  const r: any = currentRoomDetail.value as any
  const selectedRaw = h?.cover_url || h?.coverUrl || s?.cover_url || r?.cover_url || ''
  logger.warn('system', 'player_cover_load_failed', {
    component: 'LiveView',
    imageSlot: 'player-placeholder-cover',
    roomId: roomId.value || '',
    sessionId: sessionId.value || '',
    roomFromHomeUrl: (roomFromHome.value as any)?.coverUrl || (roomFromHome.value as any)?.cover_url || '',
    roomDetailUrl: (currentRoomDetail.value as any)?.coverUrl || (currentRoomDetail.value as any)?.cover_url || '',
    sessionDetailUrl: (sessionDetail.value as any)?.coverUrl || (sessionDetail.value as any)?.cover_url || '',
    selectedRawCoverUrl: selectedRaw || '',
    resolvedPlayerCoverUrl: playerCoverUrl.value || ''
  })
  playerCoverBroken.value = true
}

function handleFunctionalTabImageError() {
  const tab: any = currentFunctionalTab.value as any
  logger.warn('system', 'functional_tab_image_load_failed', {
    component: 'LiveView',
    imageSlot: 'functional-tab-image',
    roomId: roomId.value || '',
    sessionId: sessionId.value || '',
    tabKey: tab?.key || '',
    tabTitle: tab?.title || '',
    rawImageUrl: tab?.image_url || '',
    resolvedImageUrl: tab?.image_url ? (normalizeAnyImageUrl(tab.image_url) || '') : ''
  })
}

onShareAppMessage(() => {
  const path = sharePath.value || '/pages/live/LiveView'
  return {
    title: shareTitle.value,
    path,
    imageUrl: shareImageUrl.value
  }
})

/**
 * 通过roomId查找sessionId
 * 流程：1. 先查房间详情获取current_session_id 2. 如果没有则查场次列表取最新场次
 */
async function findSessionIdByRoomId(roomIdParam: string): Promise<string | null> {
  try {
    console.log('🔍 [findSessionIdByRoomId] 开始查找场次ID', { roomId: roomIdParam })
    
    // 步骤1：获取房间详情，尝试获取current_session_id
    const roomResponse = await getRoomById(roomIdParam)
    console.log('📡 [findSessionIdByRoomId] 房间详情响应', roomResponse)
    
    // 兼容：整包 {code,data} / 已解包 room
    const raw: any = roomResponse as any
    let room: any = raw?.data ?? raw
    if (room && !room.id && room.data?.id) room = room.data
    // 供无场次时的「连接测试」弱提示 / 文案判断
    currentRoomDetail.value = room
    console.log('🏷️ [findSessionIdByRoomId] room meta', {
      id: room?.id,
      title: room?.title,
      is_private: room?.is_private,
      source_room_id: room?.source_room_id
    })
    const currentSessionId = room?.current_session_id
    
    if (currentSessionId) {
      console.log('✅ [findSessionIdByRoomId] 从房间详情获取到current_session_id', currentSessionId)
      return currentSessionId
    }
    
    // 步骤2：如果没有current_session_id，获取场次列表，取最新场次
    console.log('⚠️ [findSessionIdByRoomId] 房间没有current_session_id，尝试获取场次列表')
    const sessionsResponse = await getRoomSessions(roomIdParam, {
      page: 1,
      size: 10,
      sort_by: 'created_at',
      sort_order: 'desc'
    } as any)
    console.log('📡 [findSessionIdByRoomId] 场次列表响应', sessionsResponse)
    
    // 处理响应拦截器提取后的数据
    const paginatedData = (sessionsResponse as any).data || sessionsResponse
    const sessions =
      (Array.isArray(paginatedData?.items) ? paginatedData.items : null) ||
      (paginatedData?.data && Array.isArray(paginatedData.data.items) ? paginatedData.data.items : null) ||
      []
    
    if (sessions.length > 0) {
      const pickByStatus = (wanted: string) => {
        const found = sessions.find((x: any) => String(x?.status || '').toLowerCase() === wanted)
        return found || null
      }

      const best = pickByStatus('live') || pickByStatus('scheduled') || sessions[0]
      const bestId = String((best as any)?.id || (best as any)?.session_id || '')
      if (bestId) {
        console.log('✅ [findSessionIdByRoomId] 从场次列表获取到场次ID', { bestId, status: (best as any)?.status })
        return bestId
      }
    }
    
    console.warn('⚠️ [findSessionIdByRoomId] 该房间没有场次')
    return null
  } catch (err: any) {
    console.error('❌ [findSessionIdByRoomId] 查找场次ID失败', err)
    throw err
  }
}

/**
 * 页面加载
 */
onLoad(async (options?: { id?: string; sessionId?: string; roomId?: string }) => {
  pageLoaded.value = true
  console.log('🔍 [onLoad] 接收到的参数:', options)
  
  // 从 store 获取从首页传递过来的房间数据
  roomFromHome.value = roomStore.getSelectedRoomFromHome()
  if (roomFromHome.value) {
    console.log('📦 [onLoad] 从 store 获取到房间数据:', roomFromHome.value)
    // 可以使用 roomFromHome 中的数据进行展示或预加载
    // 例如：title, coverUrl, summary, category 等
  }
  
  // 优先使用直接传入的sessionId或id
  sessionId.value = options?.id || options?.sessionId || ''
  roomId.value = options?.roomId || ''
  
  console.log('🔍 [onLoad] 设置后的 sessionId:', sessionId.value, 'roomId:', roomId.value)

  // ...existing code...

  // 如果没有sessionId但有roomId，通过roomId查找sessionId
  if (!sessionId.value && roomId.value) {
    try {
      loading.value = true
      const foundSessionId = await findSessionIdByRoomId(roomId.value)
      
      if (!foundSessionId) {
        // 无场次 = 房间信息模式：绝不挂红色 ErrorBanner（测播尤其如此）
        roomInfoOnly.value = true
        error.value = null
        logger.warn('system', '未找到场次ID（将进入房间信息模式）', {
          roomId: roomId.value,
          isPrivate: isPrivateRoom.value
        })

        // 进入“房间信息模式”：仍然加载房间级信息（tabs/brands），保证页面可展示
        try {
          await loadRoomBrands()
          await loadExpertInfo()
          await loadRoomFunctionalTabs()
        } catch (e: any) {
          logger.warn('system', '房间信息加载失败', { roomId: roomId.value, error: e })
        }
        return
      }
      
      sessionId.value = foundSessionId
      console.log('✅ [onLoad] 通过roomId查找到sessionId:', sessionId.value)
    } catch (err: any) {
      error.value = err.message || '查找场次失败，请稍后重试'
      logger.error('system', '查找场次ID失败', { error: err, roomId: roomId.value })
      return
    } finally {
      loading.value = false
    }
  }

  if (!sessionId.value) {
    // 若存在 roomId，说明已进入“房间信息模式”（无场次），无需按错误中断。
    if (roomId.value) return

    error.value = '缺少场次ID或房间ID参数，请检查跳转链接是否正确'
    logger.error('system', '缺少必要参数', { options })
    return
  }
  
  logger.info('system', '直播观看页面加载', { sessionId: sessionId.value, roomId: roomId.value })
  console.log('🔍 [onLoad] 准备加载数据，sessionId:', sessionId.value)
  
  try {
    // 先加载场次详情（因为播放地址从详情中获取）
    await loadSessionDetail()

    // 加载场次标签（独立接口，不依赖 sessionDetail.tags）
    await loadSessionTags()

    // 按专家模块设计：场次专家关联来自 live_session_experts，需要先拉场次专家列表
    await loadSessionExperts()

    // 加载专家信息（通过公开接口）
    await loadExpertInfo()

    // 统一补齐 roomId（功能性 tab 依赖 room_id）；若路由 roomId 与详情不一致，使用详情中的标准 room_id
    if (sessionDetail.value?.room_id) {
      roomId.value = sessionDetail.value.room_id
    }
    
    // 场次详情加载后，从详情中提取播放地址
    loadPlayUrl()

    logger.info('system', 'watch_history_page_ready', {
      sessionId: sessionId.value,
      roomId: roomId.value,
      sessionType: resolveWatchHistorySessionType(),
      isScheduled: isScheduled.value,
      isLive: isLive.value,
      isReplay: isReplayForActions.value,
      playUrlReady: !!playUrl.value
    })

    // 进入页面即记录一次，确保预告/直播/回放都能进入观看历史
    await recordWatchHistorySnapshot('enter', 0)

    // 并行加载其他数据（brands 需要在 tabs 注入前准备好）
    console.log('🔄 [onLoad] 准备加载 stats/brands/tabs', { roomId: roomId.value, sessionId: sessionId.value })
    await Promise.all([loadStats(), loadRoomBrands()])
    console.log('🔄 [onLoad] stats/brands 完成，开始加载 tabs')
    await loadRoomFunctionalTabs()
    console.log('🔄 [onLoad] tabs 加载完成')
    
    if (isLive.value) startStatsTimer()
  } catch (err) {
    logger.error('system', '数据加载失败', { error: err, sessionId: sessionId.value })
    error.value = error.value || '加载失败，请稍后重试'
  }
})

/**
 * 页面显示
 */
onShow(() => {
  // 页面显示时刷新统计数据
  if (sessionId.value && isLive.value) {
    loadStats()
    startStatsTimer()
  }
})

/**
 * 页面隐藏
 */
onHide(() => {
  // 页面隐藏时停止定时器
  void flushWatchRecord('hide')
  stopStatsTimer()
})

/**
 * 组件卸载
 */
onUnmounted(() => {
  void flushWatchRecord('unmounted')
  stopStatsTimer()
  // 清除从首页传递过来的房间数据（避免数据残留）
  roomStore.clearSelectedRoomFromHome()
})
</script>

<style lang="scss" scoped>
/* 不在 scoped 里 import uni.scss：:root 会被编译成 .data-v-xxx:root，微信里变量失效 */
.live-view-page {
  height: 100vh;
  width: 100%;
  background: linear-gradient(180deg, #fcfcfc 0%, #f5f5f5 100%);
  color: #333333;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.live-body-scroll {
  flex: 1 1 auto;
  min-height: 0;
  height: 0;
  width: 100%;
  box-sizing: border-box;
}

.live-body-spacer {
  width: 100%;
  height: calc(120rpx + constant(safe-area-inset-bottom));
  height: calc(120rpx + env(safe-area-inset-bottom));
  flex-shrink: 0;
}

.live-tabs-section {
  width: 100%;
  background: #ffffff;
  border-top: 1px solid #ebeef5;
  box-sizing: border-box;
}

/* StickyTabPager styleIsolation=shared：Tab 条在外层 scroll-view 内吸顶 */
.live-tabs :deep(.stp-tabs) {
  position: sticky;
  top: 0;
  z-index: 20;
}

.player-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, var(--color-surface-light) 0%, var(--color-background) 100%);
  width: 100%;
  box-sizing: border-box;
}

.player-native-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.player-native-tools__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.player-native-tools__label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.player-native-tools__value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 600;
}

.player-native-tools__btn {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border: 1px solid var(--color-primary-soft-strong);
}

.intro-card {
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.intro-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.intro-avatar {
  width: 44px;
  height: 44px;
  border-radius: 22px;
  background: var(--color-bg-tertiary);
}

.intro-avatar--placeholder {
  background: linear-gradient(90deg, var(--color-bg-tertiary) 0%, var(--color-border-light) 50%, var(--color-bg-tertiary) 100%);
}

.intro-meta {
  flex: 1;
  min-width: 0;
}

.intro-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.intro-subtitle {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.intro-action {
  font-size: 12px;
  color: var(--color-primary);
  padding: 6px 10px;
  border-radius: var(--border-radius-full);
  background: var(--color-primary-soft);
}

.intro-body {
  margin-top: 10px;
}

.intro-text {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 22px;
}

.intro-text.is-collapsed {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  overflow: hidden;
}

.intro-toggle {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 8px;
}

.intro-toggle__text {
  font-size: 12px;
  color: var(--color-primary);
}

.intro-images {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.intro-image {
  width: 100%;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
}

.brand-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.expert-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.expert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border-radius: 0;
  background: transparent;
  border-bottom: 1px solid var(--color-border);
}

.expert-item:last-child {
  border-bottom: none;
}

.expert-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
}

.expert-avatar--placeholder {
  background: linear-gradient(90deg, var(--color-bg-tertiary) 0%, var(--color-border-light) 50%, var(--color-bg-tertiary) 100%);
}

.expert-meta {
  flex: 1;
  min-width: 0;
}

.expert-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.expert-sub {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  word-break: break-all;
}

.brand-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border-radius: 0;
  background: transparent;
  border-bottom: 1px solid var(--color-border);
}

.brand-item:last-child {
  border-bottom: none;
}

.brand-logo {
  width: 44px;
  height: 44px;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
}

.brand-logo--placeholder {
  background: linear-gradient(90deg, var(--color-bg-tertiary) 0%, var(--color-border-light) 50%, var(--color-bg-tertiary) 100%);
}

.brand-meta {
  flex: 1;
  min-width: 0;
}

.brand-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.brand-website {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  word-break: break-all;
}

.player-container {
  position: relative;
  width: 100%;
  background-color: #000;
  border-bottom-left-radius: 18px;
  border-bottom-right-radius: 18px;
  overflow: hidden;
  max-height: 420rpx;
  
  // 视频播放器容器（16:9比例）
  &::before {
    content: '';
    display: block;
    padding-top: 50%; // 更紧凑的高度（约 2:1），避免播放器显得过高
  }
}

.video-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.player-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #000;
}

.player-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.placeholder-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
}

.session-info {
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  width: 100%;
  box-sizing: border-box;
}

.session-info__expert--placeholder {
  opacity: 0.96;
}

.session-info__title-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.privacy-chip {
  flex-shrink: 0;
  font-size: 11px;
  line-height: 1.2;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(21, 148, 136, 0.3);
  color: #0f766e;
  background: rgba(21, 148, 136, 0.08);
}

.title {
  flex: 1;
  min-width: 0;
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.description {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.expert-avatar--placeholder {
  background: var(--color-bg-tertiary);
}

.expert-title--placeholder {
  min-height: 14px;
}

.follow-btn--disabled {
  background: var(--color-bg-secondary);
  color: var(--color-text-tertiary);
  border-color: var(--color-border);
}

.skeleton-block {
  position: relative;
  overflow: hidden;
}

.skeleton-block::after {
  content: '';
  position: absolute;
  top: 0;
  left: -60%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent);
  animation: skeletonShimmer 1.2s infinite;
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: var(--color-bg-tertiary);
  position: relative;
  overflow: hidden;
}

.skeleton-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: -60%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent);
  animation: skeletonShimmer 1.2s infinite;
}

.skeleton-line--name {
  width: 120px;
  margin-bottom: 8px;
}

.skeleton-line--title {
  width: 160px;
  height: 10px;
}

@keyframes skeletonShimmer {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(220%);
  }
}

.session-info__meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item--clickable:active {
  opacity: 0.7;
}

.meta-icon {
  font-size: 14px;
  line-height: 1;
}

.meta-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.session-info__expert {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.expert-brief {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.follow-btn {
  padding: 4px 12px;
  border-radius: 16px;
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  font-size: 12px;
}

.follow-btn--active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.session-info__actions {
  margin-top: 12px;
  display: flex;
  background: transparent;
  border-radius: 0;
  overflow: visible;
}

.action-chip {
  flex: 1;
  min-width: 0;
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.action-chip + .action-chip {
  border-left: none;
}

.action-chip:active {
  opacity: 0.7;
}

.action-chip--active {
  background: transparent;
}

.action-chip--like-active {
  background: transparent;
}

.action-icon {
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon__glyph {
  font-size: 18px;
  line-height: 1;
}

.action-icon__img {
  width: 18px;
  height: 18px;
  display: block;
}

.action-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.action-text--active {
  color: var(--color-warning);
  font-weight: 600;
}

.action-text--like-active {
  color: var(--color-danger);
  font-weight: 600;
}

.session-info__tags {
  margin-top: 8px;
}

.tags-row {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tags-toggle {
  padding: 4px 8px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-full);
}

.tags-toggle-text {
  font-size: 12px;
  color: var(--color-primary);
}

.tab-content {
  background: #ffffff;
  color: #333333;
  width: 100%;
  min-height: 240rpx;
  box-sizing: border-box;
  overflow-x: hidden;
}

.section-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160rpx;
  padding: 32rpx 24rpx;
  box-sizing: border-box;
}

.empty-text {
  font-size: 28rpx;
  color: #909399;
  line-height: 1.5;
  text-align: center;
}

.tab-content--message {
  /* 仅一层底垫：盖住 fixed 输入条 + 底栏；外层另有 live-body-spacer，勿再叠 msg-scroll-spacer */
  padding-bottom: calc(280rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(280rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

// ---- 留言区 ----
.message-board-tab {
  display: flex;
  flex-direction: column;
}

.message-list {
  width: 100%;
  padding: 24rpx;
  box-sizing: border-box;
}

.msg-loading,
.msg-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80rpx 0;
}

.msg-loading-text,
.msg-empty-text {
  font-size: 26rpx;
  color: var(--color-text-tertiary);
}

.msg-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;

  .msg-load-more-text {
    font-size: 24rpx;
    color: var(--color-primary);
  }
}

.msg-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 20rpx;
  margin-bottom: 8rpx;
  background: rgba(24, 144, 255, 0.08);
  border-radius: 8rpx;
}

.msg-tip-text {
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.msg-input-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(146rpx + constant(safe-area-inset-bottom));
  bottom: calc(146rpx + env(safe-area-inset-bottom));
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  background: var(--color-surface);
  border-top: 1rpx solid var(--color-border);
}

.msg-login-hint {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(242rpx + constant(safe-area-inset-bottom));
  bottom: calc(242rpx + env(safe-area-inset-bottom));
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 24rpx;
  background: rgba(24, 144, 255, 0.08);
  border-top: 1rpx solid rgba(24, 144, 255, 0.15);
}

.msg-login-hint-text {
  font-size: 24rpx;
  color: var(--color-primary);
}

.msg-input-wrap {
  flex: 1;
  position: relative;
}

.msg-input-mask {
  position: absolute;
  inset: 0;
  z-index: 1;
  border-radius: 32rpx;
}

.msg-input {
  flex: 1;
  height: 64rpx;
  padding: 0 24rpx;
  background: var(--color-bg-secondary);
  border-radius: 32rpx;
  font-size: 28rpx;
  color: var(--color-text-primary);
}

.msg-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  padding: 0 32rpx;
  background: var(--color-primary);
  border-radius: 32rpx;

  .msg-send-text {
    font-size: 26rpx;
    color: #ffffff;
  }

  &.msg-send-disabled {
    opacity: 0.5;
  }
}

.msg-char-count {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(110rpx + constant(safe-area-inset-bottom));
  bottom: calc(110rpx + env(safe-area-inset-bottom));
  z-index: 100;
  display: flex;
  justify-content: flex-end;
  padding: 0 24rpx 8rpx;
  background: var(--color-surface);
}

.msg-char-count-text {
  font-size: 20rpx;
  color: var(--color-text-tertiary);
}

.intro-tab {
  padding: 16px;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.section-content {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.expert-title {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 12px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
  border-radius: var(--border-radius-full);
}

.debug-info {
  view {
    margin: 4px 0;
  }
}

.empty-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 20px;
  background: linear-gradient(180deg, var(--color-surface-light) 0%, var(--color-background) 100%);
  border-top: 1px solid var(--color-border-light);
  
  .placeholder-text {
    color: var(--color-text-tertiary);
    font-size: 14px;
  }
}

.share-sheet {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 1200;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
}

.share-sheet__panel {
  width: 100%;
  background: var(--color-surface, #fff);
  border-radius: 16px 16px 0 0;
  padding: 16px 16px calc(16px + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.share-sheet__title {
  display: block;
  text-align: center;
  font-size: 15px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.share-sheet__actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.share-sheet__btn {
  margin: 0;
  padding: 12px 16px;
  text-align: center;
  font-size: 16px;
  line-height: 1.4;
  color: var(--color-text-primary);
  background: var(--color-surface-light, #f5f5f5);
  border-radius: 10px;
  border: none;
}

.share-sheet__btn--primary {
  color: var(--color-primary);
  background: var(--color-primary-soft, #eef5ff);
}

.share-sheet__btn::after {
  border: none;
}

.share-sheet__cancel {
  margin-top: 12px;
  padding: 12px 16px;
  text-align: center;
  font-size: 16px;
  color: var(--color-text-secondary);
}
</style>

