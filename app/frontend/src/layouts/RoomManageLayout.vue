<template>
  <el-container class="room-manage-layout" direction="vertical">
    <!-- 顶部操作栏（全宽） -->
    <el-header class="top-header">
      <div class="top-toolbar">
        <div class="toolbar-left">
          <el-button type="text" :icon="ArrowLeft" class="back-button" @click="goBack">返回话题列表</el-button>
        </div>
        <div class="toolbar-center">
          <el-space :size="16">
            <i class="divider-vert" />
            <slot name="top-left" />
          </el-space>
        </div>
        <div class="toolbar-right">
          <el-space :size="16">
            <el-button link :icon="Platform" size="small">
              中控台
              <el-tag type="danger" size="small" style="margin-left: 4px;">NEW</el-tag>
            </el-button>
            <el-button link :icon="Upload" size="small">推送</el-button>
            <el-button link :icon="View" size="small">预览</el-button>
            <el-button link :icon="QuestionFilled" size="small">帮助</el-button>
            <el-button link :icon="Download" size="small">下载</el-button>
            <el-button type="primary" :icon="Share">分享</el-button>
            <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
          </el-space>
        </div>
      </div>
    </el-header>

    <!-- 顶部下方的三栏布局区域 -->
    <el-container class="inner-container">
      <!-- 左侧主导航栏（一级） -->
      <el-aside width="100px" class="left-sidebar">

      <!-- 主菜单（显式插入图标，兼容不支持 :icon 属性的环境） -->
      <el-menu
        :default-active="activeMenu"
        class="main-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="live-interaction">
          <el-icon><Star /></el-icon>
          <span>常用功能</span>
        </el-menu-item>
        <el-menu-item index="basic-info">
          <el-icon><Document /></el-icon>
          <span>基本信息</span>
        </el-menu-item>
        <el-menu-item index="live-interaction">
          <el-icon><ChatDotRound /></el-icon>
          <span>直播互动</span>
        </el-menu-item>
        <el-menu-item index="live-marketing">
          <el-icon><Promotion /></el-icon>
          <span>直播营销</span>
        </el-menu-item>
        <el-menu-item index="data-analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>数据分析</span>
        </el-menu-item>
        <el-menu-item index="live-decoration">
          <el-icon><Star /></el-icon>
          <span>直播装修</span>
        </el-menu-item>
        <el-menu-item index="broadcast-settings">
          <el-icon><VideoCamera /></el-icon>
          <span>开播设置</span>
        </el-menu-item>
        <el-menu-item index="content-summary">
          <el-icon><DocumentCopy /></el-icon>
          <span>内容总结</span>
        </el-menu-item>
        <el-menu-item index="marketing-automation">
          <el-icon><MagicStick /></el-icon>
          <span>营销自动化</span>
        </el-menu-item>
      </el-menu>
      </el-aside>

      <!-- 左侧详细功能栏（二级，原右侧） -->
      <el-aside width="120px" class="detail-sidebar">
      <el-menu
        :default-active="activeSubMenu"
        class="sub-menu"
        @select="handleSubMenuSelect"
      >
        <el-menu-item index="home" class="active-item">
          设置首页
        </el-menu-item>
        
        <el-sub-menu index="basic-settings">
          <template #title>
            <span>基本设置</span>
          </template>
          <el-menu-item index="basic-settings-item" @click="goToBasicSettings">基本设置</el-menu-item>
          <el-menu-item index="viewer-settings">观看页设置</el-menu-item>
          <el-menu-item index="ad-settings">广告设置</el-menu-item>
          <el-menu-item index="private-traffic">私域引流</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="live-methods">
          <template #title>
            <span>直播方式</span>
          </template>
          <el-menu-item index="multi-venue" @click="goToMultiVenue">多会场直播</el-menu-item>
          <el-menu-item index="multi-language">多语言直播</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="content-security">
          <template #title>
            <span>内容安全</span>
          </template>
          <el-menu-item index="whitelist">白名单</el-menu-item>
          <el-menu-item index="marquee">跑马灯</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="other">
          <template #title>
            <span>其他</span>
          </template>
          <el-menu-item index="enter-popup">进入弹窗</el-menu-item>
          <el-menu-item index="recommended-topics">推荐话题</el-menu-item>
          <el-menu-item index="page-jump">页面跳转</el-menu-item>
          <el-menu-item index="smart-subtitles">智能字幕</el-menu-item>
          <el-menu-item index="admin-settings">管理员设置</el-menu-item>
        </el-sub-menu>
      </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <!-- 页面内容插槽 -->
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Star,
  Document,
  ChatDotRound,
  Promotion,
  TrendCharts,
  VideoCamera,
  DocumentCopy,
  MagicStick,
  Platform,
  Upload,
  View,
  QuestionFilled,
  Download,
  Share
} from '@element-plus/icons-vue'

