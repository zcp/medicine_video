import type { BrandItem } from '@/types/brands'

export type BrandFunctionCategory =
  | '全部'
  | '药品/药企'
  | '医疗器械'
  | '耗材'
  | '数字化/平台'
  | '教育/培训'
  | '服务机构'
  | '其他'

export type BrandDepartmentCategory =
  | '全部'
  | '心内科'
  | '肿瘤科'
  | '呼吸科'
  | '消化科'
  | '神经科'
  | '骨科'
  | '妇产科'
  | '儿科'
  | '麻醉/ICU'
  | '急诊'
  | '影像科'
  | '检验科'
  | '眼科'
  | '皮肤科'
  | '全科/健康管理'
  | '其他'

export interface BrandCategoryResult {
  functionCategory: BrandFunctionCategory
  departmentCategory: BrandDepartmentCategory
  matchedKeywords?: string[]
}

const functionRules: Array<{ cat: BrandFunctionCategory; keywords: string[] }> = [
  { cat: '药品/药企', keywords: ['制药', '药业', '药品', '药物', '疫苗', 'biopharma', 'pharma', '药企', '生物制药', '抗体', '靶向', '化疗'] },
  { cat: '医疗器械', keywords: ['器械', '医疗器械', '影像', '超声', 'CT', 'MR', 'MRI', '监护', '麻醉机', '呼吸机', '内镜', '介入', '手术', '缝合', '机器人', '植入', '支架'] },
  { cat: '耗材', keywords: ['耗材', '敷料', '导管', '注射', '手套', '口罩', '针', '管路', '试剂盒', '一次性'] },
  { cat: '数字化/平台', keywords: ['平台', '系统', '云', 'SaaS', 'saas', 'AI', '智能', '数据', '数字化', '互联网', '软件', '小程序', 'App', '解决方案'] },
  { cat: '教育/培训', keywords: ['培训', '课程', '教育', '学术', '讲堂', '学院', '会议', '论坛', '直播', '学习'] },
  { cat: '服务机构', keywords: ['服务', '咨询', '运营', '医院管理', '检测服务', '第三方', '机构'] }
]

const departmentRules: Array<{ cat: BrandDepartmentCategory; keywords: string[] }> = [
  { cat: '心内科', keywords: ['心内', '心血管', '冠脉', '介入', '心律失常', '心衰', '高血压'] },
  { cat: '肿瘤科', keywords: ['肿瘤', '放疗', '化疗', '肿瘤科', '肿瘤学', '癌', '肿瘤免疫'] },
  { cat: '呼吸科', keywords: ['呼吸', '哮喘', 'COPD', '慢阻肺', '肺', '呼吸机'] },
  { cat: '消化科', keywords: ['消化', '胃', '肠', '肝', '胰', '内镜'] },
  { cat: '神经科', keywords: ['神经', '卒中', '脑', '癫痫', '帕金森'] },
  { cat: '骨科', keywords: ['骨科', '关节', '脊柱', '骨折', '骨质疏松', '运动医学'] },
  { cat: '妇产科', keywords: ['妇产', '产科', '妇科', '生殖', '围产', '母婴'] },
  { cat: '儿科', keywords: ['儿科', '新生儿', '儿童', '儿'] },
  { cat: '麻醉/ICU', keywords: ['麻醉', 'ICU', '重症', '监护'] },
  { cat: '急诊', keywords: ['急诊', '创伤', '急救', '120'] },
  { cat: '影像科', keywords: ['影像', '放射', 'CT', 'MR', 'MRI', 'DR', '超声'] },
  { cat: '检验科', keywords: ['检验', '实验室', '试剂', '生化', 'PCR', '免疫', '血常规'] },
  { cat: '眼科', keywords: ['眼科', '视网膜', '白内障', '屈光'] },
  { cat: '皮肤科', keywords: ['皮肤', '银屑病', '痤疮', '皮炎'] },
  { cat: '全科/健康管理', keywords: ['健康管理', '体检', '慢病', '随访', '全科', '家庭医生'] }
]

function matchCategory<T extends string>(text: string, rules: Array<{ cat: T; keywords: string[] }>): { cat: T; matched: string[] } | null {
  const matched: string[] = []
  for (const rule of rules) {
    for (const kw of rule.keywords) {
      if (!kw) continue
      if (text.includes(kw)) {
        matched.push(kw)
      }
    }
    if (matched.length) {
      return { cat: rule.cat, matched }
    }
  }
  return null
}

/**
 * 前端临时分类（mock）：基于品牌 name/description 的关键词规则推断“功能/科室”。
 * 说明：这不是后端权威分类，后续建议由后端提供结构化字段。
 */
export function categorizeBrandMock(brand: Pick<BrandItem, 'name' | 'description'>): BrandCategoryResult {
  const text = `${brand.name || ''} ${(brand.description || '')}`

  const func = matchCategory<BrandFunctionCategory>(text, functionRules)
  const dept = matchCategory<BrandDepartmentCategory>(text, departmentRules)

  return {
    functionCategory: func?.cat || '其他',
    departmentCategory: dept?.cat || '其他',
    matchedKeywords: [...(func?.matched || []), ...(dept?.matched || [])]
  }
}
