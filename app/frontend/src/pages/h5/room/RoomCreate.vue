<template>
  <AdminLayout>
    <div class="room-create-container">
      <el-card class="main-card">
        <div class="form-wrapper">
          <!-- 顶部类型选择 -->
          <el-form-item label-width="100px" label="直播类型">
            <el-radio-group v-model="formModel.live_type">
              <el-radio-button label="video">
                <el-icon><VideoCamera /></el-icon> 视频直播
              </el-radio-button>
              <el-radio-button label="image" disabled>
                <el-icon><Picture /></el-icon> 图片直播
              </el-radio-button>
              <el-radio-button label="vr" disabled>
                <el-icon><View /></el-icon> VR直播
              </el-radio-button>
              <el-radio-button label="audio" disabled>
                <el-icon><Headset /></el-icon> 语音直播
              </el-radio-button>
              <el-radio-button label="doc" disabled>
                <el-icon><Document /></el-icon> 图文直播
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form :model="formModel" label-position="right" label-width="100px" class="main-form">
            <!-- 基本信息 -->
            <el-form-item label="直播形式" required>
              <div>
                <el-radio-group v-model="formModel.format">
                  <el-radio label="live">直播</el-radio>
                  <el-radio label="vod" disabled>点播/录播</el-radio>
                  <el-radio label="pseudo" disabled>伪直播</el-radio>
                </el-radio-group>
                <div class="form-item-tip">实时直播形式，根据实际画面进行传播，无法快进或回放</div>
              </div>
            </el-form-item>

            <el-form-item label="直播名称" required :error="errors.title">
              <el-input v-model="formModel.title" placeholder="请输入直播名称，100字内" maxlength="100" show-word-limit />
            </el-form-item>

            <el-form-item label="直播简介" required :error="errors.description">
              <el-input 
                v-model="formModel.description" 
                type="textarea" 
                placeholder="请输入直播简介，500字内" 
                maxlength="500" 
                show-word-limit 
                :rows="3"
              />
            </el-form-item>

            <el-form-item label="开始时间" required>
              <div>
                <el-date-picker v-model="formModel.start_time" type="datetime" placeholder="选择日期时间" />
                <div class="form-item-tip">
                  本场直播将于 {{ formattedStartTime }} 开播
                  <el-button link type="primary" @click="showComingSoonToast">设置开播提醒</el-button>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="显示模式">
              <div>
                <el-radio-group v-model="formModel.displayMode">
                  <el-radio label="horizontal">横屏</el-radio>
                  <el-radio label="vertical" disabled>竖屏</el-radio>
                  <el-radio label="three-screen" disabled>三分屏</el-radio>
                </el-radio-group>
                <div class="form-item-tip">
                  比例为16:9，视野相对开阔，适用于空间层次感丰富，纵深感强的场景
                  <el-tooltip content="详细说明文字" placement="top">
                    <el-icon style="margin-left: 4px; vertical-align: middle;"><InfoFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="直播封面" required :error="errors.cover_url">
              <div class="cover-uploader" @click="selectCoverAndPreview">
                <img v-if="coverPreviewUrl" :src="coverPreviewUrl" class="cover-preview" />
                <img v-else-if="formModel.cover_url" :src="getCoverSrc(formModel.cover_url)" class="cover-preview" />
                <div v-else class="uploader-placeholder">
                  <el-icon><Plus /></el-icon>
                  <span>点击上传封面（本地先预览，创建成功后以后端URL展示）</span>
                </div>
              </div>
              <div class="form-item-tip">推荐图片尺寸为: 1000*562, 不超过10M；支持png、jpg、gif格式</div>
            </el-form-item>

            <!-- 分类与场景 -->
            <el-form-item label="直播分类">
              <el-select placeholder="请选择话题分类" disabled style="width: 220px; margin-right: 8px;"></el-select>
              <el-button @click="showComingSoonToast">+ 添加分类</el-button>
            </el-form-item>

            <el-form-item label="所属频道">
              <el-button @click="showComingSoonToast">+ 选择频道</el-button>
            </el-form-item>

            <el-form-item label="使用场景">
              <el-radio-group v-model="formModel.scene">
                <el-radio label="general">通用</el-radio>
                <el-radio v-for="s in scenes" :key="s" :label="s" disabled>{{ s }}</el-radio>
              </el-radio-group>
            </el-form-item>

            <!-- 观看与回放 -->
            <el-form-item label="观看方式">
              <div>
                <el-radio-group v-model="formModel.is_private">
                  <el-radio-button :label="false"><el-icon><Unlock /></el-icon> 公开</el-radio-button>
                  <el-radio-button :label="true"><el-icon><Lock /></el-icon> 加密</el-radio-button>
                  <el-radio-button label="paid" disabled><el-icon><Money /></el-icon> 付费</el-radio-button>
                  <el-radio-button label="ticket" disabled><el-icon><Ticket /></el-icon> 购票进入</el-radio-button>
                </el-radio-group>
                <div class="form-item-tip">公开直播，所有人可以进来观看</div>
              </div>
            </el-form-item>

            <el-form-item label="回放方式">
              <div>
                <el-radio-group v-model="formModel.replay_type">
                  <el-radio-button label="after_end">结束后回放</el-radio-button>
                  <el-radio-button label="real_time" disabled>实时回放</el-radio-button>
                  <el-radio-button label="no_replay" disabled>结束后不回放</el-radio-button>
                </el-radio-group>
                <div class="form-item-tip">结束后话题才生成回放视频</div>
              </div>
            </el-form-item>

            <el-form-item label="生成回放视频">
              <div>
                <el-radio-group v-model="formModel.replay_video_type">
                  <el-radio-button label="single">单个视频</el-radio-button>
                  <el-radio-button label="multiple" disabled>多个视频</el-radio-button>
                  <el-checkbox style="margin-left: 16px;" disabled>开启自动打点 <el-icon><InfoFilled /></el-icon></el-checkbox>
                </el-radio-group>
                <div class="form-item-tip">直播时长最多7天，直播后生成单个视频，视频时长不能超过48小时，超过24小时截取最新24小时的视频</div>
                <div class="form-item-tip">注：创建时可以选择单个或多个视频，创建后不能修改</div>
              </div>
            </el-form-item>

            <el-form-item label="回放有效期">
              <el-radio-group v-model="formModel.replay_validity">
                <el-radio-button label="unlimited">无限制</el-radio-button>
                <el-radio-button label="all_day" disabled>全天</el-radio-button>
                <el-radio-button label="partial" disabled>部分时段</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 签到活动 -->
            <el-form-item label="签到活动">
              <el-button link type="primary" @click="showComingSoonToast">+ 创建活动</el-button>
            </el-form-item>

          </el-form>
        </div>
      </el-card>

      <div class="fixed-action-bar">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="handleCreate">立即创建</el-button>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import dayjs from 'dayjs';
