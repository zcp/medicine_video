/**
 * URL / 资源地址相关工具
 * @description 处理媒体URL、图片URL的规范化
 */

/**
 * 小程序 image 不支持 http（开发者工具/真机都会告警或失败）。
 * 这里做一个保守兜底：
 * - http://xxx -> https://xxx
 * - //xxx -> https://xxx
 * - 其它（https、相对路径、本地静态资源）原样返回
 * 
 * ⚠️ 对于外部HTTPS图片（如专家头像），保持原样不做降级处理
 */
export function normalizeImageUrl(url?: string | null): string | null {
  if (!url) return null;
  const trimmed = String(url).trim();
  if (!trimmed) return null;

  if (trimmed.startsWith('//')) return `https:${trimmed}`;
  if (trimmed.startsWith('http://')) {
    // 检测是否为 IPv4 地址（直接用正则，避免 new URL() 在部分移动端运行时不可用）
    const ipv4Match = trimmed.match(/^https?:\/\/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?/);
    if (ipv4Match) {
      const ip = ipv4Match[1];
      const parts = ip.split('.').map(Number);
      const isValidIPv4 = parts.length === 4 && parts.every(p => p >= 0 && p <= 255);
      if (isValidIPv4) {
        console.log('[normalizeImageUrl] ✅ IPv4地址，保持HTTP:', trimmed);
        return trimmed;
      }
    }
    // 非IPv4则升级到HTTPS
    console.log('[normalizeImageUrl] ⚠️ 升级HTTP到HTTPS:', trimmed);
    return `https://${trimmed.slice('http://'.length)}`;
  }
  
  if (trimmed.startsWith('https://')) {
    return trimmed;
  }

  return trimmed;
}

/**
 * 从 API Base URL 推导 origin
 */
function deriveOriginFromBaseApiUrl(raw?: string): string | null {
  const v = (raw || '').trim().replace(/\/+$/, '');
  if (!v) return null;
  try {
    const u = new URL(v);
    return u.origin;
  } catch {
    return null;
  }
}

/**
 * 将后端返回的媒体路径（如 /media/xxx.png）转换为可访问的完整 URL。
 *
 * 优先使用 VITE_MEDIA_BASE_URL（建议配置为域名 origin，例如 https://mp.xxx.com）
 * 否则从 VITE_BASE_API_URL 推导 origin（例如 https://mp.xxx.com/api/core -> https://mp.xxx.com）
 */
export function resolveMediaUrl(path?: string | null): string {
  const trimmed = String(path || '').trim();
  if (!trimmed) return '';

  // APP本地文件、data URI、内容URI 直接透传，避免被错误拼接成网络地址
  if (
    trimmed.startsWith('file://') ||
    trimmed.startsWith('data:') ||
    trimmed.startsWith('content://')
  ) {
    return trimmed;
  }

  // APP本地沙箱路径（uni.saveFile 常见返回）直接透传
  if (trimmed.startsWith('_doc/') || trimmed.startsWith('/_doc/')) {
    return trimmed;
  }

  // 已经是完整URL
  if (/^https?:\/\//i.test(trimmed) || trimmed.startsWith('//')) {
    return normalizeImageUrl(trimmed) || '';
  }

  // 小程序包内静态资源
  if (trimmed.startsWith('/static/') || trimmed.startsWith('static/')) {
    return trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  }

  // 后端返回的相对路径（通常以 /media 或 /uploads 开头）
  const mediaBase = (import.meta as any).env?.VITE_MEDIA_BASE_URL as string | undefined;
  const baseApi = (import.meta as any).env?.VITE_BASE_API_URL as string | undefined;
  
  // ===== 诊断日志 =====
  console.log('[resolveMediaUrl] 🔍 解析路径:', trimmed);
  console.log('[resolveMediaUrl] 📋 import.meta.env.VITE_MEDIA_BASE_URL:', mediaBase);
  console.log('[resolveMediaUrl] 📋 import.meta.env.VITE_BASE_API_URL:', baseApi);
  
  // 获取 origin，如果都没有则使用生产环境兜底
  let origin = (mediaBase || '').trim().replace(/\/+$/, '') || deriveOriginFromBaseApiUrl(baseApi) || '';
  console.log('[resolveMediaUrl] 🌐 推导的 origin:', origin);
  
  // #ifdef APP-PLUS
  // App 模式兜底：如果环境变量都未配置，使用硬编码的生产域名
  if (!origin) {
    origin = 'https://mp.dayilive.com';
    console.warn('[URL] App模式使用兜底域名:', origin);
  }
  // #endif

  const normalizedPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  const full = origin ? `${origin}${normalizedPath}` : normalizedPath;
  console.log('[resolveMediaUrl] 🔗 拼接后的完整URL (normalize前):', full);

  const normalizedFull = normalizeImageUrl(full) || full;
  console.log('[resolveMediaUrl] ✅ 最终URL (normalize后):', normalizedFull);

  return normalizedFull;
}

/**
 * 检查字符串是否为标准UUID格式
 */
export function isValidUUID(id: string | null | undefined): boolean {
  if (!id) return false;
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
}
