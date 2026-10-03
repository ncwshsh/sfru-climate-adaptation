# -*- coding: utf-8 -*-
"""paper_figs_pub_P.py —— 路线 2：全部图件改用中性面板代号 P1–P6。

与 paper_figs_pub.py 的差别**只有代号**：
  * 读 *_P.tsv（module 列已重编为 P1–P6）
  * 图例/标题/坐标轴上的模块名一律用 P1–P6
  * 颜色与原图严格一一对应（P1=原红、P2=原蓝 …）
  * 输出到 report/pub_p/，**绝不覆盖**原图件

不带任何地理暗示：正文与图内均不出现国名/洲名作为面板标识。
"""
import os
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, "/mnt/c/SF_data/tools")
import matplotlib.pyplot as plt
from pub_style_p import (set_style, save, add_basemap, align_panel_height, PALETTE,
                         STRAIN_COL, GREY, MODS, OLD2NEW)

ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
set_style()

# 数据量降序的面板顺序（默认绘图顺序）
ORD = ["P1", "P2", "P3", "P4", "P5", "P6"]


def load_all():
    gea = pd.read_csv(os.path.join(REP, "gea_input_P.tsv"), sep="\t")
    for c in ["lat", "lon", "rate", "raw_depth", "PC1", "PC2", "PC3", "PC4",
              "bio1", "bio4", "bio11", "bio12"]:
        if c in gea.columns:
            gea[c] = pd.to_numeric(gea[c], errors="coerce")
    # ★ 缺列即停：2026-10-03 才发现 gea_input.tsv 的 PC1–PC4 一直是空的，
    #   结果 Fig2 画出一张**完全没有点**的图、标题还显示 r = +nan，却没人发现。
    #   空列 → 静默空图，是最危险的一类绘图 bug。宁可报错。
    need = ["lat", "lon", "rate", "raw_depth", "PC1", "PC2", "bio1", "bio12"]
    for c in need:
        if c not in gea.columns:
            raise ValueError("gea_input_P.tsv 缺列 %s —— 拒绝出图（历史事故：PC 列曾整列为空）" % c)
        n = int(gea[c].isna().sum())
        if n:
            raise ValueError("gea_input_P.tsv 列 %s 有 %d/%d 个缺失 —— 拒绝出图"
                             % (c, n, len(gea)))
    return gea


# ---------------- Fig 1：采样分布 + 气候空间 ----------------
# 2026-10-03 重做底图：原图 extent 245°×95° 塞进 ~1.2:1 的面板且未设 aspect，
# 地图被横向压缩约 2.3 倍（南美洲成了细长条）。现改为：
#   * extent 收紧到数据外接框 + 边距 → 比例 245:88
#   * aspect_equal=True（1° 经度 = 1° 纬度，Plate Carrée 正确比例）
#   * step=1 用全分辨率 2160×1080（0.167°）画海岸线，消除锯齿
#   * 面板加宽以容纳地图的正确比例；点径与图例相应收紧
def fig1(gea):
    # 图幅按「(a) 地图不压到 (b)」反推：
    #   (a) 绘图区高 h 英寸 ⇒ 宽 = h×2.773；(b) 需 ≈2.0 英寸宽；
    #   加上左右边距(1.30) + 面板间距(0.34) ⇒ 总宽 ≈ h×2.773 + 3.64
    #   取 h ≈ 1.30 ⇒ 宽 ≈ 7.25，高 = h + 0.30(title) + 0.52(xlabel) ≈ 2.12
    fig = plt.figure(figsize=(7.3, 2.15))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.05, 1.0])
    ax1 = fig.add_subplot(gs[0])
    add_basemap(ax1, step=1, extent=(-126, 118, -40, 48), aspect_equal=True)
    # 图例顺序与正文/表格统一为 P1→P6（旧代码沿用的是地理序 P1,P6,P2,P4,P3,P5）
    for m in ORD:
        s = gea[gea["module"] == m]
        if len(s):
            ax1.scatter(s["lon"], s["lat"], s=9, c=PALETTE[m], alpha=.9,
                        edgecolors="none", label="%s (%d)" % (m, len(s)), zorder=3)
    ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")
    ax1.set_title("(a) Sampling sites (n = 214)", pad=4)

    ax2 = fig.add_subplot(gs[1])
    for m in ORD:
        s = gea[gea["module"] == m]
        if len(s):
            ax2.scatter(s["bio1"], s["bio12"], s=11, c=PALETTE[m], alpha=.85,
                        edgecolors="none")
    ax2.set_xlabel("BIO1 annual mean temperature (C)")
    ax2.set_ylabel("BIO12 annual precipitation (mm)")
    ax2.set_title("(b) Climatic space occupied", pad=4)

    # 图例放整图底部横排：面板内任何角落都会压住数据点
    # （左上=加州 P1，左下=巴西 P2/P4，右上=P3 非洲）⇒ 只能外置
    h, l = ax1.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, frameon=False,
               handletextpad=.3, columnspacing=1.0, fontsize=6.5,
               bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.078, right=0.985, top=0.865, bottom=0.245, wspace=0.32)
    # ★ 让 (a) 与 (b) 上下沿看齐、高度严格一致（详见 pub_style_p.align_panel_height）
    align_panel_height(fig, ax1, ax2, ratio=(118 - (-126)) / (48 - (-40)), verbose=True)
    save(fig, "Fig1_sampling_and_climate")


