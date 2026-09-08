import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import matplotlib.font_manager as fm


# ==========================================
# 1. 字体与基础配置
# ==========================================
def set_matplot_zh_font():
    font_names = ['SimSun', 'STSong', 'Songti SC', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    found_font = None
    for name in font_names:
        if name in [f.name for f in fm.fontManager.ttflist]:
            found_font = name
            break
    if found_font:
        plt.rcParams['font.sans-serif'] = [found_font] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    else:
        plt.rcParams['font.sans-serif'] = ['sans-serif']
    plt.rcParams['mathtext.fontset'] = 'cm'


set_matplot_zh_font()

# --- 样式常量 ---
FS_TITLE_MAIN = 18
FS_PHASE = 15
FS_BLOCK_TITLE = 13
FS_BODY = 11.5
FS_NOTE = 10.5

LW_BOX = 1.5
LW_ARROW = 1.3
C_BORDER = "#000000"
C_BG_WHITE = "#FFFFFF"
C_BG_YELLOW = "#FFFBF0"
C_BG_GREEN = "#F5FFF5"
C_BG_NOTE = "#FAFAFA"

# ==========================================
# 2. 画布初始化
# ==========================================
fig, ax = plt.subplots(figsize=(13, 7.5))
ax.set_xlim(0, 22)
ax.set_ylim(0, 14)
ax.axis('off')


# ==========================================
# 3. 绘图辅助函数 (逻辑重构版)
# ==========================================
def draw_module_box(x, y, w, h, title, items, bg=C_BG_WHITE, dashed=False):
    """绘制 Phase I 模块"""
    style = "dashed" if dashed else "solid"
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                          facecolor=bg, edgecolor=C_BORDER, linewidth=LW_BOX, linestyle=style, zorder=10)
    ax.add_patch(rect)

    # 标题
    ax.text(x + w / 2, y + h - 0.6, title, ha="center", va="center",
            fontsize=FS_BLOCK_TITLE, fontweight='bold', zorder=11)
    # 分割线
    ax.plot([x, x + w], [y + h - 1.2, y + h - 1.2], color="black", lw=1, zorder=11)

    # 内容
    start_text_y = y + h - 1.8
    for item in items:
        va_align = "top" if "\n" in item else "center"
        pos_y = start_text_y if "\n" not in item else start_text_y + 0.2
        ax.text(x + 0.15, pos_y, f"• {item}", ha="left", va=va_align,
                fontsize=FS_BODY, color="#333333", zorder=11, linespacing=1.4)
        lines = item.count('\n') + 1
        start_text_y -= (0.5 + lines * 0.35)  # 动态行高
    return {'x': x, 'y': y, 'w': w, 'h': h, 'cx': x + w / 2, 'cy': y + h / 2}


def draw_simple_box(x, y, w, h, text, subtitle=None, bg=C_BG_WHITE, dashed=False):
    """绘制 Phase II 实体框"""
    style = "dashed" if dashed else "solid"
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                          facecolor=bg, edgecolor=C_BORDER, linewidth=LW_BOX, linestyle=style, zorder=10)
    ax.add_patch(rect)
    cx, cy = x + w / 2, y + h / 2
    if subtitle:
        ax.text(cx, cy + h * 0.2, text, ha="center", va="center", fontsize=FS_BLOCK_TITLE, fontweight='bold', zorder=11)
        ax.text(cx, cy - h * 0.25, subtitle, ha="center", va="center", fontsize=FS_NOTE, zorder=11)
    else:
        ax.text(cx, cy, text, ha="center", va="center", fontsize=FS_BLOCK_TITLE, fontweight='bold', zorder=11)
    return {'x': x, 'y': y, 'w': w, 'h': h, 'cx': cx, 'cy': cy}


def draw_arrow_annotate(start_xy, end_xy, text="", rad=0.0, label_pos=0.5):
    """
    使用 annotate 绘制箭头，保证方向绝对正确
    start_xy: 起点 (箭头尾)
    end_xy: 终点 (箭头头)
    """
    # connectionstyle key
    conn_style = f"arc3,rad={rad}" if rad != 0 else "arc3"

    ax.annotate("", xy=end_xy, xytext=start_xy,
                arrowprops=dict(arrowstyle="-|>", color="black", lw=LW_ARROW, connectionstyle=conn_style),
                zorder=20)

    if text:
        # 计算文字位置
        mid_x = start_xy[0] + (end_xy[0] - start_xy[0]) * label_pos
        mid_y = start_xy[1] + (end_xy[1] - start_xy[1]) * label_pos
        if rad != 0: mid_y += rad * 2.5
        ax.text(mid_x, mid_y, text, ha="center", va="center", fontsize=FS_NOTE,
                backgroundcolor="white", bbox=dict(facecolor='white', edgecolor='none', pad=2, alpha=0.9), zorder=21)


