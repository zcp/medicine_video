import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch


def _add_arrow(ax, p1, p2, color="#263238", lw=1.3, ls="-", rad=0.0, zorder=6, mscale=16):
    """Draw an arrow from p1 to p2, ensure it's above boxes (zorder)."""
    arrow = FancyArrowPatch(
        p1, p2,
        arrowstyle="->",
        mutation_scale=mscale,
        linewidth=lw,
        linestyle=ls,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        zorder=zorder
    )
    ax.add_patch(arrow)
    return arrow


def _label_on_segment(ax, p1, p2, text, side="above", offset=0.18, fontsize=9,
                      color="#263238", zorder=9, with_box=True):
    """
    Place label near midpoint of segment p1->p2, offset along normal.
    with_box=True adds a white background to improve readability.
    """
    p1 = np.array(p1, dtype=float)
    p2 = np.array(p2, dtype=float)
    v = p2 - p1
    if np.linalg.norm(v) < 1e-6:
        return

    v = v / np.linalg.norm(v)
    n = np.array([-v[1], v[0]])  # +90 deg normal
    sgn = 1.0 if side == "above" else -1.0

    mid = (p1 + p2) / 2.0
    pos = mid + sgn * offset * n

    bbox = None
    if with_box:
        bbox = dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85)

    ax.text(pos[0], pos[1], text,
            ha="center", va="center",
            fontsize=fontsize, color=color,
            bbox=bbox,
            zorder=zorder)


def _draw_diamond(ax, center, size=0.38, edgecolor="#263238", ls="-", lw=1.2,
                  facecolor="white", zorder=7):
    """Draw a diamond decision node."""
    cx, cy = center
    poly = patches.Polygon(
        [(cx, cy + size), (cx + size, cy), (cx, cy - size), (cx - size, cy)],
        closed=True,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=lw,
        linestyle=ls,
        zorder=zorder
    )
    ax.add_patch(poly)
    return poly


