/**
 * 图片代理工具
 * @description 解决APP端外部图片跨域/防盗链问题
 * 
 * 使用场景：
 * - 专家头像来自外部网站（如 www.fahsysu.org.cn）
 * - uni-app的image组件在APP端无法直接加载外部URL
 * 
 * 实现原理：
 * 1. 使用 uni.downloadFile 下载图片（支持自定义header）
 * 2. 使用 uni.saveFile 保存为永久文件
 * 3. 返回本地文件路径（uni-app 完美支持）
 */

import logger from '@/utils/logger';

// 缓存配置
const CACHE_KEY_PREFIX = 'img_proxy_';
const CACHE_EXPIRE_TIME = 7 * 24 * 60 * 60 * 1000; // 7天过期

// 并发请求控制（避免重复请求同一URL）
const pendingRequests = new Map<string, Promise<string | null>>();

// 配置：是否启用图片代理（测试模式下必须为 true）
const USE_PROXY = true; // 🧪 测试模式：必须保持 true

interface CachedImage {
  filePath: string;  // 🔥 改为存储文件路径（而不是base64）
  timestamp: number;
}

/**
 * 判断是否为外部图片URL
 */
function isExternalUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

/**
 * 转换文件路径为可用的URL格式
 * @description 在不同平台上，uni.saveFile返回的路径格式不同，需要统一处理
 * 
 * **重要**：Android image 组件不支持相对路径，必须转换为 file:// 格式的绝对路径
 */
function normalizeFilePath(filePath: string): string {
  if (!filePath) return filePath;
  
  // 已经是完整URL，直接返回
  if (filePath.startsWith('file://') || filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath;
  }
  
  // APP端：所有路径都需要转换为绝对路径
  // @ts-ignore
  if (typeof plus !== 'undefined' && plus.io && plus.io.convertLocalFileSystemURL) {
    try {
      // 统一转换：相对路径和绝对路径都通过 convertLocalFileSystemURL 处理
      // @ts-ignore
      const absolutePath = plus.io.convertLocalFileSystemURL(filePath);
      
      // convertLocalFileSystemURL 返回的是纯绝对路径（/storage/...），需要添加 file:// 前缀
      if (absolutePath && !absolutePath.startsWith('file://')) {
        const fileUrl = 'file://' + absolutePath;
        logger.info('[ImageProxy] 路径标准化: ' + filePath.substring(0, 30) + '... -> file://...' + absolutePath.substring(absolutePath.length - 20));
        return fileUrl;
      }
      
      return absolutePath;
    } catch (e) {
      logger.error('[ImageProxy] 路径转换失败:', filePath, e);
      // 转换失败时，尝试降级处理
      if (filePath.startsWith('/')) {
        return 'file://' + filePath;
      }
      return filePath; // 实在不行，返回原路径
    }
  }
  
  // 非 APP 环境：直接返回
  return filePath;
}

/**
 * 从缓存中获取图片文件路径
 */
function getFromCache(url: string): string | null {
  try {
    const cacheKey = CACHE_KEY_PREFIX + encodeURIComponent(url);
    const cached = uni.getStorageSync(cacheKey) as CachedImage | null;
    
    if (!cached) return null;
    
    // 检查是否过期
    const now = Date.now();
    if (now - cached.timestamp > CACHE_EXPIRE_TIME) {
      // 过期，删除缓存
      uni.removeStorageSync(cacheKey);
      return null;
    }
    
    // 🔥 转换路径格式（normalizeFilePath 内部会输出转换日志）
    const normalized = normalizeFilePath(cached.filePath);

    // 防御：历史脏缓存可能包含引号等非法字符，命中后会反复加载失败。
    // 发现异常路径时直接清理缓存，触发后续重新下载。
    if (!normalized || normalized.includes('"')) {
      uni.removeStorageSync(cacheKey);
      logger.warn('[ImageProxy] 检测到异常缓存路径，已清理并跳过命中');
      return null;
    }

    return normalized;
  } catch (e) {
    logger.warn('[ImageProxy] 读取缓存失败:', e);
    return null;
  }
}

