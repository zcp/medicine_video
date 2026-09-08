import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import matplotlib.font_manager as fm


# ==========================================
# 1. 字体与排版配置
# ==========================================
def set_matplot_zh_font():
    font_names = [
        'SimSun', 'STSong',  # 宋体
        'Microsoft YaHei',  # 雅黑
        'SimHei',  # 黑体
        'Arial Unicode MS'
    ]

    found_font = None
    for name in font_names:
        if name in [f.name for f in fm.fontManager.ttflist]:
            found_font = name
            break

    if found_font:
        plt.rcParams['font.sans-serif'] = [found_font] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        print(f"成功加载中文字体: {found_font}")
    else:
        plt.rcParams['font.sans-serif'] = ['sans-serif']

    plt.rcParams['mathtext.fontset'] = 'cm'


set_matplot_zh_font()

# --- 字号定义 (已调大一号) ---
FS_TITLE = 14.0   # 原 12.0
FS_BODY = 12.0    # 原 10.5
FS_NOTE = 10.5    # 原 9.0

# --- 绘图风格 ---
LW_BOX = 1.0
LW_ARROW = 1.0
C_BORDER = "#000000"
C_BORDER_SUB = "#444444"
C_TEXT = "#000000"
C_TEXT_SUB = "#555555"
C_BG_BOX = "#FFFFFF"
C_BG_ENCLAVE = "#F9F9F9"
C_BG_YELLOW = "#FFFBF0"
C_BG_SM = "#F2F2F2"


# ==========================================
# 2. 绘图辅助函数
# ==========================================
def draw_box(ax, x, y, w, h, text, subtitle=None, bg=C_BG_BOX, ec=C_BORDER, lw=LW_BOX, z=10):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        facecolor=bg, edgecolor=ec, linewidth=lw, zorder=z
    )
    ax.add_patch(rect)

    cx, cy = x + w / 2, y + h / 2

    if subtitle:
        ax.text(cx, cy + h * 0.15, text, ha="center", va="center",
                fontsize=FS_BODY, fontweight='bold', color=C_TEXT, zorder=z + 1)
        ax.text(cx, cy - h * 0.20, subtitle, ha="center", va="center",
                fontsize=FS_NOTE, color=C_TEXT, zorder=z + 1)
    else:
        ax.text(cx, cy, text, ha="center", va="center",
                fontsize=FS_BODY, color=C_TEXT, zorder=z + 1, linespacing=1.5)

    return {'x': x, 'y': y, 'w': w, 'h': h, 'cx': cx, 'cy': cy}


def draw_arrow_straight(ax, start_xy, end_xy, text=None, offset=(0, 0), color=C_BORDER, lw=LW_ARROW):
    ax.annotate(
        "", xy=end_xy, xytext=start_xy,
        arrowprops=dict(arrowstyle="->", color=color, lw=lw, shrinkA=0, shrinkB=0),
        zorder=20
    )
    if text:
        mx = (start_xy[0] + end_xy[0]) / 2 + offset[0]
        my = (start_xy[1] + end_xy[1]) / 2 + offset[1]
        ax.text(mx, my, text, ha="center", va="center", fontsize=FS_BODY,
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=1),
                zorder=21)


# ==========================================
# 3. 主绘图逻辑
# ==========================================
fig, ax = plt.subplots(1, 1, figsize=(13, 7.5))
ax.set_xlim(0, 25)
ax.set_ylim(0, 15)
ax.set_aspect("equal")
ax.axis("off")

# --- 布局参数 ---
enclave_x, enclave_y = 5.0, 4.5
enclave_w, enclave_h = 12.0, 9.0

role_w, role_h = 3.5, 1.8
prover_x = 0.5
verifier_x = 19.0
verifier_y = 6.5

box_w, box_h = 3.8, 1.5
col1_x = enclave_x + 0.8
col2_x = enclave_x + 6.8

GAP_Y = 1.8

# 左侧模块 Y 坐标
y_guard = enclave_y + enclave_h - 2.2
y_rule = y_guard - (box_h + GAP_Y)
y_zk = y_rule - (box_h + GAP_Y)

# 右侧模块 Y 坐标 (显著上移)
y_key = y_rule + 1.5
y_rng = y_key - (box_h + 1.2)