# ---------------- Fig 2：群体结构 ----------------
# 2026-10-03 版面重做（两个问题）：
#   ① (b) 的 ylabel "PC1" 溢出到 (a) 面板里、把 (a) 右缘的数据点挡住
#      ⇒ colorbar 改用独立 cax（原先 plt.colorbar(ax=ax2) 会就地吃掉 ax2 的宽度），
#        并加 wspace + labelpad
#   ② PC1–PC4 曾整列为空 ⇒ 画出一张全空的图（详见 load_all 的断言）
def fig2(gea):
    fig = plt.figure(figsize=(7.2, 3.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.12, 1.0, 0.052],
                          left=0.085, right=0.945, top=0.895, bottom=0.155,
                          wspace=0.34)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    cax = fig.add_subplot(gs[2])
    for m in ORD:
        s = gea[gea["module"] == m]
        if len(s):
            ax1.scatter(s["PC1"], s["PC2"], s=11, c=PALETTE[m], alpha=.85,
                        edgecolors="none", label="%s" % m)
    ax1.axhline(0, c="#dddddd", lw=.6); ax1.axvline(0, c="#dddddd", lw=.6)
    ax1.set_xlabel("PC1 (6.61%)"); ax1.set_ylabel("PC2 (3.01%)")
    ax1.set_title("(a) Population structure (PCAngsd)", pad=4)
    # 图例放面板内右上角（x>0.1, y>0.1 无数据点；最高的点在左上 x=-0.28）
    ax1.legend(frameon=False, ncol=3, handletextpad=.2, columnspacing=.6,
               loc="upper right", fontsize=6.5)

    us = gea[gea["module"] == "P1"]
    sc = ax2.scatter(us["lat"], us["PC1"], s=13, c=us["rate"], cmap="viridis",
                     edgecolors="none")
    ax2.set_xlabel("Latitude (deg)")
    ax2.set_ylabel("PC1", labelpad=1.0)
    r = np.corrcoef(us["lat"], us["PC1"])[0, 1]
    ax2.set_title("(b) P1 panel: PC1 vs latitude  (r = %+.3f)" % r, pad=4)
    cb = fig.colorbar(sc, cax=cax)
    cb.set_label("Mapping rate (%)")
    save(fig, "Fig2_population_structure")


