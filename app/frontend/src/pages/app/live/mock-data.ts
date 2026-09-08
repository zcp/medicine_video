/**
 * LiveView页面Mock数据
 * 用于开发阶段，当 ENV_CONFIG.VITE_USE_MOCK = true 时使用
 *
 * 🎯 混合Mock策略：
 * - 主播放器：使用真实业务流，提前发现环境问题
 * - 推荐列表：使用差异化测试源，验证切换功能
 */

// 🎯 统一使用真实业务流URL
// 所有播放地址统一使用真实案例URL，确保播放功能正常
const REAL_M3U8_URL = 'https://mp2.dayilive.com/clip/2aa5b88f3d.m3u8';

// 🎯 专家信息Mock数据（用于后端API字段不完整时的降级方案）
export const mockExpertData = {
  id: 'expert-mock-001',
  name: '房树强',
  title: '主任医师、教授',
  hospital: '北京大学人民医院',
  department: '肝胆胰外科',
  avatar: '/static/default-avatar.png',  // 🎨 使用项目中的头像图片
  bio: '北京大学人民医院肝胆外科主任，从事肝胆胰外科临床工作30余年，擅长肝胆胰疾病的微创手术治疗。',
};

// 主场次Mock数据（使用真实业务流）
export const mockSessionData = {
  id: 'session-123',
  room_id: 'room-456',
  title: '肝胆胰外科微创手术的最新进展与病例讨论会——2025年秋季学术研讨会第三场',
  summary: '本次直播将邀请国内知名肝胆胰外科专家，围绕微创手术技术最新进展进行深入讨论...',
  status: 'live', // 'live' | 'scheduled' | 'ended'
  start_time: new Date().toISOString(),
  cover_url: '/static/mock-cover.jpg',
  playback_url: REAL_M3U8_URL,  // 🔧 使用真实URL
  expert: mockExpertData,  // 🔧 使用统一的Mock专家数据
  tags: [
    { id: 'tag-1', name: '微创手术' },
    { id: 'tag-2', name: '肝胆胰外科' },
    { id: 'tag-3', name: '病例讨论' }
  ]
};

// 聊天消息Mock数据
export const mockChatMessages = [
  {
    id: 'msg-1',
    user: {
      id: 'user-1',
      name: '李医生',
      avatar: '/static/mock-avatar-1.jpg'
    },
    content: '这个手术技术很不错！',
    timestamp: new Date(Date.now() - 300000).toISOString()
  },
  {
    id: 'msg-2',
    user: {
      id: 'user-2',
      name: '王护士',
      avatar: '/static/mock-avatar-2.jpg'
    },
    content: '请问术后恢复需要多久？',
    timestamp: new Date(Date.now() - 180000).toISOString()
  }
];

// 问答Mock数据
export const mockQuestions = [
  {
    id: 'q-1',
    user: {
      id: 'user-3',
      name: '赵医生'
    },
    content: '请问这种手术的成功率如何？',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    answer: {
      expert: {
        id: 'expert-789',
        name: '张三教授'
      },
      content: '根据我们的临床经验，这种手术的成功率在95%以上...',
      timestamp: new Date(Date.now() - 300000).toISOString()
    }
  }
];

// 相关推荐Mock数据（混合使用真实流和测试流）
export const mockRelatedSessions = [
  {
    id: 'session-124',
    title: '胃肠外科微创手术新技术分享',
    expert: {
      name: '李四教授'
    },
    start_time: new Date(Date.now() + 86400000).toISOString(),
    cover_url: '/static/mock-cover-2.jpg',
    playback_url: REAL_M3U8_URL,  // 🔧 使用真实URL
    status: 'live'
  },
  {
    id: 'session-125',
    title: '骨科关节置换手术案例分析',
    expert: {
      name: '王五主任'
    },
    start_time: new Date(Date.now() + 172800000).toISOString(),
    cover_url: '/static/mock-cover-3.jpg',
    playback_url: REAL_M3U8_URL,  // 🔧 使用真实URL
    status: 'ended'
  }
];

// 资料下载Mock数据
export const mockMaterials = [
  {
    id: 'material-1',
    name: '手术技术要点.pdf',
    size: 2048000, // 2MB
    url: '/static/materials/surgery-guide.pdf'
  },
  {
    id: 'material-2',
    name: '病例分析报告.pdf',
    size: 1536000, // 1.5MB
    url: '/static/materials/case-report.pdf'
  }
];

// 病例介绍Mock数据
export const mockCaseData = {
  description: `病例摘要：
• 患者女性，71岁，因"发现肝占位性病变1个月"就诊
• 现病史：患者1周前在当地医院行CT提示：肝V段肿物，考虑恶性（肝内胆管癌可能大）；腹盆腔、腹膜后未见明显肿大淋巴结
• 既往史：无乙肝病史，阑尾切除术30年
• 实验室检查：CA199和AFP均正常，FER 1070 ng/mL，肝功能A级，肝储备功能正常
• 手术方案：建议行腹腔镜肝V段切除术`,
  patientInfo: {
    age: '71岁',
    gender: '女性',
    diagnosis: '肝V段肿物，考虑恶性（肝内胆管癌可能大）'
  }
};