# ----------------------------
# A. Enclave (可信域)
# ----------------------------
enc_rect = FancyBboxPatch(
    (enclave_x, enclave_y), enclave_w, enclave_h,
    boxstyle="round,pad=0.2,rounding_size=0.4",
    facecolor=C_BG_ENCLAVE, edgecolor=C_BORDER, linewidth=1.5, zorder=5
)
ax.add_patch(enc_rect)
ax.text(enclave_x + enclave_w / 2, enclave_y + enclave_h - 0.3,
        "RISC-V Keystone Enclave (可信域)",
        ha="center", fontsize=FS_TITLE, fontweight='bold', zorder=6)

# ----------------------------
# B. Enclave 内部模块
# ----------------------------
box_guard = draw_box(ax, col1_x, y_guard, box_w, box_h, "属性门控")
box_rule = draw_box(ax, col1_x, y_rule, box_w, box_h, "规则求值")
box_zk = draw_box(ax, col1_x, y_zk, box_w, box_h, "ZK 证明生成\nSigma + Fiat–Shamir \n (SM2)")
box_key = draw_box(ax, col2_x, y_key, box_w, box_h, "密钥与封存")
box_rng = draw_box(ax, col2_x, y_rng, box_w, box_h, "随机性与防回放")

# --- 内部连线 ---

# 1. Guard -> Rule
draw_arrow_straight(ax,
                    (box_guard['cx'], box_guard['y']),
                    (box_rule['cx'], box_rule['y'] + box_rule['h']),
                    text="规则相关属性", offset=(0, 0))

# 2. Rule -> ZK
draw_arrow_straight(ax,
                    (box_rule['cx'], box_rule['y']),
                    (box_zk['cx'], box_zk['y'] + box_zk['h']),
                    text=r"若 $\varphi_{rid}(\mathbf{x}) = \text{true}$", offset=(0, 0))

# --- 关键连线修改 (使用 arc3 彻底避免报错) ---

# 3. Key -> ZK (从 Key 左侧 -> ZK 右侧偏上)
key_start = (box_key['x'], box_key['cy'])
zk_right_upper = (box_zk['x'] + box_zk['w'], box_zk['cy'])

conn_key = ConnectionPatch(
    xyA=key_start, xyB=zk_right_upper, coordsA="data", coordsB="data",
    axesA=ax, axesB=ax,
    arrowstyle="->", color=C_BORDER_SUB, lw=LW_ARROW,
    # 【修复】：使用 arc3，rad=0.2 表示轻微向上弯曲的弧线
    #connectionstyle="arc3,rad=0.2",
    zorder=5
)
ax.add_patch(conn_key)

# 标签
label_x_key = (key_start[0] + zk_right_upper[0]) / 2  + 0.8
label_y_key = (key_start[1] + zk_right_upper[1]) / 2 + 0.6
ax.text(label_x_key, label_y_key,
        r"签名 $H(\pi \parallel y) \to \sigma_E$",
        fontsize=FS_NOTE, color=C_BORDER_SUB, ha="center", va="bottom",
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=0.3), zorder=25)

# 4. RNG -> ZK (从 RNG 下方 -> ZK 右侧偏下)
rng_bottom = (box_rng['cx'], box_rng['y'])
zk_right_lower = (box_zk['x'] + box_zk['w'], box_zk['cy'])

conn_rng = ConnectionPatch(
    xyA=rng_bottom, xyB=zk_right_lower, coordsA="data", coordsB="data",
    axesA=ax, axesB=ax,
    arrowstyle="->", color=C_BORDER_SUB, lw=LW_ARROW,
    # 【修复】：使用 arc3，rad=-0.4 表示向下弯曲的弧线，从底部绕过去
    #connectionstyle="arc3,rad=-0.4",
    zorder=5
)
ax.add_patch(conn_rng)

# 标签
# 计算弧线路径上的点 (近似)
label_x_rng = (rng_bottom[0] + zk_right_lower[0]) / 2 + 1.5
label_y_rng = zk_right_lower[1] +1
ax.text(label_x_rng, label_y_rng,
        r"随机性 + 推导 FS 挑战 $e$",
        fontsize=FS_NOTE, color=C_BORDER_SUB, ha="center", va="top",
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=0.3), zorder=25)