def draw_macra_clean_labels_v8(save_path="macra_architecture_v8.png"):
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 22)
    ax.set_ylim(-1.2, 10)
    ax.axis("off")

    agent_style = dict(boxstyle="round,pad=0.5", fc="#E1F5FE", ec="#01579B", lw=1.5)
    var_style = dict(boxstyle="square,pad=0.3", fc="#FFFFFF", ec="#455A64", lw=1, ls="--")
    loop_box_style = dict(boxstyle="round,pad=1.0", fc="#F5F5F5", ec="#B0BEC5", lw=1, ls=":")
    final_style = dict(boxstyle="round,pad=0.5", fc="#E8F5E9", ec="#2E7D32", lw=2)

    # =========================
    # 关键布局：把 QC 相关节点移到 loop 大框正下方
    # loop 大框：x=7..17.5, y=3.5..7.0, center x=12.25
    # =========================
    P = {
        "D": (2, 8.5),
        "ext": (5, 8.5),
        "S": (9, 8.5),

        "gen": (2, 5),
        "R0": (5, 5),

        "critic": (8.5, 5),
        "Ct": (11.5, 5),
        "reflect": (14.5, 5),
        "Rtp1": (17.5, 5),

        # moved block (under loop)
        "Rref": (17.5, 2.2),
        "qc": (12.25, 2.2),
        "Rfinal": (12.25, -0.5),
    }

    def shift(p, dx=0.0, dy=0.0):
        return (p[0] + dx, p[1] + dy)

    # Nodes
    ax.text(*P["D"], "Clinical \n Document \n (D)", bbox=var_style, ha="center", va="center", fontsize=10, zorder=10)
    ax.text(*P["ext"], "Fact Scaffold \n Extraction Agent $\\Phi_{ext}$", bbox=agent_style,
            ha="center", va="center", fontsize=10, fontweight="bold", zorder=10)
    ax.text(*P["S"], "Fact Scaffold\n(S)", bbox=var_style, ha="center", va="center", fontsize=10, zorder=10)

    ax.text(*P["gen"], "Drafting Agent\n$\\Phi_{gen}$", bbox=agent_style,
            ha="center", va="center", fontsize=10, fontweight="bold", zorder=10)
    ax.text(*P["R0"], "First Draft\n($R_0$)", bbox=var_style, ha="center", va="center", fontsize=10, zorder=10)

    loop_x, loop_y, loop_w, loop_h = 7, 3.5, 10.5, 3.5
    loop_rect = patches.FancyBboxPatch((loop_x, loop_y), loop_w, loop_h, **loop_box_style)
    loop_rect.set_zorder(1)
    ax.add_patch(loop_rect)

    ax.text(12, 7.7, "Cognitive Reflection Loop", ha="center",
            fontsize=11, fontweight="bold", color="#546E7A", zorder=10)
    ax.text(13.2, 7, "Stop if $v_t = Pass$ or $t$ reaches $T_{max}$",
            ha="center", fontsize=9, color="#C62828", style="italic", zorder=10)
    ax.text(7.5, 6.6, "Shared context: (D, S)", fontsize=9, color="#455A64", fontweight="bold", zorder=10)

    ax.text(*P["critic"], "Medical Critic Agent\n$\\Phi_{critic}$", bbox=agent_style,
            ha="center", va="center", fontsize=10, fontweight="bold", zorder=10)
    ax.text(*P["Ct"], "Critic Output\n$C_t = <v_t, \\, \\alpha_t>$", bbox=var_style,
            ha="center", va="center", fontsize=9, zorder=10)
    ax.text(*P["reflect"], "Reflection Agent\n$\\Phi_{reflect}$", bbox=agent_style,
            ha="center", va="center", fontsize=10, fontweight="bold", zorder=10)
    ax.text(*P["Rtp1"], "Revised Draft\n($R_{t+1}$)", bbox=var_style,
            ha="center", va="center", fontsize=10, zorder=10)

    ax.text(*P["Rref"], "$R_{reflected}$", bbox=var_style, ha="center", va="center", fontsize=10, zorder=10)
    ax.text(*P["qc"], "Publication QC Gate\n$\\Phi_{qc}$", bbox=agent_style,
            ha="center", va="center", fontsize=10, fontweight="bold", zorder=10)
    ax.text(*P["Rfinal"], "Final Summary ($R_{final}$)", bbox=final_style,
            ha="center", va="center", fontsize=11, fontweight="bold", zorder=10)

    ax.text(P["qc"][0] + 2.2, P["qc"][1] - 0.4,
            "Gatekeeping: format + safety compliance;\nno new medical facts",
            color="#D32F2F", fontsize=8, style="italic", va="center", zorder=10)

    # --- D -> ext (箭头不动，只调 label 的端点让其视觉居中) ---
    p1 = shift(P["D"], dx=0, dy=0.0)
    p2 = shift(P["ext"], dx=-1.4, dy=0.0)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["D"], dx=+0.55, dy=0.0), shift(P["ext"], dx=-1.4, dy=0.0),
                      r"$D$", side="above", offset=0.2, fontsize=10)

    # --- ext -> S ---
    p1 = shift(P["ext"], dx=0, dy=0.0)
    p2 = shift(P["S"], dx=-0.7, dy=0.0)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["ext"], dx=+1.9, dy=0.0), shift(P["S"], dx=-1.2, dy=0.0),
                      r"$S=\Phi_{ext}(D)$", side="above", offset=0.2, fontsize=10)

    # D -> gen
    p1 = shift(P["D"], dy=0)
    p2 = shift(P["gen"], dy=+0.25)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, p1, p2, r"$D$", side="above", offset=0.2, fontsize=10)

    # S -> gen
    p1 = shift(P["S"], dx=-0.75, dy=-0.25)
    p2 = shift(P["gen"], dx=0, dy=0.25)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, p1, p2, r"$S$", side="below", offset=0.18, fontsize=10)

    # gen -> R0
    p1 = shift(P["gen"], dx=0.0)
    p2 = shift(P["R0"], dx=-0.6)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax,
                      shift(P["gen"], dx=+1.3, dy=0.0),
                      shift(P["R0"], dx=-1.00, dy=0.0),
                      "$R_0=$\n$\\Phi_{gen}(D,S)$", side="above", offset=0.3, fontsize=9)

    # R0 -> critic
    p1 = shift(P["R0"], dx=0.0)
    p2 = shift(P["critic"], dx=-1.3)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["R0"], dx=+0.5, dy=0.0), shift(P["critic"], dx=-1.30, dy=0.0),
                      r"$R_t(init=R_0)$", side="above", offset=0.2, fontsize=9)

    # critic -> Ct
    p1 = shift(P["critic"], dx=1.0)
    p2 = shift(P["Ct"], dx=-0.7)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["critic"], dx=+1.65, dy=0.0), shift(P["Ct"], dx=-1.05, dy=0.0),
                      r"$C_t$", side="above", offset=0.2, fontsize=10)

    # Ct -> reflect
    p1 = shift(P["Ct"], dx=0.0)
    p2 = shift(P["reflect"], dx=-1.1)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["Ct"], dx=+0.5, dy=0.0), shift(P["reflect"], dx=-1.10, dy=0.0),
                      r"$C_t$", side="above", offset=0.2, fontsize=10)

    # reflect -> Rtp1
    p1 = shift(P["reflect"], dx=0)
    p2 = shift(P["Rtp1"], dx=-0.75)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["reflect"], dx=+1.4, dy=0.0), shift(P["Rtp1"], dx=-1.10, dy=0.0),
                      r"$R_{t+1}$", side="above", offset=0.2, fontsize=10)

    # loop back arc
    start = shift(P["Rtp1"], dy=0.25)
    end = shift(P["critic"], dy=0.25)
    _add_arrow(ax, start, end, color="#1976D2", lw=1.6, rad=0.35, zorder=6)
    ax.text(13, 6.5, r"$R_t \leftarrow R_{t+1}$", ha="center", va="center",
            fontsize=10, color="#1976D2",
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.2), zorder=10)

    # loop exit -> R_reflected (保持你原逻辑：从 loop 右侧出来到 Rref)
    loop_exit = (loop_x + loop_w, loop_y + 1.3)  # (17.5, 4.8)
    p1 = loop_exit
    p2 = shift(P["Rref"], dy=0.15)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, p1, p2, r"$R_{reflected}=R_{curr}$", side="above", offset=0.2, fontsize=9)

    # R_reflected -> QC
    p1 = shift(P["Rref"], dx=0)
    p2 = shift(P["qc"], dx=1.15)
    _add_arrow(ax, p1, p2)
    _label_on_segment(ax, shift(P["Rref"], dx=+1.6, dy=0.0), shift(P["qc"], dx=-1.2, dy=0.0),
                      r"$R_{reflected}$", side="below", offset=0.2, fontsize=9)

    # ============================================================
    # ✅ QC Gate -> Diamond decision -> (Pass -> Final) / (Fail -> two branches)
    # ============================================================
    # 菱形放在 QC gate 正下方
    decision_center = (P["qc"][0], 1.05)
    _draw_diamond(ax, decision_center, size=0.38, edgecolor="#D32F2F", ls="--", lw=1.2, facecolor="white", zorder=7)
    ax.text(decision_center[0], decision_center[1], "QC\nFail?", ha="center", va="center",
            fontsize=8, color="#D32F2F", zorder=10)

    # QC -> Decision（黑色实线）
    p1 = shift(P["qc"], dy=0)
    p2 = (decision_center[0], decision_center[1] + 0.35)
    _add_arrow(ax, p1, p2, color="#263238", lw=1.2, ls="-", zorder=6)

    # Decision PASS -> Final（黑色实线 + 公式注释只放这里）
    p1 = (decision_center[0], decision_center[1] - 0.40)
    p2 = shift(P["Rfinal"], dy=+0.20)
    _add_arrow(ax, p1, p2, color="#263238", lw=1.2, ls="-", zorder=6)
    _label_on_segment(
        ax,
        p1, p2,
        r"$R_{final}=\Phi_{qc}(R_{reflected};\,p_{format},\,p_{safety})$",
        side="right" if False else "above",  # 这里不改函数，只用 above，避免引入新 side
        offset=0.22, fontsize=8
    )

    # 在同一条 PASS 线上加“Pass”标签（放在公式另一侧，避免重叠）
    _label_on_segment(
        ax,
        p1, shift(P["Rfinal"], dy=+0.90),
        "Pass",
        side="below",  # 与公式的 above 相反
        offset=0.3,  # 小一点避免太远
        fontsize=9,
        color="#263238",
        with_box=True
    )

    # Decision FAIL -> two dashed branches（两种情况）
    y_bus = decision_center[1]  # 用菱形所在 y 作为分叉总线更自然

    # Fail -> Drafting (Safety fail -> Regenerate)
    # 走底部虚线到 gen 的 x，再向上虚线箭头到 gen（不穿越主流程）
    ax.plot([decision_center[0], P["gen"][0]], [y_bus, y_bus],
            color="#D32F2F", lw=1.0, ls="--", zorder=2)
    _add_arrow(ax, (P["gen"][0], y_bus), shift(P["gen"], dy=-0.28),
               color="#D32F2F"
                     "", lw=1.0, ls="--", zorder=2)
    ax.text(P["gen"][0] + 9.65, y_bus + 0.2,
            "Fail",
            ha="center", va="top", fontsize=8.5, color="#D32F2F", zorder=10)


    # ============================================================

    plt.title("Figure X. Overview of MACRA multi-agent inference workflow for clinical summarization",
              fontsize=16, fontweight="bold", pad=30)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    draw_macra_clean_labels_v8("macra_architecture_v8.png")
