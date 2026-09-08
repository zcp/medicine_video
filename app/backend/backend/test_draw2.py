import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

# --- 全局配置 ---
COLORS = {
    'hw_bg': '#FFF3E0',
    'sw_bg': '#FAFAFA',
    'untrusted': '#F5F5F5',
    'trusted': '#E1F5FE',
    'sensor': '#FFF9C4',
    'module_blue': '#90CAF9',
    'module_gray': '#EEEEEE',
    'module_hw': '#FFCC80',
    'line_pmp': '#D32F2F',  # PMP 红线
    'line_dma': '#BF360C',
    'text': '#212121'
}

FONT_SIZES = {
    'title': 26,
    'region': 24,
    'module': 20,
    'note': 18
}


def draw_fancy_box(ax, xy, width, height, color, label, edge_color='#757575', fontsize=20, fontweight='normal',
                   style='round,pad=0.2', align='center'):
    box = FancyBboxPatch(xy, width, height, boxstyle=style,
                         facecolor=color, edgecolor=edge_color, linewidth=2, zorder=10)
    ax.add_patch(box)

    tx, ty = xy[0] + width / 2, xy[1] + height / 2
    ha = 'center'
    if align == 'top_left':
        tx = xy[0] + 0.3
        ty = xy[1] + height - 0.4
        ha = 'left'

    ax.text(tx, ty, label, ha=ha, va='center',
            fontsize=fontsize, color=COLORS['text'], fontweight=fontweight, zorder=11)
    return box


def draw_arrow(ax, start, end, color='#455A64', style='-|>', lw=2.5, ls='-'):
    ax.annotate('', xy=end, xycoords='data', xytext=start, textcoords='data',
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls, shrinkA=0, shrinkB=0), zorder=12)


# ==========================================
# 图 1: 系统架构 (保持不变，为了代码完整性保留)
# ==========================================
def plot_architecture_final_v3():
    # 画布加宽到 8.5
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 11)
    ax.axis('off')

    # (此处省略图1的具体绘制代码，重点在于图2的更新，如果需要重新生成图1，请使用之前的代码)
    # 为了让代码可运行，这里简单占位，或者您可以把之前图1的代码复制过来
    print("图1代码请使用上一版本，重点更新在下面的图2")
    plt.close()


