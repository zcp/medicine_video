import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import textwrap

# ==========================================
# 1. 字体与全局设置
# ==========================================
# 设置中文字体优先级
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'STSong', 'Songti SC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'cm'

# 定义字号常量
FS_TITLE = 18
FS_BOX_TITLE = 14
FS_TEXT = 12
FS_ARROW = 11
FS_LEGEND = 11

# 定义颜色常量
C_EDGE = '#EAF2FF'  # 浅蓝
C_IPFS = '#EAFBEA'  # 浅绿
C_BC = '#FFF7E6'  # 浅黄
C_REC = '#F2F0FF'  # 浅紫灰
C_BORDER = '#222222'  # 深色边框
C_ARROW_DATA = '#1F4E79'  # 深蓝实线
C_ARROW_TRUST = '#B45F06'  # 深橙虚线

# ==========================================
# 2. 画布设置
# ==========================================
fig, ax = plt.subplots(figsize=(13.5, 5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 25)
ax.axis('off')


# ==========================================
# 3. 绘制模块函数
# ==========================================
def draw_module(x, y, w, h, title, content_list, fill_color):
    # 1. 绘制圆角矩形背景
    # 注意：FancyBboxPatch 的 (x,y) 是左下角，宽高是 box 的尺寸
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.3,rounding_size=0.15",
        fc=fill_color,
        ec=C_BORDER,
        linewidth=1.5,
        zorder=10
    )
    ax.add_patch(box)

    # 2. 绘制标题分隔线 (约顶部下方 25% 处)
    # 考虑 padding，实际视觉边界会比 x,y,w,h 略大，这里在逻辑坐标内绘制
    sep_y = y + h * 0.72
    ax.plot([x, x + w], [sep_y, sep_y], color=C_BORDER, linewidth=1.0, zorder=11)

    # 3. 绘制标题
    # 标题居中位于分隔线上方
    title_y = y + h * 0.86
    ax.text(x + w / 2, title_y, title,
            ha='center', va='center',
            fontsize=FS_BOX_TITLE, fontweight='bold', color=C_BORDER, zorder=12)

    # 4. 绘制内容
    # 内容位于分隔线下方，左对齐
    # 使用 textwrap 自动换行
    content_start_y = sep_y - 1.5
    line_height = 2.0  # 行间距

    current_y = content_start_y
    for item in content_list:
        # 自动换行处理 (假设每行约 10-12 个全角字符宽度，这里 wrap_width 设为 14 个英文字符宽度的估算值)
        wrapped_lines = textwrap.wrap(item, width=16)
        for line in wrapped_lines:
            ax.text(x + 1, current_y, line,
                    ha='left', va='top',
                    fontsize=FS_TEXT, color=C_BORDER, zorder=12)
            current_y -= line_height


# ==========================================
# 4. 定义模块数据并绘制
# ==========================================
# 坐标定义 (x, y, w, h)
edge_coords = (5, 10, 14, 12)
ipfs_coords = (30, 10, 14, 12)
bc_coords = (55, 10, 14, 12)
rec_coords = (80, 10, 14, 12)

# 绘制 Edge 模块
draw_module(*edge_coords,
            title="边缘采集与快照固化\n(Edge)",
            content_list=["□ IoT 传感数据采集", "□ 事件触发加密快照", "   S=(X,M)"],
            fill_color=C_EDGE)

# 绘制 IPFS 模块
draw_module(*ipfs_coords,
            title="分布式抗毁存储\n(IPFS)",
            content_list=["□ 分片：F1..Fm", "□ 冗余扩散：副本 r", "□ 分散间隔：d_min"],
            fill_color=C_IPFS)

# 绘制 Blockchain 模块
draw_module(*bc_coords,
            title="可信存证索引\n(轻量区块链)",
            content_list=["□ 仅上链：CID +", "   元数据哈希", "□ 可审计索引", "  (Anchor Record)"],
            fill_color=C_BC)

# 绘制 Recovery 模块
draw_module(*rec_coords,
            title="灾后恢复与 BIM 重建\n(Recovery)",
            content_list=["□ 链上查询索引", "□ 拉取分片 +", "   哈希校验", "□ 重组快照并映射 BIM"],
            fill_color=C_REC)