/**
 * 保存图片文件路径到缓存
 */
function saveToCache(url: string, filePath: string): void {
  try {
    const cacheKey = CACHE_KEY_PREFIX + encodeURIComponent(url);
    const data: CachedImage = {
      filePath,  // 🔥 存储文件路径
      timestamp: Date.now()
    };
    uni.setStorageSync(cacheKey, data);
  } catch (e) {
    logger.warn('[ImageProxy] 保存缓存失败:', e);
  }
}

/**
 * 🔥 使用 uni.downloadFile 下载图片（自动保存为临时文件）
 * 
 * 优势：
 * - 跨平台支持（APP/小程序/H5全平台）
 * - 自动保存为临时文件（无需手动处理文件系统）
 * - 返回tempFilePath可直接给Image组件使用
 * - 避免base64大小限制问题
 */
async function fetchImageAsFile(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    // 🔥 固定的请求头（从 H5 端获取）
    const FIXED_HEADERS = {
      'Referer': 'https://mp.dayilive.com/',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
    };

    // 单行日志：批量图片加载场景避免每张图 10+ 行 console 阻塞主线程
    logger.info('[ImageProxy] 开始下载图片:', url.substring(0, 80));

    uni.downloadFile({
      url: url,  // 🔥 直接请求外部URL（不通过后端代理）
      header: FIXED_HEADERS,  // 🔥 设置自定义请求头
      timeout: 15000,
      
      success: (res: any) => {
        if (res.statusCode !== 200) {
          logger.error('[ImageProxy] ❌ HTTP状态码异常:', res.statusCode, url.substring(0, 80));
          reject(new Error(`HTTP ${res.statusCode}`));
          return;
        }

        if (!res.tempFilePath) {
          logger.error('[ImageProxy] ❌ 未获取到临时文件路径');
          reject(new Error('未获取到临时文件路径'));
          return;
        }

        // 🎉 直接返回临时文件路径（uni-app Image组件完美支持）
        logger.info('[ImageProxy] ✅ 下载成功:', res.statusCode);
        resolve(res.tempFilePath);
      },
      
      fail: (err: any) => {
        logger.error('[ImageProxy] ❌ 下载失败:', err.errMsg, url.substring(0, 80));
        reject(new Error(err.errMsg || '图片下载失败'));
      }
    });
  });
}

/**
 * 代理加载外部图片
 * 
 * @param url 图片URL
 * @param useCache 是否使用缓存（默认true）
 * @returns 本地文件路径，加载失败返回null
 * 
 * @example
 * ```typescript
 * // 在组件中使用
 * const avatarSrc = ref('');
 * 
 * onMounted(async () => {
 *   const proxyUrl = await loadImageWithProxy(props.avatar);
 *   if (proxyUrl) {
 *     avatarSrc.value = proxyUrl;
 *   }
 * });
 * ```
 */
