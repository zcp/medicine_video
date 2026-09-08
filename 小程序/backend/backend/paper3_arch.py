import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from matplotlib import rcParams

# 设置字体，确保支持中文 (如果在本地运行，请确保有SimHei或类似字体)
# 如果是英文环境，可以尝试 'Arial Unicode MS' 或其他支持中文的字体
rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# --- 全局配色方案 (学术风格) ---
COLORS = {
    'edge_bg': '#F5F5F5',  # 边缘域背景 (浅灰)
    'offchain_bg': '#E1F5FE',  # 链下存储背景 (浅蓝)
    'onchain_bg': '#FFF3E0',  # 链上审计背景 (浅橙)
    'dr_bg': '#F3E5F5',  # 容灾恢复背景 (浅紫)
    'box_edge': '#607D8B',  # 边框颜色
    'text': '#37474F',  # 字体颜色
    'arrow': '#455A64',  # 箭头颜色
    'highlight': '#0277BD'  # 强调色
}


def draw_fancy_box(ax, xy, width, height, color, label, fontsize=22, fontweight='normal',
                   edge_color=COLORS['box_edge']):
    """绘制带有圆角和文本的矩形框"""
    box = FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.1",
                         ec=edge_color, fc=color, lw=1.5, zorder=2)
    ax.add_patch(box)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, label, ha='center', va='center',
            fontsize=fontsize, fontweight=fontweight, color=COLORS['text'], zorder=3)
    return box


def draw_domain_bg(ax, xy, width, height, color, label):
    """绘制区域背景块"""
    rect = patches.Rectangle(xy, width, height, linewidth=0, facecolor=color, alpha=0.6, zorder=0)
    ax.add_patch(rect)
    # 区域标题
    ax.text(xy[0] + 0.2, xy[1] + height - 0.5, label, ha='left', va='center',
            fontsize=22, fontweight='bold', color='#424242', zorder=1)


def draw_arrow(ax, start, end, label=None,
               linestyle='-', connectionstyle="arc3,rad=0"):
    """绘制稳定的学术级箭头（PNG / SVG / PDF 友好）"""
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle='-|>',          # 关键：稳定箭头头
            color=COLORS['arrow'],
            lw=1.6,
            linestyle=linestyle,
            mutation_scale=18,          # 关键：箭头头大小
            connectionstyle=connectionstyle
        ),
        zorder=5                        # 关键：必须高于 box
    )

    if label:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(
            mid_x, mid_y, label,
            ha='center', va='center',
            fontsize=16,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.9),
            zorder=6
        )

def main():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # --- 1. 绘制四个主要区域 (Domains) ---

    # 左上：边缘域 (Edge Domain)
    draw_domain_bg(ax, (0, 5.5), 4, 4.2, COLORS['edge_bg'], "边缘域\n\n")

    # 中上：链下存储平面 (Off-chain Storage)
    draw_domain_bg(ax, (5, 5.5), 4, 4.2, COLORS['offchain_bg'], "链下存储层\n\n")

    # 中下：链上审计平面 (On-chain Audit)
    draw_domain_bg(ax, (5, 0.5), 4, 4.2, COLORS['onchain_bg'], "链上审计层\n\n")

    # 右侧：容灾与恢复平面 (DR & Recovery)
    draw_domain_bg(ax, (9.5, 0.5), 4, 9.2, COLORS['dr_bg'], "容灾与恢复层\n\n")

    # --- 2. 绘制具体模块 (Nodes) ---

    # 边缘域模块
    prod = draw_fancy_box(ax, (0.5, 8), 3, 1, '#FFFFFF', "数据生产者\n(IoT/Robots/Sensors)")
    relay = draw_fancy_box(ax, (0.5, 6.5), 3, 1, '#FFFFFF', "机会性中继")

    # 链下存储模块
    ipfs = draw_fancy_box(ax, (5.5, 8), 3, 1, '#FFFFFF', "IPFS 内容寻址存储\n(CID/Merkle-DAG)")
    pinning = draw_fancy_box(ax, (5.5, 6.5), 3, 1, '#FFFFFF', "副本与持久化管理")

    # 链上审计模块
    ledger = draw_fancy_box(ax, (5.5, 3), 3, 1, '#FFFFFF', "联盟账本\n($<A, ver, CID, t, σ>$")
    contract = draw_fancy_box(ax, (5.5, 1.5), 3, 1, '#FFFFFF', "审计合约")

    # 容灾与恢复模块
    policy = draw_fancy_box(ax, (10, 7.5), 3, 1, '#FFFFFF', "容灾放置策略\n($\\pi = <n, k, r>$)")
    verify = draw_fancy_box(ax, (10, 4.5), 3, 1, '#FFFFFF', "恢复与一致性验证")
    recover = draw_fancy_box(ax, (10, 2), 3, 1, '#FFFFFF', "数据恢复/解密")


    # --- 3. 绘制连接线 (Arrows) ---

    # 数据流：边缘 -> IPFS
    draw_arrow(ax, (3.6, 8.5), (5.45, 8.5), label="上传分片\n\nManifest")
    draw_arrow(ax, (3.6, 7), (5.45, 7), label="中继同步", linestyle="--")

    # 内部流：IPFS -> Pinning
    draw_arrow(ax, (7, 7.94), (7, 7.55))

    # 锚定流：Pinning -> Ledger
    draw_arrow(ax, (7, 6.44), (7, 4.05), label="CID 锚定/锁定")

    # 内部流：Ledger -> Contract
    draw_arrow(ax, (7, 2.94), (7, 2.55))

    # 策略流：Policy -> Pinning (策略驱动副本) - 跨域
    draw_arrow(ax, (9.92, 8), (8.55, 7), label="策略驱动", linestyle="--")

    # 恢复流 1: 查询链上入口
    draw_arrow(ax, (9.92, 5), (8.55, 3.5), label="1. 查询权威CID")

    # 恢复流 2: 拉取链下数据
    draw_arrow(ax, (9.92, 5), (8.5, 7.95), label="2. 拉取数据", connectionstyle="arc3,rad=-0.3")

    # 恢复流 3: 验证 -> 恢复
    draw_arrow(ax, (11.5, 4.43), (11.5, 3.05))

    plt.tight_layout()

    plt.savefig('论文3_架构图.svg', format='svg', bbox_inches='tight', pad_inches=0.1)
    plt.savefig('论文3_架构图.png', dpi=300, bbox_inches='tight', pad_inches=0.1)


    plt.show()


if __name__ == "__main__":
    main()