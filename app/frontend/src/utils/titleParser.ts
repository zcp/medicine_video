/**
 * 标题解析工具
 * 从直播标题中提取专家姓名、职称、医院、科室等信息
 * 用于在后端专家信息缺失时的临时方案
 */

/**
 * 解析结果接口
 */
export interface ParsedTitleInfo {
  /** 专家姓名 */
  expertName?: string
  /** 专家职称（可能有多个，用顿号分隔） */
  expertTitle?: string
  /** 医院名称 */
  hospital?: string
  /** 科室名称 */
  department?: string
  /** 是否成功提取到信息 */
  hasInfo: boolean
}

/**
 * 从标题中提取专家姓名和职称
 * @param title 标题字符串
 * @returns 专家姓名和职称
 */
function extractExpertInfo(title: string): { name?: string; title?: string } {
  // 常见职称列表
  const titles = [
    '教授',
    '主任医师',
    '副主任医师',
    '主治医师',
    '住院医师',
    '医师',
    '博士',
    '硕士',
    '研究员',
    '副研究员',
    '主任',
    '副主任'
  ]
  
  const titlePattern = titles.join('|')
  
  // 规则1: 姓名 + 职称（紧密连接或有空格/标点）
  // 示例: "赵国栋教授"、"房树强 主任医师、教授"
  const pattern1 = new RegExp(`([一-龥]{2,4})\\s*([${titlePattern}]+[、，\\s]*[${titlePattern}]*)`, 'g')
  const matches1 = title.match(pattern1)
  
  if (matches1 && matches1.length > 0) {
    // 取第一个匹配结果
    const match = matches1[0]
    const detailMatch = match.match(new RegExp(`([一-龥]{2,4})\\s*((${titlePattern})[、，\\s]*(${titlePattern})?)`))
    
    if (detailMatch) {
      return {
        name: detailMatch[1],
        title: detailMatch[2].replace(/\s+/g, '、').replace(/，/g, '、')
      }
    }
  }
  
  // 规则2: 使用 | 或 ｜ 分隔的格式
  // 示例: "264 赵国栋教授｜机器人扩大左半肝切除术"
  const pattern2 = /([一-龥]{2,4})(教授|主任医师|副主任医师|主治医师|医师|博士)\s*[|｜]/
  const match2 = title.match(pattern2)
  
  if (match2) {
    return {
      name: match2[1],
      title: match2[2]
    }
  }
  
  return {}
}

/**
 * 从标题中提取医院信息
 * @param title 标题字符串
 * @returns 医院名称
 */
function extractHospitalInfo(title: string): string | undefined {
  // 医院关键词
  const hospitalKeywords = ['医院', '医学院', '医疗中心', '卫生院', '诊所', '医学中心']
  
  // 规则1: 完整医院名称（包括前缀）
  // 示例: "北京大学人民医院"、"解放军总医院"
  const pattern1 = new RegExp(`([一-龥]{2,20})(${hospitalKeywords.join('|')})`)
  const match1 = title.match(pattern1)
  
  if (match1) {
    return match1[0]
  }
  
  // 规则2: 特殊医院（军队医院等）
  const pattern2 = /(解放军|武警|空军|海军|陆军)[一-龥]{0,10}医院/
  const match2 = title.match(pattern2)
  
  if (match2) {
    return match2[0]
  }
  
  return undefined
}

/**
 * 从标题中提取科室信息
 * @param title 标题字符串
 * @returns 科室名称
 */
function extractDepartmentInfo(title: string): string | undefined {
  // 科室关键词
  const deptKeywords = ['科', '部', '中心', '室']
  
  // 规则1: 医学科室名称
  // 示例: "肝胆胰外科"、"骨科医学部运动医学科"
  const pattern1 = new RegExp(`([一-龥]{2,15})(${deptKeywords.join('|')})([一-龥]{0,10}(${deptKeywords.join('|')}))?`)
  const match1 = title.match(pattern1)
  
  if (match1) {
    // 如果匹配到多级科室，返回完整的科室名称
    return match1[0]
  }
  
  return undefined
}

/**
 * 解析标题，提取专家和医院信息
 * @param title 直播标题
 * @returns 解析结果
 * 
 * @example
 * // 示例1: 包含专家信息
 * const result1 = parseTitleInfo('264 赵国栋教授｜机器人扩大左半肝切除术')
 * // { expertName: '赵国栋', expertTitle: '教授', hasInfo: true }
 * 
 * @example
 * // 示例2: 包含医院和科室信息
 * const result2 = parseTitleInfo('【低延迟】0523 2025解放军总医院骨科医学部运动医学科关节镜手术标准化诊疗学术推广年')
 * // { hospital: '解放军总医院', department: '骨科医学部运动医学科', hasInfo: true }
 */
export function parseTitleInfo(title: string): ParsedTitleInfo {
  if (!title) {
    return { hasInfo: false }
  }
  
  // 提取专家信息
  const expertInfo = extractExpertInfo(title)
  
  // 提取医院信息
  const hospital = extractHospitalInfo(title)
  
  // 提取科室信息
  const department = extractDepartmentInfo(title)
  
  // 判断是否成功提取到任何信息
  const hasInfo = !!(expertInfo.name || hospital || department)
  
  return {
    expertName: expertInfo.name,
    expertTitle: expertInfo.title,
    hospital,
    department,
    hasInfo
  }
}

/**
 * 格式化医院和科室信息为显示字符串
 * @param hospital 医院名称
 * @param department 科室名称
 * @returns 格式化后的字符串
 * 
 * @example
 * formatHospitalDepartment('北京大学人民医院', '肝胆胰外科')
 * // "北京大学人民医院 肝胆胰外科"
 */
export function formatHospitalDepartment(hospital?: string, department?: string): string {
  if (hospital && department) {
    return `${hospital} ${department}`
  }
  if (hospital) {
    return hospital
  }
  if (department) {
    return department
  }
  return ''
}
