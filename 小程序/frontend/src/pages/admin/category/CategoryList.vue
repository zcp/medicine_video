<!--
 * CategoryList - 兼容跳转壳（旧「科室分类管理」）
 * 运营面已迁至专家分类管理；保留路由避免微信开发者工具/旧深链 ENOENT
 -->
<template>
  <view class="wrap">
    <text class="tip">科室分类已并入「专家分类管理」，正在跳转…</text>
  </view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  uni.redirectTo({
    url: '/pages/admin/expertDepartment/ExpertDepartmentList',
    fail: () => {
      uni.reLaunch({ url: '/pages/admin/expertDepartment/ExpertDepartmentList' })
    }
  })
})
</script>

<style lang="scss" scoped>
.wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--color-bg-secondary, #f5f5f5);
}
.tip {
  font-size: 14px;
  color: var(--color-text-secondary, #909399);
}
</style>
