/**
 * 首页 Mock 数据
 * @description 用于开发阶段的模拟数据，通过 ENV_CONFIG.VITE_USE_MOCK 控制开关
 */

import type { Category } from '@/types/category';
import type { FeaturedContent } from '@/types/featured';
import type { HomepageRoomItem } from '@/types/homepage';

/** 当前时间戳 */
const now = new Date().toISOString();

/**
 * 分类数据
 * @description 包含推荐和各医学科室分类
 */
export const mockCategories: Category[] = [
  { id: 'recommend', name: '推荐', slug: 'recommend', icon: null, description: null, sort_order: 0, is_active: true, created_at: now, updated_at: now },
  { id: 'cat_001', name: '肝胆外科', slug: 'hepatobiliary', icon: 'icon-liver', description: null, sort_order: 1, is_active: true, created_at: now, updated_at: now },
  { id: 'cat_002', name: '胃肠外科', slug: 'gastrointestinal', icon: 'icon-stomach', description: null, sort_order: 2, is_active: true, created_at: now, updated_at: now },
  { id: 'cat_003', name: '骨科', slug: 'orthopedics', icon: 'icon-bone', description: null, sort_order: 3, is_active: true, created_at: now, updated_at: now },
  { id: 'cat_004', name: '心血管科', slug: 'cardiovascular', icon: 'icon-heart', description: null, sort_order: 4, is_active: true, created_at: now, updated_at: now },
  { id: 'cat_005', name: '神经外科', slug: 'neurosurgery', icon: 'icon-brain', description: null, sort_order: 5, is_active: true, created_at: now, updated_at: now },
];

/**
 * 焦点图数据
 * @description 首页轮播图数据，包含直播、品牌、专家等类型
 */
export const mockFeaturedData: FeaturedContent[] = [
  {
    id: 'feat_001',
    title: '肝胆外科微创手术直播',
    subtitle: '北京大学人民医院',
    image_url: 'https://via.placeholder.com/750x420/509cec/ffffff?text=直播预告',
    target_type: 'session',
    target_id: 'session_001',
    target_url: null,
    sort_order: 0,
    is_active: true,
    start_at: null,
    end_at: null,
    created_at: now,
    updated_at: now,
  },
  {
    id: 'feat_002',
    title: '迈瑞医疗器械展示',
    subtitle: '新品发布会',
    image_url: 'https://via.placeholder.com/750x420/28a745/ffffff?text=品牌专区',
    target_type: 'brand',
    target_id: 'brand_001',
    target_url: null,
    sort_order: 1,
    is_active: true,
    start_at: null,
    end_at: null,
    created_at: now,
    updated_at: now,
  },
  {
    id: 'feat_003',
    title: '房树强教授专题',
    subtitle: '肝胆外科权威专家',
    image_url: 'https://via.placeholder.com/750x420/ffc107/000000?text=专家专题',
    target_type: 'expert',
    target_id: 'expert_001',
    target_url: null,
    sort_order: 2,
    is_active: true,
    start_at: null,
    end_at: null,
    created_at: now,
    updated_at: now,
  },
];

/**
 * 首页直播卡片数据
 * @description 包含10条模拟直播间数据，涵盖不同状态和分类
 * @type HomepageRoomItem[] - 使用首页专用类型
 */
