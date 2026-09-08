/**
 * 表单校验工具
 * 提供常用的表单字段校验规则和验证函数
 */

/**
 * 校验结果接口
 */
export interface ValidationResult {
  valid: boolean
  message?: string
}

/**
 * 校验规则接口
 */
export interface ValidationRule {
  required?: boolean
  min?: number
  max?: number
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => ValidationResult
  message?: string
}

/**
 * 常用正则表达式
 */
export const REGEX_PATTERNS = {
  /** 手机号 */
  PHONE: /^1[3-9]\d{9}$/,
  /** 邮箱 */
  EMAIL: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  /** 身份证号 */
  ID_CARD: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/,
  /** 中文姓名 */
  CHINESE_NAME: /^[\u4e00-\u9fa5·]{2,20}$/,
  /** 用户名 (字母、数字、下划线，3-16位) */
  USERNAME: /^[a-zA-Z0-9_]{3,16}$/,
  /** 密码 (至少8位，包含字母和数字) */
  PASSWORD: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$/,
  /** 强密码 (至少8位，包含大小写字母、数字、特殊字符) */
  STRONG_PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  /** URL地址 */
  URL: /^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/,
  /** IP地址 */
  IP: /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  /** 银行卡号 */
  BANK_CARD: /^[1-9]\d{12,19}$/,
  /** 车牌号 */
  LICENSE_PLATE: /^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4}[A-Z0-9挂学警港澳]$/,
  /** QQ号 */
  QQ: /^[1-9][0-9]{4,10}$/,
  /** 微信号 */
  WECHAT: /^[a-zA-Z][-_a-zA-Z0-9]{5,19}$/,
  /** 固定电话 */
  LANDLINE: /^(\d{3,4}-)?\d{7,8}$/,
  /** 邮政编码 */
  POSTAL_CODE: /^[1-9]\d{5}$/,
  /** 中文字符 */
  CHINESE: /^[\u4e00-\u9fa5]+$/,
  /** 数字 */
  NUMBER: /^\d+$/,
  /** 小数 */
  DECIMAL: /^\d+(\.\d+)?$/,
  /** 整数 */
  INTEGER: /^-?\d+$/
}

/**
 * 基础校验函数
 */

/**
 * 必填校验
 * @param value 值
 * @param message 错误信息
 * @returns 校验结果
 */
export function required(value: any, message: string = '此字段为必填项'): ValidationResult {
  const valid = value !== null && value !== undefined && value !== ''
  return { valid, message: valid ? undefined : message }
}

/**
 * 最小长度校验
 * @param value 值
 * @param minLength 最小长度
 * @param message 错误信息
 * @returns 校验结果
 */
export function minLength(value: string, minLength: number, message?: string): ValidationResult {
  if (!value) return { valid: true }
  
  const valid = value.length >= minLength
  const defaultMessage = `长度不能少于${minLength}个字符`
  return { valid, message: valid ? undefined : (message || defaultMessage) }
}

/**
 * 最大长度校验
 * @param value 值
 * @param maxLength 最大长度
 * @param message 错误信息
 * @returns 校验结果
 */
export function maxLength(value: string, maxLength: number, message?: string): ValidationResult {
  if (!value) return { valid: true }
  
  const valid = value.length <= maxLength
  const defaultMessage = `长度不能超过${maxLength}个字符`
  return { valid, message: valid ? undefined : (message || defaultMessage) }
}

/**
 * 范围长度校验
 * @param value 值
 * @param min 最小长度
 * @param max 最大长度
 * @param message 错误信息
 * @returns 校验结果
 */
export function lengthRange(value: string, min: number, max: number, message?: string): ValidationResult {
  if (!value) return { valid: true }
  
  const valid = value.length >= min && value.length <= max
  const defaultMessage = `长度必须在${min}-${max}个字符之间`
  return { valid, message: valid ? undefined : (message || defaultMessage) }
}

/**
 * 最小值校验
 * @param value 值
 * @param minValue 最小值
 * @param message 错误信息
 * @returns 校验结果
 */
export function minValue(value: number, minValue: number, message?: string): ValidationResult {
  if (value === null || value === undefined) return { valid: true }
  
  const valid = value >= minValue
  const defaultMessage = `值不能小于${minValue}`
  return { valid, message: valid ? undefined : (message || defaultMessage) }
}