# ==========================================
# 5. 绘制箭头连线
# ==========================================
def draw_arrow(start_point, end_point, style, color, label, label_offset=(0, 0), curve_rad=0.0):
    connection_style = f"arc3,rad={curve_rad}"

    arrow = FancyArrowPatch(
        start_point, end_point,
        connectionstyle=connection_style,
        arrowstyle='-|>',
        mutation_scale=20,
        color=color,
        linestyle=style,
        linewidth=2,
        shrinkA=0, shrinkB=0,
        zorder=20
    )
    ax.add_patch(arrow)

    # 计算标签位置 (简单中点)
    if curve_rad == 0:
        mid_x = (start_point[0] + end_point[0]) / 2
        mid_y = (start_point[1] + end_point[1]) / 2
    else:
        # 简单估算弧线中点，向下偏移
        mid_x = (start_point[0] + end_point[0]) / 2
        # 如果是向下弯曲 (rad < 0) 或 向上弯曲 (rad > 0)，这里简单处理下弯
        mid_y = min(start_point[1], end_point[1]) - abs(start_point[0] - end_point[0]) * abs(curve_rad) * 0.3

    lbl_x = mid_x + label_offset[0]
    lbl_y = mid_y + label_offset[1]

    ax.text(lbl_x, lbl_y, label,
            ha='center', va='center',
            fontsize=FS_ARROW, color=color,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5),
            zorder=21)


# 定义连接点
p_edge_right = (edge_coords[0] + edge_coords[2] + 0.3, 16)  # y=16 是大致中心高度
p_ipfs_left = (ipfs_coords[0] - 0.3, 16)
p_ipfs_right = (ipfs_coords[0] + ipfs_coords[2] + 0.3, 16)
p_bc_left = (bc_coords[0] - 0.3, 16)
p_bc_right = (bc_coords[0] + bc_coords[2] + 0.3, 16)
p_rec_left = (rec_coords[0] - 0.3, 16)

# 底部连接点用于弧线
p_ipfs_bottom = (ipfs_coords[0] + ipfs_coords[2] / 2, ipfs_coords[1] - 0.3)
p_rec_bottom = (rec_coords[0] + rec_coords[2] / 2, rec_coords[1] - 0.3)

# 1. Edge -> IPFS (实线，深蓝)
draw_arrow(p_edge_right, p_ipfs_left, 'solid', C_ARROW_DATA, "快照数据\n(加密序列化)")

# 2. IPFS -> Blockchain (虚线，深橙)
draw_arrow(p_ipfs_right, p_bc_left, 'dashed', C_ARROW_TRUST, "CID 列表 +\n元数据哈希")

# 3. Blockchain -> Recovery (虚线，深橙)
draw_arrow(p_bc_right, p_rec_left, 'dashed', C_ARROW_TRUST, "返回锚定记录\n(可信索引)")

# 4. IPFS -> Recovery (下方弧线，实线，深蓝)
# 使用 connectionstyle="arc3,rad=0.25" 下弯
draw_arrow(p_ipfs_bottom, p_rec_bottom, 'solid', C_ARROW_DATA,
           "分片检索与重组 (Recover Snapshot)",
           label_offset=(0, 0.05), curve_rad=0.25)

# ==========================================
# 6. 绘制图例与标题
# ==========================================
# 标题
#ax.text(50, 32, "图3-1 面向深部地下断网场景的 BIM-IoT 数据抗毁存储机制总体架构",
#        ha='center', va='center',
#        fontsize=FS_TITLE, fontweight='bold', color='black', zorder=30)

# 图例 (右下角)
legend_x = 5
legend_y = 4
legend_gap = 2.5

# 实线图例
ax.plot([legend_x, legend_x + 6], [legend_y + legend_gap, legend_y + legend_gap],
        color=C_ARROW_DATA, lw=2, linestyle='solid', zorder=30)
ax.text(legend_x + 7, legend_y + legend_gap, "数据生存链路 (Data Flow)",
        ha='left', va='center', fontsize=FS_LEGEND, color='#333333', zorder=30)

# 虚线图例
ax.plot([legend_x, legend_x + 6], [legend_y, legend_y],
        color=C_ARROW_TRUST, lw=2, linestyle='dashed', zorder=30)
ax.text(legend_x + 7, legend_y, "可信验证链路 (Trust Flow)",
        ha='left', va='center', fontsize=FS_LEGEND, color='#333333', zorder=30)

# ==========================================
# 7. 保存输出
# ==========================================
plt.tight_layout()
plt.savefig('fig3_1.svg', format='svg', bbox_inches='tight', pad_inches=0.1)
plt.savefig('fig3_1.png', format='png', dpi=300, bbox_inches='tight', pad_inches=0.1)

print("生成成功：fig3_1.svg, fig3_1.png")
plt.show()