// 响应式数据
const activeMenu = ref('basic-info')
const activeSubMenu = ref('home')

// 事件处理
const goBack = () => {
  // 跳转到话题列表页面（RoomList）
  uni.navigateTo({ url: '/pages/room/new/RoomList' })
}

const setHomepage = () => {
  ElMessage.info('设置首页功能待开发，敬请期待')
}

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
  // 根据选中的主菜单更新右侧功能栏
  updateSubMenu(index)
}

const handleSubMenuSelect = (index: string) => {
  activeSubMenu.value = index
  
  // 处理特殊功能点击
  if (index === 'multi-venue') {
    goToMultiVenue()
  } else if (index === 'basic-settings-item') {
    goToBasicSettings()
  } else {
    // 其他功能显示待开发提示
    ElMessage.info('功能待开发，敬请期待')
  }
}

const updateSubMenu = (menuIndex: string) => {
  // 根据主菜单更新右侧功能栏内容
  // 这里可以根据不同主菜单显示不同的子功能
  console.log('更新子菜单:', menuIndex)
}

const goToBasicSettings = () => {
  const roomId = getRoomIdFromRoute()
  if (roomId) {
    uni.navigateTo({
      url: `/pages/room/new/RoomBasicSettings?room_id=${roomId}`
    })
  }
}

const goToMultiVenue = () => {
  const roomId = getRoomIdFromRoute()
  if (roomId) {
    uni.navigateTo({
      url: `/pages/room/new/RoomMultiVenue?room_id=${roomId}`
    })
  }
}

const getRoomIdFromRoute = (): string | null => {
  // 从当前页面路由参数中获取 room_id
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  return currentPage.options?.room_id || null
}
</script>

<style scoped>
.room-manage-layout {
  height: 100vh;
  background-color: #f5f5f5;
  overflow: hidden; /* 禁止页面最外层出现纵向滚动条 */
}

.top-header {
  padding: 0 24px;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  height: auto;
}

.inner-container {
  height: calc(100vh - 64px);
  overflow: hidden; /* 由子区域自行滚动 */
}

.left-sidebar {
  background-color: #ffffff;
  /* 与二级侧边栏的分隔线 */
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  /* 隐藏滚动条但保留滚动能力 */
  -ms-overflow-style: none; /* IE/Edge */
  scrollbar-width: none; /* Firefox */
}

.return-button {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.home-button {
  width: 100%;
  background-color: #409eff;
  border-color: #409eff;
}

.main-menu {
  border: none;
  background-color: transparent;
}

.main-menu .el-menu-item {
  height: 72px;
  line-height: 1.2;
  padding: 10px !important; /* 将四边 padding 统一为 10 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.main-menu .el-menu-item.is-active {
  background-color: #409eff;
  color: #fff;
}

/* 菜单图标置于文字上方并居中 */
.main-menu .el-menu-item .el-icon {
  margin: 0 0 6px 0;
  font-size: 20px;
}

.detail-sidebar {
  background-color: #ffffff;
  /* 与主内容区之间的分隔线 */
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  /* 隐藏滚动条但保留滚动能力 */
  -ms-overflow-style: none; /* IE/Edge */
  scrollbar-width: none; /* Firefox */
}

.sub-menu {
  border: none;
  background-color: transparent;
}

.sub-menu .el-menu-item {
  height: 40px;
  line-height: 40px;
  font-size: 14px;
}

.sub-menu .el-menu-item.is-active {
  background-color: #409eff;
  color: #fff;
}

.active-item {
  background-color: #409eff !important;
  color: #fff !important;
}

.main-content {
  background-color: #ffffff;
  padding: 0;
  height: 100%;
  overflow-y: auto; /* 主内容区域内部滚动 */
}

.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.toolbar-left {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}

.divider-vert {
  display: inline-block;
  width: 1px;
  height: 18px;
  background-color: #e4e7ed;
  margin: 0 16px;
}

.toolbar-center {
  display: flex;
  justify-content: flex-start;
  flex: 1;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

/* 隐藏 webkit 滚动条 */
.left-sidebar::-webkit-scrollbar,
.detail-sidebar::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.back-button {
  margin-right: 12px;
  padding: 0 4px;
}
</style>