# ==========================================
# 区域划分
# ==========================================
split_y = 5.5
ax.plot([0, 22], [split_y, split_y], color="gray", linestyle="--", lw=1.5)
ax.text(0.5, 12.5, "阶段1: 构建与集成阶段", fontsize=FS_PHASE, fontweight='bold', ha='left')
ax.text(0.5, 5.0, "阶段2: 运行阶段", fontsize=FS_PHASE, fontweight='bold', ha='left')

# ==========================================
# Phase I: Build Phase (左 -> 右)
# ==========================================
mod_y = 6.8
mod_h = 5.2
mod_w = 3.2
gap = 0.8
start_x = 0.5

# (A)
items_a = ["库: zklib\n(arkworks/groth16)", "入口: lib.rs", "配置: Cargo.toml", "Type: staticlib"]
box_a = draw_module_box(start_x, mod_y, mod_w, mod_h, "(A) ZK Rust Library", items_a)

# (B)
items_b = ["导出: extern \"C\"", "符号: #[no_mangle]", "生成头文件:\ncbindgen -> zklib.h"]
box_b = draw_module_box(start_x + mod_w + gap, mod_y, mod_w, mod_h, "(B) C ABI 接口层", items_b)

# (C)
items_c = ["命令: cargo build\n--release", "目标: riscv64gc\n-unknown-linux-gnu", "处理:\nlibzklib_vc.a -> \nlibzklib.a (for CMake)"]
box_c = draw_module_box(start_x + 2 * (mod_w + gap), mod_y, mod_w, mod_h, "(C) RISC-V 交叉编译", items_c)

# (D)
items_d = ["构建: CMake", "链接: target_link\n_libraries (Static)", "产物: .eapp_riscv"]
box_d = draw_module_box(start_x + 3 * (mod_w + gap), mod_y, mod_w, mod_h, "(D) Keystone 集成", items_d)

# --- 箭头 (A->B->C->D) ---
arrow_y = mod_y + mod_h / 2
# 使用 annotate 确保从左向右
draw_arrow_annotate((box_a['x']+0.05 + mod_w, arrow_y), (box_b['x'], arrow_y))
draw_arrow_annotate((box_b['x']+0.05 + mod_w, arrow_y), (box_c['x'], arrow_y))
draw_arrow_annotate((box_c['x']+0.05 + mod_w, arrow_y), (box_d['x'], arrow_y))

# --- 实现要点 (变窄) ---
note_x = box_d['x'] + mod_w + 0.8
note_w = 3.8  # 【修改点】宽度从 4.5 -> 3.5，更紧凑
note_h = 3.8
rect_note = FancyBboxPatch((note_x, mod_y + 0.7), note_w, note_h, boxstyle="round,pad=0.1",
                           facecolor=C_BG_NOTE, edgecolor="#666666", linestyle="--", lw=1.2)
ax.add_patch(rect_note)
ax.text(note_x + note_w / 2, mod_y + 0.7 + note_h - 0.5, "实现要点", ha="center", fontweight='bold',
        fontsize=FS_BLOCK_TITLE)

notes = ["1. 静态链接自包含(No dylib)", "2. TCB内执行ZK逻辑",
         "3. 交叉编译目标:\nriscv64gc-unknown-linux-gnu"]
note_start_y = mod_y + 0.7 + note_h - 1.2
for i, note in enumerate(notes):
    ax.text(note_x + 0.2, note_start_y, note, fontsize=FS_NOTE, color="#444444", va="top")
    lines = note.count('\n') + 1
    note_start_y -= (0.4 + lines * 0.45)

# ==========================================
# Phase II: Runtime Phase
# ==========================================
rt_y = 2.2
rt_h = 2.5
# 框宽缩小
w_prover = 2.2

w_enclave = 3.2
w_verifier = 2.8

# 1. 证明方 (左)
box_prover = draw_simple_box(0.5, rt_y, w_prover, rt_h, "证明方", "(设计院 / 施工方)")

# 2. Keystone Enclave (中)
box_enclave = draw_simple_box(4.5, rt_y, w_enclave, rt_h, "Keystone Enclave", "(可信域/TCB)")

# 3. 验证方 (右)
verifier_sub = "(监管机构/审计方)\n$VerifyAtt(Att, m_E)$\n$VerifySig(pk_E, σ_E, H(\pi||y))$\n$VerifyZK(y, \pi)$"
box_verifier = draw_simple_box(11.5, rt_y, w_verifier, rt_h, "验证方",  verifier_sub)

# --- 运行阶段连线 ---

