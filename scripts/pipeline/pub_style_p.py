# -*- coding: utf-8 -*-
"""pub_style_p.py —— 路线 2（中性面板代号 P1–P6）的统一样式与地图底图。

与 pub_style.py 的唯一差别：
  * PALETTE / PNAME 以中性代号 P1–P6 为键
  * 颜色与原图**一一对应保持**（P1 沿用原 US 的红等），
    使得图件风格、读者既有印象、色觉可达性全都不变
  * 另提供 OLD2NEW / NEW2OLD，方便任何脚本按需转换

映射（数据量降序）：
    P1=US(143)  P2=BR(24/30)  P3=AF(16)  P4=AM(15)  P5=CN(10)  P6=FL(6)
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio

FONT = "DejaVu Sans"

OLD2NEW = {"US": "P1", "BR": "P2", "AF": "P3", "AM": "P4", "CN": "P5", "FL": "P6"}
NEW2OLD = {v: k for k, v in OLD2NEW.items()}

# 颜色与 pub_style.PALETTE 严格一一对应（只换键，不换色）
PALETTE = {
    "P1": "#c0392b",   # 原 US 红
    "P2": "#2471a3",   # 原 BR 蓝
    "P3": "#1e8449",   # 原 AF 绿
    "P4": "#7d3c98",   # 原 AM 紫
    "P5": "#d68910",   # 原 CN 橙
    "P6": "#117a65",   # 原 FL 青
}

# 图例里显示的面板名（中性：不带任何地理暗示）
PNAME = {k: k for k in PALETTE}

# 默认绘图的模块顺序（沿用原脚本习惯：按数据量降序）
MODS = ["P1", "P2", "P3", "P4", "P5", "P6"]

STRAIN_COL = {"C": "#c0392b", "R": "#2471a3", "H": "#7f8c8d"}
GREY = "#555555"
LAND = "#e8e6e1"
SEA = "#fbfbfa"


def set_style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [FONT, "Arial", "Helvetica"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


_ELEV = None


def _land_mask(step=2):
    global _ELEV
    if _ELEV is None:
        with rasterio.open("/home/hugo/data/climate/wc2.1_10m_elev.tif") as src:
            a = src.read(1)
            b = src.bounds
            _ELEV = (a, b)
    a, b = _ELEV
    land = (a != -32768).astype(np.uint8)
    if step > 1:
        h, w = land.shape
        land = land[: h // step * step, : w // step * step].reshape(
            h // step, step, w // step, step).mean(axis=(1, 3)) > 0.5
    return land.astype(float), b


def add_basemap(ax, step=1, lw=0.35, color=GREY, land_color=LAND, sea_color=SEA,
                extent=(-180, 180, -60, 75), aspect_equal=False, anchor="C"):
    """画 WorldClim 派生的陆地掩膜底图。

    aspect_equal=True 时按 Plate Carrée 的真实比例绘图（1° 经度 = 1° 纬度）。
    ★ 关键坑：matplotlib 默认 aspect='auto'，若不给显式比例，地图会按面板的
    物理宽高比被拉伸 —— 245°×88° 的地图塞进 1.2:1 的面板会被横向压掉一半，
    看起来「特别窄」（南美洲变成细长条）。世界地图一律应开 aspect_equal。
    """
    land, b = _land_mask(step)
    x0, x1 = b.left, b.right
    y0, y1 = b.bottom, b.top
    xs = np.linspace(x0, x1, land.shape[1])
    ys = np.linspace(y1, y0, land.shape[0])
    ax.set_facecolor(sea_color)
    ax.contourf(xs, ys, land, levels=[0.5, 1.5], colors=[land_color], zorder=0)
    ax.contour(xs, ys, land, levels=[0.5], colors=[color], linewidths=lw, zorder=1)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    if aspect_equal:
        ax.set_aspect("equal", adjustable="box", anchor=anchor)
    return ax


def align_panel_height(fig, ax_map, ax_other, ratio, verbose=False):
    """把 ax_map 的绘图区设成「与 ax_other **同高、同上下沿**、宽度按经纬比推导」。

    为什么需要：设了 aspect='equal' 的地图面板，若 subplot 分配的宽度不足以满足
    数据经纬比 `ratio`，matplotlib 会**只压高度**来满足比例，于是该面板比旁边矮一截。

    ★ 为什么不用 gridspec 的 width_ratios 迭代：
      `gs.set_width_ratios()` 在 `fig.canvas.draw()` 之后**不生效**（实测 ratio 被改成
      57467 而 ax1 位置纹丝不动）—— 因为 subplot 创建时位置已固化。改 `fig.subplots_adjust()`
      又会和 aspect 打架。所以直接用 `set_position()` 绝对定位，一次到位、无需迭代。

    ratio：经度跨度/纬度跨度。extent=(-126,118,-40,48) ⇒ 244/88 = 2.773。
    返回 (pos, overlap_bool)：overlap=True 表示地图右沿压到了 ax_other，需调 figsize/wspace。
    """
    W, H = fig.get_size_inches()
    fig.canvas.draw()
    po = ax_other.get_position()
    h = po.height
    w = h * H * ratio / W            # figure fraction；经纬比要在英寸尺度上算
    pm = ax_map.get_position()
    ax_map.set_position([pm.x0, po.y0, w, h])
    fig.canvas.draw()
    p_new = ax_map.get_position()
    overlap = p_new.x1 > ax_other.get_position().x0 + 1e-6
    if verbose:
        print("    [align] ax_map x0=%.3f x1=%.3f  y0=%.3f h=%.4f  |  ax_other x0=%.3f  h=%.4f%s"
              % (p_new.x0, p_new.x1, p_new.y0, p_new.height,
                 ax_other.get_position().x0, po.height, "  << OVERLAP" if overlap else ""))
    return p_new, overlap


def save(fig, name, outdir="/mnt/c/SF_data/tools/report/pub_p"):
    """输出到独立的 pub_p 目录，绝不覆盖原图件。"""
    os.makedirs(outdir, exist_ok=True)
    p1 = os.path.join(outdir, name + ".png")
    p2 = os.path.join(outdir, name + ".pdf")
    fig.savefig(p1)
    fig.savefig(p2)
    plt.close(fig)
    print("  已写出 %s (.png/.pdf)" % name)
    return p1
