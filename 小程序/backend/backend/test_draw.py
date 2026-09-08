import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

# --- IEEE 学术配色 ---
COLORS = {
    'hw_bg': '#FFF3E0',  # 硬件层
    'linux_bg': '#FAFAFA',  # 不可信域
    'enclave_bg': '#E3F2FD',  # 可信域
    'module_gray': '#EEEEEE',
    'module_blue': '#BBDEFB',  # 基础组件
    'module_core': '#64B5F6',  # 核心逻辑
    'module_hw': '#FFCC80',  # 硬件模块 (深橙黄)
    'pmp_hw': '#FFAB91',  # PMP 硬件特有颜色 (突显)
    'line_pmp': '#D32F2F',  # PMP 红线
    'line_dma': '#E65100',  # DMA 橙红线
    'line_call': '#1565C0',  # 内部调用线
    'text': '#263238'
}


def draw_box(ax, xy, w, h, color, label, fontsize=10, fontweight='normal', alpha=1.0, zorder=2, align='center',
             edge_color='none', linestyle='-'):
    box = FancyBboxPatch(xy, w, h, boxstyle='round,pad=0.1', fc=color, ec=edge_color, alpha=alpha, zorder=zorder,
                         linestyle=linestyle)
    ax.add_patch(box)

    cx, cy = xy[0] + w / 2, xy[1] + h / 2
    ha = 'center'
    if align == 'top':
        cy = xy[1] + h - 0.3

    ax.text(cx, cy, label, ha=ha, va='center', fontsize=fontsize, fontweight=fontweight, color=COLORS['text'],
            zorder=zorder + 1)
    return box


def draw_arrow(ax, start, end, color='black', style='-|>', lw=1.5, connectionstyle="arc3"):
    ax.annotate('', xy=end, xycoords='data', xytext=start, textcoords='data',
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=0,
                                connectionstyle=connectionstyle), zorder=15)


