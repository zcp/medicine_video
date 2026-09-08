<template>
  <el-container class="admin-layout">
    <!-- 顶部全局导航 (Header) -->
    <el-header class="header">
      <div class="header-left">
        <el-space :size="24">
          <div class="logo-title">Med-Scholar的直播间</div>
          <el-menu
            :default-active="activeTopMenu"
            mode="horizontal"
            background-color="#2b2f3a"
            text-color="#fff"
            active-text-color="#ffd04b"
            :ellipsis="false"
          >
            <el-menu-item index="home">首页</el-menu-item>
            <el-menu-item index="live">直播</el-menu-item>
            <el-menu-item index="marketing">营销</el-menu-item>
            <el-menu-item index="content">内容</el-menu-item>
            <el-menu-item index="product">商品</el-menu-item>
            <el-menu-item index="trade">交易</el-menu-item>
            <el-menu-item index="user">用户</el-menu-item>
            <el-menu-item index="data">数据</el-menu-item>
            <el-menu-item index="wecom">企微</el-menu-item>
          </el-menu>
          <el-dropdown>
            <span class="el-dropdown-link">
              社区团购<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>功能一</el-dropdown-item>
                <el-dropdown-item>功能二</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-space>
      </div>
      <div class="header-right">
        <el-space :size="16">
          <el-input placeholder="搜索功能与帮助" :prefix-icon="Search" />
          <el-tooltip content="帮助"><el-button link :icon="QuestionFilled" /></el-tooltip>
          <el-tooltip content="书签"><el-button link :icon="Collection" /></el-tooltip>
          <el-tooltip content="下载"><el-button link :icon="Download" /></el-tooltip>
          <el-tooltip content="通知"><el-button link :icon="Bell" /></el-tooltip>
          <el-tooltip content="刷新"><el-button link :icon="Refresh" /></el-tooltip>
          <el-dropdown>
            <el-avatar :icon="UserFilled" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-space>
      </div>
    </el-header>

    <el-container class="main-container">
      <!-- 左侧边栏 (SideNav) -->
      <el-aside width="220px" class="sider">
        <el-scrollbar>
          <el-menu :default-active="activeSideMenu" class="side-menu" router>
            <el-menu-item index="/pages/room/new/RoomCreate">
              <el-icon><Plus /></el-icon>
              <span>新建直播</span>
            </el-menu-item>
            <el-menu-item index="/pages/room/new/RoomList">
              <el-icon><Monitor /></el-icon>
              <span>直播管理</span>
            </el-menu-item>
            <el-sub-menu index="department">
              <template #title>
                <el-icon><Collection /></el-icon>
                <span>科室管理</span>
              </template>
              <el-menu-item index="/pages/h5/department/DepartmentManage">
                <el-icon><List /></el-icon>
                <span>科室列表</span>
              </el-menu-item>
              <el-menu-item index="/pages/h5/department/DepartmentMerge">
                <el-icon><Share /></el-icon>
                <span>合并科室</span>
              </el-menu-item>
              <el-menu-item index="/pages/h5/department/UnmappedExperts">
                <el-icon><Warning /></el-icon>
                <span>未映射专家</span>
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/pages/h5/expert/ExpertCreate">
              <el-icon><User /></el-icon>
              <span>创建专家</span>
            </el-menu-item>
            <el-menu-item index="channel-management" @click="handleComingSoon">
              <el-icon><VideoPlay /></el-icon>
              <span>频道管理</span>
            </el-menu-item>
            <el-menu-item index="image-live" @click="handleComingSoon">
              <el-icon><Picture /></el-icon>
              <span>图片直播</span>
            </el-menu-item>
            <el-menu-item index="software-download" @click="handleComingSoon">
              <el-icon><Download /></el-icon>
              <span>软件下载</span>
            </el-menu-item>
            <el-menu-item index="general-settings" @click="handleComingSoon">
              <el-icon><Setting /></el-icon>
              <span>通用设置</span>
            </el-menu-item>
            <el-menu-item index="multi-channel" @click="handleComingSoon">
              <el-icon><Share /></el-icon>
              <span>多渠道分发</span>
            </el-menu-item>
            <el-menu-item index="live-console">
              <el-icon><Platform /></el-icon>
              <span>直播中控台</span>
              <el-tag type="danger" size="small" class="menu-tag">NEW</el-tag>
            </el-menu-item>
            <el-menu-item index="execution-service">
              <el-icon><Tools /></el-icon>
              <span>执行服务</span>
              <el-tag type="warning" size="small" class="menu-tag">HOT</el-tag>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <el-scrollbar>
          <slot />
        </el-scrollbar>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  ArrowDown,
  Search,
  QuestionFilled,
  Collection,
  Download,
  Bell,
  Refresh,
  UserFilled,
  Plus,
  Monitor,
  User,
  List,
  Warning,
  VideoPlay,
  Picture,
  Setting,
  Share,
  Platform,
  Tools
} from '@element-plus/icons-vue';

const route = useRoute();

const activeTopMenu = computed(() => 'live'); // 顶部菜单暂时固定
const activeSideMenu = computed(() => route.path);

const handleComingSoon = () => {
  ElMessage.info('功能待开发，敬请期待');
};
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.header {
  height: 64px;
  padding: 0 24px;
  background-color: #2b2f3a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.main-container {
  height: calc(100vh - 64px);
}

.sider {
  background-color: #fff;
  height: 100%;
}

.side-menu {
  border-right: none;
  height: 100%;
}

.main-content {
  background-color: #f0f2f5;
  padding: 24px;
  left: 250px;
}

/* Ensure scrollbars take full height inside their containers */
.sider .el-scrollbar,
.main-content .el-scrollbar {
  height: 100%;
}
:deep(.sider .el-scrollbar__view),
:deep(.main-content .el-scrollbar__view) {
  height: 100%;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
}

.logo-title {
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.el-dropdown-link {
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.menu-tag {
  margin-left: 8px;
}
</style>