/**
 * 最大值校验
 * @param value 值
 * @param maxValue 最大值
 * @param message 错误信息
 * @returns 校验结果
 */
export function maxValue(value: number, maxValue: number, message?: string): ValidationResult {
  if (value === null || value === undefined) return { valid: true }
  
  const valid = value <= maxValue
  const defaultMessage = `值不能大于${maxValue}`
  return { valid, message: valid ? undefined : (message || defaultMessage) }
}

/**
 * 正则表达式校验
 * @param value 值
 * @param pattern 正则表达式
 * @param message 错误信息
 * @returns 校验结果
 */
export function pattern(value: string, pattern: RegExp, message: string = '格式不正确'): ValidationResult {
  if (!value) return { valid: true }
  
  const valid = pattern.test(value)
  return { valid, message: valid ? undefined : message }
}

/**
 * 具体字段校验函数
 */

/**
 * 手机号校验
 * @param phone 手机号
 * @param message 错误信息
 * @returns 校验结果
 */
export function validatePhone(phone: string, message: string = '请输入正确的手机号'): ValidationResult {
  return pattern(phone, REGEX_PATTERNS.PHONE, message)
}

/**
 * 邮箱校验
 * @param email 邮箱
 * @param message 错误信息
 * @returns 校验结果
 */
export function validateEmail(email: string, message: string = '请输入正确的邮箱地址'): ValidationResult {
  return pattern(email, REGEX_PATTERNS.EMAIL, message)
}

/**
 * 身份证号校验
 * @param idCard 身份证号
 * @param message 错误信息
 * @returns 校验结果
 */
export function validateIdCard(idCard: string, message: string = '请输入正确的身份证号'): ValidationResult {
  if (!idCard) return { valid: true }

  // 基础格式校验
  const formatResult = pattern(idCard, REGEX_PATTERNS.ID_CARD, message)
  if (!formatResult.valid) return formatResult

  // 校验位校验
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
  
  let sum = 0
  for (let i = 0; i < 17; i++) {
    sum += parseInt(idCard[i]) * weights[i]
  }
  
  const expected = codes[sum % 11]
  const actual = idCard[17].toUpperCase()
  
  const valid = expected === actual
  return { valid, message: valid ? undefined : message }
}

/**
 * 中文姓名校验
 * @param name 姓名
 * @param message 错误信息
 * @returns 校验结果
 */
export function validateChineseName(name: string, message: string = '请输入正确的中文姓名'): ValidationResult {
  return pattern(name, REGEX_PATTERNS.CHINESE_NAME, message)
}

/**
 * 用户名校验
 * @param username 用户名
 * @param message 错误信息
 * @returns 校验结果
 */
export function validateUsername(username: string, message: string = '用户名只能包含字母、数字、下划线，长度3-16位'): ValidationResult {
  return pattern(username, REGEX_PATTERNS.USERNAME, message)
}

/**
 * 密码强度校验
 * @param password 密码
 * @param level 强度等级 'weak' | 'medium' | 'strong'
 * @param message 错误信息
 * @returns 校验结果
 */
export function validatePassword(password: string, level: 'weak' | 'medium' | 'strong' = 'medium', message?: string): ValidationResult {
  if (!password) return { valid: true }

  switch (level) {
    case 'weak':
      const valid = password.length >= 6
      return { 
        valid, 
        message: valid ? undefined : (message || '密码长度不能少于6位') 
      }
    
    case 'medium':
      return pattern(password, REGEX_PATTERNS.PASSWORD, message || '密码至少8位，需包含字母和数字')
    
    case 'strong':
      return pattern(password, REGEX_PATTERNS.STRONG_PASSWORD, message || '密码至少8位，需包含大小写字母、数字和特殊字符')
    
    default:
      return { valid: false, message: '未知的密码强度等级' }
  }
}

/**
 * 确认密码校验
 * @param password 密码
 * @param confirmPassword 确认密码
 * @param message 错误信息
 * @returns 校验结果
 */
export function validatePasswordConfirm(password: string, confirmPassword: string, message: string = '两次输入的密码不一致'): ValidationResult {
  const valid = password === confirmPassword
  return { valid, message: valid ? undefined : message }
}

/**
 * URL校验
 * @param url URL地址
 * @param message 错误信息
 * @returns 校验结果
 */