export async function loadImageWithProxy(
  url: string,
  useCache: boolean = true
): Promise<string | null> {
  // 空URL
  if (!url) return null;
  
  // 本地图片（/static/xxx）直接返回
  if (!isExternalUrl(url)) {
    return url;
  }
  
  // ⚠️ 降级模式：代理未启用时直接返回原始URL
  // 注意：APP端可能无法加载，但不会阻塞渲染
  if (!USE_PROXY) {
    logger.warn('[ImageProxy] 代理未启用，直接返回原始URL（可能无法加载）');
    return url;
  }
  
  // 🔥 新缓存策略：使用 storage 缓存 savedFilePath（永久保存的文件路径）
  if (useCache) {
    const cached = getFromCache(url);
    if (cached) {
      // 缓存命中，直接返回（normalizeFilePath 已经输出转换日志）
      logger.info('[ImageProxy] ✅ 缓存命中');
      return cached;
    }
  }
  
  // 检查是否已有相同URL的请求正在进行
  const existing = pendingRequests.get(url);
  if (existing) {
    logger.info('[ImageProxy] 复用进行中的请求');
    return existing;
  }
  
  // 创建新的请求Promise
  const promise = (async () => {
    try {
      logger.info('[ImageProxy] 开始下载图片:', url.substring(0, 50) + '...');
      
      // 🔥 使用 uni.downloadFile 下载图片（返回临时文件路径）
      const tempFilePath = await fetchImageAsFile(url);
      
      // 🔥 使用 uni.saveFile 保存为永久文件（避免被系统清理）
      let savedFilePath = tempFilePath;
      if (useCache) {
        try {
          const saveResult = await new Promise<string>((resolve, reject) => {
            uni.saveFile({
              tempFilePath: tempFilePath,
              success: (res: any) => {
                console.log('[ImageProxy] 💾 文件已永久保存:', res.savedFilePath);
                resolve(res.savedFilePath);
              },
              fail: (err: any) => {
                console.warn('[ImageProxy] ⚠️ 永久保存失败，使用临时文件:', err.errMsg);
                resolve(tempFilePath);  // 回退到临时文件
              }
            });
          });
          savedFilePath = saveResult;
          
          // 缓存文件路径到storage
          saveToCache(url, savedFilePath);
          logger.info('[ImageProxy] 文件路径已缓存');
        } catch (e) {
          logger.warn('[ImageProxy] 保存文件失败，使用临时文件:', e);
        }
      }
      
      // 🔥 转换路径格式为可用的URL（确保 image 组件能正确加载）
      const normalizedPath = normalizeFilePath(savedFilePath);
      
      logger.info('[ImageProxy] ✅ 图片加载成功，返回路径:', normalizedPath.substring(0, 80));
      return normalizedPath;
    } catch (e: any) {
      logger.error('[ImageProxy] ❌ 图片加载失败:', e.message);
      return null;
    } finally {
      // 请求完成，从pending列表中移除
      pendingRequests.delete(url);
    }
  })();
  
  // 添加到pending列表
  pendingRequests.set(url, promise);
  
  return promise;
}

/**
 * 批量代理加载图片（用于列表场景）
 * 
 * @param urls 图片URL数组
 * @param concurrency 并发数（默认3）
 * @returns base64数组（与输入数组顺序一致，加载失败的为null）
 */
export async function loadImagesWithProxy(
  urls: string[],
  concurrency: number = 3
): Promise<(string | null)[]> {
  const results: (string | null)[] = new Array(urls.length).fill(null);
  
  // 分批并发加载
  for (let i = 0; i < urls.length; i += concurrency) {
    const batch = urls.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(url => loadImageWithProxy(url))
    );
    
    // 填充结果
    batchResults.forEach((result, index) => {
      results[i + index] = result;
    });
  }
  
  return results;
}

/**
 * 清除图片缓存
 * 
 * @param url 要清除的图片URL，不传则清除所有图片缓存
 */
export function clearImageCache(url?: string): void {
  try {
    if (url) {
      // 清除指定URL的缓存
      const cacheKey = CACHE_KEY_PREFIX + encodeURIComponent(url);
      uni.removeStorageSync(cacheKey);
      logger.info('[ImageProxy] 已清除图片缓存:', url);
    } else {
      // 清除所有图片缓存
      const { keys } = uni.getStorageInfoSync();
      keys.forEach(key => {
        if (key.startsWith(CACHE_KEY_PREFIX)) {
          uni.removeStorageSync(key);
        }
      });
      logger.info('[ImageProxy] 已清除所有图片缓存');
    }
  } catch (e) {
    logger.error('[ImageProxy] 清除缓存失败:', e);
  }
}

/**
 * 获取缓存统计信息
 */
export function getImageCacheStats(): { count: number; size: string } {
  try {
    const { keys, currentSize } = uni.getStorageInfoSync();
    const cacheKeys = keys.filter(key => key.startsWith(CACHE_KEY_PREFIX));
    
    return {
      count: cacheKeys.length,
      size: `${(currentSize / 1024).toFixed(2)} KB`
    };
  } catch (e) {
    return { count: 0, size: '0 KB' };
  }
}
