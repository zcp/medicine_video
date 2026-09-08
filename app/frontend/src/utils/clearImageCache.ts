/**
 * 清空图片缓存工具
 * 
 * 使用方法：
 * 1. 在任意页面的 onMounted 中调用
 * 2. 或者在浏览器控制台直接执行
 * 
 * 注意：现在缓存的是文件路径（storage中的img_proxy_*键）
 */

/**
 * 清空所有图片代理缓存（删除storage中的缓存记录）
 */
export function clearImageCache(): number {
  let clearedCount = 0;
  
  try {
    // 获取所有本地存储的key
    const result = uni.getStorageInfoSync();
    const keys = result.keys || [];
    
    console.log('[ClearCache] 本地存储总Key数量:', keys.length);
    
    // 筛选出图片缓存的key（以 img_proxy_ 开头）
    const imageCacheKeys = keys.filter(key => key.startsWith('img_proxy_'));
    
    console.log('[ClearCache] 图片缓存Key数量:', imageCacheKeys.length);
    
    // 删除所有图片缓存
    imageCacheKeys.forEach(key => {
      try {
        uni.removeStorageSync(key);
        clearedCount++;
      } catch (e) {
        console.error('[ClearCache] 删除失败:', key, e);
      }
    });
    
    console.log('[ClearCache] ✅ 清空完成！删除了', clearedCount, '个缓存记录');
    
    uni.showToast({
      title: `已清空 ${clearedCount} 个图片缓存`,
      icon: 'success',
      duration: 2000
    });
    
    return clearedCount;
  } catch (e) {
    console.error('[ClearCache] ❌ 清空失败:', e);
    
    uni.showToast({
      title: '清空缓存失败',
      icon: 'error'
    });
    
    return 0;
  }
}

/**
 * 清空指定URL的缓存
 */
export function clearImageCacheByUrl(url: string): boolean {
  try {
    const cacheKey = 'img_proxy_' + encodeURIComponent(url);
    uni.removeStorageSync(cacheKey);
    
    console.log('[ClearCache] ✅ 已清空指定URL的缓存:', url);
    return true;
  } catch (e) {
    console.error('[ClearCache] ❌ 清空失败:', e);
    return false;
  }
}

/**
 * 查看当前缓存统计
 */
export function getImageCacheStats() {
  try {
    const result = uni.getStorageInfoSync();
    const keys = result.keys || [];
    
    const imageCacheKeys = keys.filter(key => key.startsWith('img_proxy_'));
    
    const stats = {
      totalKeys: keys.length,
      imageCacheCount: imageCacheKeys.length,
      currentSize: result.currentSize || 0,
      limitSize: result.limitSize || 0
    };
    
    console.log('[CacheStats] 缓存统计:', stats);
    console.log('[CacheStats] 图片缓存Keys:', imageCacheKeys.slice(0, 5), '...');
    
    return stats;
  } catch (e) {
    console.error('[CacheStats] ❌ 获取统计失败:', e);
    return null;
  }
}