export function validateUrl(url: string, message: string = '请输入正确的URL地址'): ValidationResult {
  return pattern(url, REGEX_PATTERNS.URL, message)
}

/**
 * 银行卡号校验
 * @param cardNumber 银行卡号
 * @param message 错误信息
 * @returns 校验结果
 */
export function validateBankCard(cardNumber: string, message: string = '请输入正确的银行卡号'): ValidationResult {
  if (!cardNumber) return { valid: true }

  // 移除空格
  const cleanNumber = cardNumber.replace(/\s/g, '')
  
  // 基础格式校验
  const formatResult = pattern(cleanNumber, REGEX_PATTERNS.BANK_CARD, message)
  if (!formatResult.valid) return formatResult

  // Luhn算法校验
  let sum = 0
  let isEven = false
  
  for (let i = cleanNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cleanNumber[i])
    
    if (isEven) {
      digit *= 2
      if (digit > 9) {
        digit -= 9
      }
    }
    
    sum += digit
    isEven = !isEven
  }
  
  const valid = sum % 10 === 0
  return { valid, message: valid ? undefined : message }
}

/**
 * 组合校验器
 * @param value 要校验的值
 * @param rules 校验规则数组
 * @returns 校验结果
 */
export function validate(value: any, rules: ValidationRule[]): ValidationResult {
  for (const rule of rules) {
    // 必填校验
    if (rule.required) {
      const result = required(value, rule.message)
      if (!result.valid) return result
    }

    // 如果值为空且非必填，跳过后续校验
    if (!value && !rule.required) continue

    // 长度校验
    if (rule.minLength !== undefined) {
      const result = minLength(value, rule.minLength, rule.message)
      if (!result.valid) return result
    }

    if (rule.maxLength !== undefined) {
      const result = maxLength(value, rule.maxLength, rule.message)
      if (!result.valid) return result
    }

    // 数值校验
    if (rule.min !== undefined) {
      const result = minValue(value, rule.min, rule.message)
      if (!result.valid) return result
    }

    if (rule.max !== undefined) {
      const result = maxValue(value, rule.max, rule.message)
      if (!result.valid) return result
    }

    // 正则校验
    if (rule.pattern) {
      const result = pattern(value, rule.pattern, rule.message || '格式不正确')
      if (!result.valid) return result
    }

    // 自定义校验
    if (rule.custom) {
      const result = rule.custom(value)
      if (!result.valid) return result
    }
  }

  return { valid: true }
}

/**
 * 表单校验器类
 */
export class FormValidator {
  private rules: Record<string, ValidationRule[]> = {}
  private errors: Record<string, string> = {}

  /**
   * 添加字段校验规则
   * @param field 字段名
   * @param rules 校验规则
   */
  addRule(field: string, rules: ValidationRule[]): void {
    this.rules[field] = rules
  }

  /**
   * 校验单个字段
   * @param field 字段名
   * @param value 值
   * @returns 校验结果
   */
  validateField(field: string, value: any): ValidationResult {
    const rules = this.rules[field]
    if (!rules) return { valid: true }

    const result = validate(value, rules)
    
    if (result.valid) {
      delete this.errors[field]
    } else {
      this.errors[field] = result.message || '校验失败'
    }

    return result
  }

  /**
   * 校验整个表单
   * @param data 表单数据
   * @returns 校验结果
   */
  validateForm(data: Record<string, any>): { valid: boolean; errors: Record<string, string> } {
    this.errors = {}
    let valid = true

    for (const field in this.rules) {
      const result = this.validateField(field, data[field])
      if (!result.valid) {
        valid = false
      }
    }

    return { valid, errors: { ...this.errors } }
  }

  /**
   * 获取字段错误信息
   * @param field 字段名
   * @returns 错误信息
   */
  getFieldError(field: string): string | undefined {
    return this.errors[field]
  }

  /**
   * 获取所有错误信息
   * @returns 错误信息对象
   */
  getAllErrors(): Record<string, string> {
    return { ...this.errors }
  }

  /**
   * 清除错误信息
   * @param field 字段名，不传则清除所有
   */
  clearErrors(field?: string): void {
    if (field) {
      delete this.errors[field]
    } else {
      this.errors = {}
    }
  }
}

// 导出默认校验器实例
export const defaultValidator = new FormValidator()
