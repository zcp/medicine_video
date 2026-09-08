/**
 * 手机号工具函数（与后端 core/phone.py 规则对齐）
 *
 * 统一校验规则：^1[3-9]\d{9}$
 * 统一提交格式：纯 11 位（去除 +86/86 前缀、空格、横线）
 *
 * 接入清单（禁止各页面自写正则）：
 * - 注册页、登录页（验证码/手机号+密码）、一键登录确认页：实时校验
 * - 绑定手机号页：提交前校验 + 提交时携带归一化值
 * - 账号安全页：仅展示掩码，不提供直接编辑
 */

/** 中国大陆手机号正则：1 开头，第二位 3-9，共 11 位 */
const CN_PHONE_PATTERN = /^1[3-9]\d{9}$/;

/**
 * 归一化手机号：去除空白/横线、+86/86 前缀，返回纯 11 位
 * @param phone 原始输入
 * @returns 归一化后的手机号
 * @example
 * normalizeCnPhone('+86 138 0013 8000') // '13800138000'
 * normalizeCnPhone('8613800138000')     // '13800138000'
 */
export function normalizeCnPhone(phone: string): string {
  let value = (phone || '').trim().replace(/\s+/g, '').replace(/-/g, '');
  if (value.startsWith('+86')) {
    value = value.slice(3);
  } else if (value.startsWith('86') && value.length === 13) {
    value = value.slice(2);
  }
  return value;
}

/**
 * 判断手机号是否合法（先归一化再匹配，与后端 validate_cn_phone 一致）
 * @param phone 原始输入
 * @returns 是否合法
 * @example
 * isValidCnPhone('13800138000')      // true
 * isValidCnPhone('+8613800138000')   // true
 * isValidCnPhone('12345678901')      // false（第二位不是 3-9）
 */
export function isValidCnPhone(phone: string): boolean {
  if (!phone) return false;
  return CN_PHONE_PATTERN.test(normalizeCnPhone(phone));
}
