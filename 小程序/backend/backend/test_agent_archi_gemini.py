import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch

# --- 1. Neurocomputing 期刊标准设置 ---
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
plt.rcParams['mathtext.fontset'] = 'stix'

FS_TITLE_GRP = 9
FS_NODE = 8
FS_LABEL = 7.5
FS_NOTE = 7.0

# --- 2. 配色方案 ---
C_TOP_BG = "#F3E5F5"
C_TOP_EC = "#7B1FA2"
C_MID_BG = "#E3F2FD"
C_MID_EC = "#1976D2"
C_BOT_BG = "#E0F2F1"
C_BOT_EC = "#00695C"
C_AGENT = "#FFFFFF"
C_VAR = "#FAFAFA"
C_ARROW = "#37474F"
C_FAIL = "#C62828"


def _add_arrow(ax, p1, p2, color=C_ARROW, lw=0.8, ls="-", rad=0.0, zorder=6, mscale=10):
    arrow = FancyArrowPatch(
        p1, p2,
        arrowstyle="-|>",
        mutation_scale=mscale,
        linewidth=lw,
        linestyle=ls,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        zorder=zorder
    )
    ax.add_patch(arrow)


def _label_on_segment(ax, p1, p2, text, side="above", offset=0.25, fontsize=FS_LABEL,
                      color="#263238", zorder=9, with_box=True):
    p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    v = p2 - p1
    if np.linalg.norm(v) < 1e-6:
        return
    v = v / np.linalg.norm(v)
    n = np.array([-v[1], v[0]])
    sgn = 1.0 if side == "above" else -1.0
    mid = (p1 + p2) / 2.0
    pos = mid + sgn * offset * n
    bbox = dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85) if with_box else None
    ax.text(pos[0], pos[1], text, ha="center", va="center",
            fontsize=fontsize, color=color, bbox=bbox, zorder=zorder)


def _draw_diamond(ax, center, size=0.35, edgecolor=C_FAIL, ls="-", lw=1.0, facecolor="white", zorder=7):
    cx, cy = center
    w, h = size * 1.5, size * 0.9
    poly = patches.Polygon(
        [(cx, cy + h), (cx + w, cy), (cx, cy - h), (cx - w, cy)],
        closed=True, facecolor=facecolor, edgecolor=edgecolor,
        linewidth=lw, linestyle=ls, zorder=zorder
    )
    ax.add_patch(poly)


def _draw_group_box(ax, x, y, w, h, title, bg_color, ec_color):
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.2",
        fc=bg_color, ec=ec_color, lw=1.0, ls="--", alpha=0.5, zorder=0
    )
    ax.add_patch(rect)
    ax.text(x + 0.2, y + h - 0.1, title, ha="left", va="bottom",
            fontsize=FS_TITLE_GRP, fontweight="bold", color=ec_color, zorder=1)


