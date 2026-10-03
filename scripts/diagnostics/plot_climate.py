# -*- coding: utf-8 -*-
"""plot_climate.py —— 画气候梯度图，确认"这个队列真的有气候梯度可分析"

三张图：
  1. 全队列：年均温 vs 年降水的气候空间（按模块着色）——看环境覆盖是否足够
  2. 美国内部：纬度 vs 年均温 / 最冷季均温 —— 这是唯一能做梯度分析的模块
  3. 各模块气候箱线对比
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TBL = "/mnt/c/SF_data/tools/report/climate_s2.tsv"
OUT = "/mnt/c/SF_data/tools/report/climate_gradient.png"


def load():
    rows = [l.rstrip("\n").split("\t") for l in open(TBL, encoding="utf-8")]
    hdr = rows[0]
    out = []
    for r in rows[1:]:
        d = dict(zip(hdr, r))
        try:
            d["bio1"] = float(d["bio1"]); d["bio12"] = float(d["bio12"])
            d["bio11"] = float(d["bio11"]); d["lat"] = float(d["lat"])
        except (ValueError, KeyError):
            continue
        out.append(d)
    return out


def main():
    rows = load()
    mods = np.array([r["module"] for r in rows])
    colors = {"US": "#c0392b", "BR": "#2980b9", "AF": "#27ae60",
              "AM": "#8e44ad", "CN": "#f39c12", "FL": "#16a085"}

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))

    # 1. 气候空间
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = mods == m
        if s.sum():
            ax[0].scatter([r["bio1"] for r in rows if r["module"] == m],
                          [r["bio12"] for r in rows if r["module"] == m],
                          s=22, alpha=.7, label="%s (%d)" % (m, s.sum()),
                          c=colors[m], edgecolors="none")
    ax[0].set_xlabel("BIO1 Annual mean temp (C)")
    ax[0].set_ylabel("BIO12 Annual precip (mm)")
    ax[0].set_title("Climate space of 214 analysis samples", fontsize=11)
    ax[0].legend(fontsize=8, markerscale=1.3)

    # 2. US: latitude vs temperature
    us = [r for r in rows if r["module"] == "US"]
    lat = np.array([r["lat"] for r in us])
    b1 = np.array([r["bio1"] for r in us])
    b11 = np.array([r["bio11"] for r in us])
    ax[1].scatter(lat, b1, s=24, alpha=.75, c="#c0392b", label="BIO1 annual mean", edgecolors="none")
    ax[1].scatter(lat, b11, s=24, alpha=.75, c="#2980b9", label="BIO11 coldest quarter", edgecolors="none")
    ax[1].set_xlabel("Latitude (deg)")
    ax[1].set_ylabel("Temperature (C)")
    ax[1].set_title("US module: latitude vs temperature\nr(BIO1)=%+.3f  r(BIO11)=%+.3f"
                    % (np.corrcoef(lat, b1)[0, 1], np.corrcoef(lat, b11)[0, 1]), fontsize=11)
    ax[1].legend(fontsize=9)
    ax[1].axhline(0, color="#cccccc", lw=.7)

    # 3. 各模块年均温箱线
    data = [[r["bio1"] for r in rows if r["module"] == m] for m in ["US", "BR", "AF", "AM", "CN", "FL"]]
    data = [d for d in data if d]
    labels = [m for m in ["US", "BR", "AF", "AM", "CN", "FL"] if any(r["module"] == m for r in rows)]
    bp = ax[2].boxplot(data, tick_labels=labels, patch_artist=True, widths=.6)  # matplotlib 3.9+ 改名为 tick_labels
    for i, (b, l) in enumerate(zip(bp["boxes"], labels)):
        b.set_facecolor(colors.get(l, "#999999"))
        b.set_alpha(.65)
    ax[2].set_ylabel("BIO1 Annual mean temp (C)")
    ax[2].set_title("Annual mean temp by module", fontsize=11)

    plt.tight_layout()
    plt.savefig(OUT, dpi=140)
    print("已写出: %s" % OUT)


if __name__ == "__main__":
    main()
