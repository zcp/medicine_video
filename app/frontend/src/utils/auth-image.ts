import { BASE_API_URL } from '@/constants/api';
import { getToken } from '@/store/auth';

const blobUrlCache: Map<string, string> = new Map();

function toAbsoluteUrl(url: string): string {
  if (!url) return '';
  if (/^https?:\/\//.test(url)) return url;
  const base = BASE_API_URL.replace(/\/+$/, '');
  const origin = base.replace(/\/api\/.*/, '');
  return origin + (url.startsWith('/') ? url : '/' + url);
}

export function needsAuthForMedia(url: string): boolean {
  const abs = toAbsoluteUrl(url);
  // 需要鉴权的典型路径：/media/ 开头，或云端主机名
  try {
    const u = new URL(abs);
    return u.pathname.startsWith('/media/');
  } catch {
    return true;
  }
}

export async function fetchAuthorizedImageBlobUrl(url: string): Promise<string> {
  const abs = toAbsoluteUrl(url);
  if (blobUrlCache.has(abs)) return blobUrlCache.get(abs)!;
  const token = getToken();
  const resp = await fetch(abs, {
    method: 'GET',
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
    },
    credentials: 'include',
    mode: 'cors',
  });
  if (!resp.ok) {
    throw new Error(`Image fetch failed: ${resp.status}`);
  }
  const ctype = resp.headers.get('content-type') || '';
  if (!/^image\//i.test(ctype)) {
    console.warn('[auth-image] unexpected content-type for media', { url: abs, status: resp.status, contentType: ctype });
  }
  const blob = await resp.blob();
  const blobUrl = URL.createObjectURL(blob);
  blobUrlCache.set(abs, blobUrl);
  return blobUrl;
}

export function revokeAuthorizedImage(url: string) {
  const abs = toAbsoluteUrl(url);
  const blobUrl = blobUrlCache.get(abs);
  if (blobUrl) {
    URL.revokeObjectURL(blobUrl);
    blobUrlCache.delete(abs);
  }
}