import { ElMessage } from 'element-plus';
import {
  VideoCamera, Picture, View, Headset, Document, Plus, InfoFilled, 
  Unlock, Lock, Money, Ticket
} from '@element-plus/icons-vue';
import { useRoomStore } from '../../../store/room';
import { useSessionStore } from '../../../store/session';
import AdminLayout from '@/layouts/AdminLayout.vue';
import { getToken } from '@/store/auth';
import { BASE_API_URL } from '@/constants/api';
// 规范化封面URL：绝对地址直接返回，/media 相对路径拼接后端Host
function getCoverSrc(url?: string | null) {
  const u = (url || '').toString();
  if (!u) return '/public/logo.png';
  if (/^https?:\/\//.test(u)) return u;
  const base = BASE_API_URL.replace(/\/+$/, '');
  const origin = base.replace(/\/api\/.*/, '');
  return origin + (u.startsWith('/') ? u : '/' + u);
}

// --- 路由与Store --- 
const router = useRouter();
const roomStore = useRoomStore();
const sessionStore = useSessionStore();

// --- 静态UI状态 ---
const isSubmitting = ref(false);
const scenes = ['慢直播', '电商带货', '关怀模版', '代理推广', '在线活动', '企业培训', '医美', '赛事竞技', '融媒体', '企业会议', '年会', '房产直播', '招聘直播', '婚庆直播', '发布会'];

// --- 表单核心逻辑 ---
const formModel = reactive({
  // --- 本期实现字段 ---
  title: '',
  description: '',
  start_time: new Date(),
  cover_url: '',
  is_private: false,
  // --- 静态UI字段 ---
  live_type: 'video',
  format: 'live',
  displayMode: 'horizontal',
  scene: 'general',
  replay_type: 'after_end',
  replay_video_type: 'single',
  replay_validity: 'unlimited',
});

const errors = reactive({
  title: '',
  description: '',
  cover_url: '',
});

// 本地选择的封面临时路径（用于提交后上传）
const selectedCoverTempPath = ref<string>('');
// 本地预览用 URL（不影响最终 cover_url 展示）
const coverPreviewUrl = ref<string>('');

const formattedStartTime = computed(() => {
  return dayjs(formModel.start_time).format('YYYY年MM月DD日 HH:mm:ss');
});

const validateForm = () => {
  let isValid = true;
  errors.title = '';
  errors.description = '';
  errors.cover_url = '';

  if (!formModel.title.trim()) {
    errors.title = '直播名称不能为空';
    isValid = false;
  }
  if (!formModel.description.trim()) {
    errors.description = '直播简介不能为空';
    isValid = false;
  }
  // 暂时不验证封面，使用默认封面
  if (!formModel.cover_url) {
    formModel.cover_url = '/logo.png'; // 使用默认封面
  }
  return isValid;
};

const handleCreate = async () => {
  if (!validateForm()) {
    ElMessage.error('请检查表单必填项');
    return;
  }

  isSubmitting.value = true;
  
  try {
    // 第一步：创建Room
    ElMessage.info('正在创建直播间123...');
    const roomResult = await roomStore.addNewRoom({
      title: formModel.title.trim(),
      description: formModel.description.trim(),
      cover_url: formModel.cover_url || '/logo.png', // 使用默认封面
      is_private: formModel.is_private,
    });

    if (!roomResult.success) {
      throw new Error(roomResult.message || '创建直播间失败123');
    }

    // 第二步：创建Session
    ElMessage.info('正在设置直播时间...');
    const sessionResult = await sessionStore.createSession(roomResult.room_id!, {
      start_time: formModel.start_time
    });

    if (!sessionResult.success) {
      // Session创建失败，可以考虑删除已创建的Room
      ElMessage.warning('直播间创建成功，但设置直播时间失败，请稍后手动设置');
      // 这里可以选择是否删除已创建的Room，暂时不删除
    }

    // 第三步：如果用户选择了本地封面，创建后上传到后端
    if (selectedCoverTempPath.value) {
      try {
        await uploadCoverToServer(roomResult.room_id!, selectedCoverTempPath.value);
        ElMessage.success('封面已上传');
      } catch (e: any) {
        ElMessage.warning(e?.message || '封面上传失败，可稍后在管理页重试');
      } finally {
        // 上传流程结束后清理本地预览（以服务器URL为准）
        coverPreviewUrl.value = '';
      }
    }

    // 统一成功反馈
    ElMessage.success('直播间创建成功');
    router.push('/pages/room/new/RoomList');
    
  } catch (error: any) {
    ElMessage.error(error.message || '创建失败，请重试123');
  } finally {
    isSubmitting.value = false;
  }
};

const goBack = () => {
  router.back();
};

// --- 封面选择与上传逻辑（含本地预览，不覆盖后端URL） ---
const selectCoverAndPreview = () => {
  uni.chooseImage({
    count: 1,
    success: (chooseRes) => {
      const filePath = chooseRes.tempFilePaths?.[0];
      if (!filePath) return;
      
      // 添加调试信息
      console.log('=== 直播间封面选择调试信息 ===');
      console.log('选择的文件路径:', filePath);
      console.log('文件路径类型:', typeof filePath);
      console.log('是否为blob URL:', filePath.startsWith('blob:'));
      console.log('文件路径长度:', filePath.length);
      console.log('文件路径前50个字符:', filePath.substring(0, 50));
      console.log('================================');
      
      // 设置预览与待上传的临时路径；不修改 formModel.cover_url
      selectedCoverTempPath.value = filePath;
      coverPreviewUrl.value = filePath;
      ElMessage.info('已选择图片，创建成功后将上传，并以返回的URL展示');
    },
    fail: () => {
      ElMessage.error('选择图片失败');
    },
  });
};

const uploadCoverToServer = (roomId: string, filePath: string) => {
  return new Promise<void>((resolve, reject) => {
    const token = getToken();
    const uploadUrl = `${BASE_API_URL.replace(/\/+$/, '')}/rooms/${roomId}/cover`;
    
    // 添加上传调试信息
    console.log('=== 直播间封面上传调试信息 ===');
    console.log('上传URL:', uploadUrl);
    console.log('文件路径:', filePath);
    console.log('文件路径类型:', typeof filePath);
    console.log('是否为blob URL:', filePath.startsWith('blob:'));
    console.log('房间ID:', roomId);
    console.log('===============================');
    
    uni.uploadFile({
      url: uploadUrl,
      filePath,
      name: 'file',
      header: {
        Authorization: `Bearer ${token || ''}`,
      },
      success: (res) => {
        console.log('封面上传响应:', res);
        try {
          const body = JSON.parse(res.data || '{}');
          console.log('解析后的响应体:', body);
          if (res.statusCode >= 200 && res.statusCode < 300 && body?.code === 0) {
            // 后端返回的正式 URL，用于展示与后续刷新
            formModel.cover_url = body?.data?.cover_url || formModel.cover_url;
            console.log('封面上传成功，cover_url:', formModel.cover_url);
            return resolve();
          }
          reject(new Error(body?.message || `上传失败(${res.statusCode})`));
        } catch (e) {
          console.error('响应解析失败:', e);
          reject(new Error('响应解析失败'));
        }
      },
      fail: (err) => {
        console.error('封面上传失败:', err);
        reject(err);
      },
    });
  });
};

// --- 静态交互 ---
const showComingSoonToast = () => {
  ElMessage.info('功能待开发，敬请期待');
};

</script>

<style scoped>
.room-create-container .main-card {
  margin: 0 auto;
  padding-bottom: 80px; 
}

.form-wrapper {
  padding: 24px;
}

.main-form {
  margin-top: 32px;
}

.main-form :deep(.el-form-item__label) {
  font-weight: normal;
}

.form-item-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}