def plot_final_complete_architecture():
    fig, ax = plt.subplots(figsize=(10, 8.5))  # 稍微增加高度以容纳细节
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # ==========================
    # 1. 区域与背景
    # ==========================
    # 硬件层
    draw_box(ax, (0, 0), 10, 1.8, COLORS['hw_bg'], '')
    ax.text(5, 0.2, 'RISC-V Hardware Layer', fontsize=12, fontweight='bold', color='#EF6C00', ha='center')

    # 不可信域
    draw_box(ax, (0, 2.0), 4.5, 6.2, COLORS['linux_bg'], '')
    ax.text(2.25, 7.9, 'Untrusted Domain\n(Linux Host)', fontsize=12, fontweight='bold', color='#757575', ha='center')

    # 可信域
    draw_box(ax, (4.8, 2.0), 5.2, 6.2, COLORS['enclave_bg'], '')
    ax.text(7.4, 7.9, 'Trusted Domain\n(Keystone Enclave)', fontsize=12, fontweight='bold', color='#1565C0',
            ha='center')

    # PMP 隔离线 (核心视觉元素)
    # 这条线现在明确地从底部的 PMP 硬件单元延伸出来
    ax.plot([4.65, 4.65], [1.5, 8.5], color=COLORS['line_pmp'], linestyle='--', lw=2, zorder=5)
    ax.text(4.65, 8.3, 'PMP Isolation Boundary', color=COLORS['line_pmp'], fontsize=9, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=COLORS['line_pmp']))

    # ==========================
    # 2. 硬件模块 (补全 PMP)
    # ==========================

    # [新增] PMP Unit - 放在正中间，支撑隔离线
    draw_box(ax, (3.9, 0.6), 1.5, 0.9, COLORS['pmp_hw'], 'PMP Unit\n(Enforcement)', fontweight='bold',
             edge_color=COLORS['line_pmp'], linestyle='-')

    # DMA Controller - 在左侧
    draw_box(ax, (1.5, 0.6), 1.5, 0.9, COLORS['module_hw'], 'DMA\nController')

    # Secure Storage - 在右侧
    draw_box(ax, (6.5, 0.6), 2.5, 0.9, COLORS['module_hw'], 'Secure Storage\n(Root Key)', fontweight='bold')

    # 外部传感器
    draw_box(ax, (-1.2, 3.5), 1.5, 1.2, '#FFF9C4', 'Sensor\nSource', fontweight='bold', edge_color='#FBC02D')

    # ==========================
    # 3. 软件模块
    # ==========================
    # Linux
    draw_box(ax, (0.8, 6.0), 2.8, 1.2, COLORS['module_gray'], 'Linux Kernel')
    draw_box(ax, (0.8, 3.5), 2.8, 1.2, COLORS['module_gray'], 'Network Stack')

    # Enclave 内部结构
    # Eyrie (调度层)
    draw_box(ax, (5.2, 6.2), 4.4, 1.0, COLORS['module_blue'], 'Eyrie Runtime (OS/Scheduling)')

    # 业务逻辑层 (Crypto + Logic)
    crypto_bg = FancyBboxPatch((5.2, 4.2), 4.4, 1.6, boxstyle='round,pad=0.1', fc='#E1F5FE', ec='#BBDEFB',
                               linestyle='--', zorder=3)
    ax.add_patch(crypto_bg)
    ax.text(7.4, 5.5, 'Crypto Services', fontsize=9, color='#1565C0', ha='center', zorder=4)

    draw_box(ax, (5.4, 4.4), 1.8, 1.0, '#90CAF9', 'SM2 Sign', zorder=4)
    draw_box(ax, (7.6, 4.4), 1.8, 1.0, '#90CAF9', 'HKDF', zorder=4)

    # 数据处理层 (TDP)
    draw_box(ax, (5.2, 2.5), 4.4, 1.2, COLORS['module_core'], 'Trusted Data Packaging (TDP)', fontweight='bold',
             zorder=4)

    # ==========================
    # 4. 关键连线与逻辑流
    # ==========================

    # [逻辑流 1] ECALL: Linux -> Eyrie
    draw_arrow(ax, (3.6, 6.6), (5.2, 6.6), color='#2E7D32', style='<|-|>', lw=2)
    ax.text(4.4, 6.8, 'ECALL', color='#2E7D32', fontsize=9, fontweight='bold', ha='center')

    # Eyrie Dispatch
    draw_arrow(ax, (7.4, 6.2), (7.4, 5.8), color=COLORS['line_call'], lw=1.5)

    # [逻辑流 2] TDP -> SM2 (调用签名)
    draw_arrow(ax, (6.0, 3.7), (6.0, 4.4), color=COLORS['line_call'], lw=1.5)
    ax.text(6.1, 4.0, 'Call Sign()', fontsize=8, color=COLORS['line_call'], ha='left')

    # [逻辑流 3] SM2 -> HKDF (协议顺序)
    draw_arrow(ax, (7.2, 4.9), (7.6, 4.9), color=COLORS['line_call'], lw=1.5, style='->')
    ax.text(7.4, 5.0, 'Seq', fontsize=8, color=COLORS['line_call'], ha='center')

    # [数据流 4] Key Load: Storage -> SM2
    draw_arrow(ax, (7.5, 1.5), (6.8, 4.4), color='#E65100', lw=2)
    ax.text(7.6, 2.0, 'Load PrvKey', color='#E65100', fontsize=8)

    # [数据流 5] DMA Bypass: Sensor -> DMA -> TDP
    # 线段 A: Sensor -> DMA
    ax.annotate('', xy=(1.5, 1.0), xytext=(0.3, 3.5),
                arrowprops=dict(arrowstyle='->', color=COLORS['line_dma'], lw=2, connectionstyle="arc3,rad=0.1"),
                zorder=10)
    # 线段 B: DMA -> TDP (注意：穿过 PMP 边界)
    ax.annotate('', xy=(5.2, 3.1), xytext=(3.0, 1.0),
                arrowprops=dict(arrowstyle='->', color=COLORS['line_dma'], lw=2, connectionstyle="arc3,rad=-0.1"),
                zorder=10)

    ax.text(2.5, 2.2, 'DMA Direct Write\n(Bypass OS)', color=COLORS['line_dma'], fontsize=9, fontweight='bold',
            ha='center', rotation=-15,
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.8))

    # [数据流 6] Encrypted Output
    draw_arrow(ax, (5.2, 3.1), (3.6, 4.0), color='#616161', lw=1.5)
    ax.text(4.4, 3.6, 'Encrypted', color='#616161', fontsize=8, ha='center')

    plt.tight_layout()
    plt.savefig('Final_Architecture_Corrected.svg', format='svg', bbox_inches='tight')
    plt.savefig('Final_Architecture_Corrected.png', dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    plot_final_complete_architecture()