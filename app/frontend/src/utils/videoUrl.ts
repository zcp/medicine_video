/**
 * 视频URL验证工具函数
 */

/**
 * 验证回放视频URL格式
 * @param url 视频URL
 * @returns 验证结果
 */
export function validatePlaybackUrl(url: string): { valid: boolean; message?: string } {
  // 允许为空
  if (!url || url.trim() === '') {
    return { valid: true };
  }

  const trimmedUrl = url.trim();

  // 1. 基础URL格式验证（使用正则表达式，兼容uni-app环境）
  // URL正则：协议://域名[:端口]/路径
  const urlPattern = /^(https?:\/\/)([a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)*)(:[0-9]+)?(\/[^\s]*)?$/;
  
  if (!urlPattern.test(trimmedUrl)) {
    console.error('❌ [URL验证] URL格式无效:', trimmedUrl);
    return { valid: false, message: '请输入有效的URL地址' };
  }

  // 2. 协议验证（允许http和https，因为内网可能使用http）
  if (!trimmedUrl.startsWith('https://') && !trimmedUrl.startsWith('http://')) {
    console.error('❌ [URL验证] 协议不支持');
    return { valid: false, message: '仅支持HTTP或HTTPS协议' };
  }

  // 3. 文件格式验证（m3u8或mp4，更宽松的检查）
  const lowerUrl = trimmedUrl.toLowerCase();
  const hasM3u8 = lowerUrl.includes('m3u8');
  const hasMp4 = lowerUrl.includes('mp4');
  const hasFlv = lowerUrl.includes('flv');
  const hasTs = lowerUrl.includes('.ts');

  if (!hasM3u8 && !hasMp4 && !hasFlv && !hasTs) {
    console.warn('⚠️ [URL验证] 未检测到常见视频格式，但仍允许通过');
    // 不再强制要求特定格式，只给出警告
  }

  // 4. URL长度限制（防止恶意超长URL）
  if (trimmedUrl.length > 2000) {
    console.error('❌ [URL验证] URL过长');
    return { valid: false, message: 'URL长度不能超过2000字符' };
  }

  console.log('✅ [URL验证] 验证通过:', trimmedUrl);
  return { valid: true };
}

/**
 * 获取视频格式
 * @param url 视频URL
 * @returns 视频格式（m3u8 | mp4 | unknown）
 */
export function getVideoFormat(url: string): 'm3u8' | 'mp4' | 'unknown' {
  if (!url) return 'unknown';
  
  const lowerUrl = url.toLowerCase();
  if (lowerUrl.includes('.m3u8')) return 'm3u8';
  if (lowerUrl.includes('.mp4')) return 'mp4';
  
  return 'unknown';
}

/**
 * 格式化视频URL显示（截断过长的URL）
 * @param url 视频URL
 * @param maxLength 最大显示长度
 * @returns 格式化后的URL
 */
export function formatVideoUrlDisplay(url: string, maxLength: number = 50): string {
  if (!url || url.length <= maxLength) return url;
  
  const start = url.substring(0, maxLength - 10);
  const end = url.substring(url.length - 10);
  
  return `${start}...${end}`;
}