# ---------------- Fig 3：株系格局 ----------------
# 2026-10-03 与 Fig 1 同步重做底图（同样的 aspect / 分辨率 / 图例外置处理）
def fig3(gea):
    fig = plt.figure(figsize=(7.3, 2.15))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.05, 1.0])
    ax1 = fig.add_subplot(gs[0])
    add_basemap(ax1, step=1, extent=(-126, 118, -40, 48), aspect_equal=True)
    for st, lab in [("C", "C (corn)"), ("R", "R (rice)"), ("H", "H (hybrid)")]:
        s = gea[gea["strain"] == st]
        if len(s):
            ax1.scatter(s["lon"], s["lat"], s=9, c=STRAIN_COL[st], alpha=.9,
                        edgecolors="none", label="%s n=%d" % (lab, len(s)), zorder=3)
    ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")
    ax1.set_title("(a) Geographic distribution of host strains", pad=4)

    ax2 = fig.add_subplot(gs[1])
    mods = ["P1", "P2", "P3", "P4", "P5", "P6"]
    c = [int((gea[(gea["module"] == m)]["strain"] == "C").sum()) for m in mods]
    r_ = [int((gea[(gea["module"] == m)]["strain"] == "R").sum()) for m in mods]
    x = np.arange(len(mods))
    ax2.bar(x, c, color=STRAIN_COL["C"], width=.62)
    ax2.bar(x, r_, bottom=c, color=STRAIN_COL["R"], width=.62)

    # 数值标签：P1=143 与 P6=6 差 24 倍，矮柱里塞 7pt 数字必糊。
    # 高柱（总高 ≥14）段内分别标；矮柱只在柱顶标总数，避免小数字互相重叠。
    for i in range(len(mods)):
        tot = c[i] + r_[i]
        if tot >= 14:
            if c[i]:
                ax2.text(i, c[i] / 2, str(c[i]), ha="center", va="center",
                         color="white", fontsize=7)
            if r_[i]:
                h = r_[i]
                if h >= 9:
                    ax2.text(i, c[i] + h / 2, str(r_[i]), ha="center", va="center",
                             color="white", fontsize=7)
                else:
                    ax2.text(i, c[i] + h + 2.5, str(r_[i]), ha="center", va="bottom",
                             color="#333333", fontsize=6.4)
        elif tot > 0:
            ax2.text(i, tot + 2.5, str(tot), ha="center", va="bottom",
                     color="#333333", fontsize=6.6)
    ax2.set_ylim(0, 152)
    ax2.set_xticks(x); ax2.set_xticklabels(mods)
    ax2.set_ylabel("Number of samples")
    ax2.set_title("(b) Strain composition by panel", pad=4)

    # 图例外置：株系含义与总数放在 (a) 下方；(b) 不再重复画同一组图例
    #（柱色与 (a) 点色一一对应，y 轴已标 Number of samples）
    h1, l1 = ax1.get_legend_handles_labels()
    fig.legend(h1, l1, loc="lower left", ncol=3, frameon=False,
               handletextpad=.3, columnspacing=1.0, fontsize=6.5,
               bbox_to_anchor=(0.075, 0.0))
    fig.subplots_adjust(left=0.078, right=0.985, top=0.865, bottom=0.245, wspace=0.32)
    # ★ 与 Fig 1 同一套对齐逻辑：地图面板与柱状图面板上下沿看齐
    align_panel_height(fig, ax1, ax2, ratio=(118 - (-126)) / (48 - (-40)), verbose=True)
    save(fig, "Fig3_host_strain")


# ---------------- Fig 4：P1 面板气候梯度 ----------------
def fig4(gea):
    us = gea[gea["module"] == "P1"].dropna(subset=["lat", "bio1"])
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    ax.scatter(us["lat"], us["bio1"], s=14, c=STRAIN_COL["C"], alpha=.75,
               edgecolors="none", label="BIO1 annual mean")
    ax.scatter(us["lat"], us["bio11"], s=14, c=STRAIN_COL["R"], alpha=.75,
               edgecolors="none", label="BIO11 coldest quarter")
    r1 = np.corrcoef(us["lat"], us["bio1"])[0, 1]
    r11 = np.corrcoef(us["lat"], us["bio11"])[0, 1]
    ax.axhline(0, c="#dddddd", lw=.6)
    ax.set_xlabel("Latitude (deg)"); ax.set_ylabel("Temperature (C)")
    ax.set_title("P1 panel climate gradient\nr(BIO1)=%+.3f, r(BIO11)=%+.3f" % (r1, r11), pad=4)
    ax.legend(frameon=False, loc="upper right")
    save(fig, "Fig4_P1_climate_gradient")


