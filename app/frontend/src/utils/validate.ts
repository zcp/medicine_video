/**
 * 表单校验工具函数
 * 提供用户名、邮箱、密码等常见字段的校验规则
 */

import { isValidCnPhone } from './phone';

/**
 * 校验用户名格式
 * 规则：2-50字符，仅允许字母、数字、下划线
 * @param username 用户名
 * @returns 是否符合规则
 * @example
 * validateUsername('john_doe123') // true
 * validateUsername('a') // false (太短)
 * validateUsername('user@name') // false (包含特殊字符)
 */
export function validateUsername(username: string): boolean {
  if (!username) return false;
  const regex = /^[a-zA-Z0-9_]{2,50}$/;
  return regex.test(username);
}

/**
 * 校验邮箱格式
 * 规则：标准邮箱格式（xxx@xxx.xxx）
 * @param email 邮箱地址
 * @returns 是否符合规则
 * @example
 * validateEmail('user@example.com') // true
 * validateEmail('invalid-email') // false
 */
export function validateEmail(email: string): boolean {
  if (!email) return false;
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

/**
 * 校验密码强度
 * 规则：至少8位，必须包含大小写字母、数字和特殊字符
 * @param password 密码
 * @returns 是否符合规则
 * @example
 * validatePassword('Test@123') // true
 * validatePassword('test123') // false (缺少大写和特殊字符)
 * validatePassword('Test123') // false (缺少特殊字符)
 */
export function validatePassword(password: string): boolean {
  if (!password || password.length < 8) return false;
  
  // 必须包含大写字母
  const hasUpperCase = /[A-Z]/.test(password);
  // 必须包含小写字母
  const hasLowerCase = /[a-z]/.test(password);
  // 必须包含数字
  const hasNumber = /[0-9]/.test(password);
  // 必须包含特殊字符
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
  
  return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
}

/**
 * 校验手机号格式（中国大陆）
 * 统一委托 src/utils/phone.ts 的 isValidCnPhone（先归一化再匹配，支持 +86/86 前缀、空格、横线）
 * @param phone 手机号
 * @returns 是否符合规则
 * @example
 * validatePhone('13812345678') // true
 * validatePhone('+8613812345678') // true
 * validatePhone('12345678901') // false (不是1开头或第二位不是3-9)
 */
export function validatePhone(phone: string): boolean {
  return isValidCnPhone(phone);
}

/**
 * 校验昵称长度
 * 规则：2-50字符
 * @param nickname 昵称
 * @returns 是否符合规则
 */
export function validateNickname(nickname: string): boolean {
  if (!nickname) return false;
  return nickname.length >= 2 && nickname.length <= 50;
}