# ----------------------------
# C. 证明方 (左侧)
# ----------------------------
prover_y = box_guard['cy'] - role_h / 2
box_prover = draw_box(ax, prover_x, prover_y, role_w, role_h, "证明方", "(设计院 / 施工方)")

draw_arrow_straight(ax,
                    (box_prover['x'] + box_prover['w'], box_prover['cy']),
                    (box_guard['x'], box_guard['cy']),
                    text=r"私有见证 $w = (\mathbf{x}, \mathbf{r})$", offset=(0, 0.4))

# ----------------------------
# D. 验证方 (右侧)
# ----------------------------
box_verifier = draw_box(ax, verifier_x, verifier_y, role_w, role_h, "验证方", "(监管机构 / 审计方)")

# 1. Verifier -> RNG
v_out = (box_verifier['x'], box_verifier['cy'] - 0.2)
rng_in = (box_rng['x'] + box_rng['w'], box_rng['cy'])
ax.annotate("", xy=rng_in, xytext=v_out,
            arrowprops=dict(arrowstyle="->", color=C_BORDER, lw=LW_ARROW, shrinkA=0, shrinkB=0), zorder=20)
ax.text((v_out[0] + rng_in[0]) / 2, (v_out[1] + rng_in[1]) / 2 + 0.3,
        r"挑战 $n_V$ (新鲜性)",
        ha="center", fontsize=FS_BODY,
        bbox=dict(facecolor='white', edgecolor='none', alpha=1.0, pad=1), zorder=25)

# 2. ZK -> Verifier (证明输出)
zk_out = (box_zk['cx'], box_zk['y'])
v_in_corner = (box_verifier['x'], box_verifier['y'] + 0.2)

conn_proof = ConnectionPatch(
    xyA=zk_out, xyB=v_in_corner, coordsA="data", coordsB="data",
    axesA=ax, axesB=ax,
    arrowstyle="->", color=C_BORDER, lw=LW_ARROW,
    connectionstyle="arc3,rad=0.15",
    zorder=30
)
ax.add_patch(conn_proof)

# 标签：ZK 框紧下方
label_x = (zk_out[0] + v_in_corner[0]) / 2 + 1.4
label_y = box_zk['y'] + 0.3
ax.text(label_x, label_y,
        r"证明: $\pi(y) + \sigma_E + \text{Att}$",
        ha="center", fontsize=FS_BODY, fontweight='bold',
        bbox=dict(facecolor='white', edgecolor='#cccccc', boxstyle='round,pad=0.3', alpha=1.0), zorder=31)

# ----------------------------
# E. 公开输入 (右下)
# ----------------------------
pub_w, pub_h = 4.5, 3.2
pub_x = verifier_x - 0.5
pub_y = verifier_y - 4.5

pub_rect = FancyBboxPatch(
    (pub_x, pub_y), pub_w, pub_h,
    boxstyle="round,pad=0.1,rounding_size=0.2",
    facecolor=C_BG_YELLOW, edgecolor="#D4AF37", linewidth=1.0, linestyle="--", zorder=5
)
ax.add_patch(pub_rect)

# 标题修改：避免误解为输入方
ax.text(pub_x + pub_w / 2, pub_y + pub_h - 0.4, "验证输入（公开）",
        ha="center", fontsize=FS_BODY, fontweight='bold', zorder=6)

content_y = (
        r"$y = \{rid, \tau, ctx, n_V, pk_E, m_E\}$" + "\n" +
        r"$rid$: 规则 ID, $\tau$: 阈值" + "\n" +
        r"$ctx$: 上下文哈希" + "\n" +
        r"$n_V$: 随机数, $pk_E$: Enclave 公钥" + "\n" +
        r"$m_E$: Enclave 度量值"
)
ax.text(pub_x + pub_w / 2, pub_y + pub_h / 2 - 0.2, content_y,
        ha="center", va="center", fontsize=FS_NOTE, color="#444444",
        linespacing=1.8, zorder=6)