# 1. 证明方 -> Enclave (直线，左到右)
draw_arrow_annotate((box_prover['x']+0.1 + w_prover, rt_y + rt_h / 2), (box_enclave['x']-0.05, rt_y + rt_h / 2),
                    r"$w=(\mathbf{x}, \mathbf{r})$")

# 2. 验证方 -> Enclave (上弧线，右到左) - [挑战]
# xytext=Verifier(Start), xy=Enclave(End) -> Arrow points to Enclave
draw_arrow_annotate((box_verifier['x']-0.1, rt_y + rt_h - 0.2), (box_enclave['x']+0.1 + w_enclave, rt_y + rt_h - 0.2),
                    text="挑战 $n_V$")  # rad>0 for Right->Left upper arc

# 3. Enclave -> 验证方 (下弧线，左到右) - [证据包]
# xytext=Enclave(Start), xy=Verifier(End) -> Arrow points to Verifier
draw_arrow_annotate((box_enclave['x']+0.1 + w_enclave, rt_y + 0.4), (box_verifier['x']-0.05, rt_y + 0.4),
                    text=r"证据包 $(\pi, \sigma_E, Att)$")  # rad>0 for Left->Right lower arc

# --- 公开参数 y ---
y_x = 16.5
y_y = 2.2
y_w = 3.5
y_h = 2.1
y_rect = FancyBboxPatch((y_x, y_y), y_w, y_h, boxstyle="round,pad=0.1",
                        facecolor=C_BG_YELLOW, edgecolor="#D4AF37", linestyle="--", lw=1.2, zorder=5)
ax.add_patch(y_rect)
ax.text(y_x + y_w / 2, y_y + y_h - 0.4, "公开验证参数 $y$", ha="center", fontweight='bold', fontsize=FS_BLOCK_TITLE)

y_formula = r"$y=\{rid, \tau, ctx, n_V, pk_E, m_E\}$"
y_desc = "rid:规则ID, " + r"$\tau$:阈值" + "\n" + "ctx:上下文哈希, " + r"$n_V$:随机数" + "\n" + r"$pk_E$:Enclave公钥, " +  "\n" + r"$m_E$:Enclave度量值"
ax.text(y_x + 0.2, y_y + 1.8, y_formula, ha="left", fontsize=FS_NOTE, color="#000000", zorder=20)
ax.text(y_x + 0.2, y_y + 0, y_desc, ha="left", fontsize=9, color="#444444", linespacing=1.6, zorder=20)

# y -> Verifier 虚线箭头
# Start: y框左侧, End: Verifier右侧
draw_arrow_annotate((y_x-0.05, y_y + y_h / 2), (box_verifier['x']+0.1 + w_verifier, y_y + y_h / 2),
                    text=r"Verify($y, \pi$)", label_pos=0.5)
# Note: dashed styling is hard with plain annotate arrows in one go without patch customization,
# so standard arrow here is fine, or we use patch.
# Re-adding dash style manually via patch properties hidden in annotate:
#ax.annotate("", xy=(box_verifier['x'] + w_verifier, y_y + y_h / 2), xytext=(y_x, y_y + y_h / 2),
#            arrowprops=dict(arrowstyle="-|>", color="black", lw=LW_ARROW, linestyle="--"), zorder=21)

# --- 决策输出 (Accept/Reject) ---
box_result = draw_simple_box(11.8, 0.2, 2.2, 0.6, "接受/拒绝", bg=C_BG_GREEN)
# 箭头：Verifier -> Result (向下)
draw_arrow_annotate((box_verifier['cx'], box_verifier['y']-0.1), (box_result['cx'], box_result['y'] + 0.7), text="决策输出")

# ==========================================
# 跨阶段连接
# ==========================================
d_bottom = (box_d['cx'], box_d['y'])
enc_top = (box_enclave['cx'], box_enclave['y'] + box_enclave['h'])
conn_cross = ConnectionPatch(xyA=enc_top, xyB=d_bottom, coordsA="data", coordsB="data",
                             axesA=ax, axesB=ax, arrowstyle="-|>", linestyle="--", color="#333333", lw=1.5)
ax.add_patch(conn_cross)
ax.text(box_enclave['cx'], (enc_top[1] + d_bottom[1]) / 2, "静态集成至可信域 (TCB 内执行 ZK)",
        ha="center", va="center", fontsize=FS_NOTE,
        bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.2', alpha=0.9))

plt.tight_layout()

plt.savefig('keystone_zk_flow_final_v5.svg', format='svg', bbox_inches='tight', pad_inches=0.05)
plt.savefig('keystone_zk_flow_final_v5.png', dpi=300, bbox_inches='tight')
plt.show()