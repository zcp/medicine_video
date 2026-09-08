/**
 * 安全工具模块
 * 提供数据脱敏、XSS防护、URL校验等安全功能
 * 遵循《直播SaaS平台移动端前端设计文档.md》第4章安全规范
 */

import { PHONE_REGEX, ID_CARD_REGEX, EMAIL_REGEX, SENSITIVE_FIELD_KEYS } from '@/common/constants'

/**
 * 手机号脱敏
 * @param phone - 手机号
 * @returns 脱敏后的手机号（保留前3后4位）
 * @example maskPhone('13812345678') // '138****5678'
 */
export function maskPhone(phone: string | null | undefined): string {
  if (!phone) return ''
  const phoneStr = String(phone).trim()
  if (!PHONE_REGEX.test(phoneStr)) return phoneStr
  return phoneStr.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 身份证号脱敏
 * @param idCard - 身份证号
 * @returns 脱敏后的身份证号（保留前3后4位）
 * @example maskIdCard('420102199001011234') // '420***********1234'
 */
export function maskIdCard(idCard: string | null | undefined): string {
  if (!idCard) return ''
  const idStr = String(idCard).trim()
  if (!ID_CARD_REGEX.test(idStr)) return idStr
  return idStr.replace(/^(.{3}).*(.{4})$/, '$1***********$2')
}

/**
 * 邮箱脱敏
 * @param email - 邮箱地址
 * @returns 脱敏后的邮箱（保留前2位和@后全部）
 * @example maskEmail('example@test.com') // 'ex****@test.com'
 */
export function maskEmail(email: string | null | undefined): string {
  if (!email) return ''
  const emailStr = String(email).trim()
  if (!EMAIL_REGEX.test(emailStr)) return emailStr
  const [localPart, domain] = emailStr.split('@')
  if (!localPart || !domain) return emailStr
  const maskedLocal = localPart.length <= 2 
    ? localPart 
    : `${localPart.substring(0, 2)}****`
  return `${maskedLocal}@${domain}`
}

/**
 * 患者姓名脱敏
 * 支持中文复姓处理（68个常见复姓）
 * @param name - 患者姓名
 * @returns 脱敏后的姓名（保留姓氏，名字用*替代）
 * @example maskPatientName('张三') // '张*'
 * @example maskPatientName('欧阳修') // '欧阳*'
 */
export function maskPatientName(name: string | null | undefined): string {
  if (!name) return ''
  const nameStr = String(name).trim()
  if (nameStr.length === 0) return ''
  
  // 68个常见复姓列表
  const compoundSurnames = [
    '欧阳', '太史', '端木', '上官', '司马', '东方', '独孤', '南宫', '万俟', '闻人',
    '夏侯', '诸葛', '尉迟', '公羊', '赫连', '澹台', '皇甫', '宗政', '濮阳', '公冶',
    '太叔', '申屠', '公孙', '慕容', '仲孙', '钟离', '长孙', '宇文', '城司', '司徒',
    '鲜于', '司空', '汝嫣', '闾丘', '子车', '亓官', '司寇', '巫马', '公西', '颛孙',
    '壤驷', '公良', '漆雕', '乐正', '宰父', '谷梁', '拓跋', '夹谷', '轩辕', '令狐',
    '段干', '百里', '呼延', '东郭', '南门', '羊舌', '微生', '公户', '公玉', '公仪',
    '梁丘', '公仲', '公上', '公门', '公山', '公坚', '左丘', '公伯'
  ]
  
  // 检查是否为复姓
  for (const surname of compoundSurnames) {
    if (nameStr.startsWith(surname)) {
      return nameStr.length === surname.length 
        ? nameStr 
        : `${surname}${'*'.repeat(nameStr.length - surname.length)}`
    }
  }
  
  // 单姓处理
  if (nameStr.length === 1) {
    return nameStr
  } else if (nameStr.length === 2) {
    return `${nameStr[0]}*`
  } else {
    return `${nameStr[0]}${'*'.repeat(nameStr.length - 1)}`
  }
}

/**
 * HTML转义（XSS防护）
 * @param html - 需要转义的HTML字符串
 * @returns 转义后的安全字符串
 * @example sanitizeHtml('<script>alert("xss")</script>') // '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
 */
export function sanitizeHtml(html: string | null | undefined): string {
  if (!html) return ''
  const htmlStr = String(html)
  const escapeMap: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  }
  return htmlStr.replace(/[&<>"'/]/g, (char) => escapeMap[char] || char)
}

/**
 * URL校验（仅允许http/https协议）
 * @param url - 需要校验的URL
 * @returns 是否为合法的http/https URL
 * @example validateUrl('https://example.com') // true
 * @example validateUrl('javascript:alert(1)') // false
 */
export function validateUrl(url: string | null | undefined): boolean {
  if (!url) return false
  try {
    const urlStr = String(url).trim()
    const parsedUrl = new URL(urlStr)
    return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:'
  } catch {
    return false
  }
}

/**
 * 对象深度递归脱敏
 * 自动识别敏感字段并进行脱敏处理
 * @param obj - 需要脱敏的对象
 * @returns 脱敏后的对象（深拷贝）
 */
export function desensitizeObject(obj: Record<string, any> | null | undefined): Record<string, any> | null | undefined {
  if (!obj || typeof obj !== 'object') return obj
  if (Array.isArray(obj)) return desensitizeArray(obj)
  
  const result: Record<string, any> = {}
  
  for (const key in obj) {
    if (!Object.prototype.hasOwnProperty.call(obj, key)) continue
    
    const value = obj[key]
    const lowerKey = key.toLowerCase()
    
    // 检查是否为敏感字段
    const isSensitive = SENSITIVE_FIELD_KEYS.some(
      sensitiveKey => lowerKey.includes(sensitiveKey.toLowerCase())
    )
    
    if (isSensitive && typeof value === 'string') {
      // 根据字段名选择脱敏方式
      if (lowerKey.includes('phone') || lowerKey.includes('mobile')) {
        result[key] = maskPhone(value)
      } else if (lowerKey.includes('idcard')) {
        result[key] = maskIdCard(value)
      } else if (lowerKey.includes('email')) {
        result[key] = maskEmail(value)
      } else if (lowerKey.includes('patientname') || lowerKey.includes('patient_name')) {
        result[key] = maskPatientName(value)
      } else {
        // 默认脱敏：保留前2后2位
        result[key] = value.length <= 4 
          ? '****' 
          : `${value.substring(0, 2)}****${value.substring(value.length - 2)}`
      }
    } else if (value !== null && typeof value === 'object') {
      // 递归处理嵌套对象或数组
      result[key] = Array.isArray(value) 
        ? desensitizeArray(value) 
        : desensitizeObject(value)
    } else {
      result[key] = value
    }
  }
  
  return result
}

/**
 * 数组深度递归脱敏
 * @param arr - 需要脱敏的数组
 * @returns 脱敏后的数组（深拷贝）
 */
export function desensitizeArray(arr: any[] | null | undefined): any[] | null | undefined {
  if (!arr || !Array.isArray(arr)) return arr
  
  return arr.map(item => {
    if (item === null || item === undefined) {
      return item
    } else if (Array.isArray(item)) {
      return desensitizeArray(item)
    } else if (typeof item === 'object') {
      return desensitizeObject(item)
    } else {
      return item
    }
  })
}

/**
 * 自动脱敏（智能识别数据类型）
 * @param data - 任意类型的数据
 * @returns 脱敏后的数据
 */
export function autoDesensitize(data: any): any {
  if (data === null || data === undefined) {
    return data
  } else if (Array.isArray(data)) {
    return desensitizeArray(data)
  } else if (typeof data === 'object') {
    return desensitizeObject(data)
  } else {
    return data
  }
}

// ==================== 图片占位符功能 ====================

/**
 * 默认封面占位符
 */
export const DEFAULT_COVER_PLACEHOLDER = 'https://via.placeholder.com/1000x562?text=No+Cover'

/**
 * 默认头像占位符
 */
export const DEFAULT_AVATAR_PLACEHOLDER = 'https://via.placeholder.com/200x200?text=No+Avatar'

/**
 * 可信任的图片域名白名单（生产环境强制校验）
 */
export const TRUSTED_IMAGE_DOMAINS = [
  'mp.dayilive.com',
  'cdn.dayilive.com',
  'static.dayilive.com',
  'via.placeholder.com' // 占位符服务
]

/**
 * 获取安全的图片URL
 * @param url - 原始图片URL
 * @param type - 图片类型（'cover' | 'avatar'）
 * @returns 安全的图片URL或占位符
 * @example
 * const coverUrl = getImageUrl(session.cover_url, 'cover');
 * const avatarUrl = getImageUrl(expert.avatar, 'avatar');
 */
export function getImageUrl(url: string | undefined | null, type: 'cover' | 'avatar' = 'cover'): string {
  // 如果URL为空，返回对应的占位符
  if (!url || url.trim() === '') {
    return type === 'cover' ? DEFAULT_COVER_PLACEHOLDER : DEFAULT_AVATAR_PLACEHOLDER
  }

  // 安全校验：禁止 data:image/svg（可能包含 script）
  if (url.startsWith('data:image/svg')) {
    console.warn('[Security] 禁止使用 data:image/svg，可能存在 XSS 风险')
    return type === 'cover' ? DEFAULT_COVER_PLACEHOLDER : DEFAULT_AVATAR_PLACEHOLDER
  }

  // 复用已有的 validateUrl 函数进行基础校验
  if (!validateUrl(url)) {
    console.warn('[Security] 图片URL校验失败:', url)
    return type === 'cover' ? DEFAULT_COVER_PLACEHOLDER : DEFAULT_AVATAR_PLACEHOLDER
  }

  // 生产环境：强制域名白名单校验
  if (import.meta.env.PROD) {
    try {
      const urlObj = new URL(url)
      const hostname = urlObj.hostname

      // 检查是否在白名单中
      const isTrusted = TRUSTED_IMAGE_DOMAINS.some(domain => {
        return hostname === domain || hostname.endsWith('.' + domain)
      })

      if (!isTrusted) {
        console.warn('[Security] 图片域名不在白名单中:', hostname)
        return type === 'cover' ? DEFAULT_COVER_PLACEHOLDER : DEFAULT_AVATAR_PLACEHOLDER
      }
    } catch (error) {
      console.error('[Security] 解析图片URL失败:', error)
      return type === 'cover' ? DEFAULT_COVER_PLACEHOLDER : DEFAULT_AVATAR_PLACEHOLDER
    }
  }

  // 通过所有校验，返回原始URL
  return url
}
