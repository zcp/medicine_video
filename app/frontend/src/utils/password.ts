/**
 * 密码强度计算工具
 * 提供密码强度评估和可视化反馈
 */

import type { PasswordStrength, PasswordStrengthLevel } from '@/types/auth';

/**
 * 密码强度级别枚举（与types保持一致）
 */
export const PasswordStrengthEnum = {
  VeryWeak: 1,
  Weak: 2,
  Medium: 3,
  Strong: 4,
  VeryStrong: 5
} as const;

/**
 * 计算密码强度等级
 * 评分规则：
 * - 长度 ≥ 8位：+1分
 * - 长度 ≥ 12位：+1分
 * - 包含大写字母：+1分
 * - 包含小写字母：+1分
 * - 包含数字：+1分
 * - 包含特殊字符：+1分
 * 总分0-5分，对应5个强度等级
 * 
 * @param password 密码字符串
 * @returns 密码强度对象（包含等级、文本、颜色、分数）
 * @example
 * calculatePasswordStrengthLevel('Test@123')
 * // 返回: { level: 4, text: '强', color: '#84CC16', score: 4 }
 */
export function calculatePasswordStrengthLevel(password: string): PasswordStrength {
  let score = 0;
  
  // 1. 长度检查（最多2分）
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  
  // 2. 包含大写字母（1分）
  if (/[A-Z]/.test(password)) score++;
  
  // 3. 包含小写字母（1分）
  if (/[a-z]/.test(password)) score++;
  
  // 4. 包含数字（1分）
  if (/[0-9]/.test(password)) score++;
  
  // 5. 包含特殊字符（1分）
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score++;
  
  // 限制最大分数为5
  score = Math.min(score, 5);
  
  // 根据分数返回强度对象
  const strengthMap: Record<number, PasswordStrength> = {
    0: { 
      level: PasswordStrengthEnum.VeryWeak as PasswordStrengthLevel, 
      text: '密码太短', 
      color: '#EF4444', 
      score: 0 
    },
    1: { 
      level: PasswordStrengthEnum.VeryWeak as PasswordStrengthLevel, 
      text: '很弱', 
      color: '#EF4444', 
      score: 1 
    },
    2: { 
      level: PasswordStrengthEnum.Weak as PasswordStrengthLevel, 
      text: '弱', 
      color: '#F59E0B', 
      score: 2 
    },
    3: { 
      level: PasswordStrengthEnum.Medium as PasswordStrengthLevel, 
      text: '中', 
      color: '#EAB308', 
      score: 3 
    },
    4: { 
      level: PasswordStrengthEnum.Strong as PasswordStrengthLevel, 
      text: '强', 
      color: '#84CC16', 
      score: 4 
    },
    5: { 
      level: PasswordStrengthEnum.VeryStrong as PasswordStrengthLevel, 
      text: '很强', 
      color: '#22C55E', 
      score: 5 
    },
  };
  
  return strengthMap[score];
}

/**
 * 获取密码强度建议
 * @param password 密码字符串
 * @returns 改进建议数组
 * @example
 * getPasswordSuggestions('test123')
 * // 返回: ['添加大写字母', '添加特殊字符', '建议长度达到12位以上']
 */
export function getPasswordSuggestions(password: string): string[] {
  const suggestions: string[] = [];
  
  if (password.length < 8) {
    suggestions.push('密码长度至少8位');
  } else if (password.length < 12) {
    suggestions.push('建议长度达到12位以上');
  }
  
  if (!/[A-Z]/.test(password)) {
    suggestions.push('添加大写字母（A-Z）');
  }
  
  if (!/[a-z]/.test(password)) {
    suggestions.push('添加小写字母（a-z）');
  }
  
  if (!/[0-9]/.test(password)) {
    suggestions.push('添加数字（0-9）');
  }
  
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    suggestions.push('添加特殊字符（!@#$等）');
  }
  
  return suggestions;
}