.cover-uploader :deep(.el-upload) {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
  width: 240px;
  height: 135px; /* 16:9 */
}

.cover-uploader :deep(.el-upload:hover) {
  border-color: var(--el-color-primary);
}

.uploader-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  color: #8c939d;
}
.uploader-placeholder .el-icon {
  font-size: 28px;
}
.uploader-placeholder span {
  font-size: 14px;
  margin-top: 8px;
}

.cover-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.fixed-action-bar {
  position: fixed;
  bottom: 0;
  left: 220px; /* 与侧边栏宽度一致 */
  right: 0;
  background-color: #fff;
  padding: 16px 24px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  z-index: 10;
  border-top: 1px solid var(--el-border-color-lighter);
}

.el-radio-group {
  display: flex;
  flex-wrap: wrap;
}

/* --- 样式覆盖：将 RadioButton 的选中样式从“背景填充”改为“边框高亮” --- */
:deep(.el-radio-button__inner) {
    background: #f5f7fa;
    color: #606266;
    border: 1px solid #dcdfe6;
    border-left: 0;
    box-shadow: none !important;
}

:deep(.el-radio-button:first-child .el-radio-button__inner) {
    border-left: 1px solid #dcdfe6;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
    background-color: #ffffff !important;
    color: var(--el-color-primary) !important;
    border-color: var(--el-color-primary) !important;
    box-shadow: -1px 0 0 0 var(--el-color-primary) !important;
}

:deep(.el-radio-button:first-child .el-radio-button__original-radio:checked + .el-radio-button__inner) {
    box-shadow: none !important;
}

:deep(.el-radio-button__inner:hover) {
    color: var(--el-color-primary);
}
</style>