# ==========================================
# 图 2: 双向认证协议 (Bidirectional Auth) - 与论文 3.4 节严格一致
# ==========================================
def plot_protocol_bidirectional():
    # 增加高度，容纳更多步骤细节
    fig, ax = plt.subplots(figsize=(9.0, 13.5))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(0, 13.5)
    ax.axis('off')

    x_gw = 1.5
    x_linux = 4.5
    x_enc = 7.5  # 稍微拉宽一点，给 Enclave 内部逻辑框留空间

    # --- 1. 泳道头部 ---
    draw_fancy_box(ax, (x_gw - 1.0, 11.5), 2.0, 0.9, '#EEEEEE', 'Gateway', fontweight='bold',
                   fontsize=FONT_SIZES['module'])
    ax.plot([x_gw, x_gw], [0.5, 11.5], color='#BDBDBD', linestyle='--', lw=2)

    draw_fancy_box(ax, (x_linux - 1.0, 11.5), 2.0, 0.9, '#E0E0E0', 'Linux (Host)', fontweight='bold',
                   fontsize=FONT_SIZES['module'])
    ax.plot([x_linux, x_linux], [0.5, 11.5], color='#BDBDBD', linestyle='--', lw=2)

    draw_fancy_box(ax, (x_enc - 1.0, 11.5), 2.0, 0.9, '#BBDEFB', 'Enclave (TEE)', fontweight='bold',
                   fontsize=FONT_SIZES['module'])
    ax.plot([x_enc, x_enc], [0.5, 11.5], color='#BDBDBD', linestyle='--', lw=2)

    # --- PMP 隔离边界 ---
    x_pmp = (x_linux + x_enc) / 2
    ax.plot([x_pmp, x_pmp], [0.5, 12.8], color=COLORS['line_pmp'], linestyle='-.', lw=2)
    # 调整文字位置和大小，避免遮挡
    ax.text(x_pmp, 13.0, 'PMP Hardware Isolation Boundary', color=COLORS['line_pmp'], fontsize=16, fontweight='bold',
            ha='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.8))

    # --- 2. 交互流程 (双向认证逻辑) ---
    y = 10.5

    # [Step 1] 网关发起挑战 (含签名)
    # 论文对应: "网关生成挑战随机数 N_G...签名形成 Sigma_G...发送至设备"
    draw_arrow(ax, (x_gw, y), (x_linux, y), color='black')
    ax.text((x_gw + x_linux) / 2, y + 0.2, '1. Req (N_G, Sig_G)', ha='center', fontsize=FONT_SIZES['note'],
            fontweight='bold')

    y -= 1.2
    ax.text(x_linux + 0.1, y, 'Copy to UTM\n(Shared Mem)', ha='left', fontsize=16, color='#616161')

    y -= 0.8
    # [Step 2] ECALL 进入 Enclave
    draw_arrow(ax, (x_linux, y), (x_enc, y), color='#2E7D32', lw=3)
    ax.text((x_linux + x_enc) / 2, y + 0.2, '2. ECALL', ha='center', fontsize=FONT_SIZES['note'], color='#1B5E20',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.9))

    # [Enclave 内部逻辑] - 关键修改点
    # 论文对应: "Enclave...验证 Sigma_G...生成 N_D...对(N_G||N_D)签名"
    y -= 3.0
    logic_text = "Logic:\n1. Verify Sig_G\n2. Gen Nonce_D\n3. SM2 Sign"
    box_width = 2.6
    box_x = x_enc - (box_width / 2)

    # 绘制黄色逻辑框
    draw_fancy_box(ax, (box_x, y), box_width, 2.4, '#FFF9C4', logic_text, edge_color='#FBC02D',
                   fontsize=FONT_SIZES['note'], style='round,pad=0.2')

    y -= 1.2
    # [Step 3] 返回 Linux
    draw_arrow(ax, (x_enc, y), (x_linux, y), color='#2E7D32', lw=3, ls='--')
    ax.text((x_linux + x_enc) / 2, y + 0.2, '3. Return', ha='center', fontsize=FONT_SIZES['note'], color='#1B5E20')

    y -= 1.5
    # [Step 4] 响应网关 (含设备签名)
    # 论文对应: "Linux...将 Resp (Sig_D, N_D) 发送回网关"
    draw_arrow(ax, (x_linux, y), (x_gw, y), color='black')
    ax.text((x_gw + x_linux) / 2, y + 0.2, '4. Resp (Sig_D, N_D)', ha='center', fontsize=FONT_SIZES['note'],
            fontweight='bold')

    y -= 2.2
    # [网关验证 & 密钥生成]
    # 论文对应: "验证 Cert_D...验签...HKDF 派生 K_sess"
    verify_text = "Gateway Actions:\n• Verify Sig_D\n• HKDF Gen Key"
    draw_fancy_box(ax, (0.2, y), 2.6, 1.8, '#F5F5F5', verify_text, edge_color='#BDBDBD', fontsize=FONT_SIZES['note'],
                   style='round,pad=0.2', align='center')

    y -= 0.8
    # [Step 5] 成功建立连接
    draw_arrow(ax, (x_gw, y), (x_linux, y), color='#43A047', lw=3)
    ax.text((x_gw + x_linux) / 2, y + 0.2, '5. Session Established', ha='center', fontsize=FONT_SIZES['note'],
            color='#2E7D32', fontweight='bold')

    plt.tight_layout(pad=1.0)
    plt.savefig('Fig3_3_Proto_Bidirectional.svg', format='svg', bbox_inches='tight', pad_inches=0.1)
    plt.savefig('Fig3_3_Proto_Bidirectional.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    print("生成: Fig3_3_Proto_Bidirectional.svg (双向认证版)")
    plt.close()


if __name__ == "__main__":
    plot_protocol_bidirectional()