def draw_macra_spaced(save_path="macra_architecture_spaced.pdf"):
    # 如果你的论文正文没有“Phase I/II/III”分段，把它设为 False（只隐藏背景框，不动任何节点/箭头关系）
    SHOW_PHASE_BOXES = False

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    ax.set_xlim(0, 22)
    ax.set_ylim(-2.5, 11.5)
    ax.axis("off")

    y_top = 9.5
    y_mid = 5.5
    y_bot_qc = 1.5
    y_bot_final = -3

    P = {
        "D": (1.5, y_top), "ext": (6, y_top), "S": (11.0, y_top),
        "gen": (1.5, y_mid), "R0": (5.5, y_mid),
        "critic": (9.5, y_mid), "Ct": (13.0, y_mid), "reflect": (16.5, y_mid), "Rtp1": (20.5, y_mid),
        "Rref": (20.5, y_bot_qc), "qc": (14.5, y_bot_qc), "Rfinal": (14.5, y_bot_final),
    }

    style_agent = dict(boxstyle="round,pad=0.5", fc=C_AGENT, ec="#455A64", lw=1.0)
    style_var = dict(boxstyle="square,pad=0.3", fc=C_VAR, ec="#607D8B", lw=0.8, ls="--")
    style_final = dict(boxstyle="round,pad=0.4", fc="#E8F5E9", ec="#2E7D32", lw=1.2)

    def shift(p, dx=0.0, dy=0.0):
        return (p[0] + dx, p[1] + dy)

    # --- 背景框（可一键关闭） ---
    if SHOW_PHASE_BOXES:
        _draw_group_box(ax, 0.5, 8.2, 12.0, 2.6, "Phase I: Context Extraction", C_TOP_BG, C_TOP_EC)

    loop_x, loop_w = 7.5, 14.0
    loop_rect = patches.FancyBboxPatch(
        (loop_x, 4), loop_w, 3.6,
        boxstyle="round,pad=0.2", fc=C_MID_BG, ec=C_MID_EC, lw=0.8, ls=":", zorder=0
    )
    ax.add_patch(loop_rect)
    if SHOW_PHASE_BOXES:
        ax.text(loop_x + loop_w / 2, 7.35, "Phase II: Cognitive Reflection Loop",
                ha="center", va="bottom", fontsize=FS_TITLE_GRP, fontweight="bold", color=C_MID_EC, zorder=1)

    # ✅ 与论文一致：停止条件只写 v_t=Pass 或 t=T_max
    ax.text(15, 7.5, "Stop if $v_t=Pass$ or $t=T_{max}$",
            ha="center", fontsize=FS_NOTE, color=C_FAIL, style="italic", zorder=1)

    if SHOW_PHASE_BOXES:
        _draw_group_box(ax, 11.5, -2.0, 10.0, 4.8, "Phase III: Quality Assurance", C_BOT_BG, C_BOT_EC)

    # --- 节点 ---
    ax.text(*P["D"], "Clinical \n Document \n (D)", bbox=style_var, ha="center", va="center", fontsize=FS_NODE, zorder=10)
    ax.text(*P["ext"], "Fact Scaffold \n Extraction Agent $\\Phi_{ext}$",
            bbox=style_agent, ha="center", va="center", fontsize=FS_NODE, fontweight="bold", zorder=10)
    ax.text(*P["S"], "Fact Scaffold\n(S)", bbox=style_var, ha="center", va="center", fontsize=FS_NODE, zorder=10)

    ax.text(*P["gen"], "Drafting Agent\n$\\Phi_{gen}$", bbox=style_agent, ha="center", va="center",
            fontsize=FS_NODE, fontweight="bold", zorder=10)
    ax.text(*P["R0"], "First Draft\n($R_0$)", bbox=style_var, ha="center", va="center", fontsize=FS_NODE, zorder=10)

    ax.text(*P["critic"], "Medical Critic\n$\\Phi_{critic}$", bbox=style_agent, ha="center", va="center",
            fontsize=FS_NODE, fontweight="bold", zorder=10)
    ax.text(*P["Ct"], "$C_t = <v_t, \\alpha_t>$", bbox=style_var, ha="center", va="center", fontsize=FS_NODE, zorder=10)
    ax.text(*P["reflect"], "Reflection Agent\n$\\Phi_{reflect}$", bbox=style_agent, ha="center", va="center",
            fontsize=FS_NODE, fontweight="bold", zorder=10)
    ax.text(*P["Rtp1"], "Revised Draft\n($R_{t+1}$)", bbox=style_var, ha="center", va="center", fontsize=FS_NODE, zorder=10)

    ax.text(*P["Rref"], "$R_{reflected}$", bbox=style_var, ha="center", va="center", fontsize=FS_NODE, zorder=10)
    ax.text(*P["qc"], "Publication QC Gate\n$\\Phi_{qc}$", bbox=style_agent, ha="center", va="center",
            fontsize=FS_NODE, fontweight="bold", zorder=10)
    ax.text(*P["Rfinal"], "Final Summary ($R_{final}$)", bbox=style_final, ha="center", va="center",
            fontsize=FS_NODE, fontweight="bold", zorder=10)

    ax.text(P["qc"][0] -4.6 , P["qc"][1], "Check: format + safety;\nno new medical facts",
            color=C_FAIL, fontsize=FS_NOTE, style="italic", va="center", zorder=10)

    # ✅ 这是“共享输入/证据”：对齐你正文中 critic/reflect 都以 (D,S) 为上下文
    ax.text(8.0, y_mid + 1.4, "Shared context: (D, S)", fontsize=FS_NOTE, color="#455A64", fontweight="bold", zorder=10)

    # --- 连线 ---
    _add_arrow(ax, shift(P["D"], 0.7), shift(P["ext"], dx=-1.7))
    _label_on_segment(ax, shift(P["D"], 0.3), shift(P["ext"], -1.1), r"$D$")

    _add_arrow(ax, shift(P["ext"], 1.1), shift(P["S"], -0.9))
    _label_on_segment(ax, shift(P["ext"], 1.5), shift(P["S"], -0.7), r"$S=\Phi_{ext}(D)$")

    _add_arrow(ax, shift(P["D"], 0, -0.5), shift(P["gen"], 0, 0.4))
    _label_on_segment(ax, shift(P["D"], 0, -0.8), shift(P["gen"], 0, 0.8), r"$D$", offset=0.2)

    _add_arrow(ax, shift(P["S"], -0, -0.5), shift(P["gen"], 0, 0.55))
    _label_on_segment(ax, shift(P["S"], -0.4, -0.5), shift(P["gen"], 0.4, 0.5), r"$S$", side="below", offset=0.25)

    _add_arrow(ax, shift(P["gen"], 1.0), shift(P["R0"], -0.7))
    _label_on_segment(ax, shift(P["gen"], 1.2), shift(P["R0"], -0.7),
                      r"$R_0$" + "=\n" + r"$\Phi_{gen}(D,S)$", side="above", offset=0.5, fontsize=FS_NOTE)

    _add_arrow(ax, shift(P["R0"], 0.7), shift(P["critic"], -1.1))
    _label_on_segment(ax, shift(P["R0"], 0.7), shift(P["critic"], -1.0), r"$R_t(init=R_0)$", offset = 0.35)

    _add_arrow(ax, shift(P["critic"], 1.0), shift(P["Ct"], -0.9))
    # ✅ 保留这一处 C_t：表示 critic 生成 C_t
    _label_on_segment(ax, shift(P["critic"], 1.0), shift(P["Ct"], -0.8), r"$C_t$")

    _add_arrow(ax, shift(P["Ct"], 0.8), shift(P["reflect"], -1.3))
    # ✅ 最小改动：删掉这一处重复 C_t 标签（避免“两个 C_t”的观感）
    # _label_on_segment(ax, shift(P["Ct"], 0.8), shift(P["reflect"], -1.0), r"$C_t$")

    _add_arrow(ax, shift(P["reflect"], 1.0), shift(P["Rtp1"], -0.9))
    _label_on_segment(ax, shift(P["reflect"], 1.0), shift(P["Rtp1"], -0.8), r"$R_{t+1}$")

    _add_arrow(ax, shift(P["Rtp1"], 0, 0.55), shift(P["critic"], 0, 0.55), color=C_MID_EC, lw=1.0, rad=0.22)
    ax.text(15, y_mid + 1.3, r"$R_t \leftarrow R_{t+1}$",
            ha="center", va="center", fontsize=FS_LABEL, color=C_MID_EC,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.1), zorder=10)

    # Exit to R_reflected
    p1, p2 = shift(P["Rtp1"], 0, -0.45), shift(P["Rref"], 0, 0.25)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, p1, p2, r"$R_{reflected}=R_{curr}$", side="above", offset=0.18, fontsize=FS_NOTE)

    _add_arrow(ax, shift(P["Rref"], -0.6), shift(P["qc"], 1.6))
    _label_on_segment(ax, shift(P["Rref"], -0), shift(P["qc"], 1.2), r"$R_{reflected}$", side="below", offset=0.3)

    # --- Diamond QC decision ---
    decision_center = (P["qc"][0], y_bot_qc - 2.2)
    _draw_diamond(ax, decision_center, size=0.6)

    # ✅ 判断语义更规范：Passed?
    ax.text(decision_center[0], decision_center[1], "QC\nPassed?",
            ha="center", va="center", fontsize=FS_LABEL, color=C_FAIL, zorder=10)

    _add_arrow(ax, shift(P["qc"], 0, -0.5), (decision_center[0], decision_center[1] + 0.35))

    # Pass -> Final
    p_pass_start, p_pass_end = (decision_center[0], decision_center[1] - 0.45), shift(P["Rfinal"], 0, 0.35)
    _add_arrow(ax,  p_pass_start, p_pass_end, ls="-", zorder=6)

    _label_on_segment(ax, p_pass_start, p_pass_end,
                      r"$R_{final}=\Phi_{qc}(R_{reflected};\,p_{fmt},\,p_{safe})$",
                      side="above", offset=0.22, fontsize=FS_NOTE)
    _label_on_segment(ax, p_pass_start, shift(P["Rfinal"], 0, 1.3),
                     "Pass", side="below", offset=0.4, fontsize=FS_LABEL, with_box=True)

    # Fail -> back to Drafting
    y_bus = decision_center[1]
    ax.plot([decision_center[0] - 0.5, P["gen"][0]], [y_bus, y_bus], color=C_FAIL, lw=1.0, ls="--", zorder=2)
    _add_arrow(ax, (P["gen"][0], y_bus), shift(P["gen"], 0, -0.5), color=C_FAIL, lw=1.0, ls="--", zorder=2)
    ax.text(P["qc"][0] - 2.5, y_bus + 0.15,  r"Fail $\rightarrow$ backtrack to Drafting / Reflection",
            ha="right", va="bottom", fontsize=FS_NOTE, color=C_FAIL, zorder=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=600, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    draw_macra_spaced("macra_neuro_spaced_fixed.pdf")