# ---------------- Fig 5：RDA 结果（与面板代号无关，照旧） ----------------
def fig5():
    z = pd.read_csv(os.path.join(REP, "gea_rda_z_full.tsv"), sep="\t")
    zv = z["z"].values.astype(np.float64)
    mk = z["marker"].values
    fig = plt.figure(figsize=(7.2, 2.9))

    ax1 = fig.add_subplot(131)
    ax1.hist(zv, bins=220, color="#9aa0a6")
    for t in (-4, 4):
        ax1.axvline(t, c=STRAIN_COL["C"], ls="--", lw=.9)
    ax1.set_yscale("log")
    ax1.set_xlabel("z of RDA1 loading"); ax1.set_ylabel("Number of SNPs (log)")
    ax1.set_title("(a) Loading distribution", pad=4, fontsize=8)

    ax2 = fig.add_subplot(132)
    from scipy.stats import norm
    p = 2.0 * norm.sf(np.abs(zv))
    p = np.sort(p)
    n = len(p)
    exp = -np.log10(np.arange(1, n + 1) / (n + 1))
    obs = -np.log10(np.clip(p, 1e-300, 1))
    step = max(1, n // 200000)
    ax2.scatter(exp[::step], obs[::step], s=.8, c="#7f8c8d", edgecolors="none", rasterized=True)
    lim = max(exp.max(), obs.max())
    ax2.plot([0, lim], [0, lim], c=STRAIN_COL["C"], lw=.9, ls="--")
    thr = -np.log10(2 * norm.sf(5.189))
    ax2.axhline(thr, c="#2471a3", lw=.8, ls=":")
    ax2.text(0.06 * lim, thr * 1.04, "FDR 0.05", fontsize=6, color="#2471a3")
    ax2.set_xlabel("Expected -log10(p)"); ax2.set_ylabel("Observed -log10(p)")
    ax2.set_title("(b) QQ plot (tail departure)", pad=4, fontsize=8)

    ax3 = fig.add_subplot(133)
    chrom = np.array([str(m).rsplit("_", 1)[0] for m in mk])
    pos = np.array([int(str(m).rsplit("_", 1)[1]) for m in mk])
    order = sorted(set(chrom))
    cand_thr = 5.189
    off, ticks, labels = 0, [], []
    for i, c in enumerate(order):
        sel = chrom == c
        ax3.scatter(pos[sel] + off, zv[sel], s=.1, c="#95a5a6", alpha=.3,
                    edgecolors="none", rasterized=True)
        cc = sel & (np.abs(zv) >= cand_thr)
        if cc.any():
            ax3.scatter(pos[cc] + off, zv[cc], s=2.4, c=STRAIN_COL["C"],
                        edgecolors="none", rasterized=True)
        if i % 5 == 0:
            ticks.append(off + pos[sel].max() / 2)
            labels.append(str(i + 1))
        off += pos[sel].max() + 2_000_000
    ax3.axhline(0, c="#dddddd", lw=.5)
    ax3.set_xticks(ticks); ax3.set_xticklabels(labels, fontsize=6)
    ax3.set_xlabel("Chromosome"); ax3.set_ylabel("z (RDA1)")
    ax3.set_title("(c) Manhattan plot (n=%d FDR-significant)"
                  % int((np.abs(zv) >= cand_thr).sum()), pad=4, fontsize=8)
    save(fig, "Fig5_RDA_results")


# ---------------- Fig 6：跨面板对比 ----------------
def fig6():
    d = pd.read_csv(os.path.join(REP, "crossregion_genes.tsv"), sep="\t")
    old_cols = ["US-C", "BR-C", "AF-C", "AM-C", "CN-C"]
    cols = [c.split("-")[0] for c in old_cols]
    cols = [OLD2NEW[c] + "-C" for c in cols]
    gs = np.zeros((len(cols), len(cols)), int)
    for i, a in enumerate(old_cols):
        for j, b in enumerate(old_cols):
            k = np.sum((d[a] == 1) & (d[b] == 1))
            gs[i, j] = k
    fig = plt.figure(figsize=(7.2, 3.2))
    # 2026-10-03：原先 plt.colorbar(im, ax=ax1) 会**就地吃掉 ax1 的宽度**，
    # 把 (b) 往左挤，导致 colorbar 的 label "Number of genes" 与 (b) 的 y 刻度数字
    # （1200 / 1000…）**直接叠字**。改用独立 cax + 显式 wspace（与 Fig2 同一修法）。
    # ★ 2026-10-03 第三次修：前两版都白改了。实测数据（figsize 7.2×3.2）：
    #     版                     热图x1   色带x0   热图→色带
    #     单层 3 格 wspace=0.40   0.386   0.449    0.450 in
    #     嵌套 wsub=0.30          0.397   0.445    0.349 in
    #     嵌套 wsub=0.05          0.435   0.445    0.065 in   ← 色带只左移 3px！
    #   原因：压缩间隙的同时**热图等比例变宽**，把色带又推回原处。
    #   ⇒ 要真正左移必须**让热图变窄** = 增大**外层** wspace（外层 gap 挤占左区）。
    #   实测 wmain=0.58 + wsub=0.10：热图x1=0.405、色带x0=0.422 ⇒ 左移 0.027 figure
    #   ≈ 0.20 inch ≈ 60 px@300dpi，且热图与色带保持 0.12 inch 的正常间距。
    #   ⇒ 真正的杠杆是**让左区（热图+色带）整体变窄** ⇒ width_ratios 让左区比右区窄 22%。
    #   实测：热图 x1 由 0.405 → 0.368，色带 x0 由 0.422 → 0.385（相对初版 0.449 左移
    #   0.064 figure ≈ 0.46 inch ≈ 130 px@300dpi，明显可见），而热图只缩约 6%。
    gspec = fig.add_gridspec(1, 2, width_ratios=[0.78, 1.0], wspace=0.50,
                             left=0.085, right=0.985, top=0.875, bottom=0.135)
    gspecL = gspec[0].subgridspec(1, 2, width_ratios=[1.0, 0.030], wspace=0.06)
    ax1 = fig.add_subplot(gspecL[0])
    cax = fig.add_subplot(gspecL[1])
    im = ax1.imshow(gs, cmap="Reds")
    ax1.set_xticks(range(len(cols))); ax1.set_xticklabels(cols, fontsize=6.5)
    ax1.set_yticks(range(len(cols))); ax1.set_yticklabels(cols, fontsize=6.5)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax1.text(j, i, str(gs[i, j]), ha="center", va="center", fontsize=6,
                     color="white" if gs[i, j] > gs.max() * .6 else "black")
    ax1.set_title("(a) Shared candidate genes\n(same-threshold per panel)", pad=4)
    # 刻度保持**默认（右）侧**。曾试过挪到左侧，结果压到热图格子上
    # （"311" 被 "1400" 盖住），更糟。右侧才是安全侧。
    # 刻度精简为 3 个（0/800/1600）+ 字号 6：缩小右侧占用，视觉上更贴近 (a)。
    cb = fig.colorbar(im, cax=cax)
    cax.set_yticks([0, 800, 1600])
    for t in cax.get_yticklabels():
        t.set_fontsize(6)
    # ★ 色带上下沿必须与 (a) 面板对齐。imshow 的 aspect=1.0 会把 ax1 的盒子拉成
    #   **正方形**（实测 2.184×2.184），而 cax 用的还是 gridspec 给的原长方形
    #   （高 2.368）⇒ 色带比热图高出 0.092 inch。显式按 ax1 的实际 position 对齐。
    fig.canvas.draw()
    _p1, _pc = ax1.get_position(), cax.get_position()
    cax.set_position([_pc.x0, _p1.y0, _pc.width, _p1.height])

    ax2 = fig.add_subplot(gspec[1])
    nshare = d["n_region"].values
    vals, cnts = np.unique(nshare, return_counts=True)
    ax2.bar(vals.astype(str), cnts, color="#2471a3", width=.6)
    for v, c in zip(vals, cnts):
        ax2.text(v, c, str(c), ha="center", va="bottom", fontsize=7)
    ax2.set_xlabel("Number of panels sharing the gene")
    ax2.set_ylabel("Number of genes")
    ax2.set_yscale("log")
    ax2.set_title("(b) Sharing across panels", pad=4)
    save(fig, "Fig6_cross_region")


# ---------------- Fig 7：混淆诊断 ----------------
def fig7():
    d = pd.read_csv(os.path.join(REP, "qc_s2_bm2k15_P.tsv"), sep="\t")
    for c in ["lat", "rate", "raw_depth"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["lat"])
    # 2026-10-03：原先用 add_subplot(131/132/133) 走**默认 wspace**，三个面板都带
    # ylabel + y 刻度，间隙被吃掉，(b)(c) 看着贴在一起。改用 gridspec 显式放大间隙。
    # wspace 0.42 ⇒ 面板间实际空白约 0.95 inch（原默认 0.2 时约 0.42 inch）。
    fig = plt.figure(figsize=(7.5, 2.7))
    gs = fig.add_gridspec(1, 3, wspace=0.42,
                          left=0.078, right=0.985, top=0.855, bottom=0.185)
    ax1 = fig.add_subplot(gs[0])
    for m in ORD:
        s = d[d["module"] == m]
        if len(s):
            ax1.scatter(s["lat"], s["rate"], s=11, c=PALETTE[m], alpha=.8,
                        edgecolors="none", label=m)
    r = np.corrcoef(d["lat"], d["rate"])[0, 1]
    ax1.set_xlabel("Latitude (deg)"); ax1.set_ylabel("Mapping rate (%)")
    ax1.set_title("(a) All panels: r = %+.3f\n(cross-panel effect)" % r, pad=4)
    ax1.legend(frameon=False, ncol=2, handletextpad=.2, columnspacing=.5)

    us = d[d["module"] == "P1"]
    ax2 = fig.add_subplot(gs[1])
    ax2.scatter(us["lat"], us["rate"], s=12, c=PALETTE["P1"], alpha=.85, edgecolors="none")
    r2 = np.corrcoef(us["lat"], us["rate"])[0, 1]
    ax2.set_xlabel("Latitude (deg)"); ax2.set_ylabel("Mapping rate (%)")
    ax2.set_title("(b) P1 panel: r = %+.3f\n(no within-panel confounding)" % r2, pad=4)

    ax3 = fig.add_subplot(gs[2])
    for m in ORD:
        s = d[d["module"] == m]
        if len(s):
            ax3.scatter(s["lat"], s["raw_depth"], s=11, c=PALETTE[m], alpha=.8, edgecolors="none")
    r3 = np.corrcoef(d["lat"], d["raw_depth"], )[0, 1]
    ax3.axhline(6, c=GREY, ls="--", lw=.9)
    # 原来放在数据坐标 (-33, 6.6)，正好压住 P2/P4 的点 → 改到面板左上角空白
    ax3.text(0.025, 0.965, "dashed: target 6x", transform=ax3.transAxes,
             fontsize=6, color=GREY, ha="left", va="top")
    ax3.set_xlabel("Latitude (deg)"); ax3.set_ylabel("Raw depth (x)")
    ax3.set_title("(c) Depth vs latitude: r = %+.3f\n(not a confounder)" % r3, pad=4)
    save(fig, "Fig7_confounding_diagnostics")


# ---------------- Fig S1：各面板比对率 ----------------
def figS1():
    d = pd.read_csv(os.path.join(REP, "qc_s2_bm2k15_P.tsv"), sep="\t")
    d["rate"] = pd.to_numeric(d["rate"], errors="coerce")
    mods = ORD                      # 原为 ["P1","P6","P2","P4","P3","P5"]，统一成 P1→P6
    data = [d[d["module"] == m]["rate"].dropna().values for m in mods]
    fig, ax = plt.subplots(figsize=(3.6, 3.2))
    bp = ax.boxplot(data, tick_labels=mods, patch_artist=True, widths=.6,
                    medianprops=dict(color="black", lw=1), flierprops=dict(markersize=1.8))
    for b, m in zip(bp["boxes"], mods):
        b.set_facecolor(PALETTE[m]); b.set_alpha(.65); b.set_edgecolor("black"); b.set_linewidth(.6)
    for i, m in enumerate(mods):
        v = data[i]
        ax.scatter(np.random.normal(i + 1, .07, len(v)), v, s=4, c="black", alpha=.35, edgecolors="none")
    ax.axhline(90, c=GREY, ls="--", lw=.9)
    # 原来放在数据坐标 (0.6, 90.8)，正好压住 P1 的箱体与离群点 → 改到右下角空白
    ax.text(0.985, 0.025, "dashed: 90% reference", transform=ax.transAxes,
            fontsize=6, color=GREY, ha="right", va="bottom")
    ax.set_ylabel("Mapping rate (%)")
    ax.set_title("Mapping rate by panel\n(P2 suffers reference bias)", pad=4)
    save(fig, "FigS1_mapping_rate")


# ---------------- Fig S2：两法一致性（与面板无关） ----------------
def figS2():
    zr = pd.read_csv(os.path.join(REP, "gea_rda_z_full.tsv"), sep="\t")
    pl = pd.read_csv(os.path.join(REP, "gea_lfmm_p.tsv"), sep="\t")[["marker", "p"]]
    m = pl.merge(zr, on="marker", how="inner")
    x = np.abs(m["z"].values.astype(float))
    y = -np.log10(np.maximum(m["p"].values.astype(float), 1e-300))
    r = np.corrcoef(x, y)[0, 1]
    from scipy.stats import spearmanr
    rho = spearmanr(x, y).correlation
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    hb = ax.hexbin(x, y, gridsize=70, bins="log", cmap="viridis", mincnt=1)
    ax.set_xlabel("|z| (partial RDA)")
    # 第 5 条（2026-10-02）：原来只写 "single-SNP F test"，未点出方法名，
    # 与图注的 *p*_LFMM-type 不一致。改为显式写 LFMM-type。
    ax.set_ylabel("-log10(p) (LFMM-type F test)")
    ax.set_title("Cross-method concordance\nr=%+.3f, rho=%+.3f (n=%.2fM SNPs)"
                 % (r, rho, len(m) / 1e6), pad=4)
    plt.colorbar(hb, ax=ax, label="log10 count", fraction=.046)
    save(fig, "FigS2_cross_method")


# ---------------- Fig S3：株系判别验证 ----------------
def figS3():
    d = pd.read_csv(os.path.join(REP, "strain_predicted_P.tsv"), sep="\t")
    us = d[(d["module"] == "P1") & (d["strain_known"].isin(["C", "R"]))]
    tab = pd.crosstab(us["strain_known"], us["strain_pred"])
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    im = ax.imshow(tab.values, cmap="Blues")
    ax.set_xticks(range(tab.shape[1])); ax.set_xticklabels(tab.columns)
    ax.set_yticks(range(tab.shape[0])); ax.set_yticklabels(tab.index)
    for i in range(tab.shape[0]):
        for j in range(tab.shape[1]):
            ax.text(j, i, str(tab.values[i, j]), ha="center", va="center", fontsize=9,
                    color="white" if tab.values[i, j] > tab.values.max() * .6 else "black")
    ax.set_xlabel("Predicted (Tpi/Flightin)"); ax.set_ylabel("NCBI label")
    ax.set_title("Strain assignment validation\nleave-one-out accuracy 100%% (n=%d)"
                 % tab.values.sum(), pad=4)
    save(fig, "FigS3_strain_validation")


if __name__ == "__main__":
    gea = load_all()
    print("生成中性代号图件 → /mnt/c/SF_data/tools/report/pub_p/")
    fig1(gea); fig2(gea); fig3(gea); fig4(gea)
    fig5(); fig6(); fig7(); figS1(); figS2(); figS3()
    print("完成")