# 连线修改：虚线箭头（表示参数依赖，而非通信消息）
start_pt = (pub_x + pub_w / 2, pub_y + pub_h + 0.08)
end_pt = (box_verifier['cx'], box_verifier['y'])

ax.annotate(
    "",
    xy=end_pt,
    xytext=start_pt,
    arrowprops=dict(
        arrowstyle="->",
        color=C_BORDER,
        lw=LW_ARROW,
        linestyle="--",
        shrinkA=0,
        shrinkB=0
    ),
    zorder=20
)

# 标注修改：验证使用 y，而不是“公开输入发送”
mx = (start_pt[0] + end_pt[0]) / 2
my = (start_pt[1] + end_pt[1]) / 2

ax.text(
    mx, my,
    r"验证使用 $y$",
    ha="center", va="center",
    fontsize=FS_BODY,
    bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=1),
    zorder=21
)

# ----------------------------
# F. 安全监控器 (TCB) - 底部 & 信任支撑关系
# ----------------------------
sm_w, sm_h = 8.0, 1.6
sm_x = enclave_x + (enclave_w - sm_w)/2
sm_y = 0.8

# 绘制 SM 框
draw_box(ax, sm_x, sm_y, sm_w, sm_h, "安全监控器 (TCB)\nPMP 隔离 / 度量 / 信任根", bg=C_BG_SM)

# --- 连线 1: 基础支撑 (SM -> Enclave 整体) ---
# 起点：SM 顶部中心
sm_top_center = (sm_x + sm_w/2, sm_y + sm_h)
# 终点：Enclave 底部中心
enc_bottom_center = (enclave_x + enclave_w/2, enclave_y - 0.1)

# 绘制虚线箭头
ax.annotate("", xy=enc_bottom_center, xytext=sm_top_center,
            arrowprops=dict(arrowstyle="->", color="#666666", lw=LW_ARROW, linestyle="--"),
            zorder=5)

# 说明文字 (PMP 隔离...)
ax.text(sm_top_center[0] +0.1, (sm_top_center[1] + enc_bottom_center[1])/2 - 0.3,
        "PMP 隔离 / Enclave 度量 $m_E$ / 远程认证根",
        ha="left", va="center", fontsize=FS_NOTE, color="#666666",
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.2))

# --- 连线 2: 认证支撑 (SM -> ZK 证明生成) ---
# 起点：SM 顶部 (对应 ZK 框的水平位置)
# 终点：ZK 框底部中心
zk_bottom_center = (box_zk['cx'], box_zk['y'] + 0.1)
sm_top_zk = (box_zk['cx'], sm_y + sm_h)

# 绘制虚线箭头
ax.annotate("", xy=zk_bottom_center, xytext=sm_top_zk,
            arrowprops=dict(arrowstyle="->", color="#666666", lw=LW_ARROW, linestyle="--"),
            zorder=5)

# 说明文字 (提供度量值...)
# 放在连线左侧或右侧，避免遮挡中间的公式
ax.text(box_zk['cx'] - 2, (zk_bottom_center[1] + sm_top_zk[1])/2,
        r"提供度量值 $m_E$ 与认证材料 Att",
        ha="left", va="center", fontsize=FS_NOTE, color="#666666",
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.2))

# ----------------------------
# G. 底部绑定公式 (位置微调以避开箭头)
# ----------------------------
# 将公式稍微向上移一点点，或者放在 Enclave 内部底端偏右的位置
ax.text(enclave_x + enclave_w/2, enclave_y + 0.6,
        r"Statement binding: $e \leftarrow H(rid \parallel ctx \parallel n_V \parallel \cdots \parallel m_E) \, (\mathrm{mod}\, q)$",
        ha="center", fontsize=FS_NOTE, color="#555555",
        bbox=dict(facecolor=C_BG_ENCLAVE, edgecolor='none', alpha=0.6, pad=0.2))
# 保存
plt.tight_layout()
plt.savefig("bim_tee_zk_final_robust.svg", format='svg', bbox_inches='tight', pad_inches=0.05)
plt.savefig("bim_tee_zk_final_robust.png", dpi=300, bbox_inches='tight', pad_inches=0.05)
print("图片已生成: bim_tee_zk_final_robust.svg / .png")
plt.show()