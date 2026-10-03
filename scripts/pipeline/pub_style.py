# -*- coding: utf-8 -*-
"""pub_style.py —— 出版级图件的统一样式与地图底图

为什么自己画底图：
  2026-09-24 代理完全不通 → cartopy 装不上、Natural Earth 下不来。
  但手上 WorldClim 的海拔栅格用 **-32768 标海洋/空洞**（实测占 65.4%，正好是地球海陆比），
  直接拿它生成陆地掩膜当底图，数据来源还与环境数据一致，反而自洽。

样式统一为 Molecular Ecology / Nature 风格：无衬线字体、8pt 基准、细线、300dpi。
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio

# ---------------- 样式 ----------------
FONT = "DejaVu Sans"          # 环境内无中文字体，全部标签用英文（投稿本来也要英文）

PALETTE = {
    "US": "#c0392b", "BR": "#2471a3", "AF": "#1e8449",
    "AM": "#7d3c98", "CN": "#d68910", "FL": "#117a65",
}
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
        "pdf.fonttype": 42,        # 投稿要求：字体嵌入且可编辑
        "ps.fonttype": 42,
    })


# ---------------- 陆地掩膜底图 ----------------
_ELEV = None


def _land_mask(step=2):
    """从 WorldClim 海拔栅格生成陆地掩膜（下采样 step 倍加速绘图）"""
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


def add_basemap(ax, step=2, lw=0.35, color=GREY, land_color=LAND, sea_color=SEA,
                extent=(-180, 180, -60, 75)):
    """在世界坐标轴上加陆地底图 + 国界（国界用陆地掩膜的梯度近似不了，
    这里只画海陆轮廓；细线为陆地边界）"""
    land, b = _land_mask(step)
    x0, x1 = b.left, b.right
    y0, y1 = b.bottom, b.top
    # ★ 栅格第 0 行是**最北**一行（transform.e < 0），因此 Y 坐标必须**降序**，
    #   否则整张底图会上下翻转（表现为"亚洲变空白、陆地跑到南半球"）
    xs = np.linspace(x0, x1, land.shape[1])
    ys = np.linspace(y1, y0, land.shape[0])
    ax.set_facecolor(sea_color)
    ax.contourf(xs, ys, land, levels=[0.5, 1.5], colors=[land_color], zorder=0)
    ax.contour(xs, ys, land, levels=[0.5], colors=[color], linewidths=lw, zorder=1)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    return ax


def save(fig, name, outdir="/mnt/c/SF_data/tools/report/pub"):
    """同时存 300dpi PNG（看）与 PDF（投稿矢量）"""
    os.makedirs(outdir, exist_ok=True)
    p1 = os.path.join(outdir, name + ".png")
    p2 = os.path.join(outdir, name + ".pdf")
    fig.savefig(p1)
    fig.savefig(p2)
    plt.close(fig)
    print("  已写出 %s (.png/.pdf)" % name)
    return p1
