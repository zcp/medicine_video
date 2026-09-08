# 医疗风格素材目录

## 用途

本目录用于存放首页 Banner / 封面的**医疗风格占位与 fallback 素材**，确保应用视觉始终符合医疗专业定位。

## 要求的素材文件

1. **`banner_med_1.jpg`** - Banner 轮播占位图（800×400px 或更高分辨率）
2. **`cover_placeholder.png`** - 回放卡片封面占位图（750×420px 或 16:9 比例）
3. 可选：`banner_med_2.jpg`、`banner_med_3.jpg` 等（多个 Banner fallback）

## 风格要求（强制）

### ✅ 允许使用的风格：
- **医疗场景**：手术室、医院走廊、会诊场景、医疗设备
- **学术会议**：会议厅、讲台、医学专家演讲
- **医院环境**：三甲医院外观、病房、诊疗室
- **抽象医学纹理**：DNA 双螺旋、细胞图谱、心电图纹理、医学图标组合
- **中性专业色调**：浅蓝、浅灰、白色为主，干净简洁

### ❌ 禁止使用的风格：
- ❌ 生活摄影：花草、食物、咖啡、风景、城市街景
- ❌ 非医疗场景：办公室、家居、户外、军事、工业
- ❌ 过度装饰性图案：几何图案、渐变色块（除非极简医学风）

## 实现方式

当前代码中：
- `FeaturedCarousel.vue`：Mock 数据时使用 picsum.photos 临时占位，后端 API 返回的真实 `image_url` 会优先显示。如需医疗风格 fallback，将 `getDefaultCampaigns()` 中的 `image_url` 改为 `/static/med/banner_med_1.jpg` 等本地路径。
- `RoomCard.vue`：`defaultCover` 已设为 `/static/med/cover_placeholder.png`，后端无图时自动使用。

## 素材来源建议

1. **Unsplash**：搜索 `hospital`, `medical conference`, `doctor`, `healthcare` 等关键词（注意版权）
2. **自有素材**：使用平台真实医院/会议照片
3. **设计工具**：Figma / Canva 制作简洁医学纹理背景（如渐变 + 医学图标）

## 注意事项

- 素材文件大小建议控制在 200KB 以内（优化加载速度）
- 图片宽高比：Banner 约 2:1，封面 16:9
- 确保图片清晰度足够在移动端高分屏显示