export const mockHomepageRooms: HomepageRoomItem[] = [
  {
    id: 'room_001',
    title: '腹腔镜肝切除术技术要点',
    cover_url: 'https://via.placeholder.com/350x200/dc3545/ffffff?text=LIVE',
    summary: '本期重点讲解腹腔镜肝切除术的技术要点与并发症处理',
    live_status: 'live',
    host: {
      expert_id: 'expert_001',
      user_id: null,
      name: '房树强',
      title: '主任医师、教授',
      hospital: '北京大学人民医院',
    },
    status_data: {
      viewer_count: 1250,
      start_time: null,
      duration_seconds: null,
      play_count: null,
    },
    heat: 8500,
    category_id: 'cat_001', // 肝胆外科
  },
  {
    id: 'room_002',
    title: '胃肠道肿瘤微创治疗进展',
    cover_url: 'https://via.placeholder.com/350x200/509cec/ffffff?text=直播2',
    summary: '最新微创手术技术在胃肠道肿瘤中的应用',
    live_status: 'live',
    host: {
      expert_id: 'expert_002',
      user_id: null,
      name: '李明华',
      title: '主任医师',
      hospital: '协和医院',
    },
    status_data: {
      viewer_count: 856,
      start_time: null,
      duration_seconds: null,
      play_count: null,
    },
    heat: 6200,
    category_id: 'cat_002', // 胃肠外科
  },
  {
    id: 'room_003',
    title: '骨科机器人手术演示',
    cover_url: 'https://via.placeholder.com/350x200/ffc107/000000?text=预告',
    summary: '骨科手术机器人的临床应用',
    live_status: 'scheduled',
    host: {
      expert_id: 'expert_003',
      user_id: null,
      name: '王志刚',
      title: '副主任医师',
      hospital: '积水潭医院',
    },
    status_data: {
      viewer_count: null,
      start_time: '2025-12-05T14:00:00Z',
      duration_seconds: null,
      play_count: null,
    },
    heat: null,
    category_id: 'cat_003', // 骨科
  },
  {
    id: 'room_004',
    title: '心血管介入手术直播',
    cover_url: 'https://via.placeholder.com/350x200/6c757d/ffffff?text=回放',
    summary: '冠脉介入治疗的最新技术',
    live_status: 'replay',
    host: {
      expert_id: 'expert_004',
      user_id: null,
      name: '张伟',
      title: '主任医师',
      hospital: '阜外医院',
    },
    status_data: {
      viewer_count: null,
      start_time: null,
      duration_seconds: 3650,
      play_count: 2300,
    },
    heat: 4500,
    category_id: 'cat_004', // 心血管科
  },
  {
    id: 'room_005',
    title: '神经外科显微手术技巧',
    cover_url: 'https://via.placeholder.com/350x200/dc3545/ffffff?text=LIVE',
    summary: '脑肿瘤显微切除术的关键技术',
    live_status: 'live',
    host: {
      expert_id: 'expert_005',
      user_id: null,
      name: '刘海涛',
      title: '教授',
      hospital: '天坛医院',
    },
    status_data: {
      viewer_count: 2100,
      start_time: null,
      duration_seconds: null,
      play_count: null,
    },
    heat: 12000,
    category_id: 'cat_005', // 神经外科
  },
  {
    id: 'room_006',
    title: '肝胆疾病诊疗新进展',
    cover_url: 'https://via.placeholder.com/350x200/509cec/ffffff?text=直播6',
    summary: '肝胆胰脾外科疾病的综合诊疗',
    live_status: 'replay',
    host: {
      expert_id: 'expert_006',
      user_id: null,
      name: '陈建国',
      title: '主任医师',
      hospital: '301医院',
    },
    status_data: {
      viewer_count: null,
      start_time: null,
      duration_seconds: 5400,
      play_count: 1850,
    },
    heat: 3200,
    category_id: 'cat_001', // 肝胆外科
  },
  {
    id: 'room_007',
    title: '结直肠癌手术技术',
    cover_url: 'https://via.placeholder.com/350x200/ffc107/000000?text=预告',
    summary: 'TME手术技术要点与质量控制',
    live_status: 'scheduled',
    host: {
      expert_id: 'expert_007',
      user_id: null,
      name: '赵丽娟',
      title: '副主任医师',
      hospital: '中山医院',
    },
    status_data: {
      viewer_count: null,
      start_time: '2025-12-06T09:00:00Z',
      duration_seconds: null,
      play_count: null,
    },
    heat: null,
    category_id: 'cat_002', // 胃肠外科
  },
  {
    id: 'room_008',
    title: '关节置换术后康复',
    cover_url: 'https://via.placeholder.com/350x200/6c757d/ffffff?text=回放',
    summary: '全膝关节置换术后快速康复方案',
    live_status: 'replay',
    host: {
      expert_id: null,
      user_id: 'user_008',
      name: '孙医生',
      title: null,
      hospital: null,
    },
    status_data: {
      viewer_count: null,
      start_time: null,
      duration_seconds: 2700,
      play_count: 560,
    },
    heat: 1200,
    category_id: 'cat_003', // 骨科
  },
  {
    id: 'room_009',
    title: '房颤消融治疗策略',
    cover_url: 'https://via.placeholder.com/350x200/509cec/ffffff?text=直播9',
    summary: '心房颤动导管消融技术详解',
    live_status: 'replay',
    host: {
      expert_id: 'expert_009',
      user_id: null,
      name: '周明',
      title: '主任医师',
      hospital: '安贞医院',
    },
    status_data: {
      viewer_count: null,
      start_time: null,
      duration_seconds: 4200,
      play_count: 980,
    },
    heat: 2800,
    category_id: 'cat_004', // 心血管科
  },
  {
    id: 'room_010',
    title: '脊柱微创手术进展',
    cover_url: 'https://via.placeholder.com/350x200/ffc107/000000?text=预告',
    summary: '脊柱内镜手术的最新技术与适应症',
    live_status: 'scheduled',
    host: {
      expert_id: 'expert_010',
      user_id: null,
      name: '吴强',
      title: '副教授',
      hospital: '华西医院',
    },
    status_data: {
      viewer_count: null,
      start_time: '2025-12-07T15:30:00Z',
      duration_seconds: null,
      play_count: null,
    },
    heat: null,
    category_id: 'cat_003', // 骨科
  },
];

/**
 * 兼容旧代码的导出（已废弃，请使用 mockHomepageRooms）
 * @deprecated 使用 mockHomepageRooms 替代
 */
export const mockRoomData = mockHomepageRooms;
